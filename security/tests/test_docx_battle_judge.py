from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "battle"))
import docx_judge  # noqa: E402


def _docx(path: Path, body: str, *, comment: bytes = b"") -> None:
    parts = {
        "[Content_Types].xml": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/></Types>""",
        "_rels/.rels": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/></Relationships>""",
        "word/document.xml": body,
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = comment
        for name, text in parts.items():
            archive.writestr(name, text)


def _receipt(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "multimodal_redaction.v1",
                "status": "ready",
                "structural_verification": {
                    "forbidden_structures_absent": True,
                    "policy_literals_absent": True,
                    "zip_metadata_policy_literals_absent": True,
                    "xml_parts_valid": 3,
                },
            }
        ),
        encoding="utf-8",
    )


def test_docx_judge_rejects_decoded_xml_policy_literal(tmp_path: Path) -> None:
    _docx(
        tmp_path / "out.docx",
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>alice&#64;example.com</w:t></w:r></w:p></w:body></w:document>""",
    )
    _receipt(tmp_path / "receipt.json")
    result = docx_judge.judge(str(tmp_path), {})
    assert result["passed"] is False
    assert any("decoded XML" in violation for violation in result["violations"])


def test_docx_judge_rejects_zip_metadata_literal(tmp_path: Path) -> None:
    _docx(
        tmp_path / "out.docx",
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>[REDACTED]</w:t></w:r></w:p></w:body></w:document>""",
        comment=b"alice@example.com",
    )
    _receipt(tmp_path / "receipt.json")
    result = docx_judge.judge(str(tmp_path), {})
    assert result["passed"] is False
    assert any("ZIP metadata" in violation for violation in result["violations"])


def test_docx_judge_accepts_clean_release(tmp_path: Path) -> None:
    _docx(
        tmp_path / "out.docx",
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>Contact [REDACTED] today</w:t></w:r></w:p></w:body></w:document>""",
    )
    _receipt(tmp_path / "receipt.json")
    assert docx_judge.judge(str(tmp_path), {})["passed"] is True


def test_docx_judge_accepts_sanitized_contract_rejection(tmp_path: Path) -> None:
    execution = tmp_path / ".battle-execution"
    execution.mkdir()
    (execution / "stdout.txt").write_text("", encoding="utf-8")
    (execution / "stderr.txt").write_text("run failed: MultimodalError BATTLE_CONTRACT_REJECT\n", encoding="utf-8")
    assert docx_judge.judge(str(tmp_path), {})["passed"] is True
