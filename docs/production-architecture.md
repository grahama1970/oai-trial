# Production cloud design (AWS)

Diagram: [`production-architecture.svg`](production-architecture.svg). Labels
below match the diagram. Cost math: [`../costs/`](../costs) +
[`../scripts/estimate_aws_cost.py`](../scripts/estimate_aws_cost.py).

## Flow (matches the diagram)
- **Intake** — producers land exports in a KMS-encrypted S3 bucket, mounted
  read-only to workers. An S3 event fans out through EventBridge → SQS.
- **Distribute** — one SQS message per file (at-least-once). Large single files
  are split with FORMAT-AWARE partition semantics (below); concurrency is
  bounded by the worker pool size, not the queue depth.
- **Transform** — horizontally scaled Fargate/Batch workers pull the policy +
  key material once (Secrets Manager/KMS) and derive deterministic pseudonyms
  locally, so there is no shared-state hotspot. Each worker streams rows and
  writes to a per-file staging prefix.
- **Verify** — the independent verifier (this repo's `verification.py`, plus a
  concurrent `ripgrep -Ff` literal cross-check) reruns over staged output.
- **Release** — after ALL files verify, an immutable corpus manifest (every
  object key + content hash) is written and a single active-corpus pointer is
  atomically switched to it. Readers resolve the pointer, so a partially
  promoted corpus is never observable; individual object copies before the
  pointer switch are invisible to consumers.
- **Quarantine** — any file that fails preflight, transform, or verification
  goes to a quarantine bucket, is never promoted, and raises a `needs_human`
  alert. Retries are idempotent (deterministic pseudonyms → same output).

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
At-least-once SQS delivery + idempotent deterministic transforms make retries
safe. Checkpointing is per-file: a file is either in staging (in-flight),
promoted (done), or quarantined (failed). Recovery replays only unfinished SQS
messages. Publication is fail-closed: no partial corpus is ever promoted.

## Security
KMS-encrypted intake/work/release/quarantine buckets; keys in KMS, never in the
image or logs. No replacement mapping is persisted (deterministic keyed hash).
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
- **1 TB ≈ $52** (storage-dominant), **1 PB ≈ $51,836** (storage-dominant).
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
| stdlib deterministic pseudonyms | same, key from KMS | key management |
| fixture generator | real producer intake | data source |

Retained semantics: deterministic identity-coherent pseudonyms, fail-closed
release, independent verification, no mapping/keys in output or logs.
