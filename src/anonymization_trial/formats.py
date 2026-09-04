"""Per-format value transformers for CSV, JSON, UTF-8 text, and SQLite.

Inputs: a source file, a destination path, and a loaded ``Policy``.
Outputs: the transformed file written to destination in the same logical format,
plus ``(records, replacements)`` counts; ``iter_searchable_text`` yields output
strings for verification.
Failure modes: raises ``ValueError`` on an unsupported suffix or a SQLite
integrity-check failure; decoding is strict UTF-8 and raises on malformed input.
"""
from __future__ import annotations

import csv
import json
import math
import sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .errors import AnonError, AnonErrorCode, safe_ref
from .policy import Policy, replace_text

_BOM = b"\xef\xbb\xbf"


def _count_lines(text: str) -> int:
    """Physical line count: empty=0; final line without newline still counts."""
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def _detect_newline(raw: bytes) -> str:
    return "\r\n" if b"\r\n" in raw else "\n"

SUPPORTED_SUFFIXES = {".csv", ".json", ".txt", ".sqlite"}


def transform_file(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == ".csv":
        return _transform_csv(source, destination, policy)
    if source.suffix == ".json":
        return _transform_json(source, destination, policy)
    if source.suffix == ".txt":
        return _transform_text(source, destination, policy)
    if source.suffix == ".sqlite":
        return _transform_sqlite(source, destination, policy)
    raise ValueError(f"unsupported input suffix {safe_ref(source.suffix)}")


def _transform_text(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    raw = source.read_bytes()
    had_bom = raw.startswith(_BOM)
    body = raw[len(_BOM):] if had_bom else raw
    try:
        text = body.decode("utf-8")  # strict; no normalization
    except UnicodeDecodeError as error:
        raise AnonError(AnonErrorCode.MALFORMED_ENCODING, "text file is not valid UTF-8") from error
    transformed, count = replace_text(text, policy)
    out = ("\ufeff" if had_bom else "") + transformed
    destination.write_bytes(out.encode("utf-8"))  # exact bytes; BOM preserved
    return _count_lines(text), count


def _reject_unsupported_csv_dialect(text: str) -> None:
    """Accept only comma CSV; alternate delimiters must be in quoted fields.

    Check every record before writing output, including multiline quoted cells.
    Quotes open only at a comma-field boundary; doubled quotes escape a quote.
    Ambiguous unquoted punctuation is rejected rather than guessed as a dialect.
    """
    state = "start"
    for char in text:
        if state == "quoted":
            if char == '"':
                state = "closed"
        elif char == '"' and state in {"start", "closed"}:
            state = "quoted"
        elif char in ",\r\n":
            state = "start"
        elif state == "closed" or char in ';\t|"':
            raise AnonError(AnonErrorCode.UNSUPPORTED_FORMAT, "unsupported CSV dialect")
        else:
            state = "unquoted"
    if state == "quoted":
        raise AnonError(AnonErrorCode.UNSUPPORTED_FORMAT, "unsupported CSV dialect")


def _transform_csv(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    raw = source.read_bytes()
    had_bom = raw.startswith(_BOM)
    newline_style = _detect_newline(raw)
    encoding = "utf-8-sig" if had_bom else "utf-8"
    body = raw[len(_BOM):] if had_bom else raw
    try:
        _reject_unsupported_csv_dialect(body.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise AnonError(AnonErrorCode.MALFORMED_ENCODING, "CSV file is not valid UTF-8") from error
    count = 0
    data_rows = 0
    try:
        with source.open("r", encoding=encoding, newline="") as src, \
                destination.open("w", encoding="utf-8", newline="") as dst:
            if had_bom:
                dst.write("\ufeff")
            reader = csv.reader(src)
            writer = csv.writer(dst, lineterminator=newline_style)
            header_done = False
            for row in reader:  # streamed row by row
                if not header_done:
                    for cell in row:
                        if policy.matcher.find(cell):
                            raise AnonError(
                                AnonErrorCode.SENSITIVE_IN_SCHEMA,
                                "a sensitive literal occurs in a CSV header",
                            )
                    writer.writerow(row)  # header preserved exactly
                    header_done = True
                    continue
                new_row = []
                for cell in row:
                    replaced_cell, replaced = replace_text(cell, policy)
                    new_row.append(replaced_cell)
                    count += replaced
                writer.writerow(new_row)
                data_rows += 1
    except UnicodeDecodeError as error:
        raise AnonError(AnonErrorCode.MALFORMED_ENCODING, "CSV file is not valid UTF-8") from error
    return data_rows, count


_MAX_DEPTH = 200
_MAX_STRING = 1_000_000


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise AnonError(AnonErrorCode.MALFORMED_JSON, "duplicate JSON object key")
        seen.add(key)
    return dict(pairs)


def _reject_constant(_: str) -> Any:
    raise AnonError(AnonErrorCode.MALFORMED_JSON, "non-finite JSON number is not allowed")


def _finite_float(token: str) -> float:
    # parse_constant only fires for the Infinity/NaN *literals*; an overflowing
    # number token like 1e400 reaches parse_float and becomes float('inf'),
    # which json.dumps would then emit as invalid `Infinity`. Reject it here.
    value = float(token)
    if not math.isfinite(value):
        raise AnonError(AnonErrorCode.MALFORMED_JSON, "non-finite JSON number is not allowed")
    # A float literal that does not round-trip through IEEE-754 would be
    # re-emitted as a DIFFERENT number (9007199254740993.0 -> ...992.0, or a
    # tiny exponent underflowing to 0.0), silently changing non-sensitive data.
    # Fail closed rather than preserve the wrong value (review round 2 #6).
    try:
        if Decimal(token) != Decimal(repr(value)):
            raise AnonError(
                AnonErrorCode.MALFORMED_JSON, "JSON number cannot be preserved exactly"
            )
    except InvalidOperation as error:
        raise AnonError(AnonErrorCode.MALFORMED_JSON, "invalid JSON number") from error
    return value


def _replace_json(value: Any, policy: Policy, depth: int) -> tuple[Any, int]:
    if depth > _MAX_DEPTH:
        raise AnonError(
            AnonErrorCode.STRUCTURE_TOO_COMPLEX, "JSON nesting exceeds the depth bound"
        )
    if isinstance(value, str):
        if len(value) > _MAX_STRING:
            raise AnonError(
                AnonErrorCode.STRUCTURE_TOO_COMPLEX, "JSON string exceeds the size bound"
            )
        return replace_text(value, policy)
    if isinstance(value, list):
        output = []
        count = 0
        for item in value:
            updated, replaced = _replace_json(item, policy, depth + 1)
            output.append(updated)
            count += replaced
        return output, count
    if isinstance(value, dict):
        output = {}
        count = 0
        for key, item in value.items():
            if len(key) > _MAX_STRING:
                raise AnonError(
                    AnonErrorCode.STRUCTURE_TOO_COMPLEX, "JSON key exceeds the size bound"
                )
            if policy.matcher.find(key):
                raise AnonError(
                    AnonErrorCode.SENSITIVE_IN_SCHEMA,
                    "a sensitive literal occurs in a JSON key",
                )
            updated, replaced = _replace_json(item, policy, depth + 1)
            output[key] = updated  # key preserved, never anonymized
            count += replaced
        return output, count
    return value, 0  # bool/int/float/null unchanged


def _transform_json(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    raw = source.read_bytes()
    had_bom = raw.startswith(_BOM)
    body = raw[len(_BOM):] if had_bom else raw
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AnonError(AnonErrorCode.MALFORMED_ENCODING, "JSON file is not valid UTF-8") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except json.JSONDecodeError as error:
        raise AnonError(AnonErrorCode.MALFORMED_JSON, "input is not valid JSON") from error
    transformed, count = _replace_json(value, policy, 0)
    body_out = json.dumps(transformed, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    out = ("\ufeff" if had_bom else "") + body_out
    destination.write_bytes(out.encode("utf-8"))
    records = len(value) if isinstance(value, list) else 1
    return records, count


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _writable_columns(connection: sqlite3.Connection, table: str, policy: Policy) -> list[str]:
    """Return non-generated, non-hidden column names; reject sensitive identifiers.

    PRAGMA table_xinfo hidden flag: 0 normal, 1 hidden, 2 generated-virtual,
    3 generated-stored. Only flag 0 is safely writable.
    """
    writable: list[str] = []
    for row in connection.execute(f"PRAGMA table_xinfo({_quote(table)})"):
        name, hidden = row[1], row[6]
        if policy.matcher.find(name):
            raise AnonError(
                AnonErrorCode.SENSITIVE_IN_SCHEMA, "a sensitive literal occurs in a column name"
            )
        if hidden == 0:
            writable.append(name)
    return writable


def _snapshot_sqlite(source: Path, destination: Path) -> None:
    """Copy a consistent snapshot via the online backup API (WAL-safe)."""
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    try:
        dst = sqlite3.connect(destination)
        try:
            src.backup(dst)
        finally:
            dst.close()
    except sqlite3.Error as error:
        raise AnonError(
            AnonErrorCode.UNSUPPORTED_FORMAT, "unreadable or malformed SQLite database"
        ) from error
    finally:
        src.close()


def _transform_sqlite(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    _snapshot_sqlite(source, destination)
    records = 0
    replacements = 0
    with sqlite3.connect(destination) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for obj_name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL"
        ):
            if sql and sql.strip().upper().startswith("CREATE VIRTUAL TABLE"):
                raise AnonError(
                    AnonErrorCode.UNSUPPORTED_FORMAT, "virtual tables are not supported"
                )
            # A policy literal embedded in ANY schema object (view SQL, index
            # expression, default, object name) is retained DDL that neither the
            # row transform nor the row verifier touches -- e.g. CREATE VIEW
            # leaked AS SELECT 'Alice'. Reject rather than publish (round5 #1).
            if policy.matcher.find(obj_name) or (sql and policy.matcher.find(sql)):
                raise AnonError(
                    AnonErrorCode.SENSITIVE_IN_SCHEMA,
                    "a sensitive literal occurs in a SQLite schema object",
                )
        # Triggers can mutate unrelated columns during an UPDATE, which the
        # relational verifier cannot reproduce; reject rather than certify blind
        # (review #14). Fail-closed on constructs the verifier cannot mirror.
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type='trigger'").fetchone():
            raise AnonError(AnonErrorCode.UNSUPPORTED_FORMAT, "triggers are not supported")
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'"
        ).fetchall()
        pre_counts: dict[str, int] = {}
        for table, sql in tables:
            if policy.matcher.find(table):
                raise AnonError(
                    AnonErrorCode.SENSITIVE_IN_SCHEMA, "a sensitive literal occurs in a table name"
                )
            if sql and "WITHOUT ROWID" in sql.upper():
                raise AnonError(
                    AnonErrorCode.UNSUPPORTED_FORMAT, "WITHOUT ROWID tables are not supported"
                )
            # A user column named rowid/oid/_rowid_ shadows the hidden row id, so
            # `WHERE rowid = ?` would match that column's value and could update
            # several rows at once. An `INTEGER PRIMARY KEY` column IS the rowid
            # alias (unique, safe); only a non-alias shadow is rejected (#14).
            for info in connection.execute(f"PRAGMA table_info({_quote(table)})"):
                name, ctype, is_pk = info[1], (info[2] or ""), info[5]
                is_rowid_alias = bool(is_pk) and ctype.upper() == "INTEGER"
                if name.lower() in {"rowid", "oid", "_rowid_"} and not is_rowid_alias:
                    raise AnonError(
                        AnonErrorCode.UNSUPPORTED_FORMAT,
                        "a column shadows the SQLite rowid",
                    )
            writable = _writable_columns(connection, table, policy)
            pre_counts[table] = connection.execute(
                f"SELECT COUNT(*) FROM {_quote(table)}"  # noqa: S608 (identifier quoted)
            ).fetchone()[0]
            if not writable:
                records += pre_counts[table]
                continue
            select_cols = ", ".join(_quote(c) for c in writable)
            query = f"SELECT rowid, {select_cols} FROM {_quote(table)}"  # noqa: S608 (quoted)
            rows = connection.execute(query).fetchall()
            records += len(rows)
            for row in rows:
                rowid, values = row[0], row[1:]
                updates: dict[str, str] = {}
                for column, value in zip(writable, values, strict=True):
                    if isinstance(value, str):
                        transformed, count = replace_text(value, policy)
                        replacements += count
                        if transformed != value:
                            updates[column] = transformed
                if updates:
                    assignments = ", ".join(f"{_quote(name)} = ?" for name in updates)
                    connection.execute(
                        f"UPDATE {_quote(table)} SET {assignments} WHERE rowid = ?",  # noqa: S608
                        [*updates.values(), rowid],
                    )
        connection.commit()
        _verify_sqlite(connection, pre_counts)
    return records, replacements


def _verify_sqlite(connection: sqlite3.Connection, pre_counts: dict[str, int]) -> None:
    """Independent relational checks: row counts, integrity, foreign keys."""
    for table, expected in pre_counts.items():
        actual = connection.execute(
            f"SELECT COUNT(*) FROM {_quote(table)}"  # noqa: S608 (identifier quoted)
        ).fetchone()[0]
        if actual != expected:
            raise AnonError(AnonErrorCode.VERIFICATION_FAILED, "SQLite row count changed")
    integ = connection.execute("PRAGMA integrity_check").fetchone()
    if not integ or integ[0] != "ok":
        raise AnonError(AnonErrorCode.VERIFICATION_FAILED, "SQLite integrity_check failed")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise AnonError(AnonErrorCode.VERIFICATION_FAILED, "SQLite foreign_key_check failed")


def _json_strings(value: Any):
    # Yield DECODED keys + string values so a verifier scans real values, not the
    # serialized text (review #2): an escaped "\u0041lice" in output decodes to
    # "Alice" and must not slip past a literal scan of the raw bytes.
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _json_strings(item)
    elif isinstance(value, str):
        yield value


def iter_searchable_text(path: Path):
    if path.suffix == ".json":
        # utf-8-sig strips a leading BOM the transform is allowed to preserve, so
        # the verifier parser mirrors the transform parser (review round 3 #5).
        # Duplicate keys must be rejected on the OUTPUT path too: a tampered
        # {"who":"Alice","who":"<pseudonym>"} would otherwise be read last-wins,
        # hiding the raw sensitive first value (review round 2 #3).
        parsed = json.loads(
            path.read_text(encoding="utf-8-sig"), object_pairs_hook=_no_duplicate_keys
        )
        yield from _json_strings(parsed)
        return
    if path.suffix in {".csv", ".txt"}:
        yield path.read_text(encoding="utf-8")
        return
    if path.suffix == ".sqlite":
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'"
                )
            ]
            for table in tables:
                for row in connection.execute(f"SELECT * FROM {_quote(table)}"):  # noqa: S608 (identifier quoted via _quote)
                    for value in row:
                        if isinstance(value, str):
                            yield value
