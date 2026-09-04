# Threat model

Scope: the offline, self-contained anonymization container that processes an
untrusted mounted corpus under an authoritative `policy.json`.

## Assets
- Raw input corpus (mounted read-only).
- Policy literals and protected values.
- Generated pseudonyms and the (never-persisted) identity→pseudonym relationship.
- Quarantined/failed artifacts.
- The released corpus + `report.json`.

## Trust boundaries
```
mounted /trial/input (untrusted)  ->  preflight  ->  private staging (trusted)
   ->  independent verifier  ->  atomic publish  ->  /trial/output (release)
```
- Input tree is untrusted: contents, paths, file types, encodings, and embedded
  structures are all attacker-controlled.
- Staging is private and same-filesystem; never consumer-visible.
- Release is written only after verification, report last.

## Adversaries
1. **Malicious input** — crafted files/paths trying to escape the corpus, crash
   the parser, exhaust resources, or smuggle a sensitive value into the release.
2. **Release consumer** — has the output but not the raw input or key/mapping;
   may attempt re-identification.
3. **Log/artifact reader** — may try to recover sensitive data from logs, temp
   names, error text, or the report.

## Controls (and where enforced)
| Threat | Control | Enforced in |
|---|---|---|
| Path escape / special files | `lstat` reject symlink/FIFO/socket/device; distinct non-nested roots | `pipeline._preflight` |
| Sensitive value in schema/path | reject corpus | preflight + adapters + verifier |
| SQL injection | quoted identifiers + bound parameters | `formats.py` (`_quote`) |
| Resource exhaustion | JSON depth/size bounds; streaming CSV/text; SQLite snapshot | `formats.py` |
| Partial/So-so release | staged build → verify → atomic publish → report last | `pipeline.py` |
| Sensitive data leakage | closed error vocabulary; counts/digests-only report; no mapping persisted | `errors.py`, `pipeline.py` |
| Transform bug hidden by self-check | independent verifier rereads output; mutation tests | `verification.py`, `tests/` |

## Residual risks (declared, not solved)
- Quasi-identifier / linkage / agentic re-identification (see `PRIVACY_CONTRACT.md`
  and `report.json` `does_not_establish`). Belongs to a separate production
  risk-plane, tracked as a follow-up — not a claim this pipeline makes.
- Base-image dependency CVEs (`pip`/`setuptools`) — mitigated by pinning; not
  runtime code (runtime deps are empty).

## Abuse-case coverage (deterministic tests)
The test suite exercises: malicious symlink, unsupported/special file, sensitive
literal in path/header/JSON-key/SQLite-identifier, malformed UTF-8, JSON
duplicate-key/NaN/over-depth, SQLite virtual/`WITHOUT ROWID`, nested-alias
overlap, protected/sensitive overlap, non-nested-root violation, crash-free
fail-closed publication, and verifier-sensitivity mutations. These provide
security-specific evidence even when `$hack` is unavailable to the evaluator.
