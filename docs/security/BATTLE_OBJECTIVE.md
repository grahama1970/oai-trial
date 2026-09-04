# Adaptive red/blue lineage objective (`$battle`, P1+ external lane)

`$battle` is a **development-only** hardening tool; it is never part of the
shipped runtime image. Its value here is adaptive lineage governed by an
**independent Judge**: Red cannot certify an exploit, Blue cannot certify a
patch, and the scoreboard derives only from Judge replay receipts — the same
"the thing under test cannot certify itself" principle as our verifier.

## Immutable security goal
> Find any sequence of permitted input, filesystem, process, policy, format, or
> release-state manipulation that causes an invalid or privacy-unsafe corpus to
> obtain a valid READY state, leaks source/mapping data, or violates a declared
> preservation invariant.

## Red success signals (Judge-confirmed, reproducible)
`unsafe_release_ready`, `sensitive_literal_released`, `protected_value_mutated`,
`identity_coherence_broken`, `structure_invariant_broken`, `verifier_false_accept`,
`report_corpus_binding_bypass`, `source_snapshot_bypass`, `raw_or_mapping_leak`,
`resource_bound_escape`, `host_boundary_escape`.

## Blue success signals
The exact Red proof now fails **and** all existing correctness tests still pass
**and** the independent Judge replays both. A "defense" that blocks an attack by
breaking legitimate behavior is not a defense (Battle's TDSR/FDSR distinction).

## Seeded attack families -> coverage status
| Family | Retained regression in-repo |
| --- | --- |
| Publication lineage (kill at transition, stale/foreign report, corrupt stage) | `test_pipeline_failclosed.py`, `test_verifier_sensitivity.py` |
| Source-snapshot / TOCTOU (mtime-preserved content change, inode/hardlink) | `test_source_snapshot.py` (+ pipeline `SOURCE_CHANGED` gate) |
| Matcher lineage (nested/prefix/suffix, aliases, case, long prefixes) | `test_matcher.py`, `test_graybox_adversarial.py` |
| Format parser lineage (CSV quote/newline/BOM, JSON depth/dup/NaN, SQLite PK/FK/generated) | `test_formats.py`, `test_json.py`, `test_sqlite.py`, `test_graybox_adversarial.py` |
| Verifier lineage (restored literal, wrong/swapped pseudonym, dropped/extra file, protected change) | `test_verification.py`, `test_verifier_sensitivity.py` |
| Resource/complexity lineage | `test_graybox_adversarial.py` (bounded), production design |

## Isolation & landing policy
Battle runs in git-worktree / Docker digital-twin isolation and **must not patch
`main` automatically**. A patch may be considered for landing only after: Red
proof reproduced -> Blue patch blocks the exact proof -> full deterministic suite
passes -> independent verifier passes -> no new release bypass found.

## Retain-as-regression loop (the point)
```
battle anomaly -> Judge reproduces -> focused ticket -> minimal fail-before-fix
fixture -> patch -> retained regression in oai-trial -> battle reruns lineage
```
So the evaluator reproduces every important finding with `uv run pytest -q`
alone — no battle environment required. The `source_snapshot` gate + regression
above is the first such promoted finding.

## Command (external, opt-in)
```bash
skills/hack/run.sh battle "$PWD" --rounds 100      # delegates to $battle
```
If Battle finds nothing, that is supporting evidence, not proof. If it finds
something, promote it into a deterministic regression before relying on it.
Tracked as issue #13.
