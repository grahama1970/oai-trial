# Optional RapidFuzz name-alias discovery

This is an operator-requested post-trial extension. The previously qualified
`9ebb447` archive is unchanged and does not qualify this new functionality.
The exact matcher remains the default; no fuzzy score can authorize a release.

## Main skill and file interface

The shared skill is **`anonymize-data`**, matching the catalog's verb–object
names such as `extract-entities` and `clean-text`. Its `run.sh` only invokes this
project's installed CLI. All input handling, discovery, approval, transformation
and verification logic lives in `src/anonymization_trial/`.

```bash
# From the installed skill directory:
./run.sh setup
./run.sh --input /data/exports --policy /data/policy.json --output /data/release
# Equivalent project CLI:
anonymization-trial anonymize --input /data/export.json --policy /data/policy.json --output /data/release
```

Use a supported file or directory of CSV/JSON/TXT/SQLite files, a separate policy
file, and a dedicated empty output directory. Inputs, policies, work artifacts
and releases must not overlap. Input copies are private snapshots; originals are
not modified. Existing `run --input BUNDLE` behavior and Docker evaluator commands
remain available.

## Discovery → review → exact policy → release

Install the optional dependency with `uv sync --extra dev --extra discovery`.
RapidFuzz is pinned in the project; it is imported only by discovery/approval.

```bash
anonymization-trial discover --input /data/exports --policy /data/policy.json \
  --output /data/work/candidates.json --threshold 90 --margin 5
# Inspect candidates.json and explicitly choose a candidate ID.
anonymization-trial approve-discovery --input /data/exports --policy /data/policy.json \
  --review /data/work/candidates.json --approve CANDIDATE_ID \
  --output /data/work/approved-policy.json
anonymization-trial anonymize --input /data/exports --policy /data/work/approved-policy.json \
  --output /data/release
```

Example: policy `Alice → subject_id person-a`; observed whole field `Alicee`.
Discovery can propose `Alicee` as an alias. Approval creates a new **literal**
rule for `Alicee` with the same identity, so both become `Person-390cb11ced`.
Without that approval the original literal policy is unchanged: its `Alice`
substring can still match inside `Alicee`, leaving the trailing `e`. Discovery
itself never modifies data or silently changes that original matching contract.

## Bounded behavior

- Compare whole CSV data cells, JSON string values, SQLite text cells, and text
  lines. Do not scan headers, JSON keys, schema objects, or arbitrary name spans
  within paragraphs. This is not a general PII/NER system.
- Seed only policy rules of type `name`. Name-shaped strings are 3–128 characters
  with letters, spaces, apostrophes, hyphens or periods; digits and punctuation
  such as `@`, `/`, `_` are excluded. This grammar is not proof of personhood.
- Use `rapidfuzz.fuzz.ratio` with explicit ASCII-only folding and no implicit
  preprocessing or Unicode normalization. Similarity is not a probability.
- Rank distinct identities, not aliases independently. Exact ties always refuse;
  close competitors refuse unless separated by the configured margin.
- Default threshold 90 (allowed 80–100), margin 5 (allowed 0–20). Non-finite
  settings refuse. At most 1000 seed name rules and 10000 text values per run;
  exceeding either limit fails instead of emitting a partial review.
- Protected-containing and already-known whole values are not proposed. Approval
  also runs the real policy compiler, including partial-overlap/conflict checks.
- Approval recomputes the report against current policy/corpus bytes and the
  pinned scorer version. Unknown/duplicate IDs and inconsistent or stale reports
  refuse. A trusted operator still owns the identity decision; this is not a
  cryptographic signature or user-authentication system.

## Artifacts and privacy

`anon.discovery_review.v1` contains policy/corpus digests, scorer version,
threshold/margin, typed candidates, counts and a producer validation stamp.
Candidates include raw names: the review is a **private work artifact**, not a
release report. Console output contains counts, not those names.

Approval writes an exact policy and `<policy>.approval.json` with selected IDs
and source/output digests. The consumer policy compiler runs before writing.
Both artifact types state `release_ready: false`; a compiled policy is not a
verified corpus. Files are created mode 0600, never overwrite existing files,
and may not be called `report.json` or written inside an existing release.

## Docker

The default image keeps the exact engine's standard-library-only runtime.
Enable the optional dependency explicitly:

```bash
docker build --build-arg INCLUDE_DISCOVERY=1 -t anonymization-trial:discovery .
# UID/GID keeps private work files readable by their host owner.
docker run --rm --network=none --user "$(id -u):$(id -g)" \
  -v "$INPUT":/data/input:ro -v "$POLICY":/data/policy.json:ro \
  -v "$WORK":/work anonymization-trial:discovery discover \
  --input /data/input --policy /data/policy.json --output /work/candidates.json
```

For one file, preserve its suffix in the mount target, e.g. `/data/sample.csv`.
Use the same image/mounts for `approve-discovery`, writing `/work/approved.json`,
then mount that approved policy read-only when running `anonymize` into an empty
release directory. No network, Memory, LLM or database service is used at runtime.

## Retained evaluation

`fixtures/discovery_eval.json` repeats the real project CLI matrix three times.
The shared skill's fixture repeats those same tests **through its wrapper**,
including a wrong-installed-project refusal. The matrix covers four-format
readback, default behavior, private artifacts, original-input preservation,
ties/near ties, same-identity aliases, malformed files/settings, resource limits,
forged/stale reviews, explicit approvals, protected overlaps, unsafe paths,
nonempty output and symlinks/special files. Docker evidence is separate from
source-tree pytest. None of this establishes general identity accuracy or
production-scale discovery.
