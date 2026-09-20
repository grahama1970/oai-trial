from __future__ import annotations

import json
from pathlib import Path

import pytest

from anonymization_trial.contextual_graph import audit_contextual_graph


def _write_graph(path: Path, *, edge_source: str = "subject:anon-1") -> Path:
    path.write_text(
        json.dumps(
            {
                "authorized": True,
                "subjects": [
                    {
                        "subject_id": "anon-1",
                        "clues": [{"type": "employer", "value": "Rare Labs"}],
                    }
                ],
                "auxiliary_identities": [
                    {
                        "identity_id": "person-a",
                        "clues": [{"type": "role", "value": "Archivist"}],
                    },
                    {
                        "identity_id": "person-b",
                        "clues": [{"type": "role", "value": "Archivist"}],
                    },
                ],
                "relationship_edges": [
                    {"from": edge_source, "to": "bridge:1", "type": "contextual_link"},
                    {"from": "bridge:1", "to": "bridge:2", "type": "contextual_link"},
                    {"from": "bridge:2", "to": "identity:person-a", "type": "contextual_link"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_higher_hop_relationship_path_blocks_when_clues_alone_are_clear(
    tmp_path: Path,
) -> None:
    result = audit_contextual_graph(_write_graph(tmp_path / "higher-hop.json"))

    assert result["verdict"] == "block"
    assert result["inferred_subjects"] == 1
    assert result["ambiguous_subjects"] == 0
    assert result["maximum_shared_clues"] == 0
    assert result["traversed_relationship_paths"] == 1
    assert result["maximum_relationship_hops"] == 3
    assert "anon-1" not in json.dumps(result) and "person-a" not in json.dumps(result)


def test_relationship_edges_reject_unknown_typed_endpoint(tmp_path: Path) -> None:
    path = _write_graph(tmp_path / "unknown-endpoint.json", edge_source="subject:unknown")

    with pytest.raises(ValueError, match="unknown subject or identity"):
        audit_contextual_graph(path)
