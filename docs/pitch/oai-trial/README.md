# Seven-slide technical briefing

Canonical sources: `deck.curated.yaml`, `claim_ledger.curated.yaml`, and
`speaker_notes.curated.md`. The generated deck, ledger, notes, and source-state
are projections of those files. The obsolete animated fan-out asset is retired.

## Present
- Explain slides full-screen at 16:9.
- For three stops only, put the claim on the left and VS Code in the right
  two-thirds. No new dashboard or automatic remote execution.
- Every slide's **CODE / EVIDENCE** hyperlink opens commit-pinned GitHub source.
- `.vscode/launch.json` provides `Pitch: identity`, `Pitch: typed`, and
  `Pitch: publication`. Exact breakpoints, expected values, local commands, and
  fallback receipts are in `qa/debugger_stops.json`.
- Set `DEBUGGER_SKILL` to the installed debugger skill and `ARTIFACT_DIR` to a
  writable artifact directory before copying capture commands. The optional
  skill is not part of the submitted application's runtime.
- `--workspace-artifacts` keeps GUI status in the gitignored bridge directory;
  it was needed because the host's default runtime tmpfs was full during rehearsal.

## Rebuild (from repository root)
Install development dependencies (`uv sync --extra dev`). Set `PITCHDECK_SKILL`
to the installed pitchdeck skill directory; compilation/rendering needs that
external development tool, not the anonymizer itself.

```bash
export PROJECT_ROOT="$PWD"
export ARTIFACT_DIR=/mnt/storage12tb/oai-trial/pitch-final
mkdir -p "$ARTIFACT_DIR"
python scripts/prepare_pitch_bundle.py --source-ref "$(git rev-parse HEAD)"
"$PITCHDECK_SKILL/run.sh" build \
  --deck docs/pitch/oai-trial/deck.curated.yaml \
  --claim-ledger docs/pitch/oai-trial/claim_ledger.curated.yaml \
  --source-manifest docs/pitch/oai-trial/source_manifest.yaml \
  --asset-manifest docs/pitch/oai-trial/generated/asset_manifest.yaml \
  --output "$ARTIFACT_DIR/briefing.pptx"
python scripts/link_pitch_code.py "$ARTIFACT_DIR/briefing.pptx" "$ARTIFACT_DIR/briefing-linked.pptx"
"$PITCHDECK_SKILL/run.sh" verify --bundle-dir docs/pitch/oai-trial/generated \
  --pptx "$ARTIFACT_DIR/briefing-linked.pptx"
"$PITCHDECK_SKILL/run.sh" render --pptx "$ARTIFACT_DIR/briefing-linked.pptx" \
  --output-dir "$ARTIFACT_DIR/render"
uv run pytest -q tests/test_pitch_contract.py
```

After export, retain compiler/link/verify receipts with the final PPTX hash and
canonical deck hash. Review the actual rendered slides and the Google Slides
import; do not transfer approval from an earlier deck hash. Keep binaries on the
artifact volume, not in Git. Source tests and compiler warnings do not constitute
human approval.

## Final rehearsal gate

```bash
python scripts/verify_pitch_bundle.py --bundle docs/pitch/oai-trial \
  --require-build-receipt --require-zero-verify-errors \
  --require-contact-sheet-review --require-google-slides-review
```

This must fail until `qa/final-review.json` has explicit, evidence-bound human
approval for the contact sheet and imported Slides deck. A `SOURCE_SYNCHRONIZED`
plan receipt is not a build or visual-approval receipt. Runtime candidate and
presentation source commit are recorded separately; artifact hashes bind exports.
