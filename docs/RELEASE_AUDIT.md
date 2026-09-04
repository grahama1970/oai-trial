# Release audit (clean-clone)

Independent audit from a fresh `git clone` (no inherited venv, no local services).
Resolves GitHub issue #11. Re-runnable with the commands below.

## Results

| Check | Result |
|---|---|
| Baseline git history preserved | PASS (`eed780c Initial work trial` present) |
| Secret/symlink hygiene | PASS (no `.env` or `agent-skills` tracked) |
| `pip install -e .` + `pytest` | PASS (35 passed) |
| `ruff check src tests scripts` | PASS (All checks passed) |
| `docker build --no-cache` | PASS |
| `docker run --rm <img>` (demo) | PASS (2 sizes, 4 files each) |
| Mounted `run` happy path | PASS (`status: ready`, report + 4 formats read back) |
| Cost model reproduces | PASS (1 TB ≈ $52, 1 PB ≈ $51,836) |

## Fail-closed negative matrix

Each exits non-zero with a typed, privacy-safe reason and leaves **no**
`report.json` ready marker:

| Case | Exit | Reason code |
|---|---|---|
| unsupported file type | 1 | `unsupported_format` |
| symlink in corpus | 1 | `unsafe_input` |
| bad policy version | 1 | `invalid_policy` |
| sensitive literal in CSV header | 1 | `sensitive_in_schema_identifier` |
| protected/sensitive overlap | 1 | `protected_sensitive_overlap` |
| malformed UTF-8 | 1 | `malformed_encoding` |

## Reproduce

```bash
git clone <repo> /tmp/oai-audit && cd /tmp/oai-audit
python3.12 -m venv .venv && .venv/bin/pip install -e . pytest ruff
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests scripts
docker build --no-cache -t oai-audit .
docker run --rm oai-audit
docker run --rm -v "$IN:/trial/input:ro" -v "$OUT:/trial/output" oai-audit run
python scripts/estimate_aws_cost.py --inputs costs/aws-us-east-1-inputs.json
```

## Proof boundary

Local + in-container deterministic checks only. Not run at TB/PB scale; cloud
prices are list prices not yet confirmed against a dated source; optional
discovery (classifier/RapidFuzz) and the concurrent `ripgrep` cross-check are
designed, not built (see `SUBMISSION.md`).
