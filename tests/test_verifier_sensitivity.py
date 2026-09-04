"""Verifier-sensitivity + subject-level tests (research adopt-now items).

Mutation testing after a real pipeline run proves the independent verifier
catches injected faults (DICOM validation methodology arXiv:2508.01889); the
subject-level checks follow SPIA (arXiv:2604.21211).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError, AnonErrorCode
from anonymization_trial.policy import compile_policy
from anonymization_trial.verification import verify_corpus


def _pol():
    return compile_policy(
        {
            "version": 1,
            "sensitive_values": [
                {"rule_id": "n1", "subject_id": "p1", "type": "name", "value": "Ada"},
                {"rule_id": "n1b", "subject_id": "p1", "type": "name", "value": "Ada Lovelace"},
                {"rule_id": "n2", "subject_id": "p2", "type": "name", "value": "Bob"},
            ],
            "protected_values": [{"value": "Northwind"}],
        }
    )


def _dir(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (root / name).write_text(content, encoding="utf-8")
    return root


def _run(tmp: Path, pol):
    from anonymization_trial.policy import replace_text

    src = _dir(tmp / "src", {"a.txt": "Ada Lovelace and Ada met Bob at Northwind\n"})
    out = tmp / "out"
    out.mkdir()
    text = (src / "a.txt").read_text(encoding="utf-8")
    (out / "a.txt").write_text(replace_text(text, pol)[0], encoding="utf-8")
    verify_corpus(src, out, pol)  # baseline: passes
    return src, out


def test_baseline_passes(tmp_path: Path):
    _run(tmp_path, _pol())


def test_restored_literal_is_caught(tmp_path: Path):
    pol = _pol()
    src, out = _run(tmp_path, pol)
    (out / "a.txt").write_text("Ada is back\n", encoding="utf-8")  # literal restored
    with pytest.raises(AnonError) as exc:
        verify_corpus(src, out, pol)
    assert exc.value.code == AnonErrorCode.VERIFICATION_FAILED


def test_incomplete_subject_coverage_is_caught(tmp_path: Path):
    pol = _pol()
    src, out = _run(tmp_path, pol)
    # Strip the subject's pseudonyms from output -> coverage < source occurrences.
    (out / "a.txt").write_text("nothing sensitive here Northwind\n", encoding="utf-8")
    with pytest.raises(AnonError) as exc:
        verify_corpus(src, out, pol)
    assert exc.value.code == AnonErrorCode.VERIFICATION_FAILED


def test_report_carries_non_claims(tmp_path: Path):
    from anonymization_trial.fixture import generate_fixture
    from anonymization_trial.pipeline import run_pipeline

    generate_fixture(tmp_path / "input", 20)
    report = run_pipeline(tmp_path / "input", tmp_path / "output")
    data = json.loads((tmp_path / "output" / "report.json").read_text())
    assert data["key_mode"] == "public-deterministic-trial-namespace"
    assert data["algorithm_version"] == "pseudonym-v1"
    assert "formal_anonymity_or_differential_privacy" in data["does_not_establish"]
    assert report.scope_id == "trial-v1"
