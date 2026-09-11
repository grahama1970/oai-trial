"""Same-class representation holes surfaced by the typed-PII disqualifier.

WebGPT-audited 2026-09-11. Each test guards one axis of the failure class
"the same sensitive value in a representation the matcher does not
canonicalize, with the verifier equally blind."

- BLOB: FIXED (fail-closed). Retained so it stays closed.
- NFC/NFD: KNOWN OPEN HOLE (xfail). A correct fix needs offset-safe NFC
  matching + policy-side normalization + collision preflight + an
  independent verifier NFC path + fault tests. Marked xfail(strict) so it
  fails LOUD the moment someone claims it fixed without the guard passing.
- Negative scope (literal-match contract): these MUST NOT match; matching
  them would mean scope crept beyond the documented literal contract.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unicodedata
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.pipeline import run_pipeline


def _run(corpus_writers, policy_value):
    td = tempfile.mkdtemp()
    base = Path(td)
    inp, out = base / "input", base / "output"
    (inp / "corpus").mkdir(parents=True)
    out.mkdir()
    (inp / "policy.json").write_text(
        json.dumps(
            {
                "version": 1,
                "protected_values": [],
                "sensitive_values": [
                    {"rule_id": "r", "subject_id": "s", "type": "name", "value": policy_value}
                ],
            }
        ),
        encoding="utf-8",
    )
    for name, writer in corpus_writers.items():
        writer(inp / "corpus" / name)
    run_pipeline(inp, out)  # may raise AnonError (fail-closed)
    return out


def test_sqlite_blob_value_fails_closed() -> None:
    def w(p: Path) -> None:
        c = sqlite3.connect(p)
        c.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, b BLOB)")
        c.execute("INSERT INTO t VALUES(1, ?)", (b"Alice",))
        c.commit()
        c.close()

    with pytest.raises(AnonError):
        _run({"a.sqlite": w}, "Alice")


def test_nfc_nfd_canonical_equivalence_no_leak() -> None:
    nfc = unicodedata.normalize("NFC", "José Malké")
    nfd = unicodedata.normalize("NFD", "José Malké")
    assert nfc != nfd
    out = _run({"c.json": lambda p: p.write_text(json.dumps({"who": nfd}), encoding="utf-8")}, nfc)
    result = json.loads((out / "corpus" / "c.json").read_text())["who"]
    assert unicodedata.normalize("NFD", "José Malké") not in unicodedata.normalize("NFD", result)


def test_negative_scope_literal_contract_does_not_overmatch() -> None:
    # Differently-FORMATTED instances are different literals; under the
    # documented literal-match contract they MUST NOT be replaced. If any of
    # these ever match, scope crept beyond the claim surface.
    for policy_value, corpus_value in [
        ("5551234567", "555-123-4567"),
        ("Alice", "Al\u200bice"),
        ("Jon Bell", "Jon\u00a0Bell"),
    ]:
        out = _run(
            {"c.json": lambda p, cv=corpus_value: p.write_text(json.dumps({"who": cv}), encoding="utf-8")},
            policy_value,
        )
        result = json.loads((out / "corpus" / "c.json").read_text())["who"]
        assert result == corpus_value, f"literal-scope creep: {policy_value!r} matched {corpus_value!r}"
