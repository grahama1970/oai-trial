from __future__ import annotations

import csv
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from anonymization_trial.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[1]


def _fixture_generator():
    path = ROOT / "fixtures" / "generate_fixture.py"
    spec = importlib.util.spec_from_file_location("fixture_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_fixture


class PipelineTests(unittest.TestCase):
    def test_mixed_format_happy_path_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_root = root / "input"
            output_one = root / "output-one"
            output_two = root / "output-two"
            _fixture_generator()(input_root, 12)

            first = run_pipeline(input_root, output_one)
            second = run_pipeline(input_root, output_two)

            self.assertTrue(first.verification_passed)
            self.assertEqual(first.records_processed, second.records_processed)
            policy = json.loads((input_root / "policy.json").read_text(encoding="utf-8"))
            forbidden = [item["value"] for item in policy["sensitive_values"]]
            for path in (output_one / "corpus").glob("*.*"):
                if path.suffix != ".sqlite":
                    text = path.read_text(encoding="utf-8")
                    self.assertFalse(any(value in text for value in forbidden))

            with (output_one / "corpus" / "customers.csv").open(newline="", encoding="utf-8") as handle:
                csv_rows = list(csv.DictReader(handle))
            json_rows = json.loads((output_one / "corpus" / "events.json").read_text(encoding="utf-8"))
            self.assertEqual(csv_rows[1]["name"], json_rows[1]["actor"]["name"])
            self.assertEqual(csv_rows[1]["email"], json_rows[1]["actor"]["email"])
            self.assertEqual(csv_rows[1]["company"], "Northwind Research")

            with sqlite3.connect(output_one / "corpus" / "accounts.sqlite") as connection:
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM activity").fetchone()[0], 12)
                database_name = connection.execute("SELECT name FROM users WHERE id = 1").fetchone()[0]
            self.assertEqual(database_name, json_rows[0]["actor"]["name"])

    def test_report_is_sanitized_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_root = root / "input"
            output_root = root / "output"
            _fixture_generator()(input_root, 3)
            run_pipeline(input_root, output_root)
            report = json.loads((output_root / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "success")
            self.assertTrue(report["verification_passed"])
            self.assertEqual(report["files_processed"], 4)


if __name__ == "__main__":
    unittest.main()
