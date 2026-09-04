"""Acceptance test for ticket pseudonym-domain-preflight (#8)."""
from __future__ import annotations

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.pseudonyms import build_replacements


def test_over_capacity_ip_policy_rejects_before_collision_search() -> None:
    # 254 distinct ip_address identities exceed the 253-value host-octet domain;
    # the preflight must reject up front, not after a long salted-hash search.
    identities = [("ip_address", f"host-{i}") for i in range(254)]
    with pytest.raises(AnonError):
        build_replacements(identities, 1)


def test_at_capacity_ip_policy_is_accepted() -> None:
    identities = [("ip_address", f"host-{i}") for i in range(253)]
    result = build_replacements(identities, 1)
    assert len({*result.values()}) == 253  # all distinct
