# Submission

## Time spent

The brief sets an eight-hour limit. The recorded work-commit span starts at
2026-09-04 15:09:10 UTC (`d8ad9e4`); the final SQLite/report-write corrections
were committed at 23:40:24 UTC (`5b1f22d`), after the eight-hour elapsed point.
That span includes review waits and presentation work; active engineering time
was not tracked separately. This candidate includes post-timebox corrections
and must not be represented as a verified under-eight-hour completion.

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
subprocess: 26.33 MB @100, 29.99 MB @1000; throughput 8,164.78 and
10,424.11 records/s respectively in the retained presentation run
(`docs/pitch/oai-trial/qa/runtime-evidence.json`). These are small synthetic
workload observations, not bounded-memory or TB-scale guarantees.
Exit 0 only when each run verifies.

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

## Production hardening after the eight-hour trial

The implementation optimizes for a small, auditable correctness boundary rather
than production completeness. The priorities below are deliberate next steps if
this mechanism is promoted beyond the trial, not claims of shipped functionality.
Post-timebox corrections are disclosed above.

### Assurance

**Must be correct now:** literal replacement, identity coherence, format and
protected-value preservation, whole-corpus verification, and report-last release.
SQLite verification includes logical schema/object definitions, column and
foreign-key metadata, and typed per-row values; legal `sqliteX` tables are not
mistaken for reserved `sqlite_` objects. Report writes handle partial progress
and reject zero progress before a readiness marker can be committed.

**Bounded now:** verification independently rereads/re-derives values but shares
replacement primitives. Input is mounted read-only; staging is trusted and
single-writer. Ordinary source mutation is detected, but a hostile host capable
of swapping and restoring bytes is outside this threat model. Local failure is
uncommitted output, not a quarantine service.

**Next:** an implementation-diverse verifier, systematic write/fsync/rename/crash
qualification, and immutable object versions/snapshots. The concurrent `ripgrep`
cross-check is designed, not wired. Successful cleanup and digest-helper tests
are not presented as an exhaustive crash campaign.

### Scale and operations

Local processing uses **per-file materialization**, not bounded-memory TB/PB
streaming. CSV is a strict comma/double-quote dialect: unquoted semicolons, tabs,
and pipes or malformed quoting reject; quote punctuation when it is cell data.
Quoting is normalized logically. SQLite rejects triggers, unsafe rowid shadows,
virtual tables, and `WITHOUT ROWID`; wider support should follow real workloads.
The container runs as root for mounted-write robustness.

**Next:** format-aware bounded-memory processing, distributed checkpoints/replay,
safe observability, quarantine/access/retention workflows, and workload-driven
optimization. Replace assumed object sizes, throughput, retries, list prices and
quotas with measurements before deployment—not a local production platform now.

The cost model includes three stored copies, verifier rereads, staging/promotion
requests, retries, and per-service SQS/EventBridge/KMS/CloudWatch unit prices.
It excludes output expansion, transfer charges, KMS key rental, log retention and
S3 tier/discount modeling. Same-region transfer is assumed free; the worker pool
assumes a raised Fargate vCPU quota. Price citations are dated, but not a billing
quote or demonstrated TB/PB execution.

### Privacy posture

The public deterministic `trial-v1` namespace demonstrates identity coherence,
not private-key secrecy or cross-tenant unlinkability. Phone/IP domains are
bounded and reject exhaustion. Literal replacement does not establish discovery
of unlisted identifiers, quasi-identifier anonymity, or resistance to linkage.

**Next:** tenant/purpose-scoped HMAC keys with rotation/version semantics,
workload-driven discovery, and a separate residual-risk plane. Adaptive red-team
lineage stays development-only; useful findings become small retained regressions.
Issues #12 and #13 remain future work, not prerequisites for this bounded runtime.

### Stopping rule

Reopen the implementation only for a reproducible required-invariant violation,
a missing mandatory brief requirement, or a false evaluator-facing claim. After
the three concrete review defects are closed, qualify the exact container/archive
and stop. Stronger assurance, additional formats and optimizations are documented
priorities, not an open-ended feature backlog for this submission.

## Candidate qualification

The three concrete release fixes are recorded in runtime commit
`5b1f22d` (SQLite inventory/schema and partial report writes). The reproducible
qualification command is:

```bash
uv run --extra dev python scripts/qualify_submission.py --output "$QUALIFICATION_OUTPUT"
```

Use a new directory on the artifact volume. The procedure clones the pushed
candidate, preserves baseline history, runs full pytest/Ruff, performs a clean
Docker build and the exact evaluator commands, independently reads all four
formats and report digests, tests early/late refusal, and compares an offline
replay. It verifies every packaged file, including `.git`, against that checkout.

`QUALIFICATION.json` beside the resulting ZIP records the exact qualified
checkout SHA, image ID, commands, exit codes and artifact hashes. Keeping that
receipt outside the immutable ZIP avoids a self-referential commit/hash loop.
A script or a passing unit suite is not qualification: require that receipt's
PASS and read back its archive hash. Presentation QA remains a separate weekend
activity, not a technical-runtime release prerequisite.

## Operator-requested post-trial integration

The shared `anonymize-data` skill is a thin wrapper around this project; it adds
no duplicate engine or host-service dependency. The `anonymize` command accepts
a supported file/folder plus a separate policy and empty output directory.

Optional RapidFuzz discovery now proposes whole-field/whole-line name aliases.
It never replaces data automatically. Explicit candidate-ID approval recomputes
source-bound proposals and emits a validated exact-match policy; the normal
pipeline still owns release. Defaults are threshold 90 and identity separation
margin 5, with tie refusal, protected-value checks, strict bounds and private
work artifacts. See `docs/DISCOVERY.md` and `fixtures/discovery_eval.json`.

These extensions were explicitly requested after the qualified `9ebb447`
candidate. That earlier archive and reviewer PASS are preserved, not relabeled
as proof of these additions. The default Docker image retains the exact engine;
`INCLUDE_DISCOVERY=1` includes the pinned optional RapidFuzz dependency.

## Python conventions (deliberate overrides)
The repo follows universal Python best practices (centralized `StrEnum` error
codes, no runtime `assert`, no `shell=True`/`eval`/`exec`/`pickle`, `pathlib`,
module docstrings, files < 800 lines, thin `__init__`, no `sys.path` surgery,
regex removed from the value path). The house Loguru/Typer/httpx defaults are
intentionally **overridden**: the exact engine is stdlib-only (`argparse` + `print`,
`dependencies = []`). Optional discovery adds RapidFuzz only. Self-contained
Docker does not forbid dependencies; the small default dependency set is an
implementation choice, not a requirement invented from the brief.

## AI tool disclosure

Built with an AI coding assistant. Output was checked by a deterministic gate on
every change: the full pytest gate (`uv run pytest -q`) and `ruff check`, plus live
`docker build` and both `docker run` commands read back from produced artifacts.
