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
import sqlite3
from pathlib import Path
from typing import Any

from .errors import AnonError, AnonErrorCode
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
    raise ValueError(f"unsupported input suffix: {source.suffix}")


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


def _transform_csv(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    raw = source.read_bytes()
    had_bom = raw.startswith(_BOM)
    newline_style = _detect_newline(raw)
    encoding = "utf-8-sig" if had_bom else "utf-8"
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
            text, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant
        )
    except json.JSONDecodeError as error:
        raise AnonError(AnonErrorCode.MALFORMED_JSON, "input is not valid JSON") from error
    transformed, count = _replace_json(value, policy, 0)
    body_out = json.dumps(transformed, indent=2, ensure_ascii=False) + "\n"
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
        for _name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL"
        ):
            if sql and sql.strip().upper().startswith("CREATE VIRTUAL TABLE"):
                raise AnonError(
                    AnonErrorCode.UNSUPPORTED_FORMAT, "virtual tables are not supported"
                )
        tables = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
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


def iter_searchable_text(path: Path):
    if path.suffix in {".csv", ".json", ".txt"}:
        yield path.read_text(encoding="utf-8")
        return
    if path.suffix == ".sqlite":
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
            for table in tables:
                for row in connection.execute(f"SELECT * FROM {_quote(table)}"):  # noqa: S608 (identifier quoted via _quote)
                    for value in row:
                        if isinstance(value, str):
                            yield value
