# Academic grounding (arXiv)

Retrieved via the arXiv API on 2026-09-04 (titles/ids verified; abstracts not yet
fully read — proof boundary).

## Format-preserving encryption
- **Practical Solutions For Format-Preserving Encryption** — http://arxiv.org/abs/1506.04113
- Privacy Protection of Automotive Location Data Based on FPE of Geographical Coordinates — http://arxiv.org/abs/2510.20300
- eFPE: Lightweight Format-Preserving Encryption for Embedded Systems — http://arxiv.org/abs/2511.12225

Relevance: backs the optional FF3-1 format-preserving mode (phone/email/id keep a
valid-looking shape). NIST SP 800-38G is the normative reference.

## Differential privacy (production tradeoffs)
- **Differential Privacy Overview and Fundamental Techniques** — http://arxiv.org/abs/2411.04710
- Gaussian Differential Privacy (rejoinder) — http://arxiv.org/abs/2104.01987

Relevance: SUBMISSION "production design" should state why we do *deterministic
pseudonymization* (referential integrity, format parity) rather than DP
(aggregate release with a privacy budget) — different guarantees; our task
requires per-value replacement with preserved structure, not statistical release.

## k-anonymity / t-closeness (re-identification risk)
- Distribution-Preserving k-Anonymity — http://arxiv.org/abs/1711.01514
- kt-Safety: Graph Release via k-Anonymity and t-Closeness — http://arxiv.org/abs/2210.17479

Relevance: names the residual risk our approach does *not* solve — pseudonymizing
identifiers doesn't prevent re-identification from quasi-identifier combinations.
A one-paragraph "known limitation" in SUBMISSION should cite this.

## Referential integrity mechanics
- Hashing with Linear Probing and Referential Integrity — http://arxiv.org/abs/1808.04602

Relevance: background for the deterministic-hash → stable-pseudonym design that
preserves cross-table/file relationships without a mapping table.

## Recent / cutting-edge (2026, sorted by submission date)
Retrieved 2026-09-04 via arXiv API `sortBy=submittedDate`. Titles/ids verified;
abstracts not fully read (proof boundary). These bound the *known-limitations*
and *evaluation* narrative for SUBMISSION.md — our task is deterministic
literal replacement from a supplied policy, so detection-quality papers are
context for the optional discovery boundary, not the core runtime.

- **Mind the Gap: Robustness Risks in PII Detection Systems** (2026-09-03) — http://arxiv.org/abs/2609.03464
  Why detection-based redaction is fragile → supports our choice of *policy-
  supplied literals + deterministic replacement* over NLP detection at runtime.
- **REDACT: A Systematically Controlled Multilingual Benchmark for Personal Information Detection** (2026-06-18) — http://arxiv.org/abs/2606.19881
  Benchmark framing for the design-time discovery/reviewer tier.
- **Institution-Specific LLM Prompting Recovers PHI That De-identification Systems and Their Gold Standards Both Miss** (2026-08-17) — http://arxiv.org/abs/2608.17051
  Direct evidence for the residual re-identification risk our approach does not
  solve — cite as a known limitation alongside k-anonymity.
- **Redakto — The Incognito Tab for LLMs** (2026-08-18) — http://arxiv.org/abs/2608.18260
  Contemporary redaction-pipeline framing; contrast with our offline
  deterministic container.
- **ToolMinimize: Auditing and Rewriting LLM Agent Tool Calls to Minimize Privacy Exposure** (2026-08-25) — http://arxiv.org/abs/2608.24957
  Tokenize→untokenize referential-integrity pattern (matches the reuse-audit
  `pii-tokenization` idea).
- **LLMs as strategy designers for privacy-preserving tabular data synthesis** (2026-08-30) — http://arxiv.org/abs/2608.29674
  Production-design enrichment: LLM proposes strategy, deterministic code
  executes — mirrors our Tier-2/design-time cascade boundary.
- **SynthGuard-ReleaseBench: Locked-Audit Evidence for Synthetic Tabular Data Releases** (2026-08-14) — http://arxiv.org/abs/2608.14753
  "Locked-audit evidence" for safe release — supports the fail-closed atomic
  publish + verification-receipt design (files 05, 11).
