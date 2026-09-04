"""Closed, privacy-safe error vocabulary for the anonymization pipeline.

Inputs: none (definitions only).
Outputs: ``AnonErrorCode`` (closed set) and ``AnonError`` (carries a code and a
message that never contains raw sensitive/protected values or file contents).
Failure modes: raising ``AnonError`` signals a fail-closed rejection; callers
convert it to a non-zero exit with no ready release.
"""
from __future__ import annotations

import hashlib
from enum import StrEnum


def safe_ref(value: str) -> str:
    """An opaque, stable reference to an attacker-controlled identifier.

    Policy fields such as ``rule_id`` and ``data_type`` are attacker-controlled
    and could carry PII (an email in a rule_id). Error text must never echo them
    raw, so it references them by a short non-reversible digest instead, which a
    developer can still correlate against the policy without leaking the value.
    """
    return "ref:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


class AnonErrorCode(StrEnum):
    """Every rejection reason. Messages must stay free of raw data."""

    INVALID_POLICY = "invalid_policy"
    DUPLICATE_RULE_ID = "duplicate_rule_id"
    IDENTITY_CONFLICT = "identity_conflict"
    UNSUPPORTED_MATCH = "unsupported_match"
    NON_ASCII_INSENSITIVE = "non_ascii_case_insensitive"
    PROTECTED_SENSITIVE_OVERLAP = "protected_sensitive_overlap"
    NAMESPACE_EXHAUSTED = "namespace_exhausted"
    UNSUPPORTED_FORMAT = "unsupported_format"
    MALFORMED_ENCODING = "malformed_encoding"
    SENSITIVE_IN_SCHEMA = "sensitive_in_schema_identifier"
    MALFORMED_JSON = "malformed_json"
    STRUCTURE_TOO_COMPLEX = "structure_too_complex"
    VERIFICATION_FAILED = "verification_failed"
    PUBLICATION_FAILED = "publication_failed"
    UNSAFE_INPUT = "unsafe_input"
    SOURCE_CHANGED = "source_changed"


class AnonError(RuntimeError):
    """A typed, privacy-safe pipeline error.

    ``message`` must describe the failure class without echoing any sensitive or
    protected literal, cell, key, identifier, or file content.
    """

    def __init__(self, code: AnonErrorCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}: {message}")
