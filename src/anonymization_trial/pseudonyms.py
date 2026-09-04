"""Deterministic, collision-safe replacement generation.

Inputs: canonical identities ``(data_type, identity)`` and a policy version.
Outputs: a ``dict`` mapping each canonical identity to a stable, type-valid
replacement string, guaranteed distinct across different canonical identities of
the same data type.
Failure modes: raises ``AnonError(NAMESPACE_EXHAUSTED)`` if a bounded domain
(phone suffix, IPv4 host octet) cannot yield a distinct replacement.

Determinism: replacements derive from ``SHA256(policy_version:data_type:identity
[:salt])``. Same inputs always produce the same output; no mapping table is
persisted (a mapping table would itself be reversible PII).
"""
from __future__ import annotations

import hashlib

from .errors import AnonError, AnonErrorCode

CanonicalIdentity = tuple[str, str]  # (data_type, identity)


def _digest(policy_version: int, data_type: str, identity: str, salt: int) -> str:
    material = f"{policy_version}:{data_type}:{identity}:{salt}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _render(data_type: str, digest: str) -> str:
    short = digest[:10]
    number = int(digest[:8], 16)
    if data_type == "name":
        return f"Person-{short}"
    if data_type == "email":
        return f"user-{short}@example.invalid"
    if data_type == "phone":
        return f"+1-555-{number % 10_000:04d}"
    if data_type == "ip_address":
        return f"198.51.100.{1 + number % 253}"
    if data_type == "secret":
        return f"[REDACTED-{short}]"
    return f"anon-{data_type}-{short}"


def build_replacements(
    identities: list[CanonicalIdentity], policy_version: int
) -> dict[CanonicalIdentity, str]:
    """Return a stable, per-type-distinct replacement for each identity.

    Identities are processed in sorted order so the plan is independent of input
    order. On a collision within a bounded domain, the salt is incremented
    deterministically until the replacement is unique for that data type.
    """
    replacements: dict[CanonicalIdentity, str] = {}
    used_by_type: dict[str, set[str]] = {}
    for data_type, identity in sorted(set(identities)):
        seen = used_by_type.setdefault(data_type, set())
        salt = 0
        while True:
            candidate = _render(data_type, _digest(policy_version, data_type, identity, salt))
            if candidate not in seen:
                break
            salt += 1
            if salt > 100_000:
                raise AnonError(
                    AnonErrorCode.NAMESPACE_EXHAUSTED,
                    f"cannot derive a distinct replacement for data_type={data_type!r}",
                )
        seen.add(candidate)
        replacements[(data_type, identity)] = candidate
    return replacements
