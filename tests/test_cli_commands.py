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


def test_explain(capsys):
    code, out, _ = _capture(capsys, ["explain"])
    data = json.loads(out)
    assert code == 0
    assert "leftmost -> longest -> stable rule_id tie-break" in data["matching"]
    assert data["does_not_establish"]


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
