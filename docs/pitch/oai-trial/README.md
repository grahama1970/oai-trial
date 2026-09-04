# Pitch-deck bundle

This directory is the source-controlled handoff for a README-derived deck.

The current briefing is `deck.curated.yaml` with `claim_ledger.curated.yaml`.
`generated/deck.public.yaml` and `generated/claim_ledger.yaml` are exact text
copies of those curated manifests, not the old auto-planned draft. After editing:

```bash
cp deck.curated.yaml generated/deck.public.yaml
cp claim_ledger.curated.yaml generated/claim_ledger.yaml
```

Keep `generated/speaker_notes.md` aligned with the seven curated slides.
The original `plan_receipt.json` and source-state files remain historical planning
provenance, not proof that current slides have been rendered or accepted.

1. Edit `source_manifest.yaml` and point it at local README files.
2. Run `pitchdeck plan` into a generated subdirectory.
3. Review every candidate in `claim_ledger.yaml`.
4. Edit the deck manifest so each slide has one message, a source, and a visual plan.
5. Build, verify, render, inspect the contact sheet, then import the PPTX into Google Slides.

Do not commit large exports here. Store generated PPTX/PDF/PNG outputs on the configured
artifact volume and link the receipts from project documentation.
