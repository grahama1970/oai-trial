import json
import sqlite3

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy, replace_text


def _policy(value: str):
    return compile_policy({
        "version": 1,
        "protected_values": [],
        "sensitive_values": [{"rule_id": "phone", "subject_id": "p", "type": "phone", "value": value}],
    })


def test_formatted_phone_matches_digit_only_text_alias():
    policy = _policy("555-123-4567")

    replaced, count = replace_text("call 5551234567", policy)

    assert count == 1
    assert "5551234567" not in replaced


def test_json_integer_matches_formatted_phone_policy(tmp_path):
    src = tmp_path / "in.json"
    dst = tmp_path / "out.json"
    src.write_text(json.dumps({"phone": 5551234567}), encoding="utf-8")

    records, replacements = transform_file(src, dst, _policy("555-123-4567"))

    assert records == 1
    assert replacements == 1
    assert "5551234567" not in dst.read_text(encoding="utf-8")


def test_sqlite_integer_matches_formatted_phone_policy(tmp_path):
    src = tmp_path / "in.sqlite"
    dst = tmp_path / "out.sqlite"
    con = sqlite3.connect(src)
    con.execute("CREATE TABLE t(phone INTEGER)")
    con.execute("INSERT INTO t VALUES (5551234567)")
    con.commit()
    con.close()

    records, replacements = transform_file(src, dst, _policy("555-123-4567"))

    assert records == 1
    assert replacements == 1
    out = sqlite3.connect(dst)
    try:
        assert isinstance(out.execute("SELECT phone FROM t").fetchone()[0], str)
    finally:
        out.close()


def test_leading_zero_policy_numeric_scalar_fails_closed(tmp_path):
    src = tmp_path / "in.json"
    dst = tmp_path / "out.json"
    src.write_text(json.dumps({"phone": 5551234567}), encoding="utf-8")

    with pytest.raises(AnonError, match="lossy numeric representation"):
        transform_file(src, dst, _policy("05551234567"))
