# Deterministic pseudonymization + identity coherence

## Requirement (brief)
Replacements stable across files and repeated runs; one identity forms one
pseudonymous profile (via `subject_id`); distinct identities must not share a
type-specific replacement; aliases of one identity may converge.

## Sources
- Google Cloud Sensitive Data Protection — Pseudonymization: https://docs.cloud.google.com/sensitive-data-protection/docs/pseudonymization
- xata.io — Pseudonymization vs Anonymization: https://xata.io/blog/pseudonymization-vs-anonymization-which-approach-fits-your-data-strategy
- xata.io — Data Pseudonymization Explained: https://xata.io/blog/data-pseudonymization-explained-when-anonymization-isnt-enough
- IRI — Reversible/Irreversible tokenization: https://www.iri.com/solutions/data-masking/static-data-masking/pseudonymize
- DEV — Data Pseudonymization: When You Can't Just Delete Everything: https://dev.to/manualwise/data-pseudonymization-when-you-cant-just-delete-everything-4goa

## Key findings
- **Deterministic transform is the standard for referential integrity.** Same
  input + same key/algorithm → same pseudonym everywhere, so relationships
  survive without a reversible lookup table. (Google Cloud, xata, DEV)
- **A mapping table is itself reversible PII under GDPR.** Keeping `12345 → ab7x9`
  reintroduces the compliance catch; a keyed deterministic function avoids
  storing that mapping. (xata) → argues for the starter's **stateless hash**
  design over a persisted mapping.
- Google's "context tweak" = a per-type/context salt so the same raw value maps
  to different pseudonyms in different contexts when desired — the inverse of our
  requirement, but the mechanism (type/context in the hash input) is what keeps
  **distinct identities from colliding**.
- Techniques taxonomy (IRI): recoverable, unrecoverable, consistent/self-updating,
  deterministic. We want **unrecoverable + deterministic + consistent**.

## Implication for our implementation
- Keep `replacement_for` **stateless and deterministic**: `HMAC/SHA256(key,
  subject_id_or_rule_id : data_type)`. `subject_id` gives alias convergence;
  including `data_type` keeps per-type replacements distinct.
- Add a **collision guard**: distinct `(identity, type)` pairs must not produce
  the same rendered replacement. Widen the hash slice or detect+extend on
  collision; assert it in a test.
- Do **not** persist a mapping file in the release dir or logs (GDPR + brief:
  "keep replacement mappings out of the release directory and logs").
- A keyed function needs a **key source**: for the trial, a fixed/derived salt is
  fine (document it); in production the key lives in a KMS (see file 07).
