# Representation-class hole audit (2026-09-11, WebGPT-audited)

The typed-PII disqualifier (a phone stored as a JSON/SQLite integer passing
through untouched) was one instance of a failure CLASS: *the same sensitive
value appears in a representation the matcher does not canonicalize, and the
verifier shares the same blind spot, so nothing fails closed.*

Every axis below was tested empirically against the real pipeline. Independent
audit by WebGPT confirmed the scope split and the ranking.

## Governing invariant (adopt)
Every representation accepted at the input boundary must end in exactly one of
three states: supported-and-scanned, explicitly protected, or rejected. There
is no accepted-but-opaque fourth state. And: for every canonicalization the
transform performs, qualification must contain a fault case where that behavior
is disabled and the independent verifier rejects the output.

## Status

| Axis | Verdict | Status |
|---|---|---|
| Numeric scalar (int/float) | P0 same-class | FIXED + Docker-verified (fd80eca) |
| SQLite BLOB passthrough | P0 same-class | FIXED - fail-closed (this change) |
| JSON \uXXXX escape equivalence | P0 if present | Already correct (JSON parsed, decoded form matched) |
| UTF-16 / invalid encoding | P0 boundary | Already correct (malformed_encoding, fail-closed) |
| UTF-8 BOM | P0 boundary | Already correct (matched, BOM preserved) |
| NFC/NFD canonical equivalence | P0 same-class | FIXED - NFC/NFD variant patterns + NFC-folded policy collision + independent NFC verifier (3ca4ad7); Docker-verified |
| Numeric precision / scientific notation | P0 refinement | Partial (int/float ok); exact-decimal + precision-boundary rule pending |
| Policy-side canonical collisions | P0 | Pending (normalize policy literals + reject NFC collisions) |
| Verifier protected-value scalar coverage | P1 | Pending |
| Cross-format identity coherence | P1 | Pending |
| Chunk-boundary matching | P1 if streamed | Pending (confirm whole-scalar processing) |
| Formatting (dashes), zero-width, NBSP, fullwidth | NOT a hole under literal scope | Documented; negative-scope test guards against creep |
| base64 / hex / URL / entity encoding, split-across-cells | NOT a hole | Out of scope by literal + value-scoped contract |

## Required correct NFC fix (do not stub)
- NFC-normalize the match view AND policy literals (NFC, NOT NFKC).
- Offset-safe: NFC is not length-preserving; map offsets back to original
  bytes, or register NFC+NFD literal variants as patterns.
- Preflight the policy: reject two entries that NFC-collide with conflicting
  identity/replacement/protected semantics.
- Independent verifier NFC path (not the transform's helper) + a fault test:
  disable transform NFC -> verifier must reject.

## Claim surface (rewrite; never overclaim)
Not "no PII reaches the output." Instead: "For supported inputs, every
policy-identified value is removed or replaced across CSV, JSON, UTF-8 text,
and supported SQLite scalar values. Text literals compare under Unicode NFC and
the documented case policy; supported numeric scalars use the documented exact
canonical representation. Unsupported encodings, storage classes (including
BLOB), and ambiguous scalar representations fail closed. No semantic PII
discovery, compatibility folding, whitespace/punctuation normalization, or
decoding of base64/hex/embedded payloads."
