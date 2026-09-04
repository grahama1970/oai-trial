"""SQLite adapter tests (issue #7)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError, AnonErrorCode
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy


def _pol(value="Ada"):
    return compile_policy(
        {
            "version": 1,
            "sensitive_values": [{"rule_id": "r", "type": "name", "value": value}],
            "protected_values": [],
        }
    )


def test_sqlite_values_replaced_integrity_preserved(tmp_path: Path):
    src = tmp_path / "a.sqlite"
    dst = tmp_path / "out.sqlite"
    con = sqlite3.connect(src)
    con.executescript("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);")
    con.executemany("INSERT INTO users(id, name) VALUES (?, ?)", [(1, "Ada"), (2, "Bob")])
    con.commit()
    con.close()
    records, count = transform_file(src, dst, _pol())
    con = sqlite3.connect(dst)
    names = [r[0] for r in con.execute("SELECT name FROM users ORDER BY id")]
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2
    con.close()
    assert "Ada" not in names
    assert records == 2 and count == 1


def test_sqlite_foreign_keys_preserved(tmp_path: Path):
    src = tmp_path / "a.sqlite"
    dst = tmp_path / "out.sqlite"
    con = sqlite3.connect(src)
    con.executescript(
        "CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);"
        "CREATE TABLE orders(oid INTEGER PRIMARY KEY, uid INTEGER REFERENCES users(id));"
    )
    con.execute("INSERT INTO users VALUES (1, 'Ada')")
    con.execute("INSERT INTO orders VALUES (10, 1)")
    con.commit()
    con.close()
    transform_file(src, dst, _pol())
    con = sqlite3.connect(dst)
    con.execute("PRAGMA foreign_keys = ON")
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    con.close()


def test_sqlite_sensitive_column_name_rejected(tmp_path: Path):
    src = tmp_path / "a.sqlite"
    con = sqlite3.connect(src)
    con.executescript('CREATE TABLE users(id INTEGER PRIMARY KEY, "Ada" TEXT);')
    con.commit()
    con.close()
    with pytest.raises(AnonError) as exc:
        transform_file(src, tmp_path / "o.sqlite", _pol())
    assert exc.value.code == AnonErrorCode.SENSITIVE_IN_SCHEMA


def test_sqlite_without_rowid_rejected(tmp_path: Path):
    src = tmp_path / "a.sqlite"
    con = sqlite3.connect(src)
    con.executescript("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT) WITHOUT ROWID;")
    con.commit()
    con.close()
    with pytest.raises(AnonError) as exc:
        transform_file(src, tmp_path / "o.sqlite", _pol())
    assert exc.value.code == AnonErrorCode.UNSUPPORTED_FORMAT
