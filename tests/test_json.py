"""JSON adapter tests (issue #6)."""
from __future__ import annotations

from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError, AnonErrorCode
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy


def _pol(value="Ada"):
    return compile_policy(
        {
            "version": 1,
            "sensitive_values": [{"rule_id": "r", "type": "name", "value": value}],
            "protected_values": [],
        }
    )


def test_json_string_values_transformed_numbers_preserved(tmp_path: Path):
    src = tmp_path / "a.json"
    dst = tmp_path / "out.json"
    src.write_text('{"name": "Ada", "n": 42, "ok": true, "z": null}', encoding="utf-8")
    records, count = transform_file(src, dst, _pol())
    out = dst.read_text(encoding="utf-8")
    assert "Ada" not in out
    assert '"n": 42' in out and '"ok": true' in out and '"z": null' in out
    assert count == 1 and records == 1


def test_json_duplicate_keys_rejected(tmp_path: Path):
    src = tmp_path / "a.json"
    src.write_text('{"k": 1, "k": 2}', encoding="utf-8")
    with pytest.raises(AnonError) as exc:
        transform_file(src, tmp_path / "o.json", _pol())
    assert exc.value.code == AnonErrorCode.MALFORMED_JSON


def test_json_nan_rejected(tmp_path: Path):
    src = tmp_path / "a.json"
    src.write_text('{"x": NaN}', encoding="utf-8")
    with pytest.raises(AnonError) as exc:
        transform_file(src, tmp_path / "o.json", _pol())
    assert exc.value.code == AnonErrorCode.MALFORMED_JSON


def test_json_sensitive_key_rejected(tmp_path: Path):
    src = tmp_path / "a.json"
    src.write_text('{"Ada": 1}', encoding="utf-8")
    with pytest.raises(AnonError) as exc:
        transform_file(src, tmp_path / "o.json", _pol())
    assert exc.value.code == AnonErrorCode.SENSITIVE_IN_SCHEMA


def test_json_key_order_preserved(tmp_path: Path):
    src = tmp_path / "a.json"
    dst = tmp_path / "out.json"
    src.write_text('{"b": "x", "a": "y", "c": "z"}', encoding="utf-8")
    transform_file(src, dst, _pol())
    out = dst.read_text(encoding="utf-8")
    assert out.index('"b"') < out.index('"a"') < out.index('"c"')
