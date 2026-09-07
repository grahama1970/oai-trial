# Visible-language clarification audit

Technical names remain in code anchors and detailed explanations. The visible slide adds their purpose; these changes do not add runtime capabilities.

| Slide | Before | After |
|---|---|---|
| r02-demo-result | Here is the result—not just a success flag | Run the anonymization demo |
| r02-demo-result | The four-format qualification fixture keeps one declared identity. | Apply declared replacements, check four formats, and write the completion report. |
| r03-demo-observations | Two recorded demo sizes, with a 10× logical-workload step. | Small test datasets show measured time, processing speed and memory use. |
| r04-docker | The required demo interface is preserved. | One container packages the engine and its runtime together. |
| r05-mounted-cli | The mounted command is the original evaluator contract. | Input: policy.json and a data folder. Output: transformed files and report.json. |
| r06-output-evidence | • Four logical formats read back | • Open and check CSV, JSON, text and SQLite output |
| r06-output-evidence | • Policy / source / corpus digests compared | • Compare hashes—the fingerprints of policy and data files |
| r06-output-evidence | • Early and late refusal; offline replay | • Reject bad input; repeat with networking disabled |
| r07-pipeline-map | Four high-level groups orient the code walkthrough. | Work on a private copy; check it before marking the output ready. |
| r08-policy | Explicit sensitive and protected lists | A literal is exact text supplied in the policy |
| r08-policy | A valid policy is not proof that its identity assignments are true. | Conservative literal-overlap rejection; context-scoped exceptions are not implemented. |
| r09-identity | Policy-declared identity—not inferred personhood. | Alice and A.L share a policy-assigned key—not inferred personhood. |
| r10-spans | Original spans only; generated text is never rematched. | Find matching text, choose non-overlapping segments, then replace once. |
| r11-formats | Preserve logical meaning—not identical serialization | Preserve data structure—not identical file bytes |
| r12-typed-locations | Verification checks location and scalar type. | Check each value’s type and its original row or field. |
| r13-publication | Technically READY under the declared transformation contract. | report.json is the completion marker; it is written last. |
| r15-capacity | The SLA is a scenario—not a benchmark | The completion target is modeled—not measured |
| r15-capacity | 200 workers × 20 MB/s is an assumed capacity model. | Estimate duration from worker count and assumed processing speed. |
| r16-cost | Compare components within a scenario—not across incomparable rows. | Storage cost depends on how much data is retained and for how long. |
| r17-disclosure | Public namespace; shared verifier primitives | No secret key; transformation and checks share some code |
| r21-answer-verifier | Fixture readback adds a separate, bounded oracle. | A separate checker compares known test outputs with expected results. |
