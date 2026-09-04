# Acceptance matrix

Maps every normative requirement in `TRIAL_BRIEF.md` to its implementation owner,
a positive test, a negative/adversarial test, and independent read-back evidence.
Resolves GitHub issue #2. Semantics referenced by number are from
`docs/ANONYMIZATION_SEMANTICS.md`.

| ID | Requirement (brief) | Owner module | Positive test | Negative/adversarial test | Independent evidence |
|----|---------------------|--------------|---------------|---------------------------|----------------------|
| R1 | Valid output in same logical format as each input | `formats/*` adapters | round-trip each format parses | truncated/malformed input rejected | verifier re-parses each output file |
| R2 | Replace every policy-identified value | `matcher.py` | seeded values absent from output | leftmost-longest over the whole input (no chunk splitting) | verifier re-scans decoded output for surviving literals + per-location recompute (text/CSV/JSON) |
| R3 | Stable replacements across files & reruns | `pseudonyms.py` | two runs byte-identical corpus | — | digest of two runs equal |
| R4 | Distinct identities never share type replacement; aliases converge | `pseudonyms.py` (sem #1,#2) | alias→same, distinct→different | forced collision → domain-extend or `namespace_exhausted` | verifier cross-file alias/distinctness check |
| R5 | Protected values preserved | `matcher.py` (sem #5) | protected unchanged, same count | protected∩sensitive overlap → reject | verifier per-literal count parity |
| R6 | Preserve non-sensitive meaning/structure | adapters | non-sensitive cells/keys/rows unchanged | — | verifier recomputes expected output per location for text/CSV/JSON |
| R7 | Preserve CSV headers/rows, JSON structure, SQLite tables/relationships/row-counts/integrity | `formats/*` | header/order/rowcount preserved | sensitive-in-header/key/identifier → reject (sem #9) | CSV/JSON per-location recompute; SQLite `integrity_check`+`foreign_key_check`+rowcount (relational, not per-row-located; triggers/rowid-shadow rejected) |
| R8 | Verify whole corpus before release | `verification.py` (#8) | verified corpus publishes | inject surviving literal → fail | verifier reads staged output from disk, not transform booleans |
| R9 | Keep raw inputs, mappings, quarantine out of release & logs | `pipeline.py` (#4) | release has only corpus+report | prior release cleared before promote; staging is private 0700 | publish writes only `corpus/` + `report.json`; no mapping table is ever persisted |
| R10 | Exit non-zero on failure; no partial ready corpus | `pipeline.py` (#4, sem #11) | success exits 0 | each failure class exits ≠0, no report.json | fresh read: `/trial/output` has no ready marker |
| R11 | Encoding policy (UTF-8/BOM/malformed) | text/csv/json adapters (sem #6,#8) | BOM preserved | malformed UTF-8 rejected, no excerpt | verifier parses JSON with utf-8-sig (BOM) + strict decode |
| R12 | Deterministic overlap precedence, no cascade | `matcher.py` (sem #3,#4) | leftmost-longest selected | replacement-to-source overlap not re-matched | verifier: no selected literal remains |
| R13 | Container: self-contained demo, both `docker run` commands | `Dockerfile`, `__main__` (#9) | bare run demo exits 0; mounted run writes report+corpus | network/service absent still works | clean-image build + read back outputs |
| R14 | Demo: 4 formats, ≥2 sizes (≥10×), throughput+peak mem | `__main__ demo` (#9) | metrics present, verified | verification fail → non-zero | per-run peak RSS (subprocess), records/s, bytes/s |
| R15 | Production design + reproducible 1TB/1PB cost | `SUBMISSION.md`, `costs/` (#10) | cost script reproduces numbers | — | `scripts/estimate_aws_cost.py` output matches doc |
| R16 | Preserve baseline git history; return full repo incl .git | repo (#11) | `git log` shows baseline commit | — | clean-clone audit |

## Bounded-support rejections (documented, fail-closed)
- Non-ASCII literal with `case_sensitive=false` → reject (sem #6).
- Sensitive literal in schema identifier/path → reject (sem #9).
- Protected∩sensitive overlap → reject (sem #5).
- Malformed/unsupported encoding → reject (sem #8).
- SQLite: virtual tables, attached DBs, generated-column writes, or any construct
  the verifier cannot reproduce → reject (#7 bounded).
- JSON: duplicate keys, `NaN`/`Infinity`, depth/size over bound → reject (#6).

Each rejection is a typed error from the closed `errors.py` vocabulary, exits
non-zero, and leaves no ready release.
