# Overlap precedence, protected values, encoding/BOM

## Requirement (brief)
Deterministic precedence that prevents replacement cascades (nested,
prefix/suffix, replacement-to-source overlaps). Protected values must not change,
even when they overlap/contain/intersect a sensitive literal. CSV header with a
sensitive literal: transform (with schema mapping) or reject — never silently
retain. UTF-8 contract; reject malformed/unsupported encodings safely; document
BOM, multibyte, locale-sensitive case.

## Sources
- Python bug 7185 — csv reader UTF-8 BOM: https://bugs.python.org/issue7185
- FlipperFile — CSV BOM (U+FEFF) garbles first header: https://flipperfile.com/text-guides/csv-encoding-issues/
- ConvertToCSV — one malformed record corrupts the output; set encoding at every step: https://converttocsv.com/blog/csv-encoding-issues/
- FastCSV — strict vs lenient unclosed-quote handling: https://fastcsv.org/architecture/interpretation/
- Google Cloud pseudonymization (surrogate annotation / precedence context): https://docs.cloud.google.com/sensitive-data-protection/docs/pseudonymization

## Key findings
- **Replacement cascades are the core correctness bug.** Naive per-rule
  `str.replace` in arbitrary order can (a) re-match a substring of an earlier
  replacement, or (b) let a short literal corrupt a longer one. Fixes:
  - **Longest-match-first**: sort rules by descending `len(value)` so the most
    specific literal wins.
  - **Single-pass, non-overlapping**: build one combined matcher
    (e.g. alternation / Aho-Corasick), scan left-to-right, and **never re-scan
    already-emitted replacement text**. This is the deterministic precedence the
    brief asks for.
- **Protected values dominate.** Compute protected spans first; a sensitive match
  overlapping a protected span is suppressed (protected wins). Document exact/
  contained/partial-overlap behavior explicitly.
- **CSV header BOM:** U+FEFF on the first field turns `Name` into `\ufeffName`,
  breaking header-keyed logic (Python 3.12 bug 7185; FlipperFile). Read with
  `encoding="utf-8-sig"` to strip a leading BOM deterministically, and record
  whether a BOM was present.
- **Headers are data too.** Starter skips row 0, so a sensitive literal in a
  header is silently retained — explicitly unsafe per brief. Either transform the
  header (and carry a documented schema mapping) or reject the file before release.
- **Malformed input must fail closed.** "One malformed record can corrupt an
  entire output file." Decode strictly; on `UnicodeDecodeError` quarantine the file
  with a sanitized message rather than emitting partial output. (ConvertToCSV)
- **Quote/newline handling:** use the `csv` module (handles embedded newlines and
  quoting); don't hand-split. Decide strict vs lenient unclosed-quote behavior and
  document it (FastCSV shows the tradeoff).
- **Locale-sensitive case:** `case_sensitive=false` needs Unicode casefold, not
  locale `.lower()`, to be deterministic across environments.

## Implication for our implementation
- Replace `replace_text` with a **single left-to-right pass** over a combined,
  longest-first matcher; protected spans masked out first; emitted replacement text
  never re-scanned.
- Read text/CSV with `utf-8-sig`; decode strictly; quarantine on decode error.
- Treat CSV header cells through the same matcher; if a header would change,
  record a schema mapping in the (sanitized) report; if policy says reject, fail
  closed.
- Use `str.casefold()` for case-insensitive rules.
- **Candidate for a reusable `best-practices-data-anonymization` skill.**
