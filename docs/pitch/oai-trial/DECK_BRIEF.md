# Technical briefing brief

## Audience and decision
OpenAI privacy-engineering trial reviewers evaluating engineering judgment,
correctness, evidence, and explicit tradeoffs. There is no sales ask.

## Narrative
Assignment → architecture → hard semantics → release reliability → adversarial
evidence → AWS production mapping → tradeoffs/non-claims.

Exactly seven slides. The repo and debugger supply depth; do not add slides to
absorb questions. Plan 36 minutes with four minutes for interruptions.

## Presentation arrangement (operator-approved)
- Explain: show the 16:9 slide full-screen.
- Inspect: use a compact claim on the left and VS Code in roughly the right
  two-thirds of the shared screen. Use existing windows, not a new dashboard.
- Three prepared stops only: alias identity, typed mutation rejection, report-last
  authorization. Each has a source-pinned hyperlink, explicit local launch, and
  captured fallback in `qa/debugger_stops.json`.
- Judge legibility at 1080p screen-share size, not just local 4K resolution.
- Never launch code automatically from a web link. Source links navigate;
  debugger commands are explicit local actions.

## Boundaries
Literal-policy pseudonymization, not formal anonymity. Verification is independent
reread/re-derivation using shared replacement primitives. Local failures remain
uncommitted; quarantine is a production design. TB/PB throughput and AWS costs
are modeled, not measured deployment results.

## Visual constraints
One dominant composition and one message per slide. Arial native text; one cyan
accent, amber for verification, red for failure, green for READY. Static SVGs;
no neon fan-out animation, full-slide rasterization, or tooling showcase.
Contact-sheet and Google Slides import approval are separate explicit gates.
