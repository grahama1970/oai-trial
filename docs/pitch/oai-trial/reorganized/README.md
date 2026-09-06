# OAI trial — reorganized authoring bundle

This is a coordinated **candidate authoring bundle**, not the submitted anonymizer archive, a fresh technical qualification, or an approved slide export.

Start with `INTERVIEW_GUIDE.md`, then `TOC.md` and `WALKTHROUGH.md`. `deck.public.yaml` contains 30 normal-playback slides: 28 prepared slides totaling 30 minutes, then a separate 15+ minute Discussion reserve and a final Thank you. The entire 48-question bank remains outside playback, preserved in the transcript and `question-map.json`.

## Contents

- `deck.public.yaml`, `claim_ledger.yaml`, `source_manifest.yaml`, `asset_manifest.yaml`: schema-bound current-consumer draft; all claims candidate.
- `slide-map.json`: stable new slide IDs, primary Q mappings, legacy sections, durations, code path/symbol/line ranges/commit and diagram/figure links.
- `TOC.md`, `WALKTHROUGH.md`: one coordinated hierarchy and full spoken transcript with code citations and the preserved question appendix.
- `assets/`: actual supplied header PNG and authored self-contained static SVGs. SVG internals are image content in the current PowerPoint exporter, not native editable shapes. Prose and slide headings remain native text.
- `assets/figures/`: cost chart rows/spec and create-figure metrics input, plus source-derived fixture expectation metadata. Modeled cost data is not mixed with observed demo measurements.
- `sources/`: exact supplied source excerpts and normalized historical evidence, including qualification, reviewed narrative, disclosures and modeled costs. Source inspection is distinct from execution.
- `schemas/`, `validation/authoring-checks.json`, `theme/README.md`, `CHANGELOG.md`: consumer contracts, actual authoring checks and pending local acceptance.

## Local handoff

Resolve manifest paths relative to this extracted bundle. Keep the frozen implementation checkout available for linked code navigation; no runtime source is modified. Use the current supported pitchdeck consumer to load these manifests. This package does not replace or patch that renderer.

The theme tokens already specify the supplied grahama.co preset and independent header fill/image opacity. The existing renderer owns its band texture and footer; do not overlay an authored footer or duplicate texture. The actual supplied PNG is included for identity checking. No font files are bundled.

Claims are not approved. A successful JSON Schema check does not satisfy local producer/publish gates or human visual review. Do not bypass those gates or copy older approvals. A real local preview and export/GUI inspection remain necessary.

No application, pytest, Ruff, Docker, local compiler, analytics, create-figure, create-svg, recording or Live Evidence execution is claimed by this authoring task. See CHANGELOG.md for exact boundaries.

## Reported local integration before this focused update

The project agent reports that the downloaded original ZIP is retained unchanged outside the repository. The incoming committed copy contains these local corrections: three missing visible qualifiers on
prepared-question slides; native editable question text and source-navigation
labels instead of text-only SVGs; an explicit 1000/100 = 10 source derivation;
and the verified input_bundle end line (71). The transcript qualifiers and
source references were kept in sync. No runtime source changed.

The project agent reports that the prior local consumer models and draft build passed, and that the prior SVG assets passed the owning create-svg XML/safety checks. Those are historical reported results, not executions or acceptance of this update. This remains an unapproved presentation
draft: Google Slides import, full visual approval, live-demo rehearsal,
VS Code interaction, and Live Evidence wiring are not established. The opening
currently uses recorded qualification evidence, not a newly captured live run.
Some picture containers retain legacy blue framing; the visual review must not
be represented as final grahama.co conformance.

The incoming README referred to an older validation/report.json that was not included among the current-package payloads. This update does not invent it. The supplied current schemas and decoded payloads are the authoring authority; new checks are in validation/authoring-checks.json, not a local renderer acceptance receipt.

## Focused interview/slides update

This copy updates the committed authoring sources at `ecfaaaac2cc7844bd0e52fd7d2bbf3abab36ab78`; runtime remains `0375af56bf681e9441edcb7433cfe58951db77b2`. The slide order, 30-minute prepared budget, question IDs and answers are retained. r02 has explicit live-action and historical-fallback branches; only the exact one-sentence wrapper mention precedes a live run. r26 now has native editable contract/delegation/behavior rows and a source-only reuse reference. `INTERVIEW_GUIDE.md` is rehearsal guidance, not a real interview transcript.

All payload hashes in the incoming `current-package.json` were checked against their own decoded content. No older inventory is used as byte authority for normalized evidence. Current authoring checks are in `validation/authoring-checks.json` and their limits in `validation/SCOPE.md`. The prior local draft build reported by the project agent does not establish that this edited deck has been rendered.

The actual supplied preview is retained under `reference/` for context only. No font files, application changes, renderer patches, new runtime tests or execution receipts are added. Old question/navigation SVGs remain reference files but are not bound to normal playback.

## Native pitchdeck import

The four current manifests use the standard pitchdeck filenames ending in
`.yaml` (their JSON syntax is valid YAML). These are the single editable sources;
the original WebGPT JSON files remain in the downloaded ZIP. Native UI emission
uses this project-owned bundle; generated browser assets stay on the artifact
drive. No shared pitchdeck implementation files are changed.

Native presentation URL (local workstation):
`http://127.0.0.1:3006/?deck=./oai-trial-current/deck.data.json`

The import preserves title/message claim bindings by using matching freeform
element IDs. The closing slide adds the grahama.co caption. Candidate claim
warnings remain intentional. Next-slide navigation was exercised; recording and
VS Code sync were not activated. The narrow native view currently duplicates
authored header-positioned titles below its automatic header; this observed
shared-renderer issue was sent to the pitchdeck owner. It is not final visual
approval or a reason to alter the anonymizer.
