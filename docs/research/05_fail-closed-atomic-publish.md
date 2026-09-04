# Fail-closed atomic publish (no partial release)

## Requirement (brief)
Verify the complete corpus before marking it ready. Exit non-zero after a
failure. Do not leave a partial corpus that looks ready for release. Keep raw
inputs, mappings, and quarantine out of the release dir and logs.

## Sources
- DEV — "Your CI is green and your pipeline produced nothing" (dir mtime trap): https://dev.to/provedone/your-ci-is-green-and-your-pipeline-produced-nothing-213o
- ConvertToCSV — one malformed record corrupts the output file: https://converttocsv.com/blog/csv-encoding-issues/
- POSIX rename(2) atomicity (same-filesystem rename is atomic) — general Unix semantics referenced by the staging pattern.

## Key findings
- **Publish must be atomic.** Write the whole corpus + report to a **staging**
  directory, verify it, then **atomically promote** (rename) into the release
  location only on full success. `os.rename`/`os.replace` within one filesystem is
  atomic, so a reader never sees a half-written release. The starter writes
  straight into `/trial/output/corpus`, so a verify failure leaves partial output.
- **Verify the staged corpus, not the source.** The starter's `_verify` re-scans
  output for raw sensitive literals — good — but it runs after files are already in
  the final dir, and it can pass on a **cascaded** corpus (a replacement that
  itself contains a sensitive literal). Verification must also check the transform
  invariants, not just literal absence.
- **Fail closed = leave nothing publishable.** On any error: do not promote
  staging; remove/keep-quarantined the staged partial; exit non-zero. The mounted
  `/trial/output` should be empty (or untouched) on failure.
- **Quarantine is separate from release.** Unsafe/malformed files go to a
  quarantine path that is never promoted and never logged verbatim.
- **Directory mtime is not proof of output.** Overwriting files in place doesn't
  change a dir's mtime; don't use it as a success signal — assert on actual files.

## Implication for our implementation
- Pipeline: `output_root/.staging/{corpus,report.json}` → run all transforms →
  verify staged corpus (literal-absence + invariants + SQLite integrity/FK) →
  `os.replace` staging into place; on any exception, `shutil.rmtree(.staging)` and
  return non-zero, leaving `/trial/output` without a release-looking corpus.
- Never write replacement mappings to disk; sanitize the report (counts only, no
  raw values).
- Add a **negative test**: a corpus that fails verification must exit non-zero and
  leave no `/trial/output/corpus`.
