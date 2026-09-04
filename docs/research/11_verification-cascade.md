# Verification cascade (3 tiers + escalation)

Single-pass verification can share the transform's blind spot (see
`10_...oracle` — a homoglyph leak passed a naive scan). Model verification as a
3-tier cascade with an explicit classification change, mirroring
`monitor-sparta` (T0 deterministic → T1.5 classifier/GPT → T2 teacher) and
`project-watchdog` (detect → review → reclassify + alert).

## The three tiers

### Tier 1 — Detector (deterministic, IN the offline container)
Runs on every file + the whole staged corpus. No models, no network. Emits a
per-item verdict `PASS | SUSPECT | FAIL`.
- **Literal-absence scan** (naive): no raw sensitive literal survives.
- **Normalized scan** (independent code path): NFKC + homoglyph-fold (borrow
  `clean-text`) then re-scan — catches evasion the naive scan misses.
- **Structural checks:** SQLite `integrity_check` + `foreign_key_check` + per-table
  row-count parity; CSV header scanned (not skipped); JSON structure preserved.
- **Protected-value preservation:** every protected value still present, unchanged.
Any `FAIL` → fail closed (no promote, exit non-zero, quarantine). `SUSPECT`
(e.g. normalized scan disagrees with naive) → escalate to Tier 2.

### Tier 2 — Reviewer (out-of-band oracle, control-plane / design-time — NOT the sealed run)
Reviews Tier-1 `SUSPECT` items (and a sampled fraction of `PASS` for drift).
Different modality / different author than the transform:
- **Render→OCR/VLM oracle** (`10_...oracle`): render output to pixels, read back,
  confirm no sensitive value is visible.
- Optional **LLM/classifier reviewer** (project-watchdog style) for judgment calls.
Emits `confirm_verified | confirm_fail | uncertain`.
Barred from the evaluator's offline `docker run` (needs models/services = host
services). Lives in our dev/CI loop and in the production control-plane.

### Tier 3 — Classification change + escalation
Assigns the final state per item/corpus, echoing `pi.agent_status` states:
| State | Trigger | Action |
|---|---|---|
| `verified` | Tier 1 PASS (+ Tier 2 confirm where run) | promote staging → release |
| `needs_human` | Tier 2 `uncertain`, or SUSPECT the reviewer can't clear | quarantine; **`$ops-discord` alert**; block release |
| `failed` | any Tier 1 FAIL or Tier 2 `confirm_fail` | fail closed: exit non-zero, quarantine, no partial release |

`needs_human` alert (control-plane only):
```bash
skills/ops-discord/run.sh notify --webhook oai_trial \
  --content "anonymization needs_human: <corpus> file=<path> reason=<normalized_scan_disagreement>"
```
(Webhook resolves via `OPS_DISCORD_WEBHOOK_OAI_TRIAL_URL` / `DISCORD_WEBHOOK_URL`;
falls back to `--discord-bot --channel-name`.)

## Layer placement (hard boundary)
```
Evaluator `docker run` (offline, self-contained, deterministic):
    Tier 1 detector only. FAIL/SUSPECT -> fail closed. No Discord, no models.

Control-plane / production (SUBMISSION design) + our dev-CI loop:
    Tier 2 reviewer (OCR/VLM/LLM) over quarantined SUSPECT items.
    Tier 3 classification + $ops-discord needs_human alert.
    Verified-only promotion into the release bucket.
```
The sealed container never emits `needs_human` to a human mid-run — it fails
closed and quarantines; the surrounding control-plane is what reviews the
quarantine and pings Discord. This keeps the evaluator run deterministic while
still giving the 3-tier detector→reviewer→reclassify+alert loop the user wants.

## Reuse
- `monitor-sparta` / `project-watchdog` — cascade shape and reclassify+alert pattern.
- `clean-text` — NFKC + homoglyph fold for the Tier-1 normalized scan.
- `$ops-discord` — the `needs_human` notification transport.
