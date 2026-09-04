# Anonymization semantics (v1, frozen)

Authoritative correctness contract for the pipeline. Freezes the choices the
`TRIAL_BRIEF.md` leaves to the implementer. `GOAL.md` and `TRIAL_BRIEF.md` are
not weakened by this document. Resolves GitHub issue #2.

## 1. Canonical identity
The replacement identity of a rule is `(data_type, subject_id)`. When
`subject_id` is absent, use `(data_type, rule_id)`. Multiple literals sharing one
canonical identity are **aliases** and intentionally converge to the same
replacement.

## 2. Distinctness
Two different canonical identities of the **same** `data_type` must receive
**different** replacements. Bounded domains (phone suffixes: 10,000; IPv4 host
octet: 253) have a cardinality preflight: a policy naming more identities of a
bounded type than its domain can injectively hold is rejected up front with a
typed `namespace_exhausted` error, and the deterministic collision search is
bounded by the domain capacity. There is no domain extension.

## 3. Match against original input only
Matching runs against the **original decoded input**. Generated replacements are
**never** rescanned. This makes replacement-to-source cascades structurally
impossible.

## 4. Overlap precedence
When candidate spans overlap, selection is **leftmost-longest**, then a stable
`rule_id` tie-break. Emission is left-to-right over non-overlapping selected
spans.

## 5. Protected/sensitive overlap → REJECT (fail closed)
If any sensitive literal and any protected literal overlap **exactly, by
containment, or by partial intersection** (including case-folded overlap for
accepted case-insensitive rules), the **policy/corpus is rejected before
release** with a typed error. Rationale: "replace every sensitive value" and
"never change a protected value" are both unconditional; an overlap makes them
irreconcilable, so we refuse rather than silently violate one. (This supersedes
the earlier "protected wins" draft in `docs/research/03`.)

## 6. Case behavior
Case-sensitive matching compares exact Unicode code points. Case-insensitive
rules use **locale-independent ASCII case folding**; a non-ASCII literal with
`case_sensitive=false` is **rejected** in v1 (no full-Unicode/locale folding).

## 7. No Unicode normalization (matcher)
The matcher performs **no** Unicode normalization. Canonically equivalent
spellings match only when listed as separate policy literals. (Homoglyph/NFKC
folding may be used **only** as an independent verifier signal that can REJECT a
release — never to silently produce a match. See `docs/research/11`.)

## 8. Encoding
Accept UTF-8 and UTF-8-with-BOM; preserve whether a text-bearing file had a BOM.
Decode strictly; **reject** malformed or unsupported encodings before release
with a privacy-safe error (no raw excerpt).

CSV accepts comma-delimited records with double-quoted fields and doubled-quote
escaping. Semicolons, tabs, and pipes outside quoted fields are rejected across
the entire file, including data rows. Quote those characters when they are cell
content. This deliberately rejects ambiguous inputs rather than guessing a dialect.
Malformed quoting is rejected; multiline quoted fields remain supported.

## 9. Schema-bearing names are protected
Reject the corpus before release when a **selected sensitive literal** occurs in
a relative path, CSV header cell, JSON object key, SQLite table name, or SQLite
column name. Schema identifiers are never anonymized or renamed.

## 10. Release readiness marker
A release is committed only by a valid `report.json` written **last**, binding
the policy hash, corpus manifest digest, verification results, and aggregate
metrics. A corpus directory without that marker is **not ready** and must never
be described as ready.

## 11. Fail closed
Unknown formats, unsupported SQLite features, malformed data, invalid policy,
ambiguity, verification failure, or publication failure return **non-zero** and
leave **no** ready release (no partial corpus that looks releasable). Raw inputs,
replacement mappings, and quarantined content never appear in the release
directory or logs.

## Replacement domains (type-valid placeholders)
Deterministic pseudonyms derived from a versioned PRF/hash over
`(policy_version, data_type, canonical_identity)`:
- `name` → `Person-<hash>`
- `email` → `user-<hash>@example.invalid`
- `phone` → `+1-555-<NNNN>` (bounded domain: over-capacity policies rejected)
- `ip_address` → `198.51.100.<N>` (TEST-NET; N=1..253; bounded domain, exhausted searches or over-capacity policies rejected)
- `secret` → `[REDACTED-<hash>]`
- other → `anon-<type>-<hash>`
