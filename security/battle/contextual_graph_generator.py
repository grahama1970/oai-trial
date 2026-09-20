"""Retained Battle case for the policy-bound contextual graph release gate."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _render(path: Path, text: str) -> None:
    image = Image.new("RGB", (1000, 180), "white")
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 64)
    ImageDraw.Draw(image).text((30, 45), text, fill="black", font=font)
    image.save(path, resolution=200)


def generate(work_dir, params):
    root = Path(work_dir) / "contextual-graph-two-hop-risk"
    corpus = root / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "record.txt").write_text(
        "Alice works at Rare Labs.\n", encoding="utf-8"
    )
    (corpus / "record.json").write_text(
        json.dumps({"city": "Leeds"}), encoding="utf-8"
    )
    _render(root / "badge.png", "Rare Labs")
    _render(root / "brief.pdf", "Leeds")
    (root / "policy.json").write_text(
        json.dumps(
            {
                "version": 1,
                "sensitive_values": [
                    {"rule_id": "name", "type": "name", "value": "Alice"}
                ],
                "protected_values": [],
                "release_risk": {"contextual_graph_min_shared_clues": 2},
            }
        ),
        encoding="utf-8",
    )
    clues = [
        {"type": "employer", "value": "Rare Labs"},
        {"type": "city", "value": "Leeds"},
    ]
    (root / "contextual_graph.json").write_text(
        json.dumps(
            {
                "authorized": True,
                "clue_catalog": clues,
                "subject_sources": [
                    {
                        "subject_id": "anon-1",
                        "files": ["badge.png", "brief.pdf"],
                    }
                ],
                "auxiliary_identities": [
                    {"identity_id": "person-a", "clues": clues},
                    {
                        "identity_id": "person-b",
                        "clues": [{"type": "city", "value": "Leeds"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "invalid_input.json").write_text(
        json.dumps(
            {
                "schema": "battle.invalid_input_predicate.v1",
                "approved": True,
                "predicate": "authorized two-hop contextual inference must block publication",
            }
        ),
        encoding="utf-8",
    )
    yield "contextual-graph-two-hop-risk", str(root), "MUST_REJECT"

    safe = Path(work_dir) / "contextual-graph-safe-control"
    safe_corpus = safe / "corpus"
    safe_corpus.mkdir(parents=True, exist_ok=True)
    (safe_corpus / "record.txt").write_text(
        "Alice works at Rare Labs.\n", encoding="utf-8"
    )
    (safe_corpus / "record.json").write_text(
        json.dumps({"city": "Leeds"}), encoding="utf-8"
    )
    _render(safe / "badge.png", "Rare Labs")
    _render(safe / "brief.pdf", "Leeds")
    (safe / "policy.json").write_text(
        json.dumps(
            {
                "version": 1,
                "sensitive_values": [
                    {"rule_id": "name", "type": "name", "value": "Alice"}
                ],
                "protected_values": [],
                "release_risk": {"contextual_graph_min_shared_clues": 2},
            }
        ),
        encoding="utf-8",
    )
    (safe / "contextual_graph.json").write_text(
        json.dumps(
            {
                "authorized": True,
                "clue_catalog": clues,
                "subject_sources": [
                    {
                        "subject_id": "anon-1",
                        "files": ["badge.png", "brief.pdf"],
                    }
                ],
                "auxiliary_identities": [
                    {
                        "identity_id": "person-a",
                        "clues": [{"type": "city", "value": "Leeds"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    yield "contextual-graph-safe-control", str(safe), "MUST_ACCEPT"


# Adaptive adapter contract. Battle owns the loop, scoring, selection, lineage,
# promotion, and release verdict; this module only describes/materializes the
# target-specific input family.
def adaptive_seeds(params):
    return [
        {"hop_count": 2, "clues": ["employer", "city"], "ambiguous": False,
         "carriers": ["txt", "json"]},
        {"hop_count": 3, "clues": ["employer", "city", "role"], "ambiguous": True,
         "carriers": ["png", "pdf", "json"]},
    ]


def adaptive_mutations(parent, judge_receipt, params):
    # The objective Judge result controls whether Red broadens a defended path
    # or minimizes a winning repro. This branch is recorded in lineage.
    won = judge_receipt.get("verdict") != "PASS"
    clues = list(parent["clues"])
    carriers = list(parent["carriers"])
    if won:
        return [
            {**parent, "hop_count": max(2, parent["hop_count"] - 1),
             "clues": clues[:2], "carriers": carriers[:2]},
            {**parent, "ambiguous": not parent["ambiguous"]},
        ]
    next_clue = next((item for item in ["role", "postcode", "team"] if item not in clues), "team")
    next_carrier = next((item for item in ["png", "pdf", "csv", "json", "txt"] if item not in carriers), "txt")
    return [
        {**parent, "hop_count": parent["hop_count"] + 1,
         "clues": clues + [next_clue], "carriers": carriers + [next_carrier]},
        {**parent, "ambiguous": not parent["ambiguous"],
         "carriers": list(reversed(carriers))},
    ]


def adaptive_safe_control(mutation):
    return {**mutation, "safe_control": True}


def materialize_adaptive_case(root, mutation, case_id):
    root = Path(root)
    corpus = root / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    values = {
        "employer": "Rare Labs", "city": "Leeds", "role": "Archivist",
        "postcode": "LS1 1AA", "team": "Indigo",
    }
    clues = [{"type": kind, "value": values[kind]} for kind in mutation["clues"]]
    hop_count = int(mutation["hop_count"])
    safe_control = bool(mutation.get("safe_control"))
    # Two-hop specimens use the product's native subject->clue->identity shape.
    # Higher-hop specimens encode a real ordered relationship chain. The subject
    # exposes only the first clue, so a target that ignores relationship_edges
    # will publish instead of recognizing the composed re-identification path.
    carrier_clues = clues if hop_count == 2 or safe_control else clues[:1]
    files = []
    for index, carrier in enumerate(mutation["carriers"]):
        clue = carrier_clues[index % len(carrier_clues)]
        name = f"carrier-{index}.{carrier}"
        path = root / name
        if carrier == "json":
            path.write_text(json.dumps({clue["type"]: clue["value"]}), encoding="utf-8")
        elif carrier == "csv":
            path.write_text(f'{clue["type"]},{clue["value"]}\n', encoding="utf-8")
        elif carrier in {"png", "pdf"}:
            _render(path, clue["value"])
        else:
            path.write_text(clue["value"] + "\n", encoding="utf-8")
        files.append(name)
    (corpus / "record.txt").write_text("Alice synthetic record.\n", encoding="utf-8")
    (root / "policy.json").write_text(json.dumps({
        "version": 1,
        "sensitive_values": [{"rule_id": "name", "type": "name", "value": "Alice"}],
        "protected_values": [],
        "release_risk": {"contextual_graph_min_shared_clues": 2},
    }), encoding="utf-8")
    identity_clues = clues[:1] if safe_control else clues
    relationship_edges = []
    if hop_count > 2 and not safe_control:
        identity_clues = [clues[-1]]
        chain_nodes = ["subject:anon-1"]
        chain_nodes.extend(f"bridge:{index}" for index in range(1, hop_count))
        chain_nodes.append("identity:person-a")
        relationship_edges = [
            {"from": chain_nodes[index], "to": chain_nodes[index + 1], "type": "contextual_link"}
            for index in range(hop_count)
        ]
    identities = [{"identity_id": "person-a", "clues": identity_clues}]
    if mutation.get("ambiguous") and not safe_control:
        identities.append({"identity_id": "person-b", "clues": list(identity_clues)})
    graph = {
        "authorized": True, "clue_catalog": clues,
        "subject_sources": [{"subject_id": "anon-1", "files": files}],
        "auxiliary_identities": identities,
        "relationship_edges": relationship_edges,
        "battle_mutation_metadata": {
            "relationship_hop_count": hop_count,
            "cross_carrier_count": len(set(mutation["carriers"])),
            "clue_combination": list(mutation["clues"]),
            "ambiguous": bool(mutation.get("ambiguous")),
        },
    }
    (root / "contextual_graph.json").write_text(json.dumps(graph), encoding="utf-8")
    expectation = "MUST_ACCEPT" if safe_control else "MUST_REJECT"
    if expectation == "MUST_REJECT":
        (root / "invalid_input.json").write_text(json.dumps({
            "schema": "battle.invalid_input_predicate.v1", "approved": True,
            "predicate": "authorized adaptive contextual inference must block publication",
        }), encoding="utf-8")
    return case_id, str(root), expectation


def adaptive_validate_materialized_case(root, mutation):
    root = Path(root)
    graph = json.loads((root / "contextual_graph.json").read_text(encoding="utf-8"))
    metadata = graph.get("battle_mutation_metadata") or {}
    edges = graph.get("relationship_edges") or []
    hop_count = int(mutation["hop_count"])
    safe_control = bool(mutation.get("safe_control"))
    problems = []
    if metadata.get("relationship_hop_count") != hop_count:
        problems.append("hop_count_binding_mismatch")
    if metadata.get("clue_combination") != list(mutation["clues"]):
        problems.append("clue_combination_binding_mismatch")
    if metadata.get("ambiguous") != bool(mutation.get("ambiguous")):
        problems.append("ambiguity_binding_mismatch")
    if metadata.get("cross_carrier_count") != len(set(mutation["carriers"])):
        problems.append("cross_carrier_binding_mismatch")
    if hop_count > 2 and not safe_control:
        if len(edges) != hop_count:
            problems.append("relationship_edge_count_mismatch")
        elif edges[0].get("from") != "subject:anon-1" or edges[-1].get("to") != "identity:person-a":
            problems.append("relationship_chain_endpoint_mismatch")
        elif any(edges[index].get("to") != edges[index + 1].get("from") for index in range(len(edges) - 1)):
            problems.append("relationship_chain_disconnected")
    elif edges:
        problems.append("unexpected_relationship_edges")
    return {
        "schema": "battle.contextual_graph_mutation_materialization.v1",
        "status": "FAIL" if problems else "PASS",
        "mutation": mutation,
        "relationship_hop_count": hop_count,
        "relationship_edge_count": len(edges),
        "clue_count": len(mutation["clues"]),
        "ambiguous": bool(mutation.get("ambiguous")),
        "cross_carrier_count": len(set(mutation["carriers"])),
        "problems": problems,
    }
