from __future__ import annotations

import argparse
import json
import resource
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from .fixture import generate_fixture
from .pipeline import PipelineError, run_pipeline


def _peak_memory_mb() -> float | None:
    try:
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return round(value / (1024 * 1024), 2)
        return round(value / 1024, 2)
    except (AttributeError, ValueError):
        return None


def _demo() -> int:
    summaries = []
    for records in (25, 250):
        with tempfile.TemporaryDirectory(prefix="anonymization-demo-") as directory:
            root = Path(directory)
            input_root = root / "input"
            output_root = root / "output"
            generate_fixture(input_root, records)
            started = time.perf_counter()
            report = run_pipeline(input_root, output_root)
            elapsed = time.perf_counter() - started
            summaries.append(
                {
                    "logical_records": records,
                    "elapsed_seconds": round(elapsed, 6),
                    "records_per_second": round(report.records_processed / max(elapsed, 1e-9), 2),
                    "bytes_per_second": round(report.bytes_read / max(elapsed, 1e-9), 2),
                    "peak_memory_mb": _peak_memory_mb(),
                    "verification_passed": report.verification_passed,
                }
            )
    print(json.dumps({"demo": "success", "runs": summaries}, sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the anonymization trial starter")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("demo", help="run the bundled self-contained demonstration")
    run = subparsers.add_parser("run", help="process a mounted input bundle")
    run.add_argument("--input", type=Path, default=Path("/trial/input"))
    run.add_argument("--output", type=Path, default=Path("/trial/output"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command in {None, "demo"}:
            return _demo()
        report = run_pipeline(args.input, args.output)
        print(json.dumps(asdict(report), sort_keys=True))
        return 0
    except (OSError, ValueError, PipelineError) as error:
        print(f"run failed: {type(error).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
