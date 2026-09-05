# OAI trial — technical walkthrough and adversarial Q&A

> **Presentation draft for review.** Thirty minutes of prepared explanation, followed by at least fifteen minutes for questions. The question bank is reference material, not another fifteen minutes of planned slides.
>
> **Frozen implementation:** [`0375af56bf681e9441edcb7433cfe58951db77b2`](https://github.com/grahama1970/oai-trial/tree/0375af56bf681e9441edcb7433cfe58951db77b2). This document is a post-submission presentation artifact; it does not change the submitted ZIP or runtime.
>
> **Evidence labels:** **VERIFIED — source** means the cited implementation was inspected. **VERIFIED — local execution** means a retained execution receipt was read back. **REVIEWER EVIDENCE** means the human supplied WebGPT's bounded review; it is not an independent execution by WebGPT. **INFERENCE / PROPOSAL** marks design choices, anticipated questions, and future work.

## How to use this document

Read the **Say** passages as speaker notes, not as claims that every implementation decision was made without AI assistance. Use **Show** for one short code jump. Answer the question asked; open the deeper evidence only when needed.

The seven section IDs match the existing deck. Their timing below replaces the older 36-minute speaker notes. Existing slide exports have not yet been regenerated from this document.

| Section / future slide | Time | Audience takeaway | Evidence jump |
|---|---:|---|---|
| [01-brief](#01-brief) | 00:00–03:00 | The guarantee is policy-bounded pseudonymization, not general anonymity. | [Policy compiler][C01] |
| [02-architecture](#02-architecture) | 03:00–07:00 | Transformation and release authorization are different steps. | [Pipeline orchestration][C02] |
| [03-semantics](#03-semantics) | 07:00–13:00 | Stable identity, explicit overlap rules, and typed verification preserve meaning. | [Pseudonyms][C03], [matcher][C04], [typed equality][C05] |
| [04-reliability](#04-reliability) | 13:00–18:00 | Verified bytes and private work artifacts must stay on opposite sides of the release boundary. | [Publication][C06], [canonical paths][C07] |
| [05-evidence](#05-evidence) | 18:00–23:00 | Demonstrated failures and output readback support the claims; fuzzy discovery grants no authority. | [Regression][C08], [approval][C09], [qualification][C10] |
| [06-production](#06-production) | 23:00–27:00 | Production scales the work while retaining one corpus-level release decision. | [AWS design][D02], [cost model][C11] |
| [07-nonclaims](#07-nonclaims) | 27:00–30:00 | The remaining limits are explicit engineering decisions and disclosure obligations. | [Submission][D01] |
| Questions / follow-ups | 30:00–45:00+ | Inspect the challenged invariant rather than race through more slides. | [Question bank](#adversarial-question-bank) |

**If interrupted:** count the interruption against the question reserve. Skip optional code detail, not the final limitations statement. Do not build an image, install dependencies, or repair a browser during the presentation.

<a id="01-brief"></a>
## 01 — What problem did I choose to solve? · 3 minutes

**Evidence boundary: VERIFIED — source.** [The brief][D00] requires CSV, JSON, UTF-8 text, and SQLite; consistent identities; preservation of protected data and structure; and verification before a release is marked ready.

### Say

“The assignment calls this anonymization. The narrower guarantee I can defend is deterministic, policy-bounded pseudonymization. Given a declared literal policy, the pipeline replaces those values consistently across four formats, preserves protected meaning, and refuses to authorize an output that fails verification.

“The policy is important because detection and transformation are different problems. A name that the policy does not identify is not automatically discovered by the exact engine. I did not hide that limitation behind a claim that a clean scan makes the data anonymous.

“The same fictional person can appear in a CSV row, a JSON object, a text export, and a SQLite table. If their aliases belong to one declared identity, the replacements should agree. If two rules contradict each other about identity or protected content, the pipeline should reject the policy rather than guess.

“My organizing decision was to make release authorization the center of the design. A successful string replacement is not the same thing as a safe, usable release.”

### Show

Open [`policy.py::compile_policy`][C01], then `examples/policy.json`. Point out `sensitive_values`, `protected_values`, and the optional `subject_id`. The approved input contract is version 1, with literal matching and case sensitivity enabled by default.

**Tradeoff:** explicit policy boundaries make correctness reviewable, but do not discover every sensitive item in an unknown dataset.

**Transition:** “Once the contract is explicit, the pipeline can decide whether the output deserves a readiness marker.”

**Question handles:** Q01–Q03.

<a id="02-architecture"></a>
## 02 — Walk one input through the pipeline · 4 minutes

**Evidence boundary: VERIFIED — source.** [`run_pipeline`][C02] orchestrates preflight, staging, transformation, verification, source checks, sealing, and publication.

### Say

“The evaluator has a small interface: build the Docker image, run a self-contained demonstration, or mount an input bundle and an output directory. The input bundle contains the policy and a corpus; the successful output contains a corpus and a sanitized report.

“Inside `run_pipeline`, the code validates the policy path and preflights the input inventory. It records source digests before transforming files. Each adapter understands its format; this is not a text substitution over the raw bytes of a SQLite database or an entire serialized JSON object.

“The output is first written into a private staging directory on the output filesystem. That placement lets publication use a same-filesystem rename. The staged files are then reread and checked against the source and policy. After verification, the source digests are checked again. The verified output receives a content-manifest digest that is checked again immediately before publication.

“The extra file/folder interface does not replace this engine. `input_bundle` validates and snapshots a supported source plus a separate policy into the bundle shape the engine already understands. The shared skill is another entrypoint, not a second implementation of the anonymization logic.”

### Show

Use this **conceptual flow**, then follow the actual calls in [the source][C02]:

```text
policy + input inventory
        ↓
private staged corpus
        ↓
format-aware transformation
        ↓
full-corpus reread and verification
        ↓
source unchanged? → seal verified output
        ↓
promote corpus → publish report.json last
```

The staging directory is mode `0700`; the separate discovery work artifacts are mode `0600`. Neither permission mode is a substitute for enforcing the release boundary.

**Tradeoff:** the local implementation materializes files and several verification structures. It is not a demonstrated bounded-memory TB/PB streaming system.

**Transition:** “The verifier can only reconstruct the correct result if matching and identity semantics are deterministic.”

**Question handles:** Q04–Q06.

<a id="03-semantics"></a>
## 03 — Identity, overlap, and meaning · 6 minutes

**Evidence boundary: VERIFIED — source.** [Identity planning][C03], [span selection][C04], and [location-aware verification][C05] are separate concerns.

### Say: identity

“Identity coherence is supplied by the policy, not inferred from someone having the same first name. Rules identify a data type and a canonical identity. Aliases of that identity intentionally share a replacement for that type.

“The derivation includes an algorithm version, a namespace, policy version, data type, identity, and salt. Identities are processed in deterministic sorted order. If two identities collide in a replacement domain, the allocator searches deterministically for a distinct value; if it cannot satisfy the bounded contract, it rejects instead of silently merging people.

“This is a public deterministic namespace, not a secret-key cryptographic design. Someone who knows the identity inputs can recompute it. Stability is for the same compiled policy and identity set; I would not promise that collision assignments remain unchanged through arbitrary policy growth.”

**Show — exact excerpt from `pseudonyms.py::_digest`:**

```python
def _digest(policy_version: int, data_type: str, identity: str, salt: int) -> str:
    material = f"{ALGORITHM_VERSION}:{SCOPE_ID}:{policy_version}:{data_type}:{identity}:{salt}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
```

Explain the inputs before discussing the hash. Hashing alone neither establishes anonymity nor supplies a secret.

### Say: overlaps and replacement cascades

“The matcher finds candidate spans in the original input. It chooses leftmost matches, the longest match at a shared start position, and a stable rule-ID tie-break. It then emits the selected replacements once. It does not run a sequence of `text.replace` calls that might replace text produced by an earlier rule.

“Protected-versus-sensitive conflicts are rejected at policy compilation, including containment and boundary overlaps. That is deliberately conservative. The pipeline should not choose between two contradictory promises on behalf of the caller.”

**Show — exact excerpt from `matcher.py::Matcher.replace`:**

```python
    def replace(self, text: str) -> tuple[str, int]:
        spans = self.find(text)
        if not spans:
            return text, 0
        out: list[str] = []
        cursor = 0
        for span in spans:
            out.append(text[cursor:span.start])
            out.append(span.replacement)
            cursor = span.end
        out.append(text[cursor:])
        return "".join(out), len(spans)
```

“No rescan” does not mean that an emitted pseudonym may contain another sensitive literal. The final residual scan can still reject that output.

### Say: structure is not enough

“Checking that all original names disappeared would miss a different error: two valid pseudonyms swapped between rows. A count can remain correct while the person associated with a value is wrong.

“The verifier therefore reconstructs expected values at their locations. It also distinguishes types. In Python, `True == 1` and `1 == 1.0`, but changing a JSON Boolean to a number, or a SQLite integer to a real value, is not harmless preservation of meaning.

“For SQLite, the verifier compares logical schema definitions, column and foreign-key metadata, row identity, and typed values. A view definition can contain sensitive text even when table cells are clean.”

**Show — exact excerpt from `verification.py::_typed_equal`:**

```python
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_typed_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(
            _typed_equal(x, y) for x, y in zip(a, b, strict=True)
        )
    return a == b
```

**Tradeoff:** this verifier independently rereads and re-derives values, but shares replacement primitives with the transformer. Correlated defects remain possible. The supported SQLite surface is bounded; unsupported constructs reject rather than receive a best-effort rewrite.

**Transition:** “Correct values are necessary. The next question is which bytes are allowed to appear in a release at all.”

**Question handles:** Q07–Q12.

<a id="04-reliability"></a>
## 04 — Publication and the defect the reviewer caught · 5 minutes

**Evidence boundary: VERIFIED — source; REVIEWER EVIDENCE for the bounded follow-up PASS.** [Publication][C06] and [canonical destination validation][C07] enforce different parts of the boundary.

### Say: report-last publication

“The release contract is report-last. During publication, an old readiness marker is removed before the corpus is changed. The staged digest is checked against the digest of the verified bytes, the corpus is promoted, and the new report is written through a temporary file and renamed last.

“Writing the report requires a complete write, not one optimistic `os.write` call. The implementation loops until all bytes are written, rejects zero progress, and fsyncs before the readiness-marker rename.

“This is not an atomic transaction over every output file. A crash can leave corpus bytes without a readiness marker. A consumer must not treat the presence of a corpus directory alone as permission to use it. The intended guarantee is no newly authorized partial release—not that every failure leaves the output directory empty or that this has passed an exhaustive power-loss campaign.”

**Show — exact excerpt from `_publish`:**

```python
        remaining = memoryview(data)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("report write made no progress")
            remaining = remaining[written:]
        os.fsync(fd)
```

### Say: the canonical-path bug

“The final external review found a real gap in the optional discovery workflow. A private review could be directed into an already READY corpus using a relative path or a symlink alias. The validator resolved the path for one check, then walked the original lexical parents for another. The write followed a different notion of location from the release check.

“For example, from inside `release/corpus`, the lexical parents of `review.json` do not lead the validator up to `release`. The resolved destination does. The fix is to validate that resolved location and carry it into the write. Approval must validate its sibling receipt as well as the policy file.

“This matters because a discovery review contains raw candidate names. Mode `0600` and exclusive creation are good properties, but they do not make it acceptable to add that file beneath an existing READY release.”

**Show — exact excerpt from `bundle.py::separate_output`:**

```python
    out = output.resolve()
    for source in inputs:
        path = source.resolve()
        if out == path or out.is_relative_to(path) or path.is_relative_to(out):
            raise AnonError(AnonErrorCode.UNSAFE_INPUT, "output overlaps an input")
    if out.is_dir() and any(out.iterdir()):
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "use an empty output directory")
    if any(
        (parent / "report.json").is_file() and (parent / "corpus").is_dir()
        for parent in out.parents
    ):
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "work artifacts must stay outside a release")
    return out
```

The complete function also rejects output-file symlinks before resolution. Its production callers use the returned `Path`. `write_private` is a writer of an already validated path, not a standalone release-boundary validator.

**Tradeoff:** this closes the demonstrated deterministic path aliases. It is not a claim of protection against a hostile concurrent process replacing filesystem objects after validation.

**Transition:** “The strongest demonstration is not this explanation—it is a test that creates a real release and tries to violate its boundary.”

**Question handles:** Q13–Q17.

<a id="05-evidence"></a>
## 05 — Evidence, optional discovery, and approval authority · 5 minutes

**Evidence boundary: VERIFIED — source and retained local execution; REVIEWER EVIDENCE is separately attributed.**

### Say: test the failure, not the status label

“The retained path regression creates a real READY release and snapshots the complete file inventory and bytes. It then attempts discovery and approval through relative and symlinked destinations, including a receipt-only symlink. Each rejected operation must leave that snapshot unchanged.

“The positive controls matter just as much. Equivalent relative and symlinked destinations in a normal private work directory still succeed, and the generated review, policy, and receipt have private permissions. Otherwise a test could pass simply because every operation had been disabled.

“I also distinguish source review from execution. WebGPT inspected the pinned source and regression and closed its specific blocker. It did not execute pytest or Docker in that review. Locally, the targeted test ran through both the project interface and the wrapper, and the submission qualification cloned the exact pushed candidate, built Docker, exercised the evaluator interface, independently read the output, and checked the ZIP.”

**Show — optional rehearsal command, not a requirement to rerun during the talk:**

```bash
uv run --extra dev --extra discovery pytest -q \
  tests/test_discovery_boundaries.py::test_work_artifacts_cannot_enter_release_via_relative_or_symlink_paths
```

Open [the test][C08] and show the attempted destination and `release_bytes()` comparison—not only a green test result. The [retained wrapper eval][E02] is execution evidence with a stated scope, not a universal security score.

### Say: what RapidFuzz does and does not do

“The optional extension proposes whole-field or whole-line name aliases. It does not turn the exact engine into fuzzy replacement. Discovery scores candidate values, rejects ties or insufficient separation between identities, and writes private review material. Its default threshold is 90 and its identity margin is 5; these are selection parameters, not calibrated probabilities.

“A human must approve specific candidate IDs. Approval reruns discovery against the current policy, corpus, and settings, compares the complete report, and sends the proposed additions through the real policy compiler. Only then does it write a new exact literal policy. The standard pipeline must still transform and verify the corpus before release.

“Consequently, a misspelling like `Alicee` is not automatically assigned to `Alice` because a fuzzy score is high. The review-and-approval step is explicit, and policy conflicts still reject.”

**Show — exact excerpt from `discovery.py::approve`:**

```python
    fresh = discover(bundle, supplied.threshold, supplied.margin)
    if asdict(fresh) != asdict(supplied):
        _reject(AnonErrorCode.DISCOVERY_STALE, "review differs from current inputs or settings")
    by_id = {c.id: c for c in fresh.candidates}
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(by_id):
        _reject(AnonErrorCode.DISCOVERY_REJECTED, "approve explicit, unique proposed candidate ids")
```

**Tradeoff:** whole-value proposals are deliberately bounded and can miss names inside longer narrative text. Discovery permits at most 1,000 eligible name rules and 10,000 text values. The default Docker image does not install RapidFuzz; the optional build argument enables that dependency.

**Transition:** “These checks establish a bounded local mechanism. A production design must preserve its semantics without pretending the local benchmark proves petabyte throughput.”

**Question handles:** Q18–Q23.

<a id="06-production"></a>
## 06 — What changes at terabyte and petabyte scale? · 4 minutes

**Evidence boundary: INFERENCE / PROPOSAL, supported by an inspected design and reproducible arithmetic. No cloud deployment or TB/PB benchmark is claimed.**

### Say

“The worked production design uses S3 for input, staging, release, and quarantine; EventBridge and SQS for dispatch; and a bounded Fargate or Batch worker pool. The key architectural change is a corpus manifest and a single active pointer rather than a local filesystem readiness marker.

“Workers can finish at different times. Their individual success must not make a partial corpus visible as a complete release. The proposed coordinator waits for verification of the expected object set, writes an immutable manifest of object versions or keys and digests, and updates the active pointer. Consumers must follow that protocol rather than enumerate staging objects.

“Partitioning must understand formats. A CSV record can span lines; a UTF-8 character can span bytes; a literal can cross a text partition. Arbitrary byte splitting would corrupt meaning or miss replacements. JSON and SQLite need bounded whole-document or snapshot treatment unless a different supported framing is introduced.

“The cost model makes its assumptions executable. The reference scenario assumes 200 workers at 20 MB/s, yielding an ideal 4 GB/s before verification, retries, and overhead. That is an assumption, not a measured property of this implementation. The design targets one hour for 1 TB and seven days for 1 PB under the stated scenario.

“The first production step would be to validate representative throughput, file-size distributions, retention, requests, account quotas, and security boundaries—not simply multiply a small synthetic benchmark.”

### Show

Open the [production design][D02], then the [cost model][C11]. The model can be reproduced with:

```bash
python scripts/estimate_aws_cost.py --inputs costs/aws-us-east-1-inputs.json
```

Do not memorize a headline price without its inputs. The documented estimate is about $86 for 1 TB and $85,734 for 1 PB under dated list-price assumptions; transfers, storage tiers, retention, expansion, and account quotas require attention. These are model outputs, not a billing quote.

**Critical qualification:** every partition must use the same versioned identity/replacement plan. Independent per-partition collision allocation over different identity subsets could break coherence. A secret HMAC key alone does not solve that coordination problem.

**Tradeoff:** retries and distributed publication need idempotency and conditional/versioned state transitions. The local code does not implement that cloud protocol. The proposed extra `ripgrep` cross-check is not wired into the shipped local verifier.

**Transition:** “The last part of the walkthrough is the boundary I will not overstate.”

**Question handles:** Q24–Q27.

<a id="07-nonclaims"></a>
## 07 — What remains, and what did the review establish? · 3 minutes

**Evidence boundary: VERIFIED — source for current disclosures; REVIEWER EVIDENCE for the human-supplied bounded PASS; INFERENCE / PROPOSAL for future priorities.**

### Say

“The final reviewer closed the canonical-path blocker at the submitted commit. That is a useful, specific conclusion—not a statement that the system has no vulnerabilities or that all privacy risks are solved.

“The exact engine does not establish formal anonymity, resistance to external linkage, or discovery of all unlisted identifiers. The pseudonym namespace is public. The verifier shares replacement primitives. Processing is per-file rather than production streaming. We have not performed an exhaustive crash campaign or a cloud-scale deployment.

“The timebox also needs a direct answer. `SUBMISSION.md` records post-timebox corrections and additions. Its retrospective eight-hour allocation is an estimate, not an instrumented proof of compliance. I used AI assistance and external review, and the work took longer than intended. A technical PASS does not erase that.

“With more time, I would prioritize representative workload measurements, stronger verifier independence, and tenant-scoped key and identity-plan management. Those are future decisions, not hidden claims about this submission.

“The result I can defend is a bounded mechanism: explicit matching semantics, coherent pseudonyms, format-aware transformation, verification before readiness, and a corrected separation between private discovery work and released data. I can show the code and the evidence for each of those claims.”

### Close

“Which boundary would you like to inspect: identity mapping, typed verification, publication, or discovery approval?”

**Question handles:** Q28–Q30. Stop the prepared talk at 30 minutes.

<a id="adversarial-question-bank"></a>
## Adversarial question bank — reference, not spoken script

**INFERENCE:** these are plausible challenges derived from the brief, implementation, and review history. They are not a prediction of the interviewer's actual questions. Answers describe the pinned implementation unless explicitly marked as proposals.

Section numbers are the existing slide IDs' numeric prefixes. Q IDs remain stable for the slide notes and later Live Evidence mappings.

| ID / section | Challenge | Short answer | Likely follow-up and response | Code / evidence |
|---|---|---|---|---|
| Q01 / 01 | Is this actually anonymization? | It is policy-bounded pseudonymization. It does not establish formal anonymity or linkage resistance. | **Can you safely publish arbitrary customer exports?** No; discovery completeness and residual risk require a separate assessment. | [Policy][C01], [disclosures][D01] |
| Q02 / 01 | What happens to a name absent from the policy? | The exact engine makes no general detection promise. Optional discovery only proposes bounded name aliases. | **What about a name inside a paragraph?** Whole-line discovery can miss it; this is not a general entity detector. | [Discovery][C12] |
| Q03 / 01 | Why not use an existing PII platform? | The trial guarantee is narrow and auditable. The shipped matcher is local stdlib code; RapidFuzz is confined to optional proposals. | **Did the custom matcher increase risk?** Yes, it adds code we own; tests and shared-verifier limitations must be acknowledged. | [Matcher][C04], [submission][D01] |
| Q04 / 02 | Why isn't a successful transform enough? | Transformation can produce valid-looking but wrong output. Readiness follows a separate corpus verification step. | **Is that verifier truly independent?** It rereads and re-derives but shares matching primitives; not implementation-diverse. | [Pipeline][C02], [verification][C13] |
| Q05 / 02 | Are raw inputs protected just by Docker's read-only mount? | The mount is part of the assumption; preflight and source-digest checks also detect ordinary unsafe input and changes. | **Can a hostile host swap bytes and restore them?** That adversary is outside this local threat model. | [Preflight][C14], [pipeline][C02] |
| Q06 / 02 | Why create another skill? | The skill exposes the same project interface; the engine remains self-contained and does not depend on that skill at runtime. | **What prevents the wrong installed package being used?** The wrapper checks the imported package location; mismatch is a retained rejection case. | [Wrapper eval][E02], [interface][C15] |
| Q07 / 03 | Why do aliases share a pseudonym? | Their rules share a canonical type/identity key. The policy supplies identity authority. | **Does similar spelling prove identity?** No. Fuzzy similarity is a proposal, requiring explicit approval. | [Policy][C01], [allocator][C03] |
| Q08 / 03 | Can two identities collide? | Allocation detects per-type collisions and searches deterministically; bounded exhaustion rejects. | **Will adding identities preserve old values?** Not guaranteed when collision assignments change. Production needs a versioned shared plan. | [Allocator][C03] |
| Q09 / 03 | Is a SHA-256 pseudonym secret? | No. This namespace is public and inputs may be guessable. | **What would you replace?** A tenant/purpose-scoped keyed scheme with explicit rotation and collision-plan semantics; not a claim about shipped code. | [Digest][C03], [disclosures][D01] |
| Q10 / 03 | What if two literals overlap? | Selected spans are leftmost-longest with stable tie-breaking, taken from original input. | **Can emitted text trigger another replacement?** It is not rescanned; residual sensitive output still causes verification failure. | [Matcher][C04], [verifier][C13] |
| Q11 / 03 | What if a protected phrase contains a sensitive name? | The policy compiler rejects conflicting containment or boundary overlap rather than silently choosing a winner. | **Is that too conservative?** Deliberately; relaxing it would require a different explicit preservation contract. | [Overlap validation][C16] |
| Q12 / 03 | Why do you need strict type equality? | Python equality can equate Boolean/integer and integer/float values that carry different format semantics. | **What about two correct values swapped between rows?** Location-aware checks reconstruct expected values per row/cell, not just counts. | [Typed verifier][C05], [SQLite verifier][C17] |
| Q13 / 04 | Is report-last an atomic transaction? | No. It makes readiness the final step; corpus bytes may exist without an authorizing report. | **Can readers ignore the marker?** Then they violate the consumer protocol; the pipeline cannot make that usage safe. | [Publication][C06] |
| Q14 / 04 | What if the report write is short? | The write-all loop consumes the remaining bytes, rejects zero progress, then fsyncs and renames the marker. | **Does fsync prove every crash case?** No; no exhaustive storage/power-loss campaign is claimed. | [Publication][C06] |
| Q15 / 04 | How did the relative-path leak happen? | The guard resolved one path but checked lexical ancestors of another representation. | **Why isn't changing one loop sufficient?** Production writers must use the returned canonical destination, including the sibling approval receipt. | [Boundary][C07], [CLI][C15], [approval][C09] |
| Q16 / 04 | Why doesn't mode 0600 solve it? | Permissions restrict access; they do not keep raw-name work artifacts outside a READY corpus. | **Does exclusive creation help?** It prevents overwrites, not misplacement. Both guarantees are required. | [Private writer][C18], [regression][C08] |
| Q17 / 04 | Can a symlink change after validation? | The fix closes deterministic relative/symlink aliases under the trusted single-writer assumption. | **Would you claim race-proof path traversal?** No. Stronger hostile-filesystem protection is outside this proof. | [Boundary][C07], [disclosures][D01] |
| Q18 / 05 | How do you know the fix didn't disable every output? | The same regression checks successful ordinary private-directory flows and private modes. | **Did you test the wrapper too?** The retained wrapper eval and local targeted run exercise the project test through the wrapper. | [Regression][C08], [wrapper receipt][E02] |
| Q19 / 05 | Does a 95 similarity score mean 95% probability? | No. It is a string-similarity score, not calibrated identity confidence. | **What prevents ambiguous matches?** Identity-level tie and margin refusal, then explicit approval and policy compilation. | [Discovery][C12], [approval][C09] |
| Q20 / 05 | Can I edit the review to approve an invented alias? | Approval recomputes discovery and compares the complete supplied report before accepting explicit unique candidate IDs. | **What if source bytes changed?** The source-bound proposal comparison rejects stale review material. | [Approval][C09] |
| Q21 / 05 | Does human approval authorize release? | No. It creates a validated exact policy plus a private receipt; normal transformation and verification still own readiness. | **Could approval introduce a protected overlap?** The real policy compiler runs again and rejects that conflict. | [Approval][C09], [overlap][C16] |
| Q22 / 05 | Did WebGPT execute your Docker tests? | No. Its final PASS came from source and regression inspection; local qualification is separate execution evidence. | **Then what does PASS establish?** Closure of the demonstrated canonical-path blocker in bounded scope—not universal correctness. | [Evidence ledger](#evidence-ledger), [qualification][C10] |
| Q23 / 05 | Does a large green test count prove safety? | No. A useful test names an invariant, attacks it, and checks the resulting bytes and structure. | **What evidence would change your mind?** A concrete reproducer that violates a required invariant on the pinned version. | [Regression][C08], [verification][C13] |
| Q24 / 06 | Why can't you split every file at newline boundaries? | CSV records can contain newlines; UTF-8 and literal matches can cross byte boundaries; JSON/SQLite have their own structure. | **What is implemented now?** Local per-file processing. Format-aware distributed partitioning is a proposal. | [Adapters][C19], [design][D02] |
| Q25 / 06 | Where is the shared state for pseudonyms in production? | Every worker must receive the same versioned policy/identity plan. Local collision allocation must not run over inconsistent subsets. | **Does a common HMAC key fix that?** No; collision assignment and identity authority still need a shared versioned contract. | [Allocator][C03], [design][D02] |
| Q26 / 06 | What proves the 1 PB SLA and cost? | Nothing proves operational delivery yet. The model exposes throughput, pool size, retention, retries, and request-price assumptions. | **What would you measure first?** Representative throughput and skew, object counts, memory, verification cost, and quota ceilings. | [Cost model][C11], [design][D02] |
| Q27 / 06 | What happens when two cloud workers retry the same object? | Proposed production processing needs idempotent attempt outputs and manifest-based conditional publication. | **Is that implemented here?** No. Deterministic content helps replay but is not an exactly-once distributed commit protocol. | [Design][D02], [local publication][C06] |
| Q28 / 07 | Did you stay within eight hours? | I cannot substantiate that. The submission discloses post-timebox work and labels the eight-hour allocation a retrospective estimate. | **Why the overrun?** Additional corrections and extensions were made; technical PASS does not waive the timebox. | [Time disclosure][D01] |
| Q29 / 07 | How much did AI do, and can you explain the code? | The work was AI-assisted; the submission discloses that. Demonstrate understanding by tracing a concrete invariant and its failure test. | **What did review actually catch?** For example, the canonical-path artifact leak, whose exact mechanism and regression are shown here. | [Disclosure][D01], [boundary][C07], [regression][C08] |
| Q30 / 07 | What would you do next, and what would you refuse to claim? | Prioritize workload evidence, verifier diversity, and key/identity-plan management. Do not claim general anonymity or production readiness. | **Why not add more features now?** The submitted mechanism has a bounded contract; expansion needs a new goal and evidence. | [Unfinished work][D01] |

<a id="evidence-ledger"></a>
## Evidence ledger and proof boundaries

| ID | Evidence | What it supports | What it does not support |
|---|---|---|---|
| E01 | Presenter-local `QUALIFICATION.json`, schema `oai_trial.release_qualification.v1`, source commit `0375af56bf681e9441edcb7433cfe58951db77b2`, status `PASS` | Clean-clone checks, default Docker build/demo/mounted runs, independent output readback, refusal cases, offline replay, baseline history and ZIP-byte verification | Optional discovery Docker qualification, production execution, exhaustive faults, or eight-hour compliance |
| E02 | [Retained wrapper eval artifact][E02] | Recorded targeted regression execution through the skill wrapper, with per-trial output | A personally executed WebGPT check, all possible path races, or universal skill reliability |
| E03 | Presenter-local `path-regression.log` and `wrapper-regression.log` | Targeted post-fix regression passed through the project and wrapper; each recorded one collected test function | A test count is not the number of adversarial scenarios or proof of completeness |
| E04 | Human-supplied final WebGPT response: `VERDICT: PASS` at `0375af56bf681e9441edcb7433cfe58951db77b2` | The reviewer inspected the fixed source/regression and closed the specific release-path blocker | The reviewer explicitly did not run pytest, wrapper, Docker, or qualification |
| E05 | Submitted ZIP `oai-trial-0375af56.zip`; SHA-256 `afb851e90d37159007aa58c4beac453bef5963e80264db28d18775638535a715` | Identity of the qualified archive; unchanged submitted artifact can be distinguished from later presentation commits | A hash alone says nothing about correctness or privacy |

Presenter-local receipts are not public repository files. Keep the qualification receipt next to the submitted ZIP for the interview. Do not invent a downloadable repository link for it or substitute an older pitch receipt.

## Live Evidence handoff — prepared mapping, not an active integration

**Status: preparation only.** No audio capture, Memory import, briefing-pack load, or live card delivery is claimed by this document.

For each later oracle record, preserve this relationship:

```text
question ID + paraphrases + follow-up
          ↓
short answer + explicit limitation
          ↓
walkthrough section ID = deck slide ID
          ↓
file + symbol + pinned commit + evidence ID
```

Example: `Q15` maps to section/slide `04-reliability`, `bundle.py::separate_output`, the production CLI caller, `discovery.py::approve`, and the boundary regression. A question about permissions instead maps to `Q16` and `write_private`, not just the same generic “security” answer.

The actual `live_evidence.prep_pack.v1` and briefing-pack artifacts are a later task, validated through the owning skill. These Markdown IDs are not a claim of schema conformance or successful retrieval. If a source changes, its old claim must be rechecked before publishing a card.

Use rehearsal for coaching and practice Q&A. During a formal assessment, honor the skill's frozen session policy: no candidate-answer generation or briefing prompts. Recording consent and any permission for interview assistance must be explicit; AI use during the coding trial is not itself evidence of permission during the recorded interview.

## Optional Q&A code stops — outside the 30-minute core

1. **Identity/collision allocation:** trace one alias pair and one collision through [policy compilation][C01] and [allocation][C03]. Explain the same-policy condition.
2. **Typed mutation:** show a Boolean-to-number or row-value-swap regression and [the location verifier][C05]. Do not treat preserved counts as preserved meaning.
3. **Release artifact bypass:** walk `release_bytes()` before and after one denied operation in [the real regression][C08], then the successful private-directory control.
4. **Publication interruption:** identify the marker removal, sealed-digest check, corpus rename, full report write, and final marker rename in [`_publish`][C06]. State what readers may see between them.

These are code-navigation stops, not promises of a running debugger. Rehearse any debugger commands separately and retain a recorded fallback. Do not use a debugger during a formal-assessment session where that capability is disabled.

## Source links — fixed to the submitted implementation

[C01]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L129-L253
[C02]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L214-L281
[C03]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pseudonyms.py#L29-L104
[C04]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/matcher.py#L112-L145
[C05]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L129-L184
[C06]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L166-L211
[C07]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/bundle.py#L22-L37
[C08]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/tests/test_discovery_boundaries.py#L180-L244
[C09]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L329-L378
[C10]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/qualify_submission.py#L137-L314
[C11]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/estimate_aws_cost.py
[C12]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L222-L309
[C13]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L205-L249
[C14]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L80-L116
[C15]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/__main__.py#L207-L233
[C16]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L100-L126
[C17]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L64-L126
[C18]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L312-L326
[C19]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/formats.py
[D00]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/TRIAL_BRIEF.md
[D01]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/SUBMISSION.md
[D02]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/docs/production-architecture.md
[E02]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/artifacts/release-artifact-path-evals.json
