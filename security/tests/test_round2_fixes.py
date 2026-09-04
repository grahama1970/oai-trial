"""Regression tests for WebGPT review round-2 fixes."""
from __future__ import annotations

from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy
from anonymization_trial.verification import verify_corpus

_EMPTY = {"version": 1, "sensitive_values": [], "protected_values": []}
_NAME = compile_policy({
    "version": 1,
    "protected_values": [],
    "sensitive_values": [{"rule_id": "a", "subject_id": "alice", "type": "name", "value": "Alice"}],
})


def test_lossy_float_rejected(tmp_path: Path) -> None:  # round2 #6
    src = tmp_path / "a.json"
    src.write_text('{"n": 9007199254740993.0}', encoding="utf-8")
    with pytest.raises(AnonError):
        transform_file(src, tmp_path / "o.json", compile_policy(_EMPTY))


def test_exact_float_still_allowed(tmp_path: Path) -> None:  # round2 #6 (no false positive)
    src = tmp_path / "a.json"
    src.write_text('{"a": 0.1, "b": 1.5, "c": 100.0}', encoding="utf-8")
    transform_file(src, tmp_path / "o.json", compile_policy(_EMPTY))  # must not raise


def test_verifier_rejects_duplicate_output_keys(tmp_path: Path) -> None:  # round2 #3
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    out.mkdir()
    (src / "a.json").write_text('{"who": "Alice"}', encoding="utf-8")
    transform_file(src / "a.json", out / "a.json", _NAME)
    pseudo = (out / "a.json").read_text(encoding="utf-8")
    # rebuild output with a duplicate key hiding the raw sensitive value first
    (out / "a.json").write_text('{"who": "Alice", "who": ' + pseudo.split(":", 1)[1], encoding="utf-8")
    with pytest.raises(AnonError):
        verify_corpus(src, out, _NAME)


def test_partial_boundary_overlap_rejected() -> None:  # review #8
    with pytest.raises(AnonError):
        compile_policy({
            "version": 1,
            "sensitive_values": [{"rule_id": "r", "subject_id": "s", "type": "name", "value": "abcP"}],
            "protected_values": [{"value": "Person-"}],
        })
