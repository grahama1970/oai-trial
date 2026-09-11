# Requirements & representation matrix — DERIVED FROM THE BRIEF AND BUNDLE

Root-cause correction (2026-09-11): checks must be derived from TRIAL_BRIEF.md
and the delivered bundle (examples/policy.json, examples/policy.schema.json,
the four stated formats), NOT from what the code already does. Every hole that
lost the trial maps to a representation the brief + bundle explicitly admit.

## Requirements (each = a brief line)
| # | Requirement | Brief line |
|---|---|---|
| R1 | Produce valid output in the same logical format per input | 16 |
| R2 | Replace EVERY VALUE identified by the policy (value-scoped, any representation) | 16 |
| R3 | Stable replacements across files/runs; distinct identities distinct; aliases converge | 17 |
| R4 | Preserve protected values + meaning of non-sensitive data | 18, 33 |
| R5 | Preserve CSV headers/rows, JSON structure, SQLite tables/relationships/row counts/integrity | 19 |
| R6 | Verify the COMPLETE corpus before release | 20 |
| R7 | Keep raw inputs, mappings, quarantine out of release + logs | 21 |
| R8 | Exit non-zero after failure; no partial corpus that looks ready | 22 |
| R9 | Overlap precedence (nested/prefix/suffix/replacement-to-source; protected vs sensitive) | 40-44 |
| R10 | CSV header with sensitive literal: transform-with-mapping or reject; never silently retain | 42-44 |
| R11 | Encoding + normalization policy; reject malformed/unsupported; BOM, multibyte, locale-case | 46-49 |
| R12 | Identity coherence across files/formats/partitions/retries | 51 |
| R13 | Container demo: all 4 formats, 2+ sizes (10x), metrics, exit 0 only if verified | 69 |
| R14 | Mounted run: output only report.json + corpus | 92 |

## Representation universe (DERIVED FROM THE STATED FORMATS + BUNDLE)
Brief line 5: "contain CSV, JSON, UTF-8 text, and SQLite ... The same synthetic
identity can appear in EVERY format." R2 says replace every VALUE. So the value
universe is the union of what these formats admit:

| Format | Representations a VALUE can take | Source of truth |
|---|---|---|
| JSON | string, **integer**, **float**, scientific-notation, bool, null | JSON spec (RFC 8259) |
| SQLite | **TEXT, INTEGER, REAL, BLOB**, NULL | SQLite storage classes |
| CSV | quoted / unquoted cell (all text) | CSV (RFC 4180) |
| UTF-8 text | any Unicode; **NFC/NFD normalization**, BOM, multibyte | brief line 46-49 |

## Check matrix (requirement x representation) with status
| Representation | Required by | Check exists? | Status |
|---|---|---|---|
| JSON string | R2 | yes | pass |
| JSON integer | R2 (value-scoped) | yes (test_representation_class_holes / typed_pii) | FIXED fd80eca |
| JSON float | R2 | yes | FIXED fd80eca |
| JSON scientific notation | R2 | partial (parses to float, repr matched) | needs exact-decimal rule |
| SQLite TEXT | R2 | yes | pass |
| SQLite INTEGER | R2 | yes | FIXED fd80eca |
| SQLite REAL | R2 | yes | FIXED fd80eca |
| SQLite BLOB | R2 | yes (fail-closed) | FIXED 406aee4 |
| CSV quoted/unquoted | R2 | yes | pass |
| UTF-8 NFC vs NFD | R2 + R11 (normalization policy) | yes (xfail strict) | OPEN — proven leak |
| UTF-8 BOM | R11 | yes (probe) | pass |
| UTF-16 / invalid encoding | R11 (reject) | yes (probe) | pass (fail-closed) |
| protected value as INTEGER/REAL/NFC-variant | R4 | NO | MISSING |
| identity coherence across all 4 formats | R12 | partial | needs cross-format check |

## The lesson made mechanical
The representation column is NOT invented — it is the closed set each stated
format admits. Deriving checks from the brief+bundle means: for every
(requirement that touches a value) x (representation its format admits), a
fail-capable check must exist. Missing rows above are the remaining work; each
was derivable from the brief on day one.
