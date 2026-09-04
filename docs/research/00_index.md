# Research index — oai-trial anonymization

Deep research supporting the implementation, mapped to `TRIAL_BRIEF.md`
requirements. Each file lists external sources (URLs), key findings, and the
concrete implication for our pipeline. Gathered via `$brave-search`, `$dogpile`,
and the arXiv API on 2026-09-04.

| # | Requirement area | File |
|---|---|---|
| 01 | Deterministic pseudonymization + identity coherence | `01_deterministic-pseudonymization.md` |
| 02 | Safe SQLite value rewriting + integrity | `02_sqlite-safe-rewrite.md` |
| 03 | Overlap precedence, protected values, encoding/BOM | `03_overlap-precedence-encoding.md` |
| 04 | Streaming at TB/PB scale, bounded memory | `04_streaming-scale.md` |
| 05 | Fail-closed atomic publish (no partial release) | `05_fail-closed-atomic-publish.md` |
| 06 | Container contract / Dockerfile | `06_docker-container-contract.md` |
| 07 | Cloud cost + capacity design (1 TB / 1 PB) | `07_cloud-cost-design.md` |
| 08 | Academic grounding (arXiv) | `08_arxiv-papers.md` |

## Proof boundary

- Source URLs are retrieved and cited; page bodies were read only where quoted.
- arXiv entries in file 08 are title/id-verified from the API; abstracts not yet
  fully read.
- Cloud prices (file 07) are **not yet pinned** to a dated price page — the
  SUBMISSION.md cost math must cite a specific region + price date before use.
