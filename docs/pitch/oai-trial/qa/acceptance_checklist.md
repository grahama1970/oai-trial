# Briefing acceptance checklist

Receipt index: `final-review.json`. Checked items below are source, machine, or
agent checks—not human approval. The final rehearsal gate remains fail-closed.

## Source and claims
- [x] One canonical seven-slide deck, ledger and 36-minute notes.
- [x] Generated deck/ledger/notes mirror the canonical files.
- [x] Visible text has claim bindings, precise evidence spans and required qualifiers.
- [x] Compiler verification reports zero errors and zero warnings.
- [x] No public slide references private-classified sources or assets.
- [x] Local reread/re-derivation, bounded domains and uncommitted failure are qualified.

## Artifacts and presentation controls
- [x] Static local release and publication diagrams replace the stale fan-out.
- [x] Narrative text, identity flow and evidence matrix remain editable text/shapes.
- [x] Every slide has a clickable commit-pinned CODE / EVIDENCE link.
- [x] Explicit local debugger launch configurations exist for three demonstrations.
- [x] All three stops were captured in the Python debugger and visible VS Code debugpy.
- [x] Publication claim/code arrangement captured at 1080p for review.
- [x] Full-screen 16:9 explanation plus three temporary code-dominant splits documented.

## Build and review
- [x] `generated/build-receipt.json` binds the linked PPTX hash.
- [x] `generated/verify_receipt.json` records zero errors and warnings.
- [x] Final PPTX rendered to PDF, seven PNGs and contact sheet.
- [x] Agent inspected every rendered slide; footer overlap/link contrast corrected.
- [ ] Human approves the rendered deck/contact sheet at audience viewing size.
- [ ] Google Slides upload/import completed and every slide inspected for drift.
- [ ] Human completes the 36-minute talk plus interruption-margin rehearsal.

Google Drive was opened, but upload was not proven. Do not mark import approved
from local PPTX or PDF checks. Record the actual imported URL, reviewer, date and
hash-bound evidence in `final-review.json` before clearing the final gate.
