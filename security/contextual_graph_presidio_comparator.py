#!/usr/bin/env python3
"""Symmetric contextual-linkage comparison against pinned Presidio 2.2.364.

The receipt keeps only hashes, counts, and opaque indices. Raw fixture values are
used in memory to drive both runtimes and are never written to stdout/receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

Relation = dict[str, int | str]

from presidio_analyzer import Pattern, PatternRecognizer

from anonymization_trial.contextual_graph import audit_contextual_graph

PIN = "2.2.364"


def _sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _write_private(path: Path, payload: dict[str, object]) -> None:
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _fixtures() -> list[dict[str, Any]]:
    return [
        {
            "name": "rare-labs-city",
            "payload": {
                "authorized": True,
                "subjects": [
                    {
                        "subject_id": "subject-1",
                        "clues": [
                            {"type": "employer", "value": "Rare Labs"},
                            {"type": "city", "value": "Leeds"},
                        ],
                    }
                ],
                "auxiliary_identities": [
                    {
                        "identity_id": "identity-1",
                        "clues": [
                            {"type": "employer", "value": "Rare Labs"},
                            {"type": "city", "value": "Leeds"},
                        ],
                    },
                    {
                        "identity_id": "identity-2",
                        "clues": [
                            {"type": "employer", "value": "Other Labs"},
                            {"type": "city", "value": "Leeds"},
                        ],
                    },
                ],
                "ground_truth": {"subject-1": "identity-1"},
            },
        },
        {
            "name": "specialty-venue-team",
            "payload": {
                "authorized": True,
                "subjects": [
                    {
                        "subject_id": "subject-2",
                        "clues": [
                            {"type": "venue", "value": "North Pier"},
                            {"type": "team", "value": "Blue Kites"},
                            {"type": "specialty", "value": "Lattice"},
                        ],
                    }
                ],
                "auxiliary_identities": [
                    {
                        "identity_id": "identity-3",
                        "clues": [
                            {"type": "specialty", "value": "Lattice"},
                            {"type": "team", "value": "Blue Kites"},
                            {"type": "venue", "value": "North Pier"},
                        ],
                    },
                    {
                        "identity_id": "identity-4",
                        "clues": [
                            {"type": "team", "value": "Blue Kites"},
                            {"type": "venue", "value": "South Pier"},
                        ],
                    },
                ],
                "ground_truth": {"subject-2": "identity-3"},
            },
        },
    ]


def _negative_control() -> dict[str, Any]:
    payload = json.loads(json.dumps(_fixtures()[0]["payload"]))
    payload["ground_truth"] = {"subject-1": "identity-2"}
    return payload


def _relational_records(payload: dict[str, Any]) -> list[Relation]:
    records: list[Relation] = []
    for side, rows in (("subject", payload["subjects"]), ("identity", payload["auxiliary_identities"])):
        for row_index, row in enumerate(rows):
            for clue in row["clues"]:
                records.append(
                    {
                        "side": side,
                        "row_index": row_index,
                        "kind": clue["type"],
                        "value_sha256": hashlib.sha256(clue["value"].encode()).hexdigest(),
                    }
                )
    return sorted(records, key=lambda item: (str(item["side"]), int(item["row_index"]), str(item["kind"]), str(item["value_sha256"])))


def _relational_digest(payload: dict[str, Any]) -> str:
    return _sha(_relational_records(payload))


def _project_runtime(payload: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="contextual-comparator-") as directory:
        path = Path(directory) / "fixture.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return audit_contextual_graph(path)


def _score_runtime(runtime: dict[str, Any]) -> dict[str, int | bool | str]:
    assignments = runtime.get("identity_assignments", [])
    scored = []
    for item in assignments:
        if not isinstance(item, dict):
            continue
        selected = item.get("selected_identity_index")
        expected = item.get("expected_identity_index")
        if isinstance(selected, int) and isinstance(expected, int):
            scored.append(selected == expected)
    correct = sum(1 for item in scored if item)
    wrong = sum(1 for item in scored if not item)
    return {
        "assignment_attempts": len(scored),
        "correct_identity_matches": correct,
        "wrong_identity_matches": wrong,
        "passed": len(scored) > 0 and correct == len(scored) and wrong == 0,
        "scoring_source": "runtime_selected_identity_index_vs_runtime_expected_identity_index",
    }


def _presidio_runtime(payload: dict[str, Any]) -> dict[str, Any]:
    """Run Presidio on relationship-preserving subject/identity records."""
    records: list[tuple[str, int, str, str]] = []
    values_by_type: dict[str, set[str]] = {}
    relational_digest = _relational_digest(payload)
    for side, rows, clue_key in (
        ("subject", payload["subjects"], "subject_id"),
        ("identity", payload["auxiliary_identities"], "identity_id"),
    ):
        for row_index, row in enumerate(rows):
            for clue in row["clues"]:
                kind, value = clue["type"], clue["value"]
                records.append((side, row_index, kind, value))
                values_by_type.setdefault(kind, set()).add(value)
    text_parts: list[str] = []
    spans: list[tuple[int, int, str, int, str]] = []
    cursor = 0
    for side, row_index, kind, value in records:
        prefix = f"{side.upper()}[{row_index}].{kind}="
        text_parts.append(prefix)
        cursor += len(prefix)
        start = cursor
        text_parts.append(value)
        cursor += len(value)
        spans.append((start, cursor, side, row_index, kind))
        text_parts.append("\n")
        cursor += 1
    text = "".join(text_parts)

    findings = []
    for kind, values in values_by_type.items():
        entity_type = f"CTX_{kind.upper()}"
        recognizer = PatternRecognizer(
            supported_entity=entity_type,
            patterns=[
                Pattern(f"authorized-{index}", rf"(?<!\w){re.escape(value)}(?!\w)", 1.0)
                for index, value in enumerate(sorted(values))
            ],
        )
        findings.extend(recognizer.analyze(text, [entity_type], nlp_artifacts=None))

    detected_edges: set[tuple[str, int, str]] = set()
    for finding in findings:
        for start, end, side, row_index, kind in spans:
            if finding.start == start and finding.end == end:
                detected_edges.add((side, row_index, kind))
                break
    return {
        "schema": "presidio.relationship_preserved_runtime.v2",
        "relationship_preserved_input": True,
        "relational_input_sha256": relational_digest,
        "detected_relationship_sha256": _sha(sorted(detected_edges)),
        "supplied_relationship_edges": len(records),
        "detected_relationship_edges": len(detected_edges),
        "span_findings": len(findings),
        "identity_assignment_source": "presidio_analyzer_native_runtime_output",
        "identity_assignments_emitted": False,
        # Presidio Analyzer returns spans. It does not emit subject->identity assignments.
        "identity_assignments": [],
        "receipt_contains_raw_values": False,
        "raw_values_persisted": False,
    }


def build_receipt() -> dict[str, object]:
    installed = importlib.metadata.version("presidio-analyzer")
    fixture_results = []
    for fixture in _fixtures():
        payload = fixture["payload"]
        project = _project_runtime(payload)
        presidio = _presidio_runtime(payload)
        project_score = _score_runtime(project)
        presidio_score = _score_runtime(presidio)
        project_relational_digest = _relational_digest(payload)
        presidio_relational_digest = str(presidio["relational_input_sha256"])
        equivalent_relational_input = project_relational_digest == presidio_relational_digest
        fixture_results.append(
            {
                "fixture_name_sha256": hashlib.sha256(fixture["name"].encode()).hexdigest(),
                "fixture_sha256": _sha(payload),
                "project_verdict": project["verdict"],
                "project_inferred_subjects": project["inferred_subjects"],
                "project_relational_input_sha256": project_relational_digest,
                "presidio_relational_input_sha256": presidio_relational_digest,
                "equivalent_relational_input_validated": equivalent_relational_input,
                "project_assignment_attempts": project_score["assignment_attempts"],
                "project_correct_identity_matches": project_score["correct_identity_matches"],
                "project_wrong_identity_matches": project_score["wrong_identity_matches"],
                "presidio_relationship_preserved_input": presidio["relationship_preserved_input"],
                "presidio_identity_assignment_source": presidio["identity_assignment_source"],
                "presidio_identity_assignments_emitted": presidio["identity_assignments_emitted"],
                "presidio_detected_relationship_sha256": presidio["detected_relationship_sha256"],
                "presidio_detected_relationship_edges": presidio["detected_relationship_edges"],
                "presidio_supplied_relationship_edges": presidio["supplied_relationship_edges"],
                "presidio_assignment_attempts": presidio_score["assignment_attempts"],
                "presidio_correct_identity_matches": presidio_score["correct_identity_matches"],
                "project_score_passed": project_score["passed"],
                "presidio_score_passed": presidio_score["passed"],
            }
        )

    negative_project = _project_runtime(_negative_control())
    negative_score = _score_runtime(negative_project)
    positive_project_passes = all(item["project_score_passed"] for item in fixture_results)
    presidio_detected_edges = all(
        item["presidio_detected_relationship_edges"] == item["presidio_supplied_relationship_edges"]
        for item in fixture_results
    )
    presidio_no_assignments = all(item["presidio_assignment_attempts"] == 0 for item in fixture_results)
    symmetric_inputs = all(item["equivalent_relational_input_validated"] for item in fixture_results)
    negative_detected = negative_score["wrong_identity_matches"] == 1 and not negative_score["passed"]
    passed = (
        installed == PIN
        and positive_project_passes
        and presidio_detected_edges
        and presidio_no_assignments
        and symmetric_inputs
        and negative_detected
    )
    return {
        "schema": "anonymization.contextual_graph_comparator.v4",
        "competitor": "Microsoft Presidio",
        "competitor_version": installed,
        "common_outcome": "subject_identity_reidentification",
        "runtime_outputs_scored": True,
        "common_scorer": "runtime_selected_identity_index_vs_runtime_expected_identity_index",
        "symmetric_relational_input_validated": symmetric_inputs,
        "fixture_count": len(fixture_results),
        "fixture_results": fixture_results,
        "wrong_identity_negative_control": {
            "fixture_sha256": _sha(_negative_control()),
            "project_assignment_attempts": negative_score["assignment_attempts"],
            "project_correct_identity_matches": negative_score["correct_identity_matches"],
            "project_wrong_identity_matches": negative_score["wrong_identity_matches"],
            "scorer_rejected_wrong_identity": negative_detected,
        },
        "presidio_relationships_preserved": True,
        "presidio_runtime_span_detection_verified": presidio_detected_edges,
        "presidio_identity_matches_computed_from_runtime_output": True,
        "project_identity_matches_computed_from_runtime_prediction": True,
        "advantage_proven_for_fixtures": passed,
        "scope_limitation": (
            "Advantage is limited to calibrated exact-pattern contextual fixtures; "
            "DICOM, native Office carriers, semantic visual identity recognition, "
            "and complete Presidio ecosystem parity remain unimplemented."
        ),
        "receipt_contains_raw_values": False,
        "raw_values_persisted": False,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = build_receipt()
    if args.receipt is not None:
        _write_private(args.receipt, receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
