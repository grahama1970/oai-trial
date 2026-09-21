#!/usr/bin/env python3
"""Retained real-path check for native DICOM metadata redaction."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def elem(group: int, element: int, vr: str, value: bytes) -> bytes:
    if len(value) % 2:
        value += b" "
    return group.to_bytes(2, "little") + element.to_bytes(2, "little") + vr.encode("ascii") + len(value).to_bytes(2, "little") + value


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

print("DICOM_REDACTION_REAL_PATH_VERIFIED")
