"""Real CLI checks for file/folder execution and explicitly approved fuzzy aliases.

No mocked matcher, file adapter or provider. Fixtures are synthetic; the CLI
subprocess uses the canonical installed package with its pinned discovery extra.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UV = shutil.which("uv")


def cli(*args, cwd=None):
    command = [
        UV,
        "run",
        "--project",
        str(ROOT),
        "--extra",
        "dev",
        "--extra",
        "discovery",
        "anonymization-trial",
        *map(str, args),
    ]
    if os.environ.get("ANONYMIZE_DATA_TEST_RUNNER"):
        command = [os.environ["ANONYMIZE_DATA_TEST_RUNNER"], *map(str, args)]
    return subprocess.run(  # noqa: S603 (explicit test runner and synthetic paths)
        command,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "PYTHONPATH": ""},
        check=False,
    )


def make_input(root, values=None, rules=None):
    source = root / "exports"
    source.mkdir()
    payload = {
        "version": 1,
        "sensitive_values": rules
        or [
            {"rule_id": "a", "subject_id": "person-a", "type": "name", "value": "Alice"},
        ],
        "protected_values": [{"value": "KEEP", "reason": "protected control"}],
    }
    policy = root / "policy.json"
    policy.write_text(json.dumps(payload))
    (source / "sample.json").write_text(json.dumps(values or {"name": "Alicee", "flag": True}))
    return source, policy


def test_discover_approve_and_anonymize_all_four_formats(tmp_path):
    source, policy = make_input(tmp_path)
    (source / "sample.csv").write_text("name,note\nAlicee,KEEP\n")
    (source / "sample.txt").write_text("Alicee\n")
    with sqlite3.connect(source / "sample.sqlite") as db:
        db.execute("CREATE TABLE people(name TEXT)")
        db.execute("INSERT INTO people VALUES (?)", ("Alicee",))
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    policy_before = policy.read_bytes()
    common = ["--input", source, "--policy", policy]
    plain = tmp_path / "plain"
    assert cli("anonymize", *common, "--output", plain).returncode == 0
    expected = (
        "Person-" + hashlib.sha256(b"pseudonym-v1:trial-v1:1:name:person-a:0").hexdigest()[:10]
    )
    assert json.loads((plain / "corpus/sample.json").read_text())["name"] == expected + "e"
    review = tmp_path / "review.json"
    result = cli("discover", *common, "--output", review)
    assert result.returncode == 0, result.stderr
    assert "Alicee" not in result.stdout and "Alice" not in result.stdout
    data = json.loads(review.read_text())
    assert data["release_ready"] is False
    assert data["seam_validation"]["status"] == "PASS"
    assert len(data["candidates"]) == 1
    candidate = data["candidates"][0]
    assert candidate["value"] == "Alicee" and candidate["occurrences"] == 4
    assert candidate["subject_id"] == "person-a" and candidate["similarity"] >= 90
    assert stat.S_IMODE(review.stat().st_mode) == 0o600
    approved = tmp_path / "approved.json"
    result = cli(
        "approve-discovery",
        *common,
        "--review",
        review,
        "--approve",
        candidate["id"],
        "--output",
        approved,
    )
    assert result.returncode == 0, result.stderr
    assert stat.S_IMODE(approved.stat().st_mode) == 0o600
    receipt = json.loads(approved.with_name("approved.json.approval.json").read_text())
    assert receipt["policy_sha256"] == hashlib.sha256(approved.read_bytes()).hexdigest()
    out = tmp_path / "out"
    result = cli("anonymize", "--input", source, "--policy", approved, "--output", out)
    assert result.returncode == 0, result.stderr
    report = json.loads((out / "report.json").read_text())
    assert report["verification_passed"] and report["files_processed"] == 4
    assert report["policy_sha256"] == receipt["policy_sha256"]
    assert json.loads((out / "corpus/sample.json").read_text()) == {"name": expected, "flag": True}
    assert (out / "corpus/sample.txt").read_text() == expected + "\n"
    with (out / "corpus/sample.csv").open(newline="") as handle:
        assert list(csv.reader(handle)) == [["name", "note"], [expected, "KEEP"]]
    with sqlite3.connect(out / "corpus/sample.sqlite") as db:
        assert db.execute("SELECT name FROM people").fetchall() == [(expected,)]
    assert {p.name: p.read_bytes() for p in source.iterdir()} == before
    assert policy.read_bytes() == policy_before


def test_noise_protected_identifiers_and_ties_never_become_aliases(tmp_path):
    source, policy = make_input(
        tmp_path,
        ["Alita", "Alina", "CODE-12", "KEEP", "   ", "Alina KEEP"],
        [
            {"rule_id": "a", "subject_id": "a", "type": "name", "value": "Alina"},
            {"rule_id": "b", "subject_id": "b", "type": "name", "value": "Alisa"},
        ],
    )
    review = tmp_path / "review.json"
    result = cli(
        "discover", "--input", source, "--policy", policy, "--output", review, "--threshold", 80
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(review.read_text())
    assert data["candidates"] == []
    assert data["counts"]["ambiguous"] == 1
    assert data["counts"]["protected"] == 2
    assert data["counts"]["noise"] == 2
    out = tmp_path / "approved.json"
    assert (
        cli(
            "approve-discovery",
            "--input",
            source,
            "--policy",
            policy,
            "--review",
            review,
            "--approve",
            "unknown",
            "--output",
            out,
        ).returncode
        != 0
    )
    assert not out.exists()


@pytest.mark.parametrize("fault", ["candidate", "corpus", "policy"])
def test_stale_or_edited_review_cannot_write_a_policy(tmp_path, fault):
    source, policy = make_input(tmp_path)
    review = tmp_path / "review.json"
    common = ["--input", source, "--policy", policy]
    assert cli("discover", *common, "--output", review).returncode == 0
    data = json.loads(review.read_text())
    identity = data["candidates"][0]["id"]
    if fault == "candidate":
        data["candidates"][0]["value"] = "Mallory"
        review.write_text(json.dumps(data))
    elif fault == "corpus":
        (source / "sample.json").write_text('{"name":"changed"}')
    else:
        policy.write_bytes(policy.read_bytes() + b"\n")
    out = tmp_path / "approved.json"
    result = cli(
        "approve-discovery", *common, "--review", review, "--approve", identity, "--output", out
    )
    assert result.returncode != 0 and "stale_discovery_review" in result.stderr
    assert not out.exists()


@pytest.mark.parametrize("value", ["nan", "79", "101"])
def test_invalid_discovery_threshold_fails_before_artifact(tmp_path, value):
    source, policy = make_input(tmp_path)
    output = tmp_path / "review.json"
    result = cli(
        "discover", "--input", source, "--policy", policy, "--output", output, "--threshold", value
    )
    assert result.returncode != 0 and not output.exists()


def test_single_file_relative_paths_and_output_safety(tmp_path):
    source, policy = make_input(tmp_path)
    result = cli(
        "anonymize",
        "--input",
        "exports/sample.json",
        "--policy",
        "policy.json",
        "--output",
        "out",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert {p.name for p in (tmp_path / "out/corpus").iterdir()} == {"sample.json"}
    assert (
        cli("anonymize", "--input", source, "--policy", policy, "--output", source).returncode != 0
    )
    link = tmp_path / "linked.json"
    link.symlink_to(source / "sample.json")
    assert (
        cli(
            "anonymize", "--input", link, "--policy", policy, "--output", tmp_path / "bad"
        ).returncode
        != 0
    )
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("do not delete")
    assert (
        cli("anonymize", "--input", source, "--policy", policy, "--output", occupied).returncode
        != 0
    )
    assert (occupied / "keep.txt").read_text() == "do not delete"
