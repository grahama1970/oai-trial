# Battle–oai-trial acceptance integration v1 — immutable goal

> **Immutable goal:** One provider-independent oai-trial pre-submission command
> runs the frozen acceptance suite through pinned Battle code under an
> oai-trial-owned profile, verifies security and useful transformation behavior,
> produces independently checkable receipts, and exposes the same evaluation
> path to the production battle loop within the agreed per-commit budget.

Decided 2026-09-12 from the WebGPT advisory thread (conversation
`chatgpt.com/c/6aa4c1df-7e54-83ea-94f1-0164b2e73932`, tab 837436960).
Implementation order: **5 → 2 → 1 → 3 → 4** (goal first, profile ownership,
pinning, functional judge, production adapter). Missing or unimplemented
checks must FAIL, never skip.

## Acceptance criteria

| ID | Acceptance criterion | Deterministic check |
|---|---|---|
| **BSO-1: Bound semantics** | Executed evaluator code, runtime, profile, and case inventory are identified and enforced. | Advancing or dirtying the external checkout cannot change executed code. Corrupting the verified bundle, supplying a mismatched runtime, removing a required case, or giving an invalid overlay blocks execution with a receipt. |
| **BSO-2: Useful processing** | The frozen 39+13 suite passes with every expectation enforced and a positive, sensitive-value-bearing acceptance floor across all four formats. | Every accepted case passes both security and functional judges; every permitted rejection satisfies its verified rejection predicate and safe-output check. No missing functional checks, unsupported-oracle successes, or skipped mandatory cases. |
| **BSO-3: Qualified failure detection** | The judges and gate reject the specific failure classes this integration claims to address. | A frozen qualification manifest covers the retained historical leaks, BOM-less UTF-16, and functional corruptions: empty output, dropped/duplicated rows, changed protected content, collapsed identities, and inconsistent replacements. Each bad control fails for its intended reason; benign twins pass their applicable judge. Reject-everything, missing-judge, and judge-error tests also block campaign PASS. |
| **BSO-4: Shared execution and verifiable evidence** | Direct invocation and the production adapter use the same evaluator and preserve evidence. | Replay a fixed request through both entry paths and compare semantic results, excluding timing and caller metadata. An offline verifier recomputes artifact hashes, case/receipt correspondence, counts, and final verdict; removal or alteration of required evidence fails verification. One small fresh-Docker repeat checks stable replacement bindings. |
| **BSO-5: Bounded per-commit operation** | The integration remains provider-independent and close to current campaign cost. | Enforce the 52 primary case executions plus at most four small additional Docker executions, one build of the target under test, zero provider calls, and fixed fixture-size/time limits. Run retained-output qualification without target containers. At closure, require the five-run warm median on the same benchmark host to be no more than **1.25×** the recorded baseline. |

The timing criterion is a measured performance budget, not a claim that
wall-clock duration is deterministic; its calculation and threshold are fixed.
The other execution-count limits are deterministic. Qualification must be a
required gate dependency, bound to the current evaluator/runtime/profile/
control-manifest identities. A generic exception does not count as successful
detection of a leaking control.

## Explicitly outside this goal

Codec/homoglyph expansion, arbitrary-schema functional verification, a general
cross-project catalog service, live-provider discovery quality, and proof that
no further anonymization defects exist.
