"""Battle Judge for aggregate-only DP count receipts."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_SAMPLING_CONTRACT = {
    "noise_family": "two_sided_geometric",
    "parameterization": "p_half",
    "support": "all_integers",
    "zero_noise_allowed": True,
    "postprocessing": "clamp_to_nonnegative",
    "privacy_loss_upper_bound": 0.7,
}


def _load_battle_case(output_root: Path) -> tuple[dict[str, Any], list[dict[str, str]]] | None:
    """Find the frozen Battle input beside the output for replayable judging."""
    case_id = output_root.name
    candidate = output_root.parent.parent / "plan-cases" / case_id
    case_json = candidate / "case.json"
    data_csv = candidate / "data.csv"
    if not case_json.is_file() or not data_csv.is_file():
        return None
    case = json.loads(case_json.read_text(encoding="utf-8"))
    with data_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return case, rows


def _true_count_from_case(case: dict[str, Any], rows: list[dict[str, str]]) -> int:
    column = case.get("column")
    equals_sha256 = case.get("equals_sha256")
    if not isinstance(column, str) or not isinstance(equals_sha256, str):
        raise ValueError("case must declare column and equals_sha256")
    return sum(
        hashlib.sha256(row.get(column, "").encode("utf-8")).hexdigest() == equals_sha256
        for row in rows
    )


def judge(target_dir: str, params: dict) -> dict:
    root = Path(target_dir)
    receipt_path = root / "receipt.json"
    violations: list[str] = []
    try:
        text = receipt_path.read_text(encoding="utf-8")
        receipt = json.loads(text)
    except Exception as exc:  # fail closed: unreadable receipt never proves release safety
        return {"passed": False, "violations": [f"dp-count receipt unreadable: {type(exc).__name__}"], "evidence": {}}

    if not isinstance(receipt, dict):
        return {"passed": False, "violations": ["dp-count receipt must be a JSON object"], "evidence": {}}

    forbidden = ["condition", '"A"', '"B"', "true_count", "predicate"]
    for token in forbidden:
        if token in text:
            violations.append(f"raw-or-predicate-token-persisted:{token}")
    expected = {
        "schema": "differentially_private_count.v1",
        "mechanism": "exact_two_sided_geometric_p_half",
        "privacy_guarantee": "pure_epsilon_differential_privacy",
        "adjacency": "add_remove_one_record",
        "composition": "single_query_only",
        "raw_values_persisted": False,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            violations.append(f"unexpected-{key}:{receipt.get(key)!r}")
    if receipt.get("formal_epsilon_upper_bound") != 0.7:
        violations.append("formal epsilon upper bound must be 0.7")
    if receipt.get("epsilon") != 0.7:
        violations.append("declared epsilon must match the battle contract")
    if receipt.get("sensitivity") != 1:
        violations.append("sensitivity must be one")
    noisy_count = receipt.get("noisy_count")
    if type(noisy_count) is not int or noisy_count < 0:  # noqa: E721 - bool is an int subclass
        violations.append("noisy_count must be a non-negative JSON integer, not boolean")
    if receipt.get("cryptographic_randomness") is not True:
        violations.append("battle target must use cryptographic randomness")
    if receipt.get("sampling_contract") != EXPECTED_SAMPLING_CONTRACT:
        violations.append("sampling contract must identify the exact geometric mechanism")

    replay = _load_battle_case(root)
    true_count = None
    if replay is None:
        violations.append("battle input case unavailable for replayable judge observation")
        case_schema = None
    else:
        case, rows = replay
        case_schema = case.get("schema")
        try:
            true_count = _true_count_from_case(case, rows)
        except Exception as exc:  # fail closed on malformed case controls
            violations.append(f"battle input case malformed: {type(exc).__name__}")
        if receipt.get("sampling_contract") != EXPECTED_SAMPLING_CONTRACT and noisy_count == true_count:
            violations.append("unnoised count cannot be accepted without the sampling contract")

    return {
        "passed": not violations,
        "violations": violations,
        "evidence": {
            "schema": receipt.get("schema"),
            "mechanism": receipt.get("mechanism"),
            "receipt_bytes": len(text.encode("utf-8")),
            "raw_values_persisted": receipt.get("raw_values_persisted"),
            "case_schema": case_schema,
            "true_count_recomputed_for_control": true_count is not None,
            "sampling_contract_verified": receipt.get("sampling_contract") == EXPECTED_SAMPLING_CONTRACT,
        },
    }
