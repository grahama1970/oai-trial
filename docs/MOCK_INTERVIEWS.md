# Mock interviews — code-grounded practice

**Synthetic rehearsal scenarios authored by WebGPT, not actual interviews or statements by Graham.** Suggested answers are preparation material, not proof of readiness. No live interview assistance or recording is authorized by this document.

Source snapshot: `3c77ec9386e2e037a4d2014422e693df99ee3bda`. [Docker and separate wrapper receipt log](pitch/oai-trial/rehearsal-evidence.json).

## How to rehearse

Read each interviewer turn, answer aloud, then reveal the suggested response. Use the alternative follow-ups to test vague versus evidence-grounded answers. Focus on explanation, not memorization or avoiding legitimate scrutiny.

## Preparation priorities

1. **Which source, image and entrypoint does the new receipt actually cover?** Keep package commit, execution commit, runtime comparison, wrapper and container distinct; cite both conflict refusals without relabeling this as original qualification. Action: `prepare_spoken_answer`.

2. **What does policy-bounded readiness establish about privacy?** A consistent literal transformation cannot prove policy completeness, real-person identity or safe public release. Action: `prepare_spoken_answer`.

3. **Why was the SQLite comparison corrected rather than the runtime?** Explain unchanged artifacts, version-dependent bytes, equal logical dumps and independent per-output bindings; do not dismiss a failed oracle. Action: `prepare_spoken_answer`.

4. **Where is verification independent, and where is code shared?** Name separate rereading, shared replacement primitives and the fixture-bounded independent oracle. Action: `prepare_spoken_answer`.

5. **What can exist after a publication failure?** Explain readiness, partial writes and digest trust without promising rollback, universal empty directories or signed attestation. Action: `prepare_spoken_answer`.

6. **Which research and existing components changed concrete decisions?** Preserve dogpile, pre-existing projects and skills, reuse before bespoke code, and narrow adaptations without claiming superiority or paper reproduction. Action: `prepare_spoken_answer`.

7. **What separates cloud capacity targets from demonstrated execution?** Retain modeled durations; local materialization, distributed allocation and release protocols are not established by tiny offline runs. Action: `retain_limit`.

8. **Which cost assumptions dominate, and which operations are simplified?** Explain retention, object-size sensitivity and per-object orchestration accounting rather than presenting a billing guarantee. Action: `prepare_spoken_answer`.

9. **What does this receipt not demonstrate about discovery and Judge evidence?** No discovery or adaptive campaign ran here; source-described approval adds global literal rules, while Judge evidence remains fixture-backed. Action: `retain_limit`.

10. **How should effort and chronology be described?** Use rough retrospective proportions only; avoid numerical hour allocations, measured overruns or verified compliance. Action: `retain_limit`.

## Privacy skeptic

**Interviewer · turn 1:** I’m reviewing this from the perspective of someone deciding whether to release the resulting data. My concern is the distance between a successful transformation and an acceptable privacy decision.

*Source: slide:r19-answer-exact*

<details>
<summary>Turn 2: Graham — suggested response</summary>

I’ll keep the declared policy and intended use separate, using the handout and privacy slides to anchor the discussion rather than treating the demo as release authorization.

*Source: docs/DESIGN_DECISIONS_AND_LIMITATIONS.md#questions-at-a-glance; slide:r19-answer-exact*

</details>

**Interviewer · turn 3:** The word ready is where misunderstandings can begin. Let’s establish what a downstream reader should take from that label before working through the identity examples.

*Source: slide:r13-publication; slide:r09-identity*

<details>
<summary>Turn 4: Graham — suggested response</summary>

I’ll start with the scope the pipeline claims, then use the policy and receipt references as we distinguish transformation evidence from the broader decision about releasing data.

*Source: src/anonymization_trial/policy.py::compile_policy; receipt:/proof_boundary*

</details>

**Interviewer · turn 5:** Let us treat ready as a technical claim, not permission to publish. What exactly does this system protect?

*Source: slide:r19-answer-exact*

<details>
<summary>Turn 6: Graham — suggested response</summary>

It replaces policy-declared literals while checking supported structure, protected values and declared identity consistency. It does not establish complete personal-data discovery, real-world identity truth or resistance to contextual linkage.

*Source: src/anonymization_trial/policy.py::compile_policy; receipt:/commands/5/stdout*

</details>

**Interviewer · turn 7:** Suppose a patient and a nurse are both called Alice. How does your identity policy distinguish them?

*Source: slide:r08-policy; src/anonymization_trial/policy.py::Rule.identity*

<details>
<summary>Turn 8: Graham — suggested response</summary>

It cannot distinguish them from that literal. Assigning conflicting identities to the same match domain rejects. A single supplied assignment can still be factually wrong; contextual identity resolution is not implemented.

*Source: src/anonymization_trial/policy.py::compile_policy*

</details>

**Interviewer · turn 9:** Then a valid policy might merge two real people. Who owns that decision, and what can your verifier actually establish?

*Source: src/anonymization_trial/policy.py::Rule.identity; slide:r09-identity*

<details>
<summary>Turn 10: Graham — suggested response</summary>

The policy author supplies identity authority. Verification checks conformance to that declaration, not whether two names truly identify one person. Technical readiness cannot substitute for reviewing the policy and its intended use.

*Source: src/anonymization_trial/verification.py::_verify_subject_level*

</details>

**Interviewer · turn 11:** But you hash the identity. Surely that prevents an outsider from guessing the person?

*Source: src/anonymization_trial/pseudonyms.py::_digest; slide:r09-identity*

<details>
<summary>Turn 12: Graham — suggested response</summary>

No. The namespace and derivation are public and unkeyed. Guessable identity inputs can be recomputed. HMAC, secret-key management and rotation are not implemented; even a key would not remove contextual linkage.

*Source: src/anonymization_trial/pseudonyms.py::_digest; src/anonymization_trial/pseudonyms.py::KEY_MODE*

</details>

**Interviewer · turn 13:** Return to policy completeness. An unlisted name and a rare occupation survive together. Does ready certify that combination as safe?

*Source: slide:r19-answer-exact*

<details>
<summary>Turn 14: Graham — suggested response</summary>

No. The engine enforces the supplied literals; it does not infer that combination identifies someone. An existing literal could match a substring, but there is no general discovery or residual-risk clearance promise.

*Source: src/anonymization_trial/matcher.py::Matcher.replace; receipt:/commands/5/stdout/does_not_establish*

</details>

**Interviewer · turn 15:** Your optional review shows one candidate cell. Does approving it change only that cell?

*Source: slide:r27-discovery; src/anonymization_trial/discovery.py::approve*

<details>
<summary>Turn 16: Graham — suggested response</summary>

No. Approval adds a global, case-sensitive literal rule. It can affect matching substrings elsewhere, including longer values. The reviewed location is evidence for the proposal, not the replacement scope.

*Source: src/anonymization_trial/discovery.py::approve; src/anonymization_trial/matcher.py::Matcher.replace*

</details>

**Interviewer · turn 17:** Given that broader effect, what prevents approval itself from being mistaken for release authorization?

*Source: slide:r27-discovery*

<details>
<summary>Turn 18: Graham — suggested response</summary>

Approval recomputes the review, compiles the resulting exact policy and writes private artifacts. It does not publish a corpus. The ordinary transformation and verification path must still run, and identity judgment remains the operator’s responsibility.

*Source: src/anonymization_trial/discovery.py::approve; src/anonymization_trial/pipeline.py::run_pipeline*

</details>

**Interviewer · turn 19:** Do the new Docker and wrapper successes demonstrate that this approval flow worked?

*Source: receipt:/proof_boundary; slide:r04-docker*

<details>
<summary>Turn 20: Graham — suggested response</summary>

No. This receipt covers the default engine and a separate local wrapper run and verify. No discovery or approval run occurred. Optional capability described in source is not evidence of execution here.

*Source: receipt:/proof_boundary; Dockerfile::INCLUDE_DISCOVERY*

</details>

**Interviewer · turn 21:** Earlier you called the policy authoritative. When it both protects and replaces Alice, do protected values win?

*Source: src/anonymization_trial/policy.py::_check_overlap*

<details>
<summary>Turn 22: Graham — suggested response</summary>

Neither obligation silently wins. Compilation rejects the conflict. Both recorded entrypoints returned protected_sensitive_overlap; the refusal checks found no readiness marker and empty rejection directories for these cases.

*Source: receipt:/commands/8; receipt:/commands/9; receipt:/readback*

</details>

**Interviewer · turn 23:** What is the strongest privacy conclusion you would let a reviewer repeat?

*Source: docs/DESIGN_DECISIONS_AND_LIMITATIONS.md#questions-at-a-glance*

<details>
<summary>Turn 24: Graham — suggested response</summary>

The recorded four-format cases satisfied the declared transformation checks, and conflicting policies were refused. Those results do not establish complete discovery, correct real-world identity assignments, or anonymous output.

*Source: receipt:/readback; slide:r19-answer-exact*

</details>

### Alternative follow-ups

**After turn 8**

- If your answer is vague: Show where the policy distinguishes the patient from the nurse. What happens when identical literals have conflicting subject IDs?

- If your answer is supported: What privacy mistake can still survive a syntactically valid single-identity policy?

**After turn 16**

- If your answer is vague: Point to the location constraint in the appended rule. Which field limits its scope?

- If your answer is supported: How would you explain the wider effect before accepting the policy, without pretending verification supplies human intent?

### Debrief

- prepare_spoken_answer: Separate policy conformance, personhood and release suitability.

- prepare_spoken_answer: Explain global alias approval without implying it ran in this receipt.

**Avoid claiming:**

- Names removed means anonymous.

- A public digest is encryption.

- Explicit approval proves identity or authorizes publication.

## Correctness engineer

**Interviewer · turn 1:** I have the comparison note and both output readbacks in front of me. The SQLite discrepancy is the point I want to understand before accepting the comparison.

*Source: receipt:/comparison_note; receipt:/readback*

<details>
<summary>Turn 2: Graham — suggested response</summary>

I’ll use those same artifacts and the readback function, keeping the original comparison failure visible rather than skipping directly to the corrected result.

*Source: receipt:/comparison_note; scripts/qualify_submission.py::readback*

</details>

**Interviewer · turn 3:** My concern is the evaluation standard changing after a failure, especially when a seemingly harmless format difference could hide a real change to the data.

*Source: receipt:/comparison_note; slide:r11-formats*

<details>
<summary>Turn 4: Graham — suggested response</summary>

I’ll separate the intended preservation contract, the comparison that failed, and the evidence used afterward. That gives us a concrete basis for examining the discrepancy.

*Source: slide:r11-formats; scripts/qualify_submission.py::readback*

</details>

**Interviewer · turn 5:** Your Docker and local outputs contain different SQLite bytes. Why should I not call that a correctness failure?

*Source: receipt:/comparison_note; slide:r11-formats*

<details>
<summary>Turn 6: Graham — suggested response</summary>

The contract preserves logical content, not universal serialization identity. The receipt records matching logical SQL dumps, with SQLite 3.46.1 in Docker and 3.45.1 locally. Each output also passed its own independent readback.

*Source: receipt:/comparison_note; receipt:/readback*

</details>

**Interviewer · turn 7:** You changed the harness after it failed. What stayed fixed, and what evidence replaced the failed comparison?

*Source: receipt:/comparison_note*

<details>
<summary>Turn 8: Graham — suggested response</summary>

The runtime and generated outputs stayed fixed; transforms were not repeated. The corrected comparison uses the logical contract. Separate standard-library and JSON Schema readbacks passed; CSV, JSON and text bytes match, and SQLite logical dumps match.

*Source: receipt:/comparison_note; scripts/qualify_submission.py::readback*

</details>

**Interviewer · turn 9:** A matching SQL dump says nothing about JSON true becoming 1. Show the additional check that rejects that counterexample.

*Source: scripts/qualify_submission.py::readback; slide:r12-typed-locations*

<details>
<summary>Turn 10: Graham — suggested response</summary>

The fixture readback explicitly requires Boolean flags and integer numbers. In the runtime, _typed_equal requires identical scalar types recursively. Ordinary Python equality alone would accept true and 1 as equal.

*Source: scripts/qualify_submission.py::readback; src/anonymization_trial/verification.py::_typed_equal*

</details>

**Interviewer · turn 11:** Correct types and pseudonyms, but Alice’s replacement is on Bob’s row. Counts still match.

*Source: src/anonymization_trial/verification.py::_verify_locations*

<details>
<summary>Turn 12: Graham — suggested response</summary>

The verifier compares corresponding cells and expected values. SQLite rows are matched by rowid under the supported subset. Swapping correctly typed pseudonyms therefore differs from the reconstructed value at that location.

*Source: src/anonymization_trial/verification.py::_verify_sqlite_locations; src/anonymization_trial/verification.py::_verify_locations*

</details>

**Interviewer · turn 13:** Now suppose an emitted pseudonym contains another sensitive literal. Does the next replacement rule rewrite it?

*Source: slide:r10-spans; src/anonymization_trial/matcher.py::Matcher.replace*

<details>
<summary>Turn 14: Graham — suggested response</summary>

No. Emission uses spans selected from the original input. Generated text is not rematched for replacement. The later residual scan can still reject that output, so no cascading does not guarantee successful publication.

*Source: src/anonymization_trial/matcher.py::Matcher.replace; src/anonymization_trial/verification.py::verify_corpus*

</details>

**Interviewer · turn 15:** That reconstruction uses the same matcher. Is your claimed independence really a second implementation?

*Source: slide:r21-answer-verifier; src/anonymization_trial/verification.py::_expected_json*

<details>
<summary>Turn 16: Graham — suggested response</summary>

No. Runtime verification rereads and reconstructs but shares replacement primitives. The separate qualification readback avoids runtime transformer and verifier imports, using fixed fixture expectations. That adds a bounded independent check, not a general independent engine.

*Source: src/anonymization_trial/verification.py::_expected_json; scripts/qualify_submission.py::fixture; scripts/qualify_submission.py::readback*

</details>

**Interviewer · turn 17:** Then tell me what the independent check earned here, without extending it to every possible input.

*Source: scripts/qualify_submission.py::readback*

<details>
<summary>Turn 18: Graham — suggested response</summary>

For each retained fixture output it checks inventory, expected values, alias associations, protected values, JSON types, SQLite relationships and schema, then validates the report and recomputes its bindings. It does not establish universal correctness.

*Source: scripts/qualify_submission.py::readback; receipt:/readback*

</details>

**Interviewer · turn 19:** Which artifacts received that readback? Are you describing the standalone demo’s temporary outputs as the mounted outputs?

*Source: receipt:/commands/4; receipt:/readback*

<details>
<summary>Turn 20: Graham — suggested response</summary>

The independent readback entries name docker-output and wrapper-output: the mounted Docker result and the separate local CLI result. The standalone demo’s two workload measurements are separate command output, not those retained artifacts.

*Source: receipt:/commands/4/stdout; receipt:/readback/docker-output; receipt:/readback/wrapper-output*

</details>

**Interviewer · turn 21:** Return to determinism: the corpus hashes and reports differ too. Was your earlier answer hiding that?

*Source: receipt:/readback; slide:r06-output-evidence*

<details>
<summary>Turn 22: Graham — suggested response</summary>

No. Different physical SQLite bytes produce different corpus hashes. Each report must match its own artifact. Run identifiers and timings can also differ intentionally; logical transformation equality does not imply identical reports across environments.

*Source: src/anonymization_trial/pipeline.py::run_pipeline; receipt:/comparison_note*

</details>

**Interviewer · turn 23:** Where is the line between correcting the oracle and quietly weakening the contract?

*Source: slide:r11-formats; receipt:/comparison_note*

<details>
<summary>Turn 24: Graham — suggested response</summary>

Preserve the original logical contract and disclose the failed byte-equality assumption. Retain typed, structural and per-artifact digest checks. Accepting arbitrary byte changes without those checks would not be the correction recorded here.

*Source: receipt:/comparison_note; scripts/qualify_submission.py::readback*

</details>

### Alternative follow-ups

**After turn 8**

- If your answer is vague: Which readback checks actual rows and report bindings independently of those flags?

- If your answer is supported: Which semantic mutation would still fail even with logically comparable serializations?

**After turn 16**

- If your answer is vague: Follow _expected_json into replace_text. Which code is shared with transformation?

- If your answer is supported: What common-mode risk survives, and why is the fixture oracle still useful?

### Debrief

- prepare_spoken_answer: Defend the corrected logical oracle without dismissing the original failure.

- prepare_spoken_answer: Distinguish runtime checking, independent fixture readback and cross-environment comparison.

**Avoid claiming:**

- Different bytes never matter.

- Matching dumps alone prove every type and relationship.

- The new readback reran original submission qualification.

## Reliability engineer

**Interviewer · turn 1:** For this discussion, I’m taking the perspective of someone consuming an output directory after a run has stopped. I care most about recognizing a usable release and handling uncertainty.

*Source: slide:r13-publication*

<details>
<summary>Turn 2: Graham — suggested response</summary>

I’ll anchor the walkthrough in the recorded execution identities and publication sequence, with the receipt available to distinguish observed behavior from the failure cases we discuss.

*Source: receipt:/source_commit; src/anonymization_trial/pipeline.py::_publish*

</details>

**Interviewer · turn 3:** I also want the successful runs and refusal cases kept distinct. They give us a starting point, but one example should not stand in for every interruption.

*Source: receipt:/commands; receipt:/readback*

<details>
<summary>Turn 4: Graham — suggested response</summary>

We’ll identify the exercised entrypoints first, then follow the output state through publication. I’ll keep the relevant code beside the receipt rather than relying on a summary status.

*Source: receipt:/commands; src/anonymization_trial/pipeline.py::_publish*

</details>

**Interviewer · turn 5:** Before discussing fail-closed behavior, pin what actually ran. Is the documentation commit also the rehearsal execution commit?

*Source: receipt:/source_commit; receipt:/runtime_baseline*

<details>
<summary>Turn 6: Graham — suggested response</summary>

No. The receipt records execution source fbd9aa92 and runtime baseline 0375af56. This package is at 3c77ec93. The receipt identifies the image by its full digest and separately hashes the wrapper; those identities are not interchangeable.

*Source: receipt:/source_commit; receipt:/image_id; receipt:/wrapper_sha256*

</details>

**Interviewer · turn 7:** Was Docker invoked through the skill? Give the exact build and offline demo commands before explaining the wrapper.

*Source: receipt:/commands/2/argv; receipt:/commands/4/argv; slide:r26-wrapper*

<details>
<summary>Turn 8: Graham — suggested response</summary>

The commands were docker build -t anonymization-trial:interview-fbd9aa92 . and docker run --rm --network=none anonymization-trial:interview-fbd9aa92. The wrapper separately invoked the local CLI for run and verify; it did not execute that container.

*Source: receipt:/commands/2; receipt:/commands/4; receipt:/commands/6; receipt:/commands/7*

</details>

**Interviewer · turn 9:** You said offline. Was the image build also offline and cache-free?

*Source: receipt:/commands/2/argv; receipt:/commands/2/stderr*

<details>
<summary>Turn 10: Graham — suggested response</summary>

No such claim follows. The build command has neither an offline flag nor --no-cache, and its log includes cached layers. Network isolation applies to the recorded Docker execution commands.

*Source: receipt:/commands/2; receipt:/commands/4/argv; receipt:/commands/5/argv*

</details>

**Interviewer · turn 11:** Both rejected runs left empty directories. Does every failed run therefore leave nothing behind?

*Source: receipt:/readback/rejections_empty_directories; slide:r13-publication*

<details>
<summary>Turn 12: Graham — suggested response</summary>

No. Those were conflicting-policy refusals against the exercised destinations. Later publication failures can leave uncommitted corpus bytes. An early failure on a rerun can preserve a prior release. Empty output is not a universal guarantee.

*Source: src/anonymization_trial/pipeline.py::run_pipeline; src/anonymization_trial/pipeline.py::_publish*

</details>

**Interviewer · turn 13:** Suppose the process dies after moving the corpus but before publishing the marker. What should a consumer do?

*Source: src/anonymization_trial/pipeline.py::_publish*

<details>
<summary>Turn 14: Graham — suggested response</summary>

Treat the directory as unready. The protocol removes old readiness before replacement and publishes report.json last. It is not whole-workflow rollback; consumers must not interpret corpus presence as readiness.

*Source: src/anonymization_trial/pipeline.py::_publish; slide:r13-publication*

</details>

**Interviewer · turn 15:** Trace a partial report write, then a zero-progress write. What code prevents premature readiness?

*Source: src/anonymization_trial/pipeline.py::_publish*

<details>
<summary>Turn 16: Graham — suggested response</summary>

The loop advances its memoryview by the returned byte count. Zero or negative progress raises before the final marker rename. The temporary report is fsynced, renamed last, and followed by directory fsync.

*Source: src/anonymization_trial/pipeline.py::_publish*

</details>

**Interviewer · turn 17:** Does a valid verification hash prove verification ran if an attacker can rewrite both corpus and report?

*Source: slide:r13-publication; src/anonymization_trial/pipeline.py::run_pipeline*

<details>
<summary>Turn 18: Graham — suggested response</summary>

No. verification_sha256 is the sealed corpus digest, not a separate signed verifier attestation. Binding requires a trusted reference. Trusted single-writer staging is an assumption; hostile-host forgery resistance is not established.

*Source: src/anonymization_trial/pipeline.py::run_pipeline; src/anonymization_trial/pipeline.py::_publish*

</details>

**Interviewer · turn 19:** Why was separate readback necessary after the wrapper’s verify command succeeded?

*Source: receipt:/commands/7; receipt:/readback/wrapper-output*

<details>
<summary>Turn 20: Graham — suggested response</summary>

Corpus verification and report validation are different checks. The separate readback inspects expected values and inventory, validates JSON Schema, and recomputes policy, source and corpus bindings. A verify success flag alone does not supply all that evidence.

*Source: scripts/qualify_submission.py::readback; question-map:Q43*

</details>

**Interviewer · turn 21:** Revisit fail-closed evidence. What precisely did both refusal cases demonstrate about errors and readiness?

*Source: receipt:/commands/8; receipt:/commands/9*

<details>
<summary>Turn 22: Graham — suggested response</summary>

Both exited with code 1 and protected_sensitive_overlap. The receipt records no readiness markers, empty rejection directories and absence of the raw-name leak checked by the harness. These observations cover those cases, not every failure mode.

*Source: receipt:/readback/rejections_no_ready_marker; receipt:/readback/rejection_raw_name_absent*

</details>

**Interviewer · turn 23:** Would you present this as fresh qualification of the original submitted archive?

*Source: question-map:Q45; receipt:/proof_boundary*

<details>
<summary>Turn 24: Graham — suggested response</summary>

No. These are later rehearsal executions with their own source and image identity. The recorded runtime comparison covers the source directory and Dockerfile. They do not rerun the complete original qualification workflow or recertify its archive.

*Source: receipt:/commands/1/argv; receipt:/proof_boundary*

</details>

### Alternative follow-ups

**After turn 8**

- If your answer is vague: Compare the mounted Docker argv with the absolute run.sh argv. Which one starts a container?

- If your answer is supported: What can offline container execution establish that the build log cannot?

**After turn 16**

- If your answer is vague: Locate the corpus rename and final report rename. What exists between them?

- If your answer is supported: How should an existing consumer behave during that interval, and which crash guarantees remain unproved?

### Debrief

- prepare_spoken_answer: Read exact receipt identities and entrypoints before summarizing success.

- retain_limit: Refusal observations do not become universal rollback, crash or authenticity guarantees.

**Avoid claiming:**

- The build was offline or --no-cache.

- The wrapper was the Docker entrypoint.

- A digest authenticates verification.

- Every failure empties output.

## Scale/cost reviewer

**Interviewer · turn 1:** I’m using the cloud section for a capacity-planning discussion, not a procurement decision. The useful outcome is understanding which assumptions drive the proposed service targets.

*Source: slide:r15-capacity*

<details>
<summary>Turn 2: Graham — suggested response</summary>

I’ll keep the small-workload receipt separate from the scenario inputs and bring the estimator into the discussion when we reach capacity or cost.

*Source: receipt:/commands/4/stdout; scripts/estimate_aws_cost.py::_one*

</details>

**Interviewer · turn 3:** I’m particularly interested in the workload behind the numbers. Let’s keep the file-size, concurrency and retention assumptions visible so the discussion stays tied to a defined scenario.

*Source: costs/aws-us-east-1-inputs.json*

<details>
<summary>Turn 4: Graham — suggested response</summary>

I’ll use the committed capacity and cost figures as the starting scenario, then keep any workload variations explicit rather than quietly changing the basis of comparison.

*Source: slide:r15-capacity; slide:r16-cost*

</details>

**Interviewer · turn 5:** I am considering a petabyte workload. Which numbers are observations, and which belong only to the cloud model?

*Source: slide:r15-capacity; receipt:/commands/4/stdout*

<details>
<summary>Turn 6: Graham — suggested response</summary>

The receipt measures two small synthetic demo sizes. The cloud model assumes 200 workers at 20 MB/s each and roughly 1 MiB objects. Those assumptions are not validated by this rehearsal.

*Source: costs/aws-us-east-1-inputs.json; receipt:/commands/4/stdout*

</details>

**Interviewer · turn 7:** Could you extrapolate that successful demo into the seven-day petabyte commitment shown on the slide?

*Source: slide:r15-capacity*

<details>
<summary>Turn 8: Graham — suggested response</summary>

No. The slide distinguishes a 141.67-hour model from a seven-day design target. Both depend on assumed throughput, verification cost, retries and concurrency. Neither is a measured service level or contractual delivery promise.

*Source: slide:r15-capacity; scripts/estimate_aws_cost.py::_one*

</details>

**Interviewer · turn 9:** Then suppose one input file is larger than worker memory. What does the actual local implementation do that your diagram abstracts away?

*Source: src/anonymization_trial/verification.py::_searchable; docs/DESIGN_DECISIONS_AND_LIMITATIONS.md#questions-at-a-glance*

<details>
<summary>Turn 10: Graham — suggested response</summary>

Local adapters materialize files or tables, and verification retains searchable text from both corpora. It is not bounded-memory streaming. The distributed, format-aware execution path is proposed architecture, not implemented by this local engine.

*Source: src/anonymization_trial/verification.py::_searchable; src/anonymization_trial/verification.py::verify_corpus*

</details>

**Interviewer · turn 11:** Then split at newlines. A quoted CSV field contains a newline, and a text boundary cuts a UTF-8 character. What happens?

*Source: docs/production-architecture.md#distribution-concurrency-skew-formats*

<details>
<summary>Turn 12: Graham — suggested response</summary>

Those are counterexamples to naive splitting. The design requires parser-confirmed CSV records and UTF-8-safe text boundaries with match-overlap ownership. JSON documents and SQLite remain whole units there. That partitioner is not implemented locally.

*Source: docs/production-architecture.md#distribution-concurrency-skew-formats; question-map:Q24*

</details>

**Interviewer · turn 13:** Reconnect scale to identity correctness. Two workers share a key but see different identity subsets. Will their allocations necessarily agree?

*Source: slide:r14-cloud; src/anonymization_trial/pseudonyms.py::build_replacements*

<details>
<summary>Turn 14: Graham — suggested response</summary>

No. Collision resolution depends on the sorted identity set. A shared key alone does not coordinate the resulting salts. Workers need a consistent versioned identity and allocation plan; distributed plan management is not implemented here.

*Source: src/anonymization_trial/pseudonyms.py::build_replacements; question-map:Q25*

</details>

**Interviewer · turn 15:** Why should I trust approximately $86 per TB and $85,734 per PB when those assumptions are unmeasured?

*Source: slide:r16-cost; docs/production-architecture.md#cost-reproducible*

<details>
<summary>Turn 16: Graham — suggested response</summary>

Trust the arithmetic as an inspectable scenario, not a quote. Three retained copies for one month dominate these inputs. Compute, requests and orchestration are explicit approximations with dated list prices, not observed deployment bills.

*Source: scripts/estimate_aws_cost.py::_one; costs/aws-us-east-1-inputs.json*

</details>

**Interviewer · turn 17:** Same total bytes, but files are ten times smaller. Which terms change, and does total cost become ten times larger?

*Source: scripts/estimate_aws_cost.py::_sensitivity*

<details>
<summary>Turn 18: Graham — suggested response</summary>

The modeled object count grows tenfold, increasing request and per-object orchestration costs accordingly. Storage and byte-based compute stay unchanged in that formula. Total cost therefore does not simply grow tenfold.

*Source: scripts/estimate_aws_cost.py::_one; scripts/estimate_aws_cost.py::_sensitivity*

</details>

**Interviewer · turn 19:** Does the orchestration term count SQS send, receive and delete separately, plus every encryption operation?

*Source: scripts/estimate_aws_cost.py::_one*

<details>
<summary>Turn 20: Graham — suggested response</summary>

No. It budgets one priced SQS unit, one EventBridge event and one KMS request per object, plus log bytes. That is simplified accounting, not a trace of every billable API call.

*Source: scripts/estimate_aws_cost.py::_one; question-map:Q47*

</details>

**Interviewer · turn 21:** Earlier you relied on deterministic workers. If two attempts finish the same object, does determinism itself prevent premature publication?

*Source: slide:r14-cloud*

<details>
<summary>Turn 22: Graham — suggested response</summary>

No. The proposed orchestrator still needs idempotent attempt handling, complete manifest validation and conditional pointer publication. At-least-once delivery is not exactly-once processing. The local implementation does not establish that distributed release protocol.

*Source: question-map:Q27; docs/production-architecture.md#reliability*

</details>

**Interviewer · turn 23:** What decision can this model support today without pretending the deployment exists?

*Source: slide:r23-answer-scale*

<details>
<summary>Turn 24: Graham — suggested response</summary>

It supports discussion of workload assumptions, sensitivity and required capacity. It does not authorize a petabyte delivery guarantee. The cloud durations remain valid modeled content and are unrelated to retrospective development-effort allocation.

*Source: slide:r15-capacity; scripts/estimate_aws_cost.py::_one*

</details>

### Alternative follow-ups

**After turn 8**

- If your answer is vague: Where was sustained 20 MB/s per worker measured on representative data?

- If your answer is supported: Which workload characteristic could invalidate the model even with enough vCPUs?

**After turn 16**

- If your answer is vague: Which inputs account for every API operation, storage tier and deployment overhead?

- If your answer is supported: How would smaller objects shift the dominant cost without changing total bytes?

### Debrief

- prepare_spoken_answer: Trace assumptions through _one instead of repeating a total.

- retain_limit: Preserve modeled capacity and distributed-design labels.

**Avoid claiming:**

- Small-demo throughput validates petabyte delivery.

- A shared key alone guarantees distributed identity consistency.

- A reproducible calculator is a billing quote.

## Research/reuse reviewer

**Interviewer · turn 1:** I’m approaching the research section as a review of engineering choices. The useful story is the route from framing the problem to selecting existing components and deciding what remained custom.

*Source: slide:r06a-research-reuse*

<details>
<summary>Turn 2: Graham — suggested response</summary>

I’ll follow the research and reuse map: dogpile across Brave, arXiv and GitHub, then pre-existing projects and skills, with reuse and composition considered before bespoke code.

*Source: docs/pitch/oai-trial/reorganized/sources/research-workflow.md#working-method*

</details>

**Interviewer · turn 3:** The distinction I care about is between considering a source and adopting its method. A short account of the tradeoffs will help more than a catalogue of papers.

*Source: slide:r06b-research-adoption*

<details>
<summary>Turn 4: Graham — suggested response</summary>

I’ll pair the research examples with their code references and stated limits, while keeping reusable development tooling separate from the shipped engine. That will frame the choices we discuss.

*Source: docs/pitch/oai-trial/reorganized/sources/research-workflow.md#research-that-led-to-narrower-code-changes; slide:r26-wrapper*

</details>

**Interviewer · turn 5:** You emphasize research-first, yet shipped a custom matcher. Explain the actual reuse process before defending that choice.

*Source: slide:r06a-research-reuse; docs/pitch/oai-trial/reorganized/sources/research-workflow.md#working-method*

<details>
<summary>Turn 6: Graham — suggested response</summary>

Frame the challenge first. Use dogpile across Brave web, arXiv and GitHub, inspect methods and implementations, then examine pre-existing projects and skills. Reuse or compose suitable components before writing the remaining contract-specific code.

*Source: docs/pitch/oai-trial/reorganized/sources/research-workflow.md#working-method*

</details>

**Interviewer · turn 7:** What did FlashText-style matching, clean-text and Presidio contribute, and where is the benchmark proving your matcher better?

*Source: docs/pitch/oai-trial/reorganized/sources/research-workflow.md#concrete-choices-in-this-project*

<details>
<summary>Turn 8: Graham — suggested response</summary>

Their matching, boundary, encoding and overlap ideas informed the design. Detection authority and silent normalization did not fit the literal contract. The standard library supplies format machinery. No comparative benchmark established superiority over FlashText or a PII platform.

*Source: docs/pitch/oai-trial/reorganized/sources/research-workflow.md#concrete-choices-in-this-project; src/anonymization_trial/matcher.py::_Aho*

</details>

**Interviewer · turn 9:** How do you distinguish research-led refinement from a bibliography attached after coding? Give a concrete sequence rather than saying research first again.

*Source: docs/pitch/oai-trial/reorganized/sources/research-workflow.md#chronology-and-time-boundary*

<details>
<summary>Turn 10: Graham — suggested response</summary>

The source map records initial research before the hardened matcher change, and an adoption memo before privacy exclusions, subject checks, namespace labels and sensitivity tests. Research also continued alongside implementation; not every paper preceded every line of code.

*Source: docs/pitch/oai-trial/reorganized/sources/research-workflow.md#chronology-and-time-boundary*

</details>

**Interviewer · turn 11:** Your slide names SPIA. Did the project pass its subject-level inference evaluation?

*Source: slide:r06b-research-adoption; arXiv:2604.21211*

<details>
<summary>Turn 12: Graham — suggested response</summary>

No. The adaptation is narrower: declared-identity coherence checks and explicit privacy limits. The subject check tests pseudonym presence and same-type distinctness; location checks add correspondence. None of that constitutes SPIA’s inference-attack evaluation.

*Source: src/anonymization_trial/verification.py::_verify_subject_level; docs/pitch/oai-trial/reorganized/sources/research-workflow.md#research-that-led-to-narrower-code-changes*

</details>

**Interviewer · turn 13:** Give similarly concrete boundaries for DICOM validation, AnonShield and Proteus. Which code should I inspect?

*Source: slide:r06b-research-adoption*

<details>
<summary>Turn 14: Graham — suggested response</summary>

Inspect qualification readback and verifier-sensitivity tests for known-truth and corrupted-output checking. Inspect _digest for explicit namespace labels. DICOM processing, paper benchmarks, HMAC, encryption and key rotation are not implemented.

*Source: scripts/qualify_submission.py::readback; security/tests/test_verifier_sensitivity.py; src/anonymization_trial/pseudonyms.py::_digest; arXiv:2508.01889; arXiv:2606.15650; arXiv:2603.06540*

</details>

**Interviewer · turn 15:** And the reusable anonymize-data skill: another engine, or a dependency the default container needs?

*Source: slide:r26-wrapper; Dockerfile*

<details>
<summary>Turn 16: Graham — suggested response</summary>

Neither. It is a thin wrapper around the project CLI. The container runs independently. The new receipt separately records the local wrapper’s run and verify; that does not convert it into the Docker entrypoint or demonstrate optional discovery.

*Source: docs/pitch/oai-trial/reorganized/sources/skill-reuse-reference.md#thin-delegation; receipt:/commands/6; receipt:/commands/7*

</details>

**Interviewer · turn 17:** The source slide links an earlier wrapper snapshot. How do you avoid presenting those excerpts as the exact later installation?

*Source: docs/pitch/oai-trial/reorganized/sources/skill-reuse-reference.md; receipt:/wrapper_sha256*

<details>
<summary>Turn 18: Graham — suggested response</summary>

The excerpts explain the pattern and explicitly disclaim identifying a later execution. For this run, the receipt records the wrapper file’s SHA-256 and actual command paths. I would not extend that hash to every dependency or another installation.

*Source: docs/pitch/oai-trial/reorganized/sources/skill-reuse-reference.md; receipt:/wrapper_sha256*

</details>

**Interviewer · turn 19:** The deck also says Adaptive Lineage. Does the new rehearsal include a live adaptive attack against this target?

*Source: slide:r25-lineage; receipt:/proof_boundary*

<details>
<summary>Turn 20: Graham — suggested response</summary>

No. The retained Judge demonstration is fixture-backed. This receipt records default-engine executions, readbacks and conflict refusals, not discovery or an adaptive campaign. Those evidence classes must remain separate.

*Source: docs/DESIGN_DECISIONS_AND_LIMITATIONS.md#questions-at-a-glance; receipt:/proof_boundary*

</details>

**Interviewer · turn 21:** Return to research-first: can commit timestamps prove that research consumed most effort, or that the timebox was met or exceeded?

*Source: question-map:Q28; slide:r17-disclosure*

<details>
<summary>Turn 22: Graham — suggested response</summary>

No. Roughly a third researching, a quarter building and testing, and the rest on extras and polish. That is retrospective, not instrumented. Commit history records chronology, not active effort or verified timebox compliance.

*Source: docs/pitch/oai-trial/reorganized/sources/research-workflow.md#chronology-and-time-boundary; question-map:Q28*

</details>

**Interviewer · turn 23:** How should these prepared answers be used without implying authorization for live assistance during an assessment?

*Source: question-map:Q48*

<details>
<summary>Turn 24: Graham — suggested response</summary>

As private practice for explaining mechanisms and limits in my own words. These are suggested answers, not past statements or readiness proof. Live assistance and recording require their own explicit permissions; coding-tool permission does not automatically carry over.

*Source: question-map:Q48*

</details>

### Alternative follow-ups

**After turn 8**

- If your answer is vague: Where is the comparison, and which requirement could not be met by reuse?

- If your answer is supported: Which maintenance and common-mode verification risks did custom matching leave with this project?

**After turn 16**

- If your answer is vague: Which recorded argv uses run.sh, and which uses docker run?

- If your answer is supported: How do historical wrapper excerpts differ from the executable identity recorded for this run?

### Debrief

- prepare_spoken_answer: Pair each research name with one adaptation and one exclusion.

- prepare_spoken_answer: Defend reuse choices without inventing comparative results.

- retain_limit: Keep effort rough and assistance permission separate.

**Avoid claiming:**

- All research finished before any code existed.

- Paper citation means full implementation or benchmark reproduction.

- Default runs exercised discovery or a live adaptive campaign.

- Commit duration measures active effort.

## Deck implications

WebGPT recommended no additional significant slide edits from these scenarios. Prepare stronger spoken answers and preserve the existing limitations. This is reviewer judgment—not proof that a real interviewer will follow these paths.

## Proof and limitations

The project agent ran Docker and the separate local CLI wrapper, independently read both synthetic four-format outputs, and checked conflicting-policy refusals. WebGPT retrieved the committed receipt and code; it did not execute those commands. SQLite bytes differ across the two environments but logical dumps match; the receipt discloses the corrected byte-equality assumption.

These transcripts have setup, two-sided dialogue, follow-ups and closes. The structure heuristic accepted correctness and reliability; it flagged privacy, scale and research for question density (11/24), counting declarative setup phrases containing words such as “what” or “which.” These remain practice drafts, not realism-approved meeting playback. No audio was generated or recording started.
