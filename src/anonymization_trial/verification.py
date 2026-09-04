"""Independent whole-corpus verification, decoupled from the transform path.

Inputs: the original source corpus directory, the staged output corpus
directory, and the compiled ``Policy``.
Outputs: none on success; raises ``AnonError(VERIFICATION_FAILED)`` on any
mismatch. This module rereads both corpora from disk and never calls the
``transform_*`` functions or trusts their success booleans.
Failure modes: file-set divergence, a surviving sensitive literal in an output
value, or a changed protected-value occurrence count.

Independence: the transform uses the Aho-Corasick matcher; this verifier uses a
plain ``str`` scan over freshly read output, so a matcher bug cannot mask itself.

Subject-level coverage (SPIA arXiv:2604.21211): span-absence alone is a weak
unit of protection. This verifier additionally recomputes the expected
pseudonym per canonical identity and requires every selected source occurrence
to appear as its replacement in output, and requires distinct same-type
identities to hold distinct replacements.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from .errors import AnonError, AnonErrorCode, safe_ref
from .policy import Policy, replace_text
from .pseudonyms import build_replacements


def _expected_json(value: Any, policy: Policy) -> Any:
    """Independent recompute of the transform's JSON contract: keys unchanged,
    string values replaced, scalars untouched. Comparing output == this catches
    swapped pseudonyms, dropped/added keys or items, and relocated protected
    values that aggregate counts miss (review #1)."""
    if isinstance(value, str):
        return replace_text(value, policy)[0]
    if isinstance(value, list):
        return [_expected_json(item, policy) for item in value]
    if isinstance(value, dict):
        return {key: _expected_json(item, policy) for key, item in value.items()}
    return value


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise AnonError(AnonErrorCode.VERIFICATION_FAILED, "duplicate JSON object key")
        seen.add(key)
    return dict(pairs)


def _load_json(path: Path) -> Any:
    # utf-8-sig mirrors the transform's BOM handling (round 3 #5). A duplicate-
    # rejecting parse so a tampered output cannot hide a raw value behind a
    # second same-named key that last-wins would keep (round 2 #3).
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_no_duplicate_keys)


def _verify_sqlite_locations(source: Path, staged: Path, policy: Policy, name: str) -> None:
    """Per-row location oracle for accepted SQLite files (review #1/#14).

    The transform rejects triggers, rowid-shadowing, WITHOUT ROWID, and virtual
    tables, so every accepted table is addressable by hidden rowid. Compare each
    source row to the output row with the same rowid: text cells must equal the
    independent recompute and non-text cells must be byte-identical, which
    catches swapped pseudonyms and unrelated-value mutation that row counts,
    integrity_check, and foreign_key_check cannot see.
    """
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    out = sqlite3.connect(f"file:{staged}?mode=ro", uri=True)
    try:
        q = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        src_tables = sorted(r[0] for r in src.execute(q))
        out_tables = sorted(r[0] for r in out.execute(q))
        if src_tables != out_tables:
            raise AnonError(
                AnonErrorCode.VERIFICATION_FAILED, f"sqlite table set changed in {safe_ref(name)}"
            )
        for table in src_tables:
            ident = '"' + table.replace('"', '""') + '"'
            sel = f"SELECT rowid, * FROM {ident} ORDER BY rowid"  # noqa: S608 (quoted)
            for s_row, o_row in zip(
                src.execute(sel), out.execute(sel), strict=True
            ):
                if s_row[0] != o_row[0]:
                    raise AnonError(
                        AnonErrorCode.VERIFICATION_FAILED,
                            f"sqlite row identity changed in {safe_ref(name)}"
                    )
                for s_val, o_val in zip(s_row[1:], o_row[1:], strict=True):
                    expected = replace_text(s_val, policy)[0] if isinstance(s_val, str) else s_val
                    if not _typed_equal(o_val, expected):
                        raise AnonError(
                            AnonErrorCode.VERIFICATION_FAILED,
                            f"sqlite cell location mismatch in {safe_ref(name)}",
                        )
    finally:
        src.close()
        out.close()


def _typed_equal(a: Any, b: Any) -> bool:
    """Equality that also requires identical scalar TYPES (round6 #1).

    Python's == treats True == 1 and 1 == 1.0 as equal, so a JSON true mutated
    to 1, or a SQLite INTEGER mutated to REAL, would pass a plain != check.
    """
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_typed_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(
            _typed_equal(x, y) for x, y in zip(a, b, strict=True)
        )
    return a == b


def _csv_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.reader(handle))


def _verify_locations(source_corpus: Path, staged_corpus: Path, output_files: set[Path],
                      policy: Policy) -> None:
    """Per-location structural verification for JSON and CSV (review #1)."""
    for rel in sorted(output_files):
        if rel.suffix == ".json":
            src = _load_json(source_corpus / rel)
            out = _load_json(staged_corpus / rel)
            if not _typed_equal(out, _expected_json(src, policy)):
                raise AnonError(
                    AnonErrorCode.VERIFICATION_FAILED,
                        f"json location mismatch in {safe_ref(rel.name)}"
                )
        elif rel.suffix == ".sqlite":
            _verify_sqlite_locations(source_corpus / rel, staged_corpus / rel, policy, rel.name)
        elif rel.suffix == ".csv":
            src_rows = _csv_rows(source_corpus / rel)
            out_rows = _csv_rows(staged_corpus / rel)
            if len(src_rows) != len(out_rows):
                raise AnonError(
                    AnonErrorCode.VERIFICATION_FAILED,
                        f"csv row count changed in {safe_ref(rel.name)}"
                )
            for src_row, out_row in zip(src_rows, out_rows, strict=True):
                if len(src_row) != len(out_row):
                    raise AnonError(
                        AnonErrorCode.VERIFICATION_FAILED,
                            f"csv column count changed in {safe_ref(rel.name)}"
                    )
                for src_cell, out_cell in zip(src_row, out_row, strict=True):
                    if replace_text(src_cell, policy)[0] != out_cell:
                        raise AnonError(
                            AnonErrorCode.VERIFICATION_FAILED,
                            f"csv cell location mismatch in {safe_ref(rel.name)}",
                        )


def _relative_files(root: Path) -> set[Path]:
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}


def _searchable(root: Path, relatives: set[Path]) -> list[str]:
    from .formats import iter_searchable_text  # local import avoids a cycle

    texts: list[str] = []
    for rel in sorted(relatives):
        texts.extend(iter_searchable_text(root / rel))
    return texts


def _count(needle: str, texts: list[str], case_sensitive: bool) -> int:
    probe = needle if case_sensitive else needle.casefold()
    return sum((text if case_sensitive else text.casefold()).count(probe) for text in texts)


def verify_corpus(source_corpus: Path, staged_corpus: Path, policy: Policy) -> None:
    """Fail closed unless the staged corpus is a safe release of the source."""
    from .formats import iter_searchable_text

    source_files = _relative_files(source_corpus)
    output_files = _relative_files(staged_corpus)
    if source_files != output_files:
        raise AnonError(AnonErrorCode.VERIFICATION_FAILED, "source and output file sets differ")

    for rel in sorted(output_files):
        for text in iter_searchable_text(staged_corpus / rel):
            for rule in policy.rules:
                haystack = text if rule.case_sensitive else text.casefold()
                needle = rule.value if rule.case_sensitive else rule.value.casefold()
                if needle in haystack:
                    raise AnonError(
                        AnonErrorCode.VERIFICATION_FAILED,
                        f"a sensitive literal survived in {safe_ref(rel.name)}",
                    )

    # Value-level skeleton for text files: independently recompute the expected
    # output from source+policy and compare. Catches swapped/wrong pseudonyms
    # and partial replacement that presence/count checks miss. (Text only;
    # other formats keep structural + count checks.)
    for rel in sorted(output_files):
        if rel.suffix == ".txt":
            src_text = (source_corpus / rel).read_text(encoding="utf-8")
            out_text = (staged_corpus / rel).read_text(encoding="utf-8")
            if replace_text(src_text, policy)[0] != out_text:
                raise AnonError(
                    AnonErrorCode.VERIFICATION_FAILED,
                        f"text value skeleton mismatch in {safe_ref(rel.name)}"
                )

    _verify_locations(source_corpus, staged_corpus, output_files, policy)

    source_texts = _searchable(source_corpus, source_files)
    output_texts = _searchable(staged_corpus, output_files)
    for protected in policy.protected_values:
        if _count(protected, source_texts, True) != _count(protected, output_texts, True):
            raise AnonError(
                AnonErrorCode.VERIFICATION_FAILED, "a protected value occurrence count changed"
            )

    _verify_subject_level(policy, source_texts, output_texts)


def _verify_subject_level(policy: Policy, source_texts: list[str], output_texts: list[str]) -> None:
    """Subject-level coverage + same-type distinctness (independent recompute)."""
    replacements = build_replacements([rule.identity for rule in policy.rules], policy.version)

    # Distinctness: no two identities of the same data type share a replacement.
    by_type: dict[str, set[str]] = {}
    for (data_type, _identity), replacement in replacements.items():
        seen = by_type.setdefault(data_type, set())
        if replacement in seen:
            raise AnonError(
                AnonErrorCode.VERIFICATION_FAILED, "two identities share a type replacement"
            )
        seen.add(replacement)

    # Coverage (presence-based, nesting-safe): any identity whose alias appears in
    # the source must have its pseudonym present in output. Exact removal is
    # already proven by the literal-absence scan above; counting per-rule would
    # double-count nested aliases ("Ada" inside "Ada Lovelace").
    present: set[tuple[str, str]] = set()
    for rule in policy.rules:
        if _count(rule.value, source_texts, rule.case_sensitive) > 0:
            present.add(rule.identity)
    for identity in present:
        if _count(replacements[identity], output_texts, True) < 1:
            raise AnonError(
                AnonErrorCode.VERIFICATION_FAILED, "a subject's pseudonym is missing from output"
            )
