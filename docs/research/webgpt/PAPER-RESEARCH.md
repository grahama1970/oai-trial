# Yes—several are genuinely useful

I searched arXiv work from 2025 through September 4, 2026. The papers divide into two groups:

1. **Papers that should directly change the implementation and tests.**
2. **Papers that should change the threat model, production design, and what the submission claims.**

The important distinction is that `oai-trial` is a **policy-driven deterministic pseudonymization and verified-release exercise**. It is not asking us to invent a general PII detector, rewrite prose with an LLM, generate synthetic datasets, or prove formal anonymity. Most recent anonymization research is valuable as architecture or evaluation guidance, but only a small subset belongs on the eight-hour implementation path.

## Highest-priority papers

### 1. *AnonShield: Scalable On-Premise Pseudonymization for CSIRT Vulnerability Data*

**arXiv:2606.15650, 2026**

This is the closest recent implementation analogue I found. AnonShield combines:

* deterministic HMAC-SHA256 pseudonyms;
* consistency across correlated records;
* schema-aware field policies;
* streaming processing for structured and unstructured formats;
* JSON streaming through `ijson`;
* performance and accuracy benchmarking;
* separation between entity detection and replacement policy. ([arXiv][1])

#### What to borrow

For tickets **#3, #5, #6, #9, and #10**:

* Compile rules once into a schema-aware replacement plan.
* Derive production pseudonyms with a keyed, domain-separated construction.
* Keep the entity type in the pseudonym-generation domain.
* Preserve referential consistency across formats.
* Stream large inputs rather than constructing full document trees where semantics permit.
* Benchmark repeated entities and policy sizes, not only record counts.
* Separate “which value is sensitive?” from “how is its replacement generated?”

AnonShield’s use of HMAC-SHA256 is particularly relevant to the production architecture. The same entity generates a consistent pseudonym under the same key, while unkeyed hashes are more exposed to dictionary attacks. It also uses incremental processing for JSON, JSONL, CSV, and text. ([arXiv][1])

#### What not to borrow

Do not bring its GPU/NER stack into this trial. The input policy already identifies the literals. Also do not persist a local database containing original-to-pseudonym mappings: AnonShield does this to support controlled re-identification, but the trial neither requires re-identification nor permits mappings to leak into the release. ([arXiv][1])

For the local implementation, a deterministic synthetic replacement construction is sufficient to meet the specified contract. For production, document:

```text
KMS-protected versioned key
    -> unwrap once per worker task
    -> HMAC-SHA256(
           algorithm_version ||
           tenant_or_corpus_scope ||
           data_type ||
           canonical_subject_id ||
           collision_counter
       )
    -> type-specific encoding
```

Do not introduce a new secret parameter into the evaluator’s fixed container contract unless there is a safe default and the exact required commands still work.

---

### 2. *Medical Image De-Identification Resources: Synthetic DICOM Data and Tools for Validation*

**arXiv:2508.01889, 2025**

The DICOM format is not relevant, but the **evaluation methodology is extremely relevant**. The authors created a corpus with synthetic PHI/PII planted in structured fields, text fields, and pixel data, then provided known-truth answer keys and Python validators that compare outputs against expected transformations. ([arXiv][2])

This is the best research precedent for how we should strengthen the fixture generator and verifier.

#### What to borrow

For tickets **#2, #8, and #9**, generate a private test truth manifest such as:

```json
{
  "schema": "anonymization_trial.fixture_truth.v1",
  "policy_sha256": "...",
  "files": [
    {
      "path_id": "sha256:...",
      "format": "csv",
      "expected_records": 1000,
      "expected_structure_sha256": "...",
      "expected_occurrences": {
        "person-001-name": 500,
        "person-001-email": 500
      },
      "expected_protected_occurrences": {
        "protected-001": 1000
      }
    }
  ]
}
```

The test harness should know:

* which rule occurs in which format and logical location;
* how many matches should be selected after overlap resolution;
* which aliases belong to the same subject;
* which protected values must remain;
* which structural properties must remain unchanged;
* which malformed or adversarial variants must be rejected.

This truth data belongs only in synthetic fixtures and test working directories. It must never enter `/trial/output`, `report.json`, logs, or the final runtime image as an original-to-replacement map.

---

### 3. *From Production SIEM to Reusable Cybersecurity Artifacts*

**arXiv:2606.21389, June 19, 2026**

This paper treats the boundary between private production telemetry and releasable research artifacts as the primary design problem. It emphasizes preserving temporal order and entity consistency, using explicit validation, and reporting a measurable privacy–utility boundary rather than claiming formal anonymity. ([arXiv][3])

That is almost exactly the right conceptual frame for `oai-trial`.

#### What to borrow

For tickets **#2, #8, #10, and #11**:

* Treat the **release boundary** as a first-class object.
* State which invariants make the output useful.
* Test those invariants separately from sensitive-value removal.
* Preserve entity consistency across heterogeneous sources.
* Run a deterministic verifier over the released artifact.
* Explicitly state what the verification does and does not prove.

For this trial, the preserved utility conditions are not model accuracy. They are:

```text
CSV      valid parse, same headers/order/rows/shape
JSON     same topology, keys, order, array lengths, non-string scalars
Text     valid UTF-8, BOM/newline policy, untouched non-selected spans
SQLite   same schema, keys, row counts, relationships, non-text values
Corpus   same logical file set
```

The paper also supports an important wording correction:

> “Verification passed” means the output satisfies the declared policy and structural release contract. It does not mean the corpus is formally anonymous against every possible linkage attack.

---

### 4. *Tau-Eval: A Unified Evaluation Framework for Useful and Private Text Anonymization*

**arXiv:2506.05979, revised September 2025; EMNLP 2025 Demo**

Despite the name, this is unrelated to `grahama1970/tau`. Tau-Eval evaluates anonymization through both privacy protection and downstream utility rather than reporting one undifferentiated success metric. ([arXiv][4])

#### What to borrow

For tickets **#2, #8, and #9**, divide the acceptance matrix and report checks into three dimensions:

| Dimension                           | `oai-trial` checks                                                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Policy/privacy correctness          | Every independently observed selected occurrence is replaced; no protected value is changed; aliases and subjects are coherent |
| Utility and structural preservation | Format-specific topology, rows, relationships, values, order, and parse validity remain correct                                |
| Operational release safety          | Full verification, no metadata leakage, no partial ready release, repeatability, bounded resources                             |

This prevents an aggregate “all tests passed” number from hiding a failure in one critical dimension.

I would **not** add Tau-Eval itself as a dependency. Its evaluation model is useful; its text/ML framework is broader than the evaluator contract and would unnecessarily enlarge the Docker image.

---

### 5. *A General Pseudonymization Framework for Cloud-Based LLMs*

**arXiv:2502.15233, 2025**

This paper separates privacy-value identification, creation of type-compatible replacements, controlled substitution, and optional restoration. It is oriented toward cloud LLM prompts, but the conceptual decomposition is useful. ([arXiv][5])

#### What to borrow

For tickets **#3 and #10**:

```text
policy boundary
    -> canonical identity resolution
    -> type-specific pseudonym generation
    -> replacement
    -> verification
    -> optional controlled restoration boundary
```

For this submission, the restoration stage should be explicitly absent. That gives us a clear production decision:

* **Base design:** deterministic pseudonymization with no stored mapping and no routine re-identification.
* **Optional regulated variant:** isolated mapping vault, separate authorization, audit trail, retention schedule, and additional cost/security analysis.

Do not borrow random or LLM-selected replacement candidates. Replacement choice must be deterministic, globally collision-checked, and independent of policy file order.

---

## Papers that should change the threat model and non-claims

### 6. *RAT-Bench: A Comprehensive Benchmark for Text Anonymization*

**arXiv:2602.12806, February 2026**

RAT-Bench evaluates anonymization by residual re-identification risk rather than only identifier-removal recall. Its results show that explicit identifiers can be removed while indirect identifiers and unusual representations still permit re-identification. ([arXiv][6])

#### Concrete change

Add this distinction to `SUBMISSION.md` and the report schema documentation:

```text
PROVEN:
- Every policy-selected literal occurrence was transformed.
- Protected values and declared structural invariants were preserved.
- Stable subject/type pseudonyms were used.
- The complete accepted corpus was reread before publication.

NOT PROVEN:
- Resistance to linkage with external datasets.
- Protection against inference from quasi-identifiers.
- Formal anonymity, differential privacy, or k-anonymity.
- Discovery of sensitive information omitted from policy.json.
```

RAT-Bench should not expand the local implementation into an LLM anonymizer. It should prevent us from overstating what a literal-driven pipeline establishes.

---

### 7. *Subject-level Inference for Realistic Text Anonymization Evaluation* — SPIA

**arXiv:2604.21211v2, June 25, 2026**

SPIA argues that span-level masking is an inadequate unit of evaluation. Its evaluation instead asks whether each data subject remains inferable, including non-primary subjects; the paper reports cases where high span masking still produces weak subject-level protection. ([arXiv][7])

#### Concrete change

The trial’s `subject_id` field gives us a clean way to add **subject-level deterministic checks**, even though we cannot prove inference resistance:

* Every rule belonging to a subject resolves to one stable pseudonymous profile.
* Every observed alias for that subject is transformed.
* No type-specific pseudonym is shared with another subject.
* Every format reports safe counts by hashed or policy-provided subject identifier.
* The verifier reconciles subject-level source and output observations.

This is stronger than merely checking each `rule_id` independently and maps directly to tickets **#3 and #8**.

---

### 8. *Large-scale Online Deanonymization with LLMs*

**arXiv:2602.16800, revised February 25, 2026**

This work demonstrates a pipeline that extracts identity clues from unstructured text, retrieves candidate profiles, and reasons over matches. The authors report up to 68% recall at 90% precision in their evaluated settings, substantially above classical baselines, and argue that “practical obscurity” is no longer a reliable privacy assumption for persistent pseudonymous content. ([arXiv][8])

#### Concrete change

For tickets **#10 and #11**:

* Identify stable pseudonyms as a deliberate utility feature **and** a potential linkage surface.
* Explain whether pseudonyms are corpus-scoped, tenant-scoped, or global.
* Prefer the narrowest scope that still meets the business requirement.
* Do not expose pseudonyms across customers merely because global consistency is technically convenient.
* Add an optional pre-release re-identification red-team lane for production.
* Do not make an LLM/web-search attack a blocker for the local trial unless the claimed protection level is expanded beyond the supplied brief.

This also supports using a corpus- or tenant-scoped HMAC domain in production instead of globally stable identifiers.

---

### 9. *Why Data Anonymization Has Not Taken Off*

**arXiv:2509.10165, September 2025**

This paper’s most useful argument is that anonymization claims are meaningless without defining the domain, unit of protection, scope, and protection standard. It also argues that practical anonymization is usually case-specific and should be combined with access, retention, security, and governance controls. ([arXiv][9])

#### Concrete change

Ticket **#2** should make these fields explicit:

```yaml
privacy_boundary:
  domain: customer export corpus
  protected_unit: policy-listed literal and subject identity
  scope: one mounted corpus under one policy version
  transformation: deterministic type-specific pseudonymization
  discovery_authority: policy.json only
  adversary_assumption: release consumer lacks raw input and private key/mapping
  protection_standard: complete declared-literal replacement plus structural preservation
  excluded_claims:
    - unlisted sensitive-value discovery
    - quasi-identifier anonymity
    - external-dataset unlinkability
    - formal differential privacy
```

That would make the submission much more defensible than calling the output “anonymous” without qualification.

---

## Useful, but not on the eight-hour critical path

### *Prεεmpt: Sanitizing Sensitive Prompts for LLMs*

The paper distinguishes format-dependent values, for which it uses format-preserving encryption, from semantically meaningful values, for which it uses metric differential privacy. ([arXiv][10])

This is valuable as a production alternatives discussion, but I would **not implement FPE or differential privacy locally**. FPE introduces key management, domain-size, collision, type, and test complexity. Differential privacy deliberately adds randomized behavior that conflicts with the trial’s stable-repeatability requirement.

Use it in `SUBMISSION.md` as a considered alternative:

> FPE could be appropriate when exact format preservation and reversible tokenization are required. It was not selected for the bounded local implementation because the trial requires deterministic, independently verifiable replacement across heterogeneous formats but does not require reversible exact-domain ciphertexts.

### *Adaptive Text Anonymization: Learning Privacy–Utility Trade-offs via Prompt Optimization*

This paper adapts LLM anonymization instructions to specific privacy and utility goals. It reinforces that anonymization policy is context-dependent, but LLM rewriting would introduce nondeterminism and semantic drift that are counterproductive for the required literal contract. ([arXiv][11])

### *LLM Anonymization Against Agentic Re-Identification*

AURA evaluates anonymized text against web-search-assisted re-identification while also checking retained utility. This is useful for a future production red-team or a stronger semantic-anonymization lane, but not for the exact, cross-format local transformer. ([arXiv][12])

### *What to Remember, What to Reveal: Privacy-Aware Memory for Conversational Agents*

This August 2026 paper separates sanitized searchable memory from isolated exact private values and applies authorization-gated retrieval. It is much more relevant to `graph-memory-operator` than to the standalone trial image. It supports keeping any raw-to-pseudonym mapping outside searchable operational stores, but the simplest `oai-trial` design should avoid storing such a mapping altogether. ([arXiv][13])

---

# Changes I would make to the implementation strategy

## 1. Call the mechanism pseudonymization internally

Keep the repository and CLI names required by the trial, but define the mechanism precisely as:

> Deterministic policy-driven pseudonymization followed by independent whole-corpus verification and fail-closed publication.

Use “anonymization pipeline” when quoting the assignment, but do not claim that literal substitution creates universally anonymous data. RAT-Bench, SPIA, and the large-scale deanonymization paper all show why that distinction matters. ([arXiv][6])

## 2. Add an explicit threat model to ticket #2

The threat model should identify:

* assets: raw corpus, policy literals, pseudonym key, any mapping, quarantined artifacts;
* trust boundaries: input mount, private staging, verifier, release directory;
* adversary: consumer of the released corpus, compromised logs, accidental partial-publication reader;
* required protections: declared-literal removal, no mapping/log exposure, structural correctness;
* residual risks: quasi-identifiers, linkage, unlisted sensitive data, global stable identifiers.

## 3. Upgrade fixtures from examples into known-truth test corpora

Inspired by the DICOM validation work:

* plant every sensitive type in every supported format;
* plant aliases of the same subject across different formats;
* plant protected values adjacent to sensitive values;
* generate overlap, case, BOM, malformed encoding, schema-key, path, and SQLite constraint variants;
* retain exact expected occurrence counts privately;
* mutate one invariant at a time to prove the verifier catches it.

## 4. Add two verification levels

```text
Level A — contract verification
  exact policy occurrence reconciliation
  replacement coherence and collision freedom
  protected-value preservation
  complete structural and relational checks
  report/manifest binding
  no release metadata leakage

Level B — privacy-risk assessment
  quasi-identifier and linkage review
  subject-level inference review
  optional agentic re-identification test
```

Level A is mandatory for this trial. Level B belongs in the production threat model and can be a non-blocking final audit experiment. Mixing them would either overstate Level A or consume the eight-hour window attempting an open-ended privacy problem.

## 5. Use HMAC in production, not an exposed mapping service

AnonShield strongly supports deterministic keyed pseudonyms for referential integrity. The local trial can retain its self-contained deterministic construction, while the production design should use a KMS-protected HMAC key scoped to the tenant or corpus. ([arXiv][1])

The production manifest should bind:

```text
algorithm version
key identifier and version
pseudonym scope
policy digest
source snapshot digest
```

It must not contain plaintext keys or raw mappings.

## 6. Make streaming an evidence-driven decision

AnonShield demonstrates that streaming and schema-aware processing can improve scale substantially, but its performance results do not prove our specific overlap, protected-value, duplicate-key, and independent-verification semantics. ([arXiv][1])

Therefore:

* stream text and CSV now;
* use the SQLite backup API and row-wise batches now;
* adopt `ijson` only after semantic-equivalence and duplicate-key tests pass;
* otherwise impose a safe JSON size bound and document record-framed JSON as the production path;
* benchmark `pyahocorasick` only after the reference matcher is correct.

---

# Recommended reading order

For the implementation team, the most efficient sequence is:

1. **AnonShield** — architecture, pseudonym derivation, schema policy, streaming.
2. **Medical Image De-Identification Resources** — fixture truth and independent validation.
3. **Production SIEM to Reusable Artifacts** — release boundary, preserved utility, non-claims.
4. **Tau-Eval** — privacy-versus-utility evaluation structure.
5. **RAT-Bench and SPIA** — adversarial evaluation and subject-level coverage.
6. **Large-scale Online Deanonymization** — production residual-risk model.
7. **Why Data Anonymization Has Not Taken Off** — scope and claim discipline.

The most important new insight is not a new package. It is that the submission should have **two clearly separated claims**:

```text
Release correctness:
fully provable by deterministic local tests and complete reread verification.

Resistance to re-identification:
a separate, context-dependent risk assessment that this literal-policy trial
does not and should not pretend to solve.
```

That distinction will make the code smaller, the tests stronger, and `SUBMISSION.md` substantially more credible.

[1]: https://arxiv.org/html/2606.15650v1 "AnonShield: Scalable On-PremisePseudonymization for CSIRT Vulnerability Data"
[2]: https://arxiv.org/abs/2508.01889 "[2508.01889] Medical Image De-Identification Resources: Synthetic DICOM Data and Tools for Validation"
[3]: https://arxiv.org/html/2606.21389v1 "From Production SIEM toReusable Cybersecurity Artifacts"
[4]: https://arxiv.org/abs/2506.05979 "[2506.05979] Tau-Eval: A Unified Evaluation Framework for Useful and Private Text Anonymization"
[5]: https://arxiv.org/abs/2502.15233 "[2502.15233] A General Pseudonymization Framework for Cloud-Based LLMs: Replacing Privacy Information in Controlled Text Generation"
[6]: https://arxiv.org/html/2602.12806v1 "RAT-Bench: A Comprehensive Benchmark for Text Anonymization"
[7]: https://arxiv.org/html/2604.21211 "Subject-level Inference for Realistic Text Anonymization Evaluation"
[8]: https://arxiv.org/pdf/2602.16800?utm_source=chatgpt.com "Large-scale online deanonymization with LLMs"
[9]: https://arxiv.org/abs/2509.10165?utm_source=chatgpt.com "Why Data Anonymization Has Not Taken Off"
[10]: https://arxiv.org/abs/2504.05147 "[2504.05147] Pr$εε$mpt: Sanitizing Sensitive Prompts for LLMs"
[11]: https://arxiv.org/html/2602.20743v1?utm_source=chatgpt.com "Learning Privacy-Utility Trade-offs via Prompt Optimization"
[12]: https://arxiv.org/html/2605.30848v2?utm_source=chatgpt.com "LLM Anonymization Against Agentic Re-Identification"
[13]: https://arxiv.org/html/2608.16551v1 "What to Remember, What to Reveal: Privacy-Aware Memory for Conversational Agents"
