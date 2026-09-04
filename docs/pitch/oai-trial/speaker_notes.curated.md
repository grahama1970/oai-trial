# OpenAI technical briefing — 36 minutes + 4 minutes for interruption

Runtime candidate: `0795dc66deaa5991cd34959c6d8b81f80a8042a0`.
This is an engineering evaluation, not a sales pitch. Commands run from the repo
root. Keep the built deck and prepared outputs open before the meeting. Explain slides
full-screen; switch to a compact claim on the left and code in the right two-thirds
for the identity, typed-mutation, and publication stops only. Use
`qa/debugger_stops.json` for explicit local commands and recorded fallbacks. Do not
spend presentation time installing dependencies, building Docker, or debugging
browser transport. The terminal, code and test output are the depth layer.

## 01-brief — The assignment
Time: 4 minutes (00:00–04:00)
Claim: A release must replace declared literals across four formats without
changing protected meaning or identity, and must refuse ambiguous inputs.
Evidence: `TRIAL_BRIEF.md` §§ Required behavior, Container contract;
`docs/ACCEPTANCE_MATRIX.md` R1–R16. Claim ID: brief.
Live jump: Open the brief beside `README.md`; point at the two required Docker
commands and the policy contract. Explain that policy.json, not a detector, owns
what is sensitive. Use the prepared demo output; build before the meeting.
Likely challenge: Why call this anonymization rather than pseudonymization?
Concise answer: The assignment uses anonymization, but the implemented guarantee
is literal replacement with coherent pseudonyms. I explicitly do not establish
re-identification resistance or discovery of unlisted identifiers.
Required qualifier: Authoritative literal policy; no claim of formal anonymity.
Transition: The release decision is the core architecture, not the string replacement.

## 02-architecture — The transformer cannot authorize release
Time: 5 minutes (04:00–09:00)
Claim: Private staging is reread and re-derived before report-last authorization.
Evidence: `src/anonymization_trial/pipeline.py::run_pipeline`, `_publish`;
`src/anonymization_trial/verification.py::verify_corpus`. Claim ID: local.
Live jump: Open `run_pipeline`: policy load, inventory, staging, verify, source
digest check, sealed digest, publish. Then open `_publish` and point at the last
`os.replace(tmp, report_path)`. Keep the local-pipeline SVG visible beside code.
Likely challenge: Is the verifier independent if both sides share code?
Concise answer: It independently rereads the source and staged artifacts and
re-derives expected values. It shares replacement primitives, so correlated
matcher defects remain possible. It does not merely trust a success flag.
Required qualifier: Independent reread/re-derivation, not a separate implementation.
Local failures are FAILED/UNCOMMITTED; quarantine belongs to the production design.
Transition: To re-derive anything, the ambiguous matching semantics must first be frozen.

## 03-semantics — Identity is stable; ambiguity is rejected
Time: 8 minutes (09:00–17:00)
Claim: Aliases share an identity; selected spans come only from original input;
bounded domains and contradictory policies fail closed.
Evidence: `docs/ANONYMIZATION_SEMANTICS.md` §§1–9;
`pseudonyms.py::build_replacements`, `matcher.py`; `formats.py` SQLite schema scan;
`verification.py::_typed_equal`, `_verify_sqlite_locations`.
Claim ID: semantics.
Live jump: Trace two aliases through `(type, subject_id)`, then show an overlapping
match on the original string. Spend the second half on JSON true versus 1 and
SQLite INTEGER versus REAL: open `security/tests/test_typed_scalar_verification.py`.
Run `uv run pytest -q security/tests/test_typed_scalar_verification.py` if time permits.
Explain schema-object rejection: a view literal can leak despite clean table cells.
Likely challenge: Why reject formats or collisions instead of trying harder?
Concise answer: The eight-hour contract favors a bounded refusal over a silent
semantic change. Phone/IP capacity and collision-search limits are explicit.
JSON scalar types are compared strictly; SQLite values are checked at their rowid.
Required qualifier: Per-file materialization; CSV rows are iterated, not TB-scale
streaming. The local namespace is public and unkeyed. No cross-tenant unlinkability.
Transition: Correct transformed values still do not make a released corpus.

## 04-reliability — A transformed corpus is not a release
Time: 5 minutes (17:00–22:00)
Claim: Only report.json written last authorizes READY over the verified corpus.
Evidence: `pipeline.py::_publish`; `security/tests/test_publish_hardening.py`;
`tests/test_pipeline_failclosed.py`. Claim ID: release.
Live jump: Show the release-state SVG, then the report evidence chain in a prepared
output. Trace STAGED → REREAD/VERIFY → SEALED → CORPUS PUBLISHED → report.json LAST
→ READY. Optional command: `uv run pytest -q security/tests/test_publish_hardening.py`.
Explain a crash between corpus promotion and report creation: corpus bytes may
exist, but no READY marker exists. This is not a multi-file transaction.
Likely challenge: Can another writer change the bytes after verification?
Concise answer: I recheck the sealed digest immediately before promotion. This
assumes a trusted, single-writer staging filesystem and read-only input mount.
External hostile writers and swap-and-restore attacks are explicitly outside scope.
Required qualifier: Failures produce no new READY release; an old valid release
may remain if the new run fails before publication. No claim of universal rollback.
Transition: The useful evidence is what happens when we deliberately violate these assumptions.

## 05-evidence — Try to falsify the release
Time: 5 minutes (22:00–27:00)
Claim: Concrete output readback and adversarial mutations are stronger evidence
than scanner labels or a large test count.
Evidence: `qa/runtime-evidence.json`; `security/tests/test_sqlite_location.py`;
`security/tests/test_typed_scalar_verification.py`; `security/tests/test_publish_hardening.py`.
Claim ID: evidence.
Live jump: `docker run --rm anonymization-trial` (or show the saved receipt).
Show the four formats, the 100→1000 logical-record step, and observed RSS/throughput.
Then run `uv run pytest -q security/tests/test_sqlite_location.py::test_swapped_sqlite_subject_pseudonyms_rejected`.
Open the test and point at the mutation, not just its green result: swapping two
valid pseudonyms preserves aggregate presence but violates row identity.
Second example: true→1 / INTEGER→REAL violates meaning despite Python equality.
Likely challenge: What does the 10× benchmark establish about a terabyte?
Concise answer: Nothing about TB throughput. It establishes a reproducible small
container demo and records measured costs at two sizes. Scaling is a separate model.
Required qualifier: Synthetic input, real container/CLI; observed measurements are
not SLA guarantees. Bandit is supporting evidence; no vulnerability-free claim.
Transition: Production must preserve these authorization semantics across many workers.

## 06-production — Scale the work; keep one release decision
Time: 5 minutes (27:00–32:00)
Claim: AWS workers can partition work while a manifest/pointer gates the corpus release.
Evidence: `docs/production-architecture.md` §§ Flow, Distribution, SLA, Cost;
`costs/example-estimates.json`, `scripts/estimate_aws_cost.py`. Claim ID: production.
Live jump: Use the AWS SVG. Walk intake → format-aware partitions → workers →
verifier fan-in → immutable corpus manifest → active pointer. Discuss retries and
quarantine, then run `python scripts/estimate_aws_cost.py --inputs costs/aws-us-east-1-inputs.json`.
Show 1 TB ≤1h and 1 PB ≤7d targets and the model totals, not a provider comparison.
Likely challenge: Why trust these cost and throughput estimates?
Concise answer: They are an explicit scenario: 200 workers at 20 MB/s each,
transform plus verify and retries, three stored copies, cited unit prices. Rates,
quotas, object size, retention and throughput must be validated before deployment.
Required qualifier: Modeled, not deployed or benchmarked at TB/PB; price tables
require confirmation. OCI/data/verification contracts are portable; AWS is the only
worked reference. Local report-last is not the cloud pointer implementation.
Transition: The final engineering decision is where to stop claiming certainty.

## 07-nonclaims — Know what this release does not establish
Time: 4 minutes (32:00–36:00)
Claim: The literal-policy guarantees do not imply anonymity or production readiness.
Evidence: `docs/PRIVACY_CONTRACT.md` §§ Verified locally, Not established;
`SUBMISSION.md` Known gaps. Claim ID: nonclaims.
Live jump: Open report.json's `does_not_establish` beside the privacy contract.
Summarize three choices: reject ambiguity; preserve evidence; avoid building a
platform. Leave re-identification analysis and adaptive Battle outside this release.
Likely challenge: What would you implement next with more time?
Concise answer: First validate production throughput, object-size distributions,
key scope and billing assumptions against a representative corpus. Discovery and
re-identification need separate goals and evidence; they are not hidden in this claim.
Required qualifier: No unlisted-PII discovery, formal anonymity, external-linkage
resistance, TB/PB benchmark, or vulnerability-free assertion.
Transition: That is the boundary I would defend; which decision would you like to inspect?

## Q&A reserve
4 minutes (36:00–40:00). There is no sales ask and no eighth slide. Follow questions
into the repo; skip an optional live command rather than rush an invariant.
