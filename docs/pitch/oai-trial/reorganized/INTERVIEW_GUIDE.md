# Interview guide — prepared rehearsal, not an interview record

**Candidate update from `ecfaaaac2cc7844bd0e52fd7d2bbf3abab36ab78`.** The anonymizer remains frozen at `0375af56bf681e9441edcb7433cfe58951db77b2`. “Interview” here means rehearsal instructions, not a transcript of a conversation that occurred.

[Full spoken walkthrough](WALKTHROUGH.md) · [Opening contents](TOC.md) · [48-question appendix](WALKTHROUGH.md#adversarial-question-bank) · [Primary question map](question-map.json) · [Slide/code map](slide-map.json)

## Keep the existing clock

There are **28 prepared slides totaling 30 minutes including navigation**, then a separate **15+ minute Discussion** and **Thank you**. No introductory skill slide is added. The original primary question mappings and all short/deeper answers are unchanged. No backup material follows Thank you in normal playback.

| Prepared block | Time | Navigation |
|---|---|---|
| Contents | 00:00–00:45 | [r01](WALKTHROUGH.md#r01-toc) |
| Demo and results | 00:45–03:15 | [r02 action/result](WALKTHROUGH.md#r02-demo-result), [r03 historical metrics](WALKTHROUGH.md#r03-demo-observations) |
| Reproduce and verify | 03:15–07:00 | [Docker](WALKTHROUGH.md#r04-docker), [mounted CLI](WALKTHROUGH.md#r05-mounted-cli), [readback evidence](WALKTHROUGH.md#r06-output-evidence) |
| Core code and required cloud model | 07:00–21:00 | [pipeline](WALKTHROUGH.md#r07-pipeline-map) through [disclosure](WALKTHROUGH.md#r17-disclosure) |
| Three prepared Question → Answer pairs | 21:00–24:00 | [exact policy](WALKTHROUGH.md#r18-question-exact), [shared verifier](WALKTHROUGH.md#r20-question-verifier), [scale](WALKTHROUGH.md#r22-question-scale) |
| Extra Credit, last substantive block | 24:00–30:00 | [Security Evals](WALKTHROUGH.md#r24-security-evals), [lineage](WALKTHROUGH.md#r25-lineage), [wrapper](WALKTHROUGH.md#r26-wrapper), [aliases](WALKTHROUGH.md#r27-discovery), [path boundary](WALKTHROUGH.md#r28-canonical-path) |
| Audience discussion | 30:00–45:00+ | [Discussion](WALKTHROUGH.md#r29-discussion), then [Thank you](WALKTHROUGH.md#r30-thank-you) |

<a id="preflight"></a>
## Preflight before playback — presenter checklist, not executed here

Resolve `ANONYMIZE`, `ANONYMIZE_DATA_ROOT`, `INPUT`, and `OUTPUT` to the existing tested wrapper, the frozen project checkout, the prepared synthetic qualification bundle, and a dedicated empty output directory. These are operator paths, not normalized receipt labels to open. Use the primary checkout on `main`. Later documentation commits are allowed; verify the runtime files still match `0375af56bf681e9441edcb7433cfe58951db77b2` rather than switching branches or requiring HEAD to equal the old commit. The wrapper also checks its installed package location.

Before rehearsal, from the primary project checkout:

```bash
git diff --exit-code 0375af56bf681e9441edcb7433cfe58951db77b2 -- \
  src/anonymization_trial schemas pyproject.toml uv.lock Dockerfile .dockerignore \
  scripts/qualify_submission.py
```

A non-zero diff requires review; it is not permission to reset or switch the checkout.

The running example remains Alice and A.L → person-a, Bob → person-b, with KEEP and typed non-sensitive values. Prepare it and any independent readback before the presentation using the existing workflow; do not create new code or install packages on stage. Establish that the example contains all four formats, including the known SQLite `sqliteX` case, and that OUTPUT does not overlap the source or private work.

Run the existing preflight before the session, not as a new timed introductory lecture:

```bash
"$ANONYMIZE" preflight --input "$INPUT"
```

A successful preflight is not a transformed release. Prepare a trusted view of actual output and the [existing fixture readback](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/qualify_submission.py#L80-L134). Open the [historical qualification](sources/qualification.json) as a fallback. Do not run `qualify_submission.py` during the talk: it clones main and requires equality with its invoking HEAD, rather than accepting any historical ref.

<a id="demo-decision"></a>
## The demo decision — same 90-second r02 slot

**Live branch:** immediately before the prepared command, say exactly this one sentence:

> I’m using a thin skill wrapper around the project’s CLI; the same engine runs independently in Docker.

Then act; do not add a skill explanation:

```bash
"$ANONYMIZE" run --input "$INPUT" --output "$OUTPUT" &&
  "$ANONYMIZE" verify --input "$INPUT" --output "$OUTPUT"
```

Inspect the real `report.json`, output inventory and generated values. Check alias association, protected KEEP, JSON scalar types and SQLite rows; use the existing prepared readback rather than inventing an oracle on stage. Only describe checks actually completed. A `verify`/`inspect` status is not report authentication, a screenshot, or proof that a separate readback ran.

**Fallback branch:** say, “I’m using the recorded qualification fallback, not a live result.” If an attempted live command failed or was stopped, disclose that first. Open the historical receipt and the checker-derived reference illustration. Do not deliver live-success language or silently use stale OUTPUT. Do not troubleshoot, install or consume the discussion reserve to finish the demo.

**Either branch:** r03 remains historical. Say the recorded `1000 / 100 = 10` workload derivation; timing/memory figures belong to the retained receipt, not the command just attempted. The figure is not a terminal capture. A measured live result needs its own evidence; this package manufactures none.

## Rehearse decisions, not a memorized defense

Use one answer plus one evidence jump. The three prepared objections already have their own Question → Answer pairs and visible qualifiers. All other deeper answers belong in the audience reserve. Keep the pause/navigation inside each slide’s allocation; shorten optional inspection rather than extending the prepared talk.

| Challenge to practice | Preserved answer links |
|---|---|
| Policy authority and incomplete discovery | [Q01](WALKTHROUGH.md#q01), [Q02](WALKTHROUGH.md#q02), [Q03](WALKTHROUGH.md#q03), [Q33](WALKTHROUGH.md#q33) |
| Identity, policy changes and no cascades | [Q07](WALKTHROUGH.md#q07), [Q08](WALKTHROUGH.md#q08), [Q10](WALKTHROUGH.md#q10), [Q31](WALKTHROUGH.md#q31), [Q32](WALKTHROUGH.md#q32) |
| Located/type checks and shared primitives | [Q04](WALKTHROUGH.md#q04), [Q12](WALKTHROUGH.md#q12), [Q37](WALKTHROUGH.md#q37), [Q38](WALKTHROUGH.md#q38) |
| Report-last, path boundary and actual evidence | [Q13](WALKTHROUGH.md#q13), [Q15](WALKTHROUGH.md#q15), [Q18](WALKTHROUGH.md#q18), [Q22](WALKTHROUGH.md#q22), [Q45](WALKTHROUGH.md#q45) |
| Cloud scenario versus measured performance | [Q24](WALKTHROUGH.md#q24), [Q25](WALKTHROUGH.md#q25), [Q26](WALKTHROUGH.md#q26), [Q47](WALKTHROUGH.md#q47) |
| Extra Credit: reuse and reviewed proposals | [Q06](WALKTHROUGH.md#q06), [Q19](WALKTHROUGH.md#q19), [Q20](WALKTHROUGH.md#q20), [Q21](WALKTHROUGH.md#q21), [Q34](WALKTHROUGH.md#q34), [Q35](WALKTHROUGH.md#q35) |
| Timebox, authorship and permissions | [Q28](WALKTHROUGH.md#q28), [Q29](WALKTHROUGH.md#q29), [Q30](WALKTHROUGH.md#q30), [Q48](WALKTHROUGH.md#q48) |

The rest of Q01–Q48 remain in the complete appendix, with unchanged answers and primary-slide relationships. For an unverified case, explain the boundary and the evidence needed; do not improvise certainty.

## Extra Credit discipline

Only r26 explains why a workflow merits a reusable skill: concise SKILL.md contract, thin run.sh delegation, and retained behavioral checks. The native rows are a design explanation, not blanket proof of `best-practices-skills` compliance. No live building or installation is planned.

Keep the exact TOC label **Security Evals (White, Grey, Black, and Adaptive Lineage)**. Detail slides qualify white/gray/black-box methodology, Bandit-only supporting evidence, zero Semgrep target files, no SCA receipt, and the fixture-backed Battle/Judge demonstration—not a live adaptive campaign against this project.

## Evidence and visual acceptance boundaries

The supplied standard-mode project-state report collected tests; it did not execute them. Its source-informed interpretation does not call for repairing synthetic fixture values or missing module basenames. It does not establish Memory import or live-assistance wiring. See the [retained context](sources/project-state-context.md), not a new security campaign.

The supplied preview predates the latest notes and this revision. All claims remain candidate. The actual house-band PNG and theme tokens are preserved, including the separate opaque brown fill and 10% image overlay. Native text remains editable; SVG interiors are images. Legacy blue framing is a renderer/export issue for local inspection, not permission to invent proof or remove qualifiers.

Final consumer rendering, GUI/import, visible typography, demo rehearsal and human approval remain local acceptance work. Source navigation is not a VS Code sync, breakpoint or debugger capture. No Archify, React Flow, GSN, recording, Memory import or Live Evidence delivery is established.

Formal-assessment rules govern any actual assistance. Permission to use AI coding tools is not interview-assistance permission. Recording consent must be explicit and separate. Technical PASS is not eight-hour compliance; preserve the timebox disclosure.

## Subsequent local operational checks

The project agent exercised the real skill preflight/run/verify path on the
prepared four-format synthetic input and independently read back all four outputs.
See `sources/live-demo-readback.json`. This was not a timed human rehearsal.

Use the dedicated native viewer on port 3016 for this workspace. Identity, typed
verification and publication source reveals were observed through the native UI.
A publication debug session stopped at `_publish:209`, exposed report_path, and
was continued to termination. Before the marker rename, independent filesystem
readback found a complete temporary report and the corpus but no final marker.
This proves the exercised controls, not every configured stop or a crash campaign.
The existing debug launches use their small Bob/Bobby example, separate from the
main Alice/A.L demo. No recording was started.
