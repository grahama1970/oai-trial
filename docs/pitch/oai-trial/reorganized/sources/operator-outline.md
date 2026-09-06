# OAI trial: proposed presentation organization

Status: human-review proposal. The deck has not yet been reorganized and no new
WebGPT reorganization request has been submitted. This revision preserves the
prepared adversarial-question block explicitly rather than folding it into
technical detail or audience discussion.

## Fixed instructions

- First slide: **Table of Contents**. No cover or demo precedes it.
- Then show the working demo and the actual result before explaining internals.
- Prepared narrative: **30 minutes**, including code navigation; reserve another
  **15+ minutes** for audience discussion.
- One concept per detail slide. Four concepts is a ceiling, not a target.
- Prepared adversarial questions explain and defend the choices **before Extra Credit**.
- Extra Credit is the last substantive prepared block.
- Audience slide: **Discussion**. Final slide: **Thank you.**
- Preserve evidence qualifiers, code references, and Q01–Q48. No runtime changes.

## Proposed Table of Contents

1. **Demo and Results**
   - Let's run it
   - Here is the result: changed values and preserved meaning
2. **Reproduce and Verify**
   - Exact CLI invocation and input/output locations
   - Supported setup and Docker environment
   - Verification command, output evidence, and limitations
3. **How the Solution Works**
   - Compact pipeline orientation
   - Code walkthrough: one concept per slide
     - Validate policy and input boundaries
     - Assign identity-coherent pseudonyms
     - Resolve original-input spans without cascades
     - Transform the supported formats
     - Verify values, types, structure, and location
     - Seal and publish the verified corpus
   - Production design, capacity, SLA, and cost assumptions
4. **Why These Choices? — Prepared Adversarial Questions**
   - Why exact-policy matching rather than automatic PII detection?
   - How independent is a verifier that shares replacement primitives?
   - What changes at petabyte scale, and what does the cost model actually prove?
5. **Extra Credit**
   - **Security Evals (White, Grey, Black, and Adaptive Lineage)**
   - Thin `anonymize-data` skill wrapper
   - Explicitly reviewed name-alias discovery
6. **Discussion**
   - Audience questions and follow-ups
7. **Thank you.**

The explicit prepared-question section renumbers the later TOC entries; the
requested audience label remains Discussion. This is a proposal for human review,
not permission to silently remove the prepared questions to retain old numbering.

## Prepared-question block: one question per slide

Use a visible question, a short answer/decision, and one concrete piece of code
or evidence. Do not read the whole 48-question appendix aloud.

| Proposed slide | Decision and qualification to explain | Existing question/evidence handles |
|---|---|---|
| Why exact-policy matching? | Explicit policy supplies authority; broad detection is a separate problem. Optional discovery does not silently authorize replacement. | Q01–Q03, Q19–Q21; `policy.py::compile_policy`, `discovery.py::approve` |
| Can the verifier share code? | Rereading and location/type checks catch output faults, but shared primitives leave common-mode risk. Independent qualification checks have a bounded fixture scope. | Q04, Q12, Q22–Q23, Q37; `verification.py::verify_corpus`, `_typed_equal`, `qualify_submission.py::readback` |
| What changes at petabyte scale? | Local per-file processing is not a production benchmark. Distribution must preserve a common identity plan; costs depend on workload and quota assumptions. | Q24–Q27, Q47; `pseudonyms.py::build_replacements`, `estimate_aws_cost.py::_one`, production design |

The last prepared-question slide must lead into Extra Credit. No new substantive
prepared block follows Extra Credit; backup material is outside normal playback.

## Graham reference study

The actual supplied PPTX packages were inspected in
`ARTIFACT_ROOT/skills/pitchdeck/sources/style-corpus/`. Layout discovery used
`pitchdeck/run.sh find-layout`. Selected existing renders were viewed through
live Surf pages; source text was checked against the PPTX presentation order.

- **ACERT_Darpa_PI_Meeting_FtWorth, slide 1:** hierarchical Table of Contents,
  including indented subtopics and separate questions/deeper-dive entries.
- **SpartaAI_CyberSummitv_v3, slide 12:** an orientation page headed
  “How ACERT Works,” rather than all implementation detail on one canvas.
- **SpartaAI_CyberSummitv_v3, slides 52–53:** a distinct question page followed by
  a distinct answer/assertion page. This is the useful pattern for defending a
  choice; it is not merely another generic topic bullet.
- **SpartaAI_CyberSummitv_v3, slides 58–59:** separate Open Discussion and Thank You.

These are presentation-structure references, not evidence for oai-trial technical
claims. Historical product claims, sponsorship/distribution labels, and images
must not be transplanted into this public deck. The reference images remain
presenter-local, not in the public repository. The current grahama.co theme
request remains separate from the historical teal/white references.

Reference-study artifacts:
`ARTIFACT_ROOT/oai-trial/deck-authoring/house-study/`

## Detail-slide and evidence rules

Map each pipeline-detail slide to the actual file, function, and checked line
range. Source navigation/highlighting is not a breakpoint or a paused frame.
Run, Inspect, Step, Continue, and Stop remain explicit actions.

Core correctness checks belong in Reproduce and Verify. The additional security
methodology belongs in Extra Credit. Its detail slides must distinguish the
retained white/gray/black-box evidence from the fixture-backed Judge demonstration;
a live adaptive campaign against this project is not established.

Production architecture and cost modeling were required by the brief, so they
are not extra credit. Additional capability claims require their own evidence.

## Visual and ownership boundaries

Use the requested grahama.co brand direction and the supported pitchdeck theme
interface. The header requirement is an actual low-opacity image overlay, not
just translucent fill; the theme worker reports the supplied house-band image at
10% opacity over a separately controlled fill. Check that behavior when applied
rather than treating this instruction as a visual proof.

Preserve intended animation in the browser and separate it from fixed PPTX/PDF
geometry. Reading beside VS Code must not be confused with shrinking a full slide.
Do not edit shared agent-skills/pitchdeck implementation files concurrently with
its owner. Keep all narrative and source mappings in the oai-trial project.
