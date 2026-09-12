#!/usr/bin/env bash
# Pre-submission adversarial gate: the check that would have caught the trial
# disqualifier. Runs the PINNED Battle evaluator (verified snapshot from
# battle.lock.json, never the mutable checkout) in two campaigns:
#   1. the brief matrix (spec floor, no profile), and
#   2. the beyond-brief matrix under the oai-trial profile contract
#      (security/battle/profile.json: frozen expectations + required inventory).
# Fails if ANY policy value survives in ANY representation, if a required
# accept case is rejected, or if a required reject case is accepted.
#
# Usage: security/invariant_campaign_gate.sh [image-tag] [fuzz-count]
set -euo pipefail
IMAGE="${1:-anonymization-trial}"
FUZZ="${2:-20}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SEC="$REPO/security/battle"

echo "== resolving pinned battle evaluator =="
BATTLE="$(python3 "$SEC/resolve_battle.py")"

echo "== judge qualification (control pairs; no target execution) =="
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.qualify_judges \
  --manifest "$SEC/qualification/manifest.json" \
  --security-judge "$BATTLE/skills/battle/fixtures/reference-judges/no_data_leak_judge.py" \
  --functional-judge "$BATTLE/skills/battle/fixtures/reference-judges/functional_anonymize_judge.py" \
  --out "$SEC/qualification/receipt.json"

echo "== building $IMAGE =="
docker build -t "$IMAGE" "$REPO" >/dev/null

run_cmd="docker run --rm -v {input}/corpus:/trial/input/corpus:ro -v {input}/policy.json:/trial/input/policy.json:ro -v {output}:/trial/output $IMAGE run"

echo "== brief-matrix campaign (spec floor) through the real container =="
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.invariant_campaign \
  --generator "$BATTLE/skills/battle/fixtures/reference-generators/anon_brief_matrix.py" \
  --target-run-cmd "$run_cmd" \
  --judge "$BATTLE/skills/battle/fixtures/reference-judges/no_data_leak_judge.py" \
  --gen-params "{\"fuzz\": $FUZZ}" \
  --judge-params '{"output_subdir":"corpus"}' \
  --functional-judge "$BATTLE/skills/battle/fixtures/reference-judges/functional_anonymize_judge.py"

echo "== beyond-brief campaign under the oai-trial profile =="
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.invariant_campaign \
  --generator "$BATTLE/skills/battle/fixtures/reference-generators/anon_beyond_brief_matrix.py" \
  --target-run-cmd "$run_cmd" \
  --judge "$BATTLE/skills/battle/fixtures/reference-judges/no_data_leak_judge.py" \
  --profile "$SEC/profile.json" \
  --judge-params '{"output_subdir":"corpus"}' \
  --functional-judge "$BATTLE/skills/battle/fixtures/reference-judges/functional_anonymize_judge.py"
