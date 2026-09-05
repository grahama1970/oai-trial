# Adversarial test coverage by failure family

## Report Summary

**Overall Finding:** Partially Verified

**Core Conclusion:**  
83 collected cases across 74 functions: 50 adversarial, 21 positive controls, 6 boundary/stress probes, and 6 evidence checks. ADEQUACY: inadequate for the reviewed pre-fix snapshot. Targeted fixes require local qualification; this is not a new verdict on the corrected source. Response: /mnt/storage12tb/oai-trial/test-coverage-review/ask/ask-tau-please-assess-whether-the-curren-15df2b2d2829/node-artifacts/handler-webgpt/response.md

**Evidence Basis:**  
Fresh JUnit results joined to a source-reviewed catalog. Tests use synthetic inputs and, where stated, controlled adapter/write faults against real runtime code. Classification is project-agent judgment, not an automatic metric.

**Highest-Risk Issues:**
- F-002 Publication failure sequences and clean-submission qualification
- F-003 Sufficiency not inferred from counts

**Immediate Next Steps:**
- Reconcile the bounded WebGPT review
- A-001 Run the exact submitted Docker contract

**Non-Claims:**
- This covers security/tests, not all tests/ cases or a repo-wide attack count.
- Collected cases are not distinct attacks or statistically independent trials.
- Optional residual-risk tests are outside the release path.
- A passing test does not establish that its assertion catches every intended defect.
- This is not a new WebGPT PASS, proof of anonymity, or a shipping authorization.

## Scope
- Every collected security/tests case at 4947044f05bf9c52d60162de54ae78ba8f2b7474

## Project Context
Security cases ran; clean-submission qualification is pending.

## Source-of-Truth Inventory

| ID | Kind | Path | Limitation |
|---|---|---|---|
| Policy schema and identity conflicts | 8 cases: 7 adversarial; 1 controls; 0 boundary; 0 evidence. PASS 8; FAIL 0; SKIP 0 | security/tests/test_adversarial_matrix.py; security/tests/test_round3_fixes.py; security/tests/test_round4_fixes.py | Oracle: compile_policy/load_policy reject malformed or contradictory policies. Boundary: Mostly function-level rejection checks; not every malformed policy is exercised through Docker. |
| Bounded pseudonym domains | 2 cases: 1 adversarial; 0 controls; 1 boundary; 0 evidence. PASS 2; FAIL 0; SKIP 0 | security/tests/test_pseudonym_domains.py | Oracle: Distinct replacement cardinality at the IPv4 limit; over-capacity refusal. Boundary: IPv4 capacity is covered here; equivalent phone-capacity and forced collision exhaustion are not covered by these two cases. |
| Original-input matching and overlap | 4 cases: 1 adversarial; 0 controls; 3 boundary; 0 evidence. PASS 4; FAIL 0; SKIP 0 | security/tests/test_graybox_adversarial.py; security/tests/test_round2_fixes.py | Oracle: Replacement count, sampled literal absence, repeatability and overlap refusal. Boundary: Stress inputs are bounded; many-literal absence is sampled rather than exhaustively checked. |
| CSV dialect and located cell/row fidelity | 18 cases: 12 adversarial; 5 controls; 1 boundary; 0 evidence. PASS 18; FAIL 0; SKIP 0 | security/tests/test_csv_dialect.py; security/tests/test_graybox_adversarial.py; security/tests/test_verifier_location.py | Oracle: Unsupported/malformed dialect rejected; cells/rows reread; swaps/dropped rows rejected. Boundary: Six dialect variants use the CLI and empty-output oracle; other cases mostly call adapters/verifier directly. |
| JSON parsing, numbers and encoding | 9 cases: 5 adversarial; 3 controls; 1 boundary; 0 evidence. PASS 9; FAIL 0; SKIP 0 | security/tests/test_adversarial_matrix.py; security/tests/test_graybox_adversarial.py; security/tests/test_round2_fixes.py; security/tests/test_round3_fixes.py; security/tests/test_verifier_location.py | Oracle: Overflow/lossy numbers, depth, duplicate output keys and escaped literals; positive parsing controls. Boundary: Some positive controls assert only no exception. JSON key-set, list-order and scalar mutations outside these cases need separate coverage assessment. |
| SQLite row identity, schema and integrity | 11 cases: 8 adversarial; 3 controls; 0 boundary; 0 evidence. PASS 11; FAIL 0; SKIP 0 | security/tests/test_graybox_adversarial.py; security/tests/test_release_review_regressions.py; security/tests/test_round3_fixes.py; security/tests/test_sqlite_location.py; security/tests/test_sqlite_schema_literals.py | Oracle: Row swaps/non-text mutations rejected; trigger/rowid-shadow/view literal rejection; integrity/distinctness checks; legal sqliteX inventory and pre-verification schema mutations are checked through the complete pipeline. Boundary: DDL, column and foreign-key metadata are compared. The two supplied schema mutations are not exhaustive; wider supported schemas remain workload-driven. |
| Filesystem boundaries and privacy-safe failures | 8 cases: 7 adversarial; 1 controls; 0 boundary; 0 evidence. PASS 8; FAIL 0; SKIP 0 | security/tests/test_blackbox_contract.py; security/tests/test_error_privacy.py; security/tests/test_pipeline_failclosed.py; security/tests/test_round4_fixes.py; security/tests/test_sqlite_schema_literals.py | Oracle: Symlink/nested-root/type refusal, source-bound error redaction and CLI no-leak checks. Boundary: These cases do not exercise every special-file type, error identifier, or external writer race. |
| Publication, replay and source lineage | 11 cases: 4 adversarial; 5 controls; 0 boundary; 2 evidence. PASS 11; FAIL 0; SKIP 0 | security/tests/test_blackbox_contract.py; security/tests/test_pipeline_failclosed.py; security/tests/test_publish_hardening.py; security/tests/test_release_review_regressions.py; security/tests/test_source_snapshot.py | Oracle: Report/corpus existence, evidence hashes, clean output, prior release retention, changed-source digest detection; short writes must complete and zero-progress writes reject. Boundary: Short/zero writes are fault-injected through the real pipeline. Broader fsync/rename/power-loss campaigns remain future hardening; the source-mutation probe is helper-level. |
| Cross-format and text verifier mutations | 6 cases: 4 adversarial; 2 controls; 0 boundary; 0 evidence. PASS 6; FAIL 0; SKIP 0 | security/tests/test_typed_scalar_verification.py; security/tests/test_verifier_sensitivity.py | Oracle: Restored/removed/swapped text values and JSON bool/SQLite numeric type mutation rejected. Boundary: Re-derivation shares replacement primitives. One typed-scalar case contains two mutations, not two collected cases. |
| Public claims and report non-claims | 3 cases: 0 adversarial; 0 controls; 0 boundary; 3 evidence. PASS 3; FAIL 0; SKIP 0 | security/tests/test_blackbox_contract.py; security/tests/test_claim_surface.py; security/tests/test_verifier_sensitivity.py | Oracle: Known stale prose refused; report namespace and non-claim fields present. Boundary: Documentation/metadata checks, not adversarial data transformations. |
| Optional residual-risk demonstration | 3 cases: 1 adversarial; 1 controls; 0 boundary; 1 evidence. PASS 3; FAIL 0; SKIP 0 | security/tests/test_residual_risk.py | Oracle: Quasi-identifier singleton detection and declared-model scope. Boundary: Dev-only demonstration outside the release path; does not establish non-reidentifiability or close future issue 12. |
| S-RUN | pytest result + source-hash binding | security/reports/adversarial-coverage/security-junit.xml | Synthetic data; no full clean-submission Docker gate. |
| S-GOAL | required trial contract | GOAL.md; TRIAL_BRIEF.md | Normative requirements, not execution results. |
| S-WEBGPT | external reviewer evidence | /mnt/storage12tb/oai-trial/test-coverage-review/ask/ask-tau-please-assess-whether-the-curren-15df2b2d2829/node-artifacts/handler-webgpt/response.md | Reviewer judgment is not local closure proof. |

## Findings

### Finding: Directory totals are not attack coverage

**Finding ID:** F-001
**Status:** Verified
**Evidence:** inventory.json; security/reports/adversarial-coverage/security-junit.xml
**Rationale:** 83 collected cases across 74 functions: 50 adversarial, 21 positive controls, 6 boundary/stress probes, and 6 evidence checks.
**Impact:** Calling every case an attack inflates the assurance story.
**Owner:** project maintainer
**Valid Next Actions:** Use the family matrix and named oracles, not a count quota.
**Acceptance Check:** Every JUnit case maps once; all totals reconcile.
**Non-Claims:** Not a coverage percentage or independent-trial count.

### Finding: Release qualification is still a separate gate

**Finding ID:** F-002
**Status:** Needs Decision
**Evidence:** GOAL.md; security/reports/adversarial-coverage/security-junit.xml
**Rationale:** Nominal cleanup and digest tests do not establish crash recovery.
**Impact:** Passing pytest alone cannot authorize shipment.
**Owner:** release owner
**Valid Next Actions:** Run clean Docker qualification after reviewing required failure sequences.
**Acceptance Check:** Bare/mounted Docker commands, independent four-format readback, replay and negative cases pass from the submitted archive.
**Non-Claims:** No claim that production-hardening gaps are automatically in scope.

### Finding: Coverage sufficiency requires bounded review

**Finding ID:** F-003
**Status:** Verified
**Evidence:** ADEQUACY: inadequate for the reviewed pre-fix snapshot. Targeted fixes require local qualification; this is not a new verdict on the corrected source. Response: /mnt/storage12tb/oai-trial/test-coverage-review/ask/ask-tau-please-assess-whether-the-curren-15df2b2d2829/node-artifacts/handler-webgpt/response.md
**Rationale:** Oracles must detect defects, not just run hostile-looking inputs.
**Impact:** Adequacy requires reconciliation of named requirements and gaps.
**Owner:** project maintainer
**Valid Next Actions:** Reconcile WebGPT's actual findings with local source and reproducers.
**Acceptance Check:** Required blockers have fail-before/pass-after proof; disclosed future work stays separate.
**Non-Claims:** No universal security or anonymity guarantee.

### Finding: Three release defects were reproduced and fixed

**Finding ID:** F-004
**Status:** Verified
**Evidence:** security/reports/adversarial-coverage/remediation.json; /mnt/storage12tb/oai-trial/release-fixes/before.xml; /mnt/storage12tb/oai-trial/release-fixes/after.xml
**Rationale:** All 4 supplied failing cases pass after the targeted fixes. The local zero-progress write complement also passes.
**Impact:** Wrong-READY paths are closed under the named fault model.
**Owner:** project maintainer
**Valid Next Actions:** Qualify the clean container
**Acceptance Check:** Run supplied regressions and clean container qualification.
**Non-Claims:** Not a fresh reviewer PASS or completed Docker qualification.

## Surface / Module Contracts

### Surface Contract: Policy schema and identity conflicts
- Owning Persona: trial reviewer
- Core Purpose: Inspect policy schema and identity conflicts against R2, R3, R4, R5
- Primary Object: security/tests/test_adversarial_matrix.py::test_case_insensitive_conflicting_identities_rejected; security/tests/test_adversarial_matrix.py::test_duplicate_policy_keys_rejected; security/tests/test_adversarial_matrix.py::test_version_true_is_rejected; security/tests/test_round3_fixes.py::test_missing_protected_values_rejected; security/tests/test_round3_fixes.py::test_missing_sensitive_values_rejected; security/tests/test_round4_fixes.py::test_empty_protected_reason_is_rejected; security/tests/test_round4_fixes.py::test_non_string_protected_reason_is_rejected; security/tests/test_round4_fixes.py::test_valid_protected_reason_accepted
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: Bounded pseudonym domains
- Owning Persona: trial reviewer
- Core Purpose: Inspect bounded pseudonym domains against R3, R4
- Primary Object: security/tests/test_pseudonym_domains.py::test_at_capacity_ip_policy_is_accepted; security/tests/test_pseudonym_domains.py::test_over_capacity_ip_policy_rejects_before_collision_search
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: Original-input matching and overlap
- Owning Persona: trial reviewer
- Core Purpose: Inspect original-input matching and overlap against R2, R5, R12
- Primary Object: security/tests/test_graybox_adversarial.py::test_many_literals_completes_and_removes_all; security/tests/test_graybox_adversarial.py::test_pathological_overlap_is_deterministic; security/tests/test_graybox_adversarial.py::test_very_long_literal; security/tests/test_round2_fixes.py::test_partial_boundary_overlap_rejected
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: CSV dialect and located cell/row fidelity
- Owning Persona: trial reviewer
- Core Purpose: Inspect csv dialect and located cell/row fidelity against R1, R2, R6, R7, R11
- Primary Object: security/tests/test_csv_dialect.py::test_comma_csv_multi_column_still_accepted; security/tests/test_csv_dialect.py::test_malformed_comma_quoting_is_rejected; security/tests/test_csv_dialect.py::test_quoted_punctuation_and_multiline_comma_csv_are_preserved; security/tests/test_csv_dialect.py::test_semicolon_csv_is_rejected_not_silently_reinterpreted; security/tests/test_csv_dialect.py::test_semicolon_dialect_with_quoted_comma_is_rejected_before_release; security/tests/test_csv_dialect.py::test_single_column_comma_csv_still_accepted; security/tests/test_graybox_adversarial.py::test_csv_embedded_multiline_and_quotes_preserved; security/tests/test_graybox_adversarial.py::test_large_csv_field_preserved; security/tests/test_verifier_location.py::test_dropped_csv_row_rejected; security/tests/test_verifier_location.py::test_swapped_pseudonyms_in_csv_rejected
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: JSON parsing, numbers and encoding
- Owning Persona: trial reviewer
- Core Purpose: Inspect json parsing, numbers and encoding against R1, R2, R6, R7, R11
- Primary Object: security/tests/test_adversarial_matrix.py::test_non_finite_json_number_is_rejected; security/tests/test_graybox_adversarial.py::test_json_deep_within_bound_ok; security/tests/test_graybox_adversarial.py::test_json_over_depth_rejected; security/tests/test_round2_fixes.py::test_exact_float_still_allowed; security/tests/test_round2_fixes.py::test_lossy_float_rejected; security/tests/test_round2_fixes.py::test_verifier_rejects_duplicate_output_keys; security/tests/test_round3_fixes.py::test_json_bom_is_stripped_by_searcher; security/tests/test_verifier_location.py::test_clean_run_still_verifies; security/tests/test_verifier_location.py::test_escaped_json_sensitive_value_rejected
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: SQLite row identity, schema and integrity
- Owning Persona: trial reviewer
- Core Purpose: Inspect sqlite row identity, schema and integrity against R1, R2, R4, R6, R7
- Primary Object: security/tests/test_graybox_adversarial.py::test_sqlite_unique_column_integrity_preserved; security/tests/test_release_review_regressions.py::test_schema_mutation_is_rejected_before_publication; security/tests/test_release_review_regressions.py::test_sqlite_prefix_lookalike_is_processed; security/tests/test_round3_fixes.py::test_sqlite_rowid_shadow_rejected; security/tests/test_round3_fixes.py::test_sqlite_trigger_rejected; security/tests/test_sqlite_location.py::test_clean_sqlite_run_verifies; security/tests/test_sqlite_location.py::test_swapped_sqlite_subject_pseudonyms_rejected; security/tests/test_sqlite_location.py::test_unrelated_value_mutation_rejected; security/tests/test_sqlite_schema_literals.py::test_clean_view_still_accepted; security/tests/test_sqlite_schema_literals.py::test_sensitive_literal_in_view_sql_is_rejected
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: Filesystem boundaries and privacy-safe failures
- Owning Persona: trial reviewer
- Core Purpose: Inspect filesystem boundaries and privacy-safe failures against R9, R10
- Primary Object: security/tests/test_blackbox_contract.py::test_hostile_input_fails_closed_no_ready_marker; security/tests/test_blackbox_contract.py::test_no_sensitive_value_in_release_or_stdio; security/tests/test_error_privacy.py::test_hostile_policy_identifiers_never_appear_in_error_text; security/tests/test_pipeline_failclosed.py::test_nested_roots_rejected; security/tests/test_pipeline_failclosed.py::test_symlink_in_corpus_rejected; security/tests/test_pipeline_failclosed.py::test_unsupported_input_fails_closed; security/tests/test_round4_fixes.py::test_policy_symlink_rejected_before_policy_read; security/tests/test_sqlite_schema_literals.py::test_hostile_filenames_never_appear_in_error_text
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: Publication, replay and source lineage
- Owning Persona: trial reviewer
- Core Purpose: Inspect publication, replay and source lineage against R3, R8, R9, R10
- Primary Object: security/tests/test_blackbox_contract.py::test_deterministic_replay; security/tests/test_pipeline_failclosed.py::test_prior_release_survives_failed_rerun; security/tests/test_pipeline_failclosed.py::test_success_writes_report_last; security/tests/test_publish_hardening.py::test_no_staging_left_in_output; security/tests/test_publish_hardening.py::test_report_binds_evidence_chain; security/tests/test_publish_hardening.py::test_report_is_regular_file_no_temp_left; security/tests/test_publish_hardening.py::test_report_matches_committed_schema; security/tests/test_release_review_regressions.py::test_short_report_write_cannot_return_success_with_truncated_json; security/tests/test_release_review_regressions.py::test_zero_report_write_fails_closed; security/tests/test_source_snapshot.py::test_source_digest_detects_content_change_even_if_mtime_preserved; security/tests/test_source_snapshot.py::test_source_digest_stable_when_unchanged
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: Cross-format and text verifier mutations
- Owning Persona: trial reviewer
- Core Purpose: Inspect cross-format and text verifier mutations against R2, R4, R6, R8
- Primary Object: security/tests/test_typed_scalar_verification.py::test_clean_typed_run_verifies; security/tests/test_typed_scalar_verification.py::test_json_bool_number_and_sqlite_integer_real_mutations_rejected; security/tests/test_verifier_sensitivity.py::test_baseline_passes; security/tests/test_verifier_sensitivity.py::test_incomplete_subject_coverage_is_caught; security/tests/test_verifier_sensitivity.py::test_restored_literal_is_caught; security/tests/test_verifier_sensitivity.py::test_swapped_subject_pseudonyms_is_caught
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: Public claims and report non-claims
- Owning Persona: trial reviewer
- Core Purpose: Inspect public claims and report non-claims against R9, R15
- Primary Object: security/tests/test_blackbox_contract.py::test_report_declares_non_claims; security/tests/test_claim_surface.py::test_public_claims_match_current_evidence; security/tests/test_verifier_sensitivity.py::test_report_carries_non_claims
- Source of Truth: inventory.json and source-bound security-junit.xml

### Surface Contract: Optional residual-risk demonstration
- Owning Persona: trial reviewer
- Core Purpose: Inspect optional residual-risk demonstration against OUT_OF_SCOPE_RISK_PLANE
- Primary Object: security/tests/test_residual_risk.py::test_flags_unique_quasi_identifier_combo; security/tests/test_residual_risk.py::test_pass_when_all_combos_repeat; security/tests/test_residual_risk.py::test_schema_and_non_claims_present
- Source of Truth: inventory.json and source-bound security-junit.xml

## Finished / Pending / Outstanding / Broken / Blocked / Unproven

### Finished
- JUnit reconciles all 83 cases and 74 functions.

### Pending
- ADEQUACY: inadequate for the reviewed pre-fix snapshot. Targeted fixes require local qualification; this is not a new verdict on the corrected source. Response: /mnt/storage12tb/oai-trial/test-coverage-review/ask/ask-tau-please-assess-whether-the-curren-15df2b2d2829/node-artifacts/handler-webgpt/response.md
- A-001 clean-submission qualification

### Outstanding
- Reconcile the named oracle limitations, without reopening future scope.

### Broken
- none

### Blocked
- none

### Unproven
- Exhaustive security, anonymity, crash/power-loss behavior and production scale.

## Plan-Ready Next Actions

- **A-001** (F-002, P1): Run the final release gate after bounded coverage review. Acceptance: Bare/mounted Docker commands, independent four-format readback, replay and negative cases pass from the submitted archive.

## Plan-Iterate Seed

**Recommended phase id:** `release-qualification`

**Objective:** Run the final release gate after bounded coverage review.

**Deterministic Evidence Gates:**
- uv run pytest -q
- docker build -t anonymization-trial .
- docker run --rm anonymization-trial
- Mounted four-format run and independent output readback

## New Plan-Iterate Instructions

Use the Plan-Iterate Seed above as the initial phase contract.

## Non-Claims
- This covers security/tests, not all tests/ cases or a repo-wide attack count.
- Collected cases are not distinct attacks or statistically independent trials.
- Optional residual-risk tests are outside the release path.
- A passing test does not establish that its assertion catches every intended defect.
- This is not a new WebGPT PASS, proof of anonymity, or a shipping authorization.
