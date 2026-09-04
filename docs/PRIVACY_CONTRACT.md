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

## Verified locally (deterministic)

The verifier rereads the output corpus from disk and re-derives the expected
result; it does not trust the transform's return values. It shares the
replacement primitive (`replace_text`/`build_replacements`) with the transform,
so it is an independent RE-DERIVATION, not a fully separate second
implementation (see Known gaps).

- **Text, CSV, JSON: location-bound.** Output must equal an independent
  recompute (text skeleton; per-cell CSV with row/column-count checks; per-node
  JSON with decoded string values, duplicate-key rejection, and BOM handling).
  This catches swapped pseudonyms, dropped rows, relocated protected values, and
  escaped-literal evasion.
- **SQLite: relational AND per-row-located.** Row counts, `integrity_check`, and
  `foreign_key_check` are preserved, and a per-row location oracle compares
  every accepted row by rowid: text cells against the independent recompute,
  non-text cells byte-identical. Sensitive literals in any schema object SQL are
  rejected. Constructs the verifier cannot reproduce are rejected fail closed:
  triggers, `rowid`-shadowing columns, virtual tables, `WITHOUT ROWID`.
- Protected-value occurrence counts are preserved; protected/sensitive equality,
  containment, and prefix/suffix boundary overlap are rejected at compile time.
- Aliases of one subject converge to one pseudonym; distinct same-type subjects
  get distinct pseudonyms (checked in output, not only at compile time).
- The whole corpus is reread and verified, then promoted with a same-filesystem
  atomic rename and a durable (fsync + os.replace) report written last, under a
  trusted single-writer staging assumption. Any failure exits non-zero and
  leaves no ready corpus.
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
