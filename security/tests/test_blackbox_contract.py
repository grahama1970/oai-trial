"""Black-box tests: attack only the evaluator-facing CLI + mount contract.

No access to internals — everything goes through `python -m anonymization_trial
run --input --output`, mimicking the evaluator. The criterion is not "returned
non-zero"; it is "an unsafe or leaky artifact never becomes a valid release".
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _src_dir() -> str:
    # Locate src/ by walking up to the repo root (dir holding pyproject.toml)
    # rather than counting parents[N], so relocating this test cannot break it.
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return str(parent / "src")
    raise RuntimeError("repo root (pyproject.toml) not found above this test")


def _run(inp: Path, out: Path) -> subprocess.CompletedProcess:
    # The pytest interpreter (sys.executable) is the system python without the
    # editable install, so the black-box subprocess needs src on PYTHONPATH.
    env = {**os.environ, "PYTHONPATH": _src_dir() + os.pathsep + os.environ.get("PYTHONPATH", "")}
    return subprocess.run(  # noqa: S603 (fixed argv; no shell, no untrusted input)
        [
            sys.executable, "-m", "anonymization_trial", "run",
            "--input", str(inp), "--output", str(out),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=env,
    )


def _corpus(inp: Path, files: dict[str, str], policy: dict) -> None:
    (inp / "corpus").mkdir(parents=True)
    (inp / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
    for name, content in files.items():
        (inp / "corpus" / name).write_text(content, encoding="utf-8")


_POLICY = {
    "version": 1,
    "sensitive_values": [
        {"rule_id": "r", "subject_id": "p", "type": "name", "value": "TopSecretName"}
    ],
    "protected_values": [],
}


def test_no_sensitive_value_in_release_or_stdio(tmp_path: Path):
    inp, out = tmp_path / "in", tmp_path / "out"
    _corpus(inp, {"a.txt": "hello TopSecretName world\n"}, _POLICY)
    proc = _run(inp, out)
    assert proc.returncode == 0
    body = (out / "corpus" / "a.txt").read_text(encoding="utf-8")
    assert "TopSecretName" not in body
    assert "TopSecretName" not in proc.stdout and "TopSecretName" not in proc.stderr


def test_deterministic_replay(tmp_path: Path):
    inp = tmp_path / "in"
    _corpus(inp, {"a.txt": "TopSecretName here\n"}, _POLICY)
    r1 = _run(inp, tmp_path / "out1")
    r2 = _run(inp, tmp_path / "out2")
    m1 = json.loads((tmp_path / "out1" / "report.json").read_text())["corpus_manifest_sha256"]
    m2 = json.loads((tmp_path / "out2" / "report.json").read_text())["corpus_manifest_sha256"]
    assert r1.returncode == 0 and r2.returncode == 0
    assert m1 == m2 and m1


def test_hostile_input_fails_closed_no_ready_marker(tmp_path: Path):
    inp, out = tmp_path / "in", tmp_path / "out"
    _corpus(inp, {"a.txt": "ok\n"}, _POLICY)
    (inp / "corpus" / "evil").symlink_to(inp / "policy.json")
    proc = _run(inp, out)
    assert proc.returncode != 0
    assert not (out / "report.json").exists()
    assert "unsafe_input" in proc.stderr


def test_report_declares_non_claims(tmp_path: Path):
    inp, out = tmp_path / "in", tmp_path / "out"
    _corpus(inp, {"a.txt": "TopSecretName\n"}, _POLICY)
    assert _run(inp, out).returncode == 0
    report = json.loads((out / "report.json").read_text())
    assert report["does_not_establish"]
    assert report["key_mode"] == "public-deterministic-trial-namespace"
