"""Tests for the operational CLI commands (polish: preflight/verify/inspect/explain)."""
from __future__ import annotations

import json
from pathlib import Path

from anonymization_trial.__main__ import main
from anonymization_trial.fixture import generate_fixture


def _capture(capsys, argv):
    code = main(argv)
    out = capsys.readouterr()
    return code, out.out, out.err


def test_tabular_advanced_transform_real_cli_path(tmp_path: Path, capsys):
    source = tmp_path / "source.csv"
    source.write_text("group,condition\na,A\na,B\nb,A\nb,B\n", encoding="utf-8")
    hierarchy = tmp_path / "hierarchy.json"
    hierarchy.write_text(json.dumps({"group": {"a": ["*"], "b": ["*"]}}))
    output = tmp_path / "release.csv"
    code, stdout, stderr = _capture(
        capsys,
        [
            "tabular-advanced-transform",
            "--input", str(source),
            "--output", str(output),
            "--quasi-identifiers", "group",
            "--sensitive", "condition",
            "--hierarchy", str(hierarchy),
            "--minimum-k", "2",
            "--maximum-alpha", "0.5",
            "--recursive-l", "2",
            "--maximum-recursive-c", "1",
            "--maximum-beta", "0",
            "--maximum-t", "0",
        ],
    )
    receipt = json.loads(stdout)
    assert code == 0 and not stderr
    assert receipt["transformation"]["privacy_recomputed"]["k_anonymity"] == 2
    assert receipt["raw_values_persisted_in_receipt"] is False
    assert receipt["transformation"]["selected_levels"] == {"group": 0}
    assert len(output.read_text(encoding="utf-8").splitlines()) == 5


def test_explain(capsys):
    code, out, _ = _capture(capsys, ["explain"])
    data = json.loads(out)
    assert code == 0
    assert "leftmost -> longest -> stable rule_id tie-break" in data["matching"]
    assert data["does_not_establish"]


def test_dp_count_cli_omits_predicate_and_accepts_empty_neighbor(tmp_path: Path, capsys):
    source = tmp_path / "people.csv"
    source.write_text("condition\nA\nA\nB\n", encoding="utf-8")
    code, out, err = _capture(
        capsys,
        [
            "dp-count",
            "--input", str(source),
            "--column", "condition",
            "--equals", "A",
            "--epsilon", "0.7",
        ],
    )
    receipt = json.loads(out)
    assert code == 0 and not err
    assert receipt["schema"] == "differentially_private_count.v1"
    assert receipt["adjacency"] == "add_remove_one_record"
    assert receipt["raw_values_persisted"] is False
    assert "condition" not in out and '"A"' not in out

    empty = tmp_path / "empty.csv"
    empty.write_text("condition\n", encoding="utf-8")
    code, out, err = _capture(
        capsys,
        [
            "dp-count",
            "--input", str(empty),
            "--column", "condition",
            "--equals", "A",
            "--epsilon", "0.7",
        ],
    )
    receipt = json.loads(out)
    assert code == 0 and not err
    assert receipt["adjacency"] == "add_remove_one_record"
    assert receipt["noisy_count"] >= 0
    assert "condition" not in out and '"A"' not in out


def test_dp_synthesize_rejects_output_receipt_alias_before_publication(tmp_path: Path, capsys):
    source = tmp_path / "people.csv"
    domain = tmp_path / "domain.json"
    alias = tmp_path / "release.csv"
    source.write_text("region,condition\nurban,A\n", encoding="utf-8")
    domain.write_text(json.dumps({"region": ["urban"], "condition": ["A"]}), encoding="utf-8")

    code, _, err = _capture(
        capsys,
        [
            "dp-synthesize",
            "--input", str(source),
            "--output", str(alias),
            "--domain", str(domain),
            "--dimensions", "region,condition",
            "--epsilon", "0.7",
            "--receipt", str(alias),
        ],
    )

    assert code == 1
    assert "ValueError" in err
    assert not alias.exists()

    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link_dir = tmp_path / "link"
    link_dir.symlink_to(real_dir, target_is_directory=True)
    equivalent = real_dir / "same.csv"
    code, _, err = _capture(
        capsys,
        [
            "dp-synthesize",
            "--input", str(source),
            "--output", str(link_dir / "same.csv"),
            "--domain", str(domain),
            "--dimensions", "region,condition",
            "--epsilon", "0.7",
            "--receipt", str(equivalent),
        ],
    )
    assert code == 1
    assert "ValueError" in err
    assert not equivalent.exists()

    output = tmp_path / "synthetic.csv"
    receipt = tmp_path / "receipt.json"
    ledger_aliases = [(output, "output"), (receipt, "receipt")]
    for ledger, _name in ledger_aliases:
        code, _, err = _capture(
            capsys,
            [
                "dp-synthesize",
                "--input", str(source),
                "--output", str(output),
                "--domain", str(domain),
                "--dimensions", "region,condition",
                "--epsilon", "0.7",
                "--receipt", str(receipt),
                "--budget-ledger", str(ledger),
                "--budget-id", "release-authorization",
                "--maximum-epsilon", "1.4",
            ],
        )
        assert code == 1
        assert "ValueError" in err
        assert not output.exists()
        assert not receipt.exists()


def test_preflight_pass(tmp_path: Path, capsys):
    generate_fixture(tmp_path / "input", 20)
    code, out, _ = _capture(capsys, ["preflight", "--input", str(tmp_path / "input")])
    data = json.loads(out)
    assert code == 0 and data["preflight"] == "PASS"
    assert data["corpus"]["files"] == 4 and data["ready_to_transform"] is True


def test_preflight_fails_closed_on_unsupported(tmp_path: Path, capsys):
    generate_fixture(tmp_path / "input", 20)
    (tmp_path / "input" / "corpus" / "bad.parquet").write_text("x", encoding="utf-8")
    code, _, err = _capture(capsys, ["preflight", "--input", str(tmp_path / "input")])
    assert code == 1 and "unsupported_format" in err


def test_run_then_verify_and_inspect(tmp_path: Path, capsys):
    generate_fixture(tmp_path / "input", 20)
    assert main(["run", "--input", str(tmp_path / "input"), "--output", str(tmp_path / "out")]) == 0
    capsys.readouterr()

    vcode, vout, _ = _capture(
        capsys, ["verify", "--input", str(tmp_path / "input"), "--output", str(tmp_path / "out")]
    )
    assert vcode == 0 and json.loads(vout)["verify"] == "PASS"

    icode, iout, _ = _capture(capsys, ["inspect", str(tmp_path / "out")])
    idata = json.loads(iout)
    assert icode == 0 and idata["status"] == "ready"
    assert idata["key_mode"] == "public-deterministic-trial-namespace"


def test_tabular_risk_cli_runs_multiple_sensitive_real_path(tmp_path: Path, capsys):
    source = tmp_path / "people.csv"
    source.write_text(
        "group,condition,income\na,A,10\na,B,20\nb,A,10\nb,A,30\n",
        encoding="utf-8",
    )
    code, out, _ = _capture(
        capsys,
        [
            "tabular-risk", "--input", str(source),
            "--quasi-identifiers", "group", "--sensitive", "condition,income",
        ],
    )
    receipt = json.loads(out)
    assert code == 0
    assert receipt["schema"] == "multiple_sensitive_privacy_metrics.v1"
    assert receipt["sensitive_attribute_count"] == 2
    assert receipt["raw_values_persisted"] is False


def test_population_k_map_cli_fails_closed_without_raw_values(tmp_path: Path, capsys):
    release = tmp_path / "release.csv"
    population = tmp_path / "population.csv"
    release.write_text("zip,age\na,20\nb,30\n", encoding="utf-8")
    population.write_text("zip,age\na,20\na,20\nb,30\nb,30\n", encoding="utf-8")

    code, out, _ = _capture(
        capsys,
        [
            "population-k-map", "--release", str(release), "--population", str(population),
            "--quasi-identifiers", "zip,age", "--minimum-k", "2",
        ],
    )
    receipt = json.loads(out)
    assert code == 0
    assert receipt["schema"] == "population_k_map.v1"
    assert receipt["k_map_satisfied"] is True
    assert "20" not in out and "30" not in out

    population.write_text("zip,age\na,20\n", encoding="utf-8")
    code, out, _ = _capture(
        capsys,
        [
            "population-k-map", "--release", str(release), "--population", str(population),
            "--quasi-identifiers", "zip,age", "--minimum-k", "2",
        ],
    )
    receipt = json.loads(out)
    assert code == 2
    assert receipt["verdict"] == "k_map_violation"
    assert receipt["receipt_contains_qi_values"] is False
    assert "20" not in out and "30" not in out

    release.write_text("zip,zip\na,20\n", encoding="utf-8")
    code, out, err = _capture(
        capsys,
        [
            "population-k-map", "--release", str(release), "--population", str(population),
            "--quasi-identifiers", "zip,age", "--minimum-k", "2",
        ],
    )
    assert code == 1
    assert out == ""
    assert err.strip() == "run failed: ValueError"
    assert "20" not in err and "30" not in err


def test_tabular_generalize_cli_runs_real_path(tmp_path: Path, capsys):
    source = tmp_path / "people.csv"
    source.write_text("zip,condition\n10001,A\n10002,B\n", encoding="utf-8")
    hierarchy = tmp_path / "hierarchy.json"
    hierarchy.write_text(
        json.dumps({"zip": {"10001": ["1000*"], "10002": ["1000*"]}}),
        encoding="utf-8",
    )
    output = tmp_path / "generalized.csv"
    code, out, _ = _capture(
        capsys,
        [
            "tabular-generalize", "--input", str(source), "--output", str(output),
            "--quasi-identifiers", "zip", "--sensitive", "condition",
            "--hierarchy", str(hierarchy), "--minimum-k", "2",
        ],
    )
    receipt = json.loads(out)
    assert code == 0
    assert receipt["privacy_recomputed"]["k_anonymity"] == 2
    assert output.read_text(encoding="utf-8") == "zip,condition\n1000*,A\n1000*,B\n"


def test_verify_detects_tampered_output(tmp_path: Path, capsys):
    generate_fixture(tmp_path / "input", 20)
    main(["run", "--input", str(tmp_path / "input"), "--output", str(tmp_path / "out")])
    capsys.readouterr()
    note = tmp_path / "out" / "corpus" / "support-notes.txt"
    note.write_text("Mara Ellison\n", encoding="utf-8")  # restore a sensitive literal
    code, _, err = _capture(
        capsys, ["verify", "--input", str(tmp_path / "input"), "--output", str(tmp_path / "out")]
    )
    assert code == 1 and "verification_failed" in err
