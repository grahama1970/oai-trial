"""Retained acceptance contracts for the seven-slide technical briefing.

These inspect source artifacts. Rendered slide and human/import review remain
separate gates in verify_pitch_bundle.py; source tests cannot approve visuals.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "docs/pitch/oai-trial"


def load(path):
    return yaml.safe_load((B / path).read_text())


def slide(number):
    return load("deck.curated.yaml")["slides"][number - 1]


def words(number):
    return " ".join(e.get("text", "") for e in slide(number)["elements"])


def test_final_generated_deck_exactly_matches_curated_seven_slide_ids():
    expected = [
        "01-brief",
        "02-architecture",
        "03-semantics",
        "04-reliability",
        "05-evidence",
        "06-production",
        "07-nonclaims",
    ]
    assert [s["id"] for s in load("deck.curated.yaml")["slides"]] == expected
    assert load("generated/deck.public.yaml") == load("deck.curated.yaml")
    assert load("generated/claim_ledger.yaml") == load("claim_ledger.curated.yaml")
    assert load("generated/plan_receipt.json")["slide_ids"] == expected
    assert load("generated/plan_receipt.json")["candidate_claims"] == 0


def test_curated_deck_contains_no_stale_runtime_claims():
    text = (B / "deck.curated.yaml").read_text() + (B / "claim_ledger.curated.yaml").read_text()
    for pattern in (
        r"collisions extend",
        r"CSV.?/?JSON.{0,10}stream",
        r"quarantine is the fail-closed exit",
    ):
        assert not re.search(pattern, text, re.I)
    for phrase in (
        "reread/re-derivation",
        "not a separate implementation",
        "bounded",
        "per-file",
        "per-row",
    ):
        assert phrase in text.lower()


def test_slide2_local_pipeline_asset_contains_all_release_boundaries():
    assert slide(2)["visual"]["asset_id"] == "local-pipeline"
    svg = (B / "assets/local-pipeline.svg").read_text()
    for phrase in (
        "POLICY",
        "COMPILE",
        "ADAPTERS",
        "PRIVATE",
        "STAGING",
        "REREAD /",
        "RE-DERIVE",
        "VERIFIED",
        "report.json",
        "LAST",
        "READY",
        "FAILED / UNCOMMITTED",
    ):
        assert phrase in svg
    assert "<animate" not in svg and "<script" not in svg


def test_every_technical_slide_has_one_required_visual():
    for s in load("deck.curated.yaml")["slides"][1:]:
        assert s["visual"]["type"] in {"cards", "image", "native_diagram"}
        if s["visual"]["type"] == "image":
            assert len([e for e in s["elements"] if e["type"] == "asset"]) == 1
        else:
            assert len(s["visual"]["items"]) >= 2


def test_slide4_is_release_state_only():
    assert "transformed corpus is not a release" in words(4)
    assert not any(w in words(4) for w in ("SQLite", "CSV", "JSON"))
    svg = (B / "assets/publication-state.svg").read_text()
    for word in ("STAGED", "VERIFY", "SEALED", "PUBLISHED", "report.json", "LAST", "READY"):
        assert word in svg


def test_slide5_prioritizes_runtime_and_adversarial_evidence_over_scanners():
    text = words(5)
    assert text.index("DOCKER DEMO") < text.index("ADVERSARIAL") < text.index("Bandit")
    assert "Swap SQLite pseudonyms" in text and "true → 1" in text
    assert "4 formats" in text and "10× workload" in text


def test_slide6_uses_aws_reference_svg_and_sla_cost_callouts():
    assert slide(6)["visual"]["asset_id"] == "aws-production"
    assert "GCP" not in words(6) and "Azure" not in words(6)
    for term in ("1 TB", "1 PB", "≤1 hour", "≤7 days", "$86", "$85,734", "Modeled"):
        assert term in words(6)
    asset = next(
        a for a in load("generated/asset_manifest.yaml")["assets"] if a["id"] == "aws-production"
    )
    assert asset["local_path"].endswith("docs/production-architecture.svg")


def test_curated_speaker_notes_cover_all_seven_slides_and_35_to_37_minutes():
    notes = (B / "speaker_notes.curated.md").read_text()
    assert 35 <= sum(map(int, re.findall(r"^Time: (\d+) minutes", notes, re.M))) <= 37
    for s in load("deck.curated.yaml")["slides"]:
        assert f"## {s['id']}" in notes
        for key in (
            "Time:",
            "Claim:",
            "Evidence:",
            "Live jump:",
            "Likely challenge:",
            "Concise answer:",
            "Required qualifier:",
            "Transition:",
        ):
            assert key in s["notes"]
    assert (B / "generated/speaker_notes.md").read_text() == notes


def test_every_approved_proof_claim_has_precise_current_evidence_binding():
    sources = {s["id"]: s for s in load("source_manifest.yaml")["sources"]}
    for claim in load("claim_ledger.curated.yaml")["claims"]:
        if claim["status"] != "approved":
            continue
        assert claim["evidence_spans"] and claim["required_qualifier"]
        assert "Evidence command:" in claim["notes"]
        for span in claim["evidence_spans"]:
            source = sources[span["source_id"]]
            path = ROOT / source["path"].removeprefix("${PROJECT_ROOT}/")
            assert span["text"] in path.read_text()
            assert (
                source["content_sha"] == "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            )
            assert re.fullmatch(r"[0-9a-f]{40}", source["ref"])
        assert all(r.get("section") and ":" in r["locator"] for r in claim["source_refs"])


def test_debugger_stops_bind_current_source_and_explicit_local_actions():
    index = json.loads((B / "qa/debugger_stops.json").read_text())
    assert set(index["stops"]) == {"identity", "typed", "publication"}
    for name, stop in index["stops"].items():
        path = ROOT / stop["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == stop["source_sha256"]
        assert path.read_text().splitlines()[stop["line"] - 1].strip() == stop["source_line"]
        assert f"scripts/pitch_debug_demo.py {name}" in stop["capture_command"]
        assert stop["locals"] and stop["expected"]
    links = load("qa/code_links.json")
    for link in links["slides"].values():
        assert f"/blob/{links['source_commit']}/" in link["url"]
        assert (ROOT / link["path"]).is_file()
