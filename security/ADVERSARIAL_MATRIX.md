# Adversarial coverage matrix

Source: WebGPT adversarial peer review, 2026-09-04 (verdict FAIL, 21 issues, 14
rationale gaps). Full review: `../docs/research/webgpt/ADVERSARIAL_REVIEW_2026-09-04.md`.

**Status legend**
- `FIXED` — corrected, with a retained green regression test.
- `CREDIBLE` — consistent with the code on read; needs a pipeline-level red test.
- `BUNDLE-ARTIFACT` — an artifact of the 4-file review zip, not a repo defect
  (the repo contains tests, Dockerfile, `.git`, and all receipts).
- `DOC-FIXED` — corrected in this pass.
- `DESIGNED / NON-CLAIM` — an explicit, already-disclosed scope boundary.

## Round 2 (2026-09-04): reviewer CONFIRMED_FIXED #1(CSV)/#2/#3/#9/#16/report-atomicity; new fixes landed for round-2 #3 (verifier duplicate-key JSON), round-2 #6 (lossy float rejected), and #8 (boundary overlap). Still open: SQLite location-binding (#14), verify->seal race (#4 residual), TOCTOU depth (#7), cost/SLA rigor (#10), full verifier independence, and non-claim sharpening (#11/#12/#17/#18). See docs/research/webgpt/ADVERSARIAL_REVIEW_ROUND2_2026-09-04.md.

## Correctness & fail-closed (the load-bearing findings)

| # | Sev | Attack / defect | Target | Status | Test | Ticket |
|---|-----|-----------------|--------|--------|------|--------|
| 1 | high | Verifier admitted swapped pseudonyms, dropped rows, relocated protected values | `verification.py::_verify_locations` | FIXED for text/CSV/JSON (per-location recompute); SQLite is relational-only (fail-closed on unreproducible constructs) | `test_verifier_location.py` (green) | done |
| 2 | high | `"\u0041lice"` JSON-escape bypassed the verifier (scanned serialized text) | `formats.py::iter_searchable_text`, `verification.py` | FIXED (decode keys+values; dup-key + BOM handling) | `test_verifier_location.py`, `test_round2_fixes.py`, `test_round3_fixes.py` (green) | done |
| 3 | high | `{"n":1e400}` becomes `{"n": Infinity}` published as ready | `formats.py::_transform_json` | FIXED (parse_float rejects non-finite; allow_nan=False) | `test_non_finite_json_number_is_rejected` (green) | done |
| 4 | high | Staging mutable between verify and publish | `pipeline.py::run_pipeline,_publish` | MITIGATED (sealed digest re-checked before swap; single-writer staging assumption disclosed) | `test_publish_hardening.py` (green) | done |
| 5 | high | Publish not atomic/crash-durable | `pipeline.py::_publish` | FIXED (readiness invalidated first; temp+fsync+os.replace+dir fsync) | `test_publish_hardening.py` (green) | done |
| 6 | high | `.staging-*` inside the output mount; survives SIGKILL | `pipeline.py::run_pipeline` | FIXED (mode 0700 + stale-stage cleanup at startup) | `test_publish_hardening.py::test_no_staging_left_in_output` (green) | done |
| 7 | high | TOCTOU: policy/source reread windows | `pipeline.py` | MITIGATED (policy symlink rejected before read; source-digest gate; deeper host swap-and-restore disclosed) | `test_round4_fixes.py`, `test_source_snapshot.py` (green) | done |
| 8 | high | Protected/sensitive partial (prefix/suffix) overlap accepted; only equality/containment checked | `policy.py::_check_overlap` | FIXED (boundary-overlap check) | `test_round2_fixes.py::test_partial_boundary_overlap_rejected` (green) | done |
| 9 | high | Two case-insensitive rules (`Alice`/`ALICE`) for distinct subjects accepted; one wins by `rule_id` | `policy.py::compile_policy`, `matcher.py::_select` | FIXED (match-domain conflict detection) | `test_case_insensitive_conflicting_identities_rejected` (green) | done |
| 14 | high | SQLite rowid shadowing / trigger mutation / schema literals | `formats.py`, `verification.py` | FIXED (triggers + rowid-shadow + schema-literal rejection; per-row location oracle) | `test_round3_fixes.py`, `test_sqlite_location.py`, `test_sqlite_schema_literals.py` (green) | done |
| 15 | high | `report.json` binds no evidence chain | `pipeline.py::RunReport` | FIXED (report_schema/run_id/source_manifest_sha256/verification_sha256 bound) | `test_publish_hardening.py` (green) | done |
| 16 | med | Non-strict policy validation: `version:true`==1, duplicate keys last-wins (missing arrays still default empty) | `policy.py::compile_policy,load_policy` | FIXED (bool rejected; dup-key hook) | `test_version_true_is_rejected`, `test_duplicate_policy_keys_rejected` (green) | done |
| 17 | med | Attacker-controlled identifiers/filenames in error messages | `errors.py::safe_ref` | FIXED (rule_id/data_type/path material routed through safe_ref) | `test_error_privacy.py`, `test_sqlite_schema_literals.py` (green) | done |

## Scale, cost, robustness

| # | Sev | Finding | Status |
|---|-----|---------|--------|
| 10 | med | Pseudonym domains small (IPv4 253, phone 1e4); "extension" claimed not implemented; up to 1e5 hash attempts (DoS) | CREDIBLE - cardinality preflight + cap needed |
| 11 | med | `SCOPE_ID` globally fixed `trial-v1`; same subject means same token across tenants despite `across_tenants:false` | CREDIBLE - scope must be a run input, or drop the claim |
| 12 | high | Not bounded-memory/streaming (`read_bytes`, `fetchall`, whole-corpus searchable text) | DESIGNED / NON-CLAIM - TB/PB is explicitly designed, not run; tighten the non-claim |
| 13 | med | CSV newline/quoting normalized; "preserve CSV" undefined (byte vs logical) | CREDIBLE - define + verify dialect |
| 18 | med | Non-claims inconsistent: local build is a public unkeyed SHA-256 namespace, not keyed HMAC; "proven" overclaims | CREDIBLE - sharpen `docs/PRIVACY_CONTRACT.md` |

## Evidence-package findings (artifacts of the 4-file review zip)

| # | Finding | Status |
|---|---------|--------|
| 19 | Zip had only 4 md; README said 62 tests while SUBMISSION said 35 | BUNDLE-ARTIFACT for the missing files; DOC-FIXED for the 62-vs-35 drift |
| 20 | Cost/SLA "not reviewable" - referenced cost files absent from zip | BUNDLE-ARTIFACT (files exist: `scripts/estimate_aws_cost.py`, `costs/`); substantive line-item detail is a real hardening item |
| 21 | "Security theater" - no receipts in zip | BUNDLE-ARTIFACT (receipts exist: `security/battle/`, `security/hack-audit.receipt.json`); the missed counterexamples above are the real gap this matrix closes |

## Rationale gaps to docstring targets

The review's 14 RATIONALE_GAPS name functions where Graham's design reasoning
should be explicit in the docstring rather than implied. Tracked for a docstring
pass: `compile_policy`, `_check_overlap`, `matcher._select`, `_Aho.scan`,
`build_replacements`, `_transform_csv`, `_transform_json`, `_transform_sqlite`,
`run_pipeline`, `_publish`, `verify_corpus`, `_verify_subject_level`,
`AnonError`, `RunReport`.
