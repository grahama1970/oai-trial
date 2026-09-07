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
   - Research with $dogpile; inspect existing projects and skills; reuse before custom code
   - Concrete research-to-code adaptations
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

- `r06a-research-reuse` — **Research first; reuse before custom code** — 07:00–08:00
  - Understand the contract before choosing an implementation.
- `r06b-research-adoption` — **Research changed checks—not just citations** — 08:00–09:00
  - Three adaptations you can inspect in the code.
- `r07-pipeline-map` — **Transformation and release are separate steps** — 09:00–09:45
  - Four high-level groups orient the code walkthrough.
- `r08-policy` — **The policy supplies authority—not a guess** — 09:45–11:00
  - Contradictory sensitive and protected obligations reject.
- `r09-identity` — **Aliases converge because identity is declared** — 11:00–12:15
  - One type/identity pair produces one allocated replacement.
- `r10-spans` — **Select original spans; emit only once** — 12:15–13:45
  - The matcher never rematches its own replacements.
- `r11-formats` — **Preserve logical meaning—not identical serialization** — 13:45–15:00
  - Adapters own the supported format boundaries.
- `r12-typed-locations` — **A correct value on the wrong row is still wrong** — 15:00–16:30
  - Verification checks location and scalar type.
- `r13-publication` — **The marker—not the directory—authorizes use** — 16:30–18:00
  - Write the complete report, then rename it last.
- `r14-cloud` — **Distribute the work; retain one corpus decision** — 18:00–19:30
  - Required production design: AWS, not a deployed extension.
- `r15-capacity` — **The SLA is a scenario—not a benchmark** — 19:30–20:30
  - 200 workers × 20 MB/s is an assumed capacity model.
- `r16-cost` — **Retention dominates this 1 PB cost scenario** — 20:30–21:15
  - Compare components within a scenario—not across incomparable rows.
- `r17-disclosure` — **Effort estimate and implementation limits** — 21:15–22:00
  - Estimated effort: about 8 hours—3 research, 2 implementation/testing, 1 extras, 2 polish.

### Prepared Adversarial Questions

- `r18-question-exact` — **Question 1** — 22:00–22:15
  - Why exact policy instead of automatic detection?
- `r19-answer-exact` — **Explicit policy separates authority from guessing** — 22:15–23:00
  - Exact transformation is auditable; detection completeness is a separate claim.
- `r20-question-verifier` — **Question 2** — 23:00–23:15
  - How independent is a verifier that shares primitives?
- `r21-answer-verifier` — **Rereading helps; common-mode risk remains** — 23:15–24:00
  - Output mutations are checked independently of transform success flags.
- `r22-question-scale` — **Question 3** — 24:00–24:15
  - What changes at petabyte scale—and what does the model prove?
- `r23-answer-scale` — **The model exposes assumptions; it does not validate them** — 24:15–25:00
  - Distribution must preserve identity and release semantics.

### Extra Credit

- `r24-security-evals` — **Security evals test different failure surfaces** — 25:00–26:15
  - Extra Credit · white/gray/black-box methodology
- `r25-lineage` — **The retained Judge result is fixture-backed** — 26:15–27:00
  - Adaptive lineage is not established by this demonstration.
- `r26-wrapper` — **The skill delegates; it does not fork the engine** — 27:00–28:00
  - Extra Credit · reuse a concise SKILL.md, thin run.sh, and retained behavior checks.
- `r27-discovery` — **A proposed alias does not authorize release** — 28:00–29:00
  - Extra Credit · propose → approve IDs → exact policy → verify
- `r28-canonical-path` — **Validate the destination that will actually be written** — 29:00–30:00
  - The final path fix closes relative and symlink aliases.

### Discussion

- `r29-discussion` — **Discussion** — 30:00–45:00+ audience reserve
  - Your questions—not more prepared objections.

### Thank you

- `r30-thank-you` — **Thank you** — After discussion; end playback
  - End normal playback.

