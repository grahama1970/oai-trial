```ticket
id: typed-scalar-verifier
title: Make JSON and SQLite verification type-sensitive
severity: high
scope: in_scope_for_8h_trial
files: src/anonymization_trial/verification.py, security/tests/test_typed_scalar_verification.py
problem: The location oracle still uses Python equality for non-string scalars: JSON `true` compares equal to numeric `1`, and SQLite INTEGER `1` compares equal to REAL `1.0`. Those type/storage-class mutations can therefore pass verification despite the required structure and non-sensitive-data preservation guarantees. fileciteturn241file0 fileciteturn237file0
fix: Add a type-aware recursive JSON comparator that requires identical JSON scalar types as well as values, and compare SQLite storage class (`typeof()` or equivalent typed projection) plus value for every non-text cell.
acceptance: uv run pytest -q security/tests/test_typed_scalar_verification.py::test_json_bool_number_and_sqlite_integer_real_mutations_rejected
```

```ticket
id: production-svg-contract-drift
title: Update the production SVG to match the manifest-pointer publication design
severity: medium
scope: in_scope_for_8h_trial
files: docs/production-architecture.svg, docs/production-architecture.md
problem: The prose now requires format-aware partitioning and an immutable corpus manifest followed by an active-corpus pointer switch, but the committed SVG still shows only Intake -> Distribute -> Transform -> Verify -> Release and a quarantine arrow. It does not show the manifest/pointer commit, retry/replay path, or the durable publication boundary required by the brief, so diagram labels no longer agree with the production design. fileciteturn222file0 fileciteturn238file0 fileciteturn237file0
fix: Regenerate the SVG with format-aware distribution, staging, verifier fan-in, immutable corpus manifest, atomic active-pointer publication, retry/replay and quarantine paths, and explicit trust/durable boundaries matching production-architecture.md.
acceptance: uv run pytest -q tests/test_production_design_contract.py::test_svg_matches_manifest_pointer_and_retry_flow
```

```ticket
id: cost-model-required-units
title: Add the remaining mandatory billing-unit and quota assumptions to the cost model
severity: medium
scope: in_scope_for_8h_trial
files: scripts/estimate_aws_cost.py, costs/aws-us-east-1-inputs.json, costs/example-estimates.json, docs/production-architecture.md, SUBMISSION.md
problem: The totals are now synchronized and internally reproducible, but orchestration is still one uncited blended `orchestration_per_object_usd` rather than explicit SQS/EventBridge/KMS/CloudWatch billing units, and the model does not state transfer pricing assumptions, S3 tier treatment or discounts, or concrete quota assumptions. Those are explicitly required fields in the trial brief. fileciteturn219file0 fileciteturn220file0 fileciteturn222file0 fileciteturn223file0 fileciteturn237file0
fix: Replace the blended orchestration floor with explicit service quantities and unit prices, state same-region/egress transfer assumptions, model or explicitly bound S3 pricing tiers/discounts, record relevant S3/SQS/Fargate quotas, cite those price inputs, and regenerate the committed estimate.
acceptance: uv run pytest -q tests/test_cost_model.py::test_required_billing_units_transfer_tiers_and_quotas_are_explicit
```

```ticket
id: claim-surface-final-sync
title: Remove the remaining stale and contradictory proof claims
severity: medium
scope: in_scope_for_8h_trial
files: README.md, SUBMISSION.md, docs/ARCHITECTURE.md, docs/PRIVACY_CONTRACT.md, docs/ANONYMIZATION_SEMANTICS.md, security/ADVERSARIAL_MATRIX.md, security/SECURITY.md, docs/pitch/oai-trial/deck.curated.yaml, docs/pitch/oai-trial/claim_ledger.curated.yaml
problem: Current main reports a 100-test gate, but README/SUBMISSION still say 99 and the curated deck/ledger still say 62; SUBMISSION still calls CSV/TXT streaming and says the cost model omits items it now includes; ARCHITECTURE still says bounded memory and deterministic domain extension; ANONYMIZATION_SEMANTICS says both `no domain extension` and `domain-extended`; PRIVACY_CONTRACT still claims `across_tenants:false` and a consumer without a private key although the local scope is public `trial-v1`; and README/SECURITY/pitch still present Semgrep plus dependency SCA more strongly than the committed security receipts establish. fileciteturn217file0 fileciteturn224file0 fileciteturn225file0 fileciteturn226file0 fileciteturn227file0 fileciteturn228file0 fileciteturn229file0 fileciteturn231file0 fileciteturn234file0 fileciteturn236file0
fix: Generate all public claims from one current evidence inventory: use the actual gate result or avoid hard-coded counts, describe per-file materialization rather than streaming, describe bounded-reject pseudonym domains consistently, state the public fixed local scope and no private-key secrecy, update cost-gap wording to the current estimator, and downgrade SAST/SCA/Battle claims to exactly what committed receipts prove.
acceptance: uv run pytest -q security/tests/test_claim_surface.py::test_public_claims_match_current_evidence
```
