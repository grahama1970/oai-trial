"""Proposed acceptance tests from the frozen 4f332a7 coverage review.

Place this file under security/tests/ and run:
    uv run pytest -q security/tests/test_release_review_regressions.py

These are acceptance tests, not tests that assert vulnerable behavior.
They are expected to fail on the reviewed snapshot. The reviewer syntax-checked
this file but did not execute the full repository or Docker qualification.
All fixtures are synthetic; fault injection occurs BEFORE verification or at
an ordinary write API, not through a hostile concurrent staging writer.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from anonymization_trial import pipeline
from anonymization_trial.__main__ import main
from anonymization_trial.errors import AnonError
from anonymization_trial.policy import compile_policy, replace_text

PAYLOAD = {
    "version": 1,
    "sensitive_values": [
        {"rule_id": "name-a", "subject_id": "person-a", "type": "name", "value": "Alice"}
    ],
    "protected_values": [],
}


def _bundle(root: Path, table: str = "people") -> Path:
    # table is supplied only by the fixed synthetic test cases below.
    (root / "corpus").mkdir(parents=True)
    (root / "policy.json").write_text(json.dumps(PAYLOAD), encoding="utf-8")
    with sqlite3.connect(root / "corpus" / "data.sqlite") as connection:
        quoted = '"' + table.replace('"', '""') + '"'
        connection.execute(f"CREATE TABLE {quoted}(id INTEGER PRIMARY KEY, name TEXT)")
        connection.execute(
            f"INSERT INTO {quoted} VALUES (?, ?)",  # noqa: S608 (fixed, quoted synthetic identifier)
            (1, "Alice"),
        )
    return root


def test_sqlite_prefix_lookalike_is_processed(tmp_path: Path) -> None:
    """sqliteX is an ordinary user table, not a reserved sqlite_ object."""
    source = _bundle(tmp_path / "input", "sqliteX")
    output = tmp_path / "output"
    report = pipeline.run_pipeline(source, output)
    expected, _ = replace_text("Alice", compile_policy(PAYLOAD))
    with sqlite3.connect(output / "corpus" / "data.sqlite") as connection:
        actual = connection.execute('SELECT name FROM "sqliteX" WHERE id = 1').fetchone()[0]
    assert report.status == "ready"
    assert actual == expected, "READY release retained the original in an omitted user table"
    assert report.records_processed == 1
    with sqlite3.connect(source / "corpus" / "data.sqlite") as connection:
        assert connection.execute('SELECT name FROM "sqliteX"').fetchone()[0] == "Alice"


@pytest.mark.parametrize(
    "mutation_sql",
    [
        'ALTER TABLE people RENAME COLUMN name TO changed_name',
        "CREATE VIEW leaked AS SELECT 'Alice' AS name",
    ],
    ids=["renamed-column", "added-sensitive-view"],
)
def test_schema_mutation_is_rejected_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation_sql: str,
) -> None:
    """Inject a faulty adapter result before the real verifier and publisher."""
    source = _bundle(tmp_path / "input")
    # A clean positive control prevents an unrelated fixture failure from being
    # mistaken for successful detection of the injected mutation.
    pipeline.run_pipeline(source, tmp_path / "clean-output")
    original_transform = pipeline.transform_file

    def transform_with_schema_fault(src, dst, policy):
        result = original_transform(src, dst, policy)
        if dst.suffix == ".sqlite":
            with sqlite3.connect(dst) as connection:
                connection.execute(mutation_sql)
        return result

    monkeypatch.setattr(pipeline, "transform_file", transform_with_schema_fault)
    output = tmp_path / "fault-output"
    with pytest.raises(AnonError):
        pipeline.run_pipeline(source, output)
    assert not (output / "report.json").exists()
    assert not (output / "corpus").exists()


def test_short_report_write_cannot_return_success_with_truncated_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A legal short-write result must be completed or cause a safe failure."""
    source = _bundle(tmp_path / "input")
    pipeline.run_pipeline(source, tmp_path / "clean-output")
    real_write = pipeline.os.write

    def short_write(fd: int, data: bytes) -> int:
        # Progress is always positive so a correct write-all loop terminates.
        return real_write(fd, data[: max(1, len(data) // 2)])

    monkeypatch.setattr(pipeline.os, "write", short_write)
    output = tmp_path / "output"
    result = main(["run", "--input", str(source), "--output", str(output)])
    if result == 0:
        report = json.loads((output / "report.json").read_text(encoding="utf-8"))
        assert report["status"] == "ready"
        assert report["verification_passed"] is True
        assert report["corpus_manifest_sha256"] == pipeline._manifest_digest(output / "corpus")
    else:
        assert not (output / "report.json").exists()


def test_zero_report_write_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Local complement: a no-progress write must reject rather than loop forever."""
    source = _bundle(tmp_path / "input")
    monkeypatch.setattr(pipeline.os, "write", lambda _fd, _data: 0)
    output = tmp_path / "output"
    assert main(["run", "--input", str(source), "--output", str(output)]) != 0
    assert not (output / "report.json").exists()
