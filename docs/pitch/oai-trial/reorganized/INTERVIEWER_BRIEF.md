# Interviewer Brief — OAI Anonymization Trial

[Repository](https://github.com/grahama1970/oai-trial) · [Full code-assisted explanation](NARRATIVE.md) · [Presentation contents](TOC.md)

## The challenge and approach

A deterministic, policy-bounded pseudonymization pipeline transforms **CSV, JSON, UTF-8 text and SQLite** while preserving explicitly protected values and supported logical structure.

> **Humans supply semantic privacy decisions; code enforces and checks the declared literal contract.**

The policy identifies sensitive literals, protected literals and aliases sharing a **policy-declared identity**. For example, Alice and A.L share a pseudonym only because the policy declares that relationship. KEEP is protected because it appears in the protected list—not because the program understands the word.

The flow is **compile policy → transform → fresh verification → report-last publication**. Sensitive/protected literal conflicts reject mechanically; the compiler does not resolve semantic privacy contradictions.

## What the implementation establishes—and does not

| Mechanism | Boundary |
|---|---|
| Aho-Corasick matching; explicit leftmost-longest selection and non-cascading replacement | Known-string matching, not general PII detection. The custom matcher is a contract-fit choice, not benchmark-proven superiority over FlashText. |
| Deterministic, same-type-distinct pseudonym allocation | Policy-declared identity, not inferred personhood. The current SHA-256 namespace is public and unkeyed; consistency is not secrecy. |
| Fresh source/output reread, location/type checks and declared-identity coherence | Runtime verification shares replacement primitives. A separate synthetic-fixture readback adds bounded independence, not a universal second engine. |
| `report.json` published last | **Technically READY under the declared transformation contract**, not general privacy approval, full rollback or a signed attestation. |

Complete PII discovery, factual identity assignments, formal anonymity and contextual linkage resistance are not established.

## Research, reuse and evidence

The workflow starts with problem framing, **dogpile research across Brave, arXiv and GitHub**, and inspection of existing projects and skills. Reuse suitable components before custom contract logic. Standard-library format tools are reused; RapidFuzz supplies optional alias candidate scoring. FlashText-style matching informed the solution family, without a comparative superiority claim.

Research adaptations are narrow: **SPIA** informed identity-coherence and privacy-limit thinking; **DICOM validation** informed known-truth and corrupted-output checks; **AnonShield/Proteus** informed namespace and keyed-pseudonym design. Their full systems or benchmarks were not reproduced. [Research/reuse map](sources/research-workflow.md).

The [later rehearsal receipt](https://github.com/grahama1970/oai-trial/blob/main/docs/pitch/oai-trial/rehearsal-evidence.json) records offline Docker executions and a **separate local skill-wrapper** run/verify, independent four-format readback, and conflicting-policy refusals. The wrapper did not run Docker. No discovery or live adaptive attack campaign ran in that receipt.

A useful discussion example: the initial rehearsal oracle demanded cross-environment SQLite byte equality. The unchanged outputs passed logical/schema/type checks; differing SQLite versions and header metadata were observed. The comparison—not the runtime—was corrected. [Explanation](NARRATIVE.md#wrong-oracle).

The local implementation materializes data. **TB/PB capacity and AWS costs are modeled scenarios**, not production benchmarks. HMAC/key management and distributed orchestration remain design work.

## Optional code stops

| Discussion | Implementation |
|---|---|
| Literal conflicts and declared identities | [policy.py](https://github.com/grahama1970/oai-trial/blob/main/src/anonymization_trial/policy.py): `_check_overlap`, `Rule.identity` |
| Overlaps and no cascading | [matcher.py](https://github.com/grahama1970/oai-trial/blob/main/src/anonymization_trial/matcher.py): `_select`, `Matcher.replace` |
| Typed/location checks versus fixture oracle | [verification.py](https://github.com/grahama1970/oai-trial/blob/main/src/anonymization_trial/verification.py); [scripts/qualify_submission.py](https://github.com/grahama1970/oai-trial/blob/main/scripts/qualify_submission.py): `readback` |
| Privacy-safe error references | [errors.py](https://github.com/grahama1970/oai-trial/blob/main/src/anonymization_trial/errors.py): `safe_ref` |
| Readiness and publication order | [pipeline.py](https://github.com/grahama1970/oai-trial/blob/main/src/anonymization_trial/pipeline.py): `_publish` |

This is a bounded trial. Questions may lead to demonstrated code, a deliberate deferral, or an explicit need for further research—not a claim that every hardening scenario has been solved.

*Runtime reference: `0375af56bf681e9441edcb7433cfe58951db77b2`. Later presentation and rehearsal work is separate; this brief does not assert a new review verdict.*
