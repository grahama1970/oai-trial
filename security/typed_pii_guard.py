"""Fail-before-fix guard for the typed-PII disqualifier (2026-09-11).

The client's corpus stored a phone as a JSON integer / SQLite INTEGER.
The string-only matcher passed it through untouched, and the
string-only verifier could not see it either. This guard builds a
corpus carrying the SAME sensitive value in every JSON/SQLite scalar
representation, runs the REAL pipeline, and asserts the value is absent
from every output regardless of type.

Exit 0 only when no representation leaks. On the frozen runtime this
MUST exit non-zero (the integer/float phone survives) — that failure is
the retained proof the fix is real.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

from anonymization_trial.pipeline import run_pipeline

PHONE = "5551234567"  # policy literal; appears as string AND as int/real in corpus


def _write_inputs(root: Path) -> None:
    (root / "corpus").mkdir(parents=True)
    policy = {
        "version": 1,
        "protected_values": [],
        "sensitive_values": [
            {"rule_id": "p", "subject_id": "s", "type": "phone", "value": PHONE}
        ],
    }
    (root / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
    # JSON: same phone as string, integer, and float
    (root / "corpus" / "people.json").write_text(
        json.dumps(
            {
                "as_string": PHONE,
                "as_integer": int(PHONE),
                "as_float": float(PHONE),
            }
        ),
        encoding="utf-8",
    )
    # SQLite: same phone as TEXT and as INTEGER
    con = sqlite3.connect(root / "corpus" / "accounts.sqlite")
    con.executescript(
        "CREATE TABLE t (id INTEGER PRIMARY KEY, phone_text TEXT, phone_int INTEGER);"
        f"INSERT INTO t VALUES (1, '{PHONE}', {int(PHONE)});"
    )
    con.commit()
    con.close()


def _output_carries_phone(out: Path) -> list[str]:
    leaks: list[str] = []
    j = json.loads((out / "corpus" / "people.json").read_text())
    for key, val in j.items():
        # stringify EVERY scalar independently (the verifier's original blind spot)
        if PHONE in str(val):
            leaks.append(f"people.json[{key}]={val!r}")
    con = sqlite3.connect(out / "corpus" / "accounts.sqlite")
    for row in con.execute("SELECT phone_text, phone_int FROM t"):
        for col, val in zip(("phone_text", "phone_int"), row):
            if PHONE in str(val):
                leaks.append(f"accounts.t.{col}={val!r}")
    con.close()
    return leaks


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        inp, outp = base / "input", base / "output"
        inp.mkdir()
        outp.mkdir()
        _write_inputs(inp)
        try:
            run_pipeline(inp, outp)
        except Exception as exc:  # a fail-closed rejection is an ACCEPTABLE outcome
            print(f"pipeline rejected the corpus (fail-closed): {exc}")
            return 0
        leaks = _output_carries_phone(outp)
    if leaks:
        print("TYPED_PII_LEAK: sensitive phone survived in output as:")
        for leak in leaks:
            print(f"  - {leak}")
        return 1
    print("OK: no representation of the sensitive phone reached the output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
