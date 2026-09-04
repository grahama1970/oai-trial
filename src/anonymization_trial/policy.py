"""Policy loading, strict validation, and deterministic matcher compilation.

Inputs: a schema-version-1 ``policy.json`` (or an equivalent dict).
Outputs: a frozen ``Policy`` holding typed ``Rule`` records, protected values,
and a compiled ``Matcher`` whose replacements are stable, per-type-distinct
pseudonyms. ``replace_text(text, policy)`` is the shared replacement primitive.
Failure modes: raises ``AnonError`` (fail closed) on invalid schema, duplicate
rule ids, non-literal match, identity conflicts, non-ASCII case-insensitive
literals, or protected/sensitive overlap. No raw literal appears in any error.

Semantics: see docs/ANONYMIZATION_SEMANTICS.md. Matching is against original
input only; overlaps resolve leftmost-longest; protected/sensitive overlap is
rejected rather than silently resolved.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import AnonError, AnonErrorCode
from .matcher import Matcher, ascii_lower, build_matcher
from .pseudonyms import CanonicalIdentity, build_replacements

_ALLOWED_RULE_KEYS = {"rule_id", "subject_id", "type", "value", "match", "case_sensitive"}
_ALLOWED_PROTECTED_KEYS = {"value", "reason"}
_ALLOWED_TOP_KEYS = {"version", "sensitive_values", "protected_values"}


@dataclass(frozen=True, slots=True)
class Rule:
    rule_id: str
    subject_id: str | None
    data_type: str
    value: str
    case_sensitive: bool

    @property
    def identity(self) -> CanonicalIdentity:
        return (self.data_type, self.subject_id or self.rule_id)


@dataclass(frozen=True, slots=True)
class Policy:
    version: int
    rules: tuple[Rule, ...]
    protected_values: tuple[str, ...]
    matcher: Matcher


def _require(condition: bool, code: AnonErrorCode, message: str) -> None:
    if not condition:
        raise AnonError(code, message)


def _rule_from(item: object, index: int) -> Rule:
    _require(
        isinstance(item, dict),
        AnonErrorCode.INVALID_POLICY,
        f"sensitive_values[{index}] not an object",
    )
    _require(
        set(item) <= _ALLOWED_RULE_KEYS,
        AnonErrorCode.INVALID_POLICY,
        f"sensitive_values[{index}] has unknown fields",
    )
    for key in ("rule_id", "type", "value"):
        _require(
            isinstance(item.get(key), str) and item[key] != "",
            AnonErrorCode.INVALID_POLICY,
            f"sensitive_values[{index}].{key} missing or not a non-empty string",
        )
    match = item.get("match", "literal")
    _require(
        match == "literal",
        AnonErrorCode.UNSUPPORTED_MATCH,
        f"sensitive_values[{index}].match must be 'literal'",
    )
    subject_id = item.get("subject_id")
    _require(
        subject_id is None or (isinstance(subject_id, str) and subject_id != ""),
        AnonErrorCode.INVALID_POLICY,
        f"sensitive_values[{index}].subject_id must be a non-empty string when present",
    )
    case_sensitive = item.get("case_sensitive", True)
    _require(
        isinstance(case_sensitive, bool),
        AnonErrorCode.INVALID_POLICY,
        f"sensitive_values[{index}].case_sensitive must be a boolean",
    )
    return Rule(
        rule_id=item["rule_id"],
        subject_id=subject_id,
        data_type=item["type"],
        value=item["value"],
        case_sensitive=case_sensitive,
    )


def _check_overlap(rules: tuple[Rule, ...], protected: tuple[str, ...]) -> None:
    for rule in rules:
        sv = rule.value
        for pv in protected:
            a, b = (ascii_lower(sv), ascii_lower(pv)) if not rule.case_sensitive else (sv, pv)
            if a == b or a in b or b in a:
                raise AnonError(
                    AnonErrorCode.PROTECTED_SENSITIVE_OVERLAP,
                    f"sensitive rule {rule.rule_id!r} overlaps a protected value",
                )


def compile_policy(payload: object) -> Policy:
    """Validate a policy payload strictly and compile its matcher."""
    _require(isinstance(payload, dict), AnonErrorCode.INVALID_POLICY, "policy is not an object")
    _require(
        payload.get("version") == 1,
        AnonErrorCode.INVALID_POLICY,
        "unsupported policy version",
    )
    _require(
        set(payload) <= _ALLOWED_TOP_KEYS,
        AnonErrorCode.INVALID_POLICY,
        "policy has unknown top-level fields",
    )
    raw_sensitive = payload.get("sensitive_values", [])
    raw_protected = payload.get("protected_values", [])
    _require(
        isinstance(raw_sensitive, list),
        AnonErrorCode.INVALID_POLICY,
        "sensitive_values must be an array",
    )
    _require(
        isinstance(raw_protected, list),
        AnonErrorCode.INVALID_POLICY,
        "protected_values must be an array",
    )

    rules: list[Rule] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw_sensitive):
        rule = _rule_from(item, index)
        _require(
            rule.rule_id not in seen_ids,
            AnonErrorCode.DUPLICATE_RULE_ID,
            f"duplicate rule_id {rule.rule_id!r}",
        )
        seen_ids.add(rule.rule_id)
        if not rule.case_sensitive:
            _require(
                rule.value.isascii(),
                AnonErrorCode.NON_ASCII_INSENSITIVE,
                f"rule {rule.rule_id!r} is case-insensitive but not ASCII",
            )
        rules.append(rule)

    protected: list[str] = []
    for index, item in enumerate(raw_protected):
        _require(
            isinstance(item, dict),
            AnonErrorCode.INVALID_POLICY,
            f"protected_values[{index}] not an object",
        )
        _require(
            set(item) <= _ALLOWED_PROTECTED_KEYS,
            AnonErrorCode.INVALID_POLICY,
            f"protected_values[{index}] unknown fields",
        )
        value = item.get("value")
        _require(
            isinstance(value, str) and value != "",
            AnonErrorCode.INVALID_POLICY,
            f"protected_values[{index}].value invalid",
        )
        protected.append(value)

    # One source literal must not map to conflicting identities/types.
    literal_identity: dict[str, CanonicalIdentity] = {}
    for rule in rules:
        prior = literal_identity.get(rule.value)
        if prior is not None and prior != rule.identity:
            raise AnonError(
                AnonErrorCode.IDENTITY_CONFLICT,
                f"literal for rule {rule.rule_id!r} maps to conflicting identities",
            )
        literal_identity[rule.value] = rule.identity

    rules_tuple = tuple(rules)
    protected_tuple = tuple(protected)
    _check_overlap(rules_tuple, protected_tuple)

    identities: list[CanonicalIdentity] = [rule.identity for rule in rules_tuple]
    replacements = build_replacements(identities, 1)
    rules_cs: list[tuple[str, str, str]] = []
    rules_ci: list[tuple[str, str, str]] = []
    for rule in rules_tuple:
        triple = (rule.value, replacements[rule.identity], rule.rule_id)
        (rules_cs if rule.case_sensitive else rules_ci).append(triple)

    return Policy(
        version=1,
        rules=rules_tuple,
        protected_values=protected_tuple,
        matcher=build_matcher(rules_cs, rules_ci),
    )


def load_policy(path: Path) -> Policy:
    return compile_policy(json.loads(path.read_text(encoding="utf-8")))


def replace_text(text: str, policy: Policy) -> tuple[str, int]:
    """Shared replacement primitive: single-pass, deterministic, no cascade."""
    return policy.matcher.replace(text)
