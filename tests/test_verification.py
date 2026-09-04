"""Independent verifier tests (issue #8)."""
from __future__ import annotations

from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError, AnonErrorCode
from anonymization_trial.policy import compile_policy
from anonymization_trial.verification import verify_corpus


def _pol():
    return compile_policy(
        {
            "version": 1,
            "sensitive_values": [{"rule_id": "r", "type": "name", "value": "Ada"}],
            "protected_values": [{"value": "Northwind"}],
        }
    )


def _corpus(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (root / name).write_text(content, encoding="utf-8")
    return root


def test_verify_passes_on_clean_output(tmp_path: Path):
    src = _corpus(tmp_path / "src", {"a.txt": "Ada at Northwind\n"})
    out = _corpus(tmp_path / "out", {"a.txt": "Person-x at Northwind\n"})
    verify_corpus(src, out, _pol())  # no raise


def test_verify_catches_surviving_literal(tmp_path: Path):
    src = _corpus(tmp_path / "src", {"a.txt": "Ada\n"})
    out = _corpus(tmp_path / "out", {"a.txt": "Ada\n"})  # not anonymized
    with pytest.raises(AnonError) as exc:
        verify_corpus(src, out, _pol())
    assert exc.value.code == AnonErrorCode.VERIFICATION_FAILED


def test_verify_catches_file_set_mismatch(tmp_path: Path):
    src = _corpus(tmp_path / "src", {"a.txt": "x\n", "b.txt": "y\n"})
    out = _corpus(tmp_path / "out", {"a.txt": "x\n"})
    with pytest.raises(AnonError) as exc:
        verify_corpus(src, out, _pol())
    assert exc.value.code == AnonErrorCode.VERIFICATION_FAILED


def test_verify_catches_protected_count_change(tmp_path: Path):
    src = _corpus(tmp_path / "src", {"a.txt": "Northwind once\n"})
    out = _corpus(tmp_path / "out", {"a.txt": "Northwind Northwind\n"})  # duplicated protected
    with pytest.raises(AnonError) as exc:
        verify_corpus(src, out, _pol())
    assert exc.value.code == AnonErrorCode.VERIFICATION_FAILED
