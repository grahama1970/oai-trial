"""Text and CSV adapter tests (issue #5)."""
from __future__ import annotations

from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError, AnonErrorCode
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy

_BOM = b"\xef\xbb\xbf"


def _pol(value="Ada", data_type="name"):
    return compile_policy(
        {
            "version": 1,
            "sensitive_values": [{"rule_id": "r", "type": data_type, "value": value}],
            "protected_values": [],
        }
    )


def test_text_bom_preserved_and_replaced(tmp_path: Path):
    src = tmp_path / "a.txt"
    dst = tmp_path / "out.txt"
    src.write_bytes(_BOM + b"Hi Ada\n")
    records, count = transform_file(src, dst, _pol())
    out = dst.read_bytes()
    assert out.startswith(_BOM)
    assert b"Ada" not in out
    assert count == 1 and records == 1


def test_text_malformed_utf8_rejected(tmp_path: Path):
    src = tmp_path / "a.txt"
    src.write_bytes(b"\xff\xfe not utf8")
    with pytest.raises(AnonError) as exc:
        transform_file(src, tmp_path / "out.txt", _pol())
    assert exc.value.code == AnonErrorCode.MALFORMED_ENCODING


def test_csv_sensitive_header_rejected(tmp_path: Path):
    src = tmp_path / "a.csv"
    src.write_text("id,Ada\n1,x\n", encoding="utf-8")
    with pytest.raises(AnonError) as exc:
        transform_file(src, tmp_path / "out.csv", _pol())
    assert exc.value.code == AnonErrorCode.SENSITIVE_IN_SCHEMA


def test_csv_data_transformed_header_preserved(tmp_path: Path):
    src = tmp_path / "a.csv"
    dst = tmp_path / "out.csv"
    src.write_text("id,name\n1,Ada\n2,Bob\n", encoding="utf-8")
    records, count = transform_file(src, dst, _pol())
    out = dst.read_text(encoding="utf-8")
    assert out.startswith("id,name")
    assert "Ada" not in out
    assert records == 2 and count == 1


def test_csv_crlf_preserved(tmp_path: Path):
    src = tmp_path / "a.csv"
    dst = tmp_path / "out.csv"
    src.write_bytes(b"id,name\r\n1,Ada\r\n")
    transform_file(src, dst, _pol())
    assert b"\r\n" in dst.read_bytes()
