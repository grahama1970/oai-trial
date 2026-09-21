#!/usr/bin/env python3
"""Retained real-path check for ARX-style population k-map bounds."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


with tempfile.TemporaryDirectory(prefix="population-k-map-") as directory:
    root = Path(directory)
    release = root / "release.csv"
    population = root / "population.csv"
    release.write_text("zip,age\na,20\na,20\nb,30\n", encoding="utf-8")
    population.write_text(
        "zip,age\na,20\na,20\na,20\na,20\nb,30\nb,30\n", encoding="utf-8"
    )
    completed = subprocess.run(  # noqa: S603 (fixed local executable and argv)
        [
            ".venv/bin/anonymization-trial",
            "population-k-map",
            "--release",
            str(release),
            "--population",
            str(population),
            "--quasi-identifiers",
            "zip,age",
            "--minimum-k",
            "2",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    require(result["schema"] == "population_k_map.v1", "wrong schema")
    require(result["k_map_satisfied"] is True, "k-map should pass")
    require(result["minimum_population_class_size"] == 2, "wrong minimum population class size")
    require(result["maximum_population_class_size"] == 4, "wrong maximum population class size")
    require(result["receipt_contains_qi_values"] is False, "QI value persistence flag")
    require(result["raw_values_persisted"] is False, "raw persistence flag")
    require("20" not in completed.stdout and "30" not in completed.stdout, "raw value leak")

    population.write_text("zip,age\na,20\n", encoding="utf-8")
    rejected = subprocess.run(  # noqa: S603 (fixed local executable and argv)
        [
            ".venv/bin/anonymization-trial",
            "population-k-map",
            "--release",
            str(release),
            "--population",
            str(population),
            "--quasi-identifiers",
            "zip,age",
            "--minimum-k",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    require(rejected.returncode == 2, "unsafe k-map release must fail closed")
    reject_receipt = json.loads(rejected.stdout)
    require(reject_receipt["verdict"] == "k_map_violation", "wrong reject verdict")
    require(reject_receipt["violating_release_classes"] == 2, "wrong violation count")
    require("20" not in rejected.stdout and "30" not in rejected.stdout, "reject raw value leak")

    invalid_cases = [
        ("duplicate-release-header", "zip,zip\na,20\n", "zip,age\na,20\na,20\n"),
        ("short-release-row", "zip,age\na\n", "zip,age\na,20\na,20\n"),
        ("blank-release-qi", "zip,age\na,\n", "zip,age\na,20\na,20\n"),
        ("short-population-row", "zip,age\na,20\n", "zip,age\na\na,20\n"),
        ("blank-population-qi", "zip,age\na,20\n", "zip,age\na,\na,20\n"),
    ]
    for label, release_text, population_text in invalid_cases:
        release.write_text(release_text, encoding="utf-8")
        population.write_text(population_text, encoding="utf-8")
        invalid = subprocess.run(  # noqa: S603 (fixed local executable and argv)
            [
                ".venv/bin/anonymization-trial",
                "population-k-map",
                "--release",
                str(release),
                "--population",
                str(population),
                "--quasi-identifiers",
                "zip,age",
                "--minimum-k",
                "2",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        require(invalid.returncode == 1, f"{label} must fail closed")
        require(invalid.stdout == "", f"{label} must not emit a release receipt")
        require(invalid.stderr.strip() == "run failed: ValueError", f"{label} error leak")
        require("20" not in invalid.stderr and "30" not in invalid.stderr, f"{label} raw leak")

print("POPULATION_K_MAP_REAL_PATH_VERIFIED")
