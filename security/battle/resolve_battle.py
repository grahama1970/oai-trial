#!/usr/bin/env python3
"""Resolve the pinned Battle evaluator bundle for the oai-trial gate.

Reads security/battle/battle.lock.json (battle.evaluator_lock.v1), materializes
the pinned commit with `git archive`, verifies the bundle manifest digest over
the recorded files, and prints the verified snapshot directory on stdout.

Fail-closed: any mismatch (bad commit, tampered bundle, missing file) exits
nonzero with a `lock-verification-failed` line. The digest is NEVER
auto-regenerated; an intentional upgrade edits the lock and re-qualifies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_LOCK = HERE / "battle.lock.json"


def _manifest_digest(root: Path, files: list[str]) -> str:
    manifest = []
    for rel in files:
        blob = (root / rel).read_bytes()
        manifest.append([rel, "sha256:" + hashlib.sha256(blob).hexdigest()])
    manifest.sort()
    return "sha256:" + hashlib.sha256(json.dumps(manifest).encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve the pinned Battle evaluator bundle")
    ap.add_argument("--lock", default=str(DEFAULT_LOCK))
    ap.add_argument("--keep", action="store_true", help="keep the snapshot (print a marker file path instead)")
    args = ap.parse_args()

    lock = json.loads(Path(args.lock).read_text(encoding="utf-8"))
    if lock.get("schema") != "battle.evaluator_lock.v1":
        print(f"run failed: lock-verification-failed (schema {lock.get('schema')!r} != battle.evaluator_lock.v1)", file=sys.stderr)
        return 1
    repo = Path(lock["source_repo_path"])
    commit = lock["commit"]
    expected = lock["bundle_manifest_sha256"]
    files = lock["bundle_files"]

    # The pinned commit must exist in the source repo.
    exists = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
                            capture_output=True)
    if exists.returncode != 0:
        print(f"run failed: lock-verification-failed (commit {commit} not present in {repo})", file=sys.stderr)
        return 1

    snapshot = Path(tempfile.mkdtemp(prefix="battle-evaluator-"))
    archive = subprocess.run(["git", "-C", str(repo), "archive", commit],
                             capture_output=True)
    if archive.returncode != 0:
        print(f"run failed: lock-verification-failed (git archive failed for {commit})", file=sys.stderr)
        return 1
    extract = subprocess.run(["tar", "-x", "-C", str(snapshot)], input=archive.stdout,
                             capture_output=True)
    if extract.returncode != 0:
        print("run failed: lock-verification-failed (archive extraction failed)", file=sys.stderr)
        return 1

    for rel in files:
        if not (snapshot / rel).is_file():
            print(f"run failed: lock-verification-failed (bundle file missing: {rel})", file=sys.stderr)
            return 1
    actual = _manifest_digest(snapshot, files)
    if actual != expected:
        print(f"run failed: lock-verification-failed (bundle manifest {actual} != locked {expected})", file=sys.stderr)
        return 1

    marker = snapshot / ".verified"
    marker.write_text(json.dumps({"commit": commit, "bundle_manifest_sha256": actual}) + "\n")
    print(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
