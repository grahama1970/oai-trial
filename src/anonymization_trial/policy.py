"""Policy loading and deterministic replacement generation.

Inputs: a schema-version-1 ``policy.json`` (sensitive values with type, optional
subject_id, literal match, case sensitivity; plus protected_values).
Outputs: a frozen ``Policy`` of ``Rule`` records, and stable per-rule
replacement strings derived by hashing ``identity:data_type`` (identity =
subject_id or rule_id) so one identity converges and distinct identities do not
share a type-specific replacement.
Failure modes: raises ``ValueError`` on unsupported policy version, duplicate or
empty rule ids, or a non-literal ``match`` value (starter is literal-only).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    rule_id: str
    subject_id: str | None
    data_type: str
    value: str
    case_sensitive: bool


@dataclass(frozen=True)
class Policy:
    rules: tuple[Rule, ...]
    protected_values: tuple[str, ...]


def load_policy(path: Path) -> Policy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise ValueError("unsupported policy version")

    rules: list[Rule] = []
    seen_ids: set[str] = set()
    for item in payload.get("sensitive_values", []):
        rule_id = str(item["rule_id"])
        value = str(item["value"])
        if not value or rule_id in seen_ids:
            raise ValueError("policy rules need unique IDs and non-empty values")
        if item.get("match", "literal") != "literal":
            raise ValueError("the starter supports literal matching only")
        seen_ids.add(rule_id)
        rules.append(
            Rule(
                rule_id=rule_id,
                subject_id=item.get("subject_id"),
                data_type=str(item["type"]),
                value=value,
                case_sensitive=bool(item.get("case_sensitive", True)),
            )
        )

    protected = tuple(str(item["value"]) for item in payload.get("protected_values", []))
    return Policy(tuple(rules), protected)


def replacement_for(rule: Rule) -> str:
    identity = rule.subject_id or rule.rule_id
    digest = hashlib.sha256(f"{identity}:{rule.data_type}".encode()).hexdigest()
    short = digest[:10]
    number = int(digest[:8], 16)
    if rule.data_type == "name":
        return f"Person-{short}"
    if rule.data_type == "email":
        return f"user-{short}@example.invalid"
    if rule.data_type == "phone":
        return f"+1-555-{number % 10_000:04d}"
    if rule.data_type == "ip_address":
        return f"198.51.100.{1 + number % 253}"
    if rule.data_type == "secret":
        return f"[REDACTED-{short}]"
    return f"anon-{rule.data_type}-{short}"


def replace_text(text: str, policy: Policy) -> tuple[str, int]:
    replacements = 0
    result = text
    for rule in policy.rules:
        replacement = replacement_for(rule)
        if rule.case_sensitive:
            count = result.count(rule.value)
            result = result.replace(rule.value, replacement)
        else:
            pattern = re.compile(re.escape(rule.value), re.IGNORECASE)
            result, count = pattern.subn(replacement, result)
        replacements += count
    return result, replacements
