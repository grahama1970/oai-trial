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
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .policy import Policy, load_policy, replace_text

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
_DOCX_FORBIDDEN_PARTS = (
    "vbaProject",
    "embeddings/",
    "activeX/",
    "externalLinks/",
    "oleObject",
)
_DOCX_FORBIDDEN_RELATIONSHIP_MARKERS = (
    "vbaProject",
    "oleObject",
    "package",
    "activeX",
    "externalLink",
    "attachedTemplate",
)
_DOCX_FORBIDDEN_CONTENT_TYPE_MARKERS = (
    "vbaProject",
    "macroEnabled",
    "oleObject",
    "activeX",
    "externalLink",
)
_DOCX_TEXT_PARTS = (
    "word/document.xml",
    "word/header",
    "word/footer",
    "word/footnotes.xml",
    "word/endnotes.xml",
    "docProps/core.xml",
    "docProps/app.xml",
    "docProps/custom.xml",
)


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


def _policy_literal_bytes(policy: Policy) -> list[bytes]:
    return [rule.value.encode("utf-8") for rule in policy.rules if rule.value]


def _policy_literal_texts(policy: Policy) -> list[str]:
    return [rule.value for rule in policy.rules if rule.value]


def _normalized_policy_literal_texts(policy: Policy) -> list[str]:
    return [_canonical(rule.value) for rule in policy.rules if _canonical(rule.value)]


def _contains_policy_literal_text(text: str, policy: Policy) -> bool:
    if any(value in text for value in _policy_literal_texts(policy)):
        return True
    normalized = _canonical(text)
    return any(value in normalized for value in _normalized_policy_literal_texts(policy))


def _xml_root(data: bytes) -> ET.Element:
    try:
        return ET.fromstring(data)
    except (ET.ParseError, UnicodeDecodeError) as error:
        raise MultimodalError("MULTIMODAL_DOCX_XML_INVALID") from error


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _marker_in(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.casefold()
    return any(marker.casefold() in lowered for marker in markers)


def _docx_active_carrier_present(archive: zipfile.ZipFile) -> bool:
    names = archive.namelist()
    if any(_marker_in(name, _DOCX_FORBIDDEN_PARTS) for name in names):
        return True
    for name in names:
        if name == "[Content_Types].xml" or name.endswith(".rels") or name.endswith(".xml"):
            root = _xml_root(archive.read(name))
            for element in root.iter():
                content_type = element.attrib.get("ContentType", "")
                rel_type = element.attrib.get("Type", "")
                target_mode = element.attrib.get("TargetMode", "")
                if _marker_in(content_type, _DOCX_FORBIDDEN_CONTENT_TYPE_MARKERS):
                    return True
                if _marker_in(rel_type, _DOCX_FORBIDDEN_RELATIONSHIP_MARKERS):
                    return True
                if target_mode.casefold() == "external":
                    return True
    return False


def _validate_docx_package(archive: zipfile.ZipFile) -> dict[str, bool]:
    names = archive.namelist()
    required = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}
    if not required.issubset(names) or len(names) != len(set(names)):
        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")

    content_root = _xml_root(archive.read("[Content_Types].xml"))
    if _xml_local_name(content_root.tag) != "Types":
        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")
    has_document_override = any(
        element.attrib.get("PartName") == "/word/document.xml"
        and element.attrib.get("ContentType")
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
        for element in content_root.iter()
    )
    if not has_document_override:
        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")

    rel_root = _xml_root(archive.read("_rels/.rels"))
    if _xml_local_name(rel_root.tag) != "Relationships":
        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")
    has_main_relationship = any(
        element.attrib.get("Type")
        == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
        and element.attrib.get("Target") == "word/document.xml"
        and element.attrib.get("TargetMode", "").casefold() != "external"
        for element in rel_root.iter()
    )
    if not has_main_relationship:
        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")

    document_root = _xml_root(archive.read("word/document.xml"))
    if _xml_local_name(document_root.tag) != "document":
        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")
    if not any(_xml_local_name(element.tag) == "body" for element in document_root.iter()):
        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")
    return {
        "required_parts_present": True,
        "office_document_relationship_valid": True,
        "main_document_xml_valid": True,
    }


def _docx_metadata_has_policy_literal(archive: zipfile.ZipFile, policy: Policy) -> bool:
    if archive.comment and _contains_policy_literal_text(
        archive.comment.decode("utf-8", errors="ignore"), policy
    ):
        return True
    for item in archive.infolist():
        if _contains_policy_literal_text(item.filename, policy):
            return True
        if item.comment and _contains_policy_literal_text(
            item.comment.decode("utf-8", errors="ignore"), policy
        ):
            return True
    return False


def verify_docx_structural_release(path: Path, policy: Policy) -> dict[str, bool | int]:
    """Reject native DOCX releases retaining active carriers or policy literals."""
    literal_bytes = _policy_literal_bytes(policy)
    checked_parts = 0
    xml_parts_checked = 0
    try:
        with zipfile.ZipFile(path) as archive:
            package_verification = _validate_docx_package(archive)
            if _docx_active_carrier_present(archive) or _docx_metadata_has_policy_literal(archive, policy):
                raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")
            for name in archive.namelist():
                data = archive.read(name)
                checked_parts += 1
                if any(value in data for value in literal_bytes):
                    raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")
                if name.endswith((".xml", ".rels")) or name == "[Content_Types].xml":
                    root = _xml_root(data)
                    xml_parts_checked += 1
                    decoded_text = "".join(root.itertext())
                    if _contains_policy_literal_text(decoded_text, policy):
                        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED")
    except zipfile.BadZipFile as error:
        raise MultimodalError("MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED") from error
    return {
        "forbidden_structures_absent": True,
        "policy_literals_absent": True,
        "checked_parts": checked_parts,
        "xml_parts_valid": xml_parts_checked,
        "zip_metadata_policy_literals_absent": True,
        **package_verification,
    }


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


def _redact_docx(source: Path, destination: Path, policy: Policy) -> tuple[int, set[str]]:
    replacements = 0
    matched: set[str] = set()
    try:
        with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(
            destination, "w", compression=zipfile.ZIP_DEFLATED
        ) as dst:
            if _docx_active_carrier_present(src) or _docx_metadata_has_policy_literal(src, policy):
                raise MultimodalError("MULTIMODAL_DOCX_UNSUPPORTED_ACTIVE_CONTENT")
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename.endswith((".xml", ".rels")) or item.filename == "[Content_Types].xml":
                    _xml_root(data)
                if item.filename.endswith(".xml") and item.filename.startswith(_DOCX_TEXT_PARTS):
                    try:
                        text = data.decode("utf-8")
                    except UnicodeDecodeError as error:
                        raise MultimodalError("MULTIMODAL_DOCX_XML_INVALID") from error
                    transformed, count = replace_text(text, policy)
                    if count:
                        replacements += count
                        for rule in policy.rules:
                            if rule.value in text and rule.value not in transformed:
                                matched.add(rule.rule_id)
                    data = transformed.encode("utf-8")
                    _xml_root(data)
                dst.writestr(item, data)
    except zipfile.BadZipFile as error:
        raise MultimodalError("MULTIMODAL_DOCX_INVALID") from error
    return replacements, matched


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
        elif source.suffix.lower() == ".docx":
            if output.suffix.lower() != ".docx":
                raise MultimodalError("MULTIMODAL_OUTPUT_FORMAT_INVALID")
            boxes, matched = _redact_docx(source, temporary_output, policy)
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
        elif output.suffix.lower() == ".docx":
            structural_verification = verify_docx_structural_release(temporary_output, policy)
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
                "DOCX text split across multiple XML runs outside exact literal matching",
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
