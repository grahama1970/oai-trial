```ticket
id: sqlite-schema-literal-leak
title: Reject policy-sensitive literals embedded in SQLite schema objects
severity: high
scope: in_scope_for_8h_trial
files: src/anonymization_trial/formats.py, src/anonymization_trial/verification.py, security/tests/test_sqlite_location.py
problem: The new row-location oracle closes table-cell swaps, but accepted SQLite files can still carry a policy literal in sqlite_master SQL that neither transformation nor verification scans. For example CREATE VIEW leaked AS SELECT 'Alice' AS name can publish READY and SELECT * FROM leaked still returns Alice.
fix: Inventory every sqlite_master object before transformation and fail closed when a policy-sensitive literal occurs in any schema object name or SQL definition that is not transformed, including views, indexes, defaults, generated expressions, and other retained DDL.
acceptance: uv run pytest -q security/tests/test_sqlite_schema_literals.py::test_sensitive_literal_in_view_sql_is_rejected
```

```ticket
id: cost-model-billing-units
title: Finish and synchronize the mandatory 1 TB and 1 PB cost model
severity: high
scope: in_scope_for_8h_trial
files: scripts/estimate_aws_cost.py, costs/aws-us-east-1-inputs.json, costs/example-estimates.json, docs/production-architecture.md, SUBMISSION.md
problem: The estimator now models substantially more of the flow, but docs/production-architecture.md and costs/example-estimates.json still contain the old approximately $52/$51,836 totals while SUBMISSION.md reports approximately $83/$83,201. The estimator also uses one uncited blended orchestration_per_object_usd and one flat S3 storage price instead of exposing the requested service billing units, tiers or discount assumptions, transfer assumption, and quota assumptions.
fix: Decompose SQS/EventBridge/KMS/CloudWatch orchestration into explicit quantity-times-unit-price inputs, model applicable storage tiers or explicitly document the chosen tier treatment, state same-region/egress transfer cost assumptions and relevant quotas/discount assumptions, regenerate example-estimates.json, and make every documented 1 TB/1 PB total derive from that single output.
acceptance: uv run pytest -q tests/test_cost_model.py::test_1tb_1pb_cost_and_sla_contract
```

```ticket
id: claim-surface-current-state
title: Synchronize all proof and presentation claims to the current implementation
severity: medium
scope: in_scope_for_8h_trial
files: README.md, SUBMISSION.md, docs/ARCHITECTURE.md, docs/PRIVACY_CONTRACT.md, docs/ACCEPTANCE_MATRIX.md, security/ADVERSARIAL_MATRIX.md, security/SECURITY.md, docs/pitch/oai-trial/deck.curated.yaml, docs/pitch/oai-trial/claim_ledger.curated.yaml
problem: Current claim surfaces still describe superseded states: README/SUBMISSION say 78 tests while the stated gate is 96; PRIVACY_CONTRACT and SUBMISSION still say SQLite has no per-row oracle; ARCHITECTURE still claims bounded-memory/streaming and deterministic domain extension; ACCEPTANCE_MATRIX still labels SQLite relational-only; ADVERSARIAL_MATRIX still leaves fixed items pending; and README/SECURITY/pitch claims still present Semgrep plus dependency SCA more strongly than the committed receipts support.
fix: Update every claim from one current evidence inventory, distinguish independent re-derivation from separate implementation, reflect the SQLite location oracle and bounded pseudonym domains, remove streaming/bounded-memory claims, use the current test count or avoid hard-coded counts, and downgrade scanner/Battle statements to exactly what committed receipts prove.
acceptance: uv run pytest -q security/tests/test_claim_surface.py::test_claim_matrices_reference_only_current_evidence
```

```ticket
id: error-path-redaction
title: Remove remaining attacker-controlled filenames and suffixes from exception text
severity: medium
scope: in_scope_for_8h_trial
files: src/anonymization_trial/pipeline.py, src/anonymization_trial/verification.py, src/anonymization_trial/errors.py, security/tests/test_error_privacy.py
problem: safe_ref now protects rule_id and data_type, but pipeline and verifier errors still interpolate attacker-controlled path material such as entry.suffix, rel.name, and SQLite filename arguments. An unsupported filename whose suffix itself contains a policy value can therefore enter AnonError text before the sensitive-path rejection runs.
fix: Make filesystem and verification failures use generic text or safe_ref(path-relative identifiers); never place raw relative filenames, suffixes, or other input-controlled path components in AnonError messages.
acceptance: uv run pytest -q security/tests/test_error_privacy.py::test_hostile_filenames_never_appear_in_error_text
```

```ticket
id: scrub-host-paths
title: Remove real workstation paths from committed evidence artifacts
severity: low
scope: in_scope_for_8h_trial
files: security/hack-audit.receipt.json, docs/pitch/oai-trial/generated/plan_receipt.json, docs/pitch/oai-trial/generated/asset_manifest.yaml, docs/pitch/oai-trial/generated/source_manifest.resolved.yaml, docs/pitch/oai-trial/assets/architecture.receipt.json
problem: Committed receipts and generated pitch artifacts contain absolute workstation paths such as ${PROJECT_ROOT}. They are unnecessary provenance leakage and conflict with the submission instruction not to include real personal data.
fix: Regenerate or normalize committed evidence so paths are repository-relative or use a stable placeholder such as ${PROJECT_ROOT}; retain hashes and semantic provenance without host/user-specific path components.
acceptance: ! rg -n '/home/graham|/home/[^/]+/workspace' security docs/pitch
```
