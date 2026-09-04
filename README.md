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
tests/             pytest suite (unit + fail-closed + per-format)
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

- **Checked (deterministic, local):** `uv run pytest -q` → 39 passed;
  `ruff check src tests` → clean; `docker build` + both `docker run` commands
  verified with read-back of `report.json` and all four output formats; demo
  reports per-run peak memory. Containerized SAST (Semgrep + Bandit) + dependency
  SCA via `$hack`: 0 critical / 0 high — see [`security/`](security).
  Privacy scope + non-claims: [`docs/PRIVACY_CONTRACT.md`](docs/PRIVACY_CONTRACT.md).
- **Not claimed here:** TB/PB scale is designed and cost-modelled, not run at
  scale; cloud prices are list prices not yet confirmed against a dated source;
  optional classifier/RapidFuzz discovery and the concurrent `ripgrep`
  cross-check are designed, not built.

Preserve the baseline git history and the two required `docker run` commands.
`.env` is gitignored; no real personal data or credentials belong in the repo.
