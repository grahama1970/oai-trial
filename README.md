# oai-trial — Cross-Format Data Anonymization

A fail-closed pipeline that replaces policy-identified values across CSV, JSON,
UTF-8 text, and SQLite while preserving structure, protected values, and
identity coherence — then verifies the whole corpus before it releases anything.

![Pipeline](docs/production-architecture.svg)

## Start here

| You want to… | Go to |
|---|---|
| Understand the whole design in 10 min | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Read the task as given | [`TRIAL_BRIEF.md`](TRIAL_BRIEF.md) |
| See the frozen correctness rules | [`docs/ANONYMIZATION_SEMANTICS.md`](docs/ANONYMIZATION_SEMANTICS.md) |
| Trace requirements → tests | [`docs/ACCEPTANCE_MATRIX.md`](docs/ACCEPTANCE_MATRIX.md) |
| Read the submission write-up | [`SUBMISSION.md`](SUBMISSION.md) |
| See the production design + cost | [`docs/production-architecture.md`](docs/production-architecture.md) |
| Read the code | `src/anonymization_trial/` |

## Requirement traceability

Brief ask → status → evidence. `done` = implemented and tested here; `extra` =
beyond the brief; `designed` = specified but not run/built (an explicit non-claim).

### Required by the brief

| Brief ask | Status | Evidence |
|---|---|---|
| Valid output in each input's logical format | done | `formats.py`, `tests/test_formats.py` |
| Replace every policy-identified value | done | `matcher.py`, `policy.py` |
| Stable replacements; distinct identities never share a type replacement; aliases converge | done | `pseudonyms.py` (`subject_id`), `tests/test_pipeline.py` |
| Preserve protected values + non-sensitive meaning | done | `policy.py` precedence, `docs/PRIVACY_CONTRACT.md` |
| Preserve CSV headers/rows, JSON structure, SQLite tables/relationships/row-counts/integrity | done | `formats.py`, `tests/test_json.py`, `tests/test_sqlite.py` |
| Verify the whole corpus before release | done | `verification.py`, `pipeline.py` |
| Keep raw inputs, mappings, quarantined content out of release + logs | done | `pipeline.py` staging, `errors.py` |
| Exit non-zero on failure; no partial releasable corpus | done | atomic publish, `security/tests/test_pipeline_failclosed.py` |
| `policy.json` v1 boundary (literal, `subject_id`/`match`/`case_sensitive`) | done | `policy.py` |
| Overlap precedence (nested/prefix/suffix/replacement-to-source), no cascades | done | `docs/ANONYMIZATION_SEMANTICS.md`, `matcher.py` |
| protected vs sensitive exact/contained/partial overlap | done | `policy.py` rejection, `docs/PRIVACY_CONTRACT.md` |
| CSV header with a sensitive literal transformed or rejected (never silently kept) | done | `formats.py` |
| Encoding/normalization policy; safe reject of malformed/unsupported; BOM/multibyte/locale case | done | `formats.py`, `errors.py` |
| Identity coherence across files/formats/retries | done | `pseudonyms.py` canonical `(data_type, subject_id)` |
| Dockerfile self-contained, no host services/secrets | done | `Dockerfile` |
| Bare-run demo: 4 formats, >=2 sizes (largest >=10x), reports time/rps/bps/peak-mem, exit 0 only if verify passes | done | `__main__.py demo` |
| Mounted run writes only `report.json` + `corpus/` | done | `pipeline.py` |
| Production design: provider + services, distribution/concurrency/skew, retries/replay/verify/publish, security boundaries, SLA | designed | `SUBMISSION.md`, `docs/production-architecture.md` |
| State/flow diagram, labels agree with prose, trust boundaries | done | `docs/production-architecture.svg` |
| Capacity + cost for 1 TB & 1 PB, reproducible arithmetic, cited prices, sensitivity | designed | `scripts/estimate_aws_cost.py`, `costs/` (list prices, unconfirmed) |
| Which local parts carry to prod vs replace, with triggering limit/tradeoff | done | `SUBMISSION.md`, `infra/mappings/PROVIDER_MAPPING.md` |
| Return whole repo incl `.git`; preserve baseline history; completed `SUBMISSION.md`; dependency declarations | done | baseline `eed780c` intact; stdlib-only |

### Extra credit (beyond the brief)

| Extra | Evidence |
|---|---|
| Independent verifier rereads output from disk (transformer cannot self-certify) | `verification.py`, `docs/ARCHITECTURE.md` |
| TOCTOU / `SOURCE_CHANGED` source-snapshot gate | `security/tests/test_source_snapshot.py` |
| Retained adversarial regression suite (fail-before-fix counterexamples from six external review rounds) | `security/tests/`, `security/ADVERSARIAL_MATRIX.md` |
| Bandit SAST clean via `$hack` (committed receipt shows Semgrep scanned 0 target files and no SCA receipt is committed — supporting evidence only) | `security/hack-audit.receipt.json`, `security/README.md` |
| Residual-risk probe | `security/residual_risk_probe.py` |
| Machine-readable privacy non-claims + `algorithm_version`/`scope_id` binding | `docs/PRIVACY_CONTRACT.md`, `pseudonyms.py` |
| Terraform AWS reference module (fmt+validate, plan-only) + provider capability map | `infra/terraform/`, `infra/mappings/` |
| Operability CLI: `explain` / `preflight` / `verify` / `inspect` | `__main__.py` |
| Presentation briefing deck (projection of this repo, for the walkthrough) | `docs/pitch/oai-trial/` |

### Future optimizations (designed, not built)

| Optimization | Trigger to build it |
|---|---|
| Entity discovery beyond literal policy (classifier / RapidFuzz) | inputs with un-catalogued identities |
| Concurrent `ripgrep` cross-check of the verifier | large-corpus verify latency |
| Run at real TB/PB scale | scale acceptance beyond the cost model |
| Confirm cloud prices against a dated source | promoting the cost claim past a list-price estimate |
| `verify-publish` provenance pass for deck claims | external deck delivery |

## What lives where

```
src/anonymization_trial/
  policy.py        strict policy compile + typed records
  matcher.py       Aho-Corasick exact matcher (leftmost-longest, no cascade)
  pseudonyms.py    deterministic, collision-safe replacements
  formats.py       CSV / JSON / TXT / SQLite adapters
  pipeline.py      preflight -> stage -> verify -> atomic publish
  verification.py  independent whole-corpus verifier
  errors.py        closed, privacy-safe error vocabulary
tests/             pytest suite (unit + per-format + CLI)
security/          white/gray/black-box + adversarial lineage (tests, battle, SAST)
docs/              semantics, acceptance matrix, production design, research
costs/             price inputs + reproducible estimate output
```

## Inspect a release (no server)

```bash
anonymization-trial explain                       # mechanism + guarantees
anonymization-trial preflight --input IN          # validate a bundle, produce no data
anonymization-trial run --input IN --output OUT   # anonymize
anonymization-trial verify --input IN --output OUT # independently reverify
anonymization-trial inspect OUT                    # safe evidence summary
```
`report.json` conforms to [`schemas/report.schema.json`](schemas/report.schema.json).

## Quickstart

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
uv run pytest -q                        # or: .venv/bin/python -m unittest discover -s tests
.venv/bin/anonymization-trial demo
.venv/bin/python fixtures/generate_fixture.py /tmp/trial-input --records 1000
```

## Container contract

```bash
docker build -t anonymization-trial .
docker run --rm anonymization-trial                       # self-contained demo
docker run --rm \
  -v "$INPUT":/trial/input:ro \
  -v "$OUTPUT":/trial/output \
  anonymization-trial run                                 # anonymize a mounted bundle
```

## Design rules

- Deterministic literal matching only; regex removed from the value path.
- Match original input, never rescan replacements (no cascade).
- Protected/sensitive overlap and sensitive schema identifiers are **rejected**,
  not silently resolved.
- Verify the whole corpus before release; fail closed (non-zero exit, no partial
  corpus, `report.json` written last as the only readiness marker).
- No replacement mapping or key material in the release dir or logs.

## Proof and non-claims

- **Checked (deterministic, local):** the full pytest gate passes (`uv run pytest -q`);
  `ruff check src tests scripts security` → clean; `docker build` + both `docker run` commands
  verified with read-back of `report.json` and all four output formats; demo
  reports per-run peak memory. Bandit SAST clean via `$hack`; the committed
  receipt shows Semgrep scanned 0 target files and no dependency-SCA receipt is
  committed, so scanner receipts are supporting evidence only — the executable
  adversarial evidence is the retained suite in [`security/`](security).
  Privacy scope + non-claims: [`docs/PRIVACY_CONTRACT.md`](docs/PRIVACY_CONTRACT.md).
- **Not claimed here:** TB/PB scale is designed and cost-modelled, not run at
  scale; cloud prices are list prices not yet confirmed against a dated source;
  optional classifier/RapidFuzz discovery and the concurrent `ripgrep`
  cross-check are designed, not built.

Preserve the baseline git history and the two required `docker run` commands.
`.env` is gitignored; no real personal data or credentials belong in the repo.
