# Research first; reuse before custom code

## Working method

Frame the challenge before choosing an implementation. Use `$dogpile` to search current Brave web results, arXiv papers, GitHub implementations, and other relevant sources. Inspect the actual methods and code, not just titles. Check pre-existing projects and skills for components to reuse or compose. Prefer a suitable existing solution; write custom code only for the remaining contract gap. Newer is not automatically better: fit, dependencies, licensing, and verifiability decide adoption.

This is a development workflow, not a dependency of the shipped offline engine. The research index records Brave, dogpile, and arXiv gathering; the reuse audit records external repositories and existing skills examined. These are historical records, not a claim that every available source was exhaustively searched.

## Concrete choices in this project

| Candidate or existing component | Decision and reason | Current boundary |
|---|---|---|
| `extract-entities` / FlashText-style matching | Examine longest-match and boundary ideas; do not import its identifier-detection policy into exact literal replacement. | The shipped matcher is local Aho-Corasick. No comparative benchmark established it as superior to FlashText. |
| `clean-text` and Presidio | Examine encoding and overlap handling; retain the supplied policy's literal semantics rather than silently normalize text or add detector authority. | Sensitive/protected conflicts reject. Historical protected-first notes were superseded. |
| Python standard library | Reuse `csv`, `json`, `sqlite3`, `hashlib`, and filesystem primitives for format handling, allocation, and publication. | Local contract logic remains custom; format parsing was not reinvented. |
| RapidFuzz | Reuse the optional similarity scorer rather than write fuzzy string matching. | Post-trial discovery only; explicit approval and exact verification still govern release. |
| Existing skills | Compose research, review, evaluation, and presentation tooling during development; later expose the project CLI through the thin `anonymize-data` wrapper. | Skills do not become evaluator-image runtime dependencies. Wrapper mechanics remain in Extra Credit. |

## Research that led to narrower code changes

| Research input | Adaptation in this repository | Not implemented |
|---|---|---|
| [SPIA, arXiv:2604.21211](https://arxiv.org/abs/2604.21211) | Subject-coherence checks and explicit limits on what the release establishes. | Subject-level inference attack evaluation. |
| [Synthetic DICOM validation, arXiv:2508.01889](https://arxiv.org/abs/2508.01889) | Known-truth synthetic fixtures and deliberately corrupted output checks. | DICOM support or the paper's benchmark. |
| [AnonShield, arXiv:2606.15650](https://arxiv.org/abs/2606.15650) and [Proteus, arXiv:2603.06540](https://arxiv.org/abs/2603.06540) | Explicit algorithm/scope labels and disclosure of the public deterministic namespace. | HMAC, secret-key management, encryption, or rotation. |

These are adapted ideas, not reproductions of the papers. Exact source mechanisms: `verification.py::_verify_subject_level`, `security/tests/test_verifier_sensitivity.py`, `scripts/qualify_submission.py::readback`, and `pseudonyms.py::_digest`.

## Chronology and time boundary

The committed history supports research-led refinement, not a claim that all research finished before any code existed. Initial research and semantics (`813fdf3`) precede the hardened matcher change (`7248031`). The adoption memo (`12cefd7`) precedes the privacy-contract, subject-check, namespace-label, and verifier-sensitivity change (`bff518c`). Research and implementation also proceeded together; later review produced further corrections.

Estimated effort: about 8 hours—3 research, 2 implementation/testing, 1 extras, 2 polish. Retrospective estimate; active time was not instrumented. Commit history records when changes landed, not active hours. Later corrections and requested additions remain separately documented.

## Source navigation

- Research gathering: `docs/research/00_index.md`.
- Historical reuse decisions: `docs/research/09_reuse-audit.md`.
- Historical adoption memo: `docs/research/RESEARCH-ADOPTION.md` (not a current capability inventory).
- Current code and tests take precedence over historical proposals.
