"""Adversarial red tests from the WebGPT peer review (2026-09-04).

Each test asserts the CORRECT fail-closed behavior for an attack the WebGPT
review found. These four were reproduced as real defects, then fixed; the tests
now pass and guard against regression. See security/ADVERSARIAL_MATRIX.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy, load_policy

_EMPTY = {"version": 1, "sensitive_values": [], "protected_values": []}


def test_version_true_is_rejected() -> None:  # review#16 (fixed)
    with pytest.raises(AnonError):
        compile_policy({**_EMPTY, "version": True})


def test_duplicate_policy_keys_rejected(tmp_path: Path) -> None:  # review#16 (fixed)
    # Duplicate sensitive_values: last-wins keeps the empty array and silently
    # drops rule 'r', so the sensitive value would pass through unredacted.
    p = tmp_path / "policy.json"
    p.write_text(
        '{"version":1,'
        '"sensitive_values":[{"rule_id":"r","subject_id":"s","type":"name","value":"Alice"}],'
        '"sensitive_values":[],'
        '"protected_values":[]}',
        encoding="utf-8",
    )
    with pytest.raises(AnonError):
        load_policy(p)


def test_case_insensitive_conflicting_identities_rejected() -> None:  # review#9 (fixed)
    payload = {
        "version": 1,
        "protected_values": [],
        "sensitive_values": [
            {"rule_id": "r1", "subject_id": "s1", "type": "name", "value": "Alice", "case_sensitive": False},
            {"rule_id": "r2", "subject_id": "s2", "type": "name", "value": "ALICE", "case_sensitive": False},
        ],
    }
    with pytest.raises(AnonError):
        compile_policy(payload)


def test_non_finite_json_number_is_rejected(tmp_path: Path) -> None:  # review#3 (fixed)
    src = tmp_path / "a.json"
    src.write_text('{"n": 1e400}', encoding="utf-8")
    out = tmp_path / "out.json"
    pol = compile_policy(_EMPTY)
    try:
        transform_file(src, out, pol)
    except AnonError:
        return  # rejecting at transform time is the correct fail-closed behavior
    body = out.read_text(encoding="utf-8")
    assert "Infinity" not in body and "NaN" not in body
    json.loads(body)  # must be strict-valid JSON
