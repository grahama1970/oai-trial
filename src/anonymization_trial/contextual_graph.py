"""Deterministic contextual graph re-identification attack.

The attack consumes an explicitly authorized, local JSON projection. Raw labels are
used only in memory to join released subjects to auxiliary identities through typed
clues. Receipts contain aggregate counts only; no graph, labels, identifiers, or
embeddings are persisted.
"""
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .multimodal import MultimodalError, _ocr_words

SCHEMA = "contextual_graph_attack.v2"
_MIN_CALIBRATION_CASES = 10


def _calibrated_rate(payload: dict[str, Any], score: int) -> dict[str, Any] | None:
    """Return an empirical, score-matched control rate with a Wilson interval."""
    raw = payload.get("calibration_cases")
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError("calibration_cases must be an array")
    outcomes: list[bool] = []
    for case in raw:
        if not isinstance(case, dict):
            raise ValueError("calibration cases must be objects")
        shared_clues, reidentified = case.get("shared_clues"), case.get("reidentified")
        if (
            not isinstance(shared_clues, int)
            or shared_clues < 0
            or not isinstance(reidentified, bool)
        ):
            raise ValueError(
                "calibration cases require non-negative shared_clues and boolean reidentified"
            )
        if shared_clues == score:
            outcomes.append(reidentified)
    if len(outcomes) < _MIN_CALIBRATION_CASES:
        raise ValueError("calibration requires at least 10 score-matched labeled controls")
    successes, count = sum(outcomes), len(outcomes)
    rate = successes / count
    z = 1.959963984540054
    denominator = 1 + z * z / count
    center = (rate + z * z / (2 * count)) / denominator
    margin = z * math.sqrt(rate * (1 - rate) / count + z * z / (4 * count * count)) / denominator
    return {
        "method": "score_matched_labeled_controls_wilson_95",
        "shared_clue_score": score,
        "labeled_control_count": count,
        "observed_reidentification_count": successes,
        "reidentification_probability": rate,
        "confidence_interval_95": [max(0.0, center - margin), min(1.0, center + margin)],
    }


def _rows(payload: dict[str, Any], key: str, id_key: str) -> list[tuple[str, set[tuple[str, str]]]]:
    raw = payload.get(key)
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{key} must be a non-empty array")
    rows: list[tuple[str, set[tuple[str, str]]]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get(id_key), str) or not item[id_key]:
            raise ValueError(f"each {key} entry requires a non-empty {id_key}")
        identifier = item[id_key]
        if identifier in seen:
            raise ValueError(f"duplicate {id_key}")
        seen.add(identifier)
        clues_raw = item.get("clues")
        if not isinstance(clues_raw, list) or not clues_raw:
            raise ValueError(f"each {key} entry requires clues")
        clues: set[tuple[str, str]] = set()
        for clue in clues_raw:
            if not isinstance(clue, dict):
                raise ValueError("clues must be objects")
            kind, value = clue.get("type"), clue.get("value")
            if not isinstance(kind, str) or not kind or not isinstance(value, str) or not value:
                raise ValueError("each clue requires non-empty string type and value")
            clues.add((kind, value))
        rows.append((identifier, clues))
    return rows


def _scalar_text(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [text for item in value.values() for text in _scalar_text(item)]
    if isinstance(value, list):
        return [text for item in value for text in _scalar_text(item)]
    if value is None or isinstance(value, bool):
        return []
    return [str(value)]


def _ocr_text(path: Path) -> str:
    try:
        return " ".join(word.text for word in _ocr_words(path))
    except MultimodalError as error:
        raise ValueError("contextual image OCR failed closed") from error


def _carrier_text(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".json":
        return "\n".join(_scalar_text(json.loads(path.read_text(encoding="utf-8"))))
    if suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            return "\n".join(value for row in csv.reader(handle) for value in row)
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        return _ocr_text(path)
    if suffix == ".pdf":
        pdftoppm = shutil.which("pdftoppm")
        if pdftoppm is None:
            raise ValueError("contextual PDF rasterizer unavailable")
        with tempfile.TemporaryDirectory(prefix="anon-context-ocr-") as directory:
            root = Path(directory)
            completed = subprocess.run(  # noqa: S603 - resolved binary, controlled argv
                [pdftoppm, "-png", "-r", "200", str(path), str(root / "page")],
                capture_output=True,
                timeout=300,
                check=False,
            )
            pages = sorted(root.glob("page-*.png"))
            if completed.returncode != 0 or not pages:
                raise ValueError("contextual PDF rasterization failed closed")
            return "\n".join(_ocr_text(page) for page in pages)
    raise ValueError("contextual carrier must be text, structured data, image, or PDF")


def _subjects_from_carriers(
    payload: dict[str, Any], manifest_path: Path
) -> tuple[list[tuple[str, set[tuple[str, str]]]], int]:
    catalog = payload.get("clue_catalog")
    sources = payload.get("subject_sources")
    if not isinstance(catalog, list) or not catalog:
        raise ValueError("clue_catalog must be a non-empty array")
    if not isinstance(sources, list) or not sources:
        raise ValueError("subject_sources must be a non-empty array")
    clues: list[tuple[str, str]] = []
    for clue in catalog:
        if not isinstance(clue, dict):
            raise ValueError("clue_catalog entries must be objects")
        kind, value = clue.get("type"), clue.get("value")
        if not isinstance(kind, str) or not kind or not isinstance(value, str) or not value:
            raise ValueError("each catalog clue requires non-empty string type and value")
        clues.append((kind, value))

    root = manifest_path.parent.resolve()
    rows: list[tuple[str, set[tuple[str, str]]]] = []
    seen: set[str] = set()
    carrier_count = 0
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("subject_sources entries must be objects")
        subject_id, files = source.get("subject_id"), source.get("files")
        if not isinstance(subject_id, str) or not subject_id or subject_id in seen:
            raise ValueError("subject_sources requires unique non-empty subject_id values")
        if not isinstance(files, list) or not files:
            raise ValueError("each subject source requires files")
        seen.add(subject_id)
        text_parts: list[str] = []
        for relative in files:
            if not isinstance(relative, str) or not relative:
                raise ValueError("carrier paths must be non-empty strings")
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or path.is_symlink() or not path.is_file():
                raise ValueError("contextual carrier must be a regular file below the manifest")
            text_parts.append(_carrier_text(path))
            carrier_count += 1
        text = "\n".join(text_parts)
        found = {
            (kind, value)
            for kind, value in clues
            if re.search(rf"(?<!\w){re.escape(value)}(?!\w)", text, re.IGNORECASE)
        }
        rows.append((subject_id, found))
    return rows, carrier_count


def _relationship_reachability(
    payload: dict[str, Any],
    subject_ids: set[str],
    identity_ids: set[str],
) -> tuple[dict[str, set[str]], int, int]:
    """Return identity reachability through validated directed relationship edges."""

    raw_edges = payload.get("relationship_edges")
    if raw_edges is None:
        return {}, 0, 0
    if not isinstance(raw_edges, list):
        raise ValueError("relationship_edges must be an array")

    adjacency: dict[str, set[str]] = {}
    seen_edges: set[tuple[str, str]] = set()
    for edge in raw_edges:
        if not isinstance(edge, dict):
            raise ValueError("relationship_edges entries must be objects")
        source, target, kind = edge.get("from"), edge.get("to"), edge.get("type")
        if (
            not isinstance(source, str)
            or not source
            or not isinstance(target, str)
            or not target
            or kind != "contextual_link"
        ):
            raise ValueError(
                "relationship edges require non-empty from/to and type contextual_link"
            )
        pair = (source, target)
        if pair in seen_edges:
            raise ValueError("duplicate relationship edge")
        seen_edges.add(pair)
        adjacency.setdefault(source, set()).add(target)

    known_subject_nodes = {f"subject:{identifier}" for identifier in subject_ids}
    known_identity_nodes = {f"identity:{identifier}" for identifier in identity_ids}
    referenced_nodes = {
        node for edge in seen_edges for node in edge
    }
    unknown_typed_nodes = {
        node
        for node in referenced_nodes
        if (node.startswith("subject:") and node not in known_subject_nodes)
        or (node.startswith("identity:") and node not in known_identity_nodes)
    }
    if unknown_typed_nodes:
        raise ValueError("relationship edge references an unknown subject or identity")

    reachable: dict[str, set[str]] = {}
    traversed = 0
    maximum_hops = 0
    for subject_id in subject_ids:
        start = f"subject:{subject_id}"
        distances = {start: 0}
        queue = [start]
        for node in queue:
            for target in sorted(adjacency.get(node, ())):
                if target in distances:
                    continue
                distances[target] = distances[node] + 1
                queue.append(target)
        identities = {
            identity_id
            for identity_id in identity_ids
            if f"identity:{identity_id}" in distances
        }
        if identities:
            reachable[subject_id] = identities
            traversed += len(identities)
            maximum_hops = max(
                maximum_hops,
                *(distances[f"identity:{identity_id}"] for identity_id in identities),
            )
    return reachable, traversed, maximum_hops


def audit_contextual_graph(input_path: Path, min_shared_clues: int = 2) -> dict[str, Any]:
    """Attack subjects through subject -> clue -> identity paths.

    A unique best candidate is inferred. Multiple best candidates are ambiguous.
    Both outcomes block release; only subjects below the threshold are clear.
    """
    if min_shared_clues < 2:
        raise ValueError("min_shared_clues must be at least 2")
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("authorized") is not True:
        raise ValueError("contextual graph input requires explicit authorization")
    if "subject_sources" in payload:
        subjects, carriers_evaluated = _subjects_from_carriers(payload, input_path)
        subject_input_kind = "local_carriers"
    else:
        subjects = _rows(payload, "subjects", "subject_id")
        carriers_evaluated = 0
        subject_input_kind = "preprojected_clues"
    identities = _rows(payload, "auxiliary_identities", "identity_id")
    relationship_identities, relationship_paths, maximum_relationship_hops = (
        _relationship_reachability(
            payload,
            {identifier for identifier, _clues in subjects},
            {identifier for identifier, _clues in identities},
        )
    )

    inferred = ambiguous = clear = 0
    traversed_paths = 0
    max_shared = 0
    clue_types: set[str] = set()
    for subject_id, subject_clues in subjects:
        clue_types.update(kind for kind, _value in subject_clues)
        scores = []
        for _identity_id, identity_clues in identities:
            shared = len(subject_clues & identity_clues)
            traversed_paths += shared
            scores.append(shared)
        best = max(scores, default=0)
        max_shared = max(max_shared, best)
        winners = sum(score == best for score in scores)
        linked_identities = relationship_identities.get(subject_id, set())
        if len(linked_identities) == 1:
            inferred += 1
        elif len(linked_identities) > 1:
            ambiguous += 1
        elif best < min_shared_clues:
            clear += 1
        elif winners == 1:
            inferred += 1
        else:
            ambiguous += 1

    verdict = "block" if inferred or ambiguous else "clear"
    calibration = _calibrated_rate(payload, max_shared)
    does_not_establish = [
        "safety against unprovided auxiliary information",
        "complete ecosystem parity",
    ]
    if calibration is None:
        does_not_establish.insert(0, "calibrated re-identification probability")
    return {
        "schema": SCHEMA,
        "verdict": verdict,
        "release_ready": False,
        "risk_kind": "contextual_multi_hop_reidentification",
        "minimum_shared_clues": min_shared_clues,
        "minimum_path_hops": 2,
        "subjects_evaluated": len(subjects),
        "subject_input_kind": subject_input_kind,
        "carriers_evaluated": carriers_evaluated,
        "auxiliary_identities_evaluated": len(identities),
        "clue_types_evaluated": len(clue_types),
        "traversed_two_hop_paths": traversed_paths,
        "traversed_relationship_paths": relationship_paths,
        "maximum_relationship_hops": maximum_relationship_hops,
        "inferred_subjects": inferred,
        "ambiguous_subjects": ambiguous,
        "clear_subjects": clear,
        "maximum_shared_clues": max_shared,
        "raw_values_persisted": False,
        "identifiers_persisted": False,
        "embeddings_used": False,
        "requires_human_review": bool(ambiguous),
        "calibration": calibration,
        "does_not_establish": does_not_establish,
    }
