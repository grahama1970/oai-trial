"""Acceptance tests for round-5 tickets sqlite-schema-literal-leak and
error-path-redaction."""
from __future__ import annotations

import sqlite3
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


def test_sensitive_literal_in_view_sql_is_rejected(tmp_path: Path) -> None:  # round5 #1
    src = tmp_path / "a.sqlite"
    con = sqlite3.connect(src)
    con.executescript(
        "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT);"
        "INSERT INTO t VALUES (1, 'Alice');"
        "CREATE VIEW leaked AS SELECT 'Alice' AS name;"
    )
    con.commit()
    con.close()
    with pytest.raises(AnonError):
        transform_file(src, tmp_path / "o.sqlite", _POLICY)


def test_clean_view_still_accepted(tmp_path: Path) -> None:
    src = tmp_path / "a.sqlite"
    con = sqlite3.connect(src)
    con.executescript(
        "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT);"
        "INSERT INTO t VALUES (1, 'Alice');"
        "CREATE VIEW ok AS SELECT id FROM t;"
    )
    con.commit()
    con.close()
    transform_file(src, tmp_path / "o.sqlite", _POLICY)  # must not raise


def test_hostile_filenames_never_appear_in_error_text(tmp_path: Path) -> None:  # round5 #4
    from anonymization_trial.pipeline import run_pipeline

    hostile = "Alice-secret"
    inp = tmp_path / "in"
    (inp / "corpus").mkdir(parents=True)
    (inp / "policy.json").write_text(
        '{"version":1,"sensitive_values":[],"protected_values":[]}', encoding="utf-8"
    )
    # unsupported suffix carrying hostile material must not be echoed in error text
    (inp / "corpus" / f"x.{hostile}").write_text("data", encoding="utf-8")
    with pytest.raises(AnonError) as exc:
        run_pipeline(inp, tmp_path / "out")
    assert hostile not in str(exc.value)
