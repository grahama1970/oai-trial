"""oai-trial acceptance-contract floor cases for Battle.

These are the brief-derived cases required before beyond-contract cases count.
"""
from __future__ import annotations

import json
import sqlite3
import unicodedata
from pathlib import Path

PHONE = "5551234567"
FORMATTED_PHONE = "555-123-4567"
LEADING_ZERO_PHONE = "05551234567"
LOSSY_BIG_ID = "9007199254740993"
NAME = "Mara Ellison"
ACCENT = unicodedata.normalize("NFC", "Jos\u00e9 Malk\u00e9")


def _bundle(root: Path, name: str, value: str, writer, expectation: str = "MAY_REJECT") -> tuple[str, str, str]:
    d = root / name
    (d / "corpus").mkdir(parents=True, exist_ok=True)
    (d / "policy.json").write_text(json.dumps({
        "version": 1,
        "protected_values": [],
        "sensitive_values": [{"rule_id": "r", "subject_id": "s", "type": "name", "value": value}],
    }), encoding="utf-8")
    writer(d / "corpus")
    return name, str(d), expectation


def generate(work_dir, params):
    root = Path(work_dir)
    root.mkdir(parents=True, exist_ok=True)
    yield _bundle(root, "json-string", NAME, lambda c: (c / "d.json").write_text(json.dumps({"v": NAME})))
    yield _bundle(root, "csv-cell", NAME, lambda c: (c / "d.csv").write_text(f"col\n{NAME}\n"))
    yield _bundle(root, "utf8-text", NAME, lambda c: (c / "d.txt").write_text(f"note: {NAME}\n"))
    yield _bundle(root, "sqlite-text", NAME, lambda c: _sql(c, "TEXT", NAME))
    yield _bundle(root, "json-integer", PHONE, lambda c: (c / "d.json").write_text(json.dumps({"v": int(PHONE)})))
    yield _bundle(root, "json-float", PHONE, lambda c: (c / "d.json").write_text(json.dumps({"v": float(PHONE)})))
    yield _bundle(root, "json-scientific", "100000000000000000000", lambda c: (c / "d.json").write_text('{"v": 1e20}'))
    yield _bundle(root, "sqlite-integer", PHONE, lambda c: _sql(c, "INTEGER", int(PHONE)))
    yield _bundle(root, "sqlite-real", PHONE, lambda c: _sql(c, "REAL", float(PHONE)))
    yield _bundle(root, "adv-formatted-phone-json-integer", FORMATTED_PHONE, lambda c: (c / "d.json").write_text(json.dumps({"v": int(PHONE)})), "MUST_ACCEPT")
    yield _bundle(root, "adv-formatted-phone-csv-bare", FORMATTED_PHONE, lambda c: (c / "d.csv").write_text(f"col\n{PHONE}\n"), "MUST_ACCEPT")
    yield _bundle(root, "adv-formatted-phone-text-bare", FORMATTED_PHONE, lambda c: (c / "d.txt").write_text(f"note {PHONE}\n"), "MUST_ACCEPT")
    yield _bundle(root, "adv-leading-zero-json-integer", LEADING_ZERO_PHONE, lambda c: (c / "d.json").write_text(json.dumps({"v": int(LEADING_ZERO_PHONE)})), "MUST_REJECT")
    yield _bundle(root, "adv-lossy-big-json-float", LOSSY_BIG_ID, lambda c: (c / "d.json").write_text('{"v": 9007199254740993.0}'), "MUST_REJECT")
    yield _bundle(root, "adv-formatted-phone-sqlite-integer", FORMATTED_PHONE, lambda c: _sql(c, "INTEGER", int(PHONE)), "MUST_ACCEPT")
    yield _bundle(root, "adv-cross-format-same-identity-trap", FORMATTED_PHONE, lambda c: _all_formats(c, FORMATTED_PHONE, PHONE), "MUST_ACCEPT")
    yield _bundle(root, "unicode-nfd-json", ACCENT, lambda c: (c / "d.json").write_text(json.dumps({"v": unicodedata.normalize("NFD", ACCENT)})))
    yield _bundle(root, "unicode-nfd-text", ACCENT, lambda c: (c / "d.txt").write_text("who: " + unicodedata.normalize("NFD", ACCENT) + "\n"))
    yield _bundle(root, "utf8-bom-text", NAME, lambda c: (c / "d.txt").write_bytes(b"\xef\xbb\xbf" + f"note {NAME}".encode()))
    yield _bundle(root, "json-uescape", NAME, lambda c: (c / "d.json").write_bytes(b'{"v":"' + NAME.encode().replace(b"M", b"\\u004d") + b'"}'))
    yield _bundle(root, "sqlite-check-literal", PHONE, lambda c: _sql_check(c, PHONE))


def _all_formats(corpus: Path, formatted: str, digits: str) -> None:
    (corpus / "d.json").write_text(json.dumps({"phone": int(digits), "nested": [{"same": formatted}]}))
    (corpus / "d.csv").write_text(f"phone\n{digits}\n")
    (corpus / "d.txt").write_text(f"same identity {digits}\n")
    _sql(corpus, "INTEGER", int(digits))


def _sql(corpus: Path, coltype: str, value) -> None:
    con = sqlite3.connect(corpus / "d.sqlite")
    con.execute(f"CREATE TABLE t(id INTEGER PRIMARY KEY, v {coltype})")
    con.execute("INSERT INTO t(v) VALUES(?)", (value,))
    con.commit(); con.close()


def _sql_check(corpus: Path, value: str) -> None:
    con = sqlite3.connect(corpus / "d.sqlite")
    con.executescript(f"CREATE TABLE b(x TEXT, CHECK (x <> '{value}')); INSERT INTO b(x) VALUES('safe');")
    con.commit(); con.close()
