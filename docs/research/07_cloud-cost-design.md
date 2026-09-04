# Cloud cost + capacity design (1 TB / 1 PB)

## Requirement (brief)
Name provider + services; distribute work/rules; handle concurrency, skew, large
records, formats; retries/recovery/checkpointing; verification; safe publication;
security boundaries, key handling, telemetry, retention, access; define an SLA;
project 1 TB and 1 PB cost with **reproducible arithmetic** (workload/SLA, region,
price date, billing units, storage duration, concurrency/runtime, requests/
transfers, discounts/tiers, quotas, sensitivity range) with cited price inputs.

## Sources (prices NOT yet pinned — must cite dated page in SUBMISSION)
- AWS S3 pricing (authoritative): https://aws.amazon.com/s3/pricing/
- CloudZero — S3 pricing 2026 guide: https://www.cloudzero.com/blog/s3-pricing/
- Cloudchipr — S3 pricing explained 2026: https://cloudchipr.com/blog/amazon-s3-pricing-explained
- Filebase — S3 pricing 2026: https://filebase.com/blog/aws-s3-pricing-in-2026-what-youll-actually-pay/

## Proposed reference architecture (AWS, map to infra/terraform boundaries)
- **intake** (S3, `:ro` to workers) → raw customer exports.
- **rule distribution**: `policy.json` + key material in Secrets Manager/KMS;
  workers pull policy once, derive deterministic pseudonyms locally (no shared
  state → no hotspot).
- **work queue**: SQS (one message per file/partition) for at-least-once dispatch;
  large single files split by line-aligned byte ranges to handle skew.
- **transform**: horizontally scaled workers (Fargate/Batch/Lambda by file size);
  stream rows, bounded memory (file 04).
- **verify**: per-file verification in the worker + a corpus-level gate before
  publish (file 05).
- **release** (S3): atomic publish — write to a staging prefix, verify, then
  copy/rename into the release bucket; readers only see verified objects.
- **quarantine** (S3): malformed/failed files; never published, never logged raw.
- **telemetry**: CloudWatch metrics (records/s, bytes/s, failures); no sensitive
  values in logs.

## Cost arithmetic skeleton (fill with dated prices in SUBMISSION)
Let `P_store` = $/GB-month (S3 Standard), `P_get`/`P_put` = $/1k requests,
`P_compute` = $/vCPU-hour, `T` = throughput (bytes/s/worker, measured in demo).

- Storage: `bytes × P_store × months` (intake + release + short-lived work).
- Requests: `num_objects × (P_get + P_put)/1000`.
- Compute: `total_bytes / (T × workers) → worker-hours × P_compute`.
- 1 TB vs 1 PB: same formula, 1000× bytes/objects; dominant term flips from
  compute (1 TB) toward storage+requests (1 PB) — show the crossover.
- Sensitivity: vary `T` (measured range from demo) and object-size distribution
  (many small files inflate request cost); give a ±band.

## SLA sketch
State workload assumptions (avg file size, format mix, arrival rate), then a
per-batch completion target (e.g. "1 TB verified-published within N hours at C
concurrent workers"), and the fail-closed guarantee (never publish unverified).

## Proof boundary
No prices pinned here. Before using in SUBMISSION, pull current numbers from the
AWS S3 pricing page for a named region on a stated date and cite them.
