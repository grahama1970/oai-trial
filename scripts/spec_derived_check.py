#!/usr/bin/env python3
"""Acceptance check DERIVED FROM the delivered spec, not the code.

Reads the sensitive values from policy.json (the delivered spec) and asserts
none of them appears in the decoded content of any released file, in ANY
representation the format admits. This is the check the brief already defines:
"replace every value identified by the input policy." No hand-authored value
list, no code-shaped assumptions.

  python3 scripts/spec_derived_check.py --policy <policy.json> --corpus <output/corpus>

Exit 0 iff no policy value survives. A phone stored as a JSON/SQLite integer is
caught because str(5551234567) contains the policy string "5551234567".
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Any


def policy_values(policy_path: Path) -> list[str]:
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    return [str(v["value"]) for v in data.get("sensitive_values", []) if v.get("value") is not None]


def decoded_scalars(path: Path) -> list[str]:
    out: list[str] = []
    suf = path.suffix.lower()
    if suf == ".json":
        def walk(o: Any) -> None:
            if isinstance(o, bool) or o is None:
                return
            if isinstance(o, (int, float)):
                out.append(repr(o) if isinstance(o, float) else str(o))
            elif isinstance(o, str):
                out.append(o)
            elif isinstance(o, dict):
                for k, v in o.items():
                    out.append(k)
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(json.loads(path.read_text(encoding="utf-8-sig")))
    elif suf in (".csv", ".txt"):
        out.append(path.read_text(encoding="utf-8"))
    elif suf == ".sqlite":
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'")]
        for tbl in tables:
            for row in con.execute(f'SELECT * FROM "{tbl}"'):
                for val in row:
                    if isinstance(val, bool) or val is None:
                        continue
                    if isinstance(val, (int, float)):
                        out.append(repr(val) if isinstance(val, float) else str(val))
                    elif isinstance(val, str):
                        out.append(val)
                    elif isinstance(val, (bytes, bytearray)):
                        out.append(val.decode("utf-8", errors="replace"))
        con.close()
    return out


def scan(values: list[str], corpus: Path) -> list[dict[str, str]]:
    leaks: list[dict[str, str]] = []
    for path in sorted(corpus.rglob("*")):
        if path.is_dir():
            continue
        for scalar in decoded_scalars(path):
            norm = unicodedata.normalize("NFC", scalar)
            for val in values:
                if val in scalar or unicodedata.normalize("NFC", val) in norm:
                    leaks.append({"value": val, "file": str(path.relative_to(corpus))})
    return leaks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True, type=Path)
    ap.add_argument("--corpus", required=True, type=Path)
    args = ap.parse_args()
    values = policy_values(args.policy)
    leaks = scan(values, args.corpus)
    print(json.dumps({"policy_values": len(values), "leaks": leaks, "passed": not leaks}, indent=2))
    return 0 if not leaks else 1


if __name__ == "__main__":
    raise SystemExit(main())
