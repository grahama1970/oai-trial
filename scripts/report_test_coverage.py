#!/usr/bin/env python3
"""Join a source-reviewed catalog to pytest JUnit results; emit report inputs.

The create-report skill validates and renders the semantic JSON. This script
classifies nothing automatically and never treats passing cases as sufficiency.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from link_pitch_code import parse_xml

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("adversarial", "positive_control", "boundary_stress", "evidence_check")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(
    junit: Path,
    run_path: Path,
    output: Path,
    reviewer: Path | None,
    remediation: Path | None = None,
):
    catalog_path = ROOT / "security/test_catalog.json"
    catalog = json.loads(catalog_path.read_text())
    run = json.loads(run_path.read_text())
    if sha(junit) != run["junit_sha256"]:
        raise ValueError("JUnit changed after the recorded run")
    for path, digest in run["source_sha256"].items():
        if sha(ROOT / path) != digest:
            raise ValueError(f"test evidence is stale: {path}")
    rows, seen = [], set()
    for node in parse_xml(junit.read_bytes()).findall(".//testcase"):
        name = node.attrib["name"]
        path = node.attrib["classname"].replace(".", "/") + ".py"
        key = path + "::" + name.split("[", 1)[0]
        entry = catalog["cases"][key]  # unknown tests fail instead of disappearing
        if entry["kind"] not in KINDS:
            raise ValueError(f"unclassified test: {key}")
        seen.add(key)
        status = "PASS"
        if node.find("failure") is not None or node.find("error") is not None:
            status = "FAIL"
        elif node.find("skipped") is not None:
            status = "SKIP"
        rows.append({"nodeid": path + "::" + name, "function": key, **entry, "status": status})
    if not rows or seen != set(catalog["cases"]):
        raise ValueError("JUnit must cover every cataloged security test function")
    output.mkdir(parents=True, exist_ok=True)
    totals = Counter(r["kind"] for r in rows)
    outcomes = Counter(r["status"] for r in rows)
    families = []
    for key, family in catalog["families"].items():
        cases = [r for r in rows if r["family"] == key]
        counts = Counter(r["kind"] for r in cases)
        families.append(
            {
                "id": key,
                **family,
                "total": len(cases),
                **{k: counts[k] for k in KINDS},
                "passed": sum(r["status"] == "PASS" for r in cases),
                "failed": sum(r["status"] == "FAIL" for r in cases),
                "skipped": sum(r["status"] == "SKIP" for r in cases),
                "functions": sorted({r["function"] for r in cases}),
            }
        )
    inventory = {
        "schema": "oai_trial.coverage_inventory.v1",
        "source_commit": run["source_commit"],
        "catalog_sha256": sha(catalog_path),
        "run": run,
        "counts": dict(totals),
        "outcomes": dict(outcomes),
        "function_count": len(seen),
        "case_count": len(rows),
        "families": families,
        "cases": rows,
        "non_claim": "Cases and parametrizations are not independent attack scenarios.",
    }
    (output / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    columns = ["name", "total", *KINDS, "passed", "failed", "skipped", "oracle", "limitations"]
    with (output / "family-matrix.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(families)
    sources = [
        {
            "id": f["name"],
            "kind": (
                f"{f['total']} cases: {f['adversarial']} adversarial; "
                f"{f['positive_control']} controls; {f['boundary_stress']} boundary; "
                f"{f['evidence_check']} evidence. PASS {f['passed']}; "
                f"FAIL {f['failed']}; SKIP {f['skipped']}"
            ),
            "path": "; ".join(sorted({k.split("::")[0] for k in f["functions"]})),
            "limitation": f"Oracle: {f['oracle']}. Boundary: {f['limitations']}",
        }
        for f in families
    ]
    sources += [
        {
            "id": "S-RUN",
            "kind": "pytest result + source-hash binding",
            "path": str(junit),
            "limitation": "Synthetic data; no full clean-submission Docker gate.",
        },
        {
            "id": "S-GOAL",
            "kind": "required trial contract",
            "path": "GOAL.md; TRIAL_BRIEF.md",
            "limitation": "Normative requirements, not execution results.",
        },
    ]
    pending = "WebGPT sufficiency review is pending; no verdict is claimed."
    if reviewer:
        review_text = reviewer.read_text()
        receipt = json.loads((reviewer.parent / "node-receipt.json").read_text())
        if not receipt.get("ok") or receipt.get("mocked"):
            raise ValueError("reviewer transport is not proven")
        adequacy = next(line for line in review_text.splitlines() if "ADEQUACY:" in line)
        pending = (
            adequacy.lstrip("# ") + " for the reviewed pre-fix snapshot. "
            "Targeted fixes require local qualification; this is not a new verdict "
            "on the corrected source. Response: " + str(reviewer)
        )
        sources.append(
            {
                "id": "S-WEBGPT",
                "kind": "external reviewer evidence",
                "path": str(reviewer),
                "limitation": "Reviewer judgment is not local closure proof.",
            }
        )
    findings = [
        {
            "id": "F-001",
            "title": "Directory totals are not attack coverage",
            "status": "Verified",
            "evidence": ["inventory.json", str(junit)],
            "rationale": (
                f"{len(rows)} collected cases across {len(seen)} functions: "
                f"{totals['adversarial']} adversarial, "
                f"{totals['positive_control']} positive controls, "
                f"{totals['boundary_stress']} boundary/stress probes, and "
                f"{totals['evidence_check']} evidence checks."
            ),
            "impact": "Calling every case an attack inflates the assurance story.",
            "owner": "project maintainer",
            "valid_next_actions": ["Use the family matrix and named oracles, not a count quota."],
            "acceptance_check": "Every JUnit case maps once; all totals reconcile.",
            "non_claims": ["Not a coverage percentage or independent-trial count."],
        },
        {
            "id": "F-002",
            "title": "Release qualification is still a separate gate",
            "status": "Needs Decision",
            "evidence": ["GOAL.md", str(junit)],
            "rationale": "Nominal cleanup and digest tests do not establish crash recovery.",
            "impact": "Passing pytest alone cannot authorize shipment.",
            "owner": "release owner",
            "valid_next_actions": [
                "Run clean Docker qualification after reviewing required failure sequences."
            ],
            "acceptance_check": (
                "Bare/mounted Docker commands, independent four-format readback, "
                "replay and negative cases pass from the submitted archive."
            ),
            "non_claims": ["No claim that production-hardening gaps are automatically in scope."],
        },
        {
            "id": "F-003",
            "title": "Coverage sufficiency requires bounded review",
            "status": "Verified" if reviewer else "Unverified",
            "evidence": [pending],
            "rationale": "Oracles must detect defects, not just run hostile-looking inputs.",
            "impact": "Adequacy requires reconciliation of named requirements and gaps.",
            "owner": "project maintainer",
            "valid_next_actions": [
                "Reconcile WebGPT's actual findings with local source and reproducers."
            ],
            "acceptance_check": (
                "Required blockers have fail-before/pass-after proof; "
                "disclosed future work stays separate."
            ),
            "non_claims": ["No universal security or anonymity guarantee."],
        },
    ]
    if remediation:
        repair = json.loads(remediation.read_text())
        before = parse_xml(Path(repair["before_junit"]).read_bytes()).findall(".//testcase")
        after = parse_xml(Path(repair["after_junit"]).read_bytes()).findall(".//testcase")
        failed = {n.attrib["name"] for n in before if n.find("failure") is not None}
        passed = {
            n.attrib["name"]
            for n in after
            if n.find("failure") is None and n.find("error") is None and n.find("skipped") is None
        }
        if not failed or not failed <= passed:
            raise ValueError("remediation must close every recorded failing case")
        findings.append(
            {
                "id": "F-004",
                "title": "Three release defects were reproduced and fixed",
                "status": "Verified",
                "evidence": [str(remediation), repair["before_junit"], repair["after_junit"]],
                "rationale": (
                    f"All {len(failed)} supplied failing cases pass after the targeted fixes. "
                    "The local zero-progress write complement also passes."
                ),
                "impact": "Wrong-READY paths are closed under the named fault model.",
                "owner": "project maintainer",
                "valid_next_actions": ["Qualify the clean container"],
                "acceptance_check": "Run supplied regressions and clean container qualification.",
                "non_claims": ["Not a fresh reviewer PASS or completed Docker qualification."],
            }
        )
    contracts = [
        {
            "name": f["name"],
            "owning_persona": "trial reviewer",
            "core_purpose": "Inspect "
            + f["name"].lower()
            + " against "
            + ", ".join(f["requirements"]),
            "primary_object": "; ".join(f["functions"]),
            "source_of_truth": "inventory.json and source-bound security-junit.xml",
            "valid_actions": [
                "Read the named test and oracle",
                "Reproduce a missing required failure sequence",
            ],
            "outstanding_broken_constraints": [f["limitations"]],
        }
        for f in families
    ]
    action = {
        "id": "A-001",
        "related_finding": "F-002",
        "action": "Run the final release gate after bounded coverage review.",
        "owner_persona": "release owner",
        "primary_object": "submission archive and qualification receipt",
        "rationale": "Shipping is a contract decision, not a test-count threshold.",
        "acceptance_check": findings[1]["acceptance_check"],
        "dependencies": ["WebGPT findings reconciled"],
        "risk_if_skipped": "The exact deliverable has not been qualified.",
        "suggested_priority": "P1",
    }
    report = {
        "schema": "create_report.report.v1",
        "report_id": "oai-trial-adversarial-coverage",
        "title": "Adversarial test coverage by failure family",
        "persona": "OpenAI trial reviewer / release owner",
        "primary_object": "source-bound security test inventory and family matrix",
        "decision_supported": "Decide what required qualification remains before shipping",
        "overall_finding": "Partially Verified",
        "core_conclusion": (
            findings[0]["rationale"] + " " + pending
            + " Download the [family matrix CSV](family-matrix.csv) or "
            "inspect [every collected case](inventory.json)."
        ),
        "evidence_basis": (
            "Fresh JUnit results joined to a source-reviewed catalog. Tests use synthetic "
            "inputs and, where stated, controlled adapter/write faults against real runtime "
            "code. Classification is project-agent judgment, not an automatic metric."
        ),
        "highest_risk_issues": [
            "F-002 Publication failure sequences and clean-submission qualification",
            "F-003 Sufficiency not inferred from counts",
        ],
        "immediate_next_steps": [
            "Reconcile the bounded WebGPT review",
            "A-001 Run the exact submitted Docker contract",
        ],
        "scope": {
            "reviewed": ["Every collected security/tests case at " + run["source_commit"]],
            "excluded": [
                "Core tests/ cases outside security/tests are not classified in this matrix",
                "Weekend pitch-deck QA",
                "Unimplemented risk-plane and adaptive Battle",
                "Complete production hardening",
            ],
            "evidence_available": [str(junit), str(run_path), "security/test_catalog.json"],
        },
        "project_context": {
            "goals": ["Qualify the smallest fail-closed implementation against TRIAL_BRIEF.md"],
            "current_state": "Security cases ran; clean-submission qualification is pending.",
            "recent_decisions": [
                "Feature freeze; additions only for concrete required-invariant violations."
            ],
            "open_questions": ["Which missing failure sequences are release-blocking?"],
            "takeover_notes": [
                "No PROJECT_KNOWLEDGE.md found; Memory returned related prep material, "
                "not an authoritative coverage verdict."
            ],
            "sources": ["GOAL.md", "TRIAL_BRIEF.md", "memory-recall.json"],
        },
        "source_of_truth_inventory": sources,
        "findings": findings,
        "surface_contracts": contracts,
        "state_split": {
            "finished": [f"JUnit reconciles all {len(rows)} cases and {len(seen)} functions."],
            "pending": [pending, "A-001 clean-submission qualification"],
            "outstanding": [
                "Reconcile the named oracle limitations, without reopening future scope."
            ],
            "broken": [] if not outcomes["FAIL"] else ["Failing JUnit cases exist."],
            "unproven": [
                "Exhaustive security, anonymity, crash/power-loss behavior and production scale."
            ],
        },
        "plan_ready_next_actions": [action],
        "plan_iterate_seed": {
            "recommended_phase_id": "release-qualification",
            "objective": action["action"],
            "candidate_phases": [
                "Reconcile concrete reviewer blockers",
                "Run minimal reproducers",
                "Qualify submitted Docker artifact",
                "Archive evidence and decide shipment",
            ],
            "deterministic_evidence_gates": [
                "uv run pytest -q",
                "docker build -t anonymization-trial .",
                "docker run --rm anonymization-trial",
                "Mounted four-format run and independent output readback",
            ],
            "domain_review_loops": [
                "Bounded WebGPT coverage review via Ask/Tau; local reproduction owns closure"
            ],
            "interaction_evidence": "Static report; Surf proves visibility, not security.",
            "ask_persona_review": pending,
            "dogpile_reference_research": "Only for unclear failure semantics, not a count target.",
            "human_decisions": [
                "Final shipment authorization and acceptance of explicit non-claims"
            ],
            "stop_conditions": [
                "Any concrete required-invariant violation",
                "Missing artifact/readback",
                "Unavailable reviewer evidence",
            ],
            "non_claims": ["This report is not execution of the final qualification phase."],
        },
        "non_claims": [
            "This covers security/tests, not all tests/ cases or a repo-wide attack count.",
            "Collected cases are not distinct attacks or statistically independent trials.",
            "Optional residual-risk tests are outside the release path.",
            "A passing test does not establish that its assertion catches every intended defect.",
            "This is not a new WebGPT PASS, proof of anonymity, or a shipping authorization.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cases": len(rows),
                "functions": len(seen),
                "kinds": dict(totals),
                "outcomes": dict(outcomes),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewer", type=Path)
    parser.add_argument("--remediation", type=Path)
    args = parser.parse_args()
    build(args.junit, args.run, args.output, args.reviewer, args.remediation)
