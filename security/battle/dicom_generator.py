"""Retained Battle cases for native DICOM metadata redaction."""
from __future__ import annotations

import json
from pathlib import Path

POLICY = {
    "version": 1,
    "sensitive_values": [
        {"rule_id": "patient", "subject_id": "person-1", "type": "name", "value": "Alice Example"}
    ],
    "protected_values": [],
}


def _elem(group: int, element: int, vr: str, value: bytes) -> bytes:
    if len(value) % 2:
        value += b" "
    return group.to_bytes(2, "little") + element.to_bytes(2, "little") + vr.encode("ascii") + len(value).to_bytes(2, "little") + value


def _write_dicom(path: Path, patient: bytes = b"Alice Example", preamble: bool = True) -> None:
    path.write_bytes((b"\0" * 128 + b"DICM" if preamble else b"BAD!") + _elem(0x0010, 0x0010, "PN", patient) + _elem(0x0008, 0x1030, "LO", b"Chest"))


def _case(root: Path, case_id: str, expectation: str, **kwargs: object) -> tuple[str, str, str]:
    case = root / case_id
    case.mkdir(parents=True, exist_ok=True)
    (case / "policy.json").write_text(json.dumps(POLICY, sort_keys=True), encoding="utf-8")
    _write_dicom(case / "source.dcm", **kwargs)
    (case / "case.json").write_text(json.dumps({"schema": "dicom_battle_case.v1"}, sort_keys=True), encoding="utf-8")
    return case_id, str(case), expectation


def generate(work_dir, params):
    root = Path(work_dir)
    yield _case(root, "dicom-clean-redaction", "MUST_ACCEPT")
    yield _case(root, "dicom-no-policy-match-rejected", "MUST_REJECT", patient=b"Bob Patient")
    yield _case(root, "dicom-invalid-preamble-rejected", "MUST_REJECT", preamble=False)
