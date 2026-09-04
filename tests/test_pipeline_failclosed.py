"""Fail-closed / transactional-publish tests for the pipeline (issue #4)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError, AnonErrorCode
from anonymization_trial.fixture import generate_fixture
from anonymization_trial.pipeline import run_pipeline


def _make_input(tmp: Path) -> Path:
    inp = tmp / "input"
    generate_fixture(inp, 20)
    return inp


def test_success_writes_report_last(tmp_path: Path):
    inp = _make_input(tmp_path)
    out = tmp_path / "output"
    report = run_pipeline(inp, out)
    assert report.status == "ready"
    assert (out / "report.json").is_file()
    assert (out / "corpus").is_dir()
    assert report.corpus_manifest_sha256 and report.policy_sha256
    assert not list(out.glob(".staging-*"))


def test_unsupported_input_fails_closed(tmp_path: Path):
    inp = _make_input(tmp_path)
    (inp / "corpus" / "bad.parquet").write_text("x", encoding="utf-8")
    out = tmp_path / "output"
    with pytest.raises(AnonError) as exc:
        run_pipeline(inp, out)
    assert exc.value.code == AnonErrorCode.UNSUPPORTED_FORMAT
    assert not (out / "report.json").exists()
    assert not (out / "corpus").exists()


def test_symlink_in_corpus_rejected(tmp_path: Path):
    inp = _make_input(tmp_path)
    (inp / "corpus" / "evil.txt").symlink_to(inp / "policy.json")
    out = tmp_path / "output"
    with pytest.raises(AnonError) as exc:
        run_pipeline(inp, out)
    assert exc.value.code == AnonErrorCode.UNSAFE_INPUT
    assert not (out / "report.json").exists()


def test_prior_release_survives_failed_rerun(tmp_path: Path):
    inp = _make_input(tmp_path)
    out = tmp_path / "output"
    run_pipeline(inp, out)
    first = json.loads((out / "report.json").read_text())
    (inp / "corpus" / "bad.parquet").write_text("x", encoding="utf-8")
    with pytest.raises(AnonError):
        run_pipeline(inp, out)
    assert (out / "report.json").is_file()
    assert json.loads((out / "report.json").read_text()) == first


def test_nested_roots_rejected(tmp_path: Path):
    inp = _make_input(tmp_path)
    with pytest.raises(AnonError) as exc:
        run_pipeline(inp, inp / "corpus")
    assert exc.value.code == AnonErrorCode.UNSAFE_INPUT
