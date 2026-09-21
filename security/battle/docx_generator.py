"""Retained Battle cases for native DOCX release qualification."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

POLICY = {
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

BODY = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>Contact alice@example.com today</w:t></w:r></w:p></w:body></w:document>"""


def _write_docx(
    path: Path,
    body: str = BODY,
    extra: dict[str, str] | None = None,
    *,
    comment: bytes = b"",
    member_comments: dict[str, bytes] | None = None,
) -> None:
    parts = {
        "[Content_Types].xml": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/></Types>""",
        "_rels/.rels": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/></Relationships>""",
        "word/document.xml": body,
    }
    if extra:
        parts.update(extra)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = comment
        for name, text in parts.items():
            if member_comments and name in member_comments:
                item = zipfile.ZipInfo(name)
                item.comment = member_comments[name]
                archive.writestr(item, text)
            else:
                archive.writestr(name, text)


def _case(root: Path, case_id: str, expectation: str, **kwargs: object) -> tuple[str, str, str]:
    case = root / case_id
    case.mkdir(parents=True, exist_ok=True)
    (case / "policy.json").write_text(json.dumps(POLICY, sort_keys=True), encoding="utf-8")
    _write_docx(case / "source.docx", **kwargs)
    (case / "case.json").write_text(
        json.dumps({"schema": "docx_battle_case.v1", "policy_literal_sha256": "ff8d9819fc0e12bf0d24892e45987e249a28dce836a85cad60e28eaaa8c6d976"}, sort_keys=True),
        encoding="utf-8",
    )
    return case_id, str(case), expectation


def generate(work_dir, params):
    root = Path(work_dir)
    yield _case(root, "docx-clean-redaction", "MUST_ACCEPT")
    yield _case(
        root,
        "docx-active-relationship-rejected",
        "MUST_REJECT",
        extra={
            "word/_rels/document.xml.rels": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId9\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject\" Target=\"media/data.bin\"/></Relationships>"""
        },
    )
    yield _case(root, "docx-zip-comment-literal-rejected", "MUST_REJECT", comment=b"alice@example.com")
    yield _case(
        root,
        "docx-member-name-literal-rejected",
        "MUST_REJECT",
        extra={"word/alice@example.com.xml": "<safe />"},
    )
    yield _case(
        root,
        "docx-member-comment-literal-rejected",
        "MUST_REJECT",
        member_comments={"word/document.xml": b"alice@example.com"},
    )
    yield _case(
        root,
        "docx-decoded-xml-literal-rejected",
        "MUST_REJECT",
        body="""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>alice&#64;example.com</w:t></w:r></w:p></w:body></w:document>""",
    )
    yield _case(root, "docx-malformed-xml-rejected", "MUST_REJECT", body="<w:document>")
