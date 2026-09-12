#!/usr/bin/env bash
# Pre-submission adversarial gate: the check that would have caught the trial
# disqualifier. Red (the invariant campaign) generates the brief's full version
# matrix -- every format x representation x edge case -- plus fuzz, runs the real
# anonymizer in Docker on each, and an INDEPENDENT leak-Judge scores every
# output. Fails if ANY policy value survives in ANY representation.
#
# Usage: security/invariant_campaign_gate.sh [image-tag] [fuzz-count]
set -euo pipefail
IMAGE="${1:-anonymization-trial}"
FUZZ="${2:-20}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
BATTLE="/home/graham/workspace/experiments/agent-skills/skills/battle"

echo "== building $IMAGE =="
docker build -t "$IMAGE" "$REPO" >/dev/null

echo "== invariant campaign (brief matrix + fuzz) through the real container =="
PYTHONPATH="$BATTLE/src" python3 -m battle_skill.invariant_campaign \
  --generator "$BATTLE/fixtures/reference-generators/anon_brief_matrix.py" \
  --target-run-cmd "docker run --rm -v {input}/corpus:/trial/input/corpus:ro -v {input}/policy.json:/trial/input/policy.json:ro -v {output}:/trial/output $IMAGE run" \
  --judge "$BATTLE/fixtures/reference-judges/no_data_leak_judge.py" \
  --gen-params "{\"fuzz\": $FUZZ}" \
  --judge-params '{"output_subdir":"corpus"}'
