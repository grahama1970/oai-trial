"""Opt-in, bounded RapidFuzz name-alias proposals; never fuzzy runtime replacement.

Whole structured string values and whole text lines only, not NLP span discovery.
Reports contain raw candidate names and must remain private. Approval re-derives
proposals from the current snapshot and emits a separately validated exact policy.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .bundle import separate_output
from .errors import AnonError, AnonErrorCode
from .formats import (
    _finite_float,
    _no_duplicate_keys,
    _quote,
    _reject_constant,
    _reject_unsupported_csv_dialect,
)
from .matcher import ascii_lower
from .pipeline import _manifest_digest, _preflight
from .policy import _no_duplicate_keys as policy_keys
from .policy import compile_policy, load_policy


def _reject(code: AnonErrorCode, message: str):
    raise AnonError(code, message)


def _name(value: str) -> bool:
    return (
        3 <= len(value) <= 128
        and sum(c.isalpha() for c in value) >= 3
        and all(c.isalpha() or c in " '-." for c in value)
    )


@dataclass(frozen=True)
class Candidate:
    id: str
    value: str
    rule_id: str
    subject_id: str
    similarity: float
    occurrences: int

    def validate(self):
        if (
            not all(
                type(x) is str and x for x in (self.id, self.value, self.rule_id, self.subject_id)
            )
            or not _name(self.value)
            or len(self.id) != 24
            or any(c not in "0123456789abcdef" for c in self.id)
            or type(self.similarity) not in (float, int)
            or not math.isfinite(self.similarity)
            or not 0 <= self.similarity <= 100
            or type(self.occurrences) is not int
            or self.occurrences < 1
        ):
            _reject(AnonErrorCode.DISCOVERY_INVALID, "invalid candidate fields")


@dataclass(frozen=True)
class DiscoveryReport:
    policy_sha256: str
    corpus_sha256: str
    rapidfuzz_version: str
    threshold: float
    margin: float
    candidates: list[Candidate]
    counts: dict[str, int]
    schema: str = "anon.discovery_review.v1"
    release_ready: bool = False
    seam_validation: dict[str, str] = field(
        default_factory=lambda: {
            "kind": "discovery_review",
            "status": "PASS",
        }
    )

    def validate(self):
        for value in (self.policy_sha256, self.corpus_sha256):
            if (
                type(value) is not str
                or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)
            ):
                _reject(AnonErrorCode.DISCOVERY_INVALID, "invalid source digest")
        for value, low, high in ((self.threshold, 80, 100), (self.margin, 0, 20)):
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not low <= value <= high
            ):
                _reject(AnonErrorCode.DISCOVERY_INVALID, "threshold must be 80..100; margin 0..20")
        if (
            self.schema != "anon.discovery_review.v1"
            or self.release_ready is not False
            or type(self.rapidfuzz_version) is not str
            or not self.rapidfuzz_version
            or self.seam_validation != {"kind": "discovery_review", "status": "PASS"}
            or not isinstance(self.candidates, list)
            or not isinstance(self.counts, dict)
        ):
            _reject(AnonErrorCode.DISCOVERY_INVALID, "invalid review contract")
        if set(self.counts) != {
            "values",
            "proposed",
            "known",
            "protected",
            "noise",
            "low_score",
            "ambiguous",
        }:
            _reject(AnonErrorCode.DISCOVERY_INVALID, "invalid review counts")
        if any(type(n) is not int or n < 0 for n in self.counts.values()):
            _reject(AnonErrorCode.DISCOVERY_INVALID, "invalid review counts")
        for candidate in self.candidates:
            candidate.validate()
            if candidate.similarity < self.threshold:
                _reject(AnonErrorCode.DISCOVERY_INVALID, "candidate is below threshold")
        if len({c.id for c in self.candidates}) != len(self.candidates):
            _reject(AnonErrorCode.DISCOVERY_INVALID, "duplicate candidate ids")
        if (
            self.counts["proposed"] != len(self.candidates)
            or sum(n for k, n in self.counts.items() if k != "values") > self.counts["values"]
            or sum(c.occurrences for c in self.candidates) > self.counts["values"]
        ):
            _reject(AnonErrorCode.DISCOVERY_INVALID, "candidate count mismatch")
        return self


def _strings(path: Path):
    if path.suffix == ".sqlite":
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            tables = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'"
            ).fetchall()
            for (table,) in tables:
                for row in db.execute(f"SELECT * FROM {_quote(table)}"):  # noqa: S608 (quoted)
                    yield from (v for v in row if isinstance(v, str))
        return
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".txt":
        yield from text.splitlines()
    elif path.suffix == ".csv":
        _reject_unsupported_csv_dialect(text)
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = csv.reader(handle, strict=True)
            next(rows, None)  # no discovery in schema/header names
            for row in rows:
                yield from row
    elif path.suffix == ".json":
        data = json.loads(
            text,
            object_pairs_hook=_no_duplicate_keys,
            parse_float=_finite_float,
            parse_constant=_reject_constant,
        )
        stack = [(data, 0)]
        while stack:
            value, depth = stack.pop()
            if depth > 200:
                _reject(AnonErrorCode.STRUCTURE_TOO_COMPLEX, "discovery JSON is too deep")
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                stack.extend((v, depth + 1) for v in value.values())
            elif isinstance(value, list):
                stack.extend((v, depth + 1) for v in value)


def discover(bundle: Path, threshold: float = 90, margin: float = 5) -> DiscoveryReport:
    try:
        import rapidfuzz
        from rapidfuzz import fuzz, process
    except ImportError as error:
        raise AnonError(
            AnonErrorCode.DISCOVERY_UNAVAILABLE, "install the discovery extra"
        ) from error
    policy = load_policy(bundle / "policy.json")
    policy_hash = hashlib.sha256((bundle / "policy.json").read_bytes()).hexdigest()
    corpus_hash = _manifest_digest(bundle / "corpus")
    counts = dict.fromkeys(
        ["values", "proposed", "known", "protected", "noise", "low_score", "ambiguous"], 0
    )
    report = DiscoveryReport(
        policy_hash, corpus_hash, rapidfuzz.__version__, threshold, margin, [], counts
    ).validate()
    rules = sorted(
        (r for r in policy.rules if r.data_type == "name" and _name(r.value)),
        key=lambda r: (r.identity, r.rule_id),
    )
    if len(rules) > 1000:
        _reject(AnonErrorCode.STRUCTURE_TOO_COMPLEX, "discovery permits at most 1000 name rules")
    choices = [ascii_lower(r.value) for r in rules]
    values: Counter[str] = Counter()
    try:
        files = _preflight(bundle, bundle.parent / "discovery-output-boundary", policy)
        for path, _relative in files:
            for value in _strings(path):
                counts["values"] += 1
                if counts["values"] > 10_000:
                    _reject(
                        AnonErrorCode.STRUCTURE_TOO_COMPLEX,
                        "discovery permits at most 10000 text values",
                    )
                values[value] += 1
    except UnicodeError as error:
        raise AnonError(AnonErrorCode.MALFORMED_ENCODING, "discovery input is not UTF-8") from error
    except json.JSONDecodeError as error:
        raise AnonError(AnonErrorCode.MALFORMED_JSON, "discovery JSON is malformed") from error
    except RecursionError as error:
        raise AnonError(
            AnonErrorCode.STRUCTURE_TOO_COMPLEX, "discovery input is too deep"
        ) from error
    except (csv.Error, sqlite3.Error) as error:
        raise AnonError(AnonErrorCode.UNSUPPORTED_FORMAT, "unreadable discovery input") from error
    for value, occurrences in sorted(values.items()):
        if any(p in value for p in policy.protected_values):
            counts["protected"] += 1
            continue
        if any(
            value == r.value
            or (not r.case_sensitive and ascii_lower(value) == ascii_lower(r.value))
            for r in policy.rules
        ):
            counts["known"] += 1
            continue
        if not _name(value):
            counts["noise"] += 1
            continue
        # ponytail: bounded whole-value scan; use a vocabulary index if these limits grow.
        ranked = process.extract(
            ascii_lower(value), choices, scorer=fuzz.ratio, processor=None, limit=None
        )
        identities = {}
        for _match, score, index in ranked:
            rule = rules[index]
            if rule.identity not in identities:
                identities[rule.identity] = (score, rule)
        best = sorted(identities.values(), key=lambda x: (-x[0], x[1].identity))
        if not best or best[0][0] < threshold:
            counts["low_score"] += 1
            continue
        score, rule = best[0]
        if len(best) > 1 and (score == best[1][0] or score - best[1][0] < margin):
            counts["ambiguous"] += 1
            continue
        ident = hashlib.sha256(
            json.dumps([policy_hash, corpus_hash, rule.rule_id, value], ensure_ascii=True).encode()
        ).hexdigest()[:24]
        report.candidates.append(
            Candidate(ident, value, rule.rule_id, rule.identity[1], round(score, 6), occurrences)
        )
    counts["proposed"] = len(report.candidates)
    # Guard snapshot identity after reads, before emitting any review file.
    if corpus_hash != _manifest_digest(bundle / "corpus"):
        _reject(AnonErrorCode.DISCOVERY_STALE, "corpus changed during discovery")
    return report.validate()


def write_private(path: Path, payload: dict) -> None:
    """Create a new private work artifact; never overwrite an existing file."""
    if path.name == "report.json":
        _reject(AnonErrorCode.DISCOVERY_INVALID, "report.json is reserved for release readiness")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def approve(bundle: Path, review_path: Path, ids: list[str], output: Path) -> dict:
    separate_output(output, bundle, review_path)
    try:
        raw = json.loads(review_path.read_text(), object_pairs_hook=policy_keys)
        supplied = DiscoveryReport(
            **{**raw, "candidates": [Candidate(**c) for c in raw["candidates"]]}
        )
        supplied.validate()
    except (TypeError, KeyError, RecursionError) as error:
        raise AnonError(AnonErrorCode.DISCOVERY_INVALID, "invalid review fields") from error
    fresh = discover(bundle, supplied.threshold, supplied.margin)
    if asdict(fresh) != asdict(supplied):
        _reject(AnonErrorCode.DISCOVERY_STALE, "review differs from current inputs or settings")
    by_id = {c.id: c for c in fresh.candidates}
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(by_id):
        _reject(AnonErrorCode.DISCOVERY_REJECTED, "approve explicit, unique proposed candidate ids")
    payload = json.loads((bundle / "policy.json").read_text(), object_pairs_hook=policy_keys)
    for identity in sorted(ids):
        c = by_id[identity]
        payload["sensitive_values"].append(
            {
                "rule_id": "fuzzy-" + c.id,
                "subject_id": c.subject_id,
                "type": "name",
                "value": c.value,
                "match": "literal",
                "case_sensitive": True,
            }
        )
    compile_policy(payload)  # real consumer validator, including protected overlap rejection
    receipt_path = output.with_name(output.name + ".approval.json")
    if receipt_path.exists():
        _reject(AnonErrorCode.DISCOVERY_REJECTED, "approval receipt already exists")
    write_private(output, payload)
    receipt = {
        "schema": "anon.discovery_approval.v1",
        "approved_ids": sorted(ids),
        "source_policy_sha256": fresh.policy_sha256,
        "source_corpus_sha256": fresh.corpus_sha256,
        "policy_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "release_ready": False,
        "seam_validation": {"kind": "compiled_policy", "status": "PASS"},
    }
    try:
        write_private(receipt_path, receipt)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return receipt
