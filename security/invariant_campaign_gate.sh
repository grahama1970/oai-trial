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
runtime_lock = json.loads(Path(request["lock_path"]).read_text())
runtime_lock["source_repo_path"] = battle
runtime_lock_path = Path(run_root, "battle.runtime-lock.json")
runtime_lock_path.write_text(json.dumps(runtime_lock, indent=2) + "\n")
adapter = json.loads(Path("security/battle/acceptance.adapter.json").read_text())
sys.path.insert(0, str(Path(battle) / "skills"))
from common.security_authorization import validate_target_authorization
request["authorization_receipt"] = validate_target_authorization(
    Path("security/battle/authorization.json"),
    expected_target=adapter["target_identity"],
    expected_execution_target="anonymization-trial",
    requested_action="battle",
    requested_runtime_mode="docker",
)
request["lock_path"] = str(runtime_lock_path)
request["work_root"] = str(run_root)
Path(run_root, "request.json").parent.mkdir(parents=True, exist_ok=True)
Path(run_root, "request.json").write_text(json.dumps(request, indent=2))
PYGATE
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.campaign_contract run \
  --request "$RUN_ROOT/request.json"

echo "== offline verification (reruns judges on retained observations) =="
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.campaign_contract verify \
  --receipt "$RUN_ROOT/receipt.json"

echo "== contextual graph release-gate campaign =="
# Rebuild the authorized image tag with multimodal dependencies for this campaign;
# Battle authorization is bound to the exact executable image name.
GRAPH_IMAGE="$IMAGE"
docker build --build-arg INCLUDE_MULTIMODAL=1 -t "$GRAPH_IMAGE" "$REPO" >/dev/null
GRAPH_RUN_ROOT="$SEC/runs/contextual-graph-latest"
docker run --rm -v "$SEC/runs:/w" --entrypoint rm "$IMAGE" -rf /w/contextual-graph-latest >/dev/null 2>&1 || true
mkdir -p "$GRAPH_RUN_ROOT"
python3 - "$BATTLE" "$GRAPH_RUN_ROOT" "$GRAPH_IMAGE" <<'PYGRAPH'
import json, sys
from pathlib import Path
battle, run_root, graph_image = sys.argv[1], sys.argv[2], sys.argv[3]
request = json.loads(Path("security/battle/request.template.json").read_text())
request["profile_path"] = str(Path("security/battle/contextual-graph.profile.json").resolve())
request["generator"] = str(Path("security/battle/contextual_graph_generator.py").resolve())
request["target_run_cmd"] = (
    "docker run --rm -v {input}:/trial/input:ro "
    f"-v {{output}}:/trial/output {graph_image} run"
)
for key in ("judge", "functional_judge"):
    request[key] = request[key].replace("$BATTLE", battle)
runtime_lock = json.loads(Path(request["lock_path"]).read_text())
runtime_lock["source_repo_path"] = battle
runtime_lock_path = Path(run_root, "battle.runtime-lock.json")
runtime_lock_path.write_text(json.dumps(runtime_lock, indent=2) + "\n")
adapter = json.loads(Path("security/battle/acceptance.adapter.json").read_text())
sys.path.insert(0, str(Path(battle) / "skills"))
from common.security_authorization import validate_target_authorization
request["authorization_receipt"] = validate_target_authorization(
    Path("security/battle/authorization.json"),
    expected_target=adapter["target_identity"],
    expected_execution_target="anonymization-trial",
    requested_action="battle",
    requested_runtime_mode="docker",
)
request["lock_path"] = str(runtime_lock_path)
request["work_root"] = str(run_root)
Path(run_root, "request.json").write_text(json.dumps(request, indent=2) + "\n")
PYGRAPH
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.campaign_contract run \
  --request "$GRAPH_RUN_ROOT/request.json"
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.campaign_contract verify \
  --receipt "$GRAPH_RUN_ROOT/receipt.json"

echo "== DP count release-gate campaign =="
DP_RUN_ROOT="$SEC/runs/dp-count-latest"
docker run --rm -v "$SEC/runs:/w" --entrypoint rm "$IMAGE" -rf /w/dp-count-latest >/dev/null 2>&1 || true
mkdir -p "$DP_RUN_ROOT"
python3 - "$BATTLE" "$DP_RUN_ROOT" "$IMAGE" <<'PYDP'
import json, sys
from pathlib import Path
battle, run_root, image = sys.argv[1], sys.argv[2], sys.argv[3]
request = json.loads(Path("security/battle/request.template.json").read_text())
request["arena_protocol_path"] = str(Path("security/battle/dp-count.arena.json").resolve())
request["profile_path"] = str(Path("security/battle/dp-count.profile.json").resolve())
request["generator"] = str(Path("security/battle/dp_count_generator.py").resolve())
request["judge"] = str(Path("security/battle/dp_count_judge.py").resolve())
request["functional_judge"] = str(Path("security/battle/dp_count_judge.py").resolve())
request["target_run_cmd"] = (
    "docker run --rm -v {input}:/trial/input:ro -v {output}:/trial/output "
    f"{image} dp-count --input /trial/input/data.csv --column condition "
    "--equals-sha256 559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd "
    "--epsilon 0.7 > {output}/receipt.json"
)
runtime_lock = json.loads(Path(request["lock_path"]).read_text())
runtime_lock["source_repo_path"] = battle
runtime_lock_path = Path(run_root, "battle.runtime-lock.json")
runtime_lock_path.write_text(json.dumps(runtime_lock, indent=2) + "\n")
adapter = json.loads(Path("security/battle/acceptance.adapter.json").read_text())
sys.path.insert(0, str(Path(battle) / "skills"))
from common.security_authorization import validate_target_authorization
request["authorization_receipt"] = validate_target_authorization(
    Path("security/battle/authorization.json"),
    expected_target=adapter["target_identity"],
    expected_execution_target="anonymization-trial",
    requested_action="battle",
    requested_runtime_mode="docker",
)
request["lock_path"] = str(runtime_lock_path)
request["work_root"] = str(run_root)
Path(run_root, "request.json").write_text(json.dumps(request, indent=2) + "\n")
PYDP
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.campaign_contract run \
  --request "$DP_RUN_ROOT/request.json"
PYTHONPATH="$BATTLE/skills/battle/src" python3 -m battle_skill.campaign_contract verify \
  --receipt "$DP_RUN_ROOT/receipt.json"
