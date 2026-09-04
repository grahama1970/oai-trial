"""Acceptance test for round-5 ticket cost-model-billing-units: the committed
docs must derive from the single estimator output, and the SLA arithmetic must
be internally consistent."""
from __future__ import annotations

import json
from pathlib import Path

from estimate_aws_cost import _TB, _one  # pythonpath includes scripts/

_CFG = json.loads(Path("costs/aws-us-east-1-inputs.json").read_text(encoding="utf-8"))


def test_1tb_1pb_cost_and_sla_contract() -> None:
    committed = json.loads(Path("costs/example-estimates.json").read_text(encoding="utf-8"))
    live_1tb = _one(_TB, _CFG)
    live_1pb = _one(10**15, _CFG)
    # committed example must equal a fresh run of the estimator (single source)
    assert committed["estimate_1TB"]["total_usd"] == live_1tb["total_usd"]
    assert committed["estimate_1PB"]["total_usd"] == live_1pb["total_usd"]
    # docs must carry the estimator's totals, not stale ones
    arch = Path("docs/production-architecture.md").read_text(encoding="utf-8")
    sub = Path("SUBMISSION.md").read_text(encoding="utf-8")
    tb = f"{live_1tb['total_usd']:.0f}"
    pb = f"{live_1pb['total_usd']:,.0f}"
    assert tb in arch and pb in arch, "production-architecture cost totals drifted"
    assert tb in sub and pb in sub, "SUBMISSION cost totals drifted"
    # SLA arithmetic consistency: wall clock at the configured worker pool
    # (transform + verify + retries) must be under the documented 1-hour target
    assert live_1tb["wall_clock_hours_at_workers"] < 1.0
    # 1 PB at the same pool must be under the documented 7-day target
    assert live_1pb["wall_clock_hours_at_workers"] < 7 * 24
    # every material line item exists and is positive
    for key in ("storage_usd", "requests_usd", "compute_usd", "orchestration_usd"):
        assert live_1pb[key] > 0


def test_required_billing_units_transfer_tiers_and_quotas_are_explicit() -> None:
    """Round-6 ticket cost-model-required-units: explicit service billing units
    plus transfer/tier/quota assumptions must exist in the committed inputs."""
    for key in (
        "sqs_per_million_requests_usd",
        "eventbridge_per_million_events_usd",
        "kms_per_10k_requests_usd",
        "cloudwatch_logs_gb_ingested_usd",
        "log_bytes_per_object",
    ):
        assert isinstance(_CFG[key], (int, float)) and _CFG[key] > 0, key
    for key in ("transfer_assumption", "s3_tier_assumption", "quota_assumptions"):
        assert isinstance(_CFG[key], str) and len(_CFG[key]) > 20, key
    # blended floor removed: orchestration must derive from the explicit units
    assert "orchestration_per_object_usd" not in _CFG
