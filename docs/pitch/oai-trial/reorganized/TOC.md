# Table of Contents

**30 minutes prepared, including code navigation. Separate 15+ minutes audience discussion.**

1. **Demo and Results**
   - Run the prepared example and inspect real output; explicitly label any recorded fallback
   - Observed timing, throughput and memory
2. **Reproduce and Verify**
   - Supported setup and Docker
   - Actual CLI and input/output locations
   - Independent output checks and evidence boundaries
3. **How the Solution Works**
   - Compact pipeline map
   - Policy → identity → original spans → formats → verification → publication
   - Required production design, capacity/SLA and modeled costs
   - Limits and timebox disclosure
4. **Why These Choices? — Prepared Adversarial Questions**
   - Exact policy rather than automatic detection
   - A verifier with shared primitives
   - Petabyte execution and what the model establishes
5. **Extra Credit**
   - Security Evals (White, Grey, Black, and Adaptive Lineage)
   - Thin skill wrapper: concise contract, delegation and retained checks
   - Reviewed name aliases and corrected artifact path boundary
6. **Discussion**
   - Audience questions and follow-ups; not prepared objection handling
7. **Thank you**

The first playback slide is Table of Contents. The wrapper receives only the prescribed one-sentence mention immediately before a live demo; features and reuse rationale stay in Extra Credit. Extra Credit is the last substantive prepared block. Thank you is the final playback slide. The question bank is not appended to deck.public.yaml.

## Expanded hierarchy for human review

### Contents

- `r01-toc` — **Table of Contents** — 00:00–00:45
  - 30 minutes prepared · 15+ minutes audience discussion

### Demo and Results

- `r02-demo-result` — **Here is the result—not just a success flag** — 00:45–02:15
  - Same prepared fixture; live action after preflight or clearly labeled recorded fallback. No introductory skill slide.
- `r03-demo-observations` — **Small workloads were measured; petabytes were not** — 02:15–03:15
  - Two recorded demo sizes, with a 10× logical-workload step.

### Reproduce and Verify

- `r04-docker` — **The evaluator needs one self-contained image** — 03:15–04:15
  - The required demo interface is preserved.
- `r05-mounted-cli` — **One bundle in; one dedicated release directory out** — 04:15–05:30
  - The mounted command is the original evaluator contract.
- `r06-output-evidence` — **Check the artifacts, not the exit code** — 05:30–07:00
  - The qualification oracle is outside the runtime verifier.

### How the Solution Works

- `r07-pipeline-map` — **Transformation and release are separate steps** — 07:00–07:45
  - Four high-level groups orient the code walkthrough.
- `r08-policy` — **The policy supplies authority—not a guess** — 07:45–09:00
  - Contradictory sensitive and protected obligations reject.
- `r09-identity` — **Aliases converge because identity is declared** — 09:00–10:45
  - One type/identity pair produces one allocated replacement.
- `r10-spans` — **Select original spans; emit only once** — 10:45–12:15
  - The matcher never rematches its own replacements.
- `r11-formats` — **Preserve logical meaning—not identical serialization** — 12:15–13:30
  - Adapters own the supported format boundaries.
- `r12-typed-locations` — **A correct value on the wrong row is still wrong** — 13:30–15:00
  - Verification checks location and scalar type.
- `r13-publication` — **The marker—not the directory—authorizes use** — 15:00–16:30
  - Write the complete report, then rename it last.
- `r14-cloud` — **Distribute the work; retain one corpus decision** — 16:30–18:00
  - Required production design: AWS, not a deployed extension.
- `r15-capacity` — **The SLA is a scenario—not a benchmark** — 18:00–19:00
  - 200 workers × 20 MB/s is an assumed capacity model.
- `r16-cost` — **Retention dominates this 1 PB cost scenario** — 19:00–20:15
  - Compare components within a scenario—not across incomparable rows.
- `r17-disclosure` — **Technical readiness does not waive the timebox** — 20:15–21:00
  - The bounded implementation and the overrun are both disclosed.

### Prepared Adversarial Questions

- `r18-question-exact` — **Question 1** — 21:00–21:15
  - Why exact policy instead of automatic detection?
- `r19-answer-exact` — **Explicit policy separates authority from guessing** — 21:15–22:00
  - Exact transformation is auditable; detection completeness is a separate claim.
- `r20-question-verifier` — **Question 2** — 22:00–22:15
  - How independent is a verifier that shares primitives?
- `r21-answer-verifier` — **Rereading helps; common-mode risk remains** — 22:15–23:00
  - Output mutations are checked independently of transform success flags.
- `r22-question-scale` — **Question 3** — 23:00–23:15
  - What changes at petabyte scale—and what does the model prove?
- `r23-answer-scale` — **The model exposes assumptions; it does not validate them** — 23:15–24:00
  - Distribution must preserve identity and release semantics.

### Extra Credit

- `r24-security-evals` — **Security evals test different failure surfaces** — 24:00–25:15
  - Extra Credit · white/gray/black-box methodology
- `r25-lineage` — **The retained Judge result is fixture-backed** — 25:15–26:00
  - Adaptive lineage is not established by this demonstration.
- `r26-wrapper` — **The skill delegates; it does not fork the engine** — 26:00–27:00
  - Extra Credit · reuse a concise SKILL.md, thin run.sh, and retained behavior checks.
- `r27-discovery` — **A proposed alias does not authorize release** — 27:00–28:30
  - Extra Credit · propose → approve IDs → exact policy → verify
- `r28-canonical-path` — **Validate the destination that will actually be written** — 28:30–30:00
  - The final path fix closes relative and symlink aliases.

### Discussion

- `r29-discussion` — **Discussion** — 30:00–45:00+ audience reserve
  - Your questions—not more prepared objections.

### Thank you

- `r30-thank-you` — **Thank you** — After discussion; end playback
  - End normal playback.

