# Proof-boundary SVG drafts

**Drafts for human review. Not installed in the presentation.** No slides or runtime features are added to the trial.

| Draft | One idea | Proposed existing slide |
|---|---|---|
| [READY's scope](ready-meaning.svg) | Policy-bounded readiness does not establish broader privacy guarantees. | `r19-answer-exact` |
| [Verification boundaries](verification-boundary.svg) | Runtime verification shares primitives; fixture readback provides a separate bounded check. | `r21-answer-verifier` |
| [Local versus modeled](local-versus-model.svg) | Exercised local paths and proposed cloud behavior are different evidence classes. | `r23-answer-scale` |

These replace explanatory bullets if accepted; retain the existing pipeline, publication lifecycle, and required cloud architecture diagrams. Do not turn comparisons into execution arrows.

## Source grounding

- READY: [policy compilation](../../../../src/anonymization_trial/policy.py), [verification](../../../../src/anonymization_trial/verification.py), [publication](../../../../src/anonymization_trial/pipeline.py), [privacy contract](../../../PRIVACY_CONTRACT.md).
- Independence: [runtime verifier](../../../../src/anonymization_trial/verification.py), [qualification fixture/readback](../../../../scripts/qualify_submission.py). “No runtime imports” describes that fixture oracle, not a general second engine.
- Local/model distinction: [rehearsal receipt](../rehearsal-evidence.json), [cloud proposal](../../../production-architecture.md), [cost calculator](../../../../scripts/estimate_aws_cost.py). A calculated cost is not a measured cloud bill.

## Construction and proof boundary

Built through `$create-svg`'s bounded `comparison-panels` template, not hand-authored SVG geometry. Existing templates encode good/bad judgments or fan-out; this neutral comparison template adds neither. It allows two or three equal panels, at most twelve text elements, short labels and a canvas-relative grid.

The 1408×387 viewBox matches the existing 0.88×0.43 image slot on the 1920×1080 deck. Theme colors match the current warm-dark artwork; essential text uses the existing Arial/sans-serif stack. The diagrams are deliberately static: no motion is needed to explain a comparison, and the full base state carries all meaning. No font files or external resources are embedded.

Adjacent `.yml` files are reproducible inputs; `theme.yml` is shared across these drafts. `.grid.json` files describe the panel body-row grid and equal-width columns. Their scope excludes the separate heading/caption bands. XML/deterministic rebuild and grid checks do not establish human visual acceptance.

Preview pages and validation receipts are retained under `/mnt/storage12tb/skills/create-svg/oai-proof-drafts/`. Final deck installation and final visual acceptance require human review of the drafts first.
