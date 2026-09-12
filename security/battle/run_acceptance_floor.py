#!/usr/bin/env python3
"""Run the frozen acceptance-contract floor through Battle's production adapter."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_path(value: str) -> Path:
    return (REPO / value).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _require_hash(path: Path, expected: str, label: str) -> None:
    actual = _sha256(path)
    if actual != expected:
        raise ValueError(f"{label} hash mismatch: {actual} != {expected}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", default=str(HERE / "acceptance.adapter.json"))
    parser.add_argument("--battle", required=True, help="verified Battle snapshot directory")
    parser.add_argument("--image", default="anonymization-trial")
    args = parser.parse_args()

    adapter_path = Path(args.adapter).resolve()
    adapter = _load_json(adapter_path)
    if adapter.get("schema") != "battle.acceptance_adapter.v1":
        raise ValueError("adapter schema must be battle.acceptance_adapter.v1")

    bundle_path = _repo_path(adapter["acceptance_bundle_path"])
    profile_path = _repo_path(adapter["profile_path"])
    lock_path = _repo_path(adapter["battle_lock_path"])
    _require_hash(bundle_path, adapter["acceptance_bundle_sha256"], "acceptance bundle")
    _require_hash(profile_path, adapter["profile_sha256"], "floor profile")
    generator_value = adapter["generator"]
    generator_path = None if "$BATTLE" in generator_value else _repo_path(generator_value)
    if generator_path is not None and adapter.get("generator_sha256"):
        _require_hash(generator_path, adapter["generator_sha256"], "floor generator")

    battle = str(Path(args.battle).resolve())
    work_root = _repo_path(adapter["work_root"])
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)

    request = {
        "schema": "battle.production_adapter_request.v1",
        "authorization_manifest": str((HERE / "authorization.json").resolve()),
        "expected_target": adapter["target_identity"],
        "acceptance_floor": {
            "bundle_path": str(bundle_path),
            "case_map": adapter["case_map"],
        },
        "base_request": {
            "schema": "battle.campaign_request.v1",
            "profile_path": str(profile_path),
            "lock_path": str(lock_path),
            "generator": str(generator_path) if generator_path is not None else generator_value.replace("$BATTLE", battle),
            "judge": adapter["judge"].replace("$BATTLE", battle),
            "functional_judge": adapter["functional_judge"].replace("$BATTLE", battle),
            "target_run_cmd": adapter["target_run_cmd"].format(image=args.image, input="{input}", output="{output}"),
            "work_root": str(work_root),
            "gen_params": adapter.get("gen_params", {}),
            "judge_params": adapter.get("judge_params", {}),
            "lineage": {"caller": "oai-trial-acceptance-floor", "adapter": str(adapter_path)},
        },
    }

    sys.path.insert(0, str(Path(battle) / "skills/battle/src"))
    from battle_skill.production_adapter import run_production_round

    receipt = run_production_round(request)
    out = work_root / "production-adapter-receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt.get("status"), "receipt": str(out)}, indent=2))
    return 0 if receipt.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
