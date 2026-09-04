"""Source-snapshot / TOCTOU regression (battle-family: source lineage).

A source file that changes between inventory and reread must not yield a
published release. This is the deterministic, in-repo regression a `$battle`
adaptive-lineage campaign would promote; it needs no battle environment.
"""
from __future__ import annotations

import os
from pathlib import Path

from anonymization_trial.pipeline import _source_digests


def test_source_digest_detects_content_change_even_if_mtime_preserved(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"original bytes")
    files = [(f, Path("a.txt"))]
    before = _source_digests(files)
    stat_before = f.stat()

    # Mutate content, then restore mtime to defeat naive mtime-only checks.
    f.write_bytes(b"tampered bytes!")
    os.utime(f, (stat_before.st_atime, stat_before.st_mtime))

    after = _source_digests(files)
    assert before != after  # digest catches content change despite equal mtime


def test_source_digest_stable_when_unchanged(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"stable")
    files = [(f, Path("a.txt"))]
    assert _source_digests(files) == _source_digests(files)
