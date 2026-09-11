"""Round-3 convergence guards (WebGPT declared converged; these lock it in).

Each case was confirmed already fail-closed; retained so it stays that way.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.pipeline import run_pipeline


def _bundle(tmp: Path, value: str):
    inp, out = tmp / "input", tmp / "output"
    (inp / "corpus").mkdir(parents=True); out.mkdir()
    (inp / "policy.json").write_text(json.dumps({
        "version": 1, "protected_values": [],
        "sensitive_values": [{"rule_id": "r", "subject_id": "s", "type": "name", "value": value}],
    }), encoding="utf-8")
    return inp, out


def test_stored_generated_column_materializing_sensitive_value_caught(tmp_path: Path) -> None:
    inp, out = _bundle(tmp_path, "secret")
    con = sqlite3.connect(inp / "corpus" / "a.sqlite")
    con.executescript("CREATE TABLE t(a TEXT,b TEXT, g TEXT GENERATED ALWAYS AS (a||b) STORED);"
                       "INSERT INTO t(a,b) VALUES('sec','ret');")
    con.commit(); con.close()
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


def test_json_root_scalar_bigint_anonymized(tmp_path: Path) -> None:
    inp, out = _bundle(tmp_path, "100000000000000000000")
    (inp / "corpus" / "c.json").write_text("100000000000000000000", encoding="utf-8")
    run_pipeline(inp, out)
    assert "100000000000000000000" not in (out / "corpus" / "c.json").read_text()


def test_duplicate_json_keys_rejected(tmp_path: Path) -> None:
    inp, out = _bundle(tmp_path, "secret")
    (inp / "corpus" / "c.json").write_text('{"x":"secret","x":"safe"}', encoding="utf-8")
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_json_numbers_rejected(tmp_path: Path, token: str) -> None:
    inp, out = _bundle(tmp_path, "Alice")
    (inp / "corpus" / "c.json").write_text('{"x": %s}' % token, encoding="utf-8")
    with pytest.raises(AnonError):
        run_pipeline(inp, out)
