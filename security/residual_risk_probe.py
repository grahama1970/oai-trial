#!/usr/bin/env python3
"""Bounded synthetic residual-risk probe (issue #12, production risk-plane).

Reads a released corpus directory and computes one concrete residual-risk
signal: quasi-identifier k-anonymity over CSV rows. A combination of declared
quasi-identifier columns that occurs exactly once (k=1) singles out a row even
after literal pseudonymization. Emits a ``residual_risk.v1`` receipt with
explicit non-claims.

This is a DESIGN-TIME / control-plane experiment, not the offline runtime. It
never authorizes publication and does not prove non-reidentifiability. Grounded
in SPIA (arXiv:2604.21211) and RAT-Bench (arXiv:2602.12806): span removal alone
does not bound subject-level or quasi-identifier exposure.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


def probe_csv(path: Path, quasi_identifiers: list[str]) -> dict:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {"file": path.name, "rows": 0, "singletons": 0, "min_k": None}
    header = rows[0].keys()
    cols = quasi_identifiers or [c for c in header]
    combos = Counter(tuple(row.get(c, "") for c in cols) for row in rows)
    singletons = sum(1 for n in combos.values() if n == 1)
    return {
        "file": path.name,
        "rows": len(rows),
        "quasi_identifiers": cols,
        "distinct_combos": len(combos),
        "singletons": singletons,
        "min_k": min(combos.values()),
    }


def probe_corpus(corpus: Path, quasi_identifiers: list[str]) -> dict:
    files = [probe_csv(p, quasi_identifiers) for p in sorted(corpus.rglob("*.csv"))]
    total_singletons = sum(f["singletons"] for f in files)
    return {
        "schema": "anonymization_trial.residual_risk.v1",
        "attack_profile": "quasi_identifier_k_anonymity_csv",
        "files": files,
        "total_singletons": total_singletons,
        "result": "review" if total_singletons else "pass_under_declared_attack_model",
        "does_not_prove": "universal_non_reidentifiability",
        "notes": "Declared quasi-identifier columns over CSV only; k=1 combos are singled out.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded residual-risk probe (control-plane)")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--quasi-identifiers", default="", help="comma-separated column names")
    args = parser.parse_args(argv)
    if not args.corpus.is_dir():
        print("corpus directory not found", file=sys.stderr)
        return 1
    qi = [c for c in args.quasi_identifiers.split(",") if c]
    print(json.dumps(probe_corpus(args.corpus, qi), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
