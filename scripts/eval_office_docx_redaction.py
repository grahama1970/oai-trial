#!/usr/bin/env python3
"""Retained real-path check for native DOCX redaction."""
from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_docx(
    path: Path,
    body: str,
    extra: dict[str, str] | None = None,
    *,
    archive_comment: bytes = b"",
) -> None:
    parts = {
        "[Content_Types].xml": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
<Default Extension=\"xml\" ContentType=\"application/xml\"/>
<Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>
</Types>""",
        "_rels/.rels": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>
</Relationships>""",
        "word/document.xml": body,
    }
    if extra:
        parts.update(extra)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = archive_comment
        for name, data in parts.items():
            archive.writestr(name, data)


with tempfile.TemporaryDirectory(prefix="docx-redaction-") as directory:
    root = Path(directory)
    source = root / "source.docx"
    output = root / "redacted.docx"
    receipt = root / "receipt.json"
    policy = root / "policy.json"
    write_docx(
        source,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>Contact alice@example.com today</w:t></w:r></w:p></w:body></w:document>""",
    )
    policy.write_text(
        json.dumps(
            {
                "version": 1,
                "sensitive_values": [
                    {
                        "rule_id": "email",
                        "subject_id": "person-1",
                        "type": "email",
                        "value": "alice@example.com",
                    }
                ],
                "protected_values": [],
            }
        ),
        encoding="utf-8",
    )
    active_rel = root / "active-rel.docx"
    write_docx(
        active_rel,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>alice@example.com</w:t></w:r></w:p></w:body></w:document>""",
        {
            "word/_rels/document.xml.rels": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId9\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject\" Target=\"media/data.bin\"/></Relationships>"""
        },
    )
    active_rejected = subprocess.run(
        [
            ".venv/bin/anonymization-trial",
            "redact-document",
            "--input",
            str(active_rel),
            "--policy",
            str(policy),
            "--output",
            str(root / "active-out.docx"),
            "--receipt",
            str(root / "active-receipt.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    require(active_rejected.returncode != 0, "active relationship must fail closed")
    metadata = root / "metadata.docx"
    write_docx(
        metadata,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>alice@example.com</w:t></w:r></w:p></w:body></w:document>""",
        archive_comment=b"alice@example.com",
    )
    metadata_rejected = subprocess.run(
        [
            ".venv/bin/anonymization-trial",
            "redact-document",
            "--input",
            str(metadata),
            "--policy",
            str(policy),
            "--output",
            str(root / "metadata-out.docx"),
            "--receipt",
            str(root / "metadata-receipt.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    require(metadata_rejected.returncode != 0, "metadata policy literal must fail closed")

    completed = subprocess.run(
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
    require(result["status"] == "ready", "release not ready")
    require(result["redaction_boxes"] == 1, "wrong replacement count")
    require(result["structural_verification"]["policy_literals_absent"] is True, "literal verification missing")
    require(result["structural_verification"]["xml_parts_valid"] >= 3, "XML validity verification missing")
    require(
        result["structural_verification"]["zip_metadata_policy_literals_absent"] is True,
        "ZIP metadata verification missing",
    )
    require(receipt.stat().st_mode & 0o777 == 0o600, "private receipt mode")
    receipt_text = receipt.read_text(encoding="utf-8")
    require("alice@example.com" not in receipt_text, "receipt leaked raw literal")
    with zipfile.ZipFile(output) as archive:
        payload = b"".join(archive.read(name) for name in archive.namelist())
    require(b"alice@example.com" not in payload, "DOCX output leaked raw literal")

print("OFFICE_DOCX_REDACTION_REAL_PATH_VERIFIED")
