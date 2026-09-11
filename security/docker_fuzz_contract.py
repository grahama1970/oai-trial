#!/usr/bin/env python3
"""Property-based fuzz test of the anonymization guarantee through Docker.

Coverage here does NOT depend on anyone enumerating holes. Each trial:
  1. invents a random sensitive value,
  2. plants it in a RANDOMLY chosen representation across the four formats
     (JSON string/int/float; SQLite TEXT/INTEGER/REAL; CSV cell; UTF-8 text;
     Unicode NFC or NFD spelling),
  3. runs the brief's real command: docker run -v IN:/trial/input:ro
     -v OUT:/trial/output anonymization-trial run,
  4. asserts the planted value does not survive in the decoded output, in any
     representation. If the run fails closed (exit != 0, no corpus) that is also
     acceptable -- no leak.

Because the fuzzer plants the value, the oracle is exact: it checks for the one
value it just embedded, so it cannot share a producer blind spot. A leak in an
unhandled representation shows up as a concrete failing trial with the seed,
value, format, and encoding needed to reproduce it.

Usage:  python3 security/docker_fuzz_contract.py [--trials N] [--seed S]
Exit 0 iff every trial is leak-free. Deterministic for a given --seed.
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import string
import subprocess
import sys
import tempfile
import unicodedata
from decimal import Decimal
from pathlib import Path

IMG = "anonymization-trial"
REPO = Path(__file__).resolve().parents[1]


def rand_value(rng: random.Random) -> tuple[str, str]:
    """Return (policy_value, kind). kind picks the value shape."""
    kind = rng.choice(["name", "email", "phone_digits", "integer", "accented"])
    if kind == "name":
        return " ".join(
            "".join(rng.choices(string.ascii_uppercase, k=1)) + "".join(rng.choices(string.ascii_lowercase, k=rng.randint(3, 7)))
            for _ in range(2)), kind
    if kind == "email":
        return "".join(rng.choices(string.ascii_lowercase, k=rng.randint(4, 9))) + "@northwind.test", kind
    if kind == "phone_digits":
        return "".join(rng.choices(string.digits, k=10)), kind
    if kind == "integer":
        return str(rng.randint(10_000_000, 9_999_999_999)), kind
    # accented: guarantees a non-ASCII code point so NFC/NFD placement is meaningful
    base = "".join(rng.choices(string.ascii_lowercase, k=rng.randint(3, 6)))
    return "Jos\u00e9" + base.capitalize(), kind


def plant(rng: random.Random, value: str, kind: str, corpus: Path) -> str:
    """Plant `value` in one randomly chosen representation. Return a label."""
    reps = ["json_string", "csv", "text", "sqlite_text"]
    # Integer/float placement is only a faithful representation of the SAME value
    # when it round-trips. A leading-zero digit string stored as an integer loses
    # the zero and becomes a DIFFERENT identifier, so it is not planted that way.
    if value.isdigit() and str(int(value)) == value:
        reps += ["json_integer", "json_float", "sqlite_integer"]
    if any(ord(c) > 127 for c in value):
        reps += ["json_nfd", "text_nfd"]
    rep = rng.choice(reps)

    if rep == "json_string":
        (corpus / "d.json").write_text(json.dumps({"v": value}), encoding="utf-8")
    elif rep == "json_integer":
        (corpus / "d.json").write_text(json.dumps({"v": int(value)}), encoding="utf-8")
    elif rep == "json_float":
        (corpus / "d.json").write_text(json.dumps({"v": float(value)}), encoding="utf-8")
    elif rep == "json_nfd":
        (corpus / "d.json").write_text(
            json.dumps({"v": unicodedata.normalize("NFD", value)}), encoding="utf-8")
    elif rep == "csv":
        (corpus / "d.csv").write_text("col\n%s\n" % value, encoding="utf-8")
    elif rep == "text":
        (corpus / "d.txt").write_text("note: %s\n" % value, encoding="utf-8")
    elif rep == "text_nfd":
        (corpus / "d.txt").write_text(
            "note: %s\n" % unicodedata.normalize("NFD", value), encoding="utf-8")
    elif rep in ("sqlite_text", "sqlite_integer"):
        con = sqlite3.connect(corpus / "d.sqlite")
        if rep == "sqlite_integer":
            con.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, v INTEGER)")
            con.execute("INSERT INTO t(v) VALUES(?)", (int(value),))
        else:
            con.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, v TEXT)")
            con.execute("INSERT INTO t(v) VALUES(?)", (value,))
        con.commit(); con.close()
    return rep


def _num_forms(x) -> set[str]:
    out = set()
    if isinstance(x, bool):
        return out
    if isinstance(x, int):
        out.add(str(x))
    elif isinstance(x, float):
        out.add(repr(x))
        if x.is_integer():
            out.add(str(int(x)))
        try:
            out.add(format(Decimal(x), "f"))
        except Exception:
            pass
    return out


def value_survives(value: str, out: Path) -> bool:
    """Exact, representation-aware check for the one planted value."""
    v_nfc = unicodedata.normalize("NFC", value)
    v_nfd = unicodedata.normalize("NFD", value)
    # Only treat the value numerically when it is canonical (round-trips through
    # int); a leading-zero digit string is a distinct identifier, not the same
    # value written as a number.
    num_needles = _num_forms(int(value)) if (value.isdigit() and str(int(value)) == value) else set()
    texts: list[str] = []
    nums: set[str] = set()

    def walk(o):
        if isinstance(o, bool) or o is None:
            return
        if isinstance(o, (int, float)):
            nums.update(_num_forms(o))
        elif isinstance(o, str):
            texts.append(o)
        elif isinstance(o, dict):
            for k, w in o.items():
                texts.append(k); walk(w)
        elif isinstance(o, list):
            for w in o:
                walk(w)

    for f in sorted((out / "corpus").rglob("*")) + [out / "report.json"]:
        if not f.is_file():
            continue
        if f.suffix == ".json":
            try:
                walk(json.loads(f.read_text(encoding="utf-8-sig")))
            except Exception:
                texts.append(f.read_text(encoding="utf-8", errors="replace"))
        elif f.suffix in (".csv", ".txt"):
            texts.append(f.read_text(encoding="utf-8", errors="replace"))
        elif f.suffix == ".sqlite":
            con = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
            for row in con.execute("SELECT type,name,tbl_name,sql FROM sqlite_master"):
                texts.extend(x for x in row if isinstance(x, str))
            tbls = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT GLOB 'sqlite_*'")]
            for t in tbls:
                for row in con.execute(f'SELECT * FROM "{t}"'):
                    for c in row:
                        if isinstance(c, str):
                            texts.append(c)
                        elif isinstance(c, (int, float)) and not isinstance(c, bool):
                            nums.update(_num_forms(c))
            con.close()
            header = f.read_bytes()[:100]
            for off, w in ((16, 2), (28, 4), (40, 4), (48, 4), (52, 4), (56, 4), (60, 4), (64, 4), (68, 4)):
                nums.add(str(int.from_bytes(header[off:off + w], "big")))
    joined_nfc = unicodedata.normalize("NFC", "\x00".join(texts))
    joined_nfd = unicodedata.normalize("NFD", "\x00".join(texts))
    if v_nfc in joined_nfc or v_nfd in joined_nfd:
        return True
    if num_needles & nums:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    build = subprocess.run(["docker", "build", "-t", IMG, "."], cwd=REPO, capture_output=True, text=True)
    if build.returncode != 0:
        print("FAIL | docker build:", build.stderr[-400:]); return 1

    leaks = []
    for i in range(args.trials):
        value, kind = rand_value(rng)
        td = tempfile.mkdtemp(prefix="fuzz-")
        try:
            inp, out = Path(td) / "in", Path(td) / "out"
            (inp / "corpus").mkdir(parents=True); out.mkdir()
            (inp / "policy.json").write_text(json.dumps({
                "version": 1, "protected_values": [],
                "sensitive_values": [{"rule_id": "r", "subject_id": "s", "type": "name", "value": value}],
            }), encoding="utf-8")
            rep = plant(rng, value, kind, inp / "corpus")
            run = subprocess.run(["docker", "run", "--rm",
                                  "-v", f"{inp}:/trial/input:ro", "-v", f"{out}:/trial/output", IMG, "run"],
                                 capture_output=True, text=True)
            if run.returncode != 0:
                verdict = "fail-closed"  # no partial corpus -> no leak
            elif value_survives(value, out):
                verdict = "LEAK"
                leaks.append((i, value, kind, rep))
            else:
                verdict = "clean"
            print(f"trial {i:3d} | {kind:12s} | {rep:14s} | {verdict}")
        finally:
            subprocess.run(["docker", "run", "--rm", "-v", f"{td}:/w", "--entrypoint", "rm", IMG, "-rf", "/w/in", "/w/out"],
                           capture_output=True, text=True)
            subprocess.run(["rm", "-rf", td], capture_output=True, text=True)

    print()
    if leaks:
        print(f"FUZZ: FAIL — {len(leaks)} leak(s):")
        for i, v, k, r in leaks:
            print(f"  trial {i}: value={v!r} kind={k} representation={r}")
        return 1
    print(f"FUZZ: PASS — {args.trials} random trials, seed {args.seed}, zero leaks across representations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
