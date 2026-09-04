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
    # Store intake + released copy for the retention window.
    storage = gb * cfg["s3_standard_gb_month_usd"] * cfg["storage_months"] * 2
    # One PUT (write release) + one GET (read intake) per object.
    requests = objects * (cfg["s3_put_per_1k_usd"] + cfg["s3_get_per_1k_usd"]) / 1000
    worker_hours = (total_bytes / cfg["throughput_bytes_per_s_per_worker"]) / 3600
    compute = worker_hours * (
        cfg["worker_vcpu"] * cfg["fargate_vcpu_hour_usd"]
        + cfg["worker_gb"] * cfg["fargate_gb_hour_usd"]
    )
    total = storage + requests + compute
    return {
        "objects": round(objects),
        "storage_usd": round(storage, 2),
        "requests_usd": round(requests, 2),
        "compute_usd": round(compute, 2),
        "total_usd": round(total, 2),
        "dominant_term": max(
            (("storage", storage), ("requests", requests), ("compute", compute)),
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
