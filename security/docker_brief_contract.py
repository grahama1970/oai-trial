#!/usr/bin/env python3
"""Deterministic brief-contract test through the real Docker evaluator path.

Builds the image, runs BOTH brief commands, and independently verifies the
released corpus. No agent interpretation: it asserts and exits 0 (PASS) or
1 (FAIL). Anyone -- including the evaluator -- runs `python3
security/docker_brief_contract.py` and gets the same verdict.

Checks (each an assertion, not a claim):
1. docker build succeeds.
2. `docker run --rm anonymization-trial` (bare demo): exit 0, JSON demo==success,
   >=2 workload sizes, largest >=10x smallest, verification_passed on each.
3. `docker run ... run` on a generated bundle: exit 0.
4. Output tree is EXACTLY report.json + corpus/ mirroring the input logical paths.
5. Independent leak scan: NONE of policy.json's sensitive values appear in the
   decoded released corpus (JSON scalars, SQLite cells, raw SQLite bytes, text/CSV).
6. Every protected value's occurrence count is preserved.
"""
from __future__ import annotations

import json
import subprocess
import sqlite3
import sys
import tempfile
from pathlib import Path

IMG = "anonymization-trial"
REPO = Path(__file__).resolve().parents[1]
FAIL = []


def check(cond: bool, msg: str) -> None:
    print(("PASS" if cond else "FAIL") + " | " + msg)
    if not cond:
        FAIL.append(msg)


def decoded_corpus_text(corpus: Path) -> str:
    blob = ""
    for f in sorted(corpus.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix == ".sqlite":
            con = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
            for t in [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT GLOB 'sqlite_*'")]:
                for row in con.execute(f'SELECT * FROM "{t}"'):
                    blob += " ".join(str(c) for c in row)
            con.close()
            blob += f.read_bytes().decode("latin-1")
        else:
            blob += f.read_text(encoding="utf-8", errors="replace")
    return blob


def main() -> int:
    build = subprocess.run(["docker", "build", "-t", IMG, "."], cwd=REPO,
                           capture_output=True, text=True)
    check(build.returncode == 0, "docker build exits 0")

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

    # Not TemporaryDirectory: the container writes root-owned files into the
    # mounted output, so auto-cleanup raises PermissionError and would mask the
    # verdict. Use an explicit dir and clean root-owned files via the container.
    td = tempfile.mkdtemp(prefix="brief-contract-")
    try:
        inp, out = Path(td) / "in", Path(td) / "out"
        inp.mkdir(); out.mkdir()
        gen = subprocess.run([sys.executable, "fixtures/generate_fixture.py", str(inp), "--records", "500"],
                             cwd=REPO, capture_output=True, text=True,
                             env={"PYTHONPATH": str(REPO / "src"), "PATH": "/usr/bin:/bin"})
        check(gen.returncode == 0, "fixture bundle generated")

        run = subprocess.run(["docker", "run", "--rm",
                              "-v", f"{inp}:/trial/input:ro", "-v", f"{out}:/trial/output", IMG, "run"],
                             capture_output=True, text=True)
        check(run.returncode == 0, "mounted run exits 0")

        rel = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
        in_corpus = {("corpus/" + p.relative_to(inp / "corpus").as_posix()) for p in (inp / "corpus").rglob("*") if p.is_file()}
        expected = {"report.json"} | in_corpus
        check(rel == expected, f"output tree is exactly report.json + mirrored corpus (got {sorted(rel)})")

        pol = json.loads((inp / "policy.json").read_text())
        sensitive = [str(v["value"]) for v in pol["sensitive_values"]]
        protected = [str(v["value"]) for v in pol.get("protected_values", [])]
        out_text = decoded_corpus_text(out / "corpus")
        in_text = decoded_corpus_text(inp / "corpus")
        leaked = [v for v in sensitive if v in out_text]
        check(not leaked, f"no sensitive value survives in released corpus (leaked={leaked})")
        for pv in protected:
            check(out_text.count(pv) == in_text.count(pv), f"protected value preserved: {pv!r}")
    finally:
        # root-owned container output: remove via a throwaway container, then rmdir.
        subprocess.run(["docker", "run", "--rm", "-v", f"{td}:/w", "--entrypoint", "rm", IMG, "-rf", "/w/in", "/w/out"],
                       capture_output=True, text=True)
        subprocess.run(["rm", "-rf", td], capture_output=True, text=True)

    print("\n" + ("BRIEF CONTRACT: PASS" if not FAIL else f"BRIEF CONTRACT: FAIL ({len(FAIL)})"))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
