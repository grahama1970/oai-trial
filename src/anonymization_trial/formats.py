from __future__ import annotations

import csv
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from .policy import Policy, replace_text


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
    text = source.read_text(encoding="utf-8")
    transformed, count = replace_text(text, policy)
    destination.write_text(transformed, encoding="utf-8")
    return max(1, text.count("\n")), count


def _transform_csv(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    count = 0
    for row_index, row in enumerate(rows):
        if row_index == 0:
            continue
        for column_index, value in enumerate(row):
            row[column_index], replaced = replace_text(value, policy)
            count += replaced
    with destination.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    return max(0, len(rows) - 1), count


def _replace_json(value: Any, policy: Policy) -> tuple[Any, int]:
    if isinstance(value, str):
        return replace_text(value, policy)
    if isinstance(value, list):
        output = []
        count = 0
        for item in value:
            updated, replaced = _replace_json(item, policy)
            output.append(updated)
            count += replaced
        return output, count
    if isinstance(value, dict):
        output = {}
        count = 0
        for key, item in value.items():
            updated, replaced = _replace_json(item, policy)
            output[key] = updated
            count += replaced
        return output, count
    return value, 0


def _transform_json(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    value = json.loads(source.read_text(encoding="utf-8"))
    transformed, count = _replace_json(value, policy)
    destination.write_text(json.dumps(transformed, indent=2) + "\n", encoding="utf-8")
    records = len(value) if isinstance(value, list) else 1
    return records, count


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _transform_sqlite(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    shutil.copy2(source, destination)
    records = 0
    replacements = 0
    with sqlite3.connect(destination) as connection:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        for table in tables:
            columns = [row[1] for row in connection.execute(f"PRAGMA table_info({_quote(table)})")]
            rows = list(connection.execute(f"SELECT rowid, * FROM {_quote(table)}"))
            records += len(rows)
            for row in rows:
                rowid, values = row[0], row[1:]
                updates: dict[str, str] = {}
                for column, value in zip(columns, values, strict=True):
                    if isinstance(value, str):
                        transformed, count = replace_text(value, policy)
                        replacements += count
                        if transformed != value:
                            updates[column] = transformed
                if updates:
                    assignments = ", ".join(f"{_quote(name)} = ?" for name in updates)
                    connection.execute(
                        f"UPDATE {_quote(table)} SET {assignments} WHERE rowid = ?",
                        [*updates.values(), rowid],
                    )
        connection.commit()
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise ValueError("SQLite integrity check failed")
    return records, replacements


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
                for row in connection.execute(f"SELECT * FROM {_quote(table)}"):
                    for value in row:
                        if isinstance(value, str):
                            yield value
