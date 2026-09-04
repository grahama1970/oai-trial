# Production cloud design (AWS)

Diagram: [`production-architecture.svg`](production-architecture.svg). Labels
below match the diagram. Cost math: [`../costs/`](../costs) +
[`../scripts/estimate_aws_cost.py`](../scripts/estimate_aws_cost.py).

## Flow (matches the diagram)
- **Intake** — producers land exports in a KMS-encrypted S3 bucket, mounted
  read-only to workers. An S3 event fans out through EventBridge → SQS.
- **Distribute** — one SQS message per file (at-least-once). Large single files
  are split into line-aligned byte ranges to handle skew; concurrency is bounded
  by the worker pool size, not the queue depth.
- **Transform** — horizontally scaled Fargate/Batch workers pull the policy +
  key material once (Secrets Manager/KMS) and derive deterministic pseudonyms
  locally, so there is no shared-state hotspot. Each worker streams rows and
  writes to a per-file staging prefix.
- **Verify** — the independent verifier (this repo's `verification.py`, plus a
  concurrent `ripgrep -Ff` literal cross-check) reruns over staged output.
- **Release** — verified output is promoted (S3 copy) into the release bucket.
  Readers only ever see verified objects.
- **Quarantine** — any file that fails preflight, transform, or verification
  goes to a quarantine bucket, is never promoted, and raises a `needs_human`
  alert. Retries are idempotent (deterministic pseudonyms → same output).

## Distribution, concurrency, skew, formats
Work is partitioned per file; format is dispatched by suffix. Skew from large
files is handled by byte-range splitting (text/CSV line-aligned; SQLite is
snapshotted and processed whole on a sized worker). Concurrency is a bounded
worker pool with SQS backpressure.

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

## SLA (stated assumptions)
Assume avg file ~1 MiB, mixed formats, batch arrival. Target: **1 TB
verified-published within ~2 hours at 200 concurrent 1-vCPU workers** (≈20 MB/s
each → ~1.4 h transform + overhead), fail-closed guarantee that nothing
unverified is ever released. Adjust worker count linearly for tighter SLAs.

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
