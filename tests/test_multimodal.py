from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from anonymization_trial.multimodal import (
    MultimodalError,
    OCRWord,
    _matching_boxes,
    redact_document,
    verify_docx_structural_release,
    verify_pdf_structural_release,
)
from anonymization_trial.policy import compile_policy


def _policy() -> dict:
    return {
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


def test_ocr_word_sequence_matches_policy_without_persisting_value() -> None:
    policy = compile_policy(_policy())
    words = [
        OCRWord("alice", 10, 20, 40, 12),
        OCRWord("@", 50, 20, 8, 12),
        OCRWord("example.com", 58, 20, 90, 12),
    ]
    boxes, matched = _matching_boxes(words, policy)
    assert boxes == [(10, 20, 148, 32)]
    assert matched == {"email"}


def test_long_segmented_ocr_sequence_and_partial_detection() -> None:
    policy = compile_policy(_policy())
    pieces = list("alice@example.com")
    words = [OCRWord(piece, index * 10, 5, 10, 12) for index, piece in enumerate(pieces)]
    boxes, matched = _matching_boxes(words, policy)
    assert boxes == [(0, 5, len(pieces) * 10, 17)]
    assert matched == {"email"}
    assert _matching_boxes(words[:-1], policy) == ([], set())


@pytest.mark.skipif(
    not shutil.which("tesseract") or not shutil.which("pdftoppm"),
    reason="multimodal tools unavailable",
)
def test_real_image_and_pdf_redaction_paths(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    ImageFont = pytest.importorskip("PIL.ImageFont")
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not font_path.exists():
        pytest.skip("test font unavailable")
    font = ImageFont.truetype(str(font_path), 36)
    image = Image.new("RGB", (900, 160), "white")
    ImageDraw.Draw(image).text((30, 50), "Contact alice@example.com today", fill="black", font=font)
    source_image = tmp_path / "source.png"
    source_pdf = tmp_path / "source.pdf"
    image.save(source_image)
    image.save(source_pdf, "PDF", resolution=150)
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy()), encoding="utf-8")

    for source, suffix in ((source_image, ".png"), (source_pdf, ".pdf")):
        output = tmp_path / f"redacted{suffix}"
        receipt = tmp_path / f"receipt-{suffix[1:]}.json"
        result = redact_document(source, policy_path, output, receipt)
        assert result["status"] == "ready"
        assert result["redaction_boxes"] >= 1
        assert result["matched_rule_ids"] == ["email"]
        assert output.is_file()
        receipt_text = receipt.read_text(encoding="utf-8")
        assert "alice@example.com" not in receipt_text
        report = json.loads(receipt_text)
        assert report["verification_passed"] is True
        if suffix == ".pdf":
            assert report["structural_verification"] == {
                "extractable_text_absent": True,
                "forbidden_structures_absent": True,
                "sensitive_metadata_absent": True,
            }
            tampered = tmp_path / "tampered.pdf"
            tampered.write_bytes(output.read_bytes() + b"\n/EmbeddedFiles\n")
            with pytest.raises(
                MultimodalError, match="MULTIMODAL_PDF_STRUCTURAL_VERIFICATION_FAILED"
            ):
                verify_pdf_structural_release(tampered)


def _write_docx(
    path: Path,
    body_xml: str,
    extra: dict[str, str] | None = None,
    *,
    archive_comment: bytes = b"",
    member_comments: dict[str, bytes] | None = None,
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
        "word/document.xml": body_xml,
    }
    if extra:
        parts.update(extra)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = archive_comment
        for name, data in parts.items():
            if member_comments and name in member_comments:
                item = zipfile.ZipInfo(name)
                item.comment = member_comments[name]
                archive.writestr(item, data)
            else:
                archive.writestr(name, data)


def test_native_docx_redaction_is_offline_verified_and_private(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    _write_docx(
        source,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>Contact alice@example.com today</w:t></w:r></w:p></w:body></w:document>""",
    )
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy()), encoding="utf-8")
    output = tmp_path / "redacted.docx"
    receipt = tmp_path / "receipt.json"

    result = redact_document(source, policy_path, output, receipt)

    assert result["status"] == "ready"
    assert result["redaction_boxes"] == 1
    assert result["matched_rule_ids"] == ["email"]
    assert result["structural_verification"]["policy_literals_absent"] is True
    assert result["structural_verification"]["required_parts_present"] is True
    assert result["structural_verification"]["office_document_relationship_valid"] is True
    assert result["structural_verification"]["main_document_xml_valid"] is True
    assert "alice@example.com" not in receipt.read_text(encoding="utf-8")
    with zipfile.ZipFile(output) as archive:
        assert "alice@example.com" not in b"".join(archive.read(name) for name in archive.namelist()).decode("utf-8", errors="ignore")
    assert verify_docx_structural_release(output, compile_policy(_policy()))["policy_literals_absent"] is True


def test_docx_structural_verifier_rejects_active_relationships_and_content_types(tmp_path: Path) -> None:
    policy = compile_policy(_policy())
    rel_active = tmp_path / "rel-active.docx"
    _write_docx(
        rel_active,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>safe</w:t></w:r></w:p></w:body></w:document>""",
        {
            "word/_rels/document.xml.rels": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId9\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject\" Target=\"media/data.bin\"/></Relationships>"""
        },
    )
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED"):
        verify_docx_structural_release(rel_active, policy)

    content_type_active = tmp_path / "content-type-active.docx"
    _write_docx(
        content_type_active,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>safe</w:t></w:r></w:p></w:body></w:document>""",
        {
            "[Content_Types].xml": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/><Override PartName=\"/word/hidden.bin\" ContentType=\"application/vnd.ms-office.vbaProject\"/></Types>"""
        },
    )
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED"):
        verify_docx_structural_release(content_type_active, policy)


def test_docx_verifier_rejects_policy_literals_in_zip_metadata_and_decoded_xml(tmp_path: Path) -> None:
    policy = compile_policy(_policy())
    metadata = tmp_path / "metadata.docx"
    _write_docx(
        metadata,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>safe</w:t></w:r></w:p></w:body></w:document>""",
        archive_comment=b"alice@example.com",
    )
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED"):
        verify_docx_structural_release(metadata, policy)

    member_comment = tmp_path / "member-comment.docx"
    _write_docx(
        member_comment,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>safe</w:t></w:r></w:p></w:body></w:document>""",
        member_comments={"word/document.xml": b"alice@example.com"},
    )
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED"):
        verify_docx_structural_release(member_comment, policy)

    member_name = tmp_path / "member-name.docx"
    _write_docx(
        member_name,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>safe</w:t></w:r></w:p></w:body></w:document>""",
        {"word/alice@example.com.xml": "<safe />"},
    )
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED"):
        verify_docx_structural_release(member_name, policy)

    decoded = tmp_path / "decoded.docx"
    _write_docx(
        decoded,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>alice&#64;example.com</w:t></w:r></w:p></w:body></w:document>""",
    )
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED"):
        verify_docx_structural_release(decoded, policy)

    invalid = tmp_path / "invalid.docx"
    _write_docx(invalid, "<w:document>")
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_XML_INVALID"):
        verify_docx_structural_release(invalid, policy)


def test_docx_verifier_requires_minimal_valid_office_package(tmp_path: Path) -> None:
    policy = compile_policy(_policy())
    missing_relationship = tmp_path / "missing-relationship.docx"
    _write_docx(
        missing_relationship,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>safe</w:t></w:r></w:p></w:body></w:document>""",
        {"_rels/.rels": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"/>"""},
    )
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED"):
        verify_docx_structural_release(missing_relationship, policy)

    no_body = tmp_path / "no-body.docx"
    _write_docx(
        no_body,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>""",
    )
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_STRUCTURAL_VERIFICATION_FAILED"):
        verify_docx_structural_release(no_body, policy)


def test_native_docx_rejects_active_content_and_cli_writes_private_receipt(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    _write_docx(
        source,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>alice@example.com</w:t></w:r></w:p></w:body></w:document>""",
        {"word/vbaProject.bin": "macro"},
    )
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy()), encoding="utf-8")
    with pytest.raises(MultimodalError, match="MULTIMODAL_DOCX_UNSUPPORTED_ACTIVE_CONTENT"):
        redact_document(source, policy_path, tmp_path / "out.docx", tmp_path / "receipt.json")

    clean = tmp_path / "clean.docx"
    _write_docx(clean, zipfile.ZipFile(source).read("word/document.xml").decode("utf-8"))
    completed = subprocess.run(  # noqa: S603 - fixed project CLI argv
        [
            ".venv/bin/anonymization-trial",
            "redact-document",
            "--input",
            str(clean),
            "--policy",
            str(policy_path),
            "--output",
            str(tmp_path / "cli.docx"),
            "--receipt",
            str(tmp_path / "cli-receipt.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout)["structural_verification"]["policy_literals_absent"] is True
    assert (tmp_path / "cli-receipt.json").stat().st_mode & 0o777 == 0o600
