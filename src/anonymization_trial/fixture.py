from __future__ import annotations

import csv
import json
import shutil
import sqlite3
from pathlib import Path


IDENTITIES = (
    {"subject_id": "person-001", "name": "Mara Ellison", "email": "mara.ellison@northwind.test", "phone": "+1-202-555-0147", "ip_address": "203.0.113.42"},
    {"subject_id": "person-002", "name": "Jon Bell", "email": "jon.bell@northwind.test", "phone": "+1-202-555-0199", "ip_address": "203.0.113.81"},
)


def _policy() -> dict:
    values = []
    for identity in IDENTITIES:
        for data_type in ("name", "email", "phone", "ip_address"):
            values.append({
                "rule_id": f"{identity['subject_id']}-{data_type}",
                "subject_id": identity["subject_id"],
                "type": data_type,
                "value": identity[data_type],
                "match": "literal",
                "case_sensitive": data_type != "email",
            })
    values.append({
        "rule_id": "shared-api-secret",
        "type": "secret",
        "value": "sk_synthetic_7CWQ0JY5i2",
        "match": "literal",
        "case_sensitive": True,
    })
    return {
        "version": 1,
        "sensitive_values": values,
        "protected_values": [
            {"value": "Northwind Research", "reason": "fictional public organization"},
            {"value": "support@example.invalid", "reason": "approved placeholder"},
        ],
    }


def generate_fixture(target: Path, records: int) -> None:
    if records < 1:
        raise ValueError("records must be positive")
    if target.exists():
        shutil.rmtree(target)
    corpus = target / "corpus"
    corpus.mkdir(parents=True)
    (target / "policy.json").write_text(json.dumps(_policy(), indent=2) + "\n", encoding="utf-8")

    with (corpus / "customers.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["event_id", "name", "email", "region", "company"])
        writer.writeheader()
        for index in range(records):
            identity = IDENTITIES[index % len(IDENTITIES)]
            writer.writerow({
                "event_id": index,
                "name": identity["name"],
                "email": identity["email"],
                "region": "us-east" if index % 2 else "eu-west",
                "company": "Northwind Research",
            })

    events = []
    for index in range(records):
        identity = IDENTITIES[index % len(IDENTITIES)]
        events.append({
            "event_id": index,
            "actor": {"name": identity["name"], "email": identity["email"]},
            "network": {"ip": identity["ip_address"]},
            "event": "document.viewed",
            "metadata": {"approved_contact": "support@example.invalid"},
        })
    (corpus / "events.json").write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")

    lines = []
    for index in range(records):
        identity = IDENTITIES[index % len(IDENTITIES)]
        secret = " sk_synthetic_7CWQ0JY5i2" if index == records - 1 else ""
        padding = "x" * 4096 if index == records // 2 else ""
        lines.append(
            f"ticket={index} owner={identity['name']} phone={identity['phone']} "
            f"status=open company=Northwind Research{secret} {padding}".rstrip()
        )
    (corpus / "support-notes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with sqlite3.connect(corpus / "accounts.sqlite") as connection:
        connection.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                region TEXT NOT NULL
            );
            CREATE TABLE activity (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                detail TEXT NOT NULL
            );
            CREATE INDEX activity_user_idx ON activity(user_id);
        """)
        for user_id, identity in enumerate(IDENTITIES, start=1):
            connection.execute(
                "INSERT INTO users(id, name, email, region) VALUES (?, ?, ?, ?)",
                (user_id, identity["name"], identity["email"], "us-east"),
            )
        for index in range(records):
            identity_index = index % len(IDENTITIES)
            identity = IDENTITIES[identity_index]
            connection.execute(
                "INSERT INTO activity(id, user_id, detail) VALUES (?, ?, ?)",
                (index + 1, identity_index + 1, f"Login from {identity['ip_address']}"),
            )
        connection.commit()
