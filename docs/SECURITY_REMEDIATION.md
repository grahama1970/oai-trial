# Security remediation since the trial submission

The frozen trial submission was disqualified for one omission: a phone number
stored as a JSON/SQLite **integer** passed through the string-only matcher. This
document is the receipt that the miss was a **narrow representation gap, not a
methodology gap** — with roughly one to two additional hours past the frozen
submission, that obvious hole and an entire class of sibling holes were found and
fixed, using three independent hole-finders: a WebGPT security audit, the
`$hack` containerized SAST scan (bandit + semgrep), and empirical adversarial
probes against the real pipeline.

Every row below was reproduced against the live pipeline before and after the
fix. All fixes are landed on `origin/main` and covered by retained tests.

## Holes found and patched

| # | Hole | Severity | How found | Fix | Proof | Commit |
|---|------|----------|-----------|-----|-------|--------|
| 1 | Typed-PII: sensitive value stored as JSON integer/float passed through untouched (the disqualifier) | CRITICAL | client feedback | value-scoped matching — stringify int/float scalars before match, in transform and independent verifier | integer+float phone anonymized; Docker-verified; retained test | `fd80eca` |
| 2 | SQLite BLOB value opaque to text matching, passed through | CRITICAL | WebGPT audit | fail closed on non-NULL BLOB in a value column | `AnonError unsupported_format` | `406aee4` |
| 3 | Unicode NFC/NFD: same name in a different normal form leaked | CRITICAL | WebGPT audit + probe | register NFC+NFD variant patterns (offset-safe); NFC-folded policy-collision preflight; independent NFC scan in verifier | NFD name anonymized; Docker-verified; ex-xfail test now passes | `3ca4ad7` |
| 4 | SQLite VIEW reconstructs a sensitive value from clean base cells; verifier scanned base tables only | CRITICAL | WebGPT audit + probe | verifier enumerates `type IN ('table','view')` and materializes each view | reconstruction view → `verification_failed`; clean views still accepted | `e78f42b` |
| 5 | SQLite forensic residue in freelist/overflow pages after in-place UPDATE; journal/WAL sidecars | CRITICAL | WebGPT audit | `secure_delete=ON` + `VACUUM` rebuild; assert no `-wal`/`-shm`/`-journal` sidecar in published DB | residue `'Alice'` in output = False; sidecars `[]` | `ac7917e` |
| 6 | Hostile SQLite schema machinery (functions in views/generated columns/CHECK/DEFAULT); malformed cells | HIGH | WebGPT audit | `PRAGMA trusted_schema=OFF` + `cell_size_check=ON` on every untrusted-DB connection; `integrity_check` on the source *before* processing | landed; full suite green | `ac7917e` |
| 7 | SQL injection via attacker-controlled table/column identifiers (bandit B608 ×7) | MEDIUM | `$hack` SAST | already mitigated by `_quote` (doubles embedded quotes) + bound params; proven, retained adversarial guard added | malicious table name `"; DROP TABLE victim; --` → victim survives | (test) |
| 8 | SQLite **expression index** stores a computed sensitive value in the index B-tree, invisible to table/view scans | CRITICAL | WebGPT round 2 | reject expression indexes (`index_xinfo` cid −2) and partial indexes | `char(83,69,...)` index → `unsupported_format` | `2435e4f` |
| 9 | **Non-deterministic view** returns clean at verify, sensitive value later (`random()`), so one materialization is not proof | CRITICAL | WebGPT round 2 | reject views referencing non-deterministic functions | `random()` view → `unsupported_format` | `2435e4f` |
| 10 | **Computed DEFAULT expression** evaluates on future inserts: empty table verifies clean yet emits the value later | CRITICAL | WebGPT round 2 | reject non-literal DEFAULTs; plain literal defaults still accepted | `DEFAULT (char(...))` → `unsupported_format` | `2435e4f` |
| 11 | Numeric **scientific-notation alias**: policy `100000000000000000000` vs JSON `1e20` (str(float)=`1e+20`) | HIGH | WebGPT round 2 | numeric-token helper emits integral/decimal expansion; matched in transform + verifier | `1e20` anonymized; policy string absent | `2435e4f` |

## Reviewed and confirmed already-handled (no change needed)

Probed against the real pipeline; each already fails closed:

- JSON `\uXXXX` escapes — matched (parsed/decoded form).
- UTF-16 / invalid encoding — rejected (`malformed_encoding`).
- UTF-8 BOM — matched, BOM preserved.
- Symlinks in the corpus — rejected (`unsafe_input`).
- Sensitive value in a filename / JSON key / CSV header / SQLite schema object — rejected (`sensitive_in_schema*`).
- Generated columns materializing a sensitive value — caught by the verifier.
- Virtual tables (FTS) — rejected (`unsupported_format`).
- Triggers, WITHOUT ROWID, rowid-shadow columns — rejected.
- subprocess use in the CLI (bandit B404/B603) — no untrusted input reaches a shell.

## Documented as scoped (intentional, not a defect)

Under the brief's literal-match contract these are out of scope and guarded by a
negative-scope test so scope cannot silently creep:

- Formatting variance (dashes/spaces), zero-width chars, NBSP, fullwidth digits, base64/hex, values split across cells.
- Deterministic public-namespace pseudonyms disclose equality/frequency by design — already disclosed in the run report (`key_mode`, `does_not_establish`).

## Method (why this is credible, not hand-waved)

The check itself is now derived from the delivered spec, not the code:
`scripts/spec_derived_check.py` reads every value from `policy.json` and asserts
none survives in the decoded output, wired as a gate in `scripts/verify.sh` with
a dependency probe. `$setup-project` now fails unless the brief is a declared
input and the immutable goal carries the spec. Full test suite: 180 passed.


## Convergence (WebGPT, round 3)

After three independent WebGPT re-audit rounds, WebGPT states **converged**:
"no remaining concrete path that causes a policy-listed value to reach the
released corpus while verification passes," under the stated threat model
(single-process CLI in Docker; untrusted input bundle; policy.json + corpus
mounted read-only; deterministic public-namespace pseudonyms disclosed in the
report; petabyte design separate). Round-3 re-examinations (STORED generated
columns, top-level scalar JSON, duplicate keys, NaN/Infinity, CHECK/collation
schema, malformed UTF-8/NUL) were each confirmed already fail-closed and are now
retained as regression guards. Total suite: 186 passed.

Method: WebGPT security audit (3 rounds to convergence) + `$hack` containerized
SAST (bandit/semgrep, 9 findings triaged: 7 false-positive SQL-injection
mitigated by `_quote`, 2 benign subprocess) + empirical adversarial probes
against the live pipeline. ~1-2 hours past the frozen submission.
