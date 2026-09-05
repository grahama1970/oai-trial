#!/usr/bin/env python3
"""Qualify an exact clean GitHub checkout and package it with .git.

Development-only: Docker, git, uv, and jsonschema are required. The output oracle
uses csv/json/sqlite3 and the declared digest format, never the anonymizer's
transformer or verifier. Synthetic fixtures only; no host services in the image.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import jsonschema

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root: Path) -> str:
    state = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        state.update((path.relative_to(root).as_posix() + "\0" + digest(path) + "\0").encode())
    return state.hexdigest()


def fixture(root: Path) -> dict:
    corpus = root / "corpus"
    corpus.mkdir(parents=True)
    policy = {
        "version": 1,
        "sensitive_values": [
            {"rule_id": "a", "subject_id": "person-a", "type": "name", "value": "Alice"},
            {"rule_id": "alias", "subject_id": "person-a", "type": "name", "value": "A.L"},
            {"rule_id": "b", "subject_id": "person-b", "type": "name", "value": "Bob"},
        ],
        "protected_values": [{"value": "KEEP", "reason": "synthetic protected control"}],
    }
    (root / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
    (corpus / "people.csv").write_text("id,name,note\n1,Alice,KEEP\n2,A.L,KEEP\n3,Bob,KEEP\n")
    data = [
        {"name": "Alice", "flag": True, "n": 1, "note": "KEEP"},
        {"name": "A.L", "flag": False, "n": 2, "note": "KEEP"},
        {"name": "Bob", "flag": True, "n": 3, "note": "KEEP"},
    ]
    (corpus / "people.json").write_text(json.dumps(data))
    (corpus / "people.txt").write_text("Alice and A.L met Bob. KEEP\n")
    with sqlite3.connect(corpus / "people.sqlite") as db:
        db.executescript(
            "CREATE TABLE people(id INTEGER PRIMARY KEY, name TEXT, note TEXT);"
            "CREATE TABLE child(id INTEGER PRIMARY KEY, parent INTEGER REFERENCES people(id));"
            "CREATE TABLE sqliteX(v TEXT);"
            "CREATE INDEX by_name ON people(name);"
            "CREATE VIEW names AS SELECT id,name FROM people;"
        )
        db.executemany(
            "INSERT INTO people VALUES (?,?,?)", [(1, "Alice", "KEEP"), (2, "Bob", "KEEP")]
        )
        db.executemany("INSERT INTO child VALUES (?,?)", [(1, 1), (2, 2)])
        db.execute("INSERT INTO sqliteX VALUES (?)", ("Alice",))
    # Independent reference to the documented public v1 namespace, no runtime imports.
    return {
        name: "Person-"
        + hashlib.sha256(f"pseudonym-v1:trial-v1:1:name:person-{name}:0".encode()).hexdigest()[:10]
        for name in ("a", "b")
    }


def readback(source: Path, output: Path, golden: dict, schema: Path) -> dict:
    if {p.name for p in output.iterdir()} != {"corpus", "report.json"}:
        raise ValueError("release root must contain only corpus and report.json")
    corpus = output / "corpus"
    expected_files = {"people.csv", "people.json", "people.txt", "people.sqlite"}
    if {p.name for p in corpus.iterdir()} != expected_files:
        raise ValueError("corpus inventory changed")
    a, b = golden["a"], golden["b"]
    assert a != b
    with (corpus / "people.csv").open(newline="") as handle:
        assert list(csv.reader(handle)) == [
            ["id", "name", "note"],
            ["1", a, "KEEP"],
            ["2", a, "KEEP"],
            ["3", b, "KEEP"],
        ]
    data = json.loads((corpus / "people.json").read_text())
    assert data == [
        {"name": a, "flag": True, "n": 1, "note": "KEEP"},
        {"name": a, "flag": False, "n": 2, "note": "KEEP"},
        {"name": b, "flag": True, "n": 3, "note": "KEEP"},
    ]
    assert all(type(r["flag"]) is bool and type(r["n"]) is int for r in data)
    assert (corpus / "people.txt").read_text() == f"{a} and {a} met {b}. KEEP\n"
    with (
        sqlite3.connect(corpus / "people.sqlite") as db,
        sqlite3.connect(source / "corpus/people.sqlite") as src,
    ):
        assert db.execute('SELECT v FROM "sqliteX"').fetchall() == [(a,)]
        assert db.execute("SELECT * FROM people ORDER BY id").fetchall() == [
            (1, a, "KEEP"),
            (2, b, "KEEP"),
        ]
        assert db.execute("SELECT * FROM child ORDER BY id").fetchall() == [(1, 1), (2, 2)]
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        sql = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        assert db.execute(sql).fetchall() == src.execute(sql).fetchall()
        assert (
            db.execute("PRAGMA table_xinfo(people)").fetchall()
            == src.execute("PRAGMA table_xinfo(people)").fetchall()
        )
    report = json.loads((output / "report.json").read_text())
    jsonschema.Draft202012Validator(json.loads(schema.read_text())).validate(report)
    assert report["verification_passed"] is True
    assert report["policy_sha256"] == digest(source / "policy.json")
    assert report["source_manifest_sha256"] == manifest(source / "corpus")
    assert report["corpus_manifest_sha256"] == manifest(corpus) == report["verification_sha256"]
    return {
        "formats": sorted(expected_files),
        "corpus_sha256": manifest(corpus),
        "report_sha256": digest(output / "report.json"),
        "schema_validated": True,
    }


def qualify(out: Path) -> None:
    if not __debug__:
        raise RuntimeError("qualification assertions must not be disabled")
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    receipt = {
        "schema": "oai_trial.release_qualification.v1",
        "status": "RUNNING",
        "commands": commands,
        "started_at": datetime.now(UTC).isoformat(),
        "non_claims": [
            "No exhaustive crash/power-loss campaign or production-scale proof.",
            "No eight-hour timebox compliance claim or presentation approval.",
        ],
    }

    def run(argv, cwd=ROOT, expect=0):
        argv = list(map(str, argv))
        executable = shutil.which(argv[0])
        if not executable:
            raise RuntimeError(f"missing command: {argv[0]}")
        result = subprocess.run(  # noqa: S603 (fixed commands, shell disabled)
            [executable, *argv[1:]],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, "PYTHONPATH": ""},
            check=False,
        )
        log = out / f"command-{len(commands):02d}.log"
        log.write_text(result.stdout + result.stderr)
        commands.append(
            {
                "argv": argv,
                "cwd": str(cwd),
                "exit_code": result.returncode,
                "log": str(log),
                "sha256": digest(log),
            }
        )
        if (expect == 0 and result.returncode != 0) or (expect != 0 and result.returncode == 0):
            raise RuntimeError(f"unexpected exit {result.returncode}: {' '.join(argv)}")
        return result.stdout

    try:
        assert not run(["git", "status", "--porcelain"]).strip(), "commit before qualification"
        ref = run(["git", "rev-parse", "HEAD"]).strip()
        receipt["source_commit"] = ref
        remote = run(["git", "remote", "get-url", "origin"]).strip()
        checkout = out / "checkout"
        run(["git", "clone", "--single-branch", "--branch", "main", remote, checkout])
        assert run(["git", "rev-parse", "HEAD"], checkout).strip() == ref
        run(["git", "merge-base", "--is-ancestor", "eed780c", "HEAD"], checkout)
        run(["uv", "sync", "--locked", "--extra", "dev"], checkout)
        run(["uv", "run", "pytest", "-q"], checkout)
        run(["uv", "run", "ruff", "check", "src", "tests", "scripts", "security"], checkout)
        run(["docker", "build", "--no-cache", "-t", "anonymization-trial", "."], checkout)
        image = run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", "anonymization-trial"], checkout
        ).strip()
        receipt["image_id"] = image
        demo = json.loads(run(["docker", "run", "--rm", "anonymization-trial"], checkout))
        assert demo["demo"] == "success" and len(demo["runs"]) >= 2
        assert max(r["logical_records"] for r in demo["runs"]) >= 10 * min(
            r["logical_records"] for r in demo["runs"]
        )
        assert all(
            r["files_processed"] == 4
            and r["verification_passed"]
            and all(
                r[k] > 0
                for k in [
                    "elapsed_seconds",
                    "records_per_second",
                    "bytes_per_second",
                    "peak_memory_mb",
                ]
            )
            for r in demo["runs"]
        )
        receipt["demo"] = demo
        source = out / "input"
        golden = fixture(source)
        before = manifest(source)
        results = []
        for name, network in [("output", []), ("offline-output", ["--network=none"])]:
            target = out / name
            target.mkdir()
            stdout = run(
                [
                    "docker",
                    "run",
                    "--rm",
                    *network,
                    "-v",
                    f"{source}:/trial/input:ro",
                    "-v",
                    f"{target}:/trial/output",
                    "anonymization-trial",
                    "run",
                ],
                checkout,
            )
            assert not any(value in stdout for value in ["Alice", "A.L", "Bob", "KEEP"])
            results.append(
                readback(source, target, golden, checkout / "schemas/report.schema.json")
            )
        assert results[0]["corpus_sha256"] == results[1]["corpus_sha256"]
        assert manifest(source) == before
        receipt["readbacks"] = results
        for name, files in [
            ("early", {"a.csv": b'name;"city, state"\nAlice;"Buffalo, NY"\n'}),
            ("late", {"a.txt": b"Alice KEEP\n", "z.txt": b"\xff"}),
        ]:
            negative = out / name
            (negative / "corpus").mkdir(parents=True)
            shutil.copyfile(source / "policy.json", negative / "policy.json")
            for filename, content in files.items():
                (negative / "corpus" / filename).write_bytes(content)
            target = out / (name + "-output")
            target.mkdir()
            run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{negative}:/trial/input:ro",
                    "-v",
                    f"{target}:/trial/output",
                    "anonymization-trial",
                    "run",
                ],
                checkout,
                expect=1,
            )
            assert not list(target.iterdir()), "negative case left release artifacts"
            log = Path(commands[-1]["log"]).read_text()
            assert not any(value in log for value in ["Alice", "A.L", "Bob", "KEEP"])
        assert not run(["git", "status", "--porcelain"], checkout).strip()
        tracked = run(["git", "ls-files", "-z"], checkout).strip("\0").split("\0")
        assert ".env" not in tracked
        archive = out / f"oai-trial-{ref[:8]}.zip"
        paths = [checkout / p for p in tracked] + [
            p for p in (checkout / ".git").rglob("*") if p.is_file()
        ]
        with ZipFile(archive, "w", ZIP_DEFLATED) as z:
            for path in paths:
                z.write(path, "oai-trial/" + path.relative_to(checkout).as_posix())
        with ZipFile(archive) as z:
            assert z.testzip() is None
            for path in paths:
                assert (
                    z.read("oai-trial/" + path.relative_to(checkout).as_posix())
                    == path.read_bytes()
                )
            assert "oai-trial/.git/HEAD" in z.namelist()
        receipt.update(
            status="PASS",
            archive=str(archive),
            archive_sha256=digest(archive),
            baseline_history_preserved=True,
            source_unchanged=True,
            early_and_late_rejection=True,
        )
    except Exception as error:
        receipt.update(status="FAIL", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        receipt["finished_at"] = datetime.now(UTC).isoformat()
        (out / "QUALIFICATION.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    qualify(parser.parse_args().output.resolve())
