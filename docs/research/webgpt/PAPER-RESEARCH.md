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


---
# Yes. I understand the objective.

I interpret “all relevant research” as the recent work that can materially change the **architecture, privacy model, correctness guarantees, verification strategy, performance design, or evaluation methodology** for `oai-trial`. I reviewed the recent 2024–September 2026 research corpus surfaced by the 2025 text-anonymization survey, then followed its most relevant systems, attack, benchmarking, data-pipeline, property-testing, and provenance branches.

The central conclusion is important:

> We should not turn `oai-trial` into an LLM anonymizer. We should turn it into a **verified pseudonymization and release system**, with an optional second plane for probabilistic discovery and re-identification risk.

The current trial requires exact behavior for an authoritative literal policy. That belongs in a deterministic system. Recent research also shows that exact identifier removal does **not** prove that a subject cannot be inferred from contextual clues, so residual privacy risk must be represented separately rather than hidden behind a green “anonymized” label. ([arXiv][1])

---

# 1. The research-derived architecture

The strongest design is a **two-plane architecture**.

```text
                         INPUT TRUST BOUNDARY
                mounted corpus + authoritative policy
                                  │
                                  ▼
                         SOURCE PREFLIGHT
                freeze inventory, hashes, file types,
                 format limits, paths, source version
                                  │
                                  ▼
┌──────────────────────── DETERMINISTIC PROOF PLANE ───────────────────────┐
│                                                                          │
│  strict policy compiler                                                 │
│      │                                                                   │
│      ├── canonical subject + alias registry                              │
│      ├── protected/sensitive conflict analysis                           │
│      ├── scoped pseudonym plan                                           │
│      └── deterministic original-span matcher                             │
│                                  │                                       │
│                                  ▼                                       │
│               format-aware transformations                              │
│            text │ CSV │ JSON │ SQLite                                    │
│                                  │                                       │
│                                  ▼                                       │
│                      private staged corpus                               │
│                                  │                                       │
│                                  ▼                                       │
│                  independent full-corpus verifier                        │
│          source reread + output reread + structure proofs                │
│                                  │                                       │
│                                  ▼                                       │
│                 proof-gated publication / report last                    │
│                                  │                                       │
│                                  ▼                                       │
│                         releasable corpus                                │
└──────────────────────────────────────────────────────────────────────────┘

┌────────────────────────── PRIVACY-RISK PLANE ────────────────────────────┐
│ optional unlisted-PII discovery                                         │
│ subject-level inference evaluation                                      │
│ quasi-identifier and cross-record linkage analysis                       │
│ agentic/web-assisted re-identification red-team                          │
│ downstream task-utility evaluation                                      │
│                                                                          │
│ outcome: PASS-UNDER-DECLARED-ATTACK │ REVIEW │ QUARANTINE                │
│ never independently authorizes publication                              │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────── DEVELOPMENT CONTROL PLANE ───────────────────────┐
│ Tau DAGs, agentic-evals, project-agent, Graph Memory, reviewer receipts  │
│ Development and evidence controls only — absent from trial Docker image │
└──────────────────────────────────────────────────────────────────────────┘
```

This separation resolves a major conceptual problem:

* The **proof plane** can prove exact claims such as complete policy replacement, structural preservation, deterministic identity coherence, and no partial ready release.
* The **risk plane** can test whether contextual information might still permit inference, but a passing attack test cannot prove universal anonymity.

RAT-Bench, SPIA, agentic deanonymization research, and AURA all demonstrate why span-removal recall alone is an inadequate privacy claim. Proof-gated data-pipeline research independently supports keeping the release decision in a deterministic outer loop rather than trusting a model or transformer success message. ([arXiv][2])

---

# 2. Required feature set

## Feature 1 — An explicit privacy, utility, and linkage contract

**Priority: local P0**

Before processing any data, the system needs a versioned contract that states:

```yaml
schema: anonymization_trial.privacy_contract.v1
data_domain: customer_export
protected_unit:
  - policy_literal
  - policy_subject
scope_id: trial-v1
discovery_authority: policy.json
allowed_linkage:
  within_file: true
  across_files: true
  across_formats: true
  across_retries: true
  across_tenants: false
matching:
  mode: literal
  normalization: none
  case_policy: exact_or_ascii_insensitive
schema_identifier_policy: reject_if_sensitive
utility_invariants:
  - format validity
  - non-sensitive value preservation
  - protected-value preservation
  - order and relationship preservation
release_standard: complete_verified_corpus
excluded_claims:
  - discovery of unlisted sensitive data
  - resistance to all external linkage
  - formal anonymity
  - differential privacy
```

Recent work stresses that “anonymization” is underspecified until the data domain, protected unit, scope, and protection standard are explicit. Different choices produce fundamentally different guarantees. ([arXiv][3])

This contract should be the authority for:

* the policy compiler;
* every adapter;
* the verifier;
* the report schema;
* production key scope;
* residual-risk evaluation;
* `SUBMISSION.md` non-claims.

### Why linkage must be explicit

Stable pseudonyms preserve useful correlation, but stable equality is itself information. Proteus shows that stable keyed tokens support forensic correlation while also permitting cross-snapshot behavioral linkage; its design adds rotation and controlled access where unlinkability across time matters. ([arXiv][4])

For the local trial, stability across files and reruns is mandatory. In production, stability should be scoped deliberately:

```text
corpus scope   — link only within one release
purpose scope  — link across runs for one approved analytical purpose
tenant scope   — link across one customer's releases
global scope   — prohibited by default
```

---

## Feature 2 — Immutable source snapshot and source-manifest binding

**Priority: local P0; stronger attestation in production**

Every run should begin by freezing a source manifest containing safe metadata:

```json
{
  "schema": "anonymization_trial.source_manifest.v1",
  "run_id": "...",
  "policy_sha256": "...",
  "files": [
    {
      "path_id": "sha256:...",
      "format": "csv",
      "size": 1234,
      "source_sha256": "...",
      "device": 1,
      "inode": 321,
      "mode": 420
    }
  ]
}
```

The preflight must:

* use `lstat`, not blindly follow paths;
* reject symlinks, devices, FIFOs, sockets, path escapes, unsupported files, and duplicate inode surprises;
* establish that input and output roots are distinct;
* hash the source before transformation;
* recheck type, size, identity, and digest during verification;
* use the SQLite backup API to obtain a consistent database snapshot;
* reject any source that changes during the run.

Proof-gated publication research distinguishes **read-to-sink fidelity** from true **source-to-sink fidelity**. A verifier can prove that output agrees with the bytes it read, but upstream authenticity requires an independently attested source statement. ([arXiv][5])

Therefore the claims should be:

```text
Local trial:
  verified transformation of the mounted input snapshot

Production:
  verified transformation of immutable object versions
  plus a producer-signed source manifest when source authenticity is required
```

The production architecture should bind S3 object version IDs, ETags/checksums, policy version, algorithm version, container image digest, and pseudonym-key version.

---

## Feature 3 — A canonical subject and alias registry

**Priority: local P0**

The current rule list should be compiled into a first-class subject graph:

```text
SubjectKey
  = scope_id
  + data_type
  + (subject_id if present else rule_id)
```

Each canonical subject/type record should contain:

* safe subject key or digest;
* data type;
* source rule IDs;
* literal aliases;
* case behavior;
* one pseudonym;
* pseudonym derivation version;
* selected collision counter;
* internal validation status.

This is more than an implementation convenience. SPIA shows that evaluating isolated text spans can report high masking success while leaving substantial subject-level information inferable, and that non-primary subjects can remain especially exposed. ([arXiv][2])

The deterministic verifier should consequently report both:

```text
rule-level occurrence coverage
subject-level profile coherence
```

Required properties:

* every alias for one subject/type converges;
* one subject’s name, email, phone, and IP form a stable pseudonymous profile;
* no two canonical subjects share a type-specific pseudonym;
* no secondary subject present in the policy is omitted from verification;
* adding file-format boundaries does not break subject identity.

Graph Memory is useful for recalling and preserving the **development pattern**, but the runtime registry should be an immutable in-process object compiled directly from `policy.json`.

---

## Feature 4 — Scoped, domain-separated pseudonym derivation

**Priority: deterministic local version P0; keyed production version P1**

AnonShield’s most relevant contribution is its combination of deterministic keyed pseudonymization, schema-aware rules, caching, and streaming. It demonstrates that consistent HMAC-derived pseudonyms can preserve correlation across structured and unstructured records without requiring a network lookup for every occurrence. ([arXiv][6])

The production construction should be conceptually:

```text
canonical_input =
    length_prefix(algorithm_version)
  || length_prefix(scope_id)
  || length_prefix(data_type)
  || length_prefix(subject_id_or_rule_id)
  || uint64(collision_counter)

digest = HMAC-SHA-256(scope_key, canonical_input)

replacement = encode_for_type(data_type, digest)
```

Required properties:

* canonical byte encoding, not ambiguous string concatenation;
* algorithm version and key ID bound into the manifest;
* at least 128 bits of pseudorandom material retained internally;
* deterministic type-specific encoding;
* collision checks over the entire compiled policy;
* generated replacements disjoint from protected and source literals;
* no plaintext mapping stored or logged;
* one KMS unwrap per worker task in production, not one KMS request per value.

Recent experiments found that HMAC pseudonymization removed original identifiers from the measured model-exposure surface without producing a correspondingly extractable pseudonym target under that paper’s specific threat model. The same work also emphasizes that pseudonymization, differential privacy, and output filtering operate at different layers and do not automatically compose into one guarantee. ([arXiv][7])

### Local trial key mode

The evaluator’s exact command supplies no secret. Therefore the local implementation should use an explicitly disclosed mode such as:

```text
key_mode = public_deterministic_trial_namespace
```

It can use domain-separated SHA-256 or HMAC with a public fixed trial namespace to ensure repeatability and collision behavior, but it must **not claim cryptographic secrecy**.

`SUBMISSION.md` should say plainly:

> Local pseudonyms prove deterministic identity coherence, not resistance to dictionary attacks. Production replaces the public derivation namespace with a tenant- or purpose-scoped secret protected by KMS.

---

## Feature 5 — Compile-time collision and ambiguity elimination

**Priority: local P0**

Before reading or writing corpus values, compile the complete pseudonym plan and reject:

* duplicate `rule_id`;
* one literal assigned to conflicting subjects or types;
* unsupported match modes;
* empty values;
* protected/sensitive overlap;
* sensitive/sensitive ambiguity not resolved by the documented precedence;
* pseudonym/pseudonym collision;
* pseudonym/source-literal collision;
* pseudonym/protected-literal collision;
* exhausted type-specific namespace;
* unsupported non-ASCII case-insensitive rule.

The matcher must operate over the **original decoded value once**:

```text
1. Find every candidate match in the original value.
2. Sort by:
     start ascending
     length descending
     rule_id ascending
3. Select non-overlapping candidates.
4. Emit untouched source spans and replacements.
5. Never scan generated output.
```

This prevents:

* policy-order dependence;
* replacement cascades;
* a replacement being anonymized again;
* shorter nested literals stealing a longer intended match;
* transformer and verifier disagreeing about precedence.

The current task brief explicitly requires deterministic treatment of nested, prefix/suffix, protected, and replacement-to-source overlaps.

### Additional cutting-edge invariant

The plan should also scan the source corpus for **pre-existing pseudonym tokens**. A naturally occurring non-sensitive value identical to a generated pseudonym creates ambiguous verification. The safe choices are:

1. deterministically derive another candidate before transformation; or
2. reject the corpus with a safe collision code.

For production stability across evolving corpora, rejection is preferable to silently changing an existing subject’s token.

---

## Feature 6 — Format-aware adapters rather than a universal replacer

**Priority: local P0**

Recent systems obtain both reliability and speed by exploiting schema knowledge rather than applying the same detection path everywhere. AnonShield reports large gains when schema-aware configuration can bypass expensive entity detection, but its NER path still has context and malformed-input limitations. ([arXiv][6])

The system should therefore have one policy engine but four independent adapters.

### UTF-8 text

Required features:

* binary open followed by strict incremental UTF-8 decoding;
* optional BOM detection and exact BOM preservation;
* no Unicode normalization;
* no implicit newline normalization;
* bounded chunk processing;
* a match horizon at least as large as the longest literal;
* deferred commitment near chunk boundaries so leftmost-longest semantics remain correct;
* explicit maximum literal and maximum pending-buffer size;
* privacy-safe invalid-encoding errors;
* exact byte preservation outside selected replacement spans where possible.

A fundamental test property must be:

```text
transform(full_text)
==
transform(the_same_text_under_any_valid_chunk_partition)
```

### CSV

Required features:

* standard `csv` parser with `newline=""`;
* streaming rows rather than materializing the file;
* a frozen dialect policy;
* exact header order and values;
* complete header inspection before data-row publication;
* fail-closed rejection when a sensitive literal occurs in a header;
* row-count, row-order, width-profile, and cell-order fingerprints;
* explicit ragged-row policy;
* preservation of quoted commas, escaped quotes, embedded newlines, and empty cells;
* no matching across separate cells;
* no conflation with spreadsheet-formula sanitization.

### JSON

Required features:

* strict UTF-8 and BOM policy;
* duplicate-key rejection at every depth;
* rejection of `NaN`, positive infinity, and negative infinity;
* object keys treated as protected schema;
* sensitive match in a key causes rejection, not key renaming;
* only string values transformed;
* exact preservation of booleans, nulls, integers, and finite numeric semantics;
* bounded depth, key length, string length, and total file size;
* ordered topology fingerprint;
* deterministic serialization contract.

Correctness takes precedence over advertising streaming. `ijson` should be adopted only after duplicate-key, number, ordering, depth, and verifier-equivalence tests pass. Otherwise, use a documented monolithic JSON bound locally and design for JSON Lines or record-framed JSON in production.

### SQLite

Required features:

* read-only source connection;
* SQLite online backup API for a consistent staged snapshot;
* bounded busy timeout;
* ordered `sqlite_schema` fingerprint;
* `PRAGMA table_xinfo` rather than basic column inspection;
* table, column, index, trigger, view, PK, unique, and FK inventories;
* table and column names treated as protected schema;
* transformation only of values whose SQLite storage class is `text`;
* no changes to integer, real, null, or BLOB values;
* explicit transaction;
* collision checks before unique-column updates;
* safe handling of rowid and `WITHOUT ROWID` addressing;
* `integrity_check` and `foreign_key_check`;
* safe rejection of virtual tables, triggers, generated columns, attached databases, or key-update situations the implementation cannot prove.

For the eight-hour submission, **explicitly rejecting an unsupported SQLite feature is much stronger than nominally accepting it without an independent preservation oracle**.

---

## Feature 7 — Private staging and proof-gated publication

**Priority: local P0**

This is the strongest reliability feature from the recent data-pipeline literature.

Proof-Gated Publication separates publication into:

```text
Physical  -> write consumer-invisible staged data
Verify    -> compute and validate content proof
Durable   -> checkpoint the accepted state
Metadata  -> make the snapshot visible, last
```

A failed proof produces no consumer-visible snapshot. The paper is currently a proposed specification rather than a ratified standard, but the invariant maps directly to this trial. ([arXiv][5])

For `oai-trial`, the corresponding state machine should be:

```text
received
  -> preflight_passed
  -> source_frozen
  -> policy_compiled
  -> staged
  -> independently_verified
  -> corpus_published
  -> report_published
  -> ready
```

Any other terminal state is:

```text
failed
quarantined
uncommitted
interrupted
```

### Local commit protocol

1. Build everything under a unique hidden sibling staging directory.
2. Close and flush all staged files.
3. Independently reread the source and staged output.
4. Generate a verified corpus manifest.
5. Prepare `report.json` privately.
6. Remove or invalidate any old readiness marker **before** changing its bound corpus.
7. Swap the verified corpus into `/trial/output/corpus`.
8. Fsync the relevant directories where supported.
9. Atomically replace `/trial/output/report.json` **last**.
10. Treat only a valid report whose manifest digest matches the current corpus as ready.

The old report must never remain visible while its bound corpus is replaced. Otherwise, a crash can leave a valid-looking old report pointing at new, unverified bytes.

### Recovery

On startup, detect and resolve:

* stale run-owned staging directories;
* corpus present with no valid report;
* report present with missing corpus;
* report/corpus digest mismatch;
* interrupted old-corpus backup state;
* completed run already committed;
* prior valid release awaiting replacement.

Proof-gated publication research also recommends a durable workload clock separate from individual worker/container lifetimes so retries resume completed work rather than blindly repeating it. ([arXiv][5])

---

## Feature 8 — An independently implemented whole-corpus verifier

**Priority: local P0**

The verifier must not call the transformation functions or trust their counters.

It should:

* run as a separate module or process;
* reread every source and staged file;
* use a separately implemented reference matcher;
* independently derive expected source occurrence counts;
* independently count expected pseudonyms in output;
* compare protected-value occurrences;
* recompute format fingerprints;
* verify the complete file set;
* reject unknown check states;
* produce a versioned verification receipt.

For every format it should compare a **redaction-normalized skeleton**:

```text
source sensitive span    -> <SUBJECT:type:safe-id>
output pseudonym span    -> <SUBJECT:type:safe-id>
protected/non-sensitive  -> preserved exact or semantic representation
```

The source and output skeletons must agree under the format’s declared semantics.

### Verification artifacts

Use three complementary proof forms:

1. **Physical file digest**
   SHA-256 over the exact staged output bytes.

2. **Ordered structural digest**
   Used where order has meaning: text records, CSV rows, JSON arrays/member order, SQLite schema definitions.

3. **Multiplicity-sensitive content digest**
   Used in distributed production when physical partition layout and row order are not semantically meaningful.

Proof-Gated Publication argues that an ordinary ordered Merkle root is unsuitable for comparing distributed logical content when equivalent records may be arranged into different files. It proposes a keyed, order-independent, multiplicity-sensitive digest while retaining per-file checksums for physical corruption. Duplicate rows must change the digest rather than collapsing as they would under set semantics. ([arXiv][5])

For local `oai-trial`, ordinary SHA-256 and explicit format-aware ordered fingerprints are enough. The multiset construction belongs in the production design.

### Independence boundary

The newest publication research is appropriately cautious: two implementations can still fail identically, and source provenance does not replace independent recomputation. ([arXiv][5])

Therefore:

```text
local:
  separate transform and verifier implementations
  plus mutation tests proving the verifier catches transform faults

production:
  separate verifier code package
  separate IAM role/account
  separately held proof key
  read-only source and staged-data access
  write-only proof publication
```

---

## Feature 9 — A strict, sanitized readiness report

**Priority: local P0**

`report.json` should be a commit certificate, not a log dump.

Recommended shape:

```json
{
  "schema": "anonymization_trial.report.v1",
  "status": "ready",
  "assurance_profile": "declared-literal-pseudonymization-v1",
  "run_id": "...",
  "algorithm_version": "pseudonym-v1",
  "key_mode": "public-deterministic-trial-namespace",
  "policy_sha256": "...",
  "source_manifest_sha256": "...",
  "corpus_manifest_sha256": "...",
  "verification_manifest_sha256": "...",
  "files_processed": 4,
  "records_processed": 1000,
  "bytes_in": 12345,
  "bytes_out": 12987,
  "replacements_applied": 8000,
  "format_counts": {
    "text": 1,
    "csv": 1,
    "json": 1,
    "sqlite": 1
  },
  "checks": {
    "policy": "pass",
    "occurrences": "pass",
    "protected_values": "pass",
    "structure": "pass",
    "publication": "pass"
  },
  "does_not_establish": [
    "discovery_of_unlisted_sensitive_data",
    "resistance_to_all_external_linkage",
    "formal_anonymity"
  ]
}
```

It must never contain:

* source literals;
* protected literals;
* generated pseudonyms;
* source rows or records;
* mapping tables;
* SQL containing values;
* sensitive relative paths;
* exception excerpts;
* raw quarantine content.

In production, internal verification receipts may contain more detailed safe identifiers, but the consumer report should remain aggregated. Even policy rule IDs can reveal subject presence, so per-rule metrics should be internal unless explicitly approved.

---

## Feature 10 — Known-truth synthetic fixtures

**Priority: local P0**

The medical de-identification validation papers provide one of the most transferable evaluation ideas: plant synthetic sensitive data in multiple structural locations, retain an exact truth key, and validate output mechanically against that key. ([arXiv][8])

The fixture generator should create an internal truth manifest containing:

* every planted rule occurrence;
* subject and alias membership;
* format and logical location;
* selected match after overlap resolution;
* protected-value occurrences;
* expected row and record counts;
* expected structural fingerprints;
* intended unsupported/rejection cases.

The truth manifest must remain under a test-private directory and never enter the release.

Required fixture families:

```text
ordinary cross-format subjects
multiple aliases for one subject
same-type distinct subjects
nested and prefix/suffix literals
replacement-to-source collision
protected/sensitive conflict
sensitive CSV header
sensitive JSON key
sensitive SQLite identifier
UTF-8 BOM and multibyte boundaries
invalid UTF-8
duplicate JSON keys
deep JSON
SQLite PK/FK/unique/without-rowid/WAL
symlink and special-file input
late transform and publication failures
```

---

## Feature 11 — Semantic property-based testing

**Priority: local P0**

Recent property-testing work makes an important distinction: useful property testing begins with a **semantic invariant**, not random input generation. PBT-Bench evaluates whether tests fail on the buggy implementation and pass on the fixed one; DiscPBT shows that semantic properties catch drift and boundary behavior that crash-oriented fuzzing misses. ([arXiv][9])

The test suite should encode these meta-properties.

| Property                | Required relationship                                             |
| ----------------------- | ----------------------------------------------------------------- |
| Policy permutation      | Reordering rules cannot change compiled plan or output            |
| File-order permutation  | Traversal order cannot change any per-file output                 |
| Chunk decomposition     | Whole-input transform equals arbitrary valid chunk decomposition  |
| Partition recomposition | Production partitions recombine to the same logical result        |
| Rerun determinism       | Same source, policy, scope, and algorithm produce the same corpus |
| Alias coherence         | All aliases of one subject/type yield one pseudonym               |
| Type injectivity        | Distinct same-type subjects have distinct replacements            |
| Non-interference        | Adding an absent rule does not alter existing output              |
| Span locality           | Only selected original spans may differ                           |
| Protected preservation  | Protected values and counts remain unchanged                      |
| Schema preservation     | Schema-bearing identifiers cannot silently change                 |
| Parse round-trip        | Accepted output parses under the declared format contract         |
| Source/output skeleton  | Redaction-normalized source and output are equivalent             |
| Fault atomicity         | Any injected fault produces no valid ready marker                 |
| Verifier sensitivity    | Every deliberate artifact mutation is rejected                    |
| Log non-disclosure      | Sensitive values never appear in metadata or diagnostics          |
| Resource bound          | Accepted input stays within documented memory/disk limits         |

Hypothesis should generate:

* rule permutations;
* overlapping literal sets;
* chunk sizes;
* Unicode strings under the supported policy;
* CSV rows and dialect edge cases;
* JSON depths and scalar combinations;
* SQLite schema variants;
* fault locations.

Its shrinking behavior is useful because it reduces complex failures to minimal reproducible counterexamples. ([arXiv][9])

Every retained regression should have a **fail-before-fix proof**, not merely a test that passes after the repair.

---

## Feature 12 — Deterministic fault injection and replay

**Priority: local P0**

Inject one fault after every meaningful transition:

```text
after source inventory
after policy compilation
during each format adapter
after each staged file
after complete staging
during source verifier reread
during output verifier reread
after verification
before corpus swap
after corpus swap
before report replace
during report replace
during cleanup
on SIGTERM
```

For each fault, prove:

* non-zero exit;
* no matching ready report;
* no raw/mapping leak;
* old valid release is either intact or explicitly unavailable rather than falsely valid;
* rerun reaches a deterministic recovery state;
* already verified work is not duplicated incorrectly.

Proof-gated publication evaluation uses silent drops, duplicate chunks, truncation, value corruption, and partition omission rather than relying solely on thrown exceptions. That is exactly the correct adversarial model for this pipeline. ([arXiv][5])

Add data-specific silent faults:

* drop one CSV row;
* duplicate one JSON element;
* modify one SQLite non-sensitive scalar;
* restore one sensitive literal;
* substitute another subject’s pseudonym;
* delete one protected value;
* add an unmanifested file;
* alter one report digest.

---

## Feature 13 — Separate privacy and utility gates

**Priority: local P0 for structural utility; production P1 for task utility**

RUPTA uses separate privacy and utility evaluators plus an optimizer. Tau-Eval similarly finds that no single anonymization method or generic similarity metric dominates across downstream tasks. ([arXiv][10])

The useful lesson is the separation—not the use of LLMs in the core.

### Local privacy correctness

```text
complete selected-literal replacement
protected-value preservation
subject and alias coherence
replacement collision freedom
metadata/log non-disclosure
```

### Local utility correctness

```text
valid same-format output
exact file-set preservation
CSV row/header/order/shape preservation
JSON topology/key/scalar preservation
text encoding/newline preservation
SQLite schema/row/FK/non-text preservation
```

### Production task utility

For each approved consumer, define a task-specific suite:

* representative SQL queries;
* joins and grouping;
* fraud/security timelines;
* aggregation totals;
* downstream parser compatibility;
* model or rules-engine performance;
* expected relationship traversals.

Production SIEM research demonstrates that anonymized artifacts can appear syntactically valid but fail operationally when temporal order, field semantics, or entity consistency are damaged. ([arXiv][11])

No generic BLEU, ROUGE, embedding similarity, or “looks reasonable” score should replace the format and consumer-specific utility contract.

---

## Feature 14 — Subject-level and inference-based privacy evaluation

**Priority: production P1; synthetic final audit locally**

A separate residual-risk evaluator should test:

```text
Can the released artifact reveal a policy subject?
Can several harmless-looking fields jointly expose an attribute?
Can records across files be linked beyond the permitted scope?
Can pseudonym frequency or timing reveal identity?
Can one subject be inferred from another subject’s retained context?
```

SPIA reports that masking more than 90% of PII spans can still leave subject-level protection much lower because contextual inference remains possible. ([arXiv][2])

This evaluation should output:

```json
{
  "schema": "anonymization_trial.residual_risk.v1",
  "attack_profile": "...",
  "corpus_manifest_sha256": "...",
  "subjects_evaluated": 20,
  "result": "pass_under_declared_attack_model",
  "findings": [],
  "does_not_prove": "universal_non_reidentifiability"
}
```

A passing result means only that the declared attacks did not succeed at the configured threshold.

---

## Feature 15 — Agentic re-identification red-team

**Priority: production P1; optional synthetic demonstration**

Recent research shows that LLM agents can combine weak cues with external information and outperform classical linkage approaches. One large-scale study reports up to 68% recall at 90% precision in its evaluated cross-platform settings; InferLink also finds that agents can reconstruct identities from scattered cues, sometimes during tasks not explicitly framed as deanonymization. ([arXiv][12])

AURA adds a web-search-assisted adversary and a utility-retention evaluator, reinforcing the need to test the actual released artifact against a realistic attacker rather than only checking identifier removal. ([arXiv][13])

A production red-team lane should:

* receive only the candidate release, never the raw corpus or map;
* operate in an approved isolated environment;
* use synthetic, consented, or formally authorized subjects;
* record all public evidence consulted;
* test target and non-target subjects;
* produce evidence chains rather than unsupported verdicts;
* block or route to human review on a successful linkage;
* never be described as proof when it fails to find a match.

This belongs outside the eight-hour correctness core because it is probabilistic, expensive, and open-ended.

---

## Feature 16 — Optional discovery and risk-adaptive anonymization

**Priority: production P1/P2; excluded from local authority**

The authoritative local boundary remains `policy.json`. However, production should add an optional discovery lane for unexpected sensitive values:

```text
schema rules
  -> deterministic recognizers
  -> domain NER
  -> optional local/approved LLM analysis
  -> candidate-risk classification
  -> policy coverage comparison
  -> quarantine or human review
```

The 2025 survey finds that NER remains foundational but is insufficient for implicit identifiers and contextual inference. ([arXiv][1])

The safe production rule is:

> Discovery may identify a reason to block or expand a reviewed policy. It may not silently decide that no sensitive data exists.

### Risk-adaptive research

TRIP-RAG ranks entities using privacy risk, knowledge divergence, and retrieval utility. IntentAnony uses intent-conditioned exposure budgets and distributed evidence chains. RLAA introduces an arbitrator and marginal privacy-gain versus utility-cost stopping criterion. ([arXiv][14])

These suggest a future **policy-profile engine**:

```text
strict_release:
  replace every authoritative policy item

analytics_preserving:
  authoritative replacements
  plus reviewed quasi-identifier generalization

public_research:
  stricter contextual and subject-level risk threshold

internal_low-risk:
  purpose-specific exposure allowance
```

They must not alter the current trial’s unconditional requirement to replace every policy-identified value.

---

## Feature 17 — Scope rotation and optional controlled linkage

**Priority: production P1**

Stable pseudonyms are necessary for the trial but dangerous as a global default.

Proteus provides a useful advanced pattern:

```text
stable keyed pseudonym
        +
time-rotating outer protection
        =
authorized correlation without unrestricted multi-snapshot linkage
```

Its threat model explicitly recognizes that simple stable pseudonyms expose equality and behavioral correlation even when plaintext recovery remains difficult. ([arXiv][4])

Production should support:

* corpus-scoped keys;
* purpose-scoped keys;
* tenant-scoped keys;
* key epochs;
* key/version binding in manifests;
* explicit rotation and reprocessing;
* optional outer encryption for pseudonyms at rest;
* time-bounded controlled access to linkage tokens;
* no global cross-customer scope.

### Re-identification and mappings

The base system should be non-reversible and store no map.

When business or legal requirements demand re-identification, add a separately controlled mapping vault with:

* a distinct account or security boundary;
* envelope encryption;
* dual authorization;
* per-access audit receipts;
* reason and case binding;
* retention and deletion policy;
* no bulk read API;
* no inclusion in transformation workers or release reports.

---

## Feature 18 — Formal privacy mechanisms only at the correct layer

**Priority: production option, not local core**

### Differential privacy

Differential privacy is appropriate for:

* aggregate analytics;
* telemetry statistics;
* downstream model training;
* public summary publication.

It is generally not the right mechanism for a base corpus whose rows, order, and relationships must remain individually useful and exactly verifiable. Proteus similarly observes that randomized aggregation can sacrifice the event-level fidelity needed for forensic reconstruction. ([arXiv][4])

For downstream model training, add:

* DP-SGD only under an explicit privacy budget;
* canary exposure tests;
* membership-inference tests;
* utility thresholds;
* separate reporting of data-layer pseudonymization and optimizer-layer DP.

The recent CSIRT study warns against assuming these layers compose trivially and reports significant utility limitations in its evaluated small-model regime. ([arXiv][7])

### Format-preserving encryption

Prεεmpt separates format-dependent values, where it uses FPE, from semantically meaningful numeric values, where it applies metric differential privacy. ([arXiv][15])

FPE should remain optional and be adopted only when the actual requirement is:

```text
same alphabet
same length
same checksum/domain constraints
reversible under authorization
```

It adds key management, small-domain, and cryptographic-validation complexity that the trial does not require.

---

## Feature 19 — Privacy-safe provenance and attestable evidence

**Priority: local P0 manifests; signed production evidence P1**

Every result should be attributable to an exact execution identity:

```text
run_id
source manifest digest
policy digest
privacy-contract digest
algorithm version
code commit
container image digest
dependency-lock digest
key ID and epoch, never key bytes
transformer version
verifier version
corpus manifest digest
verification receipt digest
publication decision
```

Research on trustworthy provenance emphasizes persistent artifact identifiers, immutability, auditability, and versioned histories. The useful features are those provenance semantics—not necessarily its proposed blockchain implementation. ([arXiv][16])

For production, sign:

* source manifests;
* verifier receipts;
* release manifests;
* active-pointer changes.

An evidence-driven CI paper combines deterministic builds with TEE-based attestations. TEEs could strengthen high-assurance production provenance, but they attest execution identity and environment; they do not replace semantic corpus verification. ([arXiv][17])

---

## Feature 20 — Agents remain untrusted producers

**Priority: development control P0**

Tau, project agents, coding models, and reviewer models should be allowed to propose:

* source changes;
* tests;
* cost assumptions;
* architecture;
* issue closures.

They must not directly decide that a release is valid.

Proof-carrying agent research describes an outer deterministic verifier that decides whether an untrusted agent branch can merge. ([arXiv][18])

For this project:

```text
agent claim
   !=
release evidence

reviewer PASS
   !=
release evidence

test command reported in prose
   !=
test receipt

only independently readable artifacts and reproducible commands count
```

Tau should require creator and verifier/reviewer nodes to be distinct, bind all receipts to the immutable goal and candidate commit, and fail the DAG when required evidence is missing.

---

# 3. What must land in the eight-hour local implementation

These features are the reliable cutting edge that actually fit the trial.

| Priority | Required local feature                                    |
| -------- | --------------------------------------------------------- |
| P0.1     | Versioned privacy contract and explicit non-claims        |
| P0.2     | Strict JSON-Schema policy validation                      |
| P0.3     | Canonical subject/alias registry                          |
| P0.4     | Deterministic domain-separated type-specific pseudonyms   |
| P0.5     | Global collision and protected-overlap preflight          |
| P0.6     | Original-span, non-cascading leftmost-longest matcher     |
| P0.7     | Schema-aware text, CSV, JSON, and SQLite adapters         |
| P0.8     | Bounded-memory behavior or explicit safe size limits      |
| P0.9     | Immutable source manifest and change detection            |
| P0.10    | Private same-filesystem staging                           |
| P0.11    | Separate full-corpus verifier with fresh rereads          |
| P0.12    | Format-specific utility and structure fingerprints        |
| P0.13    | `report.json` as the last and sole readiness marker       |
| P0.14    | Recovery from every partial state                         |
| P0.15    | Known-truth fixture oracle                                |
| P0.16    | Property tests and fail-before-fix retained regressions   |
| P0.17    | Silent-corruption and crash fault injection               |
| P0.18    | Sanitized report, stderr, temp names, and proof artifacts |
| P0.19    | Exact Docker and mounted-run contracts                    |
| P0.20    | Two-scale benchmark in fresh subprocesses                 |

The research does **not** justify sacrificing any of these deterministic guarantees to add a model, distributed framework, mapping service, or visually impressive dashboard.

---

# 4. What belongs in the production design

These are required to make the architecture genuinely state-of-the-art at TB/PB scale, but most should be documented rather than implemented during the trial.

| Production capability  | Design                                                                    |
| ---------------------- | ------------------------------------------------------------------------- |
| Immutable source       | Versioned S3 objects plus producer-signed source manifest                 |
| Scoped pseudonyms      | Tenant/purpose/corpus HMAC keys protected by KMS                          |
| Worker key use         | One envelope-key unwrap per task; local HMAC thereafter                   |
| Partition identity     | Source version + policy + algorithm + key epoch + range/object ID         |
| Text boundaries        | Longest-literal overlap with deterministic ownership                      |
| CSV boundaries         | Quote-aware record partitioning                                           |
| JSON scale             | Prefer JSONL/record-framed data; bounded conversion for monolithic arrays |
| SQLite scale           | One isolated Batch/ECS task per database object                           |
| Backpressure           | SQS queues and explicit concurrency quotas                                |
| Orchestration          | Step Functions with durable checkpoints and replay                        |
| Staging                | Immutable run/attempt prefixes                                            |
| Verification           | Separate code and IAM/account trust domain                                |
| Distributed proof      | Per-file hashes plus multiplicity-sensitive logical digest                |
| Publication            | Immutable release manifest plus conditional active-pointer update         |
| Retry safety           | Idempotency key and completed-partition ledger                            |
| Discovery              | Schema rules, recognizers, optional NER/LLM, quarantine on gaps           |
| Residual risk          | Subject-level and agentic re-identification assessment                    |
| Utility                | Consumer-specific replay/query/task suite                                 |
| Re-identification      | Optional isolated mapping vault only when legally required                |
| Audit                  | Signed manifests, CloudTrail, privacy-safe metrics                        |
| Retention              | Distinct raw, quarantine, staging, proof, release, and deletion policies  |
| Advanced unlinkability | Purpose/epoch rotation or optional outer pseudonym encryption             |
| ML use                 | Separate DP-SGD and canary-extraction evaluation                          |

---

# 5. Features that should be rejected from the deterministic core

| Rejected core idea                           | Reason                                                                           |
| -------------------------------------------- | -------------------------------------------------------------------------------- |
| LLM-generated rewriting                      | Nondeterministic, semantically lossy, difficult to verify completely             |
| NER or Presidio as policy authority          | Detection can miss contextual and indirect identifiers                           |
| Agent/reviewer prose as release proof        | Self-attestation is not independent evidence                                     |
| Transformer reusing itself as verifier       | A shared bug can transform and certify the same wrong behavior                   |
| Sampling-only verification                   | The brief requires the complete corpus                                           |
| Global stable pseudonyms                     | Unnecessary cross-customer and cross-purpose linkage                             |
| Random Faker values                          | Stability and injectivity depend on external mutable state                       |
| Per-record KMS calls                         | Excessive cost, latency, throttling, and availability coupling                   |
| Central mapping DB solely for coherence      | Deterministic keyed derivation already provides coherence                        |
| DP in the base transform                     | Conflicts with record-level fidelity and repeatability                           |
| FPE without exact-domain need                | Adds cryptographic and domain complexity without satisfying a stated requirement |
| Naive byte partitioning                      | Misses matches and breaks CSV/UTF-8 records                                      |
| Silent JSON/SQLite feature acceptance        | Unsupported semantics should reject before publication                           |
| Blockchain provenance in the trial           | Adds complexity without improving the local correctness oracle                   |
| TEE as replacement for verification          | Attests execution, not output semantics                                          |
| Adaptive selective omission of policy values | Directly violates the authoritative policy contract                              |

LLM-based anonymization research remains valuable for the risk plane. RUPTA itself acknowledges the substantial computational cost of an iterative privacy/utility/optimization architecture, while Tau-Eval shows that utility behavior varies by downstream task. ([arXiv][10])

---

# 6. Paper-to-feature crosswalk

| Research cluster                                   | Feature we should take                                                                                                               | Disposition                                                                      |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| **2025 anonymization survey**                      | Hybrid detection, explicit quasi-identifier risk, privacy/utility evaluation, recognition of LLMs as both defender and attacker      | Architecture and risk-plane foundation. ([arXiv][1])                             |
| **AnonShield**                                     | Schema-aware processing, deterministic HMAC pseudonyms, streaming, cache, consistency across records                                 | Core production pseudonym design; no GPU/NER dependency locally. ([arXiv][6])    |
| **Proteus**                                        | Stable linkage tokens, explicit equality leakage, epoch rotation, controlled time-bounded access, source-side protection             | Production scope and unlinkability options. ([arXiv][4])                         |
| **HMAC + DP-SGD CSIRT study**                      | Separate data-layer pseudonymization from training-layer privacy; canary attacks; do not assume composition                          | Production ML extension only. ([arXiv][7])                                       |
| **Production SIEM artifacts**                      | Privacy boundary as a first-class object; preserve temporal order and entity consistency; deterministic verifier; measured non-claim | Core utility and assurance model. ([arXiv][11])                                  |
| **RUPTA**                                          | Separate privacy evaluator, utility evaluator, and optimizer                                                                         | Take the separation; keep the optimizer out of deterministic core. ([arXiv][10]) |
| **Tau-Eval**                                       | Task-specific utility, reproducible privacy/utility dimensions, no universal metric                                                  | Core acceptance matrix and production task gates. ([arXiv][19])                  |
| **RAT-Bench**                                      | Measure residual re-identification risk, including indirect and unusual identifiers                                                  | Production risk gate. ([arXiv][20])                                              |
| **SPIA**                                           | Subject—not span—as the privacy unit; include non-primary subjects                                                                   | Core subject registry plus production inference tests. ([arXiv][2])              |
| **Large-scale LLM deanonymization / InferLink**    | Treat weak cross-source cues and benign agent behavior as real attack paths                                                          | Agentic red-team threat model. ([arXiv][12])                                     |
| **AURA**                                           | Separate privacy localization from utility reconstruction; test with web-assisted attacker                                           | Optional risk plane, not local transformer. ([arXiv][13])                        |
| **IntentAnony / TRIP-RAG / RLAA**                  | Exposure budgets, context-sensitive risk, rational stopping, privacy-gain versus utility-cost                                        | Future reviewed policy profiles. ([arXiv][14])                                   |
| **Medical de-identification validation resources** | Planted synthetic PII, known-truth manifests, independent validators                                                                 | Core fixture and mutation methodology. ([arXiv][8])                              |
| **Proof-Gated Publication**                        | Invisible physical staging, independent verification, durable replay, metadata commit last, silent-fault tests                       | Core publication model and production notary. ([arXiv][5])                       |
| **Correct-by-Design Lakehouse**                    | Isolated branches, state-machine reasoning, prevent aborted branches from becoming valid inputs                                      | Recovery and stale-state restrictions. ([arXiv][21])                             |
| **PBT-Bench**                                      | Semantic invariant first; fail-on-bug/pass-on-fix scoring                                                                            | Core retained-regression standard. ([arXiv][9])                                  |
| **DiscPBT**                                        | Decomposition, recomposition, equivalence, cardinality, schema-aware generation                                                      | Core chunk/partition/format property suite. ([arXiv][22])                        |
| **Proof-carrying agents**                          | Untrusted agents produce candidate work; deterministic outer verifier controls merge                                                 | Tau development governance. ([arXiv][18])                                        |
| **Evidence-driven CI and provenance**              | Build/image identity, signed evidence, persistent artifact IDs, versioned lineage                                                    | Production evidence and optional attestation. ([arXiv][17])                      |
| **Prεεmpt**                                        | FPE for strict format-constrained values and DP for semantically meaningful values                                                   | Documented alternative, not base trial path. ([arXiv][15])                       |

---

# 7. Exact changes to the existing GitHub tickets

## #2 — Semantics and acceptance matrix

Add:

* `docs/PRIVACY_CONTRACT.md`;
* explicit protected unit, scope, allowed linkage, adversary, and release standard;
* proof-plane versus risk-plane distinction;
* exact local assurance claims and non-claims;
* subject-level acceptance rows;
* source-to-sink versus mounted-input-to-output claim boundary;
* production pseudonym scope modes.

## #3 — Policy compiler and matcher

Add:

* canonical subject registry;
* length-prefixed canonical identity encoding;
* `scope_id`, `algorithm_version`, and `key_mode`;
* production HMAC construction;
* minimum internal pseudonym entropy;
* source-corpus collision preflight;
* public local key-mode disclosure;
* subject-level coherence receipt;
* a separate naive reference detector for verifier use;
* property tests for chunk decomposition and non-interference.

## #4 — Transactional publication

Adopt the state sequence:

```text
physical/stage -> verify -> durable/checkpoint -> metadata/report
```

Also add:

* invalidate old readiness marker before corpus replacement;
* recovery table for every observable partial state;
* source manifest reread before commit;
* explicit rule preventing an aborted/stale staging tree from becoming a future run’s trusted parent;
* run-owned cleanup only;
* silent drop, duplicate, and truncation faults in addition to exceptions.

## #5, #6, and #7 — Format adapters

Add a common adapter contract that returns:

* physical digest;
* structural digest;
* source and output record counts;
* redaction-normalized skeleton digest;
* protected occurrence summary;
* safe subject/type replacement counts;
* declared format-contract version.

Each adapter should have a decomposition-equivalence property test.

## #8 — Independent verifier

Add:

* separate source and output reread paths;
* independent reference matcher;
* source/output skeleton comparison;
* rule-level and subject-level coverage;
* physical, ordered-structural, and—where appropriate—multiset proofs;
* source-attestation/non-attestation distinction;
* strict assurance and non-claim fields;
* deliberate mutant transforms to demonstrate verifier sensitivity;
* no sampling.

## #9 — Docker and benchmark

Expand benchmark axes beyond record count:

```text
bytes
records
policy rule count
canonical subjects
alias fan-out
longest literal
overlap density
largest field/record
format mix
SQLite rows/schema complexity
output expansion
verifier overhead
```

Require fresh subprocesses, fixed synthetic seeds, known-truth verification, and safe failure under memory/CPU limits.

## #10 — Production design

Add:

* corpus/purpose/tenant key scopes;
* key epoch and reprocessing semantics;
* optional outer epoch encryption;
* separate verifier/steward account;
* signed source manifest;
* multiplicity-sensitive partition proof;
* conditional active pointer;
* residual-risk and downstream-utility lanes;
* optional mapping vault;
* DP-SGD/canary lane for later model training;
* explicit distinction between authoritative policy and probabilistic discovery.

## #11 — Final audit

Add:

* subject-level coverage readback;
* synthetic agentic re-identification exercise;
* proof that every retained regression fails against an injected broken implementation;
* old-report/new-corpus crash test;
* source-manifest substitution test;
* candidate report copied from another corpus test;
* declaration that a failed red-team attack is not proof of anonymity;
* independent reviewer check of research-derived non-claims.

A separate post-trial issue would be appropriate for the complete residual-risk plane:

```text
[P1] Add subject-level, quasi-identifier, and agentic re-identification risk evaluation
```

It should not delay the deterministic eight-hour implementation.

---

# Final research verdict

A genuinely cutting-edge and reliable system for this goal has five defining properties:

1. **Pseudonyms are stable only within a declared scope**, not globally by accident.
2. **The full source-to-output relationship is independently recomputed**, not inferred from the transformer’s success.
3. **Nothing becomes ready until proof passes and the final publication marker is committed last.**
4. **Privacy correctness, structural utility, and residual re-identification risk are separate gates with separate claims.**
5. **Agents, models, workers, and reviewers are all treated as untrusted producers of candidate evidence.**

The highest-value research contribution is therefore not an LLM model or another PII library. It is the combination of:

```text
canonical subject semantics
+ scoped keyed pseudonyms
+ schema-aware bounded transformation
+ known-truth and semantic property tests
+ independent complete verification
+ proof-gated publication
+ subject-level and agentic residual-risk evaluation
```

That combination gives us a local submission that is small enough to reason about, a production architecture that scales without weakening the invariant, and documentation that makes strong claims only where the evidence supports them.

[1]: https://arxiv.org/html/2508.21587v1 "https://arxiv.org/html/2508.21587v1"
[2]: https://arxiv.org/abs/2604.21211 "https://arxiv.org/abs/2604.21211"
[3]: https://arxiv.org/abs/2509.10165 "https://arxiv.org/abs/2509.10165"
[4]: https://arxiv.org/html/2603.06540 "https://arxiv.org/html/2603.06540"
[5]: https://arxiv.org/pdf/2608.14643 "https://arxiv.org/pdf/2608.14643"
[6]: https://arxiv.org/html/2606.15650v1 "https://arxiv.org/html/2606.15650v1"
[7]: https://arxiv.org/html/2606.28479v1 "https://arxiv.org/html/2606.28479v1"
[8]: https://arxiv.org/abs/2508.01889 "https://arxiv.org/abs/2508.01889"
[9]: https://arxiv.org/html/2605.15229v2 "https://arxiv.org/html/2605.15229v2"
[10]: https://arxiv.org/html/2407.11770v2 "https://arxiv.org/html/2407.11770v2"
[11]: https://arxiv.org/html/2606.21389v1 "https://arxiv.org/html/2606.21389v1"
[12]: https://arxiv.org/abs/2602.16800 "https://arxiv.org/abs/2602.16800"
[13]: https://arxiv.org/abs/2605.30848 "https://arxiv.org/abs/2605.30848"
[14]: https://arxiv.org/html/2603.26074v3 "https://arxiv.org/html/2603.26074v3"
[15]: https://arxiv.org/abs/2504.05147 "https://arxiv.org/abs/2504.05147"
[16]: https://arxiv.org/abs/2505.24675 "https://arxiv.org/abs/2505.24675"
[17]: https://arxiv.org/abs/2605.21089 "https://arxiv.org/abs/2605.21089"
[18]: https://arxiv.org/html/2510.09567v1 "https://arxiv.org/html/2510.09567v1"
[19]: https://arxiv.org/html/2506.05979v2 "https://arxiv.org/html/2506.05979v2"
[20]: https://arxiv.org/abs/2602.12806 "https://arxiv.org/abs/2602.12806"
[21]: https://arxiv.org/html/2602.02335v3 "https://arxiv.org/html/2602.02335v3"
[22]: https://arxiv.org/html/2606.11132v1 "https://arxiv.org/html/2606.11132v1"
