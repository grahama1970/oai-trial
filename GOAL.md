# Immutable Goal

**GOAL (do not edit):** Harden the starter into a cloud data anonymization
pipeline that, for an unseen mounted input bundle, produces a releasable corpus
which satisfies every requirement in `TRIAL_BRIEF.md` — valid same-format output
for CSV/JSON/UTF-8 text/SQLite, every policy-identified value replaced,
replacements stable and identity-coherent across files and reruns, protected
values and non-sensitive meaning preserved, whole-corpus verified before
release, raw inputs/mappings/quarantine kept out of the release dir and logs,
and non-zero exit with no partial release on any failure.

**Contract that must not break:**
- `docker build -t anonymization-trial .`
- `docker run --rm anonymization-trial` → self-contained demo across all 4
  formats at ≥2 workload sizes (largest ≥10× smallest), reports throughput/mem,
  exits 0 only when verification passes.
- `docker run --rm -v "$INPUT":/trial/input:ro -v "$OUTPUT":/trial/output anonymization-trial run`
  → writes only `report.json` + `corpus/` mirroring input paths.

**Deliverables:** implementation + tests + `Dockerfile`, completed
`SUBMISSION.md` (incl. production cloud design, 1 TB & 1 PB cost arithmetic,
flow diagram, AI-tool disclosure). Preserve baseline git history.

**Definition of done:** the two required `docker run` commands pass on a clean
build with a fixture-generated corpus, verification gates the release, and
failure paths exit non-zero without leaving a release-looking corpus.
