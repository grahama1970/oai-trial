"""Acceptance test for ticket sqlite-location-oracle (#1)."""
from __future__ import annotations

import sqlite3
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


def _corpus(tmp_path: Path) -> tuple[Path, Path]:
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    out.mkdir()
    con = sqlite3.connect(src / "db.sqlite")
    con.executescript(
        "CREATE TABLE people (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);"
        "INSERT INTO people VALUES (1, 'Alice', 30), (2, 'Bob', 40);"
    )
    con.commit()
    con.close()
    transform_file(src / "db.sqlite", out / "db.sqlite", _POLICY)
    return src, out


def test_swapped_sqlite_subject_pseudonyms_rejected(tmp_path: Path) -> None:
    src, out = _corpus(tmp_path)
    con = sqlite3.connect(out / "db.sqlite")
    rows = con.execute("SELECT id, name FROM people ORDER BY id").fetchall()
    # swap the two pseudonyms between rows: counts/integrity/FKs all still pass
    con.execute("UPDATE people SET name=? WHERE id=?", (rows[1][1], rows[0][0]))
    con.execute("UPDATE people SET name=? WHERE id=?", (rows[0][1], rows[1][0]))
    con.commit()
    con.close()
    with pytest.raises(AnonError):
        verify_corpus(src, out, _POLICY)


def test_unrelated_value_mutation_rejected(tmp_path: Path) -> None:
    src, out = _corpus(tmp_path)
    con = sqlite3.connect(out / "db.sqlite")
    con.execute("UPDATE people SET age=99 WHERE id=1")  # non-text mutation
    con.commit()
    con.close()
    with pytest.raises(AnonError):
        verify_corpus(src, out, _POLICY)


def test_clean_sqlite_run_verifies(tmp_path: Path) -> None:
    src, out = _corpus(tmp_path)
    verify_corpus(src, out, _POLICY)  # must not raise
