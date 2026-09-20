# ruff: noqa: S603 -- tests execute fixed local verifier argv only
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def test_parity_matrix_executor_checks_declared_pass_and_gap(tmp_path: Path) -> None:
    matrix = {
        "schema": "anonymization.competitor_parity.v1",
        "applicability_dispositions": [
            {
                "ecosystem": "passing-tool",
                "capabilities": ["out-of-scope feature"],
                "disposition": "not_implemented",
                "reason": "Outside this bounded fixture.",
            }
        ],
        "rows": [
            {
                "capability_id": "passing-tool-01",
                "competitor": "passing-tool",
                "source": "https://example.invalid/passing-tool",
                "source_revision": "abc123",
                "capability": "pass capability",
                "our_equivalent_executable_check": "pass check",
                "proof_command": [sys.executable, "-c", "raise SystemExit(0)"],
                "expected_exit": 0,
                "result": "pass",
                "project_specific_advantage_or_remaining_gap": "Advantage: deterministic proof.",
                "runtime_consumers": ["scripts/verify_competitor_parity.py"],
            },
            {
                "capability_id": "gap-tool-01",
                "competitor": "gap-tool",
                "source": "https://example.invalid/gap-tool",
                "source_revision": "def456",
                "capability": "unsupported capability",
                "our_equivalent_executable_check": "absence check",
                "proof_command": [sys.executable, "-c", "raise SystemExit(1)"],
                "expected_exit": 1,
                "result": "gap",
                "project_specific_advantage_or_remaining_gap": "Gap: not implemented.",
                "runtime_consumers": ["scripts/verify_competitor_parity.py"],
            },
        ],
    }
    matrix_path = tmp_path / "matrix.json"
    receipt = tmp_path / "receipt.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    completed = subprocess.run(  # noqa: S603 - test controls the complete argv
        [
            sys.executable,
            "scripts/verify_competitor_parity.py",
            "--matrix",
            str(matrix_path),
            "--receipt",
            str(receipt),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    result = json.loads(receipt.read_text(encoding="utf-8"))
    assert result["schema"] == "anonymization.competitor_parity_receipt.v3"
    assert result["matrix_valid"] is True
    assert result["scoped_parity_proven"] is False
    assert result["complete_ecosystem_parity_proven"] is False
    assert result["pass_rows"] == 1
    assert result["gap_rows"] == 1
    assert len(result["matrix_sha256"]) == 64
    assert len(result["implementation_revision"]["working_tree_sha256"]) == 64
    assert receipt.stat().st_mode & 0o777 == 0o600
    digest_receipt = receipt.with_suffix(".json.sha256")
    assert digest_receipt.stat().st_mode & 0o777 == 0o600
    expected_digest, expected_name = digest_receipt.read_text().strip().split("  ")
    assert expected_name == receipt.name
    assert expected_digest == hashlib.sha256(receipt.read_bytes()).hexdigest()
    delivery = json.loads(completed.stdout)
    assert delivery == {
        "schema": "anonymization.competitor_parity_delivery.v1",
        "receipt": str(receipt),
        "receipt_bytes": len(receipt.read_bytes()),
        "receipt_sha256": expected_digest,
        "digest_receipt": str(digest_receipt),
    }
    assert all(row["matched"] for row in result["results"])
    assert all(len(row["stdout_sha256"]) == 64 for row in result["results"])
    assert all(row["proof_command"] for row in result["results"])
    assert all(len(row["row_sha256"]) == 64 for row in result["results"])
    assert all(row["proof_executable"] for row in result["results"])
    assert all(len(row["proof_executable_sha256"]) == 64 for row in result["results"])


def test_parity_executor_rejects_fail_open_shell_proofs(tmp_path: Path) -> None:
    matrix = {
        "applicability_dispositions": [
            {
                "ecosystem": "fixture",
                "capabilities": ["fixture"],
                "disposition": "applicable",
                "reason": "Exercise shell validation.",
            }
        ],
        "rows": [
            {
                "capability_id": "unsafe-shell-01",
                "competitor": "fixture",
                "source": "https://example.invalid",
                "source_revision": "revision",
                "capability": "unsafe shell sequence",
                "our_equivalent_executable_check": "must be rejected",
                "proof_command": ["bash", "-c", "false; true"],
                "expected_exit": 0,
                "result": "pass",
                "project_specific_advantage_or_remaining_gap": "fixture",
                "runtime_consumers": ["scripts/verify_competitor_parity.py"],
            }
        ],
    }
    matrix_path = tmp_path / "matrix.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_competitor_parity.py",
            "--matrix",
            str(matrix_path),
            "--receipt",
            str(tmp_path / "receipt.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "bash proof_command must begin with set -euo pipefail" in completed.stderr


def test_receipt_distinguishes_scoped_checks_from_complete_ecosystem_parity(tmp_path: Path) -> None:
    matrix = json.loads(Path("security/competitor_parity_matrix.json").read_text(encoding="utf-8"))
    # Keep this check cheap while exercising the real disposition semantics.
    matrix["rows"] = [
        {
            "capability_id": "bounded-tool-01",
            "competitor": "bounded-tool",
            "source": "https://example.invalid/bounded-tool",
            "source_revision": "revision-1",
            "capability": "bounded capability",
            "our_equivalent_executable_check": "bounded check",
            "proof_command": [sys.executable, "-c", "raise SystemExit(0)"],
            "expected_exit": 0,
            "result": "pass",
            "project_specific_advantage_or_remaining_gap": "Advantage: bounded check.",
            "runtime_consumers": ["scripts/verify_competitor_parity.py"],
        }
    ]
    matrix_path = tmp_path / "matrix.json"
    receipt_path = tmp_path / "receipt.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "scripts/verify_competitor_parity.py",
            "--matrix",
            str(matrix_path),
            "--receipt",
            str(receipt_path),
        ],
        check=True,
        capture_output=True,
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["scoped_parity_proven"] is True
    assert receipt["complete_ecosystem_parity_proven"] is False
    assert receipt["omitted_capability_dispositions"]
    binding = receipt["results"][0]["runtime_consumer_bindings"][0]
    assert binding["path"] == "scripts/verify_competitor_parity.py"
    assert len(binding["sha256"]) == 64
    assert receipt["capability_bindings"] == {
        "bounded-tool-01": receipt["results"][0]["row_sha256"]
    }


def test_release_qualification_fails_closed_on_inventory_omissions(tmp_path: Path) -> None:
    matrix = {
        "applicability_dispositions": [
            {
                "ecosystem": "fixture",
                "capabilities": ["unimplemented capability"],
                "disposition": "not_implemented",
                "reason": "Explicit release blocker.",
            }
        ],
        "rows": [
            {
                "capability_id": "fixture-01",
                "competitor": "fixture",
                "source": "https://example.invalid",
                "source_revision": "revision",
                "capability": "bounded capability",
                "our_equivalent_executable_check": "bounded check",
                "proof_command": [sys.executable, "-c", "raise SystemExit(0)"],
                "expected_exit": 0,
                "result": "pass",
                "project_specific_advantage_or_remaining_gap": "Bounded only.",
                "runtime_consumers": ["scripts/verify_competitor_parity.py"],
                "dependencies": [],
            }
        ],
    }
    matrix_path = tmp_path / "matrix.json"
    receipt_path = tmp_path / "receipt.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_competitor_parity.py",
            "--matrix",
            str(matrix_path),
            "--receipt",
            str(receipt_path),
            "--require-release-qualification",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["release_qualified"] is False
    assert receipt["qualification_steps"]["ecosystem_inventory"] == "failed"
    assert receipt["release_blockers"] == ["ecosystem_inventory"]
    assert receipt["results"][0]["step_statuses"] == {
        "proof_execution": "passed",
        "runtime_consumers": "passed",
        "source_revision": "passed",
        "package_bindings": "passed",
        "configuration_binding": "passed",
    }


def test_release_qualification_rejects_unresolved_package_binding(tmp_path: Path) -> None:
    matrix = {
        "applicability_dispositions": [
            {
                "ecosystem": "fixture",
                "capabilities": ["bounded capability"],
                "disposition": "applicable",
                "reason": "Exercise package binding.",
            }
        ],
        "rows": [
            {
                "capability_id": "fixture-01",
                "competitor": "fixture",
                "source": "https://example.invalid",
                "source_revision": "revision",
                "capability": "bounded capability",
                "our_equivalent_executable_check": "bounded check",
                "proof_command": [sys.executable, "-c", "raise SystemExit(0)"],
                "expected_exit": 0,
                "result": "pass",
                "project_specific_advantage_or_remaining_gap": "Bounded only.",
                "runtime_consumers": ["scripts/verify_competitor_parity.py"],
                "dependencies": ["definitely-not-an-installed-package==1.0"],
            }
        ],
    }
    matrix_path = tmp_path / "matrix.json"
    receipt_path = tmp_path / "receipt.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_competitor_parity.py",
            "--matrix",
            str(matrix_path),
            "--receipt",
            str(receipt_path),
            "--require-release-qualification",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert (
        receipt["qualification_steps"]["runtime_source_package_configuration_bindings"] == "failed"
    )
    assert receipt["results"][0]["dependency_bindings"][0]["resolved"] is False


def test_real_matrix_binds_only_hashed_production_consumers() -> None:
    matrix = json.loads(Path("security/competitor_parity_matrix.json").read_text(encoding="utf-8"))
    ids = [row["capability_id"] for row in matrix["rows"]]
    assert len(ids) == len(set(ids))
    for row in matrix["rows"]:
        assert row["runtime_consumers"]
        assert all(Path(path).is_file() for path in row["runtime_consumers"])
        assert all(
            not path.startswith("tests/") and "/tests/" not in path
            for path in row["runtime_consumers"]
        )


def test_real_matrix_records_bounded_gradient_attack_parity() -> None:
    matrix = json.loads(Path("security/competitor_parity_matrix.json").read_text(encoding="utf-8"))
    by_capability = {row["capability"]: row for row in matrix["rows"]}

    advanced = next(
        row for capability, row in by_capability.items() if capability.startswith("(alpha,k)")
    )
    model_attack = by_capability["learned-model and gradient membership-inference attacks"]
    comparator = by_capability[
        "paired structured-identifier comparator on identical controlled fixtures"
    ]

    assert advanced["result"] == "pass" and advanced["expected_exit"] == 0
    assert "fails closed" in advanced["project_specific_advantage_or_remaining_gap"]
    assert model_attack["result"] == "pass" and model_attack["expected_exit"] == 0
    assert "affine batch-size-one" in model_attack["project_specific_advantage_or_remaining_gap"]
    assert comparator["result"] == "pass"
    assert (
        "same structured and approved-PERSON policy"
        in comparator["our_equivalent_executable_check"]
    )
    assert "digest" in comparator["our_equivalent_executable_check"]
    assert "--receipt" not in comparator["proof_command"]
    assert comparator["source_revision"] == "presidio-analyzer==2.2.364"
    assert comparator["dependencies"] == ["presidio-analyzer==2.2.364"]
    assert "exact type/start/end finding equality" in comparator["semantic_assertions"]


def test_matrix_explicitly_disposes_omitted_capabilities() -> None:
    matrix = json.loads(Path("security/competitor_parity_matrix.json").read_text(encoding="utf-8"))
    dispositions = matrix["applicability_dispositions"]
    ecosystems = {item["ecosystem"] for item in dispositions}
    assert {
        "pyCANON/ANJANA",
        "ARX",
        "Anonymeter",
        "LeakPro",
        "Presidio image/document",
    } <= ecosystems
    assert all(
        item["disposition"] in {"applicable", "not_implemented", "not_applicable"}
        for item in dispositions
    )
    assert any("DICOM" in item["capabilities"] for item in dispositions)
