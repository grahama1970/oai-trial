"""CLI entry point exposing the two required commands.

``anonymization-trial demo`` runs a self-contained demonstration across all four
formats at two workload sizes (largest >= 10x smallest) and reports throughput
and per-run peak memory. Each size runs in its own subprocess so ``ru_maxrss``
reflects that single run's peak rather than a cumulative total.
``anonymization-trial run --input --output`` anonymizes a mounted bundle.
Exit code is 0 only when the run/demo verification passes; any handled error
prints a sanitized message to stderr and returns non-zero (fail closed).
"""
from __future__ import annotations

import argparse
import json
import resource
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from .errors import AnonError
from .fixture import generate_fixture
from .pipeline import PipelineError, run_pipeline

_DEMO_SIZES = (100, 1000)  # largest is 10x the smallest


def _peak_memory_mb() -> float | None:
    try:
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return round(value / (1024 * 1024), 2)
        return round(value / 1024, 2)
    except (AttributeError, ValueError):
        return None


def _run_once(records: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="anonymization-demo-") as directory:
        root = Path(directory)
        generate_fixture(root / "input", records)
        started = time.perf_counter()
        report = run_pipeline(root / "input", root / "output")
        elapsed = max(time.perf_counter() - started, 1e-9)
        return {
            "logical_records": records,
            "files_processed": report.files_processed,
            "records_processed": report.records_processed,
            "bytes_read": report.bytes_read,
            "elapsed_seconds": round(elapsed, 6),
            "records_per_second": round(report.records_processed / elapsed, 2),
            "bytes_per_second": round(report.bytes_read / elapsed, 2),
            "peak_memory_mb": _peak_memory_mb(),
            "verification_passed": report.verification_passed,
        }


def _demo() -> int:
    summaries = []
    for records in _DEMO_SIZES:
        proc = subprocess.run(  # noqa: S603 (fixed argv; no shell, no untrusted input)
            [sys.executable, "-m", "anonymization_trial", "bench-once", "--records", str(records)],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if proc.returncode != 0:
            print(f"demo failed at size {records}", file=sys.stderr)
            return 1
        summary = json.loads(proc.stdout)
        if not summary.get("verification_passed"):
            print("demo verification failed", file=sys.stderr)
            return 1
        summaries.append(summary)
    print(json.dumps({"demo": "success", "runs": summaries}, sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cross-format anonymization trial")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("demo", help="run the bundled self-contained demonstration")
    run = subparsers.add_parser("run", help="process a mounted input bundle")
    run.add_argument("--input", type=Path, default=Path("/trial/input"))
    run.add_argument("--output", type=Path, default=Path("/trial/output"))
    bench = subparsers.add_parser("bench-once", help="internal: one benchmark run as JSON")
    bench.add_argument("--records", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command in {None, "demo"}:
            return _demo()
        if args.command == "bench-once":
            print(json.dumps(_run_once(args.records), sort_keys=True))
            return 0
        report = run_pipeline(args.input, args.output)
        print(json.dumps(asdict(report), sort_keys=True))
        return 0
    except (OSError, ValueError, PipelineError, AnonError) as error:
        # Privacy-safe: report the error class/code only, never raw data.
        detail = error.code.value if isinstance(error, AnonError) else type(error).__name__
        print(f"run failed: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
