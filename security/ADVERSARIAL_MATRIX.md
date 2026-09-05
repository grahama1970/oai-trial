# Adversarial evidence and boundaries

The current case-level inventory and grouped results are generated in
[`reports/adversarial-coverage/report.html`](reports/adversarial-coverage/report.html)
([Markdown](reports/adversarial-coverage/report.md),
[CSV matrix](reports/adversarial-coverage/family-matrix.csv),
[exact cases](reports/adversarial-coverage/inventory.json)). They separate attacks,
positive controls, boundary probes, and metadata checks. Counts are not adequacy.

Earlier review findings remain historical evidence in
[`docs/research/webgpt/`](../docs/research/webgpt/). This page is not a scorecard
claiming that every historical finding established production assurance.

| Family | Retained checks | What the checks do not establish |
|---|---|---|
| Policy and matching | `tests/test_adversarial_matrix.py`, `tests/test_round2_fixes.py`, `tests/test_round3_fixes.py`, `tests/test_round4_fixes.py`; core matcher tests | Every rejection path exercised through the final Docker image |
| CSV and JSON fidelity | `tests/test_csv_dialect.py`, `tests/test_verifier_location.py`, `tests/test_typed_scalar_verification.py` | Exhaustive dialect support, Unicode discovery, or all structural mutations |
| SQLite rows and logical schema | `tests/test_sqlite_location.py`, `tests/test_sqlite_schema_literals.py`, `tests/test_release_review_regressions.py` | Wider unsupported SQLite features or physical-page equivalence |
| Publication | Short- and zero-progress write injection in `tests/test_release_review_regressions.py`; normal report/artifact checks in `tests/test_publish_hardening.py` | A systematic fsync/rename/SIGKILL/power-loss campaign; normal cleanup is not crash recovery proof |
| Source lineage | `tests/test_source_snapshot.py` compares digest-helper output after content mutation with restored mtime | Pipeline-level TOCTOU refusal or a hostile host that swaps and restores bytes |
| Filesystem and diagnostics | `tests/test_pipeline_failclosed.py`, `tests/test_blackbox_contract.py`, `tests/test_error_privacy.py` | Every special-file type, diagnostic sink, or external writer race |
| Pseudonym capacity | `tests/test_pseudonym_domains.py` checks IPv4 at/over capacity; compiler bounds phone/IP search | Private-key secrecy, cross-tenant unlinkability, or every collision sequence |
| Metadata and public claims | `tests/test_claim_surface.py` and report-field checks | Runtime security, full schema validation, or actual cloud pricing correctness |
| Optional residual risk | `tests/test_residual_risk.py` | Required release adequacy or universal non-reidentifiability; issue #12 stays future work |

## Latest concrete review defects

The supplied regression file exposed three required-contract defects: a legal
`sqliteX` table omitted by a LIKE wildcard; schema mutation missed by row-only
verification; and truncated readiness JSON after a short write. The fixes use a
literal reserved-prefix filter, logical-schema/column/FK comparisons plus schema
literal scanning, and a write-all loop with no-progress refusal. See
`tests/test_release_review_regressions.py` and the report's linked before/after
receipts; do not relabel the reviewed pre-fix commit as having passed these checks.

## Stopping rule

Fix concrete required-contract violations, missing mandatory requirements, or
false public claims. Qualify the actual container/archive. Keep implementation-
diverse verification, stronger crash/isolation campaigns, large-object processing,
key management and adaptive red-teaming under the production-hardening boundary
in `SUBMISSION.md`, not as an open-ended local feature backlog.
