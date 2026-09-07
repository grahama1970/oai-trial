# Production cloud design (AWS)

Diagram: [`production-architecture.svg`](production-architecture.svg). Labels
below match the diagram. Cost math: [`../costs/`](../costs) +
[`../scripts/estimate_aws_cost.py`](../scripts/estimate_aws_cost.py).

This is a proposed architecture, not a deployed or TB/PB-qualified runtime. Its
partitioners, allocation-plan distribution, cross-check and access controls are
design requirements, not capabilities established by the local demonstration.

## Flow (matches the diagram)
- **Intake** — producers land exports in a KMS-encrypted S3 bucket, mounted
  read-only to workers. An S3 event fans out through EventBridge → SQS.
- **Distribute** — one SQS message per file (at-least-once). Large single files
  are split with FORMAT-AWARE partition semantics (below); concurrency is
  bounded by the worker pool size, not the queue depth.
- **Transform** — workers receive the same versioned policy and identity-allocation
  plan, or the complete identical identity set required to regenerate that plan,
  plus protected key material. Per-record transformation remains local; collision
  allocation is not recomputed independently from arbitrary worker subsets.
  Format-aware workers write to per-file staging prefixes.
- **Verify** — a separate stage reruns the runtime verifier over staged output.
  It performs fresh rereads but shares matcher/allocation primitives. A proposed
  concurrent `ripgrep -Ff` scan adds an implementation-diverse literal-absence
  cross-check; it does not make the whole verifier implementation-diverse.
- **Release** — after ALL files verify, an immutable corpus manifest (every
  object key + content hash) is written and a single active-corpus pointer is
  conditionally switched to it. Consumers must resolve that pointer, and IAM
  must prevent direct enumeration/access to candidate release prefixes. S3 does
  not make pre-publication copies invisible automatically.
- **Quarantine** — any file that fails preflight, transform, or verification
  goes to a quarantine bucket, is never promoted, and raises a `needs_human`
  alert. Retry equivalence requires the same source snapshot, policy version
  and identity-allocation plan.

## Distribution, concurrency, skew, formats
Work is partitioned per file; format is dispatched by suffix. Skew from large
files is handled with format-specific partition semantics, because naive
line-aligned byte splitting corrupts valid data (a quoted CSV record may span
lines; a UTF-8 code point may span a byte boundary):
- **Text** — byte ranges with UTF-8-safe boundaries plus an overlap window of
  the maximum sensitive-literal length; the left partition owns matches in the
  overlap.
- **CSV** — partition on parser-confirmed RECORD boundaries (a scanner walks
  quote state to the next true record start), never on raw newlines.
- **JSON** — documents are processed whole (bounded by depth/size limits);
  record-framed JSONL may be split on record boundaries.
- **SQLite** — snapshotted and processed whole on a memory-sized worker.
Concurrency is a bounded worker pool with SQS backpressure.

## Reliability
At-least-once SQS delivery requires explicit attempt handling. Retries are
idempotent for the same source snapshot, policy version and identity-allocation
plan, not merely because pseudonym derivation is deterministic. Checkpointing is per-file: a file is either in staging (in-flight),
promoted (done), or quarantined (failed). Recovery replays only unfinished SQS
messages. Publication is fail-closed: no partial corpus is ever promoted.

## Security
KMS-encrypted intake/work/release/quarantine buckets; keys in KMS, never in the
image or logs. No raw value-to-pseudonym mapping belongs in releases or logs.
A protected, versioned allocation plan or its complete identity-set input is
required; its exact production representation remains design work.
Intermediate/staging data is short-TTL and separate from release. Telemetry
(CloudWatch: records/s, bytes/s, failures) carries no sensitive values.
Operational access is least-privilege IAM per stage.

## SLA (stated assumptions, arithmetic shown)
Assume avg file ~1 MiB, mixed formats, batch arrival, 200 concurrent 1-vCPU
workers at ~20 MB/s each → ~4 GB/s aggregate ideal.
- **1 TB**: ideal transform ≈ 250 s (~4.2 min); with the verify re-read (~2x
  IO), queueing, stragglers, and retries, target **verified-published ≤ 1
  hour** — overhead-dominated, not throughput-dominated.
- **1 PB**: ideal transform ≈ 250,000 s (~2.9 days) at the same pool; target
  **≤ 7 days**, or scale the pool (2,000 workers → ideal ≈ 7 h, target ≤ 1 day).
  Throughput scales linearly until S3 request rates / account quotas bind.
Fail-closed guarantee unchanged: nothing unverified is ever released.

## Cost (reproducible)
Run: `python scripts/estimate_aws_cost.py --inputs costs/aws-us-east-1-inputs.json`.
With the committed us-east-1 list-price inputs (price_date 2026-09-04):
- **1 TB ≈ $86** (storage-dominant), **1 PB ≈ $85,734** (storage-dominant), including staging storage, verify rereads, promote requests, a 2% retry fraction, and explicit per-object SQS/EventBridge/KMS/CloudWatch line items. Transfer, tier, and quota assumptions are stated in the committed inputs file.
- Sensitivity: halving throughput barely moves total (storage-bound); a 10×
  smaller avg file size raises the request term sharply — see
  `costs/example-estimates.json`.
- Prices are **list prices, not yet confirmed against a dated screenshot** —
  treat as illustrative until verified.

## Local-to-production mapping
| Local (this repo) | Production | Trigger to replace |
|---|---|---|
| single-process pipeline | Fargate worker pool + SQS | throughput/scale |
| `tempfile` staging + `os.replace` | S3 staging prefix → copy to release | distributed publish |
| `verification.py` in-process | same code per worker + `rg` cross-check | scale/independence |
| public deterministic pseudonyms | scoped keys plus shared allocation plan | key management and coordinated allocation |
| fixture generator | real producer intake | data source |

Intended retained semantics: policy-declared identity coherence, fail-closed
release, fresh verification with explicit shared-code limits, and no raw mappings
or keys in output or logs. Deployment must validate these properties.
