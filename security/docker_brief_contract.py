#!/usr/bin/env python3
"""Deterministic brief-contract test through the real Docker evaluator path.

Builds the image (recording the resulting image ID and git commit), runs BOTH
brief commands, and verifies the released output with a REPRESENTATION-AWARE
independent oracle. No agent interpretation: it asserts and exits 0 (PASS) or
1 (FAIL). Anyone runs `python3 security/docker_brief_contract.py` and gets the
same verdict.

The oracle is deliberately independent of the pipeline's own matcher/verifier
and is representation-aware (WebGPT audit 2026-09-11), so it cannot pass while a
value survives in an alternate spelling:
- JSON is PARSED (decoding \\uXXXX escapes), every key and scalar collected;
  numeric scalars expanded to integer/decimal canonical forms.
- SQLite: every table/view cell (numbers expanded), all sqlite_master DDL, and
  every documented header integer field read from the raw bytes.
- CSV/text: decoded UTF-8, NFC-normalized.
- report.json is scanned too (the whole released boundary, not just corpus/).
- Comparison is NFC-normalized on both sides; numeric policy values match any
  integer/decimal spelling.
Preconditions are asserted: each sensitive value must actually occur in the
INPUT (else the case is vacuous).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sqlite3
import sys
import tempfile
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

IMG = "anonymization-trial"
REPO = Path(__file__).resolve().parents[1]
FAIL: list[str] = []
_HEADER_FIELDS = ((16, 2), (28, 4), (40, 4), (44, 4), (48, 4), (52, 4),
                  (56, 4), (60, 4), (64, 4), (68, 4), (92, 4), (96, 4))


def check(cond: bool, msg: str) -> None:
    print(("PASS" if cond else "FAIL") + " | " + msg)
    if not cond:
        FAIL.append(msg)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _num_forms(x) -> set[str]:
    forms: set[str] = set()
    if isinstance(x, bool):
        return forms
    if isinstance(x, int):
        forms.add(str(x))
        return forms
    if isinstance(x, float):
        forms.add(repr(x))
        if x.is_integer():
            forms.add(str(int(x)))
        try:
            forms.add(format(Decimal(x), "f"))
        except (InvalidOperation, ValueError):
            pass
    return forms


def collect_scalars(path: Path) -> tuple[set[str], set[str]]:
    """Return (text_scalars_nfc, numeric_forms) decoded independently per format."""
    texts: set[str] = set()
    nums: set[str] = set()
    suf = path.suffix.lower()

    def walk_json(o) -> None:
        if isinstance(o, bool) or o is None:
            return
        if isinstance(o, (int, float)):
            nums.update(_num_forms(o))
        elif isinstance(o, str):
            texts.add(_nfc(o))
        elif isinstance(o, dict):
            for k, v in o.items():
                texts.add(_nfc(k)); walk_json(v)
        elif isinstance(o, list):
            for v in o:
                walk_json(v)

    if suf == ".json":
        try:
            walk_json(json.loads(path.read_text(encoding="utf-8-sig")))
        except Exception:
            texts.add(_nfc(path.read_text(encoding="utf-8", errors="replace")))
    elif suf in (".csv", ".txt", ".text"):
        texts.add(_nfc(path.read_text(encoding="utf-8", errors="replace")))
    elif suf == ".sqlite":
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        for row in con.execute("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            for field in row:
                if isinstance(field, str):
                    texts.add(_nfc(field))
        tbls = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT GLOB 'sqlite_*'")]
        for t in tbls:
            for row in con.execute(f'SELECT * FROM "{t.replace(chr(34), chr(34) * 2)}"'):
                for c in row:
                    if isinstance(c, str):
                        texts.add(_nfc(c))
                    elif isinstance(c, (int, float)) and not isinstance(c, bool):
                        nums.update(_num_forms(c))
                    elif isinstance(c, (bytes, bytearray)):
                        texts.add(_nfc(c.decode("utf-8", errors="replace")))
        con.close()
        header = path.read_bytes()[:100]
        for off, w in _HEADER_FIELDS:
            if off + w <= len(header):
                nums.add(str(int.from_bytes(header[off:off + w], "big")))
    return texts, nums


def gather(root: Path) -> tuple[str, set[str]]:
    """Whole-boundary scan: concatenated NFC text + set of numeric forms."""
    all_text = ""
    all_nums: set[str] = set()
    for f in sorted(root.rglob("*")):
        if f.is_file():
            t, n = collect_scalars(f)
            all_text += "\x00".join(t) + "\x00"
            all_nums |= n
    return all_text, all_nums


def value_present(value: str, text: str, nums: set[str]) -> bool:
    """Independent representation-aware membership: NFC substring OR numeric form."""
    v_nfc = _nfc(value)
    if v_nfc in text or unicodedata.normalize("NFD", value) in unicodedata.normalize("NFD", text):
        return True
    if value in nums:
        return True
    # policy value written as an integer string collides with an expanded number
    try:
        if str(int(value)) in nums:
            return True
    except ValueError:
        pass
    return False


def check_acceptance_bundle(path: Path) -> None:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    statements = "\n".join(req["statement"] for req in bundle.get("requirements", [])).lower()
    source_files = [f.get("path") for f in bundle.get("source", {}).get("files", [])]
    check(bundle.get("schema") == "acceptance_contract.bundle.v1", "acceptance bundle schema is acceptance_contract.bundle.v1")
    check(source_files == ["TRIAL_BRIEF.md", "examples/policy.json", "examples/policy.schema.json"],
          f"acceptance bundle source is only delivered spec files (got={source_files})")
    check(all(fmt in statements for fmt in ("csv", "json", "utf-8 text", "sqlite")),
          "acceptance bundle requires all four delivered formats")
    check("same synthetic identity can appear in every format" in statements,
          "acceptance bundle captures cross-format same-identity trap")
    check("verify the complete corpus before marking it ready for release" in statements,
          "acceptance bundle requires complete-corpus verification before release")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Docker brief-contract verification.")
    parser.add_argument("--acceptance-bundle", type=Path, help="Frozen acceptance_contract.bundle.v1 JSON to bind this Docker proof to.")
    args = parser.parse_args(argv)
    if args.acceptance_bundle is not None:
        check_acceptance_bundle(args.acceptance_bundle)

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                            capture_output=True, text=True).stdout.strip()
    build = subprocess.run(["docker", "build", "-t", IMG, "."], cwd=REPO,
                           capture_output=True, text=True)
    check(build.returncode == 0, "docker build exits 0")
    image_id = subprocess.run(["docker", "images", "--no-trunc", "-q", IMG],
                              capture_output=True, text=True).stdout.strip()
    print(f"     provenance: git_commit={commit[:12]} image_id={image_id[:19]}")

    demo = subprocess.run(["docker", "run", "--rm", IMG], capture_output=True, text=True)
    check(demo.returncode == 0, "bare demo exits 0")
    try:
        d = json.loads(demo.stdout)
        sizes = sorted(r["logical_records"] for r in d.get("runs", []))
        check(d.get("demo") == "success", "demo reports success")
        check(len(sizes) >= 2, "demo runs >=2 workload sizes")
        check(bool(sizes) and sizes[-1] >= 10 * sizes[0], "largest size >=10x smallest")
        check(all(r["verification_passed"] for r in d["runs"]), "each demo run verified")
    except (ValueError, KeyError, IndexError) as e:
        check(False, f"demo JSON parses with required fields ({e})")

    td = tempfile.mkdtemp(prefix="brief-contract-")
    try:
        inp, out = Path(td) / "in", Path(td) / "out"
        inp.mkdir(); out.mkdir()
        gen = subprocess.run([sys.executable, "fixtures/generate_fixture.py", str(inp), "--records", "500"],
                             cwd=REPO, capture_output=True, text=True,
                             env={"PYTHONPATH": str(REPO / "src"), "PATH": "/usr/bin:/bin"})
        check(gen.returncode == 0, "fixture bundle generated")

        pol = json.loads((inp / "policy.json").read_text())
        sensitive = [str(v["value"]) for v in pol["sensitive_values"]]
        protected = [str(v["value"]) for v in pol.get("protected_values", [])]

        # PRECONDITION: every sensitive value actually occurs in the input, else vacuous.
        in_text, in_nums = gather(inp / "corpus")
        missing_pre = [v for v in sensitive if not value_present(v, in_text, in_nums)]
        check(not missing_pre, f"precondition: every sensitive value present in input (missing={missing_pre})")

        run = subprocess.run(["docker", "run", "--rm",
                              "-v", f"{inp}:/trial/input:ro", "-v", f"{out}:/trial/output", IMG, "run"],
                             capture_output=True, text=True)
        check(run.returncode == 0, "mounted run exits 0")

        rel = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
        in_corpus = {("corpus/" + p.relative_to(inp / "corpus").as_posix()) for p in (inp / "corpus").rglob("*") if p.is_file()}
        check(rel == {"report.json"} | in_corpus,
              f"output tree is exactly report.json + mirrored corpus (got {sorted(rel)})")

        # Representation-aware leak scan over the WHOLE released boundary (corpus + report.json).
        out_text, out_nums = gather(out)
        leaked = [v for v in sensitive if value_present(v, out_text, out_nums)]
        check(not leaked, f"no sensitive value survives in released output, any representation (leaked={leaked})")

        # Protected values preserved (still present in output).
        for pv in protected:
            check(value_present(pv, out_text, out_nums), f"protected value preserved: {pv!r}")
    finally:
        subprocess.run(["docker", "run", "--rm", "-v", f"{td}:/w", "--entrypoint", "rm", IMG, "-rf", "/w/in", "/w/out"],
                       capture_output=True, text=True)
        subprocess.run(["rm", "-rf", td], capture_output=True, text=True)

    print("\n" + ("BRIEF CONTRACT: PASS" if not FAIL else f"BRIEF CONTRACT: FAIL ({len(FAIL)})"))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
