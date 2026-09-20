"""Deterministic post-release linkage-risk audit.

This is deliberately narrower than a calibrated re-identification score. It
measures equality/frequency disclosure from this project's stable pseudonyms
without persisting pseudonym values or requiring network/model access.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

from .pipeline import _manifest_digest
from .pseudonyms import ALGORITHM_VERSION, KEY_MODE

SCHEMA = "contextual_privacy_risk.v1"
_PATTERNS = (
    re.compile(rb"Person-[0-9a-f]{10}"),
    re.compile(rb"user-[0-9a-f]{10}@example\.invalid"),
    re.compile(rb"\+1-555-[0-9]{4}"),
    re.compile(rb"198\.51\.100\.(?:[1-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-3])"),
    re.compile(rb"\[REDACTED-[0-9a-f]{10}\]"),
    re.compile(rb"anon-[a-z_]+-[0-9a-f]{10}"),
)


def max_stable_pseudonym_frequency(corpus: Path) -> int:
    """Return the largest stable-pseudonym frequency without retaining values."""
    counts: Counter[bytes] = Counter()
    for path in sorted(corpus.rglob("*")):
        if path.is_file() and not path.is_symlink():
            data = path.read_bytes()
            for pattern in _PATTERNS:
                counts.update(pattern.findall(data))
    return max(counts.values(), default=0)


def assess_stable_pseudonym_frequency(release: Path, min_frequency: int = 2) -> dict:
    """Return aggregate equality-linkage findings without emitting pseudonyms."""
    if min_frequency < 2:
        raise ValueError("min_frequency must be at least 2")
    corpus = release / "corpus"
    report = release / "report.json"
    if not corpus.is_dir() or not report.is_file():
        raise ValueError("input must be a release containing corpus/ and report.json")
    readiness = json.loads(report.read_text(encoding="utf-8"))
    if readiness.get("status") != "ready" or readiness.get("verification_passed") is not True:
        raise ValueError("release is not verified ready")
    if readiness.get("algorithm_version") != ALGORITHM_VERSION:
        raise ValueError("unsupported or missing algorithm_version")
    if readiness.get("key_mode") != KEY_MODE:
        raise ValueError("unsupported or missing key_mode")
    manifest = readiness.get("corpus_manifest_sha256")
    if not isinstance(manifest, str) or manifest != _manifest_digest(corpus):
        raise ValueError("release report does not bind the current corpus manifest")
    if readiness.get("verification_sha256") != manifest:
        raise ValueError("release verification digest does not match corpus manifest")

    counts: Counter[bytes] = Counter()
    files_scanned = 0
    bytes_scanned = 0
    for path in sorted(corpus.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        data = path.read_bytes()
        files_scanned += 1
        bytes_scanned += len(data)
        for pattern in _PATTERNS:
            counts.update(pattern.findall(data))

    frequencies = list(counts.values())
    repeated = [count for count in frequencies if count >= min_frequency]
    verdict = "linkage_risk" if repeated else "clear"
    return {
        "schema": SCHEMA,
        "verdict": verdict,
        "release_ready": False,
        "risk_kind": "stable_pseudonym_frequency",
        "min_frequency": min_frequency,
        "files_scanned": files_scanned,
        "bytes_scanned": bytes_scanned,
        "pseudonym_occurrences": sum(frequencies),
        "unique_pseudonyms": len(frequencies),
        "repeated_groups": len(repeated),
        "max_frequency": max(frequencies, default=0),
        "raw_values_persisted": False,
        "requires_human_review": verdict == "linkage_risk",
        "does_not_establish": [
            "identity of any data subject",
            "calibrated re-identification probability",
            "safety against external auxiliary datasets",
        ],
    }


def write_private_report(path: Path, payload: dict) -> None:
    """Create a mode-0600 report atomically and never overwrite evidence."""
    path = path.resolve()
    if path.exists():
        raise FileExistsError("risk report already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        Path(temporary).unlink(missing_ok=True)
        raise
