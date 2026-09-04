#!/usr/bin/env python3
"""Three small synthetic demonstrations through real runtime code; no mocks.

Run with PYTHONPATH=src python scripts/pitch_debug_demo.py identity|typed|publication.
Use only synthetic inputs: captured debugger locals are intentionally shareable.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from anonymization_trial.errors import AnonError
from anonymization_trial.pipeline import run_pipeline
from anonymization_trial.policy import compile_policy, replace_text
from anonymization_trial.verification import verify_corpus

POLICY = {
    "version": 1,
    "protected_values": [],
    "sensitive_values": [
        {"rule_id": "r1", "subject_id": "p1", "type": "name", "value": "Bob"},
        {"rule_id": "r2", "subject_id": "p1", "type": "name", "value": "Bobby"},
    ],
}


def main(mode: str) -> None:
    policy = compile_policy(POLICY)
    if mode == "identity":
        first = replace_text("Bob", policy)[0]
        second = replace_text("Bobby", policy)[0]
        if first != second:
            raise RuntimeError("alias identity diverged")
        print(json.dumps({"Bob": first, "Bobby": second}))
        return
    if mode not in {"typed", "publication"}:
        raise ValueError("choose identity, typed or publication")
    with tempfile.TemporaryDirectory(prefix="pitch-demo-") as directory:
        root = Path(directory)
        source, output = root / "input", root / "output"
        (source / "corpus").mkdir(parents=True)
        (source / "policy.json").write_text(json.dumps(POLICY), encoding="utf-8")
        (source / "corpus/data.json").write_text('{"name":"Bob","flag":true}', encoding="utf-8")
        run_pipeline(source, output)
        report = json.loads((output / "report.json").read_text())
        if report["status"] != "ready" or not report["verification_passed"]:
            raise RuntimeError("published report did not authorize READY")
        if mode == "publication":
            print(json.dumps({"readback": report["status"], "files": report["files_processed"]}))
            return
        path = output / "corpus/data.json"
        data = json.loads(path.read_text())
        data["flag"] = 1
        path.write_text(json.dumps(data))
        try:
            verify_corpus(source / "corpus", output / "corpus", policy)
        except AnonError:
            print("REJECTED: JSON true mutated to integer 1")
            return
        raise RuntimeError("typed scalar mutation escaped verification")


if __name__ == "__main__":
    main(sys.argv[1])
