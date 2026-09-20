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
from decimal import Decimal
from pathlib import Path

from .contextual_graph import audit_contextual_graph
from .errors import AnonError
from .fixture import generate_fixture
from .model_privacy import assess_leakpro_applicability, run_gradient_inversion_attack
from .multimodal import MultimodalError, redact_document
from .pipeline import _DOES_NOT_ESTABLISH, PipelineError, _preflight, run_pipeline
from .policy import load_policy
from .privacy_risk import assess_stable_pseudonym_frequency, write_private_report
from .tabular_privacy import (
    audit_attribute_inference,
    audit_csv,
    audit_delta_presence,
    audit_multiple_sensitive_attributes,
    audit_population_reidentification,
    audit_singling_out,
    audit_two_view_linkability,
    enforce_advanced_privacy_transform,
    generalize_with_hierarchies,
    locally_generalize_with_hierarchies,
    microaggregate_and_code,
    release_dp_count,
    release_dp_counts,
    release_dp_counts_persistent,
    suppress_small_classes,
)
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


def _risk_audit_cmd(input_root: Path, output: Path, min_frequency: int) -> int:
    if output.resolve().is_relative_to(input_root.resolve()):
        raise ValueError("risk receipt must be outside the immutable release")
    result = assess_stable_pseudonym_frequency(input_root, min_frequency)
    write_private_report(output, result)
    print(json.dumps({"risk_audit": result["verdict"], "receipt": str(output)}, sort_keys=True))
    return 2 if result["verdict"] == "linkage_risk" else 0


def _contextual_graph_cmd(input_path: Path, output: Path, min_shared_clues: int) -> int:
    if output.exists():
        raise FileExistsError("output already exists")
    result = audit_contextual_graph(input_path, min_shared_clues)
    write_private_report(output, result)
    summary = {"contextual_graph": result["verdict"], "receipt": str(output)}
    print(json.dumps(summary, sort_keys=True))
    return 2 if result["verdict"] == "block" else 0


def _dp_count_cmd(input_path: Path, column: str, equals: str, epsilon: Decimal) -> int:
    print(
        json.dumps(
            release_dp_count(input_path, column, equals, epsilon),
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _dp_count_batch_cmd(
    input_path: Path,
    query_plan: Path,
    maximum_epsilon: Decimal,
    budget_ledger: Path | None,
    budget_id: str | None,
) -> int:
    queries = json.loads(query_plan.read_text(encoding="utf-8"), parse_float=Decimal)
    if not isinstance(queries, list):
        raise ValueError("query plan must be a JSON list")
    if (budget_ledger is None) != (budget_id is None):
        raise ValueError("--budget-ledger and --budget-id must be supplied together")
    result = (
        release_dp_counts_persistent(
            input_path, queries, maximum_epsilon, budget_ledger, budget_id
        )
        if budget_ledger is not None and budget_id is not None
        else release_dp_counts(input_path, queries, maximum_epsilon)
    )
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


def _delta_presence_cmd(
    release: Path, population: Path, quasi_identifiers: str
) -> int:
    qis = [value for value in quasi_identifiers.split(",") if value]
    print(json.dumps(audit_delta_presence(release, population, qis), sort_keys=True))
    return 0


def _population_risk_cmd(
    release: Path, population: Path, quasi_identifiers: str
) -> int:
    qis = [value for value in quasi_identifiers.split(",") if value]
    print(
        json.dumps(
            audit_population_reidentification(release, population, qis),
            sort_keys=True,
        )
    )
    return 0


def _tabular_risk_cmd(
    input_path: Path,
    quasi_identifiers: str,
    sensitive: str,
    raw_input: Path | None = None,
    condition_on_other_sensitive: bool = False,
) -> int:
    qis = [value for value in quasi_identifiers.split(",") if value]
    sensitive_attributes = [value for value in sensitive.split(",") if value]
    if not sensitive_attributes:
        raise ValueError("at least one sensitive attribute is required")
    result = (
        audit_csv(input_path, qis, sensitive_attributes[0], raw_input)
        if len(sensitive_attributes) == 1
        else audit_multiple_sensitive_attributes(
            input_path,
            qis,
            sensitive_attributes,
            raw_input,
            condition_on_other_sensitive=condition_on_other_sensitive,
        )
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _attribute_inference_cmd(
    release: Path,
    evaluation: Path,
    quasi_identifiers: str,
    sensitive: str,
    output: Path,
    group_by: str | None = None,
    predictor: str = "nearest_neighbor",
) -> int:
    if output.exists():
        raise FileExistsError("output already exists")
    result = audit_attribute_inference(
        release,
        evaluation,
        [value for value in quasi_identifiers.split(",") if value],
        sensitive,
        group_by,
        predictor,
    )
    write_private_report(output, result)
    print(
        json.dumps(
            {"attribute_inference": result["verdict"], "receipt": str(output)}, sort_keys=True
        )
    )
    return 2 if result["verdict"] == "attribute_inference_risk" else 0


def _singling_out_cmd(
    input_path: Path,
    quasi_identifiers: str,
    output: Path,
    max_predicate_size: int | None,
    control: Path | None = None,
) -> int:
    if output.exists():
        raise FileExistsError("output already exists")
    result = audit_singling_out(
        input_path,
        [value for value in quasi_identifiers.split(",") if value],
        max_predicate_size,
        control,
    )
    write_private_report(output, result)
    print(json.dumps({"singling_out": result["verdict"], "receipt": str(output)}, sort_keys=True))
    return 2 if result["verdict"] == "singling_out_risk" else 0


def _two_view_linkability_cmd(
    release: Path,
    auxiliary_a: Path,
    auxiliary_b: Path,
    subject_id: str,
    columns_a: str,
    columns_b: str,
    output: Path,
    control: Path | None = None,
) -> int:
    if output.exists():
        raise FileExistsError("output already exists")
    result = audit_two_view_linkability(
        release,
        auxiliary_a,
        auxiliary_b,
        subject_id,
        [value for value in columns_a.split(",") if value],
        [value for value in columns_b.split(",") if value],
        control,
    )
    write_private_report(output, result)
    print(
        json.dumps(
            {"two_view_linkability": result["verdict"], "receipt": str(output)}, sort_keys=True
        )
    )
    return 2 if result["verdict"] == "linkage_risk" else 0


def _model_privacy_cmd(
    release_kind: str,
    model: Path | None,
    gradients: Path | None,
    output: Path,
) -> int:
    result = assess_leakpro_applicability(
        release_kind=release_kind, model=model, gradients=gradients
    )
    write_private_report(output, result)
    print(json.dumps({"model_privacy": result["verdict"], "receipt": str(output)}, sort_keys=True))
    return 2 if result["verdict"] == "adapter_required" else 0


def _gradient_inversion_cmd(gradients: Path, output: Path) -> int:
    if output.exists():
        raise FileExistsError("output already exists")
    result = run_gradient_inversion_attack(gradients)
    write_private_report(output, result)
    print(
        json.dumps(
            {"gradient_inversion": result["verdict"], "receipt": str(output)}, sort_keys=True
        )
    )
    return 2 if result["verdict"] == "reconstruction_signal" else 0


def _tabular_suppress_cmd(
    input_path: Path, output: Path, quasi_identifiers: str, minimum_k: int
) -> int:
    result = suppress_small_classes(
        input_path, output, [value for value in quasi_identifiers.split(",") if value], minimum_k
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _tabular_generalize_cmd(
    input_path: Path,
    output: Path,
    quasi_identifiers: str,
    sensitive: str,
    hierarchy: Path,
    minimum_k: int,
    max_suppression_fraction: float,
) -> int:
    mappings = json.loads(hierarchy.read_text(encoding="utf-8"))
    if not isinstance(mappings, dict):
        raise ValueError("hierarchy must be a JSON object")
    result = generalize_with_hierarchies(
        input_path,
        output,
        [value for value in quasi_identifiers.split(",") if value],
        sensitive,
        mappings,
        minimum_k,
        max_suppression_fraction,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _tabular_local_generalize_cmd(
    input_path: Path,
    output: Path,
    quasi_identifiers: str,
    sensitive: str,
    hierarchy: Path,
    minimum_k: int,
) -> int:
    mappings = json.loads(hierarchy.read_text(encoding="utf-8"))
    if not isinstance(mappings, dict):
        raise ValueError("hierarchy must be a JSON object")
    result = locally_generalize_with_hierarchies(
        input_path,
        output,
        [value for value in quasi_identifiers.split(",") if value],
        sensitive,
        mappings,
        minimum_k,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _tabular_advanced_transform_cmd(
    input_path: Path,
    output: Path,
    quasi_identifiers: str,
    sensitive: str,
    hierarchy: Path,
    minimum_k: int,
    maximum_alpha: float,
    recursive_l: int,
    maximum_recursive_c: float,
    maximum_beta: float,
    maximum_t: float,
    maximum_numeric_emd_t: float | None,
    minimum_entropy_l: float | None,
    maximum_delta_disclosure: float | None,
    max_suppression_fraction: float,
) -> int:
    mappings = json.loads(hierarchy.read_text(encoding="utf-8"))
    if not isinstance(mappings, dict):
        raise ValueError("hierarchy must be a JSON object")
    result = enforce_advanced_privacy_transform(
        input_path,
        output,
        [value for value in quasi_identifiers.split(",") if value],
        sensitive,
        mappings,
        minimum_k=minimum_k,
        maximum_alpha=maximum_alpha,
        recursive_l=recursive_l,
        maximum_recursive_c=maximum_recursive_c,
        maximum_beta=maximum_beta,
        maximum_t=maximum_t,
        maximum_numeric_emd_t=maximum_numeric_emd_t,
        minimum_entropy_l=minimum_entropy_l,
        maximum_delta_disclosure=maximum_delta_disclosure,
        max_suppression_fraction=max_suppression_fraction,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _tabular_microaggregate_cmd(
    input_path: Path,
    output: Path,
    quasi_identifiers: str,
    sensitive: str,
    numeric_columns: str,
    minimum_k: int,
    bounds_path: Path,
) -> int:
    raw_bounds = json.loads(bounds_path.read_text(encoding="utf-8"))
    if not isinstance(raw_bounds, dict):
        raise ValueError("bounds must be a JSON object")
    bounds: dict[str, tuple[float | None, float | None]] = {}
    for name, limits in raw_bounds.items():
        if not isinstance(name, str) or not isinstance(limits, list) or len(limits) != 2:
            raise ValueError("each bound must be [lower, upper]")
        if any(value is not None and not isinstance(value, (int, float)) for value in limits):
            raise ValueError("coding bounds must be numeric or null")
        bounds[name] = (limits[0], limits[1])
    result = microaggregate_and_code(
        input_path,
        output,
        [value for value in quasi_identifiers.split(",") if value],
        sensitive,
        [value for value in numeric_columns.split(",") if value],
        minimum_k,
        bounds,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _inspect_cmd(output_root: Path) -> int:
    report = json.loads((output_root / "report.json").read_text(encoding="utf-8"))
    safe_keys = (
        "status",
        "files_processed",
        "records_processed",
        "replacements_applied",
        "verification_passed",
        "algorithm_version",
        "scope_id",
        "key_mode",
        "policy_sha256",
        "corpus_manifest_sha256",
        "does_not_establish",
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
    risk = subparsers.add_parser("risk-audit", help="audit stable-pseudonym frequency linkage")
    risk.add_argument("--input", type=Path, required=True, help="verified release directory")
    risk.add_argument("--output", type=Path, required=True, help="new private receipt path")
    risk.add_argument("--min-frequency", type=int, default=2)
    contextual_graph = subparsers.add_parser(
        "contextual-graph-risk",
        help="run an authorized aggregate-only multi-hop contextual linkage attack",
    )
    contextual_graph.add_argument("--input", type=Path, required=True)
    contextual_graph.add_argument("--output", type=Path, required=True)
    contextual_graph.add_argument("--min-shared-clues", type=int, default=2)
    tabular = subparsers.add_parser(
        "tabular-risk", help="measure declared-QI k/l/t privacy metrics for CSV"
    )
    tabular.add_argument("--input", type=Path, required=True)
    tabular.add_argument(
        "--quasi-identifiers", required=True, help="comma-separated declared columns"
    )
    tabular.add_argument(
        "--sensitive", required=True, help="comma-separated declared sensitive columns"
    )
    tabular.add_argument(
        "--raw-input",
        type=Path,
        help="optional authorized pre-suppression CSV for suppression-aware utility metrics",
    )
    tabular.add_argument(
        "--condition-on-other-sensitive",
        action="store_true",
        help="match pyCANON gen=False by adding other sensitive columns to each audit key",
    )
    dp_count = subparsers.add_parser(
        "dp-count", help="release one epsilon-DP predicate count with exact geometric noise"
    )
    dp_count.add_argument("--input", type=Path, required=True)
    dp_count.add_argument("--column", required=True)
    dp_count.add_argument("--equals", required=True)
    dp_count.add_argument("--epsilon", type=Decimal, required=True)
    dp_count_batch = subparsers.add_parser(
        "dp-count-batch", help="release composed exact-geometric epsilon-DP counts within one privacy budget"
    )
    dp_count_batch.add_argument("--input", type=Path, required=True)
    dp_count_batch.add_argument("--query-plan", type=Path, required=True)
    dp_count_batch.add_argument("--maximum-epsilon", type=Decimal, required=True)
    dp_count_batch.add_argument(
        "--budget-ledger", type=Path, help="private local ledger for cross-invocation accounting"
    )
    dp_count_batch.add_argument(
        "--budget-id", help="authorization-domain identifier (only its SHA-256 is persisted)"
    )
    delta_presence = subparsers.add_parser(
        "delta-presence-risk", help="measure authorized QI sample presence against a population"
    )
    delta_presence.add_argument("--release", type=Path, required=True)
    delta_presence.add_argument("--population", type=Path, required=True)
    delta_presence.add_argument("--quasi-identifiers", required=True)
    population_risk = subparsers.add_parser(
        "population-reidentification-risk",
        help="measure aggregate prosecutor, journalist, and marketer risk against a population",
    )
    population_risk.add_argument("--release", type=Path, required=True)
    population_risk.add_argument("--population", type=Path, required=True)
    population_risk.add_argument("--quasi-identifiers", required=True)
    attribute_inference = subparsers.add_parser(
        "attribute-inference-risk", help="measure authorized sensitive-attribute inference"
    )
    attribute_inference.add_argument("--release", type=Path, required=True)
    attribute_inference.add_argument("--evaluation", type=Path, required=True)
    attribute_inference.add_argument("--quasi-identifiers", required=True)
    attribute_inference.add_argument("--sensitive", required=True)
    attribute_inference.add_argument(
        "--group-by", help="optional authorized group column for aggregate disparity bounds"
    )
    attribute_inference.add_argument(
        "--predictor",
        choices=("nearest_neighbor", "exact_match"),
        default="nearest_neighbor",
        help="authorized built-in predictor (no arbitrary model loading)",
    )
    attribute_inference.add_argument("--output", type=Path, required=True)
    singling_out = subparsers.add_parser(
        "singling-out-risk", help="measure exact singling-out on authorized columns"
    )
    singling_out.add_argument("--input", type=Path, required=True)
    singling_out.add_argument("--quasi-identifiers", required=True)
    singling_out.add_argument("--max-predicate-size", type=int)
    singling_out.add_argument("--control", type=Path, help="optional authorized control CSV")
    singling_out.add_argument("--output", type=Path, required=True)
    linkability = subparsers.add_parser(
        "two-view-linkability", help="measure authorized two-view nearest-neighbor linkage"
    )
    linkability.add_argument("--release", type=Path, required=True)
    linkability.add_argument("--auxiliary-a", type=Path, required=True)
    linkability.add_argument("--auxiliary-b", type=Path, required=True)
    linkability.add_argument("--subject-id", required=True)
    linkability.add_argument("--columns-a", required=True)
    linkability.add_argument("--columns-b", required=True)
    linkability.add_argument("--control", type=Path, help="optional authorized control CSV")
    linkability.add_argument("--output", type=Path, required=True)
    model_privacy = subparsers.add_parser(
        "model-privacy-applicability",
        help="route LeakPro-style attacks by released artifact type",
    )
    model_privacy.add_argument(
        "--release-kind", choices=("file_only", "learned_model"), required=True
    )
    model_privacy.add_argument("--model", type=Path)
    model_privacy.add_argument("--gradients", type=Path)
    model_privacy.add_argument("--output", type=Path, required=True)
    gradient_inversion = subparsers.add_parser(
        "model-gradient-inversion",
        help="run an authorized bounded affine gradient-inversion attack",
    )
    gradient_inversion.add_argument("--gradients", type=Path, required=True)
    gradient_inversion.add_argument("--output", type=Path, required=True)
    suppress = subparsers.add_parser(
        "tabular-suppress", help="suppress CSV equivalence classes below k"
    )
    suppress.add_argument("--input", type=Path, required=True)
    suppress.add_argument("--output", type=Path, required=True)
    suppress.add_argument("--quasi-identifiers", required=True)
    suppress.add_argument("--minimum-k", type=int, required=True)
    generalize = subparsers.add_parser(
        "tabular-generalize", help="apply authorized hierarchies with bounded suppression"
    )
    generalize.add_argument("--input", type=Path, required=True)
    generalize.add_argument("--output", type=Path, required=True)
    generalize.add_argument("--quasi-identifiers", required=True)
    generalize.add_argument("--sensitive", required=True)
    generalize.add_argument("--hierarchy", type=Path, required=True)
    generalize.add_argument("--minimum-k", type=int, required=True)
    generalize.add_argument("--max-suppression-fraction", type=float, default=0.0)
    local_generalize = subparsers.add_parser(
        "tabular-local-generalize", help="apply authorized hierarchies only to unsafe classes"
    )
    local_generalize.add_argument("--input", type=Path, required=True)
    local_generalize.add_argument("--output", type=Path, required=True)
    local_generalize.add_argument("--quasi-identifiers", required=True)
    local_generalize.add_argument("--sensitive", required=True)
    local_generalize.add_argument("--hierarchy", type=Path, required=True)
    local_generalize.add_argument("--minimum-k", type=int, required=True)
    advanced = subparsers.add_parser(
        "tabular-advanced-transform",
        help="apply authorized hierarchies and enforce advanced privacy bounds",
    )
    advanced.add_argument("--input", type=Path, required=True)
    advanced.add_argument("--output", type=Path, required=True)
    advanced.add_argument("--quasi-identifiers", required=True)
    advanced.add_argument("--sensitive", required=True)
    advanced.add_argument("--hierarchy", type=Path, required=True)
    advanced.add_argument("--minimum-k", type=int, required=True)
    advanced.add_argument("--maximum-alpha", type=float, required=True)
    advanced.add_argument("--recursive-l", type=int, required=True)
    advanced.add_argument("--maximum-recursive-c", type=float, required=True)
    advanced.add_argument("--maximum-beta", type=float, required=True)
    advanced.add_argument("--maximum-t", type=float, required=True)
    advanced.add_argument("--maximum-numeric-emd-t", type=float)
    advanced.add_argument("--minimum-entropy-l", type=float)
    advanced.add_argument("--maximum-delta-disclosure", type=float)
    advanced.add_argument("--max-suppression-fraction", type=float, default=0.0)
    microaggregate = subparsers.add_parser(
        "tabular-microaggregate", help="apply authorized numeric coding and microaggregation"
    )
    microaggregate.add_argument("--input", type=Path, required=True)
    microaggregate.add_argument("--output", type=Path, required=True)
    microaggregate.add_argument("--quasi-identifiers", required=True)
    microaggregate.add_argument("--sensitive", required=True)
    microaggregate.add_argument("--numeric-columns", required=True)
    microaggregate.add_argument("--minimum-k", type=int, required=True)
    microaggregate.add_argument("--bounds", type=Path, required=True)
    document = subparsers.add_parser(
        "redact-document", help="OCR-redact policy literals from an image or PDF"
    )
    document.add_argument("--input", type=Path, required=True)
    document.add_argument("--policy", type=Path, required=True)
    document.add_argument("--output", type=Path, required=True)
    document.add_argument(
        "--receipt", type=Path, required=True, help="new private receipt outside the release"
    )
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
        if args.command == "risk-audit":
            return _risk_audit_cmd(args.input, args.output, args.min_frequency)
        if args.command == "contextual-graph-risk":
            return _contextual_graph_cmd(args.input, args.output, args.min_shared_clues)
        if args.command == "tabular-risk":
            return _tabular_risk_cmd(
                args.input,
                args.quasi_identifiers,
                args.sensitive,
                args.raw_input,
                args.condition_on_other_sensitive,
            )
        if args.command == "dp-count":
            return _dp_count_cmd(args.input, args.column, args.equals, args.epsilon)
        if args.command == "dp-count-batch":
            return _dp_count_batch_cmd(
                args.input,
                args.query_plan,
                args.maximum_epsilon,
                args.budget_ledger,
                args.budget_id,
            )
        if args.command == "delta-presence-risk":
            return _delta_presence_cmd(
                args.release, args.population, args.quasi_identifiers
            )
        if args.command == "population-reidentification-risk":
            return _population_risk_cmd(
                args.release, args.population, args.quasi_identifiers
            )
        if args.command == "attribute-inference-risk":
            return _attribute_inference_cmd(
                args.release,
                args.evaluation,
                args.quasi_identifiers,
                args.sensitive,
                args.output,
                args.group_by,
                args.predictor,
            )
        if args.command == "singling-out-risk":
            return _singling_out_cmd(
                args.input,
                args.quasi_identifiers,
                args.output,
                args.max_predicate_size,
                args.control,
            )
        if args.command == "two-view-linkability":
            return _two_view_linkability_cmd(
                args.release,
                args.auxiliary_a,
                args.auxiliary_b,
                args.subject_id,
                args.columns_a,
                args.columns_b,
                args.output,
                args.control,
            )
        if args.command == "model-privacy-applicability":
            return _model_privacy_cmd(
                args.release_kind, args.model, args.gradients, args.output
            )
        if args.command == "model-gradient-inversion":
            return _gradient_inversion_cmd(args.gradients, args.output)
        if args.command == "tabular-suppress":
            return _tabular_suppress_cmd(
                args.input, args.output, args.quasi_identifiers, args.minimum_k
            )
        if args.command == "tabular-generalize":
            return _tabular_generalize_cmd(
                args.input,
                args.output,
                args.quasi_identifiers,
                args.sensitive,
                args.hierarchy,
                args.minimum_k,
                args.max_suppression_fraction,
            )
        if args.command == "tabular-local-generalize":
            return _tabular_local_generalize_cmd(
                args.input,
                args.output,
                args.quasi_identifiers,
                args.sensitive,
                args.hierarchy,
                args.minimum_k,
            )
        if args.command == "tabular-advanced-transform":
            return _tabular_advanced_transform_cmd(
                args.input,
                args.output,
                args.quasi_identifiers,
                args.sensitive,
                args.hierarchy,
                args.minimum_k,
                args.maximum_alpha,
                args.recursive_l,
                args.maximum_recursive_c,
                args.maximum_beta,
                args.maximum_t,
                args.maximum_numeric_emd_t,
                args.minimum_entropy_l,
                args.maximum_delta_disclosure,
                args.max_suppression_fraction,
            )
        if args.command == "tabular-microaggregate":
            return _tabular_microaggregate_cmd(
                args.input,
                args.output,
                args.quasi_identifiers,
                args.sensitive,
                args.numeric_columns,
                args.minimum_k,
                args.bounds,
            )
        if args.command == "redact-document":
            result = redact_document(args.input, args.policy, args.output, args.receipt)
            print(json.dumps(result, sort_keys=True))
            return 0
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
                    print(
                        json.dumps(
                            {
                                "discovery": "review_required",
                                "counts": review.counts,
                                "release_ready": False,
                            },
                            sort_keys=True,
                        )
                    )
                else:
                    from .discovery import approve

                    print(
                        json.dumps(
                            approve(
                                bundle,
                                args.review,
                                args.approve,
                                args.output,
                                args.input,
                                args.policy,
                            ),
                            sort_keys=True,
                        )
                    )
            return 0
        report = run_pipeline(args.input, args.output)
        print(json.dumps(asdict(report), sort_keys=True))
        return 0
    except (OSError, ValueError, PipelineError, AnonError, MultimodalError) as error:
        # Privacy-safe: report the error class/code only, never raw data.
        detail = error.code.value if isinstance(error, AnonError) else type(error).__name__
        marker = " BATTLE_CONTRACT_REJECT" if isinstance(error, AnonError) else ""
        print(f"run failed: {detail}{marker}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
