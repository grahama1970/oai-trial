# Adversarial coverage matrix

Source: WebGPT adversarial peer review, 2026-09-04 (verdict FAIL, 21 issues, 14
rationale gaps). Full review: `../docs/research/webgpt/ADVERSARIAL_REVIEW_2026-09-04.md`.

**Status legend**
- `VERIFIED` — defect reproduced against the real code by a retained red test in
  `security/tests/test_adversarial_matrix.py` (currently `xfail(strict)`).
- `CREDIBLE` — consistent with the code on read; needs a pipeline-level red test.
- `BUNDLE-ARTIFACT` — an artifact of the 4-file review zip, not a repo defect
  (the repo contains tests, Dockerfile, `.git`, and all receipts).
- `DOC-FIXED` — corrected in this pass.
- `DESIGNED / NON-CLAIM` — an explicit, already-disclosed scope boundary.

## Correctness & fail-closed (the load-bearing findings)

| # | Sev | Attack / defect | Target | Status | Test | Ticket |
|---|-----|-----------------|--------|--------|------|--------|
| 1 | high | Verifier admits swapped pseudonyms, dropped rows, relocated protected values (subject/global, not location-bound) | `verification.py::verify_corpus,_verify_subject_level` | CREDIBLE | pipeline red test pending | pending |
| 2 | high | `"\u0041lice"` JSON-escape bypasses the verifier (scans serialized text, not decoded values) | `formats.py::iter_searchable_text`, `verification.py` | CREDIBLE | pipeline red test pending | pending |
| 3 | high | `{"n":1e400}` becomes `{"n": Infinity}` published as ready | `formats.py::_transform_json` | FIXED (parse_float rejects non-finite; allow_nan=False) | `test_non_finite_json_number_is_rejected` (green) | done |
| 4 | high | Staging mutable between `verify_corpus` and `_manifest_digest`; published bytes are not the verified bytes | `pipeline.py::run_pipeline` | CREDIBLE | pipeline red test pending | pending |
| 5 | high | Publish not atomic/crash-durable (delete-old then rename then `write_text`, no fsync/rollback) | `pipeline.py::_publish` | CREDIBLE | crash-injection test pending | pending |
| 6 | high | `.staging-*` inside the output mount; host-readable; survives SIGKILL, no startup recovery | `pipeline.py::run_pipeline` | CREDIBLE | test pending | pending |
| 7 | high | TOCTOU: policy/source reread and re-hashed at different times; swap-and-restore window | `pipeline.py::_preflight,_source_digests`, `formats.py::_snapshot_sqlite` | CREDIBLE | extends `test_source_snapshot.py` | pending |
| 8 | high | Protected/sensitive partial (prefix/suffix) overlap accepted; only equality/containment checked | `policy.py::_check_overlap` | OPEN (compile accepts; next slice) | pipeline violation test pending | pending |
| 9 | high | Two case-insensitive rules (`Alice`/`ALICE`) for distinct subjects accepted; one wins by `rule_id` | `policy.py::compile_policy`, `matcher.py::_select` | FIXED (match-domain conflict detection) | `test_case_insensitive_conflicting_identities_rejected` (green) | done |
| 14 | high | SQLite bare `rowid` can shadow a declared column; triggers mutate unrelated values | `formats.py::_transform_sqlite,_verify_sqlite` | CREDIBLE | test pending | pending |
| 15 | high | `report.json` binds no source/plan/verification digest chain | `pipeline.py::RunReport,run_pipeline` | CREDIBLE | schema test pending | pending |
| 16 | med | Non-strict policy validation: `version:true`==1, duplicate keys last-wins (missing arrays still default empty) | `policy.py::compile_policy,load_policy` | FIXED (bool rejected; dup-key hook) | `test_version_true_is_rejected`, `test_duplicate_policy_keys_rejected` (green) | done |
| 17 | med | Attacker-controlled `rule_id`/`data_type`/filenames interpolated into error messages | `errors.py::AnonError`, `policy.py`, `verification.py` | CREDIBLE | leak test pending | pending |

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
