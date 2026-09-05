# Walkthrough-derived deck — human review draft

This is the new seven-slide, 30-minute presentation candidate derived from
[WALKTHROUGH.md](../WALKTHROUGH.md). It does not replace the submitted runtime
at `0375af56bf681e9441edcb7433cfe58951db77b2`, its ZIP, or older deck exports.

## Source files

- `deck.json`: complete slide manifest, visible qualifiers, text bindings, and timed speaker notes.
- `slide-map.json`: all 48 question IDs mapped to slides, walkthrough sections, code symbols, and evidence IDs.
- `claim_ledger.json`: ten candidate claims; human presentation approval is still open.
- `source_manifest.json`: portable relative paths; implementation references remain pinned to the submitted commit.
- `asset_manifest.json` and `assets/`: two static SVG proposals. In the PPTX these are image assets, not individually editable diagram internals. Slide text remains native text.

WebGPT authored the candidate through the existing review conversation. Local
integration corrected one text-binding classification, added its verbatim
supporting passage plus the UTF-8 source passage, and removed redundant authored
footers after a real Surf capture showed overlap with the compiler's own footer.
The SVG designs otherwise retain WebGPT's proposed structure.

## Validation and current boundary

The four manifests passed their actual consumer models. Source bytes and claim
excerpts were checked against the cited files. The slide map totals 30 minutes
and covers Q01–Q48 once. Both SVGs passed XML/safety/accessibility validation.

The draft PPTX was built with `--draft-watermark --allow-candidate-claims`, then
rendered to PDF and seven PNGs. Each rendered slide was viewed through Surf.
The build reports `USABLE_WITH_GAPS`: the ten claim-approval warnings are
intentional at this stage. No formal SVG deterministic-rebuild, Google Slides
import, responsive-browser parity, timed rehearsal, or human visual approval is
claimed. The static SVGs have no animation to demonstrate.

Presenter-local output directory:
`/mnt/storage12tb/oai-trial/deck-authoring/render/`

- `oai-trial-review.pptx`
- `slides/oai-trial-review.pdf`
- `slides/contact-sheet.png`
- `slide-1-surf.png` through `slide-7-surf.png`

Review the visible wording, diagram semantics, qualifiers, and speaking order
before marking claims approved or removing the draft watermark. Debugger/VS Code
captures and active Live Evidence wiring remain later, separately verified work.
