# OAI trial deck: revised wording and slide order

Status: PROPOSED slide copy, implementing Graham's requested presentation structure. Not a claim that the deck has already changed or that any project capability passed. The oai-trial project agent must ground the final copy, commands and results in its current source and artifacts.

## Main playback

| Order | Proposed on-slide heading | What belongs on the slide |
|---|---|---|
| 1 | Let's run it. | Open with the actual working demo, not an agenda, credentials or architecture lecture. Show the real input and action. If it cannot run, disclose that instead of implying it worked. |
| 2 | Here is the result. | Show the produced artifact and the one observable result the audience should notice. Keep relevant limitations visible. |
| 3 | Run the same command. | The exact verified CLI invocation, its real input and output location. Do not invent a command or use a decorative terminal screenshot. |
| 4 | Reproduce the environment. | Actual setup/container invocation. Show Docker only if it exists and has been exercised; otherwise show the real supported environment. |
| 5 | Check the result. | Exact verification command and fresh result, including failures/skips and what the check does not prove. Never infer 'all tests pass' from collection or a narrow fixture. |
| 6 | Follow the pipeline. | A small, readable input-to-output map. This is an orientation slide, not every implementation detail on one canvas. |
| 7 onward | One source-grounded assertion per pipeline stage. | Derive the number and names of these slides from the real code. Each slide follows one transformation: relevant input, operation, output/handoff. Use the same running example. Split a long pipeline across connected slides, rather than shrinking it. |
| After the walkthrough | Up to three anticipated hard questions. | Give each question its own slide and bounded answer. Candidate headings: 'Why this design?', 'What can go wrong?', 'What is not proven yet?' Choose the questions that actually matter to this project; do not force all three. |
| Last substantive block | Extra credit: [actual capability]. | One demonstrated extra per slide. Security, Terraform, deployment or other extras belong here only when supported by actual project evidence. Do not invent an extra-credit feature merely to fill the section. |
| Penultimate | Questions? | Audience Q&A, distinct from the prepared objections above. |
| Final | Thank you. | Short close; Graham/contact/project link as appropriate to the deck's visibility. No new technical content after extra credit. |

The headings above are suggested text, not a fixed slide-count template. Replace generic pipeline headings with concrete, supported assertions. Existing project content—not these examples—determines the actual steps and extras. Keep appendices/backup slides outside normal playback.

## Pacing and text

- ONE concept per slide is the default. Advance briskly rather than accumulating dense bullets.
- Four bullets/concepts is a ceiling, not a target. Split overloaded slides.
- Prefer a short assertion headline plus the artifact, diagram or code that supports it. Put explanation in speaker notes, but never hide a claim's required qualifier there.
- Preserve claim IDs, sources, visibility, qualifications and stable slide links while reorganizing. An edited sentence does not approve a claim.

## Code accompaniment

For pipeline detail slides, map to the actual file/function/line range in VS Code. Slide navigation may reveal code; Run, Inspect, Step, Continue and Stop remain explicit actions. Do not call code highlighting a breakpoint or a paused frame. Derive mappings from current files instead of inventing line numbers.

## Visual direction already requested

Use the grahama.co brand direction from agent-skills/site/BRAND.md, site/DESIGN.md and site/app/globals.css. Display/argument type and prose have distinct roles. Graham requested highly transparent header BACKGROUNDS, potentially brown, while retaining readable text contrast. A chosen opacity is a design choice, not a measured historical value. Preserve intended slide/element animation; use the retained Graham deck examples rather than inventing a new animation system. Browser reading must reflow beside VS Code; fixed PPTX/design geometry is separate.

## Handoff boundary

The pitchdeck Theme dropdown is being handled separately by the pitchdeck worker; this message does not establish that feature's completion. Do not edit shared agent-skills/pitchdeck files concurrently. This handoff carries the requested presentation direction to the existing oai-trial session. Acknowledge receipt and use it when revising the project deck; retain the exact project-specific wording and evidence in that project's normal artifacts.
