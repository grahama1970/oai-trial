"""Acceptance test for ticket csv-dialect-failclosed (#4)."""
from __future__ import annotations

from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy

_POLICY = compile_policy({
    "version": 1,
    "protected_values": [],
    "sensitive_values": [{"rule_id": "a", "subject_id": "s", "type": "name", "value": "Alice"}],
})


def test_semicolon_csv_is_rejected_not_silently_reinterpreted(tmp_path: Path) -> None:
    src = tmp_path / "a.csv"
    src.write_text("name;city\nAlice;NYC\n", encoding="utf-8")
    with pytest.raises(AnonError):
        transform_file(src, tmp_path / "o.csv", _POLICY)


def test_comma_csv_multi_column_still_accepted(tmp_path: Path) -> None:
    src = tmp_path / "a.csv"
    src.write_text("name,city\nAlice,NYC\n", encoding="utf-8")
    transform_file(src, tmp_path / "o.csv", _POLICY)  # must not raise


def test_single_column_comma_csv_still_accepted(tmp_path: Path) -> None:
    src = tmp_path / "a.csv"
    src.write_text("name\nAlice\n", encoding="utf-8")
    transform_file(src, tmp_path / "o.csv", _POLICY)  # must not raise
