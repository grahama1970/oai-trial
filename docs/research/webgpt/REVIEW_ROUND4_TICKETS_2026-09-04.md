```ticket
id: sqlite-location-oracle
title: Add location-bound verification for the accepted SQLite subset
severity: high
scope: in_scope_for_8h_trial
files: src/anonymization_trial/formats.py, src/anonymization_trial/verification.py, docs/PRIVACY_CONTRACT.md
problem: Triggers and rowid-shadowing tables now fail closed, but accepted SQLite files are still verified only by sensitive-literal absence, subject presence, row counts, integrity_check, and foreign_key_check. A wrong pseudonym swap between ordinary rows or an unrelated value mutation can therefore remain structurally valid and pass verification.
fix: Add a source-to-output SQLite oracle for accepted tables keyed by hidden rowid or a proven INTEGER PRIMARY KEY; compare schema inventory, row identity, all non-text scalar values, and each text cell against the expected transformed value, and reject generated-column constructs the oracle cannot reproduce.
acceptance: uv run pytest -q security/tests/test_sqlite_location.py::test_swapped_sqlite_subject_pseudonyms_rejected
```

```ticket
id: production-partition-publish
title: Make production partitioning and corpus publication format-safe
severity: high
scope: in_scope_for_8h_trial
files: docs/production-architecture.md, docs/production-architecture.svg
problem: The production design proposes line-aligned byte splitting for CSV, which breaks valid quoted multiline records, and promotes verified files individually so consumers can observe a partially promoted corpus.
fix: Define format-specific partition semantics: UTF-8-safe text overlap ownership, parser-aware CSV record boundaries, a bounded/record-framed JSON strategy, and whole-object SQLite; stage all outputs and publish only an immutable verified corpus manifest plus a conditional active pointer after verifier fan-in.
acceptance: uv run pytest -q tests/test_production_design_contract.py::test_partitioning_and_corpus_publish_are_fail_closed
```

```ticket
id: cost-sla-required-arithmetic
title: Complete the mandatory 1 TB and 1 PB SLA and cost model
severity: high
scope: in_scope_for_8h_trial
files: docs/production-architecture.md, scripts/estimate_aws_cost.py, costs/aws-us-east-1-inputs.json, SUBMISSION.md
problem: The SLA says 200 workers at 20 MB/s each require about 1.4 hours for 1 TB although that assumption implies roughly 4 GB/s aggregate, and the estimator omits required verifier rereads, staging/promotion operations, retries, orchestration, queueing, KMS, logging, output expansion, transfer, tiers, and quotas.
fix: Derive runtime from concurrency and per-worker throughput for both 1 TB and 1 PB, add every material quantity-times-unit-price line item and retention assumption, include tier/quota/transfer/discount assumptions, and generate low/base/high sensitivity results from the same committed inputs.
acceptance: uv run pytest -q tests/test_cost_model.py::test_1tb_1pb_cost_and_sla_contract
```

```ticket
id: csv-dialect-failclosed
title: Define and enforce the supported CSV dialect
severity: medium
scope: in_scope_for_8h_trial
files: src/anonymization_trial/formats.py, src/anonymization_trial/verification.py, SUBMISSION.md
problem: The transformer and verifier both assume Python's default comma/quote dialect, so an alternative-delimiter CSV can be silently interpreted under the wrong logical structure instead of being rejected as unsupported.
fix: Freeze an explicit accepted CSV dialect, perform bounded preflight dialect validation and fail closed on conflicting or ambiguous dialect evidence, and make both transform and verifier use the frozen dialect contract.
acceptance: uv run pytest -q security/tests/test_csv_dialect.py::test_semicolon_csv_is_rejected_not_silently_reinterpreted
```

```ticket
id: policy-preflight-before-read
title: Reject an unsafe policy path before reading policy bytes
severity: medium
scope: in_scope_for_8h_trial
files: src/anonymization_trial/pipeline.py, src/anonymization_trial/policy.py
problem: run_pipeline calls load_policy before _preflight checks whether policy.json is a symlink or regular file, so an untrusted policy symlink is followed before the safety gate evaluates it.
fix: Split filesystem preflight from policy-dependent corpus checks; lstat policy.json and corpus first, reject symlinks and non-regular policy files, then read and compile only the validated policy object.
acceptance: uv run pytest -q security/tests/test_pipeline_failclosed.py::test_policy_symlink_rejected_before_policy_read
```

```ticket
id: privacy-safe-error-identifiers
title: Remove attacker-controlled identifiers from exception text
severity: medium
scope: in_scope_for_8h_trial
files: src/anonymization_trial/policy.py, src/anonymization_trial/pseudonyms.py, src/anonymization_trial/errors.py
problem: The error contract says messages never contain raw identifiers, but policy compilation and namespace failures interpolate attacker-controlled rule_id and data_type values into AnonError text.
fix: Emit only closed error codes plus safe indexes or opaque digests from library exceptions; never interpolate policy strings, filenames, literals, subject IDs, rule IDs, or data types into externally observable error text.
acceptance: uv run pytest -q security/tests/test_error_privacy.py::test_hostile_policy_identifiers_never_appear_in_error_text
```

```ticket
id: policy-protected-reason-schema
title: Finish strict validation of protected-value reason
severity: low
scope: in_scope_for_8h_trial
files: src/anonymization_trial/policy.py, examples/policy.schema.json
problem: The JSON schema requires protected_values[].reason to be a non-empty string when present, but compile_policy accepts any value for reason and silently ignores it.
fix: Validate reason when present as a non-empty string so compile_policy and the committed v1 schema accept and reject the same payloads.
acceptance: uv run pytest -q security/tests/test_policy_schema.py::test_non_string_protected_reason_is_rejected
```

```ticket
id: pseudonym-domain-preflight
title: Preflight bounded pseudonym namespaces instead of collision-loop exhaustion
severity: medium
scope: in_scope_for_8h_trial
files: src/anonymization_trial/pseudonyms.py, docs/ANONYMIZATION_SEMANTICS.md, SUBMISSION.md
problem: Phone and IPv4 domains are finite but build_replacements discovers exhaustion through repeated salted hashing up to 100000 attempts, while ANONYMIZATION_SEMANTICS.md still describes domain extension including an IP range the implementation does not use.
fix: Count canonical identities per bounded type before derivation, reject immediately when a type cannot be injectively represented, impose a small deterministic collision-attempt bound below capacity, and make the semantics document describe the implemented bounded-reject behavior.
acceptance: uv run pytest -q security/tests/test_pseudonym_domains.py::test_over_capacity_ip_policy_rejects_before_collision_search
```

```ticket
id: evidence-matrix-truth
title: Synchronize requirement and adversarial matrices with actual proofs
severity: medium
scope: in_scope_for_8h_trial
files: docs/ACCEPTANCE_MATRIX.md, security/ADVERSARIAL_MATRIX.md, security/SECURITY.md, src/anonymization_trial/verification.py
problem: ACCEPTANCE_MATRIX.md still names unimplemented proof such as chunk-split replacement, structural fingerprint parity, SQLite schema hashes, and verifier BOM confirmation; ADVERSARIAL_MATRIX.md still marks the trigger/rowid portion of #14 pending, and SECURITY.md still calls text processing streaming.
fix: Replace every evidence cell with an existing test or explicitly bounded non-claim, split SQLite relational proof from location proof, update fixed statuses to the retained round-3 tests, and remove all streaming/fingerprint/schema-hash claims not implemented.
acceptance: uv run pytest -q security/tests/test_claim_surface.py::test_claim_matrices_reference_only_current_evidence
```

```ticket
id: pseudonym-scope-nonclaim
title: Align privacy claims with the public fixed local pseudonym scope
severity: medium
scope: out_of_scope_but_must_be_disclosed
files: src/anonymization_trial/pseudonyms.py, docs/PRIVACY_CONTRACT.md, docs/ANONYMIZATION_SEMANTICS.md, SUBMISSION.md
problem: The local implementation uses public SCOPE_ID=trial-v1 with no private key, while PRIVACY_CONTRACT.md still states across_tenants:false and assumes the consumer lacks a private key; tenant-scoped unlinkability is a production feature, not a local guarantee.
fix: Remove the contradictory local cross-tenant/private-key claims and state that production replaces the public namespace with tenant-or-purpose-scoped keyed HMAC.
acceptance: "Local trial pseudonyms use the public fixed scope trial-v1; they provide no private-key secrecy or cross-tenant unlinkability."
```

```ticket
id: security-evidence-scope
title: Downgrade or regenerate unsupported security-scan and Battle claims
severity: medium
scope: out_of_scope_but_must_be_disclosed
files: security/README.md, security/SECURITY.md, security/hack-audit.receipt.json, security/battle/run-receipt.json
problem: The committed Hack receipt shows Semgrep scanned 0 target files and contains no SCA execution, while the docs claim Semgrep plus Bandit plus dependency SCA; the Battle receipt explicitly identifies a non-agentic local deterministic fixture rather than adaptive live lineage.
fix: Either regenerate commit-bound evidence with nonzero Semgrep targets, a committed SCA receipt, and any claimed live Battle lane, or downgrade the documentation to the exact evidence the committed receipts establish.
acceptance: "The committed security receipts are supporting evidence only: Semgrep scanned 0 target files, no dependency-SCA receipt is committed, and the Battle artifact is a deterministic fixture rather than adaptive live lineage."
```

```ticket
id: verify-seal-single-writer
title: Record the trusted single-writer assumption at the verify-to-seal boundary
severity: low
scope: out_of_scope_but_must_be_disclosed
files: src/anonymization_trial/pipeline.py, SUBMISSION.md, docs/PRIVACY_CONTRACT.md
problem: verify_corpus does not return the digest it verified; run_pipeline computes the first sealed digest afterward, so an external writer with staging access could mutate bytes in that gap. This is reasonably outside an eight-hour trial under a trusted single-writer staging filesystem.
fix: Retain the explicit single-writer assumption for the trial; production hardening should have the verifier return a digest-bound receipt and publish only those exact sealed bytes.
acceptance: "**verify -> publish assumes a trusted single-writer staging filesystem.**"
```

```ticket
id: source-toctou-readonly
title: Record the mounted-read-only source assumption for deeper TOCTOU attacks
severity: low
scope: out_of_scope_but_must_be_disclosed
files: src/anonymization_trial/pipeline.py, SUBMISSION.md
problem: Rehashing detects persistent source changes but cannot exclude a hostile host swapping bytes for one processing read and restoring them before the final digest. The required Docker command mounts input read-only, so deeper hostile-host mutation is reasonably outside the local trial threat model.
fix: Keep the limitation explicit locally; production should bind immutable object versions or snapshot identifiers rather than repeatedly reopening mutable paths.
acceptance: "A source-snapshot/TOCTOU gate rejects content that changes during a run; deeper host-side swap-and-restore is outside the mounted-read-only container threat model."
```

```ticket
id: verifier-implementation-diversity
title: Preserve the non-claim that verification reuses replacement primitives
severity: low
scope: out_of_scope_but_must_be_disclosed
files: src/anonymization_trial/verification.py, SUBMISSION.md, docs/PRIVACY_CONTRACT.md
problem: Verification independently rereads and re-derives output but still calls replace_text and build_replacements, so a common matcher or pseudonym bug can affect producer and checker. A wholly separate reference implementation is stronger assurance but not required for this eight-hour trial if the boundary is stated accurately.
fix: Keep the disclosure; a production/high-assurance follow-up should implement a simple separately coded reference span selector and pseudonym oracle for verification.
acceptance: "**The verifier is an independent re-derivation, not a separate implementation.**"
```

```ticket
id: local-memory-scaling
title: Preserve the non-claim that the local engine is not TB/PB streaming
severity: medium
scope: out_of_scope_but_must_be_disclosed
files: src/anonymization_trial/formats.py, src/anonymization_trial/verification.py, SUBMISSION.md
problem: Text, JSON, SQLite rows, matcher occurrences, and corpus-wide verifier strings are materialized in memory, so the local implementation itself is not suitable for TB/PB execution. The brief requires a production scale design rather than a local petabyte run, so this is acceptable when stated without contradictory streaming claims.
fix: Retain the explicit local non-claim and ensure the production design identifies streaming/partitioned replacements and the thresholds that trigger them.
acceptance: "**Not streaming/bounded-memory.** Per-file content is materialized in memory; TB/PB is designed and cost-modelled, not run at scale."
```
