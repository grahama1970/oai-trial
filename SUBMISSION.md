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
- **Adapters** (`formats.py`): CSV rows are iterated and TXT processed per file
  (content materialized in memory, not TB-scale streaming) with strict UTF-8 + BOM
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

1 TB ≈ $86, 1 PB ≈ $85,734 (us-east-1 list prices, price_date 2026-09-04,
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

- **SQLite is verified relationally AND per-row.** Row counts, `integrity_check`,
  and `foreign_key_check` are preserved, plus a per-row location oracle (by
  rowid: text cells vs the independent recompute, non-text cells byte-identical)
  and a schema-object literal scan. Constructs the verifier cannot reproduce are
  rejected fail closed (triggers, `rowid`-shadowing columns, virtual tables,
  `WITHOUT ROWID`).
- **The verifier is an independent re-derivation, not a separate implementation.**
  It rereads output from disk and recomputes expected results, but shares the
  `replace_text`/`build_replacements` primitive with the transform; a fully
  independent second matcher would be stronger assurance.
- **verify -> publish assumes a trusted single-writer staging filesystem.** The
  verified digest is re-checked immediately before the atomic promote, closing
  the in-process window; concurrent external mutation of staging by another
  writer is out of the assumed threat model.
- **Source is assumed mounted read-only.** A source-snapshot/TOCTOU gate rejects
  content that changes during a run; deeper host-side swap-and-restore is outside
  the mounted-read-only container threat model.
- **Not streaming/bounded-memory.** Per-file content is materialized in memory;
  TB/PB is designed and cost-modelled, not run at scale.
- **CSV uses a strict comma/double-quote dialect.** Unquoted semicolons, tabs,
  and pipes are rejected throughout the file, even in data rows; quote those
  characters when they are cell content. Malformed quoting is rejected.
  Quoting is normalized (logical preservation, not byte-level).
- **Single fixed pseudonym scope.** Local trial pseudonyms use the public fixed
  scope trial-v1; they provide no private-key secrecy or cross-tenant
  unlinkability. Production replaces this public namespace with a
  tenant-or-purpose-scoped keyed HMAC. IP/phone domains are bounded with a
  cardinality preflight that rejects over-capacity policies up front.
- The cost model includes storage (intake+staging+release), verify rereads,
  staging/promotion requests, a retry fraction, a 2x verify compute pass, and a
  per-service SQS/EventBridge/KMS/CloudWatch quantity-times-unit-price estimate.
  Dated price-source references are in the inputs JSON. It still omits output
  expansion, transfer charges, KMS key rental, log retention, and S3 tier/discount
  modeling. Same-region transfer is assumed free; prices use the first Standard
  tier. The worker pool assumes a raised Fargate vCPU quota, not default quotas.
- Cloud prices are list-price, unverified against a dated source.
- Container runs as root for mounted-write robustness; non-root variant is
  documented in the Dockerfile.
- Discovery beyond policy literals (RapidFuzz aliases / deterministic classifier)
  is designed but not built (opt-in, extra credit).
- The `ripgrep` concurrent verification cross-check is designed, not yet wired.

## Python conventions (deliberate overrides)
The repo follows universal Python best practices (centralized `StrEnum` error
codes, no runtime `assert`, no `shell=True`/`eval`/`exec`/`pickle`, `pathlib`,
module docstrings, files < 800 lines, thin `__init__`, no `sys.path` surgery,
regex removed from the value path). The house Loguru/Typer/httpx defaults are
intentionally **overridden**: the runtime is stdlib-only (`argparse` + `print`,
`dependencies = []`) so the container stays self-contained, offline, and
minimal — adding those dependencies would violate the trial's container contract.

## AI tool disclosure

Built with an AI coding assistant. Output was checked by a deterministic gate on
every change: the full pytest gate (`uv run pytest -q`) and `ruff check`, plus live
`docker build` and both `docker run` commands read back from produced artifacts.
