#!/usr/bin/env python3
"""Replayable DP-count Battle proof controls without retaining raw predicates."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


spec = importlib.util.spec_from_file_location(
    "dp_count_judge", Path("security/battle/dp_count_judge.py")
)
judge_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(judge_module)

BASE_RECEIPT = {
    "schema": "differentially_private_count.v1",
    "mechanism": "exact_two_sided_geometric_p_half",
    "privacy_guarantee": "pure_epsilon_differential_privacy",
    "formal_epsilon_upper_bound": 0.7,
    "adjacency": "add_remove_one_record",
    "epsilon": 0.7,
    "sensitivity": 1,
    "noisy_count": 3,
    "clamped_to_nonnegative": True,
    "composition": "single_query_only",
    "cryptographic_randomness": True,
    "sampling_contract": judge_module.EXPECTED_SAMPLING_CONTRACT,
    "raw_values_persisted": False,
}


def make_case(root: Path, receipt: dict) -> Path:
    case = root / "plan-cases" / "dp-count-populated"
    out = root / "out" / "dp-count-populated"
    case.mkdir(parents=True)
    out.mkdir(parents=True)
    (case / "data.csv").write_text("condition\nA\nA\nB\n", encoding="utf-8")
    (case / "case.json").write_text(
        json.dumps(
            {
                "schema": "dp_count_battle_case.v1",
                "input": "data.csv",
                "column": "condition",
                "equals_sha256": "559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (out / "receipt.json").write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return out


with tempfile.TemporaryDirectory(prefix="dp-count-battle-replay-") as directory:
    root = Path(directory)
    good = judge_module.judge(str(make_case(root / "good", BASE_RECEIPT)), {})
    require(good["passed"] is True, "valid DP-count receipt should pass judge")

    bool_receipt = dict(BASE_RECEIPT, noisy_count=True)
    bool_result = judge_module.judge(str(make_case(root / "bool", bool_receipt)), {})
    require(bool_result["passed"] is False, "boolean noisy_count must fail judge")

    unnoised_receipt = dict(BASE_RECEIPT, noisy_count=2)
    unnoised_receipt.pop("sampling_contract")
    unnoised = judge_module.judge(str(make_case(root / "unnoised", unnoised_receipt)), {})
    require(unnoised["passed"] is False, "unnoised labeled count without sampling contract must fail")
    require(
        unnoised["evidence"].get("true_count_recomputed_for_control") is True,
        "judge must independently recompute the Battle control count",
    )

print(
    json.dumps(
        {
            "schema": "dp_count_battle_replay_eval.v1",
            "judge_controls": {
                "valid_receipt_passed": True,
                "boolean_noisy_count_rejected": True,
                "unnoised_without_sampling_contract_rejected": True,
                "true_count_recomputed_for_control": True,
            },
            "receipt_contains_raw_values": False,
            "raw_values_persisted": False,
        },
        sort_keys=True,
    )
)
