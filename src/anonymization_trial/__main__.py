"""CLI entry point: the two required commands plus operational inspection.

Required: ``demo`` (self-contained demonstration) and ``run --input --output``.
Operational polish (all self-contained, no server): ``preflight`` (validate a
bundle without producing data), ``verify`` (independently reverify an existing
release), ``inspect`` (render a release's safe evidence summary), and ``explain``
(print the mechanism/guarantees). Exit code is 0 only on success; handled errors
print a sanitized code to stderr and return non-zero (fail closed).
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
from .pipeline import _DOES_NOT_ESTABLISH, PipelineError, _preflight, run_pipeline
from .policy import load_policy
from .verification import verify_corpus

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


def _explain() -> int:
    """Print the mechanism and guarantees (no policy or data contents)."""
    print(
        json.dumps(
            {
                "matching": [
                    "original-input spans only; generated output is never rescanned",
                    "leftmost -> longest -> stable rule_id tie-break",
                ],
                "identity": [
                    "(data_type, subject_id) is the canonical pseudonym identity",
                    "aliases converge; distinct same-type identities are injective",
                ],
                "protected_values": ["sensitive/protected overlap is rejected at compile time"],
                "publication": [
                    "output staged privately; independently reread and verified",
                    "report.json written last and binds the corpus manifest digest",
                    "any failure exits non-zero and leaves no ready release",
                ],
                "encoding": [
                    "UTF-8 / UTF-8 BOM; no Unicode normalization",
                    "non-ASCII case-insensitive rules rejected in v1",
                ],
                "does_not_establish": list(_DOES_NOT_ESTABLISH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _preflight_cmd(input_root: Path) -> int:
    policy = load_policy(input_root / "policy.json")
    with tempfile.TemporaryDirectory(prefix="anon-preflight-") as tmp:
        files = _preflight(input_root, Path(tmp), policy)
    by_type: dict[str, int] = {}
    for _src, rel in files:
        by_type[rel.suffix.lower()] = by_type.get(rel.suffix.lower(), 0) + 1
    print(
        json.dumps(
            {
                "preflight": "PASS",
                "policy": {
                    "version": policy.version,
                    "rules": len(policy.rules),
                    "protected": len(policy.protected_values),
                },
                "corpus": {"files": len(files), "by_type": by_type},
                "ready_to_transform": True,
            },
            sort_keys=True,
        )
    )
    return 0


def _verify_cmd(input_root: Path, output_root: Path) -> int:
    policy = load_policy(input_root / "policy.json")
    verify_corpus(input_root / "corpus", output_root / "corpus", policy)
    print(json.dumps({"verify": "PASS", "output": str(output_root)}, sort_keys=True))
    return 0


def _inspect_cmd(output_root: Path) -> int:
    report = json.loads((output_root / "report.json").read_text(encoding="utf-8"))
    safe_keys = (
        "status", "files_processed", "records_processed", "replacements_applied",
        "verification_passed", "algorithm_version", "scope_id", "key_mode",
        "policy_sha256", "corpus_manifest_sha256", "does_not_establish",
    )
    print(json.dumps({k: report.get(k) for k in safe_keys}, indent=2, sort_keys=True))
    return 0 if report.get("status") == "ready" else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cross-format anonymization trial")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("demo", help="run the bundled self-contained demonstration")
    run = subparsers.add_parser("run", help="process a mounted input bundle")
    run.add_argument("--input", type=Path, default=Path("/trial/input"))
    run.add_argument("--output", type=Path, default=Path("/trial/output"))
    bench = subparsers.add_parser("bench-once", help="internal: one benchmark run as JSON")
    bench.add_argument("--records", type=int, required=True)
    pre = subparsers.add_parser("preflight", help="validate a bundle without producing data")
    pre.add_argument("--input", type=Path, default=Path("/trial/input"))
    ver = subparsers.add_parser("verify", help="independently reverify an existing release")
    ver.add_argument("--input", type=Path, default=Path("/trial/input"))
    ver.add_argument("--output", type=Path, default=Path("/trial/output"))
    ins = subparsers.add_parser("inspect", help="render a release's safe evidence summary")
    ins.add_argument("output", type=Path)
    subparsers.add_parser("explain", help="print the mechanism and guarantees")
    for name, help_text in (
        ("anonymize", "anonymize a file/folder with a separate policy"),
        ("discover", "propose RapidFuzz name aliases; never release or replace data"),
        ("approve-discovery", "approve explicit candidate IDs into a new exact policy"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--policy", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        if name == "discover":
            command.add_argument("--threshold", type=float, default=90)
            command.add_argument("--margin", type=float, default=5)
        elif name == "approve-discovery":
            command.add_argument("--review", type=Path, required=True)
            command.add_argument("--approve", action="append", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command in {None, "demo"}:
            return _demo()
        if args.command == "bench-once":
            print(json.dumps(_run_once(args.records), sort_keys=True))
            return 0
        if args.command == "explain":
            return _explain()
        if args.command == "preflight":
            return _preflight_cmd(args.input)
        if args.command == "verify":
            return _verify_cmd(args.input, args.output)
        if args.command == "inspect":
            return _inspect_cmd(args.output)
        if args.command in {"anonymize", "discover", "approve-discovery"}:
            from .bundle import input_bundle, separate_output

            args.output = separate_output(args.output, args.input, args.policy)
            with input_bundle(args.input, args.policy, args.output) as bundle:
                if args.command == "anonymize":
                    report = run_pipeline(bundle, args.output)
                    print(json.dumps(asdict(report), sort_keys=True))
                elif args.command == "discover":
                    from .discovery import discover, write_private

                    review = discover(bundle, args.threshold, args.margin)
                    write_private(args.output, asdict(review))
                    print(json.dumps({"discovery": "review_required", "counts": review.counts,
                                      "release_ready": False}, sort_keys=True))
                else:
                    from .discovery import approve

                    print(json.dumps(approve(bundle, args.review, args.approve, args.output,
                                             args.input, args.policy),
                                     sort_keys=True))
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
