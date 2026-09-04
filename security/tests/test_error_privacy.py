"""Acceptance test for ticket privacy-safe-error-identifiers (#6)."""
from __future__ import annotations

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.policy import compile_policy

_HOSTILE = "attacker@secret-domain.example"


def test_hostile_policy_identifiers_never_appear_in_error_text() -> None:
    # A duplicate rule_id carrying PII must trigger a rejection whose message
    # does NOT echo the raw identifier.
    payload = {
        "version": 1,
        "protected_values": [],
        "sensitive_values": [
            {"rule_id": _HOSTILE, "subject_id": "a", "type": "name", "value": "Alice"},
            {"rule_id": _HOSTILE, "subject_id": "b", "type": "name", "value": "Bob"},
        ],
    }
    with pytest.raises(AnonError) as exc:
        compile_policy(payload)
    assert _HOSTILE not in str(exc.value)
    assert "duplicate_rule_id" in str(exc.value)  # closed error code still present
