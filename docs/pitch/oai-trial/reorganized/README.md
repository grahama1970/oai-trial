# OAI trial — reorganized authoring bundle

This is a coordinated **candidate authoring bundle**, not the submitted anonymizer archive, a fresh technical qualification, or an approved slide export.

Start with `TOC.md`, then `WALKTHROUGH.md`. `deck.json` contains 30 normal-playback slides: 28 prepared slides totaling30minutes, then a separate15+minute Discussion reserve and a final Thank you. The entire48-question bank remains outside playback, preserved in the transcript and `question-map.json`.

## Contents

- `deck.json`, `claim_ledger.json`, `source_manifest.json`, `asset_manifest.json`: schema-bound current-consumer draft; all claims candidate.
- `slide-map.json`: stable new slide IDs, primary Q mappings, legacy sections, durations, code path/symbol/line ranges/commit and diagram/figure links.
- `TOC.md`, `WALKTHROUGH.md`: one coordinated hierarchy and full spoken transcript with code citations and the preserved question appendix.
- `assets/`: actual supplied header PNG and authored self-contained static SVGs. SVG internals are image content in the current PowerPoint exporter, not native editable shapes. Prose and slide headings remain native text.
- `assets/figures/`: cost chart rows/spec and create-figure metrics input, plus source-derived fixture expectation metadata. Modeled cost data is not mixed with observed demo measurements.
- `sources/`: exact supplied source excerpts and normalized historical evidence, including qualification, reviewed narrative, disclosures and modeled costs. Source inspection is distinct from execution.
- `schemas/`, `validation/report.json`, `theme/README.md`, `CHANGELOG.md`: consumer contracts, actual authoring checks and pending local acceptance.

## Local handoff

Resolve manifest paths relative to this extracted bundle. Keep the frozen implementation checkout available for linked code navigation; no runtime source is modified. Use the current supported pitchdeck consumer to load these manifests. This package does not replace or patch that renderer.

The theme tokens already specify the supplied grahama.co preset and independent header fill/image opacity. The existing renderer owns its band texture and footer; do not overlay an authored footer or duplicate texture. The actual supplied PNG is included for identity checking. No font files are bundled.

Claims are not approved. A successful JSON Schema check does not satisfy local producer/publish gates or human visual review. Do not bypass those gates or copy older approvals. A real local preview and export/GUI inspection remain necessary.

No application, pytest, Ruff, Docker, local compiler, analytics, create-figure, create-svg, recording or Live Evidence execution is claimed by this authoring task. See CHANGELOG.md for exact boundaries.

## Local integration after the WebGPT handoff

The downloaded original ZIP is retained unchanged outside the repository. This
copy includes bounded local corrections: three missing visible qualifiers on
prepared-question slides; native editable question text and source-navigation
labels instead of text-only SVGs; an explicit 1000/100 = 10 source derivation;
and the verified input_bundle end line (71). The transcript qualifiers and
source references were kept in sync. No runtime source changed.

The local consumer models and draft build passed. All SVG assets passed the
owning create-svg XML/safety checks. This remains an unapproved presentation
draft: Google Slides import, full visual approval, live-demo rehearsal,
VS Code interaction, and Live Evidence wiring are not established. The opening
currently uses recorded qualification evidence, not a newly captured live run.
Some picture containers retain legacy blue framing; the visual review must not
be represented as final grahama.co conformance.

The original validation/report.json records WebGPT's authoring checks before
these local changes; it is not the local renderer's acceptance receipt.
