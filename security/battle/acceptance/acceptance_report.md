# oai-trial acceptance contract

## Result

The acceptance floor is now predicate-specific instead of generic extracted text. It contains 17 source-backed acceptance cases derived from `TRIAL_BRIEF.md`, `examples/policy.json`, and `examples/policy.schema.json`.

## Source of truth

- `TRIAL_BRIEF.md`
- `examples/policy.json`
- `examples/policy.schema.json`

## Acceptance coverage

The bundle now requires executable or receipt-backed proof for:

1. same logical output format for CSV, JSON, UTF-8 text, and SQLite
2. removal of every policy-listed value across text, JSON strings, JSON numbers, JSON escapes, CSV cells, SQLite TEXT/INTEGER/REAL, Unicode NFC/NFD, formatted phone aliases, scientific notation, and cross-format identity traps
3. stable, non-colliding replacements across files and repeated runs
4. protected-value and benign-data preservation
5. CSV/JSON/SQLite structure and integrity preservation
6. complete release-boundary verification before readiness
7. no raw inputs, replacement mappings, or quarantined content in release/logs
8. fail-closed behavior for unsafe, ambiguous, malformed, or unsupported inputs
9. policy schema v1/default/protected-value behavior
10. overlap precedence and sensitive-header handling
11. encoding and normalization behavior
12. subject identity coherence across formats and retries
13. Docker self-containment
14. bare demo workload/telemetry behavior
15. mounted-run output tree boundary
16. TB/PB production-design documentation
17. repository-contained flow/state diagram consistency

## Verification performed

- `PYTHONPATH=/home/graham/workspace/experiments/agent-skills/skills/acceptance-contract/src python3 - <<'PY' ... AcceptanceBundle.model_validate(...)`: `VALID acceptance bundle cases 17`
- `python3 security/docker_brief_contract.py --acceptance-bundle security/battle/acceptance/acceptance_bundle.json`: `BRIEF CONTRACT: PASS`
- `python3 security/battle/run_acceptance_floor.py --battle /tmp/battle-evaluator-bx8wof_4 --image anonymization-trial`: `status: PASS`, `target_launches: 21`, `acceptance_floor: PASS 17 17 []`, `executed: PASS []`, `campaign: PASS 21 / 21`
- `bash scripts/verify.sh`: `Result: PASS`
- `python3 security/docker_hardening_matrix.py`: `ALL 15/15 holes verified through docker run`
- `python3 security/docker_fuzz_contract.py --trials 20 --seed 7`: `FUZZ: PASS — 20 random trials, seed 7, zero leaks across representations`
- `skills/battle/run.sh invariant-report ...`: `overall_finding: Ready`; `No Judge-confirmed exploits survived 21 attempted attack cases; acceptance-floor coverage is digest-bound and executed.`
- `skills/create-report/run.sh validate /tmp/oai-trial-acceptance-floor-predicate-report/report.json`: `valid: true`

## Non-claims

- The Battle floor is bounded to the required 21 acceptance-floor cases; it is not an unbounded exploit search.
- The 20-trial fuzz run is a sampled check, not exhaustive proof.
- No cloud deployment was performed; production design remains document-backed, not deployment-backed.
