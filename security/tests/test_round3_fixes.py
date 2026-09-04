"""Regression tests for WebGPT review round-3 fixes (#2, #5, #14)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.formats import iter_searchable_text, transform_file
from anonymization_trial.policy import compile_policy

_NAME = {
    "version": 1,
    "protected_values": [],
    "sensitive_values": [{"rule_id": "a", "subject_id": "s", "type": "name", "value": "Alice"}],
}


def test_missing_sensitive_values_rejected() -> None:  # review #2 (round3)
    with pytest.raises(AnonError):
        compile_policy({"version": 1, "protected_values": []})


def test_missing_protected_values_rejected() -> None:  # review #2 (round3)
    with pytest.raises(AnonError):
        compile_policy({"version": 1, "sensitive_values": []})


def test_json_bom_is_stripped_by_searcher(tmp_path: Path) -> None:  # review #5 (round3)
    src = tmp_path / "a.json"
    src.write_text("\ufeff" + '{"who": "Alice"}', encoding="utf-8")
    out = tmp_path / "o.json"
    transform_file(src, out, compile_policy(_NAME))
    assert all("Alice" not in s for s in iter_searchable_text(out))


def _db(path: Path, script: str) -> None:
    con = sqlite3.connect(path)
    con.executescript(script)
    con.commit()
    con.close()


def test_sqlite_trigger_rejected(tmp_path: Path) -> None:  # review #14 (round3)
    src = tmp_path / "a.sqlite"
    _db(
        src,
        "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT);"
        "CREATE TABLE log (n TEXT);"
        "CREATE TRIGGER tr AFTER UPDATE ON t BEGIN INSERT INTO log VALUES ('x'); END;"
        "INSERT INTO t VALUES (1, 'Alice');",
    )
    with pytest.raises(AnonError):
        transform_file(src, tmp_path / "o.sqlite", compile_policy(_NAME))


def test_sqlite_rowid_shadow_rejected(tmp_path: Path) -> None:  # review #14 (round3)
    src = tmp_path / "a.sqlite"
    _db(src, "CREATE TABLE t (rowid INTEGER, name TEXT); INSERT INTO t VALUES (5, 'Alice');")
    with pytest.raises(AnonError):
        transform_file(src, tmp_path / "o.sqlite", compile_policy(_NAME))
