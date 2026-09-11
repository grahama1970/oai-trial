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


def test_sqlite_schema_literal_in_check_caught(tmp_path: Path) -> None:
    # A policy literal in a CHECK clause lives in the released schema DDL.
    # Both the transform schema-scan and the independent verifier must catch it.
    inp, out = _bundle(tmp_path, "5551234567")
    con = sqlite3.connect(inp / "corpus" / "a.sqlite")
    con.executescript("CREATE TABLE b(x TEXT, CHECK (x <> '5551234567')); INSERT INTO b(x) VALUES('safe');")
    con.commit(); con.close()
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


def test_sqlite_header_field_carrying_sensitive_value_rejected(tmp_path: Path) -> None:
    # user_version/application_id persist attacker integers outside any table.
    inp, out = _bundle(tmp_path, "123456789")
    con = sqlite3.connect(inp / "corpus" / "a.sqlite")
    con.executescript("CREATE TABLE h(x TEXT); INSERT INTO h VALUES('safe'); PRAGMA user_version=123456789;")
    con.commit(); con.close()
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


def test_schema_version_cookie_not_leaked_via_vacuum(tmp_path: Path) -> None:
    # S-1 -> VACUUM -> S attack: our backup-to-fresh-DB snapshot never copies the
    # source cookie, and schema_version is a scanned header field regardless.
    inp, out = _bundle(tmp_path, "123456789")
    con = sqlite3.connect(inp / "corpus" / "a.sqlite")
    con.executescript("CREATE TABLE t(v TEXT); INSERT INTO t VALUES('123456789'); PRAGMA schema_version=123456788;")
    con.commit(); con.close()
    run_pipeline(inp, out)  # table value anonymized; header cookie must not be the sensitive value
    raw = (out / "corpus" / "a.sqlite").read_bytes()
    assert int.from_bytes(raw[40:44], "big") != 123456789
    assert b"123456789" not in raw


def test_sqlite_page_size_as_sensitive_value_rejected(tmp_path: Path) -> None:
    # page_size (bytes 16-17) is source-selected and copied by backup().
    inp, out = _bundle(tmp_path, "8192")
    con = sqlite3.connect(inp / "corpus" / "a.sqlite")
    con.execute("PRAGMA page_size=8192"); con.execute("VACUUM")
    con.execute("CREATE TABLE t(x TEXT)"); con.execute("INSERT INTO t VALUES('benign')")
    con.commit(); con.close()
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


def test_all_sqlite_header_integers_scanned(tmp_path: Path) -> None:
    # Any policy numeric value colliding with ANY header integer (incl the
    # incremental-vacuum flag / encoding / structural counters) fails closed.
    inp, out = _bundle(tmp_path, "1")
    con = sqlite3.connect(inp / "corpus" / "a.sqlite")
    con.execute("PRAGMA auto_vacuum=INCREMENTAL")
    con.execute("CREATE TABLE t(x TEXT)"); con.execute("INSERT INTO t VALUES('benign')")
    con.commit(); con.close()
    with pytest.raises(AnonError):
        run_pipeline(inp, out)


def test_sqlite_header_payload_fraction_constants_scanned(tmp_path: Path) -> None:
    # Offsets 21-23 are mandatory format constants 64,32,32; a policy value equal
    # to one fails closed (degenerate, safe).
    for val in ("64", "32"):
        inp, out = _bundle(tmp_path / val, val)
        con = sqlite3.connect(inp / "corpus" / "a.sqlite")
        con.execute("CREATE TABLE t(x TEXT)"); con.execute("INSERT INTO t VALUES('safe')")
        con.commit(); con.close()
        with pytest.raises(AnonError):
            run_pipeline(inp, out)
