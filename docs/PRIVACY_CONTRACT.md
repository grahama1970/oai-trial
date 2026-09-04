# Privacy contract (v1)

What this pipeline proves, and — just as important — what it does not. Grounded
in recent anonymization research: exact identifier removal is not the same as
non-reidentifiability (RAT-Bench arXiv:2602.12806; SPIA arXiv:2604.21211), and an
anonymization claim is meaningless without a stated domain, protected unit,
scope, and adversary ("Why Data Anonymization Has Not Taken Off" arXiv:2509.10165).

```yaml
schema: anonymization_trial.privacy_contract.v1
data_domain: customer_export_corpus
protected_unit: [policy_literal, policy_subject]
scope_id: trial-v1
discovery_authority: policy.json only
matching: { mode: literal, normalization: none, case: exact_or_ascii_insensitive }
schema_identifier_policy: reject_if_sensitive
allowed_linkage: { within_file: true, across_files: true, across_formats: true, across_retries: true, across_tenants: false }
transformation: deterministic_type_specific_pseudonymization
key_mode: public-deterministic-trial-namespace   # local; production uses KMS-scoped HMAC
release_standard: complete_verified_corpus_fail_closed
adversary_assumption: release consumer lacks the raw input and the private key/mapping
```

## Proven (deterministic, locally verified)
- Every policy-selected literal occurrence is replaced (independently counted).
- Protected values and their occurrence counts are preserved.
- Aliases of one subject converge to one pseudonym; distinct same-type subjects
  get distinct pseudonyms (verified in output, not just at compile time).
- Structure preserved per format (CSV headers/rows/order, JSON topology/keys,
  SQLite schema/relationships/row counts/integrity).
- The whole corpus is reread and verified before an atomic, report-last release;
  any failure exits non-zero and leaves no ready corpus.
- No replacement mapping or key material appears in the release dir or logs.

## Not established (out of scope for a literal-policy pipeline)
- Discovery of sensitive values omitted from `policy.json`.
- Resistance to linkage with external datasets.
- Anonymity against inference from quasi-identifiers.
- Formal anonymity, differential privacy, or k-anonymity.
- Resistance to agentic/LLM re-identification (up to 68% recall at 90% precision
  reported in the wild — arXiv:2602.16800). This is a separate production
  risk-plane, tracked as a follow-up, not a claim this pipeline makes.

`report.json` carries the machine-readable `does_not_establish` list so a
consumer cannot mistake "verification passed" for "provably anonymous."
