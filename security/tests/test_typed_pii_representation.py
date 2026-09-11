"""Retained regression for the typed-PII disqualifier (2026-09-11).

Client feedback: a phone stored as a JSON/SQLite integer passed through
untouched because the matcher and the verifier were string-only. This
test asserts the same sensitive value is anonymized in EVERY scalar
representation. It fails against the frozen string-only runtime and
passes only with value-scoped matching + a value-scoped verifier.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from anonymization_trial.pipeline import run_pipeline

PHONE = "5551234567"


def _policy():
    return {
        "version": 1,
        "protected_values": [],
        "sensitive_values": [
            {"rule_id": "p", "subject_id": "s", "type": "phone", "value": PHONE}
        ],
    }


def test_sensitive_value_anonymized_in_every_json_and_sqlite_representation(tmp_path: Path) -> None:
    inp, out = tmp_path / "input", tmp_path / "output"
    (inp / "corpus").mkdir(parents=True)
    out.mkdir()
    (inp / "policy.json").write_text(json.dumps(_policy()), encoding="utf-8")
    (inp / "corpus" / "people.json").write_text(
        json.dumps({"s": PHONE, "i": int(PHONE), "f": float(PHONE)}), encoding="utf-8"
    )
    con = sqlite3.connect(inp / "corpus" / "accounts.sqlite")
    con.executescript(
        "CREATE TABLE t (id INTEGER PRIMARY KEY, phone_text TEXT, phone_int INTEGER);"
        f"INSERT INTO t VALUES (1, '{PHONE}', {int(PHONE)});"
    )
    con.commit()
    con.close()

    run_pipeline(inp, out)  # must not raise: valid output is produced

    j = json.loads((out / "corpus" / "people.json").read_text())
    for key, val in j.items():
        assert PHONE not in str(val), f"phone leaked in people.json[{key}]={val!r}"
    con = sqlite3.connect(out / "corpus" / "accounts.sqlite")
    for row in con.execute("SELECT phone_text, phone_int FROM t"):
        for col, val in zip(("phone_text", "phone_int"), row):
            assert PHONE not in str(val), f"phone leaked in accounts.t.{col}={val!r}"
    con.close()
