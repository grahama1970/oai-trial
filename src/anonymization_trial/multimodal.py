"""Optional, offline image/PDF OCR redaction with fail-closed verification.

The default exact-data engine remains stdlib-only. This adapter is invoked only
by the explicit ``redact-document`` command and requires the ``multimodal``
extra plus local Tesseract; PDF input additionally requires ``pdftoppm``.
Raw OCR text is never written to receipts or logs.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .policy import Policy, load_policy

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


class MultimodalError(RuntimeError):
    """Sanitized multimodal redaction failure."""


@dataclass(frozen=True, slots=True)
class OCRWord:
    text: str
    left: int
    top: int
    width: int
    height: int


def _canonical(value: str) -> str:
    return "".join(ch.casefold() for ch in value if ch.isalnum())


def _ocr_words(image: Path) -> list[OCRWord]:
    tesseract = shutil.which("tesseract")
    if tesseract is None:
        raise MultimodalError("MULTIMODAL_OCR_UNAVAILABLE")
    completed = subprocess.run(  # noqa: S603 - resolved local binary and controlled argv
        [tesseract, str(image), "stdout", "tsv"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        raise MultimodalError("MULTIMODAL_OCR_FAILED")
    lines = completed.stdout.splitlines()
    if not lines:
        raise MultimodalError("MULTIMODAL_OCR_EMPTY")
    header = lines[0].split("\t")
    required = {"text", "left", "top", "width", "height"}
    if not required.issubset(header):
        raise MultimodalError("MULTIMODAL_OCR_INVALID")
    positions = {name: header.index(name) for name in required}
    words: list[OCRWord] = []
    for line in lines[1:]:
        fields = line.split("\t")
        try:
            text = fields[positions["text"]].strip()
            if text:
                words.append(
                    OCRWord(
                        text,
                        *(
                            int(fields[positions[key]])
                            for key in ("left", "top", "width", "height")
                        ),
                    )
                )
        except (IndexError, ValueError):
            raise MultimodalError("MULTIMODAL_OCR_INVALID") from None
    return words


def _matching_boxes(
    words: list[OCRWord], policy: Policy
) -> tuple[list[tuple[int, int, int, int]], set[str]]:
    boxes: list[tuple[int, int, int, int]] = []
    matched: set[str] = set()
    for rule in policy.rules:
        target = _canonical(rule.value)
        if not target:
            continue
        for start in range(len(words)):
            combined = ""
            for end in range(start, len(words)):
                combined += _canonical(words[end].text)
                if combined == target:
                    selected = words[start : end + 1]
                    left = min(word.left for word in selected)
                    top = min(word.top for word in selected)
                    right = max(word.left + word.width for word in selected)
                    bottom = max(word.top + word.height for word in selected)
                    boxes.append((left, top, right, bottom))
                    matched.add(rule.rule_id)
                    break
                if len(combined) >= len(target):
                    break
    return boxes, matched


def verify_pdf_structural_release(path: Path) -> dict[str, bool]:
    """Independently reject non-rendered PDF carriers after raster rebuilding."""
    data = path.read_bytes()
    forbidden_markers = (
        b"/EmbeddedFiles",
        b"/Filespec",
        b"/Annots",
        b"/AcroForm",
        b"/OCProperties",
        b"/JavaScript",
        b"/Metadata",
    )
    if any(marker in data for marker in forbidden_markers):
        raise MultimodalError("MULTIMODAL_PDF_STRUCTURAL_VERIFICATION_FAILED")

    pdfinfo = shutil.which("pdfinfo")
    pdftotext = shutil.which("pdftotext")
    if pdfinfo is None or pdftotext is None:
        raise MultimodalError("MULTIMODAL_PDF_ORACLE_UNAVAILABLE")
    info = subprocess.run(  # noqa: S603
        [pdfinfo, str(path)], capture_output=True, text=True, timeout=60, check=False
    )
    text = subprocess.run(  # noqa: S603
        [pdftotext, str(path), "-"], capture_output=True, timeout=60, check=False
    )
    if info.returncode != 0 or text.returncode != 0:
        raise MultimodalError("MULTIMODAL_PDF_STRUCTURAL_VERIFICATION_FAILED")
    metadata = {
        line.split(":", 1)[0].strip().casefold(): line.split(":", 1)[1].strip()
        for line in info.stdout.splitlines()
        if ":" in line
    }
    if any(metadata.get(field) for field in ("title", "author", "subject", "keywords")):
        raise MultimodalError("MULTIMODAL_PDF_STRUCTURAL_VERIFICATION_FAILED")
    if text.stdout.strip():
        raise MultimodalError("MULTIMODAL_PDF_STRUCTURAL_VERIFICATION_FAILED")
    return {
        "forbidden_structures_absent": True,
        "sensitive_metadata_absent": True,
        "extractable_text_absent": True,
    }


def _redact_image(source: Path, destination: Path, policy: Policy) -> tuple[int, set[str]]:
    try:
        from PIL import Image, ImageDraw
    except ImportError as error:
        raise MultimodalError("MULTIMODAL_DEPENDENCY_UNAVAILABLE") from error
    words = _ocr_words(source)
    boxes, matched = _matching_boxes(words, policy)
    with Image.open(source) as image:
        rendered = image.convert("RGB")
        draw = ImageDraw.Draw(rendered)
        for box in boxes:
            draw.rectangle(box, fill="black")
        destination.parent.mkdir(parents=True, exist_ok=True)
        rendered.save(destination)
    residual_boxes, _ = _matching_boxes(_ocr_words(destination), policy)
    if residual_boxes:
        destination.unlink(missing_ok=True)
        raise MultimodalError("MULTIMODAL_VERIFICATION_FAILED")
    return len(boxes), matched


def redact_document(source: Path, policy_path: Path, output: Path, receipt: Path) -> dict:
    """Redact OCR-located policy literals from one image or PDF without overwrite."""
    source = source.resolve()
    output = output.resolve()
    receipt = receipt.resolve()
    if not source.is_file() or not policy_path.is_file():
        raise MultimodalError("MULTIMODAL_INPUT_INVALID")
    if output.exists() or receipt.exists() or output == source or receipt in {source, output}:
        raise MultimodalError("MULTIMODAL_OUTPUT_EXISTS")
    policy = load_policy(policy_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(f".{output.stem}.tmp-{os.getpid()}{output.suffix}")
    pages = 1
    boxes = 0
    matched: set[str] = set()
    try:
        if source.suffix.lower() in _IMAGE_SUFFIXES:
            if output.suffix.lower() not in _IMAGE_SUFFIXES:
                raise MultimodalError("MULTIMODAL_OUTPUT_FORMAT_INVALID")
            boxes, matched = _redact_image(source, temporary_output, policy)
        elif source.suffix.lower() == ".pdf":
            pdftoppm = shutil.which("pdftoppm")
            if output.suffix.lower() != ".pdf" or pdftoppm is None:
                raise MultimodalError("MULTIMODAL_PDF_UNAVAILABLE")
            try:
                from PIL import Image
            except ImportError as error:
                raise MultimodalError("MULTIMODAL_DEPENDENCY_UNAVAILABLE") from error
            with tempfile.TemporaryDirectory(prefix="anon-multimodal-") as directory:
                page_root = Path(directory)
                completed = subprocess.run(  # noqa: S603
                    [pdftoppm, "-png", "-r", "200", str(source), str(page_root / "page")],
                    capture_output=True,
                    timeout=300,
                    check=False,
                )
                rendered = sorted(page_root.glob("page-*.png"))
                if completed.returncode != 0 or not rendered:
                    raise MultimodalError("MULTIMODAL_PDF_RENDER_FAILED")
                redacted = []
                for index, page in enumerate(rendered):
                    redacted_page = page_root / f"redacted-{index:06d}.png"
                    count, ids = _redact_image(page, redacted_page, policy)
                    boxes += count
                    matched.update(ids)
                    redacted.append(Image.open(redacted_page).convert("RGB"))
                pages = len(redacted)
                redacted[0].save(
                    temporary_output,
                    "PDF",
                    save_all=True,
                    append_images=redacted[1:],
                    resolution=200,
                    title="",
                    author="",
                    subject="",
                    keywords="",
                )
                for image in redacted:
                    image.close()
        else:
            raise MultimodalError("MULTIMODAL_INPUT_FORMAT_UNSUPPORTED")
        if boxes == 0:
            raise MultimodalError("MULTIMODAL_NO_POLICY_MATCH")
        structural_verification = None
        if output.suffix.lower() == ".pdf":
            structural_verification = verify_pdf_structural_release(temporary_output)
        os.replace(temporary_output, output)
        output_hash = hashlib.sha256(output.read_bytes()).hexdigest()
        report = {
            "schema": "multimodal_redaction.v1",
            "status": "ready",
            "pages": pages,
            "redaction_boxes": boxes,
            "matched_rule_ids": sorted(matched),
            "output_sha256": output_hash,
            "verification_passed": True,
            "structural_verification": structural_verification,
            "does_not_establish": [
                "OCR recall for policy values not detected by Tesseract",
                "general semantic anonymity or resistance to visual re-identification",
            ],
        }
        receipt.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return report
    except Exception:
        temporary_output.unlink(missing_ok=True)
        output.unlink(missing_ok=True)
        raise
