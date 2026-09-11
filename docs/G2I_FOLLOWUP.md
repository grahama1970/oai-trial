# Follow-up on the anonymization trial

This is a short, honest account of a defect in my submission, its root cause,
and the remediation I did afterward. It is not a re-submission and does not
change the trial outcome. I am sharing it because how I handle a miss is more
informative than the miss itself.

## The defect

The submission anonymized sensitive values only when they were stored as
strings. A phone number stored as a JSON integer or a SQLite `INTEGER` passed
through untouched. For a privacy pipeline that is a disqualifying leak.

## Root cause — the honest version

The failure was not "I forgot a case." It was a process error: the acceptance
check was written to match what my code already did, not derived from the
delivered spec. `policy.json` lists the exact sensitive values; the correct,
spec-derived check is simply "none of those values appears in the decoded
output, in any representation." My fixtures, my transform, and even my
"independent" verifier all shared one invisible assumption — that PII is a
string — so no test could fail. The brief actually named the trap: "the same
synthetic identity can appear in every format."

## What I did afterward (~1-2 hours)

- **Value-scoped matching.** Numeric scalars are canonicalized (integer/decimal
  expansion, so `1e20` matches `100000000000000000000`) and matched in the
  transform and in a genuinely independent verifier that shares no helper with
  the producer.
- **Representation hardening across the class**, each reproduced and fixed:
  SQLite BLOB (fail-closed), Unicode NFC/NFD, view reconstruction, freelist
  residue, hostile-DB pragmas, expression/partial indexes, non-deterministic
  views, computed DEFAULT expressions, schema-DDL literals, and persistent
  SQLite header integers. All 17 are listed in
  [`SECURITY_REMEDIATION.md`](SECURITY_REMEDIATION.md).
- **A spec-derived acceptance gate.** `scripts/spec_derived_check.py` reads the
  values from `policy.json` and asserts none survives in the decoded output; it
  is wired into `scripts/verify.sh` with a dependency probe proving the result
  depends on the policy file, not a hardcoded list.
- **Deterministic Docker verification anyone can rerun.**
  `security/docker_brief_contract.py` builds the image, runs both brief commands,
  and checks the released bytes with a representation-aware independent oracle
  (parsed JSON, numeric canonicalization, NFC/NFD, SQLite cells + schema DDL +
  header integers, and `report.json`), asserting a precondition that each
  sensitive value is actually present in the input.
  `security/docker_hardening_matrix.py` runs 15 adversarial holes through the
  real `docker run` and reads back the container output.

## How to check it yourself

```bash
python3 security/docker_brief_contract.py     # build + both brief commands + leak scan
python3 security/docker_hardening_matrix.py   # 15 adversarial holes through docker run
```

Both exit non-zero on any failure and record the git commit and built image id,
so the verdict is reproducible rather than a claim in prose.

## What I am not claiming

This proves no policy value survives in the covered formats under the
single-process Docker threat model. It does not claim resistance to external
re-identification, differential privacy, or petabyte-scale operation — those
were disclosed non-goals in the original submission and remain so.
