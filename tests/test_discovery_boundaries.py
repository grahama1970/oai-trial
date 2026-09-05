"""Adversarial discovery/approval boundaries through the real CLI or skill wrapper."""

from __future__ import annotations

import json
import os

import pytest

from test_discovery import cli, make_input


@pytest.mark.parametrize("fault", ["release_ready", "counts", "subject", "score", "extra_field"])
def test_forged_review_fields_never_authorize_a_policy(tmp_path, fault):
    source, policy = make_input(tmp_path)
    review, approved = tmp_path / "review.json", tmp_path / "approved.json"
    common = ["--input", source, "--policy", policy]
    assert cli("discover", *common, "--output", review).returncode == 0
    raw = json.loads(review.read_text())
    identity = raw["candidates"][0]["id"]
    if fault == "release_ready":
        raw["release_ready"] = True
    elif fault == "counts":
        raw["counts"]["proposed"] = True
    elif fault == "subject":
        raw["candidates"][0]["subject_id"] = "wrong-person"
    elif fault == "score":
        raw["candidates"][0]["similarity"] = True
    else:
        raw["approve_everything"] = True
    review.write_text(json.dumps(raw))
    result = cli(
        "approve-discovery",
        *common,
        "--review",
        review,
        "--approve",
        identity,
        "--output",
        approved,
    )
    assert result.returncode != 0
    assert not approved.exists() and not approved.with_name("approved.json.approval.json").exists()
    assert "wrong-person" not in result.stdout + result.stderr


@pytest.mark.parametrize("selection", ["unknown", "duplicate"])
def test_approval_requires_specific_unique_proposals(tmp_path, selection):
    source, policy = make_input(tmp_path)
    review = tmp_path / "review.json"
    common = ["--input", source, "--policy", policy]
    assert cli("discover", *common, "--output", review).returncode == 0
    identity = json.loads(review.read_text())["candidates"][0]["id"]
    args = (
        ["--approve", "not-proposed"]
        if selection == "unknown"
        else [
            "--approve",
            identity,
            "--approve",
            identity,
        ]
    )
    approved = tmp_path / "approved.json"
    result = cli("approve-discovery", *common, "--review", review, *args, "--output", approved)
    assert result.returncode != 0 and "discovery_approval_rejected" in result.stderr
    assert not approved.exists()


@pytest.mark.parametrize(
    "filename,content",
    [
        ("bad.csv", b'name,note\nAlicee,"unfinished'),
        ("bad.json", b'{"name":"Alicee","name":"other"}'),
        ("bad.sqlite", b"not a database"),
        ("bad.txt", b"\xff"),
    ],
)
def test_malformed_files_fail_without_review_or_release(tmp_path, filename, content):
    source, policy = make_input(tmp_path)
    path = source / filename
    path.write_bytes(content)
    review = tmp_path / "review.json"
    result = cli("discover", "--input", path, "--policy", policy, "--output", review)
    assert result.returncode != 0 and not review.exists()
    assert "Alicee" not in result.stdout + result.stderr
    assert path.read_bytes() == content


@pytest.mark.parametrize("margin", ["nan", "inf", "-1", "21"])
def test_invalid_margin_is_refused(tmp_path, margin):
    source, policy = make_input(tmp_path)
    out = tmp_path / "review.json"
    result = cli(
        "discover", "--input", source, "--policy", policy, "--margin", margin, "--output", out
    )
    assert result.returncode != 0 and "invalid_discovery_review" in result.stderr
    assert not out.exists()


def test_discovery_is_deterministic_and_does_not_scan_schema_or_other_types(tmp_path):
    source, policy = make_input(
        tmp_path,
        {"Alicee": "plain data", "other": "CWE-79"},
        [
            {"rule_id": "a", "type": "name", "value": "Alice"},
            {"rule_id": "s", "type": "secret", "value": "Mallory"},
        ],
    )
    (source / "sample.json").write_text(json.dumps({"Alicee": "Malloryy"}))
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    common = ["--input", source, "--policy", policy]
    assert cli("discover", *common, "--output", a).returncode == 0
    assert cli("discover", *common, "--output", b).returncode == 0
    assert a.read_bytes() == b.read_bytes()
    assert json.loads(a.read_text())["candidates"] == []


def test_policy_without_subject_id_keeps_the_original_identity(tmp_path):
    source, policy = make_input(
        tmp_path, rules=[{"rule_id": "a", "type": "name", "value": "Alice"}]
    )
    review, approved = tmp_path / "review.json", tmp_path / "approved.json"
    common = ["--input", source, "--policy", policy]
    assert cli("discover", *common, "--output", review).returncode == 0
    candidate = json.loads(review.read_text())["candidates"][0]
    assert candidate["subject_id"] == "a"
    assert (
        cli(
            "approve-discovery",
            *common,
            "--review",
            review,
            "--approve",
            candidate["id"],
            "--output",
            approved,
        ).returncode
        == 0
    )
    added = json.loads(approved.read_text())["sensitive_values"][-1]
    assert added["subject_id"] == "a" and added["case_sensitive"] is True


def test_work_artifacts_cannot_overwrite_inputs_existing_files_or_releases(tmp_path):
    source, policy = make_input(tmp_path)
    common = ["--input", source, "--policy", policy]
    occupied = tmp_path / "occupied.json"
    occupied.write_text("KEEP EXISTING")
    assert cli("discover", *common, "--output", occupied).returncode != 0
    assert occupied.read_text() == "KEEP EXISTING"
    assert cli("discover", *common, "--output", source / "review.json").returncode != 0
    assert cli("discover", *common, "--output", policy).returncode != 0
    release = tmp_path / "release"
    release.mkdir()
    (release / "corpus").mkdir()
    (release / "report.json").write_text('{"status":"ready"}')
    assert cli("discover", *common, "--output", release / "review.json").returncode != 0
    assert {p.name for p in release.iterdir()} == {"report.json", "corpus"}
    assert cli("discover", *common, "--output", tmp_path / "report.json").returncode != 0


def test_customer_file_named_report_json_is_not_a_release_marker(tmp_path):
    source, policy = make_input(tmp_path)
    customer_report = tmp_path / "report.json"
    customer_report.write_bytes((source / "sample.json").read_bytes())
    out = tmp_path / "out"
    result = cli("anonymize", "--input", customer_report, "--policy", policy, "--output", out)
    assert result.returncode == 0, result.stderr
    assert (out / "corpus/report.json").is_file()


def test_text_value_budget_fails_closed_without_partial_proposals(tmp_path):
    source, policy = make_input(tmp_path, values=["Alicee"] * 10001)
    review = tmp_path / "review.json"
    result = cli("discover", "--input", source, "--policy", policy, "--output", review)
    assert result.returncode != 0 and "structure_too_complex" in result.stderr
    assert not review.exists()


def test_near_ties_across_identities_are_refused(tmp_path):
    source, policy = make_input(
        tmp_path,
        rules=[
            {"rule_id": "a", "subject_id": "a", "type": "name", "value": "Alice"},
            {"rule_id": "b", "subject_id": "b", "type": "name", "value": "Aliceee"},
        ],
    )
    review = tmp_path / "review.json"
    assert (
        cli("discover", "--input", source, "--policy", policy, "--output", review).returncode == 0
    )
    data = json.loads(review.read_text())
    assert data["candidates"] == [] and data["counts"]["ambiguous"] == 1


def test_aliases_of_one_identity_do_not_create_false_ties(tmp_path):
    source, policy = make_input(
        tmp_path,
        rules=[
            {"rule_id": "a", "subject_id": "same", "type": "name", "value": "Alice"},
            {"rule_id": "b", "subject_id": "same", "type": "name", "value": "Aliceee"},
        ],
    )
    review = tmp_path / "review.json"
    assert (
        cli("discover", "--input", source, "--policy", policy, "--output", review).returncode == 0
    )
    data = json.loads(review.read_text())
    assert len(data["candidates"]) == 1 and data["candidates"][0]["subject_id"] == "same"


def test_approval_rechecks_partial_protected_overlap(tmp_path):
    source, policy = make_input(tmp_path, values={"name": "Alicex"})
    payload = json.loads(policy.read_text())
    payload["protected_values"] = [{"value": "xy"}]
    policy.write_text(json.dumps(payload))
    review, approved = tmp_path / "review.json", tmp_path / "approved.json"
    common = ["--input", source, "--policy", policy]
    assert cli("discover", *common, "--output", review).returncode == 0
    identity = json.loads(review.read_text())["candidates"][0]["id"]
    result = cli(
        "approve-discovery",
        *common,
        "--review",
        review,
        "--approve",
        identity,
        "--output",
        approved,
    )
    assert result.returncode != 0 and "protected_sensitive_overlap" in result.stderr
    assert not approved.exists()


def test_name_rule_budget_is_explicit(tmp_path):
    rules = [
        {
            "rule_id": f"r{i}",
            "type": "name",
            "value": "Zed" + "".join(chr(65 + (i // 26**j) % 26) for j in range(3)),
        }
        for i in range(1001)
    ]
    source, policy = make_input(tmp_path, rules=rules)
    payload = json.loads(policy.read_text())
    payload["protected_values"] = []
    policy.write_text(json.dumps(payload))
    review = tmp_path / "review.json"
    result = cli("discover", "--input", source, "--policy", policy, "--output", review)
    assert result.returncode != 0 and "structure_too_complex" in result.stderr
    assert not review.exists()


def test_symlink_policy_and_special_file_are_refused(tmp_path):
    source, policy = make_input(tmp_path)
    linked = tmp_path / "linked-policy.json"
    linked.symlink_to(policy)
    assert (
        cli(
            "anonymize", "--input", source, "--policy", linked, "--output", tmp_path / "out"
        ).returncode
        != 0
    )
    os.mkfifo(source / "pipe.txt")
    result = cli(
        "discover", "--input", source, "--policy", policy, "--output", tmp_path / "review.json"
    )
    assert result.returncode != 0 and "unsafe_input" in result.stderr
