"""Location-aware verifier tests for WebGPT review #1/#2.

The verifier must reject a staged corpus where pseudonyms are swapped between
subjects, a row is dropped, or a sensitive value hides in escaped JSON — cases
that aggregate presence/count checks pass.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy
from anonymization_trial.verification import verify_corpus

_POLICY = compile_policy({
    "version": 1,
    "protected_values": [],
    "sensitive_values": [
        {"rule_id": "a", "subject_id": "alice", "type": "name", "value": "Alice"},
        {"rule_id": "b", "subject_id": "bob", "type": "name", "value": "Bob"},
    ],
})


def _stage(tmp_path: Path, name: str, content: str) -> tuple[Path, Path]:
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()
    (src / name).write_text(content, encoding="utf-8")
    transform_file(src / name, out / name, _POLICY)
    return src, out


def test_swapped_pseudonyms_in_csv_rejected(tmp_path: Path) -> None:  # review#1
    src, out = _stage(tmp_path, "people.csv", "name\nAlice\nBob\n")
    rows = list(csv.reader((out / "people.csv").open(newline="", encoding="utf-8")))
    rows[1][0], rows[2][0] = rows[2][0], rows[1][0]
    with (out / "people.csv").open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    with pytest.raises(AnonError):
        verify_corpus(src, out, _POLICY)


def test_dropped_csv_row_rejected(tmp_path: Path) -> None:  # review#1
    src, out = _stage(tmp_path, "people.csv", "name\nAlice\nBob\n")
    text = (out / "people.csv").read_text(encoding="utf-8").splitlines()
    (out / "people.csv").write_text("\n".join(text[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(AnonError):
        verify_corpus(src, out, _POLICY)


def test_escaped_json_sensitive_value_rejected(tmp_path: Path) -> None:  # review#2
    src, out = _stage(tmp_path, "a.json", '{"who": "Alice"}')
    (out / "a.json").write_text('{"who": "\\u0041lice"}', encoding="utf-8")
    with pytest.raises(AnonError):
        verify_corpus(src, out, _POLICY)


def test_clean_run_still_verifies(tmp_path: Path) -> None:
    src, out = _stage(tmp_path, "a.json", '{"who": "Alice", "n": 1}')
    verify_corpus(src, out, _POLICY)
    assert json.loads((out / "a.json").read_text())["who"] != "Alice"
