# OAI trial — results, choices and evidence

**Candidate coordinated authoring revision.** Implementation frozen at [0375af56bf681e9441edcb7433cfe58951db77b2](https://github.com/grahama1970/oai-trial/tree/0375af56bf681e9441edcb7433cfe58951db77b2). This presentation does not change the submitted runtime, ZIP, or prior technical-review scope.

**Prepared presentation: 30 minutes including navigation. Audience discussion: 15+ minutes separately.** Table of Contents is first; Thank you is last. Extra Credit is the last substantive prepared block. Prepared Question/Answer pairs are distinct from audience Discussion.

The supplied grahama.co house tokens and actual header texture are used. Native text remains editable; SVG internals are images in the export. No sponsor/distribution markings from reference slides are copied. No source navigation below is a breakpoint or evidence of a running debugger.

## Using the transcript

Read SAY as speaker notes rather than an undocumented authorship claim. Use SHOW for a brief pinned code or source jump inside each allocated interval. Full follow-up answers stay in the separate appendix. The speaker text is about 3,450 words; leave the remaining prepared time for transitions, observation and navigation. That is a rehearsal allocation, not a measured delivery time.

Use recorded artifacts if setup is unavailable. Do not install packages, rebuild an image or debug a tool during the talk. No successful command in the historical evidence is a command executed by this authoring environment.

[Opening hierarchy](TOC.md) · [Primary question map](question-map.json) · [Code/slide map](slide-map.json)

## Prepared timing

| Slide | Time | Takeaway |
|---|---|---|
| [r01-toc](#r01-toc) | 00:00–00:45 | Table of Contents |
| [r02-demo-result](#r02-demo-result) | 00:45–02:15 | Here is the result—not just a success flag |
| [r03-demo-observations](#r03-demo-observations) | 02:15–03:15 | Small workloads were measured; petabytes were not |
| [r04-docker](#r04-docker) | 03:15–04:15 | The evaluator needs one self-contained image |
| [r05-mounted-cli](#r05-mounted-cli) | 04:15–05:30 | One bundle in; one dedicated release directory out |
| [r06-output-evidence](#r06-output-evidence) | 05:30–07:00 | Check the artifacts, not the exit code |
| [r07-pipeline-map](#r07-pipeline-map) | 07:00–07:45 | Transformation and release are separate steps |
| [r08-policy](#r08-policy) | 07:45–09:00 | The policy supplies authority—not a guess |
| [r09-identity](#r09-identity) | 09:00–10:45 | Aliases converge because identity is declared |
| [r10-spans](#r10-spans) | 10:45–12:15 | Select original spans; emit only once |
| [r11-formats](#r11-formats) | 12:15–13:30 | Preserve logical meaning—not identical serialization |
| [r12-typed-locations](#r12-typed-locations) | 13:30–15:00 | A correct value on the wrong row is still wrong |
| [r13-publication](#r13-publication) | 15:00–16:30 | The marker—not the directory—authorizes use |
| [r14-cloud](#r14-cloud) | 16:30–18:00 | Distribute the work; retain one corpus decision |
| [r15-capacity](#r15-capacity) | 18:00–19:00 | The SLA is a scenario—not a benchmark |
| [r16-cost](#r16-cost) | 19:00–20:15 | Retention dominates this 1 PB cost scenario |
| [r17-disclosure](#r17-disclosure) | 20:15–21:00 | Technical readiness does not waive the timebox |
| [r18-question-exact](#r18-question-exact) | 21:00–21:15 | Question 1 |
| [r19-answer-exact](#r19-answer-exact) | 21:15–22:00 | Explicit policy separates authority from guessing |
| [r20-question-verifier](#r20-question-verifier) | 22:00–22:15 | Question 2 |
| [r21-answer-verifier](#r21-answer-verifier) | 22:15–23:00 | Rereading helps; common-mode risk remains |
| [r22-question-scale](#r22-question-scale) | 23:00–23:15 | Question 3 |
| [r23-answer-scale](#r23-answer-scale) | 23:15–24:00 | The model exposes assumptions; it does not validate them |
| [r24-security-evals](#r24-security-evals) | 24:00–25:15 | Security evals test different failure surfaces |
| [r25-lineage](#r25-lineage) | 25:15–26:00 | The retained Judge result is fixture-backed |
| [r26-wrapper](#r26-wrapper) | 26:00–27:00 | The skill delegates; it does not fork the engine |
| [r27-discovery](#r27-discovery) | 27:00–28:30 | A proposed alias does not authorize release |
| [r28-canonical-path](#r28-canonical-path) | 28:30–30:00 | Validate the destination that will actually be written |
| [r29-discussion](#r29-discussion) | 30:00–45:00+ audience reserve | Discussion |
| [r30-thank-you](#r30-thank-you) | After discussion; end playback | Thank you |

<a id="r01-toc"></a>
## r01-toc — Table of Contents

**Time:** 00:00–00:45. **Block:** Contents. **Primary questions:** None; navigation or paired lead-in.

### Say

I’ll start with the recorded result, so you can see what this system produced before we discuss its internals. Then I’ll show the small reproduction interface and the independent output checks. We’ll use the same synthetic Alice, A.L, and Bob example through policy authority, identity, matching, verification, and publication.
The cloud design and its cost assumptions were required by the assignment, so they stay with the core explanation. I have three prepared questions to defend the choices, followed by the additional security evidence, thin wrapper, and reviewed alias workflow. Those are distinct from your questions at the end. All source navigation is pinned to the submitted implementation.

### Show / navigate

Point down the hierarchy without reading every subtopic. No cover slide precedes this page.


**Visible qualification:** Recorded results first. Source navigation is not a live breakpoint.

**Evidence IDs:** E08

<a id="r02-demo-result"></a>
## r02-demo-result — Here is the result—not just a success flag

**Time:** 00:45–02:15. **Block:** Demo and Results. **Primary questions:** None; navigation or paired lead-in.

### Say

I’m using a thin skill wrapper around the project’s CLI; the same engine runs independently in Docker.

Start with this concrete result. The qualification fixture links Alice and A.L to person-a, and Bob to person-b. The source-side checker expects one name pseudonym for Alice’s aliases and another for Bob. KEEP, the Boolean flags, and the integer values remain unchanged.
The supplied receipt records successful readback of CSV, JSON, UTF-8 text and SQLite, including the legal sqliteX table. It also records that the original input remained unchanged. The before-and-after illustration is drawn from those checker assertions; it is not a screenshot of a newly executed terminal or a raw output file supplied with the packet.
That distinction is deliberate. You can inspect the receipt fields and the checker that produced them. We are evaluating whether the output remained useful and correctly associated—not whether a process printed PASS. The mechanism is policy-bounded pseudonymization, not evidence that every possible identifier was discovered.

### Show / navigate

Before displaying the result, run the prepared synthetic bundle through the existing skill after local preflight. This is a presenter action, not a run performed by this document. Use a dedicated empty output outside the inputs; inspect the actual output. If using the historical fallback instead, say that explicitly.

```bash
ANONYMIZE="$HOME/workspace/experiments/agent-skills/skills/anonymize-data/run.sh"
"$ANONYMIZE" run --input "$INPUT" --output "$OUTPUT"
"$ANONYMIZE" verify --input "$INPUT" --output "$OUTPUT"
```

Open sources/qualification.json at readbacks and source_unchanged; then scripts/qualify_submission.py::readback only if needed.

- [`scripts/qualify_submission.py::fixture` — L39–L77](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/qualify_submission.py#L39-L77)
- [`scripts/qualify_submission.py::readback` — L80–L134](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/qualify_submission.py#L80-L134)

**Visible qualification:** Recorded qualification + checker-asserted values; not a new output capture.

**Evidence IDs:** E01, E06

**Transition:** The same receipt also gives bounded, observed performance numbers.

<a id="r03-demo-observations"></a>
## r03-demo-observations — Small workloads were measured; petabytes were not

**Time:** 02:15–03:15. **Block:** Demo and Results. **Primary questions:** None; navigation or paired lead-in.

### Say

These are the two demo runs recorded in the supplied qualification receipt. The logical fixture sizes are 100 and 1,000. Each run processed four files and reported verification success. The elapsed observations are 0.050762 and 0.386924 seconds, and peak memory is reported as 26.83 and 29.83 MB.
The rates are also shown so the result is reproducible as evidence, not reduced to a speed claim. Records processed are not the same field as logical fixture size: the generated formats contribute multiple records to the run counters.
This is a small synthetic demonstration. It is not an estimate of what one production worker will sustain on arbitrary customer exports. Later I will label the cloud throughput separately as an assumption. Nothing on this page was remeasured while this authoring revision was prepared.

### Show / navigate

Read the exact values from sources/qualification.json#/demo/runs. Do not extrapolate a linear memory bound.

- [`src/anonymization_trial/__main__.py::_run_once` — L41–L58](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/__main__.py#L41-L58)

**Visible qualification:** Historical observations from the supplied receipt. Not current measurement.

**Evidence IDs:** E01

<a id="r04-docker"></a>
## r04-docker — The evaluator needs one self-contained image

**Time:** 03:15–04:15. **Block:** Reproduce and Verify. **Primary questions:** Q46

### Say

Here is the supported reproduction environment rather than a new service stack. From the frozen checkout, the required Docker build creates anonymization-trial, and a bare run executes the self-contained demo. The image supplies the application; the evaluator does not need the shared skill or a running database service.
For local development the project uses Python 3.12 or newer and declared extras. Dependencies are permitted by the brief. The default runtime’s small dependency set is an implementation choice, not a restriction I invented from the assignment.
The supplied qualification records the default image build and execution. The later discovery-enabled build has an explicit INCLUDE_DISCOVERY argument; do not treat this default-image receipt as proof that the optional image was exercised. We are displaying supported commands, not executing or installing anything during these slides.

### Show / navigate

Dockerfile at the pinned commit; commands in the transcript. Local setup is documented there, not a live install.

- [`src/anonymization_trial/__main__.py::main` — L207–L233](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/__main__.py#L207-L233)

**Supported commands; not executed during authoring:**

```bash
docker build -t anonymization-trial .
docker run --rm anonymization-trial
```

**Local development alternative, from the frozen checkout with uv installed:**

```bash
uv sync --locked --extra dev --extra discovery
uv run anonymization-trial --help
```

The discovery extra is optional functionality; these setup commands are not additional execution claims.

**Visible qualification:** Default image: exact engine. Optional discovery-image execution is separate.

**Evidence IDs:** E01, E08

<a id="r05-mounted-cli"></a>
## r05-mounted-cli — One bundle in; one dedicated release directory out

**Time:** 04:15–05:30. **Block:** Reproduce and Verify. **Primary questions:** Q42, Q43

### Say

The original interface accepts an input bundle containing policy.json and corpus. The input is mounted read-only; the output mount is a dedicated empty directory. On success, the release root contains only corpus and report.json.
The later file-or-folder interface adapts separate input and policy paths into that same bundle. It is useful to the operator, but it does not replace the evaluator command or create a second engine. I’ll show the thin wrapper in Extra Credit.
The operational commands also have different jobs. Preflight checks admission; inspect summarizes selected report fields; verify rereads the corpus against the source policy. None should be described as authenticating a signed release. The stronger qualification readback checks report schema and digests as a separate operation. Here we use source navigation and a supported command string, not an invented terminal recording.

### Show / navigate

Navigate to __main__.py::_verify_cmd and _inspect_cmd; show the full mounted command from WALKTHROUGH.md.

- [`src/anonymization_trial/__main__.py::_verify_cmd; _inspect_cmd` — L139–L157](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/__main__.py#L139-L157)
- [`src/anonymization_trial/bundle.py::input_bundle` — L40–L71](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/bundle.py#L40-L71)
- [`src/anonymization_trial/__main__.py::main` — L207–L233](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/__main__.py#L207-L233)

```bash
docker run --rm \
  -v "$INPUT":/trial/input:ro \
  -v "$OUTPUT":/trial/output \
  anonymization-trial run
```

```text
INPUT/                  OUTPUT/
  policy.json             report.json
  corpus/                 corpus/
```

**Installed project CLI, not an additional Docker qualification result:**

```bash
anonymization-trial verify --input "$INPUT" --output "$OUTPUT"
anonymization-trial inspect "$OUTPUT"
```

**Visible qualification:** INPUT/OUTPUT are operator paths. inspect is not release authentication.

**Evidence IDs:** E01, E08

<a id="r06-output-evidence"></a>
## r06-output-evidence — Check the artifacts, not the exit code

**Time:** 05:30–07:00. **Block:** Reproduce and Verify. **Primary questions:** Q22, Q23, Q44, Q45

### Say

The recorded qualification is more than an exit-code wrapper. Its readback computes the expected synthetic pseudonyms with the documented SHA-256 input, parses CSV and JSON directly, queries SQLite, checks the fixture’s typed values and schema, validates the report against JSON Schema, and recomputes policy and corpus digests. It does not import the runtime transformer or verifier to decide the expected result.
The receipt also records an offline replay with the same corpus digest, unchanged input, and early and late refusal cases. Those are bounded checks against the demonstrated fixture and commands—not exhaustive security proof. The submitted archive identity is recorded separately from this presentation bundle.
I have not rerun that qualification here. The script records its invoking HEAD, clones main, and requires equality; it does not accept an arbitrary historical ref. A later rerun must not silently be presented as the old qualification. For replay, compare the corpus digest, not complete reports containing run-specific time and identifiers.

### Show / navigate

Open supplied sources/qualification.json: readbacks, early_and_late_rejection, archive_sha256. Inspect readback() and its actual assertions.

- [`scripts/qualify_submission.py::readback` — L80–L134](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/qualify_submission.py#L80-L134)
- [`scripts/qualify_submission.py::qualify` — L137–L314](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/qualify_submission.py#L137-L314)

**Selected fields from the supplied historical receipt, not a raw runtime report:**

```json
{
  "source_commit": "0375af56bf681e9441edcb7433cfe58951db77b2",
  "readbacks": [
    {
      "formats": [
        "people.csv",
        "people.json",
        "people.sqlite",
        "people.txt"
      ],
      "corpus_sha256": "15e98e6b6c85720a9e6a88f8b85a3239ac577a4392e89160b10bf7ed0a49414c",
      "report_sha256": "1c247be72a32cc0a23979059ab77710733de508573897dc4b3814e5b060439dc",
      "schema_validated": true
    },
    {
      "formats": [
        "people.csv",
        "people.json",
        "people.sqlite",
        "people.txt"
      ],
      "corpus_sha256": "15e98e6b6c85720a9e6a88f8b85a3239ac577a4392e89160b10bf7ed0a49414c",
      "report_sha256": "f557790f6f6a55f0adea08fd5cd0a2850dcf9216462072011cd92e145eb7d9ec",
      "schema_validated": true
    }
  ],
  "source_unchanged": true,
  "early_and_late_rejection": true
}
```

**Visible qualification:** Supplied receipt inspected; the application, pytest and Docker were not rerun here.

**Evidence IDs:** E01, E06

**Transition:** Now the pipeline map explains where those checks fit.

<a id="r07-pipeline-map"></a>
## r07-pipeline-map — Transformation and release are separate steps

**Time:** 07:00–07:45. **Block:** How the Solution Works. **Primary questions:** None; navigation or paired lead-in.

### Say

This is the whole local path. Validate the policy and inventory, transform each supported format into private staging, reread and verify the corpus, then publish the report last.
The stage is on the output filesystem so publication can use a same-filesystem rename. Permissions restrict access, but they do not turn the filesystem into an encrypted or hostile-host-proof store. The pipeline checks source digests again and computes the output seal after verification.
Keep this map as orientation. The next pages each explain one decision rather than turning this into a single dense architecture slide. The cloud design will use different execution machinery; it must retain the same meaning of identity and readiness.

### Show / navigate

Trace run_pipeline() calls without opening every branch.

- [`src/anonymization_trial/pipeline.py::run_pipeline` — L214–L258](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L214-L258)
- [`src/anonymization_trial/formats.py::transform_file` — L39–L49](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/formats.py#L39-L49)
- [`src/anonymization_trial/verification.py::verify_corpus` — L205–L249](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L205-L249)
- [`src/anonymization_trial/pipeline.py::_publish` — L166–L211](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L166-L211)

**Visible qualification:** Shared primitives and trusted single-writer staging; no production streaming.

**Evidence IDs:** E08

<a id="r08-policy"></a>
## r08-policy — The policy supplies authority—not a guess

**Time:** 07:45–09:00. **Block:** How the Solution Works. **Primary questions:** Q05, Q11, Q33

### Say

For the running example, the policy explicitly states that Alice and A.L belong to one subject. The compiler can validate that declaration and reject contradictory match domains; it cannot determine whether the author has correctly identified the people.
It also requires both sensitive_values and protected_values. A missing sensitive list must not silently become a successful no-op. For protected text such as KEEP, the preservation promise is unconditional. When a sensitive literal equals, contains, or can partially intersect a protected literal, compilation rejects rather than selecting a convenient winner.
That overlap rule is deliberately conservative and can reject a policy even before a conflicting occurrence is encountered. A more context-sensitive exception would require a different explicit contract. The filesystem admission checks similarly reject unsafe inputs before transformation. None of those checks expands the engine into automatic detection.

### Show / navigate

compile_policy() L129–164, then _check_overlap() L110–126. Explain required arrays and one overlap decision.

- [`src/anonymization_trial/policy.py::compile_policy` — L129–L164](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L129-L164)
- [`src/anonymization_trial/policy.py::_check_overlap` — L110–L126](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L110-L126)
- [`src/anonymization_trial/pipeline.py::_preflight` — L80–L116](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L80-L116)

**Exact source excerpt (context shown in the pinned link):**

```python
def compile_policy(payload: object) -> Policy:
    """Validate a policy payload strictly and compile its matcher."""
    _require(isinstance(payload, dict), AnonErrorCode.INVALID_POLICY, "policy is not an object")
    version = payload.get("version")
```

**Visible qualification:** A valid policy is not proof that its identity assignments are true.

**Evidence IDs:** E08

<a id="r09-identity"></a>
## r09-identity — Aliases converge because identity is declared

**Time:** 09:00–10:45. **Block:** How the Solution Works. **Primary questions:** Q07, Q08, Q09, Q31, Q32

### Say

Alice and A.L converge because Rule.identity returns the same pair: name and person-a. Bob belongs to a different canonical identity and receives a distinct replacement within that type. A name and an email for one subject need not display the same token; the type is part of the derivation.
When subject_id is absent, rule_id is the fallback. Renaming that fallback can therefore change the identity input. policy_version is schema version one, not an incrementing revision counter for every policy edit. The full policy digest is recorded for provenance, not used as the pseudonym seed.
The allocator sorts the identity set, detects per-type collisions, and changes the salt or rejects exhaustion. This is deterministic for the same plan. Adding distinct identities can alter collision assignments, so arbitrary policy growth is not promised to preserve all old values. The public salt resolves allocation; it is not a secret. These distinctions matter before we propose distributing work over independent workers.

### Show / navigate

Rule.identity L38–40 → _digest L41–43 → build_replacements L62–104. Code navigation, not a breakpoint.

- [`src/anonymization_trial/policy.py::Rule.identity` — L38–L40](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L38-L40)
- [`src/anonymization_trial/pseudonyms.py::_digest` — L41–L43](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pseudonyms.py#L41-L43)
- [`src/anonymization_trial/pseudonyms.py::build_replacements` — L62–L104](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pseudonyms.py#L62-L104)

**Exact source excerpt (context shown in the pinned link):**

```python
    @property
    def identity(self) -> CanonicalIdentity:
        return (self.data_type, self.subject_id or self.rule_id)
```

**Visible qualification:** Public unkeyed namespace; stable allocation assumes the same identity set.

**Evidence IDs:** E08

<a id="r10-spans"></a>
## r10-spans — Select original spans; emit only once

**Time:** 10:45–12:15. **Block:** How the Solution Works. **Primary questions:** Q10, Q41

### Say

Use the same original sentence: Alice and A.L met Bob, followed by KEEP. The matcher collects spans over that original decoded text, chooses non-overlapping spans, and emits each replacement once.
The precedence is earliest start, then the longest match at that start, then stable rule ID. It is not a rule that the globally longest name always wins. The selected replacement is appended to a separate output list. It is never fed back into a chain of text.replace calls that could rewrite newly generated text.
This mechanism is separate from the final residual check. A generated token that contains a sensitive literal can still cause refusal; no-cascade is not a promise to publish every possible policy. Case-sensitive matching uses exact code points, and accepted insensitive rules use ASCII lowering without Unicode normalization. Deeper Unicode distinctions stay in the appendix rather than changing the matching promise on this slide.

### Show / navigate

Matcher.replace L120–131; point to source slices and replacement append. _select L134–145 defines precedence.

- [`src/anonymization_trial/matcher.py::Matcher.replace` — L120–L131](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/matcher.py#L120-L131)
- [`src/anonymization_trial/matcher.py::_select` — L134–L145](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/matcher.py#L134-L145)

**Exact source excerpt (context shown in the pinned link):**

```python
        cursor = 0
        for span in spans:
            out.append(text[cursor:span.start])
            out.append(span.replacement)
            cursor = span.end
        out.append(text[cursor:])
        return "".join(out), len(spans)
```

**Visible qualification:** No cascade does not guarantee every policy can publish; residuals may reject.

**Evidence IDs:** E08

<a id="r11-formats"></a>
## r11-formats — Preserve logical meaning—not identical serialization

**Time:** 12:15–13:30. **Block:** How the Solution Works. **Primary questions:** Q38, Q39, Q40

### Say

Each format needs a definition of preservation. CSV headers and ordered cells are logical data; quoting may be normalized. JSON keys and structure are preserved while string values are transformed; formatting and original numeric spelling are not the promise. Text is decoded strictly as UTF-8, and the adapter preserves its BOM handling.
SQLite is not edited as a bag of bytes. The adapter works on a snapshot, updates supported text cells, and checks relationships, counts and integrity. The later verifier compares logical schema and row values. Unsupported constructs are rejected rather than given a best-effort rewrite.
That distinction also prevents an overclaim about generated columns: the writer skips them, while the oracle still checks the resulting values. For all four formats, the running example is the same—change the declared name value, preserve its association and KEEP, and refuse when the supported contract cannot be maintained.

### Show / navigate

transform_file L39–49 dispatch; _verify_sqlite_locations L64–126 for logical rather than physical preservation.

- [`src/anonymization_trial/formats.py::transform_file` — L39–L49](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/formats.py#L39-L49)
- [`src/anonymization_trial/verification.py::_verify_sqlite_locations` — L64–L126](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L64-L126)

**Exact source excerpt (context shown in the pinned link):**

```python
def transform_file(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == ".csv":
        return _transform_csv(source, destination, policy)
```

**Visible qualification:** Bounded subsets; JSON formatting, CSV quoting and SQLite pages need not match bytes.

**Evidence IDs:** E08

<a id="r12-typed-locations"></a>
## r12-typed-locations — A correct value on the wrong row is still wrong

**Time:** 13:30–15:00. **Block:** How the Solution Works. **Primary questions:** Q12

### Say

Removing Alice and Bob is not enough. Swap their valid pseudonyms between rows and the names still disappear, counts still match, and the files still parse. The output now associates the wrong person with each record.
The verifier reconstructs expected values at corresponding locations. It compares CSV rows and cells, JSON nodes and list positions, text content, and SQLite rows with logical schema checks. It also distinguishes types. Python considers True equal to 1 and 1 equal to 1.0; the preservation contract cannot accept those substitutions automatically.
The exact type check is small, but the test must construct the mutation correctly. The SQLite type regression avoids affinity coercing the real value back to an integer before the checker sees it. That is useful evidence about the oracle, not just a test name. Rereading catches output faults; it does not remove common-mode defects in the shared matcher and replacement allocator. I’ll defend that tradeoff explicitly in the prepared question block.

### Show / navigate

Show _typed_equal L129–143 and one corresponding location comparison. Optional appendix: the real mutation test, not a new test run.

- [`src/anonymization_trial/verification.py::_typed_equal` — L129–L143](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L129-L143)
- [`src/anonymization_trial/verification.py::_verify_locations` — L151–L184](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L151-L184)
- [`src/anonymization_trial/verification.py::_verify_sqlite_locations` — L64–L126](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L64-L126)
- [`security/tests/test_typed_scalar_verification.py::test_json_bool_number_and_sqlite_integer_real_mutations_rejected` — L21–L48](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/security/tests/test_typed_scalar_verification.py#L21-L48)

**Exact source excerpt (context shown in the pinned link):**

```python
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_typed_equal(a[k], b[k]) for k in a)
```

**Visible qualification:** Independent reread / re-derivation; replacement primitives remain shared.

**Evidence IDs:** E06, E08

<a id="r13-publication"></a>
## r13-publication — The marker—not the directory—authorizes use

**Time:** 15:00–16:30. **Block:** How the Solution Works. **Primary questions:** Q13, Q14, Q37

### Say

Publication begins by invalidating an old readiness marker before changing the corpus. It compares the staged digest, moves the staged corpus, writes the report through a temporary file, and renames report.json last.
The report writer advances by the number of bytes os.write actually returns. It completes partial progress and rejects zero progress before a new marker is committed. Sync operations support the intended ordering; they do not establish that every device and power-loss sequence has been tested.
This is a readiness protocol, not one atomic transaction over every file. Corpus bytes can exist without a marker after a failure, and a preflight rejection can leave an earlier valid release alone. Once publication begins there is no unconditional rollback promise. The pipeline also computes the seal after verification: verification_sha256 is not a separately signed verifier receipt. A consumer that ignores the marker and trusted digest reference is outside the intended usage.

### Show / navigate

Walk _publish L166–211 from marker removal to final rename; do not run fault injection during the talk.

- [`src/anonymization_trial/pipeline.py::_publish` — L166–L211](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L166-L211)
- [`src/anonymization_trial/pipeline.py::run_pipeline` — L214–L258](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L214-L258)

**Exact source excerpt from `_publish`:**

```python
        remaining = memoryview(data)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("report write made no progress")
            remaining = remaining[written:]
        os.fsync(fd)
```

**Visible qualification:** Report-last is not full rollback, a signed attestation, or exhaustive crash proof.

**Evidence IDs:** E08

<a id="r14-cloud"></a>
## r14-cloud — Distribute the work; retain one corpus decision

**Time:** 16:30–18:00. **Block:** How the Solution Works. **Primary questions:** Q24, Q25, Q27

### Say

The assignment required a terabyte and petabyte design; it is not Extra Credit. The worked proposal uses S3 boundaries for intake, work, release and quarantine; queue-driven dispatch; and a bounded Fargate or Batch worker pool.
Workers may finish at different times. Their individual success must not expose a partial corpus as a finished release. The proposed coordinator waits for verification of the expected object set, writes an immutable manifest, then switches an active pointer. Consumer permissions and the pointer protocol matter; objects are not magically invisible because the diagram says staging.
Partition boundaries must respect formats. CSV records can span newlines, and text needs safe encoding and match-overlap ownership. Ordinary JSON and SQLite are whole-document or snapshot work in the design. Every worker also needs the same versioned identity and collision plan. A common HMAC key alone does not coordinate allocations over different identity subsets. Deterministic content helps retries, but it is not an exactly-once distributed commit protocol.

### Show / navigate

Pinned docs/production-architecture.md; connect local build_replacements to common-plan requirement. No Archify/React Flow/GSN integration claim.

- [`src/anonymization_trial/pseudonyms.py::build_replacements` — L62–L104](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pseudonyms.py#L62-L104)

**Visible qualification:** PROPOSED cloud behavior. The local code does not implement this orchestration.

**Evidence IDs:** E07, E08

<a id="r15-capacity"></a>
## r15-capacity — The SLA is a scenario—not a benchmark

**Time:** 18:00–19:00. **Block:** How the Solution Works. **Primary questions:** None; navigation or paired lead-in.

### Say

The capacity arithmetic uses 200 workers, each assumed to sustain 20 million bytes per second. That gives four billion bytes per second of ideal transform capacity, before verification, retries and scheduling overhead.
The committed estimator includes its two-pass compute factor and retry fraction. Its modeled wall times are 0.14 hours for one TB and 141.67 hours for one PB at this pool. The design targets verified publication within one hour and seven days respectively. Those are design targets under workload assumptions, not observed service levels.
The first measurement exercise would replace the assumed throughput, file-size distribution, memory, stragglers and quota availability with representative data. The small recorded demo shown earlier is not the basis for claiming petabyte throughput. We keep the two evidence types visibly separate.

### Show / navigate

costs/example-estimates.json and _one(); source formula is in the appendix.

- [`scripts/estimate_aws_cost.py::_one` — L23–L75](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/estimate_aws_cost.py#L23-L75)

**Committed modeled output:**

| Scenario | Modeled wall hours | Design target |
|---|---:|---|
| 1 TB (10^12 bytes) | 0.14 | ≤1 hour |
| 1 PB (10^15 bytes) | 141.67 | ≤7 days |

**Visible qualification:** MODELED: 1 TB / 1 PB targets. No TB/PB execution was performed.

**Evidence IDs:** E07

<a id="r16-cost"></a>
## r16-cost — Retention dominates this 1 PB cost scenario

**Time:** 19:00–20:15. **Block:** How the Solution Works. **Primary questions:** Q47

### Say

The supplied analytics description saw eight component rows: four for one TB and four for one PB. A pooled histogram or mean would not answer a useful engineering question. This chart selects the one-PB scenario and compares its four components on a zero-based dollar axis.
Storage is sixty-nine thousand dollars because the model retains three copies for one month at the stated first-tier rate. The committed total is $85,733.90; the one-TB total is $85.73. Individual displayed components are rounded, so summing them can differ by one cent from the unrounded total.
Object count is a major sensitivity. The committed one-tenth-file-size case rises to $223,749.65 for one PB. Output expansion, transfer charges, key rental, log retention, discounts and a complete API operation trace are not all priced. The figure includes its actual rows, filter and reproduction spec. It was authored from the supplied model—not generated by a newly successful analytics or create-figure run.

### Show / navigate

Open assets/figures/cost-components-1pb.spec.json; inspect _one and the normalized rows only if challenged.

- [`scripts/estimate_aws_cost.py::_one` — L23–L75](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/estimate_aws_cost.py#L23-L75)
- [`scripts/estimate_aws_cost.py::_sensitivity` — L78–L86](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/estimate_aws_cost.py#L78-L86)

**Figure provenance:** [row data](sources/cost-rows.json), [spec](assets/figures/cost-components-1pb.spec.json), [create-figure metrics input](assets/figures/cost-components-1pb.metrics.json), [supplied describe](sources/analytics-describe.txt).

The optional local create-figure command in the spec has **NOT_RUN** status. Its interface comes from supplied guidance; it was not used to claim a rendered compiler result.

**Visible qualification:** MODELED USD, price date 2026-09-04. Illustrative, not a billing quote.

**Evidence IDs:** E07

<a id="r17-disclosure"></a>
## r17-disclosure — Technical readiness does not waive the timebox

**Time:** 20:15–21:00. **Block:** How the Solution Works. **Primary questions:** Q28, Q29, Q30

### Say

Before defending the choices, I want the administrative boundary explicit. SUBMISSION.md records post-timebox corrections and later requested additions. Active engineering time was not separately tracked. The retrospective allocation totals eight hours, but it is not an instrumented proof that the stop instruction was satisfied.
The work was AI-assisted and externally reviewed; I will not invent an authorship percentage. The technical conclusion concerns a bounded mechanism and its evidence. It does not establish general anonymity, production deployment, or complete resistance to linkage. The next three prepared questions explain why these boundaries are deliberate, rather than quietly treating every future hardening idea as a missing local feature.

### Show / navigate

SUBMISSION.md: Time spent, Retrospective time estimate, Unfinished work.


**Visible qualification:** Post-timebox corrections and operator-requested additions remain separate.

**Evidence IDs:** E04, E08

<a id="r18-question-exact"></a>
## r18-question-exact — Question 1

**Time:** 21:00–21:15. **Block:** Prepared Adversarial Questions. **Primary questions:** None; navigation or paired lead-in.

### Say

The first skeptical question is whether an explicit policy is avoiding the hard detection problem. Why choose exact policy rather than automatic identification of every sensitive value?

- [`src/anonymization_trial/policy.py::compile_policy` — L129–L164](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L129-L164)

**Visible qualification:** An accepted policy is not proof of completeness or real-world identity truth.

**Evidence IDs:** E08

<a id="r19-answer-exact"></a>
## r19-answer-exact — Explicit policy separates authority from guessing

**Time:** 21:15–22:00. **Block:** Prepared Adversarial Questions. **Primary questions:** Q01, Q02, Q03

### Say

The bounded answer is that the policy defines a falsifiable transformation obligation. The compiler rejects ambiguity and the output checker can reconstruct expected values. A detection model would add another uncertainty: what it failed to identify, and whether a proposed alias really belongs to that person.
That does not make custom matching universally better or a PII platform unnecessary. It makes the submitted guarantee explicit. The later discovery workflow proposes aliases without silently authorizing a change; operator approval creates an exact policy and the normal release path still verifies. It is a constrained convenience, not a retroactive claim of complete detection.

### Show / navigate

compile_policy() and approve() are the evidence; no generic platform comparison claim.

- [`src/anonymization_trial/policy.py::compile_policy` — L129–L164](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L129-L164)
- [`src/anonymization_trial/discovery.py::approve` — L329–L378](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L329-L378)

**Visible qualification:** An accepted policy is not proof of completeness or real-world identity truth.

**Evidence IDs:** E08

<a id="r20-question-verifier"></a>
## r20-question-verifier — Question 2

**Time:** 22:00–22:15. **Block:** Prepared Adversarial Questions. **Primary questions:** None; navigation or paired lead-in.

### Say

The second question challenges the checker itself. If the verifier calls the same replacement primitives, aren’t we asking the transformer to certify its own mistake?

- [`src/anonymization_trial/verification.py::verify_corpus` — L205–L249](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L205-L249)

**Visible qualification:** Independent reread / re-derivation—not a separately implemented engine.

**Evidence IDs:** E08

<a id="r21-answer-verifier"></a>
## r21-answer-verifier — Rereading helps; common-mode risk remains

**Time:** 22:15–23:00. **Block:** Prepared Adversarial Questions. **Primary questions:** Q04

### Say

The verifier rereads both corpora and does not trust transformation counters or a success Boolean. It detects wrong output locations, scalar types, file sets and supported schema changes. Those are meaningful distinctions demonstrated by deliberate output mutations.
But the expected replacement path shares matcher and pseudonym primitives. A common defect can affect both sides. The qualification checker adds an independent expectation for a small synthetic fixture, not universal reference verification. A diverse implementation could increase assurance, but it is disclosed production hardening rather than a capability we pretend was built. The answer is qualified independence, not a slogan that the transformer can never certify itself.

### Show / navigate

verify_corpus imports replace_text/build_replacements; readback() has its own synthetic expectation.

- [`src/anonymization_trial/verification.py::verify_corpus` — L205–L249](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L205-L249)
- [`scripts/qualify_submission.py::readback` — L80–L134](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/qualify_submission.py#L80-L134)
- [`src/anonymization_trial/verification.py::_typed_equal` — L129–L143](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L129-L143)

**Visible qualification:** Independent reread / re-derivation—not a separately implemented engine.

**Evidence IDs:** E06, E08

<a id="r22-question-scale"></a>
## r22-question-scale — Question 3

**Time:** 23:00–23:15. **Block:** Prepared Adversarial Questions. **Primary questions:** None; navigation or paired lead-in.

### Say

The third question is whether the cloud slide is measured engineering or just multiplication. What must change at petabyte scale, and what do these cost and capacity numbers actually establish?

- [`scripts/estimate_aws_cost.py::_one` — L23–L75](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/estimate_aws_cost.py#L23-L75)

**Visible qualification:** No deployment, measured SLA, or complete invoice-level cost accounting.

**Evidence IDs:** E07

<a id="r23-answer-scale"></a>
## r23-answer-scale — The model exposes assumptions; it does not validate them

**Time:** 23:15–24:00. **Block:** Prepared Adversarial Questions. **Primary questions:** Q26

### Say

The model establishes reproducible arithmetic for a stated workload, not operational delivery. The execution topology must change: bounded workers, format-aware partitions, replay and one corpus-level manifest/pointer commit.
The retained semantics are the important part. Workers cannot allocate collision plans over inconsistent identity sets, and per-file success cannot authorize a partial corpus. Measurements must replace assumptions about throughput, skew, memory, requests and quotas before offering an SLA.
That finishes the three prepared objections. The remaining substantive material is explicitly Extra Credit: the additional security evidence and post-trial operator interfaces. Audience discussion remains a separate block after those additions.

### Show / navigate

Point to the model inputs and shared plan, then advance directly into Extra Credit.

- [`scripts/estimate_aws_cost.py::_one` — L23–L75](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/scripts/estimate_aws_cost.py#L23-L75)
- [`src/anonymization_trial/pseudonyms.py::build_replacements` — L62–L104](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pseudonyms.py#L62-L104)

**Visible qualification:** No deployment, measured SLA, or complete invoice-level cost accounting.

**Evidence IDs:** E07, E08

<a id="r24-security-evals"></a>
## r24-security-evals — Security evals test different failure surfaces

**Time:** 24:00–25:15. **Block:** Extra Credit. **Primary questions:** None; navigation or paired lead-in.

### Say

Extra Credit begins with the security methodology—not a larger feature surface. White-box means source-aware inspection and static analysis. Gray-box means knowledge of the contracts and deliberately chosen inputs or mutations. Black-box means exercising the CLI and observing external effects. These are test perspectives, not attacker identities or a guarantee of coverage.
The static receipt supports Bandit evidence with findings and their disposition; it must not be marketed as an all-scanner clean bill. Semgrep scanned zero target files, and no dependency-SCA receipt is committed. The retained source and CLI tests are more directly relevant to the anonymization contract than a scanner count.
The important question is what an oracle catches: a swapped value, a forbidden write, a stale proposal, or an invalid readiness artifact. We have already inspected concrete examples. This slide groups the evidence without upgrading any fixture or count into exhaustive security.

### Show / navigate

Security/SECURITY.md and retained scanner receipt; no new scans. The exact TOC label is Security Evals (White, Grey, Black, and Adaptive Lineage).

- [`security/tests/test_typed_scalar_verification.py::test_json_bool_number_and_sqlite_integer_real_mutations_rejected` — L21–L48](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/security/tests/test_typed_scalar_verification.py#L21-L48)
- [`tests/test_discovery_boundaries.py::test_work_artifacts_cannot_enter_release_via_relative_or_symlink_paths` — L180–L244](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/tests/test_discovery_boundaries.py#L180-L244)

**Visible qualification:** Bandit evidence only. Semgrep: zero target files. No SCA receipt.

**Evidence IDs:** E06, E09

<a id="r25-lineage"></a>
## r25-lineage — The retained Judge result is fixture-backed

**Time:** 25:15–26:00. **Block:** Extra Credit. **Primary questions:** None; navigation or paired lead-in.

### Say

The Adaptive Lineage part of the contents needs a precise qualification. The retained Battle receipt describes local deterministic fixture execution. It records agentic false, no models used, and a fixture_contract_proof scope.
That is useful as a demonstration of the judge-and-receipt contract, but not evidence that adaptive red and blue agents attacked this repository, learned over rounds, or established security. The non-claims explicitly say those things were not proved. A future useful finding should become a small deterministic regression; this deck does not reopen that future campaign or claim that it has already happened.

### Show / navigate

security/battle/run-receipt.json: claim_scope and execution; no target campaign inference.


**Exact selected fields of the retained receipt:**

```json
{
  "claim_scope": "fixture_contract_proof",
  "execution": {
    "agentic": false,
    "live": "local_deterministic_fixture",
    "mocked": false,
    "models_used": []
  },
  "schema": "battle.run_receipt.v1",
  "status": "PASS",
  "verdict": "BLUE_SUCCESS"
}
```

[Complete pinned receipt](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/security/battle/run-receipt.json). No live adaptive target campaign is inferred.

**Visible qualification:** Fixture contract proof—not an adaptive live campaign against this target.

**Evidence IDs:** E10

<a id="r26-wrapper"></a>
## r26-wrapper — The skill delegates; it does not fork the engine

**Time:** 26:00–27:00. **Block:** Extra Credit. **Primary questions:** Q06

### Say

The thin anonymize-data skill makes the canonical project easier to invoke. For workflows we expect to reuse, the pattern is a concise SKILL.md contract, thin delegation in run.sh, and retained behavioral checks following best-practices-skills. We do not duplicate the engine or build/install the wrapper during the presentation. It accepts a supported file or folder plus a separate policy and output location, then uses the project’s installed CLI. Matching, adapters, verification, and errors remain owned by the project.
The wrapper clears conflicting environment variables and checks the imported package location against the selected checkout. Its retained sanity workflow includes a wrong-install refusal and runs the same project tests through the wrapper. That is a focused installation boundary, not another engine or service platform.
This was requested after the original qualified trial candidate. The older archive and PASS were not relabeled as proof of the extension. The Docker interface remains self-contained, while the skill is an operator convenience with its own scoped evidence.

### Show / navigate

Project input_bundle()/main(); wrapper is documented and its execution evidence is separately pinned in the source manifest.

- [`src/anonymization_trial/bundle.py::input_bundle` — L40–L71](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/bundle.py#L40-L71)
- [`src/anonymization_trial/__main__.py::main` — L207–L233](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/__main__.py#L207-L233)

```bash
./run.sh --input exports --policy policy.json --output release
```

Example from the shared skill directory; source paths are operator-supplied. This is not another engine or a successful command executed here.

**Visible qualification:** Post-trial integration. The evaluator image does not require the shared skill.

**Evidence IDs:** E02, E08

<a id="r27-discovery"></a>
## r27-discovery — A proposed alias does not authorize release

**Time:** 27:00–28:30. **Block:** Extra Credit. **Primary questions:** Q19, Q20, Q21, Q34, Q35, Q36

### Say

Continue the same person-a example with the observed spelling Alicee. Discovery compares whole structured string values or text lines against eligible name rules. It ranks distinct identities, refuses ties and insufficient separation, and emits private proposals. The default score threshold and margin are not probabilities of identity.
Without approval, the exact Alice substring can already match inside Alicee and leave a trailing e. Approval adds the longer literal Alicee for the same canonical subject. It does not switch default anonymization into fuzzy replacement.
Approval requires explicit unique candidate IDs, re-derives the supplied report against the current source and valid supplied settings, and invokes the real policy compiler before writing. A self-consistent report is not a cryptographic signature or authenticated human consent. The operator owns that decision.
The resulting rule is global literal matching, not a row-only permission. Protected overlaps still reject, and a subsequent pipeline run must transform and verify before release. Discovery and approval receipts stay release_ready false. The private artifact boundary on the next page is what prevents those raw aliases entering a READY release.

### Show / navigate

approve() L329–378 and the all-four-format alias test. No live fuzzy scoring or probability claim.

- [`src/anonymization_trial/discovery.py::discover` — L222–L309](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L222-L309)
- [`src/anonymization_trial/discovery.py::approve` — L329–L378](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L329-L378)
- [`src/anonymization_trial/discovery.py::write_private` — L312–L326](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L312-L326)
- [`tests/test_discovery.py::test_discover_approve_and_anonymize_all_four_formats` — L64–L137](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/tests/test_discovery.py#L64-L137)

**Exact source excerpt (context shown in the pinned link):**

```python
def approve(bundle: Path, review_path: Path, ids: list[str], output: Path, *inputs: Path) -> dict:
    output = separate_output(output, bundle, review_path, *inputs)
    receipt_path = separate_output(
        output.with_name(output.name + ".approval.json"), bundle, review_path, output, *inputs
    )
```

**Visible qualification:** Whole-value proposals; score ≠ probability. Approval adds a global literal rule.

**Evidence IDs:** E02, E06, E08

<a id="r28-canonical-path"></a>
## r28-canonical-path — Validate the destination that will actually be written

**Time:** 28:30–30:00. **Block:** Extra Credit. **Primary questions:** Q15, Q16, Q17, Q18

### Say

The concrete extension defect was not in the similarity scorer. A relative review path from inside release/corpus, or a symlink alias to it, could evade a check that walked lexical parents even though another check had resolved the destination. The write and validation disagreed about location.
The fix returns a validated canonical path and carries it into writing. The CLI assigns that path to its output argument. Approval validates both the new policy and the sibling receipt before either is created. Exclusive creation and mode 0600 remain useful, but neither can substitute for keeping raw-name work outside a release.
The retained regression creates a real READY release, compares its complete file-path-to-bytes snapshot after denied writes, and includes successful equivalent private-work controls. It also checks a receipt-only symlink. The previous bounded reviewer closed that demonstrated blocker by inspecting the source and regression, not by personally running Docker.
This is the last substantive prepared page. The restriction remains trusted single-writer operation, not protection against a hostile concurrent filesystem mutator. We now move to your questions, not another prepared feature or recap.

### Show / navigate

separate_output L22–37 → main caller → approve receipt path → path regression L180–244. Use 25–30 seconds for navigation inside this slot.

- [`src/anonymization_trial/bundle.py::separate_output` — L22–L37](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/bundle.py#L22-L37)
- [`src/anonymization_trial/discovery.py::approve` — L329–L378](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L329-L378)
- [`src/anonymization_trial/discovery.py::write_private` — L312–L326](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L312-L326)
- [`tests/test_discovery_boundaries.py::test_work_artifacts_cannot_enter_release_via_relative_or_symlink_paths` — L180–L244](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/tests/test_discovery_boundaries.py#L180-L244)

**Exact source excerpt (context shown in the pinned link):**

```python
    if any(
        (parent / "report.json").is_file() and (parent / "corpus").is_dir()
        for parent in out.parents
    ):
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "work artifacts must stay outside a release")
    return out
```

**Visible qualification:** Bounded source-review closure; trusted single writer. Not race-proof traversal.

**Evidence IDs:** E02, E04, E06, E08

<a id="r29-discussion"></a>
## r29-discussion — Discussion

**Time:** 30:00–45:00+ audience reserve. **Block:** Discussion. **Primary questions:** Q48

### Say

The prepared walkthrough is complete. Which decision or boundary would you like to inspect? I’ll follow the question to the pinned code, the corresponding evidence, or the explicit limit, rather than repeat the whole presentation.

### Show / navigate

Use the 48-question appendix as permitted preparation/reference only. No automatic candidate-answer assistance or recording. Follow formal-assessment rules and obtain explicit consent.


**Visible qualification:** Audience reserve: 15+ minutes, separate from the prepared 30.

**Evidence IDs:** E08

<a id="r30-thank-you"></a>
## r30-thank-you — Thank you

**Time:** After discussion; end playback. **Block:** Thank you. **Primary questions:** None; navigation or paired lead-in.

### Say

Thank you for the discussion.

### Show / navigate

End normal playback. No substantive slide follows. Backup questions are Markdown appendix material, not appended playback slides.


**Evidence IDs:** Procedural close only.

<a id="adversarial-question-bank"></a>
## Appendix — 48 preserved questions and follow-ups

**Not in normal slide playback.** The three prepared objections do not require reading this bank. These are the existing Q01–Q48 questions and answer texts, preserved without renumbering or rewriting. The primary slide map is new; the legacy section remains traceable. Questions are plausible preparation material, not predictions of the interview.

### Q01 — Is this actually anonymization?

**Primary slide:** [r19-answer-exact](#r19-answer-exact) · **Legacy section:** `01-brief`

**Short answer:** It is deterministic, policy-bounded pseudonymization with preservation and release checks.

**Follow-up / deeper answer:** **“Then why is publication safe?”** The technical release decision is relative to the declared policy and supported formats. It does not replace an assessment of policy completeness or residual privacy risk.

**Original code/evidence references:** [`compile_policy`][C01]; [scope disclosures][D01]

### Q02 — What happens to a name absent from the policy?

**Primary slide:** [r19-answer-exact](#r19-answer-exact) · **Legacy section:** `01-brief`

**Short answer:** There is no general discovery promise. An existing literal may still match a substring.

**Follow-up / deeper answer:** **“Will discovery find a name in a paragraph?”** It compares the whole line, not extracted name spans. Most narrative lines will not qualify as name-shaped candidates; no general entity detector is implemented.

**Original code/evidence references:** [`Matcher.replace`][C04]; [`_strings`, `_name`, `discover`][C12]

### Q03 — Why not use an existing PII platform?

**Primary slide:** [r19-answer-exact](#r19-answer-exact) · **Legacy section:** `01-brief`

**Short answer:** This implementation makes a narrow transformation contract easy to inspect; that is a tradeoff, not proof that custom code is superior.

**Follow-up / deeper answer:** **“Did stdlib-only increase your risk?”** It leaves ownership of the matcher here and requires strong tests. The brief permits packaged dependencies. I am not claiming a comparative platform evaluation that was not performed.

**Original code/evidence references:** [Brief][D00]; [`Matcher`, `_Aho`][C04]; [implementation choices][D01]

### Q04 — Why isn’t a successful transform enough?

**Primary slide:** [r21-answer-verifier](#r21-answer-verifier) · **Legacy section:** `02-architecture`

**Short answer:** Parsing and transformation can succeed while values or associations are wrong. Verification precedes publication.

**Follow-up / deeper answer:** **“Is the verifier independent?”** It rereads and reconstructs, but shares matcher and pseudonym primitives. It can catch injected output faults without eliminating common-mode implementation errors.

**Original code/evidence references:** [`run_pipeline`][C02]; [`verify_corpus`][C13]

### Q05 — Are inputs protected only by Docker’s read-only mount?

**Primary slide:** [r08-policy](#r08-policy) · **Legacy section:** `02-architecture`

**Short answer:** That mount is one assumption. Preflight checks paths, and the pipeline compares source digests before publication.

**Follow-up / deeper answer:** **“Can a hostile host swap bytes and restore them?”** That is outside the local threat model. The post-trial interface also checks copies against originals, but neither mechanism is a hostile-host immutable snapshot service.

**Original code/evidence references:** [`_preflight`][C14]; [`run_pipeline`][C02]; [`input_bundle`][C25]

### Q06 — Why create another skill?

**Primary slide:** [r26-wrapper](#r26-wrapper) · **Legacy section:** `02-architecture`

**Short answer:** It exposes the project CLI; it is not another matching or verification engine.

**Follow-up / deeper answer:** **“What prevents a wrong installation?”** The wrapper workflow includes package-location checking and a retained wrong-install control. That evidence is separate from the default Docker interface, which does not require the skill.

**Original code/evidence references:** [Interface documentation][D06]; [`main`][C15]; [retained wrapper evidence][E02]

### Q07 — Why do aliases share a pseudonym?

**Primary slide:** [r09-identity](#r09-identity) · **Legacy section:** `03-semantics`

**Short answer:** They share the policy’s canonical type/identity key.

**Follow-up / deeper answer:** **“What makes that identity assignment true?”** The policy author or approving operator supplies that authority. The compiler enforces consistency, not real-world identity truth. Similarity alone is insufficient.

**Original code/evidence references:** [`Rule.identity`, `compile_policy`][C01]; [`build_replacements`][C03]

### Q08 — Can two identities collide?

**Primary slide:** [r09-identity](#r09-identity) · **Legacy section:** `03-semantics`

**Short answer:** Candidate replacements can collide; allocation checks per-type distinctness and searches again or rejects.

**Follow-up / deeper answer:** **“Will adding identities preserve existing values?”** Not unconditionally. Sorted allocation can assign a different salt when the identity set changes. Stable retries require the same plan; evolving policies need explicit lifecycle decisions.

**Original code/evidence references:** [`build_replacements`][C03]

### Q09 — Is the SHA-256 pseudonym secret?

**Primary slide:** [r09-identity](#r09-identity) · **Legacy section:** `03-semantics`

**Short answer:** No. The namespace is public and derivation inputs may be guessable.

**Follow-up / deeper answer:** **“What would a key change?”** A keyed construction changes an attacker’s ability to recompute guesses without the key. It does not remove contextual linkage, prove anonymity, or coordinate collision allocation by itself.

**Original code/evidence references:** [`_digest`, `KEY_MODE`][C03]; [privacy posture][D01]

### Q10 — What happens when literals overlap?

**Primary slide:** [r10-spans](#r10-spans) · **Legacy section:** `03-semantics`

**Short answer:** Selection is earliest start, longest at that start, then stable rule ID. Emission uses original-input spans.

**Follow-up / deeper answer:** **“Can replacement text trigger another rule?”** Not during emission. The residual verifier can still refuse generated text containing a sensitive literal. No-cascade semantics and successful publishability are different conditions.

**Original code/evidence references:** [`_select`, `Matcher.replace`][C04]; [`verify_corpus`][C13]

### Q11 — What if a protected phrase contains a sensitive name?

**Primary slide:** [r08-policy](#r08-policy) · **Legacy section:** `03-semantics`

**Short answer:** The policy is rejected rather than silently weakening either obligation.

**Follow-up / deeper answer:** **“Even when those strings never meet in this corpus?”** Yes, the compile-time overlap test is conservative. A context-sensitive exception would require a different explicit contract, not a hidden precedence rule.

**Original code/evidence references:** [`_boundary_overlap`, `_check_overlap`][C16]

### Q12 — Why require strict type equality?

**Primary slide:** [r12-typed-locations](#r12-typed-locations) · **Legacy section:** `03-semantics`

**Short answer:** Ordinary Python equality can equate Boolean/integer and integer/float values.

**Follow-up / deeper answer:** **“What about correct values on the wrong rows?”** Type checks alone do not catch that. Location reconstruction checks the expected value at the corresponding cell or row. The typed regression covers both JSON and SQLite type mutations.

**Original code/evidence references:** [`_typed_equal`][C05]; [`_verify_sqlite_locations`][C17]; [typed regression][C20]

### Q13 — Is report-last an atomic transaction?

**Primary slide:** [r13-publication](#r13-publication) · **Legacy section:** `04-reliability`

**Short answer:** No. Individual rename operations are atomic; the whole workflow is a readiness protocol.

**Follow-up / deeper answer:** **“What can a failed run leave?”** Uncommitted corpus bytes or temporary artifacts can remain after some failures. A preflight failure on a rerun can preserve a prior release. Do not promise empty output or rollback in every failure state.

**Original code/evidence references:** [`_publish`, `run_pipeline`][C06]

### Q14 — What if writing the report makes partial progress?

**Primary slide:** [r13-publication](#r13-publication) · **Legacy section:** `04-reliability`

**Short answer:** The loop advances by the returned byte count and refuses zero progress before marker publication.

**Follow-up / deeper answer:** **“Does fsync prove every crash case?”** No. The code uses file and directory sync operations, but this review does not establish every filesystem, storage-device, or power-loss outcome.

**Original code/evidence references:** [`_publish`][C06]

### Q15 — How did the relative-path leak happen?

**Primary slide:** [r28-canonical-path](#r28-canonical-path) · **Legacy section:** `04-reliability`

**Short answer:** Validation and writing used inconsistent representations of the same destination.

**Follow-up / deeper answer:** **“Why not just change `output.parents`?”** The resolved result must also reach the writer. The CLI replaces `args.output`; approval canonicalizes both its policy path and derived receipt path before writing either.

**Original code/evidence references:** [`separate_output`][C07]; [`main`][C15]; [`approve`][C09]

### Q16 — Why doesn’t mode `0600` solve the leak?

**Primary slide:** [r28-canonical-path](#r28-canonical-path) · **Legacy section:** `04-reliability`

**Short answer:** It restricts permissions, not placement. A raw-name artifact still does not belong inside a release.

**Follow-up / deeper answer:** **“And exclusive creation?”** `O_EXCL` prevents replacing an existing file; it does not prevent adding a new inappropriate file. Both location validation and private exclusive creation are needed.

**Original code/evidence references:** [`write_private`][C18]; [path regression][C08]

### Q17 — Can a symlink change after validation?

**Primary slide:** [r28-canonical-path](#r28-canonical-path) · **Legacy section:** `04-reliability`

**Short answer:** The closed blocker concerns deterministic aliases under the stated filesystem assumptions.

**Follow-up / deeper answer:** **“Is traversal race-proof?”** No such claim is made. Canonicalization is not an immutable filesystem capability. A hostile concurrent writer is outside this bounded fix.

**Original code/evidence references:** [`separate_output`][C07]; [assurance boundary][D01]

### Q18 — How do you know the fix didn’t disable all output?

**Primary slide:** [r28-canonical-path](#r28-canonical-path) · **Legacy section:** `05-evidence`

**Short answer:** The regression requires successful equivalent private-directory flows as positive controls.

**Follow-up / deeper answer:** **“What survives a denied operation?”** It compares the full file-path-to-bytes snapshot, including `report.json`, and checks that no requested policy or receipt appeared. It also checks `0600` on successful artifacts.

**Original code/evidence references:** [Path regression][C08]; E06; [wrapper result][E02]

### Q19 — Does a similarity score of 95 mean 95% probability?

**Primary slide:** [r27-discovery](#r27-discovery) · **Legacy section:** `05-evidence`

**Short answer:** No. It is a string-comparison score, not calibrated identity confidence.

**Follow-up / deeper answer:** **“What prevents two close people being merged?”** Candidates are ranked by distinct identity, ties and insufficient margins are refused, and explicit operator approval is required. Those mechanisms still do not prove the approved personhood judgment is correct.

**Original code/evidence references:** [`discover`][C12]; [`approve`][C09]

### Q20 — Can I edit the review to approve an invented alias?

**Primary slide:** [r27-discovery](#r27-discovery) · **Legacy section:** `05-evidence`

**Short answer:** Inconsistent candidate edits or stale source bindings are rejected by fresh recomputation and report comparison.

**Follow-up / deeper answer:** **“Does that make the report authentic?”** No. A self-consistent report is not a signature or authenticated human approval. The trusted operator owns the invocation; see Q35 for the settings boundary.

**Original code/evidence references:** [`DiscoveryReport.validate`, `approve`][C09]; [workflow contract][D06]

### Q21 — Does human approval authorize release?

**Primary slide:** [r27-discovery](#r27-discovery) · **Legacy section:** `05-evidence`

**Short answer:** It creates a compiled exact policy and a private receipt, not a released corpus.

**Follow-up / deeper answer:** **“Could it introduce a protected overlap?”** The real compiler is invoked after adding the selected rules and before writing. A conflict rejects. A subsequent pipeline run still has to transform and verify before readiness.

**Original code/evidence references:** [`approve`][C09]; [`_check_overlap`][C16]; [`run_pipeline`][C02]

### Q22 — Did WebGPT execute your Docker tests?

**Primary slide:** [r06-output-evidence](#r06-output-evidence) · **Legacy section:** `05-evidence`

**Short answer:** No. Its bounded follow-up PASS came from source, regression, and retained-evidence inspection.

**Follow-up / deeper answer:** **“Then who verified execution?”** The presenter reports local qualification. The local receipt must identify the source commit and artifacts; this rewrite does not turn that report into an execution personally performed by the editor.

**Original code/evidence references:** [`qualify`, `readback`][C10]; E01–E04

### Q23 — Does a large green test count prove safety?

**Primary slide:** [r06-output-evidence](#r06-output-evidence) · **Legacy section:** `05-evidence`

**Short answer:** No. The useful unit is an invariant, a concrete challenge, an oracle, and its boundary.

**Follow-up / deeper answer:** **“What would falsify your claim?”** A reproducer that violates the required contract at this commit, or evidence that a claimed check did not run or does not check the claimed property. Positive controls prevent rejection-only tests from misleading us.

**Original code/evidence references:** [Path regression][C08]; [typed regression][C20]; [`verify_corpus`][C13]

### Q24 — Why not split every file at newlines?

**Primary slide:** [r14-cloud](#r14-cloud) · **Legacy section:** `06-production`

**Short answer:** Newlines are not universal logical record boundaries.

**Follow-up / deeper answer:** **“What is implemented today?”** Per-file local adapters. Parser-aware CSV splitting, UTF-8/match overlap ownership, and distributed scheduling belong to the proposed production design. JSONL framing is not a new supported local suffix in this baseline.

**Original code/evidence references:** [`transform_file` and adapters][C19]; [AWS design][D02]

### Q25 — Where is the shared pseudonym state in production?

**Primary slide:** [r14-cloud](#r14-cloud) · **Legacy section:** `06-production`

**Short answer:** Workers must receive the same versioned policy, identity set, and replacement-allocation plan.

**Follow-up / deeper answer:** **“Does using one HMAC key suffice?”** No. Different identity subsets can cause different collision assignments. The local allocator demonstrates semantics; shared distributed plan management is a production design obligation.

**Original code/evidence references:** [`build_replacements`][C03]; [AWS design][D02]

### Q26 — What proves the petabyte SLA and price?

**Primary slide:** [r23-answer-scale](#r23-answer-scale) · **Legacy section:** `06-production`

**Short answer:** Nothing proves operational delivery yet. The repository contains a scenario model and design targets.

**Follow-up / deeper answer:** **“What would you measure first?”** Representative transform/verify throughput, memory, object-size skew, request volume, retry rates, and attainable concurrency. The model’s compute factor is an assumption, not a benchmark-derived law.

**Original code/evidence references:** [`_one`, `_sensitivity`][C11]; [inputs][D04]; [example output][D05]

### Q27 — What if two workers retry the same object?

**Primary slide:** [r14-cloud](#r14-cloud) · **Legacy section:** `06-production`

**Short answer:** Deterministic content helps, but the proposed orchestrator still needs idempotent attempt handling and conditional publication.

**Follow-up / deeper answer:** **“Is this exactly-once processing?”** No. The design starts with at-least-once delivery. Duplicate work must not cause inconsistent manifests or premature pointer updates; no distributed commit implementation is claimed locally.

**Original code/evidence references:** [AWS reliability/publication design][D02]; [`_publish`][C06]

### Q28 — Did you stay within eight hours?

**Primary slide:** [r17-disclosure](#r17-disclosure) · **Legacy section:** `07-nonclaims`

**Short answer:** I cannot substantiate compliance; post-timebox work is explicitly disclosed.

**Follow-up / deeper answer:** **“But the retrospective estimate totals eight hours?”** It is an approximate allocation, not an instrumented log. It does not erase the recorded overrun or later requested extension. The evaluator decides how that affects the trial.

**Original code/evidence references:** [`SUBMISSION.md` time disclosure][D01]

### Q29 — How much did AI do, and do you understand the implementation?

**Primary slide:** [r17-disclosure](#r17-disclosure) · **Legacy section:** `07-nonclaims`

**Short answer:** AI coding assistance and browser-backed review are disclosed; no unsupported authorship percentage is claimed.

**Follow-up / deeper answer:** **“Show your understanding.”** Trace one actual failure: the old lexical parent check, the canonical return value, both approval outputs, and the regression’s unchanged-release assertion. Explain the limit rather than reciting a PASS label.

**Original code/evidence references:** [AI disclosure][D01]; [`separate_output`][C07]; [regression][C08]

### Q30 — What would you do next, and what would you refuse to claim?

**Primary slide:** [r17-disclosure](#r17-disclosure) · **Legacy section:** `07-nonclaims`

**Short answer:** Measure representative workloads, increase checking independence where warranted, and define production key/identity-plan lifecycle.

**Follow-up / deeper answer:** **“Why stop now?”** Those are separate objectives. The submission makes bounded claims and discloses unfinished work; technical PASS is not a reason to relabel future functionality as complete.

**Original code/evidence references:** [Unfinished work and stopping rule][D01]

### Q31 — Is `policy_version` a revision ID for each policy edit?

**Primary slide:** [r09-identity](#r09-identity) · **Legacy section:** `03-semantics`

**Short answer:** No. It is the schema version, currently fixed to one.

**Follow-up / deeper answer:** **“How are edits identified?”** The report records the policy file’s digest. Derivation uses schema version and canonical identities, not that full digest. Provenance binding and pseudonym allocation are separate mechanisms.

**Original code/evidence references:** [`compile_policy`][C01]; [`_digest`][C03]; [`RunReport`, `run_pipeline`][C02]

### Q32 — Can renaming a rule change its pseudonym?

**Primary slide:** [r09-identity](#r09-identity) · **Legacy section:** `03-semantics`

**Short answer:** Yes when the rule has no `subject_id`, because `rule_id` is then the identity fallback.

**Follow-up / deeper answer:** **“What if `subject_id` is explicit?”** Renaming the rule does not change that canonical identity. It can still affect rule metadata or tie-breaking; the guarantee should be stated in terms of actual identity and matching inputs.

**Original code/evidence references:** [`Rule.identity`][C01]; [`_select`][C04]

### Q33 — Can you distinguish two different people both called Alice?

**Primary slide:** [r08-policy](#r08-policy) · **Legacy section:** `03-semantics`

**Short answer:** Not from this literal alone. Contradictory identities over the same match domain are rejected.

**Follow-up / deeper answer:** **“Could the column or surrounding sentence resolve it?”** The current policy does not provide context-scoped matching. That requires a different authority and schema, not silently treating every matching name as one person.

**Original code/evidence references:** [`compile_policy` match-domain validation][C01]; [`build_matcher`][C04]

### Q34 — Does approving one proposed cell authorize only that cell?

**Primary slide:** [r27-discovery](#r27-discovery) · **Legacy section:** `05-evidence`

**Short answer:** No. It adds a case-sensitive literal rule to the policy.

**Follow-up / deeper answer:** **“Could it affect a longer value elsewhere?”** Yes. Discovery is whole-value, but the exact engine is substring-based across eligible strings. Approval must consider that broader effect. The subsequent compiler and verifier enforce the resulting policy; they do not infer the operator intended row-only scope.

**Original code/evidence references:** [`approve`][C09]; [`Matcher.replace`][C04]; [four-format workflow test][C21]

### Q35 — Does review recomputation prove who approved it or freeze the original thresholds?

**Primary slide:** [r27-discovery](#r27-discovery) · **Legacy section:** `05-evidence`

**Short answer:** No. It proves consistency with fresh discovery using the supplied valid settings.

**Follow-up / deeper answer:** **“Could someone create another coherent review?”** The review is not signed. Threshold and margin come from the supplied report and are validated and reused. This is a trusted-operator workflow, not an authentication or tamper-evident approval system.

**Original code/evidence references:** [`DiscoveryReport.validate`, `approve`][C09]; [`discover`][C12]

### Q36 — Does `seam_validation: PASS` mean the aliases are correct or the policy is released?

**Primary slide:** [r27-discovery](#r27-discovery) · **Legacy section:** `05-evidence`

**Short answer:** Neither. It is a producer-side structural/contract check.

**Follow-up / deeper answer:** **“Does runtime use JSON Schema here?”** The producers call their Python validation methods and approval calls `compile_policy`. The retained workflow test also validates artifact shapes with JSON Schema. That does not turn the validation stamp into identity truth or release permission.

**Original code/evidence references:** [`Candidate.validate`, `DiscoveryReport.validate`, `ApprovalReceipt.validate`][C12]; [workflow test][C21]

### Q37 — Is `verification_sha256` the hash of a separate verifier receipt?

**Primary slide:** [r13-publication](#r13-publication) · **Legacy section:** `04-reliability`

**Short answer:** No. The pipeline assigns it the same sealed corpus digest as `corpus_manifest_sha256`.

**Follow-up / deeper answer:** **“Is it proof against forgery?”** A digest binds bytes only when compared against a trusted reference. This report is not a signed attestation, and the seal is computed after verification under the declared staging assumption.

**Original code/evidence references:** [`RunReport`, `run_pipeline`][C02]; [`_publish`][C06]

### Q38 — What exactly is preserved: physical bytes or logical content?

**Primary slide:** [r11-formats](#r11-formats) · **Legacy section:** `03-semantics`

**Short answer:** The contract is format-aware; do not claim universal byte identity.

**Follow-up / deeper answer:** **“Give a concrete distinction.”** JSON formatting and CSV quoting can change while values remain equivalent. SQLite checks logical DDL, metadata, and typed values, not physical pages. The JSON comparator checks key sets, not key insertion order.

**Original code/evidence references:** [Adapters][C19]; [`_typed_equal`, `_verify_locations`][C05]; [`_verify_sqlite_locations`][C17]

### Q39 — Do you reject every generated SQLite column?

**Primary slide:** [r11-formats](#r11-formats) · **Legacy section:** `03-semantics`

**Short answer:** No. The writer excludes generated/hidden columns from updates; verification still reads resulting row values.

**Follow-up / deeper answer:** **“What happens if a generated value changes?”** The row oracle compares it against the expected contract and can reject. Do not describe this as full generated-column support, or falsely claim every generated-column schema is rejected before processing.

**Original code/evidence references:** [`_writable_columns`, `_transform_sqlite`][C19]; [`_verify_sqlite_locations`][C17]

### Q40 — Why accept `0.1` but reject some other JSON decimal tokens?

**Primary slide:** [r11-formats](#r11-formats) · **Legacy section:** `03-semantics`

**Short answer:** The adapter checks decimal numeric round-trip through the serialized float representation, not exact binary representation.

**Follow-up / deeper answer:** **“So `0.1` is not exactly representable in binary?”** That is not the test being made. `_finite_float` compares `Decimal(token)` with `Decimal(repr(value))`; it refuses tokens whose decimal numeric value would change, and refuses nonfinite results. Original numeric spelling is not preserved.

**Original code/evidence references:** [`_finite_float`, `_transform_json`][C19]

### Q41 — Do matching and residual scanning apply identical Unicode rules?

**Primary slide:** [r10-spans](#r10-spans) · **Legacy section:** `03-semantics`

**Short answer:** No. Matching is exact or ASCII-insensitive; residual counting/scanning uses `casefold()` for insensitive rules.

**Follow-up / deeper answer:** **“Is there an implemented homoglyph detector?”** No general homoglyph/NFKC detector is established by this code. The broader residual fold can conservatively refuse output; it does not expand the matcher’s authority to normalize or replace additional input.

**Original code/evidence references:** [`ascii_lower`][C04]; [`_count`, `verify_corpus`][C13]

### Q42 — Is the temporary input bundle encrypted or immutable?

**Primary slide:** [r05-mounted-cli](#r05-mounted-cli) · **Legacy section:** `02-architecture`

**Short answer:** No. It is a private filesystem snapshot with copy/readback checks under stated trust assumptions.

**Follow-up / deeper answer:** **“Why copy at all?”** It adapts a file/folder into the existing engine’s bundle interface and avoids writing to originals. It is not a replacement for immutable object versions or encrypted work storage in production.

**Original code/evidence references:** [`input_bundle`][C25]; [assurance boundary][D01]

### Q43 — Do `preflight`, `inspect`, and `verify` all prove the same thing?

**Primary slide:** [r05-mounted-cli](#r05-mounted-cli) · **Legacy section:** `02-architecture`

**Short answer:** No. Preflight checks admission conditions; inspect summarizes a report; verify checks source/output corpus content.

**Follow-up / deeper answer:** **“Can inspect authenticate a release?”** No. It reads selected report fields. The qualification checker separately validates report schema and recomputes digests. Do not use an inspection display as a substitute for those checks.

**Original code/evidence references:** [`_preflight_cmd`, `_inspect_cmd`, `_verify_cmd`][C15]; [`readback`][C10]

### Q44 — Should repeated runs produce identical reports?

**Primary slide:** [r06-output-evidence](#r06-output-evidence) · **Legacy section:** `04-reliability`

**Short answer:** No. Corpus determinism is distinct from run metadata.

**Follow-up / deeper answer:** **“What should replay compare?”** Compare the corpus and appropriate content digests. `run_id` includes a time input, and elapsed time varies. Comparing complete reports would conflate stable transformation with intentionally changing execution metadata.

**Original code/evidence references:** [`run_pipeline`, `_manifest_digest`][C02]; [`qualify` replay comparison][C10]

### Q45 — Does the qualification script accept an arbitrary frozen SHA?

**Primary slide:** [r06-output-evidence](#r06-output-evidence) · **Legacy section:** `05-evidence`

**Short answer:** Not as a `--ref` argument. It records the invoking checkout’s HEAD, clones `main`, and requires equality.

**Follow-up / deeper answer:** **“What happens after main advances?”** That historical invocation should fail the equality check rather than silently qualify another commit. For this presentation, inspect the recorded receipt and archive; do not casually rerun the script and call the result historical qualification.

**Original code/evidence references:** [`qualify`][C10]; E01, E05

### Q46 — Does default Docker qualification establish optional discovery-image behavior?

**Primary slide:** [r04-docker](#r04-docker) · **Legacy section:** `05-evidence`

**Short answer:** No. The default build omits RapidFuzz; the optional build uses `INCLUDE_DISCOVERY=1`.

**Follow-up / deeper answer:** **“What evidence covers discovery?”** Project/wrapper workflow tests and their scoped artifacts. A default-image `run`/`demo` result does not prove the optional image was built or exercised. This rewrite makes no such extra execution claim.

**Original code/evidence references:** [Dockerfile][C22]; [workflow test][C21]; E01–E03

### Q47 — Are all real AWS operations priced by the estimator?

**Primary slide:** [r16-cost](#r16-cost) · **Legacy section:** `06-production`

**Short answer:** No. It is an explicit but simplified scenario model.

**Follow-up / deeper answer:** **“What is simplified beyond disclosed exclusions?”** For example, orchestration budgets one SQS price unit, one EventBridge event, and one KMS request per object. That is not a traced accounting of send/receive/delete, retries, API payload units, or every encryption operation. Use it for assumptions discussion, not invoicing certainty.

**Original code/evidence references:** [`_one`][C11]; [price/unit inputs][D04]; [cost disclosures][D01]

### Q48 — Will Live Evidence or an AI copilot help answer during the assessment?

**Primary slide:** [r29-discussion](#r29-discussion) · **Legacy section:** `07-nonclaims`

**Short answer:** This document is preparation only; no active assistance or recording is claimed.

**Follow-up / deeper answer:** **“The coding trial allowed AI—does that carry over?”** Not automatically. Formal-assessment rules and explicit permission govern interview assistance; recording consent is separate. The preparation bank is not evidence that live use is authorized.

**Original code/evidence references:** [Preparation-only handoff](#live-evidence-handoff); [evidence boundaries](#evidence-ledger)


<a id="evidence-ledger"></a>
## Evidence ledger and version boundaries

| ID | Actual material available in this revision | Boundary |
|---|---|---|
| E01 | Supplied historical qualification receipt copied as sources/qualification.json; exact0375af56 source commit and recorded demo/readbacks | The receipt was read; raw command logs and the original submission archive were not executed or rehashed here. A status does not make the authoring environment an executor. |
| E02 | Previously inspected retained wrapper eval, linked in the source record and existing question answers | Historical wrapper evidence, not a new run or automatic approval of all post-trial code. |
| E03 | Presenter-reported targeted CLI/wrapper results | No new targeted test run during this revision. |
| E04 | Prior source-only bounded reviewer PASS for canonical-path fix at0375af56 | Not timebox compliance, exhaustive security, or fresh presentation approval. |
| E05 | Archive identity recorded in supplied qualification receipt | Its hash identifies the reported original ZIP; the new authoring ZIP is a different artifact. Original archive bytes were not supplied for rehash here. |
| E06 | Source of the targeted path test, typed mutation test and four-format workflow, inspected in this conversation | Assertions and positive controls, not a fresh pytest execution. |
| E07 | Supplied committed cost output, eight normalized rows and analytics describe output | Modeled, not measured. We author a within-scenario chart and do not claim analytics/create-figure commands ran here. |
| E08 | Reviewed narrative, selected pinned source windows, and current supplied schemas/design contracts | Source/authoring validation only. No runtime, compiler, SVG skill, GUI or slide-import validation. |
| E09 | Supplied security methodology and previously inspected scanner receipt | Bandit supporting evidence; Semgrep zero-target scan; no SCA receipt. Not an all-scanner clean result. |
| E10 | Pinned Battle receipt selected fields, inspected through GitHub | Local deterministic fixture contract. agentic=false; models_used=[]; no adaptive live target campaign. |

The pinned SUBMISSION.md described the follow-up review as pending when committed. The later PASS is conversation evidence; it is not retroactively added to that immutable file.

<a id="live-evidence-handoff"></a>
## Preparation and assessment boundary

`question-map.json` is an authoring/navigation artifact. It is not a Live Evidence schema claim, a Memory import, active recording, live retrieval, or candidate-answer delivery. Preserve Q IDs, primary slide, legacy section, frozen code URL and evidence class when preparing later material.

Formal-assessment restrictions control any actual assistance. Permission to use AI coding tools during the trial is not permission to generate answers during the interview. Recording consent is separate and must be explicit. This package establishes neither.

No debugger captures or paused frames are included. Code navigation is a source reference, not Run/Step/Continue. No Archify, React Flow, or general-purpose GSN integration was adopted. Claim/evidence links here are presentation provenance, not a validated assurance case.

## Original pinned reference definitions

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
