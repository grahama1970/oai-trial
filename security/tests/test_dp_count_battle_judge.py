from __future__ import annotations

import json
from pathlib import Path

from security.battle import dp_count_judge


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
    "sampling_contract": dp_count_judge.EXPECTED_SAMPLING_CONTRACT,
    "raw_values_persisted": False,
}


def _case_root(tmp_path: Path, receipt: dict) -> Path:
    run = tmp_path / "run"
    case = run / "plan-cases" / "dp-count-populated"
    out = run / "out" / "dp-count-populated"
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
            }
        ),
        encoding="utf-8",
    )
    (out / "receipt.json").write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return out


def test_dp_count_judge_rejects_boolean_noisy_count(tmp_path: Path) -> None:
    receipt = dict(BASE_RECEIPT, noisy_count=True)

    result = dp_count_judge.judge(str(_case_root(tmp_path, receipt)), {})

    assert result["passed"] is False
    assert any("noisy_count" in violation for violation in result["violations"])


def test_dp_count_judge_rejects_unnoised_labeled_count_without_sampling_contract(tmp_path: Path) -> None:
    receipt = dict(BASE_RECEIPT, noisy_count=2)
    receipt.pop("sampling_contract")

    result = dp_count_judge.judge(str(_case_root(tmp_path, receipt)), {})

    assert result["passed"] is False
    assert any("sampling contract" in violation for violation in result["violations"])
    assert result["evidence"]["true_count_recomputed_for_control"] is True


def test_dp_count_judge_accepts_replayable_receipt_with_sampling_contract(tmp_path: Path) -> None:
    result = dp_count_judge.judge(str(_case_root(tmp_path, BASE_RECEIPT)), {})

    assert result["passed"] is True
    assert result["evidence"]["sampling_contract_verified"] is True
