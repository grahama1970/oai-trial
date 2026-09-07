# OAI trial presentation package

## Three views, one technical story

- **[Interviewer brief](INTERVIEWER_BRIEF.md):** compact advance reading.
- **[Canonical narrative](NARRATIVE.md):** expanded explanations and exact code excerpts.
- **[Complete deck JSON](deck.document.json):** the authoritative rendering input—32 slides, elements, native icons, claims, source definitions, notes and animation rows.

[WALKTHROUGH.md](WALKTHROUGH.md) retains the detailed speaking script and question bank. [TOC.md](TOC.md) is the navigation outline. Implementation source remains the evidence for all three views.

The `.yaml` manifests are retained authoring/migration history. Do not recompile them over the edited canonical JSON: that would discard later native-element changes. `deck.data.json` is generated browser output, not an authoring source.

## What “complete JSON” means

The JSON contains the whole supported deck model, not patches or slide prompts. It references image/SVG files in `assets/`; those bytes must accompany it. Native icon references resolve through the installed pitchdeck library. It is not a single file containing the entire codebase, image bytes and renderer dependencies.

`debugger.json` remains the supported code-sync companion because the canonical schema has no structured debugger-map field. `slide-map.json` links slides to narrative sections and code/evidence. These are explicit package dependencies, not opaque JSON strings hidden in provenance.

## Import and export

From the project root, with the installed pitchdeck skill:

```bash
PITCHDECK="$HOME/workspace/experiments/agent-skills/skills/pitchdeck/run.sh"
BUNDLE="docs/pitch/oai-trial/reorganized"

"$PITCHDECK" emit-document-ui \
  --document "$BUNDLE/deck.document.json" --asset-base "$BUNDLE" \
  --output-dir "$HOME/workspace/experiments/agent-skills/skills/pitchdeck/ui/public/oai-trial-current"

cp "$BUNDLE/debugger.json" \
  "$HOME/workspace/experiments/agent-skills/skills/pitchdeck/ui/public/oai-trial-current/debugger.json"

"$PITCHDECK" emit-document-pptx \
  --document "$BUNDLE/deck.document.json" --asset-base "$BUNDLE" \
  --output /mnt/storage12tb/oai-trial/native-pitchdeck/oai-trial-current.pptx

"$PITCHDECK" render \
  --pptx /mnt/storage12tb/oai-trial/native-pitchdeck/oai-trial-current.pptx \
  --output-dir /mnt/storage12tb/oai-trial/native-pitchdeck/render
```

Existing viewer: <http://127.0.0.1:3016/?deck=./oai-trial-current/deck.data.json&rehearse=1>.

The dedicated server binds `PITCHDECK_DEBUG_WORKSPACE` to the primary oai-trial checkout. Small emitted manifests belong in its real `public/` directory. The renderer's source-containment checks remain enabled.

## Presentation behavior

- TOC: seven paired entry builds, from the left; title and message remain visible.
- Demo: show the `$anonymize-data` skill prompt, then inspect real output or explicitly identify the recorded fallback.
- Brief coverage: requirement/solution/check rows move as whole units. Checks mean delivered scope; the production row is a design/model, not deployment.
- Multi-point explanations: reveal in rhetorical order. Comparisons remain complete when hiding a side would obscure the boundary.
- Slide changes use a short fade. Flow SVGs use one synchronized cycle and retain a complete reduced-motion base. The separate fixture readback is after publication, not a runtime release gate.
- Header icons are monochrome native-library cues; muted neutral checkmarks denote the stated delivered scope.
- `slide.notes` contains short presenter cues. Use the Teleprompter control for the separate companion page; the full script remains in Markdown.

## Source and debugger controls

Enable **Sync VS Code** to reveal mapped source ranges. Clicking a mapped concept or selecting **Code for** highlights its source. Progressive builds also follow their mapped concept. Neither navigation nor source reveal executes code.

**Run** is separate and only available for prepared launches. The optional publication demonstration stops before the final report rename; the highlighted function range is separate from its executable `breakLine`. The map generator is `scripts/link_presentation_code.py`.

## Retained checks and boundaries

- `scripts/verify_canonical_presentation.py`: actual JSON/UI/PPTX content, native icons, muted neutral checkmarks and timing-tree readback.
- `fixtures/canonical_presentation_eval.json`: repeated readback and unresolved-icon refusal.
- `scripts/prove_presentation_sync.py` and `fixtures/presentation_sync_eval.json`: live source selection through the browser and independent VS Code bridge-file readback; invalid concept refusal.
- `scripts/prepare_report_svgs.py`: bounded correction of the supplied report diagrams.
- `scripts/place_cloud_boundary.py` plus its source/grid: node-fit correction without shrinking the worker label.

These checks do not establish PowerPoint/Google Slides slideshow playback, font embedding, human visual approval, a timed human rehearsal, or general runtime correctness. SVG images remain images in PPTX; native comparison groups, text and library icons remain editable. PDF is static.

The frozen runtime reference is `0375af56bf681e9441edcb7433cfe58951db77b2`. Later rehearsal, presentation and renderer work does not retroactively requalify the original submission archive. Historical receipts and source excerpts are retained as history, not current execution claims.
