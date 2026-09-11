"""WebGPT hardening round 2: executable/computed SQLite schema + numeric alias.

Each case is a concrete leak path WebGPT found after round 1. All must fail
closed (or, for the numeric alias, anonymize the value).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.pipeline import run_pipeline


def _bundle(tmp: Path, policy_value: str):
    inp, out = tmp / "input", tmp / "output"
    (inp / "corpus").mkdir(parents=True)
    out.mkdir()
    (inp / "policy.json").write_text(json.dumps({
        "version": 1, "protected_values": [],
        "sensitive_values": [{"rule_id": "r", "subject_id": "s", "type": "name", "value": policy_value}],
    }), encoding="utf-8")
    return inp, out


def _sqlite(inp: Path, script: str) -> None:
    con = sqlite3.connect(inp / "corpus" / "a.sqlite")
    con.executescript(script)
    con.commit(); con.close()


def test_expression_index_rejected(tmp_path: Path) -> None:
    inp, out = _bundle(tmp_path, "SECRET")
    _sqlite(inp, "CREATE TABLE t(x TEXT); INSERT INTO t VALUES('clean'); CREATE INDEX i ON t(char(83,69,67,82,69,84));")
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


def test_nondeterministic_view_rejected(tmp_path: Path) -> None:
    inp, out = _bundle(tmp_path, "SECRET")
    _sqlite(inp, "CREATE TABLE t(x TEXT); INSERT INTO t VALUES('clean'); "
                 "CREATE VIEW v AS SELECT CASE WHEN (abs(random())%2)=0 THEN char(83,69,67,82,69,84) ELSE 'clean' END AS x;")
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


def test_computed_default_rejected(tmp_path: Path) -> None:
    inp, out = _bundle(tmp_path, "SECRET")
    _sqlite(inp, "CREATE TABLE t(x TEXT DEFAULT (char(83,69,67,82,69,84)));")
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


def test_plain_literal_default_still_accepted(tmp_path: Path) -> None:
    inp, out = _bundle(tmp_path, "Alice")
    _sqlite(inp, "CREATE TABLE t(id INTEGER PRIMARY KEY, n TEXT DEFAULT 'ok', k INTEGER DEFAULT 0); INSERT INTO t(n) VALUES('hi');")
    run_pipeline(inp, out)  # must not raise


def test_numeric_exponent_alias_anonymized(tmp_path: Path) -> None:
    inp, out = _bundle(tmp_path, "100000000000000000000")
    (inp / "corpus" / "c.json").write_text(json.dumps({"x": 1e20}), encoding="utf-8")
    run_pipeline(inp, out)
    v = json.loads((out / "corpus" / "c.json").read_text())["x"]
    assert "100000000000000000000" not in str(v), "scientific-notation alias leaked the policy value"
