#!/usr/bin/env python3
"""Reproducible AWS cost estimator for the anonymization pipeline.

Inputs: a price/assumptions JSON (see costs/aws-us-east-1-inputs.json).
Outputs: a deterministic cost breakdown for 1 TB and 1 PB to stdout (JSON), with
a sensitivity band over the dominant uncertainties (throughput, avg file size).
Failure modes: exits non-zero on a missing/invalid inputs file.

Arithmetic is intentionally explicit so every number in SUBMISSION.md can be
reproduced by running this script against the committed inputs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TB = 10**12
_PB = 10**15


def _one(total_bytes: float, cfg: dict) -> dict:
    gb = total_bytes / 1e9
    objects = total_bytes / cfg["avg_file_bytes"]
    retry_rate = cfg.get("retry_rate", 0.02)
    # Storage: intake + staging + released copy for the retention window.
    storage = gb * cfg["s3_standard_gb_month_usd"] * cfg["storage_months"] * 3
    # Requests per object across the full flow:
    #   GETs: 1 intake read (transform) + 2 verify rereads (staged + source)
    #   PUTs: 1 staging write + 1 release promote (manifest amortized)
    # plus a retry fraction re-running transform+verify requests.
    puts_per_obj = 2.0 * (1.0 + retry_rate)
    gets_per_obj = 3.0 * (1.0 + retry_rate)
    requests = objects * (
        puts_per_obj * cfg["s3_put_per_1k_usd"] + gets_per_obj * cfg["s3_get_per_1k_usd"]
    ) / 1000
    # Compute: transform pass + verify reread pass (~2x IO-bound time) + retries.
    compute_seconds = (total_bytes / cfg["throughput_bytes_per_s_per_worker"]) * 2.0
    worker_hours = compute_seconds * (1.0 + retry_rate) / 3600
    compute = worker_hours * (
        cfg["worker_vcpu"] * cfg["fargate_vcpu_hour_usd"]
        + cfg["worker_gb"] * cfg["fargate_gb_hour_usd"]
    )
    # Orchestration: explicit per-service quantity x unit price (one SQS message,
    # one EventBridge event, one KMS data-key request, and log bytes per object).
    orchestration = objects * (
        cfg["sqs_per_million_requests_usd"] / 1e6
        + cfg["eventbridge_per_million_events_usd"] / 1e6
        + cfg["kms_per_10k_requests_usd"] / 1e4
        + cfg["log_bytes_per_object"] / 1e9 * cfg["cloudwatch_logs_gb_ingested_usd"]
    )
    total = storage + requests + compute + orchestration
    workers = cfg.get("workers", 200)
    wall_hours = compute_seconds * (1.0 + retry_rate) / max(workers, 1) / 3600
    return {
        "objects": round(objects),
        "storage_usd": round(storage, 2),
        "requests_usd": round(requests, 2),
        "compute_usd": round(compute, 2),
        "orchestration_usd": round(orchestration, 2),
        "total_usd": round(total, 2),
        "wall_clock_hours_at_workers": round(wall_hours, 2),
        "workers": workers,
        "dominant_term": max(
            (
                ("storage", storage),
                ("requests", requests),
                ("compute", compute),
                ("orchestration", orchestration),
            ),
            key=lambda kv: kv[1],
        )[0],
    }


def _sensitivity(total_bytes: float, cfg: dict) -> dict:
    lo = dict(cfg, throughput_bytes_per_s_per_worker=cfg["throughput_bytes_per_s_per_worker"] * 0.5)
    hi = dict(cfg, throughput_bytes_per_s_per_worker=cfg["throughput_bytes_per_s_per_worker"] * 2.0)
    small = dict(cfg, avg_file_bytes=cfg["avg_file_bytes"] / 10)
    return {
        "half_throughput_total_usd": _one(total_bytes, lo)["total_usd"],
        "double_throughput_total_usd": _one(total_bytes, hi)["total_usd"],
        "tenth_file_size_total_usd": _one(total_bytes, small)["total_usd"],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: read --inputs JSON, print the 1 TB/1 PB cost breakdown as
    JSON to stdout; return 0 on success, 1 on a missing/invalid inputs file."""
    parser = argparse.ArgumentParser(description="AWS cost estimate for the anonymization pipeline")
    parser.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        cfg = json.loads(args.inputs.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"cannot read inputs: {type(error).__name__}", file=sys.stderr)
        return 1
    result = {
        "region": cfg["region"],
        "price_date": cfg["price_date"],
        "source": cfg["source"],
        "assumptions": cfg,
        "estimate_1TB": {**_one(_TB, cfg), "sensitivity": _sensitivity(_TB, cfg)},
        "estimate_1PB": {**_one(_PB, cfg), "sensitivity": _sensitivity(_PB, cfg)},
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
