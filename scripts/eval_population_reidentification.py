#!/usr/bin/env python3
"""Retained real-path check for aggregate population re-identification risk."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


with tempfile.TemporaryDirectory(prefix="population-risk-") as directory:
    root = Path(directory)
    release = root / "release.csv"
    population = root / "population.csv"
    release.write_text("zip,age\na,20\na,20\nb,30\n", encoding="utf-8")
    population.write_text(
        "zip,age\na,20\na,20\na,20\na,20\nb,30\nc,40\n", encoding="utf-8"
    )
    completed = subprocess.run(  # noqa: S603 (fixed local executable and argv)
        [
            ".venv/bin/anonymization-trial",
            "population-reidentification-risk",
            "--release",
            str(release),
            "--population",
            str(population),
            "--quasi-identifiers",
            "zip,age",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    require(result["schema"] == "population_reidentification_risk.v1", "wrong schema")
    require(result["maximum_prosecutor_risk"] == 1.0, "wrong prosecutor risk")
    require(result["maximum_journalist_risk"] == 1.0, "wrong journalist risk")
    require(result["marketer_success_rate"] == 0.5, "wrong marketer risk")
    require(result["sample_uniqueness_rate"] == 0.333333333333, "wrong sample uniqueness")
    require(
        result["population_uniqueness_rate"] == 0.333333333333,
        "wrong population uniqueness",
    )
    require(result["raw_values_persisted"] is False, "raw persistence flag")
    require("20" not in completed.stdout and "30" not in completed.stdout, "raw value leak")

print("POPULATION_REIDENTIFICATION_VERIFIED")
