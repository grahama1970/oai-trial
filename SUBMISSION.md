# Submission

## Time spent

Development was assistant-driven across a single working session (well under the
eight-hour cap). See `git log` for the per-issue commit trail (#2 → #9 plus this
production design).

## Implemented scope

A fail-closed, deterministic cross-format anonymization pipeline.

- **Matcher** (`matcher.py`, `policy.py`, `pseudonyms.py`, `errors.py`): strict
  policy compile; Aho-Corasick exact matching (case-sensitive over original,
  case-insensitive over an ASCII-lowered view); leftmost-longest with stable
  `rule_id` tie-break; matches only original input, never rescans replacements
  (no cascade); deterministic per-type-distinct, collision-safe pseudonyms.
- **Adapters** (`formats.py`): CSV and TXT stream with strict UTF-8 + BOM
  preservation and header/schema rejection; JSON rejects duplicate keys, NaN/Inf,
  sensitive keys, and enforces depth/size bounds; SQLite uses the online backup
  API, skips generated columns via `table_xinfo`, and verifies
  `integrity_check` + `foreign_key_check` + row counts, rejecting virtual and
  `WITHOUT ROWID` tables.
- **Pipeline** (`pipeline.py`): preflight trust boundaries (distinct roots,
  reject symlinks/special files, reject sensitive literals in paths) → staged
  build → independent verification (`verification.py`) → atomic publish →
  `report.json` written last as the sole readiness marker.
- **Container** (`Dockerfile`): self-contained `python:3.12-slim`; both required
  `docker run` commands work; demo measures per-run peak memory at two sizes.

Intentionally bounded / rejected safely: non-ASCII case-insensitive literals,
protected/sensitive overlap, malformed encodings, sensitive schema identifiers,
JSON duplicate keys / NaN / over-depth, SQLite virtual and `WITHOUT ROWID`
tables. Each returns non-zero with no ready release.

## Pipeline boundary and key decisions

Input boundary is the mounted `policy.json` (literal matching). Semantics are
frozen in [`docs/ANONYMIZATION_SEMANTICS.md`](docs/ANONYMIZATION_SEMANTICS.md)
and mapped to tests in [`docs/ACCEPTANCE_MATRIX.md`](docs/ACCEPTANCE_MATRIX.md).
Notable decisions: **reject** (not silently resolve) protected/sensitive
overlap; **no Unicode normalization** in the matcher (homoglyph folding is a
reject-only verifier signal only); schema-bearing names are protected;
report-last readiness.

## Demo hardware and benchmark results

Local x86-64 Linux, in-container. `docker run --rm anonymization-trial` at sizes
100 and 1000 (10×), all four formats, per-run peak memory measured in a
subprocess: ~26 MB @100, ~29 MB @1000 (bounded, roughly flat across 10×);
throughput ~16k–23k records/s. Exit 0 only when each run verifies.

## Production cloud design

AWS design, diagram, SLA, and reproducible cost model in
[`docs/production-architecture.md`](docs/production-architecture.md) and
[`docs/production-architecture.svg`](docs/production-architecture.svg).

## Portability (portable compute artifact, provider-specific orchestration)
The anonymization engine is a self-contained OCI container, so the portability
boundary is the image + data contract + verification semantics, not a Terraform
config. A provider-neutral deployment contract
([`infra/deployment-contract.yaml`](infra/deployment-contract.yaml)) lists the
capabilities the cloud must supply; the AWS/GCP/Azure service mapping is in
[`infra/mappings/PROVIDER_MAPPING.md`](infra/mappings/PROVIDER_MAPPING.md). AWS
is the one worked reference. `infra/terraform/` is a read-only AWS reference
module: `terraform fmt` + `validate` pass and `$ops-terraform check` returns
`status=PASS` ([`infra/ops-terraform-check.receipt.json`](infra/ops-terraform-check.receipt.json));
no state is committed and no `apply` is run (deployment earns no extra credit).

## SLA, capacity, and cost

1 TB ≈ $52, 1 PB ≈ $51,836 (us-east-1 list prices, price_date 2026-09-04,
storage-dominant). Reproduce: `python scripts/estimate_aws_cost.py --inputs
costs/aws-us-east-1-inputs.json`. Prices are **list prices not yet confirmed
against a dated screenshot** — illustrative until verified.

## Local-to-production rationale

See the mapping table in `docs/production-architecture.md`. Retained semantics:
deterministic identity-coherent pseudonyms, fail-closed release, independent
verification, no mapping/keys in output or logs.

## Privacy, security, and operational safety

No replacement mapping is persisted (a mapping table is itself reversible PII).
Errors are a closed, privacy-safe vocabulary (`errors.py`) that never echo raw
values. Raw inputs, mappings, and quarantine never enter the release dir or
logs. The verifier rereads output from disk and does not trust transform
booleans.

## Known gaps and next steps

- Cloud prices are list-price, unverified against a dated source.
- Container runs as root for mounted-write robustness; non-root variant is
  documented in the Dockerfile.
- Discovery beyond policy literals (RapidFuzz aliases / deterministic classifier)
  is designed but not built (opt-in, extra credit).
- The `ripgrep` concurrent verification cross-check is designed, not yet wired.

## AI tool disclosure

Built with an AI coding assistant. Output was checked by a deterministic gate on
every change: `uv run pytest -q` (35 tests) and `ruff check`, plus live
`docker build` and both `docker run` commands read back from produced artifacts.
