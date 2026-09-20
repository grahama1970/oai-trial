#!/usr/bin/env python3
"""Retained real-path check for the one-query ARX-style DP count release."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


with tempfile.TemporaryDirectory(prefix="dp-count-eval-") as directory:
    source = Path(directory) / "people.csv"
    source.write_text("condition\nA\nA\nB\n", encoding="utf-8")
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "anonymization_trial",
            "dp-count",
            "--input",
            str(source),
            "--column",
            "condition",
            "--equals",
            "A",
            "--epsilon",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(process.stdout)
    assert receipt["schema"] == "differentially_private_count.v1"
    assert receipt["mechanism"] == "exact_two_sided_geometric_p_half"
    assert receipt["privacy_guarantee"] == "pure_epsilon_differential_privacy"
    assert receipt["formal_epsilon_upper_bound"] == 0.7
    assert receipt["adjacency"] == "add_remove_one_record"
    assert receipt["epsilon"] == 1.0 and receipt["sensitivity"] == 1
    assert receipt["composition"] == "single_query_only"
    assert receipt["cryptographic_randomness"] is True
    assert receipt["raw_values_persisted"] is False
    assert receipt["noisy_count"] >= 0
    assert "condition" not in process.stdout and '"A"' not in process.stdout

    empty = Path(directory) / "empty.csv"
    empty.write_text("condition\n", encoding="utf-8")
    empty_process = subprocess.run(
        [
            sys.executable,
            "-m",
            "anonymization_trial",
            "dp-count",
            "--input",
            str(empty),
            "--column",
            "condition",
            "--equals",
            "A",
            "--epsilon",
            "0.7",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    empty_receipt = json.loads(empty_process.stdout)
    assert empty_receipt["schema"] == "differentially_private_count.v1"
    assert empty_receipt["adjacency"] == "add_remove_one_record"
    assert empty_receipt["noisy_count"] >= 0
    assert "condition" not in empty_process.stdout and '"A"' not in empty_process.stdout
print("DP_COUNT_REAL_PATH_VERIFIED")
