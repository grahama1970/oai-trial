"""Acceptance test for round-6 ticket typed-scalar-verifier."""
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
    "sensitive_values": [{"rule_id": "a", "subject_id": "s", "type": "name", "value": "Alice"}],
})


def test_json_bool_number_and_sqlite_integer_real_mutations_rejected(tmp_path: Path) -> None:
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    out.mkdir()
    # JSON: true mutated to 1 must be rejected (True == 1 in Python)
    (src / "a.json").write_text('{"flag": true}', encoding="utf-8")
    transform_file(src / "a.json", out / "a.json", _POLICY)
    (out / "a.json").write_text('{"flag": 1}', encoding="utf-8")
    with pytest.raises(AnonError):
        verify_corpus(src, out, _POLICY)
    # restore clean output for the sqlite half
    transform_file(src / "a.json", out / "a.json", _POLICY)

    # SQLite: INTEGER 1 mutated to REAL 1.0 must be rejected (1 == 1.0 in Python)
    # column n has NO declared type (BLOB affinity), so a REAL 1.0 stays REAL
    # instead of being coerced back to INTEGER by column affinity
    con = sqlite3.connect(src / "db.sqlite")
    con.executescript(
        "CREATE TABLE t (id INTEGER PRIMARY KEY, n);"
        "INSERT INTO t VALUES (1, 1);"
    )
    con.commit()
    con.close()
    transform_file(src / "db.sqlite", out / "db.sqlite", _POLICY)
    con = sqlite3.connect(out / "db.sqlite")
    con.execute("UPDATE t SET n = 1.0 WHERE id = 1")
    con.commit()
    con.close()
    with pytest.raises(AnonError):
        verify_corpus(src, out, _POLICY)


def test_clean_typed_run_verifies(tmp_path: Path) -> None:
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    out.mkdir()
    (src / "a.json").write_text('{"flag": true, "n": 1, "x": 1.5, "who": "Alice"}', encoding="utf-8")
    transform_file(src / "a.json", out / "a.json", _POLICY)
    verify_corpus(src, out, _POLICY)  # must not raise
