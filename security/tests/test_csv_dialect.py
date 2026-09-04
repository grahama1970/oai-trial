"""Acceptance test for ticket csv-dialect-failclosed (#4)."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from anonymization_trial.errors import AnonError
from anonymization_trial.formats import transform_file
from anonymization_trial.policy import compile_policy

_POLICY = compile_policy({
    "version": 1,
    "protected_values": [],
    "sensitive_values": [{"rule_id": "a", "subject_id": "s", "type": "name", "value": "Alice"}],
})


def test_semicolon_csv_is_rejected_not_silently_reinterpreted(tmp_path: Path) -> None:
    src = tmp_path / "a.csv"
    src.write_text("name;city\nAlice;NYC\n", encoding="utf-8")
    with pytest.raises(AnonError):
        transform_file(src, tmp_path / "o.csv", _POLICY)


@pytest.mark.parametrize("delimiter", [";", "\t", "|"])
@pytest.mark.parametrize("header", ['name{d}"city, state"\n', 'name,city\n'])
def test_semicolon_dialect_with_quoted_comma_is_rejected_before_release(
    tmp_path: Path, delimiter: str, header: str,
) -> None:
    source = tmp_path / "input"
    (source / "corpus").mkdir(parents=True)
    (source / "policy.json").write_text(json.dumps({
        "version": 1, "protected_values": [], "sensitive_values": [
            {"rule_id": "a", "subject_id": "s", "type": "name", "value": "Alice"},
        ],
    }))
    (source / "corpus/a.csv").write_text(
        header.format(d=delimiter) + f'Alice{delimiter}"Buffalo, NY"\n', encoding="utf-8",
    )
    output = tmp_path / "output"
    result = subprocess.run(  # noqa: S603 (fixed CLI argv, synthetic temp paths, no shell)
        [sys.executable, "-m", "anonymization_trial", "run",
         "--input", str(source), "--output", str(output)],
        capture_output=True, text=True, check=False, timeout=30,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")},
    )
    assert result.returncode != 0
    assert "unsupported_format" in result.stdout + result.stderr
    assert not list(output.rglob("*")), "rejected input left release artifacts"


def test_comma_csv_multi_column_still_accepted(tmp_path: Path) -> None:
    src = tmp_path / "a.csv"
    src.write_text("name,city\nAlice,NYC\n", encoding="utf-8")
    transform_file(src, tmp_path / "o.csv", _POLICY)  # must not raise


@pytest.mark.parametrize("bom", ["", "\ufeff"])
def test_quoted_punctuation_and_multiline_comma_csv_are_preserved(tmp_path: Path, bom: str) -> None:
    src, dst = tmp_path / "a.csv", tmp_path / "o.csv"
    src.write_text(
        bom + 'name,notes\r\nAlice,"Buffalo, NY; A|B\tC\r\nsays ""hello"""\r\n',
        encoding="utf-8", newline="",
    )
    transform_file(src, dst, _POLICY)
    with dst.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["name", "notes"]
    assert rows[1][0] != "Alice"
    assert rows[1][1] == 'Buffalo, NY; A|B\tC\r\nsays "hello"'
    assert dst.read_bytes().startswith(b"\xef\xbb\xbf") == bool(bom)


@pytest.mark.parametrize("row", ['Alice,"unterminated', 'Alice,"closed"junk\n', 'Alice,un"quoted\n'])
def test_malformed_comma_quoting_is_rejected(tmp_path: Path, row: str) -> None:
    src, dst = tmp_path / "a.csv", tmp_path / "o.csv"
    src.write_text("name,notes\n" + row, encoding="utf-8")
    with pytest.raises(AnonError, match="unsupported CSV dialect"):
        transform_file(src, dst, _POLICY)
    assert not dst.exists()


def test_single_column_comma_csv_still_accepted(tmp_path: Path) -> None:
    src = tmp_path / "a.csv"
    src.write_text("name\nAlice\n", encoding="utf-8")
    transform_file(src, tmp_path / "o.csv", _POLICY)  # must not raise
