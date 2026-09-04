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


def _boundary_overlap(a: str, b: str) -> bool:
    # True if a non-empty suffix of `a` equals a prefix of `b`. In source text a
    # sensitive match ending where a protected value begins (or vice versa) lets
    # the replacement consume part of the protected span, changing protected
    # bytes while its occurrence count is preserved (review #8).
    for i in range(1, min(len(a), len(b)) + 1):
        if a[-i:] == b[:i]:
            return True
    return False


def _check_overlap(rules: tuple[Rule, ...], protected: tuple[str, ...]) -> None:
    for rule in rules:
        sv = rule.value
        for pv in protected:
            a, b = (ascii_lower(sv), ascii_lower(pv)) if not rule.case_sensitive else (sv, pv)
            if (
                a == b
                or a in b
                or b in a
                or _boundary_overlap(a, b)
                or _boundary_overlap(b, a)
            ):
                raise AnonError(
                    AnonErrorCode.PROTECTED_SENSITIVE_OVERLAP,
                    f"sensitive rule {rule.rule_id!r} overlaps a protected value",
                )


def compile_policy(payload: object) -> Policy:
    """Validate a policy payload strictly and compile its matcher."""
    _require(isinstance(payload, dict), AnonErrorCode.INVALID_POLICY, "policy is not an object")
    version = payload.get("version")
    # `True == 1` in Python, so a bool must be rejected explicitly before the
    # value comparison, or `"version": true` would pass as version 1.
    _require(
        isinstance(version, int) and not isinstance(version, bool) and version == 1,
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

    # One source text must not map to conflicting identities. Conflict is judged
    # over each rule's MATCH DOMAIN, not its exact literal: two case-insensitive
    # rules 'Alice' and 'ALICE' both match the input 'alice', so keying only the
    # exact spelling would let them claim the same text for different subjects.
    # Group by case-folded value; within a group, two rules with different
    # identities conflict unless BOTH are case-sensitive with differing exact
    # spellings (their match sets are then disjoint).
    domain: dict[str, list[Rule]] = {}
    for rule in rules:
        key = ascii_lower(rule.value)
        for prior in domain.get(key, ()):
            if prior.identity == rule.identity:
                continue
            both_cs = rule.case_sensitive and prior.case_sensitive
            if not both_cs or prior.value == rule.value:
                raise AnonError(
                    AnonErrorCode.IDENTITY_CONFLICT,
                    f"rule {rule.rule_id!r} shares a match domain with a conflicting identity",
                )
        domain.setdefault(key, []).append(rule)

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


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    seen: set[str] = set()
    for key, _ in pairs:
        _require(key not in seen, AnonErrorCode.INVALID_POLICY, "duplicate key in policy JSON")
        seen.add(key)
    return dict(pairs)


def load_policy(path: Path) -> Policy:
    # Reject duplicate keys instead of silently last-wins, which could drop a
    # sensitive rule and pass its value through unredacted.
    return compile_policy(
        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    )


def replace_text(text: str, policy: Policy) -> tuple[str, int]:
    """Shared replacement primitive: single-pass, deterministic, no cascade."""
    return policy.matcher.replace(text)
