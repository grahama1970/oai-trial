"""Acceptance tests for WebGPT round-4 tickets as they are fixed."""
from __future__ import annotations

from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.pipeline import run_pipeline
from anonymization_trial.policy import compile_policy

_BASE = {"version": 1, "sensitive_values": [], "protected_values": []}


def test_non_string_protected_reason_is_rejected() -> None:  # ticket policy-protected-reason-schema
    with pytest.raises(AnonError):
        compile_policy({
            "version": 1,
            "sensitive_values": [],
            "protected_values": [{"value": "keep", "reason": 123}],
        })


def test_empty_protected_reason_is_rejected() -> None:
    with pytest.raises(AnonError):
        compile_policy({
            "version": 1,
            "sensitive_values": [],
            "protected_values": [{"value": "keep", "reason": ""}],
        })


def test_valid_protected_reason_accepted() -> None:
    compile_policy({
        "version": 1,
        "sensitive_values": [],
        "protected_values": [{"value": "keep", "reason": "regulatory hold"}],
    })


def test_policy_symlink_rejected_before_policy_read(tmp_path: Path) -> None:  # ticket policy-preflight-before-read
    real = tmp_path / "real_policy.json"
    real.write_text('{"version": 1, "sensitive_values": [], "protected_values": []}', encoding="utf-8")
    inp = tmp_path / "in"
    (inp / "corpus").mkdir(parents=True)
    (inp / "corpus" / "a.txt").write_text("hello\n", encoding="utf-8")
    (inp / "policy.json").symlink_to(real)  # untrusted symlink policy
    with pytest.raises(AnonError):
        run_pipeline(inp, tmp_path / "out")
