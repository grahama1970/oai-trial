#!/usr/bin/env python3
"""Retained real-path check for composed epsilon-DP count releases."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


with tempfile.TemporaryDirectory(prefix="dp-count-batch-eval-") as directory:
    root = Path(directory)
    source = root / "people.csv"
    plan = root / "queries.json"
    source.write_text("condition\nA\nA\nB\n", encoding="utf-8")
    plan.write_text(
        json.dumps(
            [
                {"column": "condition", "equals": "A", "epsilon": 0.7},
                {"column": "condition", "equals": "B", "epsilon": 0.7},
            ]
        ),
        encoding="utf-8",
    )
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "anonymization_trial",
            "dp-count-batch",
            "--input",
            str(source),
            "--query-plan",
            str(plan),
            "--maximum-epsilon",
            "1.4",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(process.stdout)
    assert receipt["schema"] == "differentially_private_count_batch.v1"
    assert receipt["composition"] == "basic_sequential_composition"
    assert receipt["mechanism"] == "exact_two_sided_geometric_p_half"
    assert receipt["privacy_guarantee"] == "pure_epsilon_differential_privacy"
    assert receipt["formal_epsilon_upper_bound_per_query"] == 0.7
    assert receipt["total_epsilon"] == 1.4
    assert receipt["maximum_epsilon"] == 1.4
    assert receipt["remaining_epsilon"] == 0.0
    assert receipt["query_count"] == len(receipt["noisy_counts"]) == 2
    assert receipt["cryptographic_randomness"] is True
    assert receipt["raw_values_persisted"] is False
    assert "condition" not in process.stdout and '"A"' not in process.stdout and '"B"' not in process.stdout

    empty = root / "empty.csv"
    empty.write_text("condition\n", encoding="utf-8")
    empty_process = subprocess.run(
        [
            sys.executable,
            "-m",
            "anonymization_trial",
            "dp-count-batch",
            "--input",
            str(empty),
            "--query-plan",
            str(plan),
            "--maximum-epsilon",
            "1.4",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    empty_receipt = json.loads(empty_process.stdout)
    assert empty_receipt["schema"] == "differentially_private_count_batch.v1"
    assert empty_receipt["adjacency"] == "add_remove_one_record"
    assert empty_receipt["query_count"] == len(empty_receipt["noisy_counts"]) == 2
    assert all(count >= 0 for count in empty_receipt["noisy_counts"])
    assert "condition" not in empty_process.stdout and '"A"' not in empty_process.stdout and '"B"' not in empty_process.stdout

    rejected = subprocess.run(
        [
            sys.executable,
            "-m",
            "anonymization_trial",
            "dp-count-batch",
            "--input",
            str(source),
            "--query-plan",
            str(plan),
            "--maximum-epsilon",
            "1.3",
        ],
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0
    assert "condition" not in rejected.stderr and '"A"' not in rejected.stderr and '"B"' not in rejected.stderr

    plan.write_text(
        '[{"column":"condition","equals":"A","epsilon":1.0},'
        '{"column":"condition","equals":"B","epsilon":1e-30}]',
        encoding="utf-8",
    )
    tiny = subprocess.run(
        [
            sys.executable,
            "-m",
            "anonymization_trial",
            "dp-count-batch",
            "--input",
            str(source),
            "--query-plan",
            str(plan),
            "--maximum-epsilon",
            "1",
        ],
        capture_output=True,
        text=True,
    )
    assert tiny.returncode != 0
    assert "Infinity" not in tiny.stdout + tiny.stderr and "NaN" not in tiny.stdout + tiny.stderr
print("DP_COUNT_BATCH_REAL_PATH_VERIFIED")
