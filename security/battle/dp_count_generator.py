"""Retained Battle cases for the DP count release gate."""
from __future__ import annotations

import json
from pathlib import Path


def _case(root: Path, case_id: str, csv_text: str) -> tuple[str, str, str]:
    case = root / case_id
    case.mkdir(parents=True, exist_ok=True)
    (case / "data.csv").write_text(csv_text, encoding="utf-8")
    (case / "case.json").write_text(
        json.dumps(
            {
                "schema": "dp_count_battle_case.v1",
                "input": "data.csv",
                "column": "condition",
                "equals_sha256": "559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd",
                "epsilon": "0.7",
                "must_omit_predicate": True,
                "must_omit_true_count": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return case_id, str(case), "MUST_ACCEPT"


def generate(work_dir, params):
    root = Path(work_dir)
    yield _case(root, "dp-count-populated", "condition\nA\nA\nB\n")
    yield _case(root, "dp-count-header-only", "condition\n")
    yield _case(root, "dp-count-singleton-neighbor", "condition\nA\n")
