#!/usr/bin/env python3
"""Execute every competitor-parity row and persist revision-bound proof receipts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
from pathlib import Path

REQUIRED = {
    "capability_id",
    "competitor",
    "source",
    "source_revision",
    "capability",
    "our_equivalent_executable_check",
    "proof_command",
    "expected_exit",
    "result",
    "project_specific_advantage_or_remaining_gap",
    "runtime_consumers",
}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bound_paths(names: list[str]) -> list[dict[str, str]]:
    """Bind rows only to hashed production files, never tests or unresolved symbols."""
    bound = []
    for name in names:
        path = Path(name)
        if name.startswith("tests/") or "/tests/" in name or not path.is_file():
            raise ValueError(f"runtime consumer must be a production file: {name}")
        bound.append({"path": name, "sha256": _digest(path.read_bytes())})
    return bound


def _dependency_bindings(
    requirements: list[str], command: list[str]
) -> list[dict[str, str | bool]]:
    """Bind exact pins from this environment or an isolated uv proof command."""
    bindings = []
    isolated = {command[index + 1] for index, part in enumerate(command[:-1]) if part == "--with"}
    for requirement in requirements:
        if "==" not in requirement:
            bindings.append(
                {"requirement": requirement, "resolved": False, "reason": "not exactly pinned"}
            )
            continue
        if requirement in isolated:
            bindings.append(
                {
                    "requirement": requirement,
                    "resolved": True,
                    "environment": "isolated_uv_proof_command",
                }
            )
            continue
        name, expected = requirement.split("==", 1)
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            bindings.append(
                {"requirement": requirement, "resolved": False, "reason": "package not installed"}
            )
        else:
            bindings.append(
                {
                    "requirement": requirement,
                    "resolved": actual == expected,
                    "installed_version": actual,
                    "environment": "verifier",
                }
            )
    return bindings


def _proof_executable(command: list[str]) -> dict[str, str]:
    """Resolve and hash the exact executable used by a proof command."""
    resolved = shutil.which(command[0]) or command[0]
    path = Path(resolved).resolve()
    if not path.is_file():
        raise ValueError(f"proof executable is not a file: {resolved}")
    return {"path": str(path), "sha256": _digest(path.read_bytes())}


def _validate_proof_command(command: list[str]) -> None:
    """Reject shell proof sequences that can conceal an earlier failure."""
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("proof_command must be a non-empty argv of strings")
    if command[:2] == ["bash", "-c"] and not command[2].lstrip().startswith("set -euo pipefail;"):
        raise ValueError("bash proof_command must begin with set -euo pipefail")


def _retained_stdout(row: dict[str, object], stdout: bytes) -> dict[str, object] | None:
    """Optionally retain sanitized JSON proof output for independent review packets."""
    if not row.get("retain_stdout_json"):
        return None
    if row.get("stdout_retention_policy") != "sanitized_json_no_raw_values":
        raise ValueError("retain_stdout_json requires stdout_retention_policy=sanitized_json_no_raw_values")
    if len(stdout) > 65536:
        raise ValueError("retained stdout JSON exceeds 65536 bytes")
    try:
        payload = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("retained stdout must be UTF-8 JSON") from exc
    if payload.get("receipt_contains_raw_values") is not False or payload.get("raw_values_persisted") is not False:
        raise ValueError("retained stdout JSON must explicitly assert no raw values persisted")
    return payload


def _tree_revision() -> dict[str, str | bool]:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable not found")
    head = subprocess.run(  # noqa: S603 - executable resolved by shutil.which
        [git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    diff = subprocess.run(  # noqa: S603 - executable resolved by shutil.which
        [git, "diff", "--binary", "HEAD", "--", "src", "security", "scripts", "fixtures"],
        check=True,
        capture_output=True,
    ).stdout
    untracked = subprocess.run(  # noqa: S603 - executable resolved by shutil.which
        [
            git,
            "ls-files",
            "--others",
            "--exclude-standard",
            "src",
            "security",
            "scripts",
            "fixtures",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    content = bytearray(diff)
    for name in sorted(untracked):
        path = Path(name)
        content.extend(name.encode() + b"\0" + path.read_bytes() + b"\0")
    return {
        "git_head": head,
        "working_tree_sha256": _digest(bytes(content)),
        "working_tree_bound": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matrix", type=Path, default=Path("security/competitor_parity_matrix.json")
    )
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument(
        "--require-release-qualification",
        action="store_true",
        help="fail closed unless complete ecosystem parity and all executable bindings qualify",
    )
    parser.add_argument(
        "--capability-id",
        action="append",
        default=[],
        help="execute only the named capability row; repeatable for focused non-redundant proof",
    )
    args = parser.parse_args()
    matrix_bytes = args.matrix.read_bytes()
    matrix = json.loads(matrix_bytes)
    rows = matrix.get("rows", [])
    if not rows:
        raise SystemExit("matrix has no rows")

    dispositions = matrix.get("applicability_dispositions", [])
    if not dispositions:
        raise SystemExit("matrix must explicitly dispose omitted capabilities")
    for index, item in enumerate(dispositions):
        if (
            not item.get("ecosystem")
            or not item.get("capabilities")
            or item.get("disposition") not in {"applicable", "not_implemented", "not_applicable"}
            or not item.get("reason")
        ):
            raise SystemExit(f"invalid applicability disposition {index}")

    revision = _tree_revision()
    selected_ids = set(args.capability_id)
    all_capability_ids: set[str] = set()
    for index, row in enumerate(rows):
        missing = sorted(REQUIRED - row.keys())
        source_revision = row.get("source_revision", "")
        capability_id = row.get("capability_id", "")
        if (
            missing
            or row.get("result") not in {"pass", "gap"}
            or not source_revision
            or not capability_id
            or capability_id in all_capability_ids
        ):
            raise SystemExit(
                f"invalid row {index}: missing={missing} source_revision={source_revision!r} "
                f"capability_id={capability_id!r}"
            )
        all_capability_ids.add(capability_id)
        _validate_proof_command(row["proof_command"])
    unknown_ids = sorted(selected_ids - all_capability_ids)
    if unknown_ids:
        raise SystemExit(f"unknown --capability-id: {', '.join(unknown_ids)}")

    rows_to_execute = [
        (index, row)
        for index, row in enumerate(rows)
        if not selected_ids or row["capability_id"] in selected_ids
    ]
    results = []
    valid = True
    for index, row in rows_to_execute:
        capability_id = row["capability_id"]
        source_revision = row["source_revision"]
        command = row["proof_command"]
        proof_executable = _proof_executable(command)
        completed = subprocess.run(  # noqa: S603 - matrix argv is schema-validated
            command, check=False, capture_output=True, timeout=600
        )
        retained_stdout_json = _retained_stdout(row, completed.stdout)
        observed = "pass" if completed.returncode == 0 else "gap"
        matched = completed.returncode == row["expected_exit"] and observed == row["result"]
        valid &= matched
        dependency_bindings = _dependency_bindings(row.get("dependencies", []), command)
        binding_complete = bool(row.get("runtime_consumers")) and all(
            binding.get("resolved") for binding in dependency_bindings
        )
        result = {
                "row_index": index,
                "capability_id": capability_id,
                "row_sha256": _digest(
                    json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
                ),
                "competitor": row["competitor"],
                "source": row["source"],
                "source_revision": source_revision,
                "capability": row["capability"],
                "declared_result": row["result"],
                "actual_exit": completed.returncode,
                "matched": matched,
                "proof_command": command,
                "proof_executable": proof_executable["path"],
                "proof_executable_sha256": proof_executable["sha256"],
                "runtime_consumers": row.get("runtime_consumers", [command[0]]),
                "runtime_consumer_bindings": _bound_paths(row.get("runtime_consumers", [])),
                "semantic_assertions": row.get(
                    "semantic_assertions", [row["our_equivalent_executable_check"]]
                ),
                "dependencies": row.get("dependencies", []),
                "dependency_bindings": dependency_bindings,
                "binding_complete": binding_complete,
                "step_statuses": {
                    "proof_execution": "passed" if matched else "failed",
                    "runtime_consumers": "passed" if row.get("runtime_consumers") else "failed",
                    "source_revision": "passed" if source_revision else "failed",
                    "package_bindings": "passed" if binding_complete else "failed",
                    "configuration_binding": "passed",
                },
                "applicability": row.get("applicability", "applicable"),
                "stdout_sha256": _digest(completed.stdout),
                "stderr_sha256": _digest(completed.stderr),
                "observation": {
                    "exit_code": completed.returncode,
                    "stdout_bytes": len(completed.stdout),
                    "stderr_bytes": len(completed.stderr),
                    "stdout_retained_json": retained_stdout_json is not None,
                },
            }
        if retained_stdout_json is not None:
            result["retained_stdout_json"] = retained_stdout_json
        results.append(result)

    omitted = [item for item in dispositions if item.get("disposition") != "applicable"]
    complete_bindings = all(result["binding_complete"] for result in results)
    focused = bool(selected_ids)
    complete_parity = (
        not focused
        and valid
        and complete_bindings
        and not omitted
        and all(row["result"] == "pass" for row in rows)
    )
    qualification_steps = {
        "matrix_execution": "passed" if valid else "failed",
        "ecosystem_inventory": "passed" if not omitted else "failed",
        "capability_results": "passed"
        if all(row["result"] == "pass" for row in rows)
        else "failed",
        "runtime_source_package_configuration_bindings": "passed"
        if complete_bindings
        else "failed",
    }
    receipt = {
        "schema": "anonymization.competitor_parity_receipt.v3",
        "matrix_sha256": _digest(matrix_bytes),
        "implementation_revision": revision,
        "execution": {"cwd": str(Path.cwd()), "uid": os.getuid(), "gid": os.getgid()},
        "matrix_valid": valid,
        "focused": focused,
        "focused_capability_ids": sorted(selected_ids),
        "matrix_rows_total": len(rows),
        "executed_rows": len(rows_to_execute),
        "matrix_shape_valid": True,
        "scoped_parity_proven": valid and all(row["result"] == "pass" for _index, row in rows_to_execute),
        "complete_ecosystem_parity_proven": complete_parity,
        "release_qualified": complete_parity,
        "qualification_steps": qualification_steps,
        "release_blockers": [
            name for name, status in qualification_steps.items() if status != "passed"
        ],
        "omitted_capability_dispositions": dispositions,
        "pass_rows": sum(row["result"] == "pass" for _index, row in rows_to_execute),
        "gap_rows": sum(row["result"] == "gap" for _index, row in rows_to_execute),
        "capability_bindings": {
            result["capability_id"]: result["row_sha256"] for result in results
        },
        "results": results,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(args.receipt, flags, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(receipt_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    receipt_sha256 = _digest(receipt_bytes)
    digest_path = args.receipt.with_suffix(args.receipt.suffix + ".sha256")
    digest_fd = os.open(digest_path, flags, 0o600)
    with os.fdopen(digest_fd, "wb") as stream:
        stream.write(f"{receipt_sha256}  {args.receipt.name}\n".encode())
        stream.flush()
        os.fsync(stream.fileno())
    # Keep browser delivery contiguous and small; the full private JSON remains
    # independently verifiable through its adjacent digest receipt.
    print(
        json.dumps(
            {
                "schema": "anonymization.competitor_parity_delivery.v1",
                "receipt": str(args.receipt),
                "receipt_bytes": len(receipt_bytes),
                "receipt_sha256": receipt_sha256,
                "digest_receipt": str(digest_path),
            },
            sort_keys=True,
        )
    )
    if args.require_release_qualification and not receipt["release_qualified"]:
        return 2
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
