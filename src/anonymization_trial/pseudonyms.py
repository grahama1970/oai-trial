"""Deterministic, collision-safe replacement generation.

Inputs: canonical identities ``(data_type, identity)`` and a policy version.
Outputs: a ``dict`` mapping each canonical identity to a stable, type-valid
replacement string, guaranteed distinct across different canonical identities of
the same data type.
Failure modes: raises ``AnonError(NAMESPACE_EXHAUSTED)`` if a bounded domain
(phone suffix, IPv4 host octet) cannot yield a distinct replacement.

Determinism: replacements derive from a domain-separated digest over
``(algorithm_version, scope_id, policy_version, data_type, identity, salt)``.
Same inputs always produce the same output; no mapping table is persisted (a
mapping table would itself be reversible PII).

Provenance: keyed/domain-separated pseudonym derivation with the data type in
the hash input follows AnonShield (arXiv:2606.15650); binding an
``algorithm_version`` + ``scope_id`` (rather than a single global namespace)
follows Proteus (arXiv:2603.06540). The local ``KEY_MODE`` is a public
deterministic namespace: it proves identity coherence, not cryptographic
secrecy. Production replaces it with a KMS-protected tenant/purpose-scoped HMAC.
"""
from __future__ import annotations

import hashlib

from .errors import AnonError, AnonErrorCode, safe_ref

CanonicalIdentity = tuple[str, str]  # (data_type, identity)

ALGORITHM_VERSION = "pseudonym-v1"
SCOPE_ID = "trial-v1"
KEY_MODE = "public-deterministic-trial-namespace"

# Bounded per-type replacement domains. build_replacements rejects a policy that
# names more distinct identities of a type than its domain can injectively hold,
# BEFORE any collision search, so an over-capacity policy fails fast instead of
# burning a large salted-hash loop (review ticket pseudonym-domain-preflight).
_DOMAIN_CAPACITY = {"phone": 10_000, "ip_address": 253}


def _digest(policy_version: int, data_type: str, identity: str, salt: int) -> str:
    material = f"{ALGORITHM_VERSION}:{SCOPE_ID}:{policy_version}:{data_type}:{identity}:{salt}"
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
    unique = sorted(set(identities))
    # Cardinality preflight: reject over-capacity bounded types up front.
    counts: dict[str, int] = {}
    for data_type, _identity in unique:
        counts[data_type] = counts.get(data_type, 0) + 1
    for data_type, capacity in _DOMAIN_CAPACITY.items():
        if counts.get(data_type, 0) > capacity:
            raise AnonError(
                AnonErrorCode.NAMESPACE_EXHAUSTED,
                f"data_type={safe_ref(data_type)} has {counts[data_type]} identities but its "
                f"bounded domain holds at most {capacity}",
            )

    replacements: dict[CanonicalIdentity, str] = {}
    used_by_type: dict[str, set[str]] = {}
    for data_type, identity in unique:
        seen = used_by_type.setdefault(data_type, set())
        # Bound the collision search to the domain capacity so it can never spin
        # far beyond the number of distinct values the domain can hold.
        attempt_cap = _DOMAIN_CAPACITY.get(data_type, 100_000)
        salt = 0
        while True:
            candidate = _render(data_type, _digest(policy_version, data_type, identity, salt))
            if candidate not in seen:
                break
            salt += 1
            if salt > attempt_cap:
                raise AnonError(
                    AnonErrorCode.NAMESPACE_EXHAUSTED,
                    f"cannot derive a distinct replacement for data_type={safe_ref(data_type)}",
                )
        seen.add(candidate)
        replacements[(data_type, identity)] = candidate
    return replacements
