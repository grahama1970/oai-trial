"""SAST (bandit B608) flags the f-string SQL in formats.py/verification.py.
This proves those are false positives: identifiers are quoted via _quote (which
doubles embedded quotes) and values use bound parameters, so a malicious table
name cannot inject SQL. WebGPT hardening audit #9.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from anonymization_trial.pipeline import run_pipeline


def test_malicious_table_name_cannot_inject_sql(tmp_path: Path) -> None:
    inp, out = tmp_path / "input", tmp_path / "output"
    (inp / "corpus").mkdir(parents=True)
    out.mkdir()
    (inp / "policy.json").write_text(json.dumps({
        "version": 1, "protected_values": [],
        "sensitive_values": [{"rule_id": "r", "subject_id": "s", "type": "name", "value": "Alice"}],
    }), encoding="utf-8")
    con = sqlite3.connect(inp / "corpus" / "a.sqlite")
    con.execute('CREATE TABLE "weird""; DROP TABLE victim; --" (name TEXT)')
    con.execute('CREATE TABLE victim (x TEXT)')
    con.execute('INSERT INTO "weird""; DROP TABLE victim; --" VALUES(?)', ("Alice",))
    con.commit(); con.close()

    run_pipeline(inp, out)

    o = sqlite3.connect(out / "corpus" / "a.sqlite")
    tables = {r[0] for r in o.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    o.close()
    assert "victim" in tables, "SQL injection via table name dropped a table"
