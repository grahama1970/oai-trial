#!/usr/bin/env python3
"""Retained real-path check for native DICOM metadata redaction."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def elem(group: int, element: int, vr: str, value: bytes, *, byteorder: str = "little") -> bytes:
    if len(value) % 2:
        value += b" "
    return group.to_bytes(2, byteorder) + element.to_bytes(2, byteorder) + vr.encode("ascii") + len(value).to_bytes(2, byteorder) + value


def implicit_elem(group: int, element: int, value: bytes) -> bytes:
    if len(value) % 2:
        value += b" "
    return group.to_bytes(2, "little") + element.to_bytes(2, "little") + len(value).to_bytes(4, "little") + value


def long_elem(group: int, element: int, vr: str, value: bytes, *, byteorder: str = "little") -> bytes:
    if len(value) % 2:
        value += b"\0"
    return group.to_bytes(2, byteorder) + element.to_bytes(2, byteorder) + vr.encode("ascii") + b"\0\0" + len(value).to_bytes(4, byteorder) + value


def write_dicom(path: Path, patient: bytes = b"Alice Example", study: bytes = b"Chest") -> None:
    path.write_bytes(
        b"\0" * 128
        + b"DICM"
        + elem(0x0008, 0x0020, "DA", b"20260921")
        + elem(0x0010, 0x0010, "PN", patient)
        + elem(0x0008, 0x1030, "LO", study)
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


with tempfile.TemporaryDirectory(prefix="dicom-redaction-") as directory:
    root = Path(directory)
    source = root / "source.dcm"
    output = root / "redacted.dcm"
    receipt = root / "receipt.json"
    policy = root / "policy.json"
    write_dicom(source)
    policy.write_text(
        json.dumps(
            {
                "version": 1,
                "sensitive_values": [
                    {
                        "rule_id": "patient",
                        "subject_id": "person-1",
                        "type": "name",
                        "value": "Alice Example",
                    }
                ],
                "protected_values": [],
            }
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(  # noqa: S603 - fixed project CLI argv
        [
            ".venv/bin/anonymization-trial",
            "redact-document",
            "--input",
            str(source),
            "--policy",
            str(policy),
            "--output",
            str(output),
            "--receipt",
            str(receipt),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    require(result["schema"] == "multimodal_redaction.v1", "wrong schema")
    require(result["redaction_boxes"] == 1, "wrong replacement count")
    structural = result["structural_verification"]
    require(structural["dicom_preamble_present"] is True, "missing DICOM preamble")
    require(structural["policy_literals_absent"] is True, "literal verification missing")
    require(structural["text_elements_checked"] >= 2, "text elements not checked")
    require(b"Alice Example" not in output.read_bytes(), "output retained raw patient name")
    require("Alice Example" not in receipt.read_text(encoding="utf-8"), "receipt leaked raw patient name")

    syntax_cases = {
        "implicit": elem(0x0002, 0x0010, "UI", b"1.2.840.10008.1.2")
        + implicit_elem(0x0010, 0x0010, b"Alice Example")
        + implicit_elem(0x0008, 0x1030, b"Chest"),
        "big": elem(0x0002, 0x0010, "UI", b"1.2.840.10008.1.2.2")
        + elem(0x0010, 0x0010, "PN", b"Alice Example", byteorder="big")
        + elem(0x0008, 0x1030, "LO", b"Chest", byteorder="big"),
    }
    for name, body in syntax_cases.items():
        syntax_source = root / f"{name}.dcm"
        syntax_output = root / f"{name}-out.dcm"
        syntax_receipt = root / f"{name}-receipt.json"
        syntax_source.write_bytes(b"\0" * 128 + b"DICM" + body)
        syntax_completed = subprocess.run(  # noqa: S603 - fixed project CLI argv
            [
                ".venv/bin/anonymization-trial",
                "redact-document",
                "--input",
                str(syntax_source),
                "--policy",
                str(policy),
                "--output",
                str(syntax_output),
                "--receipt",
                str(syntax_receipt),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        syntax_result = json.loads(syntax_completed.stdout)
        require(syntax_result["redaction_boxes"] == 1, f"{name} syntax was not redacted")
        require(
            syntax_result["structural_verification"]["text_elements_checked"] >= 2,
            f"{name} syntax structural text check missing",
        )
        require(b"Alice Example" not in syntax_output.read_bytes(), f"{name} output leaked raw patient")
        require("Alice Example" not in syntax_receipt.read_text(encoding="utf-8"), f"{name} receipt leaked raw patient")

    bad = root / "bad.dcm"
    write_dicom(bad, b"Bob Patient")
    rejected = subprocess.run(  # noqa: S603 - fixed project CLI argv
        [
            ".venv/bin/anonymization-trial",
            "redact-document",
            "--input",
            str(bad),
            "--policy",
            str(policy),
            "--output",
            str(root / "bad-out.dcm"),
            "--receipt",
            str(root / "bad-receipt.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    require(rejected.returncode != 0, "DICOM with no policy match must fail closed")
    require("Alice Example" not in rejected.stderr + rejected.stdout, "rejection leaked raw policy value")

    private = root / "private.dcm"
    private.write_bytes(
        b"\0" * 128
        + b"DICM"
        + elem(0x0008, 0x1030, "LO", b"Chest")
        + long_elem(0x0011, 0x1010, "OB", b"binary Alice Example carrier")
    )
    private_rejected = subprocess.run(  # noqa: S603 - fixed project CLI argv
        [
            ".venv/bin/anonymization-trial",
            "redact-document",
            "--input",
            str(private),
            "--policy",
            str(policy),
            "--output",
            str(root / "private-out.dcm"),
            "--receipt",
            str(root / "private-receipt.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    require(private_rejected.returncode != 0, "private binary policy literal must fail closed")
    require(not (root / "private-out.dcm").exists(), "private binary output published")
    require("Alice Example" not in private_rejected.stderr + private_rejected.stdout, "private rejection leaked raw value")

    if shutil.which("tesseract"):
        from PIL import Image, ImageDraw, ImageFont

        font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        require(font_path.exists(), "test font unavailable")
        image = Image.new("RGB", (900, 160), "white")
        ImageDraw.Draw(image).text(
            (30, 50),
            "Patient Alice Example",
            fill="black",
            font=ImageFont.truetype(str(font_path), 40),
        )
        pixel = root / "pixel.jpg"
        image.save(pixel, "JPEG", quality=95)
        pixel_source = root / "pixel.dcm"
        pixel_output = root / "pixel-out.dcm"
        pixel_receipt = root / "pixel-receipt.json"
        pixel_source.write_bytes(
            b"\0" * 128
            + b"DICM"
            + elem(0x0002, 0x0010, "UI", b"1.2.840.10008.1.2.4.50")
            + elem(0x0008, 0x1030, "LO", b"Chest")
            + long_elem(0x7FE0, 0x0010, "OB", pixel.read_bytes())
        )
        pixel_completed = subprocess.run(  # noqa: S603 - fixed project CLI argv
            [
                ".venv/bin/anonymization-trial",
                "redact-document",
                "--input",
                str(pixel_source),
                "--policy",
                str(policy),
                "--output",
                str(pixel_output),
                "--receipt",
                str(pixel_receipt),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        pixel_result = json.loads(pixel_completed.stdout)
        require(pixel_result["redaction_boxes"] >= 1, "compressed pixel OCR did not redact")
        require(
            pixel_result["structural_verification"]["compressed_pixel_elements_checked"] == 1,
            "compressed pixel structural verification missing",
        )
        require("Alice Example" not in pixel_receipt.read_text(encoding="utf-8"), "pixel receipt leaked raw value")

print("DICOM_REDACTION_REAL_PATH_VERIFIED")
