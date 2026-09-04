# oai-trial — Cloud Data Anonymization

Work trial: harden a starter into a scale-ready anonymization pipeline that
replaces policy-identified values across CSV, JSON, UTF-8 text, and SQLite while
preserving structure, protected values, and identity coherence.

- **Task brief (authoritative):** [`TRIAL_BRIEF.md`](TRIAL_BRIEF.md)
- **Immutable goal:** [`GOAL.md`](GOAL.md)
- **Submission write-up:** [`SUBMISSION.md`](SUBMISSION.md)

## Layout

```
src/anonymization_trial/   pipeline, formats, policy, fixture, CLI
tests/                     unittest suite
examples/                  policy.json + policy.schema.json
fixtures/                  synthetic corpus generator
agent-skills -> ../agent-skills   symlink so agent skills resolve
```

## Quickstart

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/anonymization-trial demo

# generate a synthetic input bundle
.venv/bin/python fixtures/generate_fixture.py /tmp/trial-input --records 1000
```

## Required container contract

```bash
docker build -t anonymization-trial .
docker run --rm anonymization-trial                       # self-contained demo
docker run --rm \
  -v "$INPUT":/trial/input:ro \
  -v "$OUTPUT":/trial/output \
  anonymization-trial run                                 # anonymize mounted bundle
```

## Rules

- No real personal data or credentials in the repo. `.env` is gitignored.
- Preserve baseline git history and the two required `docker run` commands.
- Verify the whole corpus before marking it releasable; fail closed (non-zero,
  no partial release) on any error.
