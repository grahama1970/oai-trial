# Cloud data anonymization at scale

## Scenario

A fictional analytics company receives customer exports. Its privacy team must anonymize each export before another internal team can use it. Exports can eventually reach terabyte or petabyte scale and contain CSV, JSON, UTF-8 text, and SQLite database files. The same synthetic identity can appear in every format.

The repository contains a deliberately small starter and a synthetic fixture generator. You have eight hours to harden it. Your choices and evidence matter more than how much code you add.

Stop after eight hours. List unfinished work and tradeoffs in `SUBMISSION.md`. Do not hide extra time.

## Required behavior

Every successful run must meet these requirements:

- Produce useful, valid output in the same logical format as each input.
- Replace every value identified by the input policy.
- Keep replacements stable across files and repeated runs. Distinct identities must not share a type-specific replacement; aliases of one identity may intentionally converge.
- Preserve protected values and the meaning of other non-sensitive data.
- Preserve CSV headers and rows, JSON structure, and SQLite tables, relationships, row counts, and integrity.
- Verify the complete corpus before marking it ready for release.
- Keep raw inputs, replacement mappings, and quarantined content out of the release directory and logs.
- Exit non-zero after a failure. Do not leave a partial corpus that looks ready for release.

`policy.json` lists seeded synthetic values, their types, identity groups, and literal match behavior. You may treat that file as your input boundary, add a discovery step, or choose another boundary. Explain what you chose and what it would mean in production.

## Policy contract

The mounted `policy.json` uses schema version 1. A complete, synthetic example
is checked in at [`examples/policy.json`](examples/policy.json), with its
machine-readable schema at [`examples/policy.schema.json`](examples/policy.schema.json).
The example demonstrates the optional `subject_id`, `match`, and
`case_sensitive` fields; omitted `match` defaults to `literal` and omitted
`case_sensitive` defaults to `true`. `protected_values` must not be changed.
The starter supports literal matching only and rejects another `match` value.

## Edge-case policy

Document how your solution treats overlapping sensitive literals (including
nested, prefix/suffix, and replacement-to-source overlaps). State a deterministic
precedence policy that prevents replacement cascades and explain what happens if
protected and sensitive values overlap exactly, are contained by one another, or
partially intersect. Also document whether a CSV header
containing a sensitive literal is transformed with a downstream schema mapping
or rejected before release; silently retaining the sensitive header is unsafe.

State an encoding and normalization policy. The starter's contract is UTF-8,
literal matching; a submission may support more, but must safely and
sanitizedly reject malformed or unsupported encodings rather than emit a
partial release. Document BOM, multibyte, and locale-sensitive case behavior.

Preserve identity coherence across contexts: values known or discovered to belong to one identity should form one stable pseudonymous profile across files, formats, partitions, and retries. A policy `subject_id` supplies a known identity link. Additional entity discovery is optional. Type-appropriate profile values do not need to share a visible identifier, and you do not need to change the input schema.

## Container contract

Provide a `Dockerfile` that builds without host services or secrets:

You may install Python packages, system packages, command-line programs, or other tools needed by your solution. Include and configure every dependency in the `Dockerfile` so the final image is self-contained and the required commands work on the evaluator's Docker host without additional software.

```bash
docker build -t anonymization-trial .
```

A bare run must execute a self-contained demonstration and then exit:

```bash
docker run --rm anonymization-trial
```

The demonstration must process all four formats at two or more synthetic workload sizes, with the largest at least 10 times the smallest. Report elapsed time, records per second, bytes per second, and peak memory when it can be measured. Exit zero only when the demonstrated outputs pass your verification.

The evaluator will also mount an unseen input bundle and an empty output directory:

```bash
docker run --rm \
  -v "$INPUT":/trial/input:ro \
  -v "$OUTPUT":/trial/output \
  anonymization-trial run
```

The mounted input has this shape:

```text
/trial/input/
  policy.json
  corpus/
    ... .csv, .json, .txt, and .sqlite files
```

On success, write only the releasable corpus and a sanitized report:

```text
/trial/output/
  report.json
  corpus/
    ... matching logical input paths
```

You may support additional commands or configuration and document them in `SUBMISSION.md`, but preserve the two commands above.

## Starter commands

The starter requires Python 3.12 and has no third-party runtime dependencies. This describes the starter, not a restriction on your solution; you may add any dependencies that can be packaged into the final Docker image.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/anonymization-trial demo
```

The fixture generator can create a bundle of any requested logical size:

```bash
.venv/bin/python fixtures/generate_fixture.py /tmp/trial-input --records 1000
```

You may replace or reorganize the starter code. Preserve the container and input/output contracts.

## Production cloud design

Use `SUBMISSION.md` to describe how you would run this pipeline at terabyte and petabyte scale on a cloud provider of your choice. This is a required part of the submission. You do not need to deploy it.

Your design should:

- Name the provider and major services or components you would use.
- Explain how work and anonymization rules are distributed, including how the design handles concurrency, skew, large records, and different file formats.
- Describe retries, recovery, checkpointing or replay, verification, and safe publication.
- Describe security boundaries, sensitive intermediate data, key and secret handling, telemetry, retention, and operational access.
- Define an SLA and state the workload assumptions behind it.
- Include a repository-contained state or flow diagram showing intake, rule distribution or mapping, transformation, verification, publication, and failure/retry or quarantine paths. Its labels must agree with the prose; show durable or trust boundaries where they affect release safety.
- Project capacity and cost for both 1 TB and 1 PB with reproducible arithmetic: workload shape/SLA, region and price date, billing units, storage duration, concurrency/runtime, requests/transfers, discounts or tiers, quotas, and a sensitivity range for dominant uncertainty. Cite the price inputs.
- Explain which parts of your local implementation would carry into production and which parts you would replace. For each material choice, state the triggering limit or retained semantic, the production capability, and the resulting tradeoff or failure mode.

## Submission contents

Return the entire Git repository, including `.git`, as a zip file. Commit your changes and do not remove the baseline history. Include:

- Your implementation, tests, and `Dockerfile`.
- A completed `SUBMISSION.md`.
- All dependency declarations needed for a clean Docker build.

You may use AI coding tools. Briefly disclose what you used and how you checked its output. Do not include credentials, real personal data, generated large datasets, or cloud state in the repository.

Evaluators will look at correctness, scale evidence, reliability, security, operability, and clarity. A cloud deployment receives no extra credit over a design supported by measurements and written assumptions.
