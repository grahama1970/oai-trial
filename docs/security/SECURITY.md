# Security review

I treated both the data and the code transforming it as adversarial surfaces.
The domain verifier (`verification.py`) checks anonymization correctness;
separately, the code was run through containerized static and dependency
analysis via `$hack` (Semgrep + Bandit inside Docker, target mounted read-only,
`--network=none`).

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
The trial's **runtime dependency set is empty** (`pyproject.toml`
`dependencies = []`, stdlib-only), so the released image introduces no
third-party runtime packages. The SCA hits (`pip`, `setuptools`, `nltk`) are in
the **local development virtualenv / base image**, not in the shipped artifact.
Mitigation for the base image is to pin a patched `pip`/`setuptools`; it does not
affect the trial's runtime code.

## Domain-specific controls (verified by tests, not the scanner)
- Input filesystem treated as untrusted: symlinks/FIFO/socket/device rejected;
  distinct non-nested input/output roots; sensitive literal in a path rejected.
- SQLite: identifiers quoted + inventoried; values parameterized; read-only
  source via the online backup API; virtual/`WITHOUT ROWID` tables rejected.
- Parsing bounds: strict UTF-8; JSON depth/size limits; streaming CSV/text.
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
skills/hack/run.sh audit "$PWD/src" --no-memory-store --receipt-out /tmp/oai-hack-audit.json
skills/hack/run.sh sca "$PWD"
```
`$hack` and its scanners are **not** dependencies of the application; they are a
final evidence gate only.
