#!/usr/bin/env bash
# Pre-submission adversarial gate: the check that would have caught the trial
# disqualifier. Runs the PINNED Battle evaluator (verified snapshot from
# battle.lock.json, never the mutable checkout) in two campaigns:
#   1. the frozen acceptance-contract floor via security/battle/acceptance.adapter.json, and
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
cd "$REPO"
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

echo "== acceptance-contract floor through Battle production adapter =="
PYTHONPATH="$BATTLE/skills/battle/src" python3 "$SEC/run_acceptance_floor.py" \
  --battle "$BATTLE" \
  --image "$IMAGE"

echo "== beyond-brief contract campaign (request -> plan -> receipt) =="
RUN_ROOT="$SEC/runs/latest"
docker run --rm -v "$SEC/runs:/w" --entrypoint rm "$IMAGE" -rf /w/latest >/dev/null 2>&1 || true
mkdir -p "$RUN_ROOT"
python3 - "$BATTLE" "$RUN_ROOT" <<'PYGATE'
import json, sys
from pathlib import Path
battle, run_root = sys.argv[1], sys.argv[2]
request = json.loads(Path("security/battle/request.template.json").read_text())
for key in ("generator", "judge", "functional_judge"):
    request[key] = request[key].replace("$BATTLE", battle)
request["work_root"] = str(run_root)
Path(run_root, "request.json").parent.mkdir(parents=True, exist_ok=True)
Path(run_root, "request.json").write_text(json.dumps(request, indent=2))
PYGATE
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.campaign_contract run \
  --request "$RUN_ROOT/request.json"

echo "== offline verification (reruns judges on retained observations) =="
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.campaign_contract verify \
  --receipt "$RUN_ROOT/receipt.json"
