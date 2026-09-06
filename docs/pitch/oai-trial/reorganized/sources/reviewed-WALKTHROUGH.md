# OAI trial — technical walkthrough and adversarial Q&A

> **Prepared walkthrough:** 30 minutes, including code navigation.<br>
> **Separate discussion:** 15 minutes or more. The appendix supports questions; it is not additional prepared presentation time.
>
> **Frozen implementation:** [`0375af56bf681e9441edcb7433cfe58951db77b2`][BASELINE].
>
> This is a post-submission presentation document. It does not modify the submitted runtime or archive, regenerate presentation exports, or extend an earlier qualification result to a different version.

## How to use this document

The **Say** passages are conversational speaker notes. They explain the implementation and its tradeoffs without claiming an undocumented personal decision history. The **Show** cues identify short code jumps; do not read entire files aloud.

The original seven slide IDs and Q01–Q30 remain stable. Q31–Q48 add deeper follow-ups. All repository links point to the frozen commit. Source links name the relevant symbols rather than relying on obsolete line ranges.

### Timing

| Section / existing slide ID | Prepared time | Main point | Primary code jump |
|---|---:|---|---|
| [01-brief](#01-brief) | 00:00–03:00 | The policy defines the transformation obligation, not a general anonymity guarantee. | `policy.py::compile_policy` |
| [02-architecture](#02-architecture) | 03:00–07:00 | Producing transformed files and authorizing their release are separate steps. | `pipeline.py::run_pipeline` |
| [03-semantics](#03-semantics) | 07:00–13:00 | Identity authority, deterministic spans, and typed/location checks preserve meaning. | `Rule.identity`, `Matcher.replace`, `_typed_equal` |
| [04-reliability](#04-reliability) | 13:00–18:00 | Readiness is a protocol; private work artifacts must stay outside it. | `_publish`, `separate_output` |
| [05-evidence](#05-evidence) | 18:00–23:00 | Concrete regressions support the boundary; proposals and approvals have different authority. | Path regression, `approve`, qualification `readback` |
| [06-production](#06-production) | 23:00–27:00 | Distributed execution needs a shared identity plan and one corpus-level publication decision. | AWS design, `_one`, committed cost inputs |
| [07-nonclaims](#07-nonclaims) | 27:00–30:00 | Technical readiness, privacy guarantees, and timebox compliance are separate claims. | `SUBMISSION.md` |
| [Q&A appendix](#adversarial-question-bank) | 30:00–45:00+ | Follow the interviewer’s question to the relevant code and evidence. | Q01–Q48 |

**Interruption policy:** Answer brief clarifications immediately. For deeper questions, either move to the appendix or shorten the next code inspection; do not quietly extend the prepared talk. Preserve the final limitations and timebox disclosure. Do not build images, install dependencies, or troubleshoot presentation tools during the walkthrough.

### Evidence vocabulary

| Label | Meaning |
|---|---|
| **SOURCE-INSPECTED** | The pinned code, test, or document was read. This is not an execution result. |
| **RETAINED EXECUTION** | A committed result artifact was inspected. Its recorded execution remains attributable to the environment that produced it. |
| **REPORTED LOCAL EXECUTION** | The presenter reports an execution result, but the underlying local receipt/log/archive was not independently inspected for this rewrite. |
| **REVIEWER EVIDENCE** | The bounded review response in this conversation. The reviewer’s source inspection must not be described as personally running pytest or Docker. |
| **DESIGN / INFERENCE** | A proposed production mechanism, engineering interpretation, or anticipated question—not shipped behavior or measured performance. |

The [evidence ledger](#evidence-ledger) records these distinctions for E01–E08.

<a id="01-brief"></a>
## 01 — Define the promise before choosing the mechanism

**Slide ID:** `01-brief`<br>
**Time:** 00:00–03:00<br>
**Question handles:** Q01–Q03

### Say

“The assignment describes anonymizing customer exports across CSV, JSON, UTF-8 text, and SQLite. The guarantee this implementation can defend is narrower: policy-bounded, deterministic pseudonymization, with preservation checks before the output is marked ready.

“The policy tells the engine which literal values are sensitive, which aliases belong to a declared identity, and which values must remain protected. That makes the transformation obligation explicit. It does not prove that the policy contains every sensitive fact in the dataset.

“That distinction matters. A transformation can be correct against its policy while the remaining data still supports identification through context or external linkage. I would not describe a successful run as proof that arbitrary customer exports are anonymous.

“The engineering problem is therefore not just finding and replacing a name. The same declared identity must remain coherent across formats. Unrelated values must keep their meaning. The output must remain usable. And a failure must not be mistaken for a newly authorized release.

“The implementation handles contradictions conservatively. For example, if the policy requires replacing a literal that overlaps protected content, it rejects the policy rather than silently choosing which promise to break.

“I’ll explain the exact engine first. The file/folder interface and reviewed name-alias discovery are later, operator-requested additions, and I’ll identify that boundary when we reach them.”

### Show

Open [`policy.py::compile_policy`][C01] and the [synthetic example policy][D03].

Point to `version`, `sensitive_values`, `protected_values`, and `subject_id`. Explain that `match` defaults to `"literal"` and `case_sensitive` defaults to `True`. The compiler validates these choices; it does not determine whether the policy author’s identity assignments are true.

**Engineering tradeoff:** A declared policy makes transformation behavior auditable. A discovery platform could widen coverage, but would introduce additional detection and adjudication questions; those are not solved by selecting a different replacement algorithm. The [brief][D00] permits dependencies and optional discovery—the small default dependency set is an implementation choice.

**Transition:** “With that promise defined, let’s follow one run and identify the point at which output becomes a release.”

<a id="02-architecture"></a>
## 02 — Follow one input to a release

**Slide ID:** `02-architecture`<br>
**Time:** 03:00–07:00<br>
**Question handles:** Q04–Q06

### Say

“The evaluator-facing interface stays small. A bare Docker run executes the synthetic demonstration. A mounted run reads `policy.json` and `corpus/`, then writes the releasable `corpus/` and `report.json`. The image remains the interface; the evaluator does not need the shared skill.

“Inside `run_pipeline`, the policy path is checked before loading. Preflight rejects unsafe corpus entries, overlapping input/output roots, unsupported file types, and sensitive literals in paths. The pipeline inventories the files and hashes their contents before processing.

“Each adapter understands a logical format. CSV is parsed into cells. JSON string values are transformed without renaming keys. SQLite is snapshotted and updated through its database interface. UTF-8 text is decoded and matched as text. This is not a substitution over arbitrary database bytes.

“The adapters write into a private staging directory on the output filesystem. Only after all files have been transformed does the verifier reread source and output. The pipeline then checks the source digests again, computes an output manifest digest, and calls publication.

“There are two important limits to that description. First, the verifier does not return a signed or independently sealed receipt; the pipeline computes the digest after verification. That interval assumes trusted single-writer staging. Second, the local processing model materializes files and verification structures in memory. It is not the distributed petabyte engine.

“The later `anonymize` command accepts a file or folder plus a separate policy. It validates the original paths, copies them into a private temporary bundle, and delegates to this same pipeline. That adapter makes the interface more convenient without creating a second transformation engine.”

### Show

Open [`pipeline.py::run_pipeline`][C02]. Follow the calls, not every branch:

```text
validated policy + source inventory
                 ↓
create private staging directory
                 ↓
format adapters write staged corpus
                 ↓
reread source/output and verify
                 ↓
source-digest comparison + pipeline-computed output seal
                 ↓
publish corpus → write report.json last
```

For the extension, point briefly to [`bundle.py::input_bundle`][C25] and its caller in [`__main__.py::main`][C15].

**Engineering tradeoff:** Same-filesystem staging supports a rename-based publication step, but staging is still inside a filesystem trust boundary. Mode `0700` restricts access; it is not encryption, a hostile-host defense, or permission for consumers to read unfinished output.

**Transition:** “That verifier needs an unambiguous expected result. Identity and matching semantics supply it.”

<a id="03-semantics"></a>
## 03 — Keep identity, matching, and meaning distinct

**Slide ID:** `03-semantics`<br>
**Time:** 07:00–13:00<br>
**Question handles:** Q07–Q12<br>
**Appendix depth:** Q31–Q33, Q38–Q41

### Say: the policy supplies identity authority

“The canonical identity is the pair of data type and subject ID. When `subject_id` is absent, the rule ID is the fallback. Two name aliases with the same canonical identity converge. A name and an email for the same subject have different type-specific replacements; they do not need a common visible token.

“The engine is enforcing declared identity, not discovering personhood. Two similar names are not necessarily one person, and two people can share the same spelling. If different identities claim the same match domain, the policy compiler rejects that ambiguity. It cannot resolve it from surrounding business context.

“Pseudonyms are allocated over the sorted set of canonical identities. A repeated run with the same inputs produces the same allocation. Different identities within a type are checked for distinct replacements; bounded-domain exhaustion rejects rather than merging them.”

**Show — exact excerpt from [`pseudonyms.py::_digest`][C03]:**

```python
def _digest(policy_version: int, data_type: str, identity: str, salt: int) -> str:
    material = f"{ALGORITHM_VERSION}:{SCOPE_ID}:{policy_version}:{data_type}:{identity}:{salt}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
```

“Notice what is—and is not—in this input. `policy_version` is the supported schema version, currently one. It is not a revision counter that changes whenever someone edits a policy. The full policy hash is recorded separately for provenance; it is not the pseudonym seed.

“An alias-only addition that preserves the canonical identity set does not create a new allocation problem. Adding distinct identities can affect collision assignments. I would not promise stability through arbitrary policy growth, or across partitions that independently allocate over different identity subsets.

“Also, this is a public, unkeyed namespace. The salt resolves allocation collisions; it is not a secret. Determinism is not confidentiality.”

### Say: overlap is resolved before emission

“The matcher finds spans in the original decoded input. At a shared starting point, the longer match wins. Across overlapping spans, the earlier start wins; rule ID provides a stable tie-break.

“That is more precise than saying ‘always take the longest name.’ A longer span beginning later does not displace an already selected earlier span.

“Emission happens once over the selected spans. It does not repeatedly rewrite its own output.”

**Show — exact method from [`matcher.py::Matcher.replace`][C04]:**

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

“The slices come from `text`, not from a progressively edited string. That is the no-cascade mechanism.

“Protected overlap is a different question. `_check_overlap` conservatively rejects equality, containment, and suffix/prefix intersections at policy compilation. It does not wait to guess precedence at an actual protected occurrence.

“No cascade is not a promise that every policy will successfully publish. If a generated replacement contains a policy-sensitive literal, the residual-output check can reject the result. Refusal is preferable to silently changing the declared rule.”

### Say: disappearance is not enough

“Suppose Alice and Bob receive distinct pseudonyms, but those pseudonyms are swapped between rows. Original names disappear, counts stay correct, and the output still parses. The records nevertheless describe the wrong people.

“The verifier therefore compares expected values at locations: ordered CSV cells, JSON nodes and array positions, text content, and SQLite rows. It also checks types.”

**Show — exact body excerpt from [`verification.py::_typed_equal`][C05]:**

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

“Python considers `True == 1` and `1 == 1.0`, but those are not interchangeable under this preservation contract. For SQLite, the checker compares logical schema objects, column and foreign-key metadata, row identity, and typed cell values. That is not byte-for-byte preservation of the database’s physical pages.

“The remaining qualification is important: location reconstruction shares `replace_text` and `build_replacements` with the transformer. Fresh reads and mutation tests add evidence, but a correlated defect in those primitives remains possible. This is independent reread and re-derivation, not a separately implemented reference engine.”

**Transition:** “Correct content is necessary. Now let’s distinguish correct staged content from permission to consume a release.”

<a id="04-reliability"></a>
## 04 — Make readiness explicit, and keep private work outside it

**Slide ID:** `04-reliability`<br>
**Time:** 13:00–18:00<br>
**Question handles:** Q13–Q17<br>
**Appendix depth:** Q37, Q44

### Say: report-last is a publication protocol

“The report is the last publication step. At the start of `_publish`, an existing readiness marker is removed before the corpus is changed. The staged digest is checked again, the staged corpus is renamed into place, and the new report is written through a temporary file and renamed last.

“That is not an atomic transaction over every file and every failure state. A failed publication can leave corpus bytes without an authorizing report. A consumer must not treat a directory’s existence as readiness.

“The implementation also handles ordinary short writes. One successful call to `os.write` does not necessarily mean that the whole buffer was written.”

**Show — exact excerpt from [`pipeline.py::_publish`][C06]:**

```python
        remaining = memoryview(data)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("report write made no progress")
            remaining = remaining[written:]
        os.fsync(fd)
```

“Only after the complete report is written and synced does the marker rename occur. This is a concrete mechanism, not a claim that every storage failure has been tested.

“Two qualifications prevent misleading shorthand. A failed rerun during preflight can leave an earlier valid release untouched. Once publication begins, that is not a rollback guarantee. And the seal is computed by the pipeline after verification, under the stated single-writer assumption—not returned as an independent verifier attestation.”

### Say: the corrected private-artifact boundary

“The later discovery extension introduced a different release risk. Reviews contain raw candidate names, and approved policies contain raw literals. Those files belong in private work storage, not inside an existing release.

“The reviewer demonstrated that the validator resolved the destination for one check but examined its lexical parents for another. From `release/corpus`, a relative `review.json` did not lead the lexical check up to `release`. A symlink alias could create the same mismatch.

“The fix makes path validation and writing agree on the destination.”

**Show — exact function from [`bundle.py::separate_output`][C07]:**

```python
def separate_output(output: Path, *inputs: Path) -> Path:
    if output.is_symlink() and not output.is_dir():
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "output artifact is a symlink")
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

“The key is not only `out.parents`. The function returns the validated path. The CLI assigns that result to `args.output`, and approval separately validates its policy destination and its derived receipt destination before either write.

“The existing-release check is deliberately conservative: an ancestor containing `report.json` and `corpus/` is treated as a release boundary. This guard does not need to trust a claimed status inside the report.

“`write_private` then exclusively creates the file with mode `0600`. Those properties prevent ordinary overwrite and restrict access. They do not replace path validation. The writer assumes the production caller has supplied a validated destination.

“This closes the demonstrated relative and symlink aliases under the existing filesystem assumptions. It does not claim race-proof traversal against a hostile process changing the filesystem after validation.”

### Navigation cue

Stay in the three-function chain:

`separate_output` → [`__main__.py::main`][C15] → [`discovery.py::approve`][C09].

Do not turn this into a tour of unrelated filesystem defenses.

**Transition:** “The test should demonstrate both refusal of the bad destinations and continued usability of the good ones.”

<a id="05-evidence"></a>
## 05 — Show the failure oracle, then separate proposal from authority

**Slide ID:** `05-evidence`<br>
**Time:** 18:00–23:00<br>
**Question handles:** Q18–Q23<br>
**Appendix depth:** Q34–Q36, Q45–Q46

### Say: what the regression actually checks

“The retained path regression first creates a real READY release. It records a mapping of every release file path to its bytes. That means its comparison covers file inventory, corpus content, and the readiness report—not merely the return code.

“It then attempts discovery and approval through relative and symlinked destinations, including a receipt-only symlink into the release. Rejection must leave the recorded release unchanged.

“The positive controls are essential. Equivalent relative and symlinked paths in a normal private work directory must still allow discovery and approval, and the resulting review, policy, and receipt must have private permissions. Otherwise the test could appear successful because we disabled useful behavior.”

### Show

Open:

[`tests/test_discovery_boundaries.py::test_work_artifacts_cannot_enter_release_via_relative_or_symlink_paths`][C08].

Point to `release_bytes()`, one rejected destination, the receipt-only symlink, and one successful outside-directory control.

The exact rehearsal command is:

```bash
uv run --extra dev --extra discovery pytest -q \
  tests/test_discovery_boundaries.py::test_work_artifacts_cannot_enter_release_via_relative_or_symlink_paths
```

This is a navigation/rehearsal aid, not a promise to execute it during the presentation.

### Say: three different authorities

“Discovery, approval, and release are separate operations.

“Discovery compares whole structured string values or whole text lines against eligible policy names. It ranks distinct identities, not each alias as though it were a different person. Ties are refused, and close competitors must meet a configured separation margin. The defaults are threshold 90 and margin 5. Those are string-score parameters, not probabilities of identity.

“Discovery writes private proposals and leaves the original policy unchanged. Approval requires explicit candidate IDs, recomputes discovery against the current inputs and supplied settings, and checks that the review agrees with that computation.”

**Show — exact excerpt from [`discovery.py::approve`][C09]:**

```python
    fresh = discover(bundle, supplied.threshold, supplied.margin)
    if asdict(fresh) != asdict(supplied):
        _reject(AnonErrorCode.DISCOVERY_STALE, "review differs from current inputs or settings")
    by_id = {c.id: c for c in fresh.candidates}
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(by_id):
        _reject(AnonErrorCode.DISCOVERY_REJECTED, "approve explicit, unique proposed candidate ids")
```

“Approval appends case-sensitive literal rules and runs the actual policy compiler before writing a new policy. Its receipt still says `release_ready: false`. Only a subsequent pipeline run transforms, verifies, and publishes a corpus.

“The `Alicee` example makes the boundary concrete. Without approval, the existing exact `Alice` rule can match its substring and leave a trailing `e`. Approval adds the longer exact literal `Alicee`, which can then become the same subject’s complete pseudonym. The extension has not changed default matching into fuzzy replacement.

“There is also an important scope change for the operator to understand: approval creates a literal policy rule, not a permission restricted to one observed row. The ordinary matcher applies that rule wherever its literal matches. Human review must consider that consequence.”

### Say: distinguish the evidence sources

“The qualification checker is another useful evidence layer: for its synthetic fixture, it calculates expected pseudonyms without importing the runtime, reads CSV/JSON/SQLite directly, and checks report schema and digests. That is stronger than accepting a success flag, but it remains a bounded fixture—not a second production verifier.

“My local qualification checks and targeted project/wrapper runs passed. The committed wrapper artifact records the targeted run. WebGPT’s final blocker closure was a source-and-regression review; it did not execute those commands. I keep those statements separate.”

Open [`qualify_submission.py::readback`][C10] only if the interviewer asks how the checker avoids self-certification. Evidence status is recorded under E01–E04 and E06.

**Transition:** “Now we can discuss scale without turning these local results into an unsupported petabyte benchmark.”

<a id="06-production"></a>
## 06 — Scale execution without changing the release decision

**Slide ID:** `06-production`<br>
**Time:** 23:00–27:00<br>
**Question handles:** Q24–Q27<br>
**Appendix depth:** Q47

**This section describes a proposed production system and a committed model—not deployed behavior.**

### Say

“The worked design uses AWS object storage for intake, staging, release, and quarantine, EventBridge and SQS for dispatch, and a bounded Fargate or Batch worker pool.

“The local release idea carries forward, but the mechanism changes. Workers can complete at different times. A coordinator must verify the expected corpus, write an immutable manifest of output keys and hashes, and switch an active-corpus pointer. Consumers resolve that pointer; they must not infer readiness by listing staged objects.

“That consumer protocol and the access boundaries are part of the design. An object is not magically invisible because we intend to publish a pointer later.

“Partitioning is format-specific. CSV needs parser-confirmed record boundaries because a quoted field can contain newlines. Text needs UTF-8-safe boundaries and a match-overlap ownership rule. The design processes ordinary JSON documents and SQLite snapshots whole; introducing a different framing would be a separate capability.

“Identity coherence also has to survive distribution. Every worker must use the same policy, canonical identity set, algorithm configuration, and collision allocation. A common HMAC key alone does not coordinate independently allocated subsets. A shared versioned replacement plan is the semantic requirement, not a feature implemented in the local worker code.

“The capacity calculation assumes 200 workers at 20 million bytes per second each: four billion bytes per second before verification, retries, and scheduling overhead. That is an assumption, not the measured throughput of this local implementation.

“The model is useful because the assumptions and arithmetic are inspectable. It is not useful if we present the totals as a production quote or the target SLA as an observed service level.”

### Show

Open the [AWS design][D02], [`estimate_aws_cost.py::_one`][C11], and the [committed inputs][D04].

| Scenario | Committed modeled cost | Modeled processing time at 200 workers | Design target |
|---|---:|---:|---|
| 1 TB, defined as \(10^{12}\) bytes | $85.73, approximately $86 | 0.14 hours | Verified publication within 1 hour |
| 1 PB, defined as \(10^{15}\) bytes | $85,733.90, approximately $85,734 | 141.67 hours | Verified publication within 7 days |

These figures are from the [committed example output][D05], not a new execution during this edit. The modeled processing time includes the estimator’s two-pass factor and retry fraction, not a measured distribution of queueing and straggler delays.

### Say: what drives those numbers

“The example assumes average files of one MiB, three stored copies for one month, first-tier list-price storage, and a raised worker quota. It includes request, compute, and per-service orchestration terms. It does not model every real operation or cost: output expansion, transfer charges, key rental, log retention, and tiered discounts are disclosed exclusions or assumptions.

“Storage dominates this scenario. But smaller files increase object-dependent charges substantially. The committed one-tenth-file-size sensitivity moves the petabyte estimate to roughly $223,750. That is a more useful conversation than defending a headline price without its workload shape.

“My first production validation would replace assumed throughput, object-size distribution, retry behavior, and quota capacity with representative measurements. There is no cloud deployment, local petabyte execution, or wired `ripgrep` cross-check to claim here.”

**Transition:** “The final slide separates what this evidence supports from what it does not.”

<a id="07-nonclaims"></a>
## 07 — State the boundary, including the timebox

**Slide ID:** `07-nonclaims`<br>
**Time:** 27:00–30:00<br>
**Question handles:** Q28–Q30<br>
**Appendix depth:** Q48

### Say

“The bounded follow-up review closed the canonical-path blocker at this submitted commit. That is a specific technical conclusion. It is not a claim of exhaustive security, guaranteed correctness, general anonymity, or approval of the presentation.

“The implementation still depends on an explicit policy. It does not discover all unlisted identifiers or establish resistance to external linkage. The pseudonym namespace is public. Verification shares replacement primitives. Local processing materializes files. Distributed execution, managed keys, and exhaustive crash qualification remain future work.

“The timebox deserves a direct answer rather than a footnote. The submission records post-timebox corrections and later operator-requested additions. Active engineering time was not separately tracked. The retrospective allocation totals eight hours, but it is an estimate, not proof that the instruction to stop after eight hours was satisfied. Technical PASS does not waive that distinction.

“The work was AI-assisted and externally reviewed. I am not claiming an undocumented split of human and AI authorship. The appropriate test of understanding is whether I can explain the behavior, navigate to the implementation, and identify the evidence and its limit.

“From here, I would not add features to make this presentation sound broader. A production follow-up would prioritize representative workload measurements, more independent checking, and explicit key and identity-plan lifecycle decisions. Those are new objectives, not capabilities hidden inside this submission.

“The result to evaluate is the bounded mechanism: declared identity authority, deterministic original-input matching, format-aware processing, verification before readiness, and a corrected separation between private review artifacts and released data.”

### Close

“Which boundary would be most useful to inspect now: identity mapping, verification, publication, or discovery approval?”

**Stop the prepared walkthrough here.** Everything below is reference material for the separate Q&A.

<a id="adversarial-question-bank"></a>
## Adversarial question bank — separate 15+ minute appendix

These are plausible interviewer questions derived from this implementation, not predictions of the interviewer’s script. Answer the short version first. Use the deeper answer only when asked.

Q01–Q30 preserve the original topics and identifiers. The **section/slide** column is the exact existing slide ID. The final column names the code symbol and evidence to open.

### Brief and architecture

| ID | Section / slide | Question | Short answer | Skeptical follow-up and deeper answer | Code / evidence |
|---|---|---|---|---|---|
| Q01 | `01-brief` | Is this actually anonymization? | It is deterministic, policy-bounded pseudonymization with preservation and release checks. | **“Then why is publication safe?”** The technical release decision is relative to the declared policy and supported formats. It does not replace an assessment of policy completeness or residual privacy risk. | [`compile_policy`][C01]; [scope disclosures][D01] |
| Q02 | `01-brief` | What happens to a name absent from the policy? | There is no general discovery promise. An existing literal may still match a substring. | **“Will discovery find a name in a paragraph?”** It compares the whole line, not extracted name spans. Most narrative lines will not qualify as name-shaped candidates; no general entity detector is implemented. | [`Matcher.replace`][C04]; [`_strings`, `_name`, `discover`][C12] |
| Q03 | `01-brief` | Why not use an existing PII platform? | This implementation makes a narrow transformation contract easy to inspect; that is a tradeoff, not proof that custom code is superior. | **“Did stdlib-only increase your risk?”** It leaves ownership of the matcher here and requires strong tests. The brief permits packaged dependencies. I am not claiming a comparative platform evaluation that was not performed. | [Brief][D00]; [`Matcher`, `_Aho`][C04]; [implementation choices][D01] |
| Q04 | `02-architecture` | Why isn’t a successful transform enough? | Parsing and transformation can succeed while values or associations are wrong. Verification precedes publication. | **“Is the verifier independent?”** It rereads and reconstructs, but shares matcher and pseudonym primitives. It can catch injected output faults without eliminating common-mode implementation errors. | [`run_pipeline`][C02]; [`verify_corpus`][C13] |
| Q05 | `02-architecture` | Are inputs protected only by Docker’s read-only mount? | That mount is one assumption. Preflight checks paths, and the pipeline compares source digests before publication. | **“Can a hostile host swap bytes and restore them?”** That is outside the local threat model. The post-trial interface also checks copies against originals, but neither mechanism is a hostile-host immutable snapshot service. | [`_preflight`][C14]; [`run_pipeline`][C02]; [`input_bundle`][C25] |
| Q06 | `02-architecture` | Why create another skill? | It exposes the project CLI; it is not another matching or verification engine. | **“What prevents a wrong installation?”** The wrapper workflow includes package-location checking and a retained wrong-install control. That evidence is separate from the default Docker interface, which does not require the skill. | [Interface documentation][D06]; [`main`][C15]; [retained wrapper evidence][E02] |

### Identity, overlap, and verification

| ID | Section / slide | Question | Short answer | Skeptical follow-up and deeper answer | Code / evidence |
|---|---|---|---|---|---|
| Q07 | `03-semantics` | Why do aliases share a pseudonym? | They share the policy’s canonical type/identity key. | **“What makes that identity assignment true?”** The policy author or approving operator supplies that authority. The compiler enforces consistency, not real-world identity truth. Similarity alone is insufficient. | [`Rule.identity`, `compile_policy`][C01]; [`build_replacements`][C03] |
| Q08 | `03-semantics` | Can two identities collide? | Candidate replacements can collide; allocation checks per-type distinctness and searches again or rejects. | **“Will adding identities preserve existing values?”** Not unconditionally. Sorted allocation can assign a different salt when the identity set changes. Stable retries require the same plan; evolving policies need explicit lifecycle decisions. | [`build_replacements`][C03] |
| Q09 | `03-semantics` | Is the SHA-256 pseudonym secret? | No. The namespace is public and derivation inputs may be guessable. | **“What would a key change?”** A keyed construction changes an attacker’s ability to recompute guesses without the key. It does not remove contextual linkage, prove anonymity, or coordinate collision allocation by itself. | [`_digest`, `KEY_MODE`][C03]; [privacy posture][D01] |
| Q10 | `03-semantics` | What happens when literals overlap? | Selection is earliest start, longest at that start, then stable rule ID. Emission uses original-input spans. | **“Can replacement text trigger another rule?”** Not during emission. The residual verifier can still refuse generated text containing a sensitive literal. No-cascade semantics and successful publishability are different conditions. | [`_select`, `Matcher.replace`][C04]; [`verify_corpus`][C13] |
| Q11 | `03-semantics` | What if a protected phrase contains a sensitive name? | The policy is rejected rather than silently weakening either obligation. | **“Even when those strings never meet in this corpus?”** Yes, the compile-time overlap test is conservative. A context-sensitive exception would require a different explicit contract, not a hidden precedence rule. | [`_boundary_overlap`, `_check_overlap`][C16] |
| Q12 | `03-semantics` | Why require strict type equality? | Ordinary Python equality can equate Boolean/integer and integer/float values. | **“What about correct values on the wrong rows?”** Type checks alone do not catch that. Location reconstruction checks the expected value at the corresponding cell or row. The typed regression covers both JSON and SQLite type mutations. | [`_typed_equal`][C05]; [`_verify_sqlite_locations`][C17]; [typed regression][C20] |

### Publication and canonical paths

| ID | Section / slide | Question | Short answer | Skeptical follow-up and deeper answer | Code / evidence |
|---|---|---|---|---|---|
| Q13 | `04-reliability` | Is report-last an atomic transaction? | No. Individual rename operations are atomic; the whole workflow is a readiness protocol. | **“What can a failed run leave?”** Uncommitted corpus bytes or temporary artifacts can remain after some failures. A preflight failure on a rerun can preserve a prior release. Do not promise empty output or rollback in every failure state. | [`_publish`, `run_pipeline`][C06] |
| Q14 | `04-reliability` | What if writing the report makes partial progress? | The loop advances by the returned byte count and refuses zero progress before marker publication. | **“Does fsync prove every crash case?”** No. The code uses file and directory sync operations, but this review does not establish every filesystem, storage-device, or power-loss outcome. | [`_publish`][C06] |
| Q15 | `04-reliability` | How did the relative-path leak happen? | Validation and writing used inconsistent representations of the same destination. | **“Why not just change `output.parents`?”** The resolved result must also reach the writer. The CLI replaces `args.output`; approval canonicalizes both its policy path and derived receipt path before writing either. | [`separate_output`][C07]; [`main`][C15]; [`approve`][C09] |
| Q16 | `04-reliability` | Why doesn’t mode `0600` solve the leak? | It restricts permissions, not placement. A raw-name artifact still does not belong inside a release. | **“And exclusive creation?”** `O_EXCL` prevents replacing an existing file; it does not prevent adding a new inappropriate file. Both location validation and private exclusive creation are needed. | [`write_private`][C18]; [path regression][C08] |
| Q17 | `04-reliability` | Can a symlink change after validation? | The closed blocker concerns deterministic aliases under the stated filesystem assumptions. | **“Is traversal race-proof?”** No such claim is made. Canonicalization is not an immutable filesystem capability. A hostile concurrent writer is outside this bounded fix. | [`separate_output`][C07]; [assurance boundary][D01] |

### Evidence and approval

| ID | Section / slide | Question | Short answer | Skeptical follow-up and deeper answer | Code / evidence |
|---|---|---|---|---|---|
| Q18 | `05-evidence` | How do you know the fix didn’t disable all output? | The regression requires successful equivalent private-directory flows as positive controls. | **“What survives a denied operation?”** It compares the full file-path-to-bytes snapshot, including `report.json`, and checks that no requested policy or receipt appeared. It also checks `0600` on successful artifacts. | [Path regression][C08]; E06; [wrapper result][E02] |
| Q19 | `05-evidence` | Does a similarity score of 95 mean 95% probability? | No. It is a string-comparison score, not calibrated identity confidence. | **“What prevents two close people being merged?”** Candidates are ranked by distinct identity, ties and insufficient margins are refused, and explicit operator approval is required. Those mechanisms still do not prove the approved personhood judgment is correct. | [`discover`][C12]; [`approve`][C09] |
| Q20 | `05-evidence` | Can I edit the review to approve an invented alias? | Inconsistent candidate edits or stale source bindings are rejected by fresh recomputation and report comparison. | **“Does that make the report authentic?”** No. A self-consistent report is not a signature or authenticated human approval. The trusted operator owns the invocation; see Q35 for the settings boundary. | [`DiscoveryReport.validate`, `approve`][C09]; [workflow contract][D06] |
| Q21 | `05-evidence` | Does human approval authorize release? | It creates a compiled exact policy and a private receipt, not a released corpus. | **“Could it introduce a protected overlap?”** The real compiler is invoked after adding the selected rules and before writing. A conflict rejects. A subsequent pipeline run still has to transform and verify before readiness. | [`approve`][C09]; [`_check_overlap`][C16]; [`run_pipeline`][C02] |
| Q22 | `05-evidence` | Did WebGPT execute your Docker tests? | No. Its bounded follow-up PASS came from source, regression, and retained-evidence inspection. | **“Then who verified execution?”** The presenter reports local qualification. The local receipt must identify the source commit and artifacts; this rewrite does not turn that report into an execution personally performed by the editor. | [`qualify`, `readback`][C10]; E01–E04 |
| Q23 | `05-evidence` | Does a large green test count prove safety? | No. The useful unit is an invariant, a concrete challenge, an oracle, and its boundary. | **“What would falsify your claim?”** A reproducer that violates the required contract at this commit, or evidence that a claimed check did not run or does not check the claimed property. Positive controls prevent rejection-only tests from misleading us. | [Path regression][C08]; [typed regression][C20]; [`verify_corpus`][C13] |

### Production and disclosure

| ID | Section / slide | Question | Short answer | Skeptical follow-up and deeper answer | Code / evidence |
|---|---|---|---|---|---|
| Q24 | `06-production` | Why not split every file at newlines? | Newlines are not universal logical record boundaries. | **“What is implemented today?”** Per-file local adapters. Parser-aware CSV splitting, UTF-8/match overlap ownership, and distributed scheduling belong to the proposed production design. JSONL framing is not a new supported local suffix in this baseline. | [`transform_file` and adapters][C19]; [AWS design][D02] |
| Q25 | `06-production` | Where is the shared pseudonym state in production? | Workers must receive the same versioned policy, identity set, and replacement-allocation plan. | **“Does using one HMAC key suffice?”** No. Different identity subsets can cause different collision assignments. The local allocator demonstrates semantics; shared distributed plan management is a production design obligation. | [`build_replacements`][C03]; [AWS design][D02] |
| Q26 | `06-production` | What proves the petabyte SLA and price? | Nothing proves operational delivery yet. The repository contains a scenario model and design targets. | **“What would you measure first?”** Representative transform/verify throughput, memory, object-size skew, request volume, retry rates, and attainable concurrency. The model’s compute factor is an assumption, not a benchmark-derived law. | [`_one`, `_sensitivity`][C11]; [inputs][D04]; [example output][D05] |
| Q27 | `06-production` | What if two workers retry the same object? | Deterministic content helps, but the proposed orchestrator still needs idempotent attempt handling and conditional publication. | **“Is this exactly-once processing?”** No. The design starts with at-least-once delivery. Duplicate work must not cause inconsistent manifests or premature pointer updates; no distributed commit implementation is claimed locally. | [AWS reliability/publication design][D02]; [`_publish`][C06] |
| Q28 | `07-nonclaims` | Did you stay within eight hours? | I cannot substantiate compliance; post-timebox work is explicitly disclosed. | **“But the retrospective estimate totals eight hours?”** It is an approximate allocation, not an instrumented log. It does not erase the recorded overrun or later requested extension. The evaluator decides how that affects the trial. | [`SUBMISSION.md` time disclosure][D01] |
| Q29 | `07-nonclaims` | How much did AI do, and do you understand the implementation? | AI coding assistance and browser-backed review are disclosed; no unsupported authorship percentage is claimed. | **“Show your understanding.”** Trace one actual failure: the old lexical parent check, the canonical return value, both approval outputs, and the regression’s unchanged-release assertion. Explain the limit rather than reciting a PASS label. | [AI disclosure][D01]; [`separate_output`][C07]; [regression][C08] |
| Q30 | `07-nonclaims` | What would you do next, and what would you refuse to claim? | Measure representative workloads, increase checking independence where warranted, and define production key/identity-plan lifecycle. | **“Why stop now?”** Those are separate objectives. The submission makes bounded claims and discloses unfinished work; technical PASS is not a reason to relabel future functionality as complete. | [Unfinished work and stopping rule][D01] |

### Additional implementation-specific follow-ups

| ID | Section / slide | Question | Short answer | Skeptical follow-up and deeper answer | Code / evidence |
|---|---|---|---|---|---|
| Q31 | `03-semantics` | Is `policy_version` a revision ID for each policy edit? | No. It is the schema version, currently fixed to one. | **“How are edits identified?”** The report records the policy file’s digest. Derivation uses schema version and canonical identities, not that full digest. Provenance binding and pseudonym allocation are separate mechanisms. | [`compile_policy`][C01]; [`_digest`][C03]; [`RunReport`, `run_pipeline`][C02] |
| Q32 | `03-semantics` | Can renaming a rule change its pseudonym? | Yes when the rule has no `subject_id`, because `rule_id` is then the identity fallback. | **“What if `subject_id` is explicit?”** Renaming the rule does not change that canonical identity. It can still affect rule metadata or tie-breaking; the guarantee should be stated in terms of actual identity and matching inputs. | [`Rule.identity`][C01]; [`_select`][C04] |
| Q33 | `03-semantics` | Can you distinguish two different people both called Alice? | Not from this literal alone. Contradictory identities over the same match domain are rejected. | **“Could the column or surrounding sentence resolve it?”** The current policy does not provide context-scoped matching. That requires a different authority and schema, not silently treating every matching name as one person. | [`compile_policy` match-domain validation][C01]; [`build_matcher`][C04] |
| Q34 | `05-evidence` | Does approving one proposed cell authorize only that cell? | No. It adds a case-sensitive literal rule to the policy. | **“Could it affect a longer value elsewhere?”** Yes. Discovery is whole-value, but the exact engine is substring-based across eligible strings. Approval must consider that broader effect. The subsequent compiler and verifier enforce the resulting policy; they do not infer the operator intended row-only scope. | [`approve`][C09]; [`Matcher.replace`][C04]; [four-format workflow test][C21] |
| Q35 | `05-evidence` | Does review recomputation prove who approved it or freeze the original thresholds? | No. It proves consistency with fresh discovery using the supplied valid settings. | **“Could someone create another coherent review?”** The review is not signed. Threshold and margin come from the supplied report and are validated and reused. This is a trusted-operator workflow, not an authentication or tamper-evident approval system. | [`DiscoveryReport.validate`, `approve`][C09]; [`discover`][C12] |
| Q36 | `05-evidence` | Does `seam_validation: PASS` mean the aliases are correct or the policy is released? | Neither. It is a producer-side structural/contract check. | **“Does runtime use JSON Schema here?”** The producers call their Python validation methods and approval calls `compile_policy`. The retained workflow test also validates artifact shapes with JSON Schema. That does not turn the validation stamp into identity truth or release permission. | [`Candidate.validate`, `DiscoveryReport.validate`, `ApprovalReceipt.validate`][C12]; [workflow test][C21] |
| Q37 | `04-reliability` | Is `verification_sha256` the hash of a separate verifier receipt? | No. The pipeline assigns it the same sealed corpus digest as `corpus_manifest_sha256`. | **“Is it proof against forgery?”** A digest binds bytes only when compared against a trusted reference. This report is not a signed attestation, and the seal is computed after verification under the declared staging assumption. | [`RunReport`, `run_pipeline`][C02]; [`_publish`][C06] |
| Q38 | `03-semantics` | What exactly is preserved: physical bytes or logical content? | The contract is format-aware; do not claim universal byte identity. | **“Give a concrete distinction.”** JSON formatting and CSV quoting can change while values remain equivalent. SQLite checks logical DDL, metadata, and typed values, not physical pages. The JSON comparator checks key sets, not key insertion order. | [Adapters][C19]; [`_typed_equal`, `_verify_locations`][C05]; [`_verify_sqlite_locations`][C17] |
| Q39 | `03-semantics` | Do you reject every generated SQLite column? | No. The writer excludes generated/hidden columns from updates; verification still reads resulting row values. | **“What happens if a generated value changes?”** The row oracle compares it against the expected contract and can reject. Do not describe this as full generated-column support, or falsely claim every generated-column schema is rejected before processing. | [`_writable_columns`, `_transform_sqlite`][C19]; [`_verify_sqlite_locations`][C17] |
| Q40 | `03-semantics` | Why accept `0.1` but reject some other JSON decimal tokens? | The adapter checks decimal numeric round-trip through the serialized float representation, not exact binary representation. | **“So `0.1` is not exactly representable in binary?”** That is not the test being made. `_finite_float` compares `Decimal(token)` with `Decimal(repr(value))`; it refuses tokens whose decimal numeric value would change, and refuses nonfinite results. Original numeric spelling is not preserved. | [`_finite_float`, `_transform_json`][C19] |
| Q41 | `03-semantics` | Do matching and residual scanning apply identical Unicode rules? | No. Matching is exact or ASCII-insensitive; residual counting/scanning uses `casefold()` for insensitive rules. | **“Is there an implemented homoglyph detector?”** No general homoglyph/NFKC detector is established by this code. The broader residual fold can conservatively refuse output; it does not expand the matcher’s authority to normalize or replace additional input. | [`ascii_lower`][C04]; [`_count`, `verify_corpus`][C13] |
| Q42 | `02-architecture` | Is the temporary input bundle encrypted or immutable? | No. It is a private filesystem snapshot with copy/readback checks under stated trust assumptions. | **“Why copy at all?”** It adapts a file/folder into the existing engine’s bundle interface and avoids writing to originals. It is not a replacement for immutable object versions or encrypted work storage in production. | [`input_bundle`][C25]; [assurance boundary][D01] |
| Q43 | `02-architecture` | Do `preflight`, `inspect`, and `verify` all prove the same thing? | No. Preflight checks admission conditions; inspect summarizes a report; verify checks source/output corpus content. | **“Can inspect authenticate a release?”** No. It reads selected report fields. The qualification checker separately validates report schema and recomputes digests. Do not use an inspection display as a substitute for those checks. | [`_preflight_cmd`, `_inspect_cmd`, `_verify_cmd`][C15]; [`readback`][C10] |
| Q44 | `04-reliability` | Should repeated runs produce identical reports? | No. Corpus determinism is distinct from run metadata. | **“What should replay compare?”** Compare the corpus and appropriate content digests. `run_id` includes a time input, and elapsed time varies. Comparing complete reports would conflate stable transformation with intentionally changing execution metadata. | [`run_pipeline`, `_manifest_digest`][C02]; [`qualify` replay comparison][C10] |
| Q45 | `05-evidence` | Does the qualification script accept an arbitrary frozen SHA? | Not as a `--ref` argument. It records the invoking checkout’s HEAD, clones `main`, and requires equality. | **“What happens after main advances?”** That historical invocation should fail the equality check rather than silently qualify another commit. For this presentation, inspect the recorded receipt and archive; do not casually rerun the script and call the result historical qualification. | [`qualify`][C10]; E01, E05 |
| Q46 | `05-evidence` | Does default Docker qualification establish optional discovery-image behavior? | No. The default build omits RapidFuzz; the optional build uses `INCLUDE_DISCOVERY=1`. | **“What evidence covers discovery?”** Project/wrapper workflow tests and their scoped artifacts. A default-image `run`/`demo` result does not prove the optional image was built or exercised. This rewrite makes no such extra execution claim. | [Dockerfile][C22]; [workflow test][C21]; E01–E03 |
| Q47 | `06-production` | Are all real AWS operations priced by the estimator? | No. It is an explicit but simplified scenario model. | **“What is simplified beyond disclosed exclusions?”** For example, orchestration budgets one SQS price unit, one EventBridge event, and one KMS request per object. That is not a traced accounting of send/receive/delete, retries, API payload units, or every encryption operation. Use it for assumptions discussion, not invoicing certainty. | [`_one`][C11]; [price/unit inputs][D04]; [cost disclosures][D01] |
| Q48 | `07-nonclaims` | Will Live Evidence or an AI copilot help answer during the assessment? | This document is preparation only; no active assistance or recording is claimed. | **“The coding trial allowed AI—does that carry over?”** Not automatically. Formal-assessment rules and explicit permission govern interview assistance; recording consent is separate. The preparation bank is not evidence that live use is authorized. | [Preparation-only handoff](#live-evidence-handoff); [evidence boundaries](#evidence-ledger) |

<a id="evidence-ledger"></a>
## Evidence ledger and proof boundaries

This ledger preserves the draft’s evidence identifiers while correcting their interpretation. A code link, a recorded result, and a reviewer conclusion are different artifacts.

| ID | Artifact / status | What it supports | What it does not establish |
|---|---|---|---|
| E01 | **REPORTED LOCAL EXECUTION:** presenter-local `QUALIFICATION.json`, reported schema `oai_trial.release_qualification.v1`, source commit `0375af56bf681e9441edcb7433cfe58951db77b2`, status `PASS`. Its checker source was inspected at [C10][C10]. | The presenter reports clean-clone default Docker qualification, independent synthetic output readback, negative cases, offline replay, baseline ancestry, and package-byte verification. | The local receipt was not supplied for independent readback in this rewrite. It does not establish optional discovery-image qualification, cloud execution, exhaustive faults, or timebox compliance. |
| E02 | **RETAINED EXECUTION:** [committed wrapper eval artifact][E02]. | The targeted path regression is recorded as passing through the wrapper, with three retained trial outputs and `WRAPPER_BOUNDARY_PASS`. | It is not a run personally executed by the editor. Its outer repository metadata identifies the wrapper environment, not a fresh qualification of every project artifact. Count or status labels are not universal semantic proof. |
| E03 | **REPORTED LOCAL EXECUTION:** presenter-local `path-regression.log` and `wrapper-regression.log`. | The presenter reports the targeted project and wrapper runs. | These logs were not supplied for independent readback in this rewrite. One collected test function contains multiple scenarios; it is not one attack or exhaustive coverage. |
| E04 | **REVIEWER EVIDENCE:** the prior bounded PASS in this conversation for `0375af56bf681e9441edcb7433cfe58951db77b2`. | The reviewer inspected the corrected source and retained regression and closed the demonstrated canonical-path blocker. | The reviewer explicitly did not run pytest, the wrapper, Docker, or clean-clone qualification in that review. It is not a new verdict on later commits. |
| E05 | **REPORTED ARCHIVE IDENTITY:** `oai-trial-0375af56.zip`, with the presenter-supplied SHA-256 below. | A reported fingerprint with which the presenter can identify the submitted archive. | The archive was not supplied or rehashed for this rewrite. The filename/hash alone proves neither correctness nor correspondence to an executed qualification. |
| E06 | **SOURCE-INSPECTED:** [path regression][C08], [typed-scalar regression][C20], and [four-format discovery workflow test][C21]. | The named test inputs, operations, assertions, and positive controls were read. | Reading an assertion does not mean the test was executed here, or that it covers all variations of its failure family. |
| E07 | **SOURCE-INSPECTED MODEL:** [estimator][C11], [inputs][D04], and [committed output][D05]. | The scenario’s arithmetic, prices as recorded in the repository, assumptions, and sensitivity outputs can be inspected. | No new estimator run, current AWS price verification, billing quotation, or cloud throughput measurement was performed for this rewrite. |
| E08 | **SOURCE-INSPECTED:** the implementation and documents in the source register below. | The walkthrough’s code descriptions and exact excerpts are grounded in the frozen baseline. | This editorial pass is not another implementation-hardening round, execution qualification, or presentation-render approval. |

**E05 — reported archive SHA-256:**

```text
afb851e90d37159007aa58c4beac453bef5963e80264db28d18775638535a715
```

Presenter-local artifacts are not repository files. Keep their status explicit and do not invent GitHub links for them.

The pinned `SUBMISSION.md` says the canonical-path follow-up review was still pending when that commit was written. E04 is the subsequent review in this conversation. This walkthrough may describe that later event without pretending the frozen submission document already contained it.

<a id="live-evidence-handoff"></a>
## Live Evidence handoff — preparation only

**No active integration is claimed.** This document does not establish Memory import, briefing-pack loading, schema validation, question-detection performance, audio capture, recording, or live assistance.

For later authorized preparation tooling, preserve:

```text
question ID + paraphrases + follow-up
                 ↓
short answer + deeper answer + explicit boundary
                 ↓
section ID = existing slide ID
                 ↓
repository + pinned commit + file + symbol
                 ↓
evidence IDs + evidence status
```

For example:

| Mapping field | Q15 value |
|---|---|
| Question | How did the relative-path leak happen? |
| Section ID | `04-reliability` |
| Slide ID | `04-reliability` |
| Implementation baseline | `0375af56bf681e9441edcb7433cfe58951db77b2` |
| Code | `bundle.py::separate_output`; `__main__.py::main`; `discovery.py::approve` |
| Evidence | E02, E04, E06 |
| Limitation | Deterministic path aliases under the stated trust assumptions; not hostile concurrent filesystem mutation |
| Integration state | Preparation only |

Q16 instead emphasizes `write_private` and the distinction between permissions and placement. Q37 concerns report evidence binding, not the same generic “security” answer.

These mappings are editorial preparation data, not an assertion of compatibility with an uninspected Live Evidence schema. Any later import must be validated by its owning workflow. Changed source requires answer revalidation, not silent reuse of an obsolete claim.

**Formal-assessment boundary:** Use the bank for rehearsal and permitted preparation. Do not generate candidate answers or briefing prompts during an assessment where assistance is prohibited or not expressly authorized. Obtain explicit recording consent separately. Permission to use AI coding tools for the trial does not itself authorize live interview assistance.

## Optional appendix code stops and later captures

These stops are outside the prepared 30 minutes and selected by the interviewer’s question.

| Stop | Navigate to | What to explain | Evidence status |
|---|---|---|---|
| Identity and policy edits | `Rule.identity` → `build_replacements` → `_digest` | Alias convergence, fallback identity, schema version, and collision-plan dependence. | Source inspected; no new collision experiment claimed. |
| Typed/location mutation | Typed regression → `_typed_equal` → `_verify_sqlite_locations` | Why valid types, correct counts, and correct locations are different properties. | Test source inspected; use retained results only with attribution. |
| Canonical output destination | `separate_output` → CLI assignment → `approve` receipt path | A single canonical destination must survive validation through writing. | Source inspected; bounded reviewer closure recorded in E04. |
| Unchanged release after refusal | Path regression’s `release_bytes()` and rejected operations | Compare inventory and file bytes, including the marker; then show the positive control. | Source inspected; wrapper execution recorded in E02. |
| Publication boundary | `_publish` | Marker invalidation, seal comparison, corpus rename, full report write, final marker rename. | No exhaustive crash campaign claimed. |
| Model versus measurement | `_one` → committed input/output JSON | Explain a quantity-times-price term and the throughput assumption that affects it. | Inspected model, not a deployed service. |

Optional VS Code or debugger captures may be added later if useful and permitted. None is represented as existing screenshot, breakpoint, or debugger-session evidence here. Until then, ordinary source navigation is the fallback. Do not imply that a prepared code stop requires live debugging during the formal assessment.

## Source register — frozen implementation

All links below are commit-pinned. Function names are navigation cues; file-level links avoid stale line selections. The targeted path links retain ranges inspected for this revision.

| Reference | File / navigation |
|---|---|
| C01 | `policy.py`: `Rule.identity`, `_rule_from`, `compile_policy`, `load_policy` |
| C02 | `pipeline.py`: `RunReport`, `_manifest_digest`, `run_pipeline` |
| C03 | `pseudonyms.py`: `_digest`, `_render`, `build_replacements` |
| C04 | `matcher.py`: `ascii_lower`, `_Aho`, `Matcher.find`, `Matcher.replace`, `_select` |
| C05 | `verification.py`: `_typed_equal`, `_expected_json`, `_verify_locations` |
| C06 | `pipeline.py`: `_publish`, including its callers’ sequencing |
| C07 | `bundle.py`: `separate_output` |
| C08 | `tests/test_discovery_boundaries.py`: targeted canonical-path regression |
| C09 | `discovery.py`: `approve` and its producer validation |
| C10 | `scripts/qualify_submission.py`: `fixture`, `readback`, `qualify` |
| C11 | `scripts/estimate_aws_cost.py`: `_one`, `_sensitivity` |
| C12 | `discovery.py`: `_name`, `_strings`, report validation, `discover` |
| C13 | `verification.py`: `verify_corpus`, `_count`, `_verify_subject_level` |
| C14 | `pipeline.py`: `_preflight`, `_source_digests` |
| C15 | `__main__.py`: `_parser`, `main`, operational commands, demo metrics |
| C16 | `policy.py`: `_boundary_overlap`, `_check_overlap` |
| C17 | `verification.py`: `_verify_sqlite_locations` |
| C18 | `discovery.py`: `write_private` |
| C19 | `formats.py`: text/CSV/JSON/SQLite adapters and searchable-value readers |
| C20 | `security/tests/test_typed_scalar_verification.py` |
| C21 | `tests/test_discovery.py`: `cli`, four-format discovery/approval workflow |
| C22 | `Dockerfile`: unchanged required entrypoint/default command and optional dependency build |
| C25 | `bundle.py`: `input_bundle` |
| D00–D06 | Brief, submission, AWS design, example policy, cost inputs/output, discovery contract |
| E02 | Committed wrapper-evaluation artifact |

[BASELINE]: https://github.com/grahama1970/oai-trial/tree/0375af56bf681e9441edcb7433cfe58951db77b2
[C01]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py
[C02]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py
[C03]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pseudonyms.py
[C04]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/matcher.py
[C05]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py
[C06]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py
[C07]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/bundle.py#L22-L37
[C08]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/tests/test_discovery_boundaries.py#L180-L244
[C09]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py
[C10]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/qualify_submission.py
[C11]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/estimate_aws_cost.py
[C12]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py
[C13]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py
[C14]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py
[C15]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/__main__.py
[C16]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py
[C17]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py
[C18]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py
[C19]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/formats.py
[C20]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/security/tests/test_typed_scalar_verification.py
[C21]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/tests/test_discovery.py
[C22]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/Dockerfile
[C25]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/bundle.py
[D00]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/TRIAL_BRIEF.md
[D01]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/SUBMISSION.md
[D02]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/docs/production-architecture.md
[D03]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/examples/policy.json
[D04]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/costs/aws-us-east-1-inputs.json
[D05]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/costs/example-estimates.json
[D06]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/docs/DISCOVERY.md
[E02]: https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/artifacts/release-artifact-path-evals.json
