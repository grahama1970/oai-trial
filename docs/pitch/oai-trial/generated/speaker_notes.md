# Speaker notes — Verified Cross-Format Anonymization

Current seven-slide projection of `../deck.curated.yaml`; the earlier auto-plan
receipts describe the initial draft, not acceptance of this briefing.

## 1. The assignment
Open with the brief and the acceptance bar.

## 2. Architecture — one fail-closed path
Show the SVG; emphasise trust boundaries and report-last publication.

## 3. The hard semantics
Explain original-input matching, alias identity, bounded collision search, and
fail-closed overlap rejection.

## 4. Reliability and format hardening
Explain per-file materialization, strict comma CSV, typed JSON/SQLite per-row
verification, and report-last publication. The verifier shares matching
primitives with the transformer; it is a re-derivation, not a second implementation.

## 5. Evidence — and the extras
Show a concrete fail-before-fix regression. Scanner receipts are supporting
evidence only; Semgrep scanned no target files and no SCA receipt is committed.

## 6. Production scale (AWS reference)
Explain what stays and what changes at 1 TB / 1 PB. Use the estimator's current
output and per-unit price citations, not a remembered total. This is a modeled
scenario, not a deployment or throughput benchmark.

## 7. What this proves — and what it does not
Close on explicit non-claims: unlisted PII, re-identification resistance, and
TB/PB operation are not established. Keep future-work lanes out of the release.
