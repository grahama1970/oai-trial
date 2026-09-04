#!/usr/bin/env python3
"""Project-only briefing preparation: mirror curated sources and render two static flows.

Uses PyYAML (dev-only); production anonymization remains stdlib-only. No model
calls, approval decisions, PPTX compilation, or browser review happen here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "docs/pitch/oai-trial"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_flow(scene: Path) -> None:
    data = yaml.safe_load(scene.read_text())
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    svg = ET.Element(
        f"{{{ns}}}svg",
        {
            "viewBox": "0 0 1400 400",
            "role": "img",
            "aria-label": data["title"],
            "font-family": "Arial, sans-serif",
        },
    )

    def element(tag: str, **attrs):
        return ET.SubElement(
            svg, f"{{{ns}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()}
        )

    def text(x, y, label, color="#e2e8f0", size=22):
        element("text", x=x, y=y, fill=color, font_size=size, text_anchor="middle").text = label

    element("rect", width=1400, height=400, fill="#0f172a")
    nodes = data["nodes"]
    width, gap = (1320 - 20 * (len(nodes) - 1)) / len(nodes), 20
    centers = []
    for i, node in enumerate(nodes):
        x = 40 + i * (width + gap)
        center = x + width / 2
        centers.append(center)
        color = {"verify": "#f59e0b", "ready": "#34d399"}.get(node.get("state"), "#22d3ee")
        element(
            "rect",
            x=x,
            y=70,
            width=width,
            height=112,
            rx=6,
            fill="#1e293b",
            stroke=color,
            stroke_width=2,
        )
        for j, line in enumerate(node["label"].split("\n")):
            text(center, 106 + j * 30, line, color, 21)
        if i:
            element(
                "path",
                d=f"M{x - gap},126 H{x - 5} l-7,-5 m7,5 l-7,5",
                stroke="#22d3ee",
                fill="none",
                stroke_width=2,
            )
        if node.get("state") != "ready":
            element(
                "path", d=f"M{center},182 V255", stroke="#f87171", fill="none", stroke_width=1.5
            )
    element(
        "path",
        d=f"M{centers[0]},255 H{centers[-2]} M700,255 V292",
        stroke="#f87171",
        fill="none",
        stroke_width=1.5,
    )
    element(
        "rect",
        x=420,
        y=292,
        width=560,
        height=60,
        rx=6,
        fill="#271923",
        stroke="#f87171",
        stroke_width=2,
    )
    text(700, 329, "ANY FAILURE → FAILED / UNCOMMITTED", "#f87171", 23)
    text(700, 386, data["qualifier"], "#94a3b8", 19)
    ET.ElementTree(svg).write(scene.with_suffix("").with_suffix(".svg"), encoding="unicode")


def prepare(source_ref: str) -> None:
    generated = BUNDLE / "generated"
    generated.mkdir(exist_ok=True)
    for scene in (BUNDLE / "assets").glob("*.scene.yml"):
        if scene.name in {"local-pipeline.scene.yml", "publication-state.scene.yml"}:
            render_flow(scene)
    notes = (BUNDLE / "speaker_notes.curated.md").read_text()
    sections = dict(re.findall(r"^## (\d\d-[\w-]+)[^\n]*\n(.*?)(?=^## |\Z)", notes, re.M | re.S))
    deck_path = BUNDLE / "deck.curated.yaml"
    deck = yaml.safe_load(deck_path.read_text())
    for slide in deck["slides"]:
        slide["notes"] = sections[slide["id"]].strip()
    deck_path.write_text(yaml.safe_dump(deck, sort_keys=False, allow_unicode=True, width=110))
    for src, dst in (
        ("deck.curated.yaml", "deck.public.yaml"),
        ("claim_ledger.curated.yaml", "claim_ledger.yaml"),
        ("speaker_notes.curated.md", "speaker_notes.md"),
    ):
        shutil.copyfile(BUNDLE / src, generated / dst)
    source_path = BUNDLE / "source_manifest.yaml"
    sources = yaml.safe_load(source_path.read_text())
    hashes = {}
    for source in sources["sources"]:
        path = ROOT / source["path"].removeprefix("${PROJECT_ROOT}/")
        source["content_sha"] = "sha256:" + digest(path)
        source["ref"] = source_ref
        hashes[source["id"]] = digest(path)
    source_path.write_text(yaml.safe_dump(sources, sort_keys=False, allow_unicode=True, width=110))
    shutil.copyfile(source_path, generated / "source_manifest.resolved.yaml")
    state = {
        "schema": "pitchdeck.source_state.v1",
        "source_commit": source_ref,
        "hashes": hashes,
        "missing": [],
        "canonical_hashes": {
            f: digest(BUNDLE / f)
            for f in ("deck.curated.yaml", "claim_ledger.curated.yaml", "speaker_notes.curated.md")
        },
    }
    assets = yaml.safe_load((generated / "asset_manifest.yaml").read_text())
    state["asset_hashes"] = {
        a["local_path"].removeprefix("${PROJECT_ROOT}/"): digest(
            ROOT / a["local_path"].removeprefix("${PROJECT_ROOT}/")
        )
        for a in assets["assets"]
    }
    (generated / "source_state.json").write_text(json.dumps(state, indent=2) + "\n")
    plan = {
        "schema": "oai_trial.pitch_projection.v1",
        "source_commit": source_ref,
        "canonical": ["deck.curated.yaml", "claim_ledger.curated.yaml", "speaker_notes.curated.md"],
        "slide_ids": [s["id"] for s in deck["slides"]],
        "candidate_claims": 0,
        "status": "SOURCE_SYNCHRONIZED",
        "human_approval": "PENDING",
        "non_claim": (
            "Source synchronization does not establish build, render, import or human approval."
        ),
    }
    (generated / "plan_receipt.json").write_text(json.dumps(plan, indent=2) + "\n")
    print("Pitch sources synchronized; visual/human approval not implied.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ref", default=None)
    args = parser.parse_args()
    ref = (
        args.source_ref
        or subprocess.check_output(  # noqa: S603 (fixed git read-only argv)
            [shutil.which("git") or "/usr/bin/git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    )
    prepare(ref)
