"""Publish-path hardening tests for WebGPT review #4/#5/#6/#15.

Proves the readiness report binds its evidence chain and validates against the
committed schema, and that staging is private and never left in the output tree.
"""
from __future__ import annotations

import json
import re
import stat
from pathlib import Path

from anonymization_trial.fixture import generate_fixture
from anonymization_trial.pipeline import run_pipeline

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _run(tmp_path: Path) -> dict:
    inp, out = tmp_path / "in", tmp_path / "out"
    generate_fixture(inp, 3)
    run_pipeline(inp, out)
    return json.loads((out / "report.json").read_text(encoding="utf-8"))


def test_report_binds_evidence_chain(tmp_path: Path) -> None:  # review#15
    report = _run(tmp_path)
    assert report["report_schema"] == "anon.run_report.v1"
    for field in ("run_id", "source_manifest_sha256", "verification_sha256", "corpus_manifest_sha256"):
        assert _HEX64.match(report[field]), f"{field} not a sha256"
    assert report["verification_sha256"] == report["corpus_manifest_sha256"]


def test_report_matches_committed_schema(tmp_path: Path) -> None:  # review#15
    report = _run(tmp_path)
    schema = json.loads(Path("schemas/report.schema.json").read_text(encoding="utf-8"))
    assert set(schema["required"]) <= set(report)
    assert set(report) <= set(schema["properties"])


def test_no_staging_left_in_output(tmp_path: Path) -> None:  # review#6
    inp, out = tmp_path / "in", tmp_path / "out"
    generate_fixture(inp, 3)
    run_pipeline(inp, out)
    leftovers = [p.name for p in out.iterdir() if p.name.startswith(".staging-")]
    assert leftovers == []
    assert {p.name for p in out.iterdir()} == {"corpus", "report.json"}


def test_report_is_regular_file_no_temp_left(tmp_path: Path) -> None:  # review#5
    inp, out = tmp_path / "in", tmp_path / "out"
    generate_fixture(inp, 3)
    run_pipeline(inp, out)
    rp = out / "report.json"
    assert rp.is_file() and stat.S_ISREG(rp.stat().st_mode)
    assert not (out / ".report.json.tmp").exists()
