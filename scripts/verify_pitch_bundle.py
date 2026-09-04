#!/usr/bin/env python3
"""Fail-closed presentation gate: canonical hashes, exports, links and named reviews.

Human review records are attestations, not inferred from compiler success. This
checker verifies their presence and binding, not the identity of their author.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import yaml
from link_pitch_code import parse_xml


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle: Path, args) -> list[str]:
    errors = []
    generated = bundle / "generated"
    deck = yaml.safe_load((bundle / "deck.curated.yaml").read_text())
    slides = deck["slides"]
    if len(slides) != 7 or [s["order"] for s in slides] != list(range(1, 8)):
        errors.append("expected exactly seven ordered slides")
    for source, target in (
        ("deck.curated.yaml", "deck.public.yaml"),
        ("claim_ledger.curated.yaml", "claim_ledger.yaml"),
        ("speaker_notes.curated.md", "speaker_notes.md"),
    ):
        if (bundle / source).read_bytes() != (generated / target).read_bytes():
            errors.append(f"stale generated artifact: {target}")
    state = json.loads((generated / "source_state.json").read_text())
    for name, digest in state["canonical_hashes"].items():
        if sha(bundle / name) != digest:
            errors.append(f"stale source snapshot: {name}")
    root = bundle.resolve().parents[2]
    for name, digest in state["asset_hashes"].items():
        if sha(root / name) != digest:
            errors.append(f"stale asset snapshot: {name}")
    review_path = bundle / "qa/final-review.json"
    review = json.loads(review_path.read_text()) if review_path.exists() else {}
    for flag, name in (
        (args.require_build_receipt, "build-receipt.json"),
        (args.require_zero_verify_errors, "verify_receipt.json"),
    ):
        if not flag:
            continue
        path = generated / name
        if not path.exists():
            errors.append(f"missing {name}")
            continue
        receipt = json.loads(path.read_text())
        if receipt.get("counts", {}).get("errors", 0) != 0:
            errors.append(f"{name}: nonzero verification errors")
        if receipt.get("readiness") not in {"READY", "USABLE_WITH_GAPS"}:
            errors.append(f"{name}: build/verify not established")
        inputs, outputs = receipt.get("inputs", {}), receipt.get("outputs", {})
        if inputs.get("source_snapshot_sha256") != sha(generated / "source_state.json"):
            errors.append(f"{name}: different source/asset snapshot")
        if inputs.get("canonical_deck_sha256") != sha(bundle / "deck.curated.yaml"):
            errors.append(f"{name}: different canonical deck")
        pptx = Path(outputs.get("linked_pptx", ""))
        if not pptx.is_file() or sha(pptx) != outputs.get("linked_pptx_sha256"):
            errors.append(f"{name}: missing or changed PPTX")
            continue
        with ZipFile(pptx) as archive:
            for n in range(1, 8):
                part = parse_xml(archive.read(f"ppt/slides/_rels/slide{n}.xml.rels"))
                if not any(r.attrib.get("Id") == "pitchEvidence" for r in part):
                    errors.append(f"slide {n}: no clickable evidence link")
    for required, key in (
        (args.require_contact_sheet_review, "contact_sheet_review"),
        (args.require_google_slides_review, "google_slides_review"),
    ):
        if not required:
            continue
        row = review.get(key, {})
        if row.get("status") != "APPROVED" or row.get("reviewer_kind") != "human":
            errors.append(f"{key}: human approval required")
        if row.get("bundle_sha256") != sha(bundle / "deck.curated.yaml"):
            errors.append(f"{key}: review is not bound to current deck")
        if not row.get("reviewed_by") or not row.get("reviewed_at"):
            errors.append(f"{key}: reviewer/date missing")
        evidence = Path(row.get("evidence_path", ""))
        if not evidence.is_file() or sha(evidence) != row.get("evidence_sha256"):
            errors.append(f"{key}: review evidence missing or changed")
        if key == "google_slides_review" and not row.get("url", "").startswith(
            "https://docs.google.com/presentation/"
        ):
            errors.append("google_slides_review: imported deck URL missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    for name in (
        "build-receipt",
        "zero-verify-errors",
        "contact-sheet-review",
        "google-slides-review",
    ):
        parser.add_argument("--require-" + name, action="store_true")
    args = parser.parse_args()
    try:
        errors = verify(args.bundle, args)
    except (OSError, ValueError, KeyError) as error:
        errors = [str(error)]
    print(json.dumps({"status": "PASS" if not errors else "NOT_READY", "errors": errors}, indent=2))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
