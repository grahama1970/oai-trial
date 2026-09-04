# Presentation plan — technical evaluation, not a pitch

The canonical seven-slide deck is `deck.curated.yaml`; the evidence ledger is
`claim_ledger.curated.yaml`; the 36-minute talk is `speaker_notes.curated.md`.
`generated/` contains reproducible projections, not another authoring source.

| Slide | Invariant | Dominant visual | Time |
|---|---|---|---|
| 1 | Literal-policy contract | Four formats / three obligations | 4 min |
| 2 | Transformer cannot authorize release | Local pipeline SVG | 5 min |
| 3 | Identity stable; ambiguity rejected | Editable identity/matching diagram | 8 min |
| 4 | Transformed corpus is not a release | Publication state SVG | 5 min |
| 5 | Try to falsify the release | Native evidence matrix | 5 min |
| 6 | Scale work, retain one release decision | AWS SVG + SLA/cost callouts | 5 min |
| 7 | Scope does not imply anonymity | PROVES / DOES NOT PROVE split | 4 min |

Four minutes remain for interruption. No sales ask, eighth slide, or new platform.

## Two viewing modes
Explain full-screen at 16:9. For three evidence stops, place the current claim
left and VS Code in the right two-thirds. Open `.vscode/launch.json` configurations
`Pitch: identity`, `Pitch: typed`, and `Pitch: publication`; see
`qa/debugger_stops.json` for exact source lines, expected locals, and replay commands.
Links open commit-pinned source; they never execute a debugger implicitly.

Use a prepared shell with `PYTHONPATH=src`. The debugger skill is an optional
presenter tool, never an anonymizer runtime dependency. A trusted VS Code workspace
and installed Python/debugger bridge extensions are required for GUI control.
Headless capture proves paused Python state, not the visible side-by-side experience.

## Rehearsal checks
1. Open the slide and source at each prepared stop before the meeting.
2. Hit the breakpoint, inspect the listed values, then continue and read output.
3. Switch back to the slide without resizing or hunting for files.
4. Inspect the shared-screen composition at 1080p. If text is too small, show
   code full-screen temporarily rather than changing the slide ratio.
5. Keep captured debugger receipts and rendered slides ready as fallbacks.

The pitch compiler is supervised authoring tooling. Its zero-error receipt is
not human visual approval or proof that a technical claim is true. Build/render
and human/import gates are recorded separately in `qa/final-review.json`.
