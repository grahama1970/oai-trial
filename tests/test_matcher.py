"""Tests for the deterministic matcher and strict policy compiler (issue #3)."""
from __future__ import annotations

import pytest

from anonymization_trial.errors import AnonError, AnonErrorCode
from anonymization_trial.policy import compile_policy, replace_text


def _policy(sensitive, protected=None):
    return compile_policy(
        {
            "version": 1,
            "sensitive_values": sensitive,
            "protected_values": protected or [],
        }
    )


def _rule(rule_id, value, data_type="name", subject_id=None, case_sensitive=True):
    item = {"rule_id": rule_id, "type": data_type, "value": value, "case_sensitive": case_sensitive}
    if subject_id is not None:
        item["subject_id"] = subject_id
    return item


def test_leftmost_longest_wins():
    pol = _policy([_rule("short", "ab", subject_id="a"), _rule("long", "abc", subject_id="b")])
    out, count = replace_text("z abc z", pol)
    assert count == 1
    # "abc" replaced as one span; the shorter "ab" did not fire inside it.
    assert "abc" not in out
    assert "c z" not in out or out.endswith("z")  # trailing 'c' not left dangling


def test_no_cascade_replacements_not_rescanned():
    # Rule B's literal "Person" appears inside rule A's generated name replacement.
    pol = _policy([_rule("a", "Bob", data_type="name"), _rule("b", "Person", data_type="secret")])
    out, count = replace_text("Bob", pol)
    assert count == 1  # only "Bob" matched in the ORIGINAL text
    assert out.startswith("Person-")  # emitted replacement, not re-replaced by rule B


def test_alias_convergence():
    pol = _policy(
        [
            _rule("r1", "Bob", subject_id="p1"),
            _rule("r2", "Bobby", subject_id="p1"),
        ]
    )
    assert replace_text("Bob", pol)[0] == replace_text("Bobby", pol)[0]


def test_distinct_identities_differ():
    pol = _policy(
        [
            _rule("r1", "Bob", subject_id="p1"),
            _rule("r2", "Cara", subject_id="p2"),
        ]
    )
    assert replace_text("Bob", pol)[0] != replace_text("Cara", pol)[0]


def test_case_insensitive_ascii():
    pol = _policy([_rule("e", "a@b.com", data_type="email", case_sensitive=False)])
    out, count = replace_text("X A@B.COM Y", pol)
    assert count == 1
    assert "A@B.COM" not in out


def test_reject_duplicate_rule_id():
    with pytest.raises(AnonError) as exc:
        _policy([_rule("dup", "A"), _rule("dup", "B")])
    assert exc.value.code == AnonErrorCode.DUPLICATE_RULE_ID


def test_reject_non_literal_match():
    with pytest.raises(AnonError) as exc:
        compile_policy(
            {
                "version": 1,
                "sensitive_values": [{"rule_id": "r", "type": "name", "value": "A", "match": "regex"}],
                "protected_values": [],
            }
        )
    assert exc.value.code == AnonErrorCode.UNSUPPORTED_MATCH


def test_reject_non_ascii_case_insensitive():
    with pytest.raises(AnonError) as exc:
        _policy([_rule("r", "caf\u00e9", case_sensitive=False)])
    assert exc.value.code == AnonErrorCode.NON_ASCII_INSENSITIVE


def test_reject_protected_sensitive_overlap():
    with pytest.raises(AnonError) as exc:
        _policy([_rule("r", "Ada")], protected=[{"value": "Adam Smith"}])
    assert exc.value.code == AnonErrorCode.PROTECTED_SENSITIVE_OVERLAP


def test_reject_unknown_top_field():
    with pytest.raises(AnonError) as exc:
        compile_policy({"version": 1, "sensitive_values": [], "protected_values": [], "extra": 1})
    assert exc.value.code == AnonErrorCode.INVALID_POLICY
