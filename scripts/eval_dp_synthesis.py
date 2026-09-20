from __future__ import annotations

import csv
import json
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="dp-synthesis-eval-") as tmp:
        work = Path(tmp)
        source = work / "people.csv"
        domain = work / "domain.json"
        output = work / "synthetic.csv"
        receipt = work / "receipt.json"
        source.write_text(
            "region,condition\nurban,A\nurban,A\nrural,B\n",
            encoding="utf-8",
        )
        empty_source = work / "empty.csv"
        empty_output = work / "empty-synthetic.csv"
        empty_receipt = work / "empty-receipt.json"
        existing_receipt = work / "existing-receipt.json"
        blocked_output = work / "blocked-synthetic.csv"
        alias_path = work / "alias.csv"
        ledger = work / "budget.json"
        persistent_output = work / "persistent-synthetic.csv"
        persistent_receipt = work / "persistent-receipt.json"
        empty_source.write_text("region,condition\n", encoding="utf-8")
        existing_receipt.write_text("{}\n", encoding="utf-8")
        domain.write_text(
            json.dumps({"region": ["urban", "rural"], "condition": ["A", "B"]}),
            encoding="utf-8",
        )
        cmd = [
            str(root / ".venv/bin/python"),
            "-m",
            "anonymization_trial",
            "dp-synthesize",
            "--input",
            str(source),
            "--output",
            str(output),
            "--domain",
            str(domain),
            "--dimensions",
            "region,condition",
            "--epsilon",
            "0.7",
            "--receipt",
            str(receipt),
        ]
        completed = subprocess.run(cmd, cwd=root, check=True, capture_output=True, text=True)
        summary = json.loads(completed.stdout)
        assert summary["schema"] == "differentially_private_synthetic_histogram.v1"
        assert summary["receipt"] == str(receipt)
        reader = csv.DictReader(output.open(newline="", encoding="utf-8"))
        data = list(reader)
        assert reader.fieldnames == ["region", "condition"]
        assert all(set(row) == {"region", "condition"} for row in data)
        assert all(row["region"] in {"urban", "rural"} for row in data)
        assert all(row["condition"] in {"A", "B"} for row in data)
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        assert payload["privacy_guarantee"] == "pure_epsilon_differential_privacy"
        assert payload["composition"] == "histogram_parallel_cells_one_record_one_cell"
        assert payload["domain_cell_count"] == 4
        assert payload["source_records"] == 3
        assert payload["synthetic_records"] == len(data)
        assert payload["receipt_contains_domain_values"] is False
        assert payload["publication_atomicity"] == "staged_csv_and_private_receipt_before_release_path"
        assert "urban" not in receipt.read_text(encoding="utf-8")
        assert "condition" not in receipt.read_text(encoding="utf-8")
        assert receipt.stat().st_mode & 0o777 == 0o600

        empty_cmd = [*cmd]
        empty_cmd[empty_cmd.index(str(source))] = str(empty_source)
        empty_cmd[empty_cmd.index(str(output))] = str(empty_output)
        empty_cmd[empty_cmd.index(str(receipt))] = str(empty_receipt)
        subprocess.run(empty_cmd, cwd=root, check=True, capture_output=True, text=True)
        empty_reader = csv.DictReader(empty_output.open(newline="", encoding="utf-8"))
        empty_rows = list(empty_reader)
        assert empty_reader.fieldnames == ["region", "condition"]
        assert all(set(row) == {"region", "condition"} for row in empty_rows)
        assert all(row["region"] in {"urban", "rural"} for row in empty_rows)
        assert all(row["condition"] in {"A", "B"} for row in empty_rows)
        empty_payload = json.loads(empty_receipt.read_text(encoding="utf-8"))
        assert empty_payload["source_records"] == 0
        assert empty_payload["synthetic_records"] == len(empty_rows)
        assert empty_payload["adjacency"] == "add_remove_one_record"

        alias_cmd = [*cmd]
        alias_cmd[alias_cmd.index(str(output))] = str(alias_path)
        alias_cmd[alias_cmd.index(str(receipt))] = str(alias_path)
        alias = subprocess.run(alias_cmd, cwd=root, capture_output=True, text=True)
        assert alias.returncode != 0
        assert not alias_path.exists()

        for alias_target in (persistent_output, persistent_receipt):
            ledger_alias_cmd = [*cmd, "--budget-ledger", str(alias_target), "--budget-id", "release-authorization", "--maximum-epsilon", "1.4"]
            ledger_alias_cmd[ledger_alias_cmd.index(str(output))] = str(persistent_output)
            ledger_alias_cmd[ledger_alias_cmd.index(str(receipt))] = str(persistent_receipt)
            ledger_alias = subprocess.run(ledger_alias_cmd, cwd=root, capture_output=True, text=True)
            assert ledger_alias.returncode != 0
            assert not persistent_output.exists()
            assert not persistent_receipt.exists()

        persistent_cmd = [*cmd, "--budget-ledger", str(ledger), "--budget-id", "release-authorization", "--maximum-epsilon", "1.4"]
        persistent_cmd[persistent_cmd.index(str(output))] = str(persistent_output)
        persistent_cmd[persistent_cmd.index(str(receipt))] = str(persistent_receipt)
        subprocess.run(persistent_cmd, cwd=root, check=True, capture_output=True, text=True)
        persistent_payload = json.loads(persistent_receipt.read_text(encoding="utf-8"))
        assert persistent_payload["schema"] == "differentially_private_synthetic_histogram_persistent.v1"
        assert persistent_payload["cumulative_epsilon"] == 0.7
        assert persistent_payload["budget_ledger_contains_domain_values"] is False
        assert "urban" not in ledger.read_text(encoding="utf-8")
        assert "release-authorization" not in ledger.read_text(encoding="utf-8")

        blocked_cmd = [*cmd]
        blocked_cmd[blocked_cmd.index(str(output))] = str(blocked_output)
        blocked_cmd[blocked_cmd.index(str(receipt))] = str(existing_receipt)
        blocked = subprocess.run(blocked_cmd, cwd=root, capture_output=True, text=True)
        assert blocked.returncode != 0
        assert not blocked_output.exists()
    print("DP_SYNTHESIS_REAL_PATH_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
