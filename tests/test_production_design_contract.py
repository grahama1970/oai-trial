"""Acceptance test for round-6 ticket production-svg-contract-drift: the SVG
labels must agree with the production prose (manifest+pointer publication,
retry/replay, quarantine, format-aware distribution)."""
from __future__ import annotations

from pathlib import Path


def test_svg_matches_manifest_pointer_and_retry_flow() -> None:
    svg = Path("docs/production-architecture.svg").read_text(encoding="utf-8")
    prose = Path("docs/production-architecture.md").read_text(encoding="utf-8")
    for label in ("corpus manifest", "active pointer", "retry / replay", "Quarantine",
                  "format-aware", "durable publication boundary"):
        assert label.lower() in svg.lower(), f"SVG missing label: {label}"
    # prose must carry the same publication design the SVG shows
    for term in ("corpus manifest", "active-corpus pointer", "format-aware", "Quarantine"):
        assert term.lower() in prose.lower(), f"prose missing: {term}"
