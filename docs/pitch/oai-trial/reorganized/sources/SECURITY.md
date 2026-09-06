# Security review

I treated both the data and the code transforming it as adversarial surfaces,
across three perspectives (methodology names, not attacker affiliation):

| Lane | Knowledge | Evidence |
|---|---|---|
| **White-box** | full source | Bandit SAST via `$hack` (committed Semgrep receipt scanned 0 target files; no SCA receipt committed — supporting evidence only) |
| **Gray-box** | data contracts | `tests/test_graybox_adversarial.py` (pathological policy/overlap, large fields, deep JSON, SQLite UNIQUE) + verifier mutation tests |
| **Black-box** | only the CLI/mount contract | `tests/test_blackbox_contract.py` (hostile mounted corpus via `python -m anonymization_trial run`, deterministic replay, fail-closed, no stdio leak) |
| **Adaptive red/blue** | evolving Judge-scored lineage | `$battle` (P1+, external dev-only) — see [`BATTLE_OBJECTIVE.md`](BATTLE_OBJECTIVE.md); promoted findings become retained regressions (first: the `source_snapshot` TOCTOU gate + `tests/test_source_snapshot.py`) |

The retained gray/black-box attacks live in this repo, so the evaluator can
reproduce them with `uv run pytest -q` without any external environment. The
domain verifier (`verification.py`) checks anonymization correctness; the SAST
lane below is a separate software-weakness gate.

## Static analysis (SAST)
Receipt: [`hack-audit.receipt.json`](hack-audit.receipt.json)
(`hack.audit_receipt.v1`, status **PASS**).

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 5 |
| LOW | 0 |

The 5 MEDIUM findings are all Bandit **CWE-89 / B608** on the SQLite adapter's
identifier interpolation (`formats.py`). They are **explicitly justified false
positives**: table/column names are quoted through `_quote()` (which doubles
embedded quotes) and never come from untrusted value data; all *values* are
bound as SQL parameters. The same lines carry `# noqa: S608` with that rationale.
No dynamic SQL is built from cell contents.

## Dependency analysis (SCA)
The application's **runtime dependency set is empty** (`pyproject.toml`
`dependencies = []`, stdlib-only). There is no SCA receipt committed, so no
package-level vulnerability result is claimed for the development environment
or container. The Python base image, OS packages, and packaging tools remain
separate dependency-audit surfaces; stdlib-only does not establish their safety.

## Domain-specific controls (verified by tests, not the scanner)
- Input filesystem treated as untrusted: symlinks/FIFO/socket/device rejected;
  distinct non-nested input/output roots; sensitive literal in a path rejected.
- SQLite: identifiers quoted + inventoried; values parameterized; read-only
  source via the online backup API; virtual/`WITHOUT ROWID` tables rejected.
- Parsing bounds: strict UTF-8; JSON depth/size limits; per-file CSV/text processing (not streaming; see SUBMISSION production-hardening boundary).
- No sensitive data in logs/reports: closed `errors.py` vocabulary; `report.json`
  carries counts + digests only and a `does_not_establish` non-claims list.
- Private same-filesystem staging; report-last atomic publish; fail closed.
- Runtime requires no network or host service.

## Non-claims
Static analysis does not establish absence of vulnerabilities, and a SAST
finding (or its absence) does not establish exploitability — see the receipt's
`non_claims`. Independent anonymization verification is a separate gate. See
[`THREAT_MODEL.md`](THREAT_MODEL.md) for the full boundary/adversary model.

## Reproduce
```bash
skills/hack/run.sh audit "$PWD/src" --no-memory-store --receipt-out TEMP_ROOT/oai-hack-audit.json
skills/hack/run.sh sca "$PWD"
```
`$hack` and its scanners are **not** dependencies of the application; they are a
final evidence gate only.
