# Research adoption decision (from webgpt/PAPER-RESEARCH.md)

Maps the WebGPT arXiv brief against what is already implemented, then ranks the
few additions worth making. The brief's central thesis is correct and already
matches our design: **this is a verified deterministic pseudonymization + release
system, not an LLM anonymizer**, and re-identification resistance is a separate
claim we should not make.

## Already satisfied (brief P0 list ↔ our code)
| Brief feature | Our implementation |
|---|---|
| Strict policy validation | `policy.py compile_policy` (reject unknown/dup/non-literal/overlap/non-ASCII-CI) |
| Deterministic type-specific pseudonyms | `pseudonyms.py` (SHA256 over policy_version:data_type:identity) |
| Global collision + protected preflight | `build_replacements` domain-extension; `_check_overlap` |
| Original-span, non-cascading leftmost-longest matcher | `matcher.py` (Aho-Corasick) |
| Schema-aware adapters | `formats.py` (CSV/TXT/JSON/SQLite) |
| Bounded memory / size limits | streaming CSV/TXT; JSON depth+size bounds |
| Private same-fs staging + atomic publish | `pipeline.py` (mkdtemp → verify → os.replace) |
| Independent verifier (fresh reread, not transform booleans) | `verification.py` |
| report.json written last; sanitized | `pipeline.py`; closed `errors.py` vocabulary |
| Recovery from failure (staging cleanup, prior release intact) | `pipeline.py` finally + test |
| Docker contract + two-scale subprocess benchmark | `Dockerfile`, `__main__ _demo` |

## Adopt now — high ROI, small, fits the deterministic core
1. **Explicit non-claims in report.json + `docs/PRIVACY_CONTRACT.md`** (RAT-Bench,
   SPIA, "Why anonymization hasn't taken off"). Add a `does_not_establish` field
   and a versioned privacy contract (domain, protected unit, scope, adversary,
   excluded claims). Cheapest, highest credibility gain. *Partly present in
   README/SUBMISSION non-claims; make it machine-readable.*
2. **Subject-level coherence in the verifier** (SPIA). Today the verifier checks
   literal absence + file-set + protected counts; it enforces alias-convergence
   and distinctness only at compile time. Add an independent output check: all
   aliases of one subject converge to one pseudonym; distinct same-type subjects
   never share one. Real correctness depth.
3. **Independent structural fingerprints in the verifier**: row counts (CSV),
   topology/key order (JSON), schema hash (SQLite) recomputed by the verifier,
   not trusted from the adapter.
4. **Known-truth fixtures + verifier mutation tests** (DICOM validation work).
   Emit an expected-occurrence truth manifest (test-private) and add
   "verifier-sensitivity" tests that mutate a staged output (restore a literal,
   swap a pseudonym, drop a row) and prove the verifier rejects it.
5. **Bind `algorithm_version` + `scope_id` + `key_mode` into pseudonym derivation
   and report** (AnonShield, Proteus). One-line change to `pseudonyms.py`;
   documents the production HMAC/KMS scoping story and labels the local mode
   `public-deterministic-trial-namespace` (no secrecy claimed).
6. **A few property tests** (PBT-Bench/DiscPBT, via Hypothesis, dev-only dep):
   policy-permutation invariance, chunk-decomposition equivalence, rerun
   determinism, non-interference (adding an absent rule changes nothing).

## Production design — document, do not build in the 8h core
KMS-scoped HMAC keys + epoch rotation (Proteus); signed source manifest +
object-version binding; multiplicity-sensitive distributed digest (Proof-Gated
Publication); separate verifier account/IAM; residual-risk plane (subject-level +
quasi-identifier + agentic re-identification red-team — the 68%-recall LLM
deanonymization result); optional mapping vault; DP-SGD/canary for downstream ML;
FPE only when exact-domain reversibility is required. Most already sketched in
`docs/production-architecture.md`; the residual-risk plane is the main addition.

## Rejected from the deterministic core (brief agrees)
LLM rewriting; NER/Presidio as policy authority; agent/reviewer prose as release
proof; transformer self-verification; sampling verification; global stable
pseudonyms; random Faker values; per-record KMS calls; DP/FPE in the base
transform; naive byte partitioning; silent acceptance of unsupported
JSON/SQLite features.

## Recommendation
The shipped trial already covers the brief's deterministic P0 set. The four
cheapest, highest-credibility additions are (1) machine-readable non-claims +
privacy contract, (2) subject-level + structural verifier checks, (3) known-truth
fixtures + verifier mutation tests, (4) `algorithm_version`/`scope_id` binding.
The residual-risk plane and KMS scoping are production-plane and belong in a
follow-up (`[P1] subject-level + agentic re-identification risk evaluation`), not
the 8h submission.
