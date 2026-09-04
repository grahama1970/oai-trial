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
