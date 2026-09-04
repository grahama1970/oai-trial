"""Bounded residual-risk probe tests (issue #12, control-plane demonstration)."""
from __future__ import annotations

from pathlib import Path

from residual_risk_probe import probe_corpus  # importable via pytest pythonpath=["scripts"]


def _corpus(root: Path, csv_text: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "a.csv").write_text(csv_text, encoding="utf-8")
    return root


def test_flags_unique_quasi_identifier_combo(tmp_path: Path):
    # (age,zip) has one singleton row -> residual re-identification risk.
    corpus = _corpus(tmp_path, "age,zip\n30,10001\n30,10001\n41,90210\n")
    report = probe_corpus(corpus, ["age", "zip"])
    assert report["result"] == "review"
    assert report["total_singletons"] == 1
    assert report["does_not_prove"] == "universal_non_reidentifiability"


def test_pass_when_all_combos_repeat(tmp_path: Path):
    corpus = _corpus(tmp_path, "age,zip\n30,10001\n30,10001\n41,90210\n41,90210\n")
    report = probe_corpus(corpus, ["age", "zip"])
    assert report["result"] == "pass_under_declared_attack_model"
    assert report["total_singletons"] == 0


def test_schema_and_non_claims_present(tmp_path: Path):
    corpus = _corpus(tmp_path, "age,zip\n1,2\n")
    report = probe_corpus(corpus, ["age", "zip"])
    assert report["schema"] == "anonymization_trial.residual_risk.v1"
    assert report["does_not_prove"]
