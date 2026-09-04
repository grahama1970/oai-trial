"""Guard the specific public overclaims found in WebGPT's final bounded review.

Historical review transcripts are evidence, not current product claims. This
checks evaluator-facing docs and pitch manifests/notes, not archived transcripts.
"""
from __future__ import annotations

import re
from pathlib import Path


def test_public_claims_match_current_evidence() -> None:
    root = Path(__file__).resolve().parents[2]
    paths = [root / p for p in (
        "README.md", "SUBMISSION.md", "docs/ANONYMIZATION_SEMANTICS.md",
        "docs/ARCHITECTURE.md", "docs/ACCEPTANCE_MATRIX.md", "docs/PRIVACY_CONTRACT.md",
        "security/SECURITY.md",
    )]
    pitch = root / "docs/pitch/oai-trial"
    paths += sorted(pitch.rglob("*.yaml")) + sorted(pitch.rglob("*.md"))
    stale = (
        r"domain[- ]extend", r"collisions? (?:are )?extend", r"extended on collision",
        r"203\.0\.113", r"(?:CSV|JSON|TXT)[^.;\n]{0,35}\bstream\b",
        r"relational, not per-row", r"relational-only",
        r"blended per-object orchestration", r"omits per-service orchestration",
        r"SCA hits", r"Semgrep\s*\+\s*Bandit\)\s*\+\s*dependency\s*SCA",
        r"\b\d+ (?:deterministic )?tests\b", r"\b\d+ passed\b",
    )
    for curated, generated in (
        ("deck.curated.yaml", "generated/deck.public.yaml"),
        ("claim_ledger.curated.yaml", "generated/claim_ledger.yaml"),
    ):
        assert (pitch / curated).read_bytes() == (pitch / generated).read_bytes()
    failures = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for pattern in stale:
            if re.search(pattern, text, re.IGNORECASE):
                failures.append(f"{path.relative_to(root)}: {pattern}")
    assert not failures, "\n".join(failures)
    # Ensure the corrections retain the positive contract, not just delete it.
    required = {
        "docs/ANONYMIZATION_SEMANTICS.md": ("198.51.100", "no domain extension"),
        "docs/ARCHITECTURE.md": ("bounded", "per-row", "materialized"),
        "docs/ACCEPTANCE_MATRIX.md": ("namespace_exhausted", "per-row"),
        "SUBMISSION.md": ("per-service", "SQS", "CloudWatch"),
        "security/SECURITY.md": ("no SCA receipt committed",),
        "docs/pitch/oai-trial/deck.curated.yaml": ("bounded", "per-file", "per-row"),
        "docs/pitch/oai-trial/claim_ledger.curated.yaml": ("bounded", "per-file", "per-row"),
    }
    for filename, phrases in required.items():
        text = (root / filename).read_text(encoding="utf-8")
        for phrase in phrases:
            assert phrase in text, f"{filename}: missing {phrase}"
