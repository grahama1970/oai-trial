# Security lineage

All white-box, gray-box, black-box, and adversarial evidence for the
anonymization pipeline lives here. This directory is the single home for the
security story; the executable adversarial tests live in `security/tests/` and
run under the normal gate (`uv run pytest`, `testpaths` includes `security/tests`).

## Hat lineage — method → evidence

| Lane | Vantage | What it attacks | Evidence |
|------|---------|-----------------|----------|
| **White-box (SAST/SCA)** | full source | code-level vulns, insecure patterns, vulnerable deps | `hack-audit.receipt.json` (Semgrep + Bandit: 0 critical / 0 high, `$hack`), `SECURITY.md` |
| **Gray-box** | internal APIs, partial knowledge | matcher/policy/verifier invariants under crafted inputs, overlap precedence, encoding traps | `tests/test_graybox_adversarial.py`, `tests/test_verifier_sensitivity.py`, `tests/test_source_snapshot.py` |
| **Black-box** | evaluator-facing CLI + mount only | can an unsafe or leaky artifact ever become a valid release | `tests/test_blackbox_contract.py`, `tests/test_pipeline_failclosed.py` |
| **Red-team / battle** | adversary vs. defender | bounded attack campaign against the fail-closed gate | `battle/` receipts (`red`, `blue`, `judge`, `run`, `scoreboard`), `BATTLE_OBJECTIVE.md` |
| **Residual-risk probe** | statistical | values that survive replacement / re-identification residue | `residual_risk_probe.py`, `tests/test_residual_risk.py` |

## Documents

- `SECURITY.md` — security posture, SAST/SCA results, three-lane methodology.
- `THREAT_MODEL.md` — trust boundaries, assets, adversaries, mitigations.
- `BATTLE_OBJECTIVE.md` — the bounded red/blue battle objective and rules.

## Non-claims

Static and adversarial scans are **supporting evidence, not proof of
vulnerability-free software**. The pipeline proves declared-literal replacement
and structural preservation, not resistance to re-identification. These lanes
narrow risk; they do not certify the software.
