"""The acceptance check is DERIVED FROM policy.json, and its result DEPENDS on it.

Three proofs, all against the real pipeline:
1. A clean anonymized output passes the spec-derived check.
2. A leak (sensitive value surviving in ANY representation) fails it.
3. Dependency probe: the SAME output checked against a DIFFERENT policy value
   that IS present flips the result to fail -- proving the check reads
   policy.json, not a hand-authored list. If this probe ever passes regardless
   of the policy, the check has been gamed.
"""
from __future__ import annotations

import json
import subprocess
import sqlite3
import sys
import tempfile
from pathlib import Path

from anonymization_trial.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts" / "spec_derived_check.py"
PHONE = "5551234567"


def _bundle(tmp: Path) -> tuple[Path, Path]:
    inp, out = tmp / "input", tmp / "output"
    (inp / "corpus").mkdir(parents=True)
    out.mkdir()
    (inp / "policy.json").write_text(json.dumps({
        "version": 1, "protected_values": [],
        "sensitive_values": [{"rule_id": "p", "subject_id": "s", "type": "phone", "value": PHONE}],
    }), encoding="utf-8")
    (inp / "corpus" / "people.json").write_text(
        json.dumps({"as_string": PHONE, "as_integer": int(PHONE)}), encoding="utf-8")
    con = sqlite3.connect(inp / "corpus" / "accounts.sqlite")
    con.executescript(f"CREATE TABLE t(id INTEGER PRIMARY KEY, phone_int INTEGER); INSERT INTO t VALUES(1, {int(PHONE)});")
    con.commit(); con.close()
    return inp, out


def _check(policy: Path, corpus: Path) -> int:
    return subprocess.run([sys.executable, str(CHECK), "--policy", str(policy), "--corpus", str(corpus)]).returncode


def test_clean_output_passes_and_leak_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        inp, out = _bundle(tmp)
        run_pipeline(inp, out)
        # 1. clean anonymized output passes
        assert _check(inp / "policy.json", out / "corpus") == 0
        # 2. the raw INPUT (integer phone present) fails the same check
        assert _check(inp / "policy.json", inp / "corpus") == 1


def test_dependency_probe_result_depends_on_policy() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        inp, out = _bundle(tmp)
        run_pipeline(inp, out)
        assert _check(inp / "policy.json", out / "corpus") == 0  # clean vs real policy
        # flip the policy to a value that IS present in the output (the pseudonym
        # prefix "Person-" the anonymizer wrote). The check MUST now fail,
        # proving it reads policy.json rather than a fixed list.
        released = (out / "corpus" / "people.json").read_text()
        present_token = json.loads(released)["as_string"]  # the pseudonym actually written
        alt_policy = tmp / "alt_policy.json"
        alt_policy.write_text(json.dumps({
            "version": 1, "protected_values": [],
            "sensitive_values": [{"rule_id": "x", "subject_id": "s", "type": "phone", "value": present_token}],
        }), encoding="utf-8")
        assert _check(alt_policy, out / "corpus") == 1, "dependency probe: result did not depend on policy.json"
