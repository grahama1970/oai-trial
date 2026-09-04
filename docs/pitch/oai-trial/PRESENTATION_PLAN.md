# Presentation plan (technical briefing, not a pitch deck)

`$pitchdeck` is **READY** on this host (doctor PASS: PIL/pptx/pydantic/typer/yaml
present; libreoffice + pdftoppm + rsvg-convert present). We use it as a
**supervised authoring** tool only — its publication gate has known bypasses, so
"the deck verified" is never evidence a technical claim is true; a human reviews
every visible slide before external use.

## Shape
A compact **7-slide technical briefing** that is a *projection of the repo*, not
a second story. The deck is a navigation layer; substance lives in
`ARCHITECTURE.md`, the SVG, the code, tests, and receipts.

| # | Slide | Source | Dominant visual |
|---|---|---|---|
| 1 | The assignment + acceptance bar | TRIAL_BRIEF / GOAL | brief invariants |
| 2 | Architecture (trust boundaries) | ARCHITECTURE §3 | `production-architecture.svg` |
| 3 | Hard semantics (identity, overlap, protected, schema, Unicode, SQLite) | ANONYMIZATION_SEMANTICS | matching diagram |
| 4 | Reliability: stage → independent verify → report-last publish | ARCHITECTURE §8-9 | state machine |
| 5 | Evidence: property/adversarial tests, verifier mutation, benchmark, `$hack` | SECURITY, tests | assurance table |
| 6 | Production scale: 1 TB / 1 PB AWS, scoped HMAC, distributed verify | production-architecture.md | AWS diagram |
| 7 | Tradeoffs & non-claims | PRIVACY_CONTRACT, SUBMISSION | PROVES / DOES NOT PROVE |

## Restraint rules (sophisticated, not overproduced)
Almost no paragraphs; one technical visual per slide; real benchmark numbers;
explicit `PROVES` / `DOES NOT PROVE`; no fake screenshots or generic AI art;
labels identical to `ARCHITECTURE.md`. Per-slide footer:
`Evidence -> ARCHITECTURE.md §N · tests/... · report.schema.json`.

## Surface transitions (the memorable part)
```
SLIDE -> SVG / ARCHITECTURE.md -> live CLI/debugger state -> adversarial test -> receipt
```
Example: slide 4 claims report-last release → `anonymization-trial run` + a
verifier-mutation test showing a tampered output is refused → `report.json`.

## Build path (supervised)
```
$pitchdeck plan   --source-manifest docs/pitch/oai-trial/source_manifest.yaml ...
# review claim_ledger.yaml (approve/qualify), edit deck.public.yaml to 7 slides
$pitchdeck build  --deck ... --claim-ledger ... --source-manifest ... --asset-manifest ...
$pitchdeck verify --bundle-dir docs/pitch/oai-trial --pptx OUT.pptx
$pitchdeck render --pptx OUT.pptx --output-dir OUT-render   # PDF + PNG contact sheet
# human review of the contact sheet before any external use
```
Reuse the committed `docs/production-architecture.svg` as a slide asset rather
than letting the compiler redraw the architecture.
