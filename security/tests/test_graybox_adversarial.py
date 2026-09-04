"""Gray-box adversarial tests: contract knowledge, hostile inputs (issue #12 lane).

Attacks the actual surface (policy/corpus/encoding/parser/SQLite/publication)
rather than HTTP. Bounded sizes keep CI fast while exercising the path.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError, AnonErrorCode
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy, replace_text


def _pol(sensitive, protected=None):
    return compile_policy(
        {"version": 1, "sensitive_values": sensitive, "protected_values": protected or []}
    )


def test_many_literals_completes_and_removes_all():
    sv = [
        {"rule_id": f"r{i}", "subject_id": f"p{i}", "type": "name", "value": f"Name{i:05d}"}
        for i in range(2000)
    ]
    pol = _pol(sv)
    text = " ".join(f"Name{i:05d}" for i in range(2000))
    out, count = replace_text(text, pol)
    assert count == 2000
    for i in range(0, 2000, 137):
        assert f"Name{i:05d}" not in out


def test_very_long_literal():
    value = "A" * 20000
    pol = _pol([{"rule_id": "r", "type": "secret", "value": value}])
    out, count = replace_text("x " + value + " y", pol)
    assert count == 1 and value not in out


def test_pathological_overlap_is_deterministic():
    pol = _pol(
        [
            {"rule_id": "a", "subject_id": "p", "type": "name", "value": "abc"},
            {"rule_id": "b", "subject_id": "p", "type": "name", "value": "abcd"},
            {"rule_id": "c", "subject_id": "p", "type": "name", "value": "bcd"},
        ]
    )
    r1 = replace_text("zabcdz abc z", pol)[0]
    r2 = replace_text("zabcdz abc z", pol)[0]
    assert r1 == r2
    assert "abcd" not in r1 and "abc" not in r1


def test_large_csv_field_preserved(tmp_path: Path):
    src = tmp_path / "a.csv"
    dst = tmp_path / "o.csv"
    big = "x" * 60000
    src.write_text(f"id,note\n1,{big}\n2,Ada\n", encoding="utf-8")
    transform_file(src, dst, _pol([{"rule_id": "r", "type": "name", "value": "Ada"}]))
    out = dst.read_text(encoding="utf-8")
    assert big in out and "Ada" not in out


def test_csv_embedded_multiline_and_quotes_preserved(tmp_path: Path):
    src = tmp_path / "a.csv"
    dst = tmp_path / "o.csv"
    src.write_text('id,note\n1,"line1\nline2, with comma"\n', encoding="utf-8")
    transform_file(src, dst, _pol([{"rule_id": "r", "type": "name", "value": "zzz"}]))
    with dst.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[1][1] == "line1\nline2, with comma"


def test_json_deep_within_bound_ok(tmp_path: Path):
    src = tmp_path / "a.json"
    dst = tmp_path / "o.json"
    depth = 150
    src.write_text("[" * depth + '"Ada"' + "]" * depth, encoding="utf-8")
    transform_file(src, dst, _pol([{"rule_id": "r", "type": "name", "value": "Ada"}]))
    assert "Ada" not in dst.read_text(encoding="utf-8")


def test_json_over_depth_rejected(tmp_path: Path):
    src = tmp_path / "a.json"
    depth = 300
    src.write_text("[" * depth + "1" + "]" * depth, encoding="utf-8")
    with pytest.raises(AnonError) as exc:
        transform_file(
            src, tmp_path / "o.json", _pol([{"rule_id": "r", "type": "name", "value": "Ada"}])
        )
    assert exc.value.code == AnonErrorCode.STRUCTURE_TOO_COMPLEX


def test_sqlite_unique_column_integrity_preserved(tmp_path: Path):
    src = tmp_path / "a.sqlite"
    dst = tmp_path / "o.sqlite"
    con = sqlite3.connect(src)
    con.executescript("CREATE TABLE users(id INTEGER PRIMARY KEY, email TEXT UNIQUE);")
    con.executemany("INSERT INTO users VALUES (?, ?)", [(1, "ada@x.io"), (2, "bob@x.io")])
    con.commit()
    con.close()
    pol = _pol(
        [
            {"rule_id": "e1", "subject_id": "p1", "type": "email", "value": "ada@x.io"},
            {"rule_id": "e2", "subject_id": "p2", "type": "email", "value": "bob@x.io"},
        ]
    )
    transform_file(src, dst, pol)
    con = sqlite3.connect(dst)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("SELECT COUNT(DISTINCT email) FROM users").fetchone()[0] == 2
    con.close()
