# Current operator direction

# OAI trial: proposed presentation organization

Status: proposed organization for the next deck revision, not evidence that
existing slide exports have been reorganized. This direction preserves the
prepared adversarial-question block explicitly rather than folding it into
technical detail or audience discussion.

Current coordinated **candidate**, still requiring human review:
[TOC](reorganized/TOC.md) · [transcript](reorganized/WALKTHROUGH.md) ·
[slide JSON](reorganized/deck.json) · [integration notes](reorganized/README.md).

## Fixed instructions

- First slide: **Table of Contents**. No cover or demo precedes it.
- Then show the working demo and the actual result before explaining internals.
- Prepared narrative: **30 minutes**, including code navigation; reserve another
  **15+ minutes** for audience discussion.
- One concept per detail slide. Four concepts is a ceiling, not a target.
- Prepared adversarial questions explain and defend the choices **before Extra Credit**.
- Extra Credit is the last substantive prepared block.
- Audience slide: **Discussion**. Final slide: **Thank you.**
- Preserve evidence qualifiers, code references, and Q01–Q48. No runtime changes.

## Proposed Table of Contents

1. **Demo and Results**
   - Let's run it
   - Here is the result: changed values and preserved meaning
2. **Reproduce and Verify**
   - Exact CLI invocation and input/output locations
   - Supported setup and Docker environment
   - Verification command, output evidence, and limitations
3. **How the Solution Works**
   - Compact pipeline orientation
   - Code walkthrough: one concept per slide
     - Validate policy and input boundaries
     - Assign identity-coherent pseudonyms
     - Resolve original-input spans without cascades
     - Transform the supported formats
     - Verify values, types, structure, and location
     - Seal and publish the verified corpus
   - Production design, capacity, SLA, and cost assumptions
4. **Why These Choices? — Prepared Adversarial Questions**
   - Why exact-policy matching rather than automatic PII detection?
   - How independent is a verifier that shares replacement primitives?
   - What changes at petabyte scale, and what does the cost model actually prove?
5. **Extra Credit**
   - **Security Evals (White, Grey, Black, and Adaptive Lineage)**
   - Thin `anonymize-data` skill wrapper
   - Explicitly reviewed name-alias discovery
6. **Discussion**
   - Audience questions and follow-ups
7. **Thank you.**

The explicit prepared-question section renumbers the later TOC entries; the
requested audience label remains Discussion. This is a proposal for human review,
not permission to silently remove the prepared questions to retain old numbering.

## Prepared-question block: one question per slide

Use a visible question, a short answer/decision, and one concrete piece of code
or evidence. Do not read the whole 48-question appendix aloud.

| Proposed slide | Decision and qualification to explain | Existing question/evidence handles |
|---|---|---|
| Why exact-policy matching? | Explicit policy supplies authority; broad detection is a separate problem. Optional discovery does not silently authorize replacement. | Q01–Q03, Q19–Q21; `policy.py::compile_policy`, `discovery.py::approve` |
| Can the verifier share code? | Rereading and location/type checks catch output faults, but shared primitives leave common-mode risk. Independent qualification checks have a bounded fixture scope. | Q04, Q12, Q22–Q23, Q37; `verification.py::verify_corpus`, `_typed_equal`, `qualify_submission.py::readback` |
| What changes at petabyte scale? | Local per-file processing is not a production benchmark. Distribution must preserve a common identity plan; costs depend on workload and quota assumptions. | Q24–Q27, Q47; `pseudonyms.py::build_replacements`, `estimate_aws_cost.py::_one`, production design |

The last prepared-question slide must lead into Extra Credit. No new substantive
prepared block follows Extra Credit; backup material is outside normal playback.

## Graham reference study

The actual supplied PPTX packages were inspected in
`ARTIFACT_ROOT/skills/pitchdeck/sources/style-corpus/`. Layout discovery used
`pitchdeck/run.sh find-layout`. Selected existing renders were viewed through
live Surf pages; source text was checked against the PPTX presentation order.

- **ACERT_Darpa_PI_Meeting_FtWorth, slide 1:** hierarchical Table of Contents,
  including indented subtopics and separate questions/deeper-dive entries.
- **SpartaAI_CyberSummitv_v3, slide 12:** an orientation page headed
  “How ACERT Works,” rather than all implementation detail on one canvas.
- **SpartaAI_CyberSummitv_v3, slides 52–53:** a distinct question page followed by
  a distinct answer/assertion page. This is the useful pattern for defending a
  choice; it is not merely another generic topic bullet.
- **SpartaAI_CyberSummitv_v3, slides 58–59:** separate Open Discussion and Thank You.

These are presentation-structure references, not evidence for oai-trial technical
claims. Historical product claims, sponsorship/distribution labels, and images
must not be transplanted into this public deck. The reference images remain
presenter-local, not in the public repository. The current grahama.co theme
request remains separate from the historical teal/white references.

Reference-study artifacts:
`ARTIFACT_ROOT/oai-trial/deck-authoring/house-study/`

## Detail-slide and evidence rules

Map each pipeline-detail slide to the actual file, function, and checked line
range. Source navigation/highlighting is not a breakpoint or a paused frame.
Run, Inspect, Step, Continue, and Stop remain explicit actions.

Core correctness checks belong in Reproduce and Verify. The additional security
methodology belongs in Extra Credit. Its detail slides must distinguish the
retained white/gray/black-box evidence from the fixture-backed Judge demonstration;
a live adaptive campaign against this project is not established.

Production architecture and cost modeling were required by the brief, so they
are not extra credit. Additional capability claims require their own evidence.

## Visual and ownership boundaries

Use the requested grahama.co brand direction and the supported pitchdeck theme
interface. The header requirement is an actual low-opacity image overlay, not
just translucent fill; the theme worker reports the supplied house-band image at
10% opacity over a separately controlled fill. Check that behavior when applied
rather than treating this instruction as a visual proof.

Preserve intended animation in the browser and separate it from fixed PPTX/PDF
geometry. Reading beside VS Code must not be confused with shrinking a full slide.
Do not edit shared agent-skills/pitchdeck implementation files concurrently with
its owner. Keep all narrative and source mappings in the oai-trial project.

## Demo entrypoint decision

Use only this sentence before running the demo: “I’m using a thin skill wrapper around the project’s CLI; the same engine runs independently in Docker.”

Do not insert a skill introduction slide before the demo. Explain the wrapper,
reuse rationale, and best-practices-skills structure in Extra Credit. Use the
existing tested wrapper; no live setup or skill creation. Preserve the 30-minute
prepared budget and clearly distinguish live output from recorded fallback.


# Project-state report

# oai-trial Project State -- 2026-09-06 (standard mode, generic profile)

## Phase 1: Infrastructure

### Daemons: not applicable (target root is not an Embry-style project)

### Tests: 84 collected

### 3-Tier Cascade: not applicable (target root is not an Embry-style project)

### Cascade Wiring: not applicable (target root is not an Embry-style project)

### Skills: not applicable (target root owns no skills/ tree (not a skills workspace))

### Deploy: 0 systemd units

## Phase 2: Memory Recall

- **oai-trial features architecture deployment**: NOT FOUND (conf=0.00, 0 items)
- **oai-trial competitive advantages unique capabilities**: NOT FOUND (conf=0.00, 0 items)
- **oai-trial known issues gaps missing features**: NOT FOUND (conf=0.00, 0 items)

## Phase 3: Doc-Code Drift (25 items)

- **future** (1x): ### Future optimizations (designed, not built)
- **not_yet** (1x): scale; cloud prices are list prices not yet confirmed against a dated source;
- **stale_reference** (23x): References `formats.py` but file not found

## Phase 4: Best Practices (1 findings)
  Critical=1 High=0 Medium=0 Low=0

- hardcoded_secret: 1x

## Phase 5: External Research (skipped -- quick mode)

## Phase 6: Gap Analysis (4 gaps)

1. **[LOW]** The report collected 84 tests under tests/; it did not execute them and this count does not cover the separate security/tests suite.
   Action: Do not present collection as a passing test run; use the dated qualification and regression receipts for execution claims.
2. **[LOW]** The automatic critical keyword flag is in the synthetic corpus generator. Source readback identifies the intentionally seeded sk_synthetic_7CWQ0JY5i2 test value; this report does not establish a real credential exposure.
   Action: Retain the synthetic fixture and original heuristic finding; do not launch unrelated security repairs from this keyword flag.
3. **[LOW]** The reported missing module basenames exist under src/anonymization_trial/. Future optimization language is explicitly labeled as unimplemented; it is not an instruction to expand runtime scope.
   Action: Treat these as detector limitations/context, not missing runtime modules. Preserve the raw report for comparison.
4. **[MEDIUM]** The coordinated presentation remains a candidate. Final visual approval, Google Slides import, live-demo rehearsal, verified VS Code interactions and Live Evidence wiring are not established. Latest speaker-note edits have not been rerendered.
   Action: Keep the pre-demo wrapper mention to one sentence; explain reuse and best-practices-skills only in Extra Credit. Next request is a source-grounded interview/transcript and focused-slide update, with a downloadable authoring ZIP.


# Full report JSON including retained automated findings and manual source review

```json
{
  "schema": "project_state.report.v1",
  "project": "oai-trial",
  "project_root": "PROJECT_ROOT",
  "project_profile": "generic",
  "timestamp": "2026-09-06T17:17:45.186921+00:00",
  "mode": "standard",
  "phase_1_infrastructure": {
    "daemons": {
      "applicable": false,
      "reason": "target root is not an Embry-style project",
      "daemons": {},
      "up": 0,
      "total": 0
    },
    "tests": {
      "total": 84,
      "collected": true,
      "path": "PROJECT_ROOT/tests"
    },
    "cascade": {
      "applicable": false,
      "reason": "target root is not an Embry-style project",
      "registry": {
        "validators": 0,
        "classifiers": 0,
        "regressors": 0,
        "gpts": 0
      },
      "shadow": {
        "total": 0,
        "usable": 0
      },
      "training_data": {},
      "classifiers_on_disk": [],
      "tier_status": {
        "tier_2_teacher": "NOT_APPLICABLE",
        "tier_1_5_gpt": "NOT_APPLICABLE",
        "tier_0_5_classifier": "NOT_APPLICABLE"
      }
    },
    "daemon_cascade_wiring": {
      "applicable": false,
      "reason": "target root is not an Embry-style project",
      "wired": {}
    },
    "skills": {
      "total": 0,
      "applicable": false,
      "reason": "target root owns no skills/ tree (not a skills workspace)",
      "path": null,
      "missing_skill_md": [],
      "missing_sanity": []
    },
    "frontend": {
      "exists": false
    },
    "deploy": {
      "systemd_units": 0,
      "containerfile": false,
      "docker_compose": true
    },
    "components": {
      "registered": 0,
      "projects": {},
      "note": "No component registry found"
    }
  },
  "phase_2_memory": {
    "available": true,
    "successful_recalls": 3,
    "attempted_recalls": 3,
    "recalls": [
      {
        "query": "oai-trial features architecture deployment",
        "found": false,
        "confidence": 0.0,
        "count": 0,
        "top_items": []
      },
      {
        "query": "oai-trial competitive advantages unique capabilities",
        "found": false,
        "confidence": 0.0,
        "count": 0,
        "top_items": []
      },
      {
        "query": "oai-trial known issues gaps missing features",
        "found": false,
        "confidence": 0.0,
        "count": 0,
        "top_items": []
      }
    ]
  },
  "phase_3_doc_drift": {
    "docs_checked": 7,
    "docs_found": 1,
    "drift_items": [
      {
        "file": "README.md",
        "issue": "future",
        "severity": "low",
        "line": "### Future optimizations (designed, not built)"
      },
      {
        "file": "README.md",
        "issue": "not_yet",
        "severity": "low",
        "line": "scale; cloud prices are list prices not yet confirmed against a dated source;"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `formats.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `matcher.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `policy.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `pseudonyms.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `policy.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `formats.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `verification.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `pipeline.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `pipeline.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `errors.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `policy.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `matcher.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `policy.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `formats.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `formats.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `errors.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `pseudonyms.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `pipeline.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `verification.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `pseudonyms.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `__main__.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `bundle.py` but file not found"
      },
      {
        "file": "README.md",
        "issue": "stale_reference",
        "severity": "medium",
        "line": "References `discovery.py` but file not found"
      }
    ],
    "drift_count": 25
  },
  "phase_4_best_practices": {
    "findings": [
      {
        "file": "src/anonymization_trial/fixture.py",
        "issue": "hardcoded_secret",
        "severity": "critical"
      }
    ],
    "total_findings": 1,
    "by_severity": {
      "critical": 1,
      "high": 0,
      "medium": 0,
      "low": 0
    },
    "best_practice_skills_available": [
      "best-practices-python",
      "best-practices-react",
      "best-practices-skills",
      "best-practices-kde"
    ]
  },
  "phase_5_research": {
    "skipped": true,
    "reason": "Use standard or --full mode"
  },
  "phase_6_gaps": {
    "gaps": [
      {
        "category": "report_scope",
        "severity": "low",
        "gap": "The report collected 84 tests under tests/; it did not execute them and this count does not cover the separate security/tests suite.",
        "action": "Do not present collection as a passing test run; use the dated qualification and regression receipts for execution claims."
      },
      {
        "category": "security_review",
        "severity": "low",
        "gap": "The automatic critical keyword flag is in the synthetic corpus generator. Source readback identifies the intentionally seeded sk_synthetic_7CWQ0JY5i2 test value; this report does not establish a real credential exposure.",
        "action": "Retain the synthetic fixture and original heuristic finding; do not launch unrelated security repairs from this keyword flag."
      },
      {
        "category": "documentation_review",
        "severity": "low",
        "gap": "The reported missing module basenames exist under src/anonymization_trial/. Future optimization language is explicitly labeled as unimplemented; it is not an instruction to expand runtime scope.",
        "action": "Treat these as detector limitations/context, not missing runtime modules. Preserve the raw report for comparison."
      },
      {
        "category": "presentation",
        "severity": "medium",
        "gap": "The coordinated presentation remains a candidate. Final visual approval, Google Slides import, live-demo rehearsal, verified VS Code interactions and Live Evidence wiring are not established. Latest speaker-note edits have not been rerendered.",
        "action": "Keep the pre-demo wrapper mention to one sentence; explain reuse and best-practices-skills only in Extra Credit. Next request is a source-grounded interview/transcript and focused-slide update, with a downloadable authoring ZIP."
      }
    ],
    "improvements": [],
    "automated_gaps": [
      {
        "category": "security",
        "severity": "critical",
        "gap": "1 critical best-practice violations (possible hardcoded secrets)",
        "action": "Run /security-scan and fix immediately"
      },
      {
        "category": "documentation",
        "severity": "low",
        "gap": "1 aspirational/TODO items in docs",
        "action": "Implement or remove aspirational claims"
      }
    ],
    "project_agent_review": {
      "source_report_sha256": "49b7075c6549c6a4c457f5dd50a528da089c5f2d65a3329bc9e609a72677001a",
      "note": "Automated phases are retained unchanged. The following gap synthesis includes explicitly identified source readback, not a new test or security run.",
      "evidence": [
        "src/anonymization_trial/fixture.py",
        "src/anonymization_trial/",
        "docs/pitch/oai-trial/reorganized/validation/local-checks.json"
      ]
    }
  }
}

```
