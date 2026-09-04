# Safe SQLite value rewriting + integrity

## Requirement (brief)
Preserve SQLite tables, relationships, row counts, and integrity. Same-format
output. Verify before release.

## Sources
- SQLite Foreign Key Support: https://sqlite.org/foreignkeys.html
- SQLite forum — changing columns in a table with FKs, views, triggers: https://sqlite.org/forum/info/fc5e8ad85a27d61caf7f4583e5703292edd4ce567d54fe8e99f06cba032bd648
- SQLite.work — modifying columns with FKs, commit failures after schema change: https://sqlite.work/modifying-columns-in-sqlite-with-foreign-keys-handling-commit-failures-after-schema-changes/
- Upscene — improving integrity with FKs: https://www.upscene.com/articles/article/6/improving-database-integrity-in-sqlite-by-using-foreign-key-constraints
- runebook — FK clause / triggers for integrity: https://runebook.dev/en/docs/sqlite/syntax/foreign-key-clause

## Key findings
- **We only change VALUES, not schema.** The FK-cascade horror stories are about
  schema changes; our task is `UPDATE` of cell values. That keeps us out of the
  table-rebuild path — but only if we respect the traps below.
- **Foreign keys + ON UPDATE CASCADE:** if a sensitive value is a **parent key**
  and a child FK references it, updating the parent can cascade (or fail) depending
  on the FK's `ON UPDATE` action and whether `PRAGMA foreign_keys` is on. To keep
  referential integrity, the **same identity must map to the same pseudonym in
  every table** (our deterministic transform guarantees this), so parent and child
  values stay consistent even if updated independently. (sqlite.org/foreignkeys)
- **Triggers fire on UPDATE.** A `BEFORE/AFTER UPDATE` trigger can mutate other
  rows or reject the write. (runebook)
- **Generated/computed columns cannot be UPDATEd** — attempting to write them
  errors. Must skip columns where `PRAGMA table_info` / `table_xinfo` marks them
  generated.
- **Verify with both checks:** `PRAGMA integrity_check` (physical/structural) AND
  `PRAGMA foreign_key_check` (referential). Starter only runs `integrity_check`.
- Views recompute from base tables — no direct update needed, but a sensitive
  literal could still surface through a view during verification.
- `sqlite_sequence`, indexes on transformed columns, collations (`NOCASE`), and
  `BLOB` vs `TEXT` typing all matter; only rewrite `TEXT`/`str` values.

## Implication for our implementation
- Enumerate columns via `PRAGMA table_info(t)` (add `table_xinfo` to detect
  generated columns) and **skip generated columns**.
- Rewrite only string-typed cell values; keep BLOBs untouched.
- Wrap all updates in a transaction; after commit run **both**
  `PRAGMA integrity_check` and `PRAGMA foreign_key_check`, and assert row counts
  per table are unchanged.
- Because the transform is deterministic across tables, FK parent/child values
  stay aligned without special ON UPDATE handling — but document this dependency.
- **Candidate for a reusable `best-practices-sqlite` skill** (untrusted-DB-safe
  value rewriting).
