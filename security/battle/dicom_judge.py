"""Battle Judge for native DICOM redaction receipts and output metadata."""
from __future__ import annotations

import json
from pathlib import Path

RAW = "Alice Example"


def _elems(data: bytes):
    if len(data) < 132 or data[128:132] != b"DICM":
        raise ValueError("not dicom")
    offset = 132
    while offset + 8 <= len(data):
        group = int.from_bytes(data[offset : offset + 2], "little")
        element = int.from_bytes(data[offset + 2 : offset + 4], "little")
        vr = data[offset + 4 : offset + 6].decode("ascii")
        length = int.from_bytes(data[offset + 6 : offset + 8], "little")
        value_offset = offset + 8
        if value_offset + length > len(data):
            raise ValueError("bad length")
        yield group, element, vr, data[value_offset : value_offset + length]
        offset = value_offset + length
    if offset != len(data):
        raise ValueError("trailing bytes")


def judge(target_dir: str, params: dict) -> dict:
    root = Path(target_dir)
    output = root / "out.dcm"
    receipt_path = root / "receipt.json"
    stdout = (root / ".battle-execution" / "stdout.txt").read_text(encoding="utf-8", errors="replace") if (root / ".battle-execution" / "stdout.txt").is_file() else ""
    stderr = (root / ".battle-execution" / "stderr.txt").read_text(encoding="utf-8", errors="replace") if (root / ".battle-execution" / "stderr.txt").is_file() else ""
    violations: list[str] = []
    if not output.is_file() or not receipt_path.is_file():
        surface = stdout + "\n" + stderr
        if "BATTLE_CONTRACT_REJECT" not in surface:
            violations.append("DICOM output and receipt are required")
        if RAW in surface:
            violations.append("rejection surface persisted raw policy literal")
        return {"passed": not violations, "violations": violations, "evidence": {"output_present": output.is_file(), "receipt_present": receipt_path.is_file()}}
    receipt_text = receipt_path.read_text(encoding="utf-8")
    if RAW in receipt_text:
        violations.append("receipt persisted raw policy literal")
    try:
        receipt = json.loads(receipt_text)
    except Exception as exc:
        return {"passed": False, "violations": [f"receipt unreadable:{type(exc).__name__}"], "evidence": {}}
    structural = receipt.get("structural_verification")
    if receipt.get("schema") != "multimodal_redaction.v1" or receipt.get("status") != "ready":
        violations.append("receipt must be ready multimodal_redaction.v1")
    if not isinstance(structural, dict) or structural.get("dicom_preamble_present") is not True or structural.get("policy_literals_absent") is not True:
        violations.append("receipt missing DICOM structural verification")
    data = output.read_bytes()
    if RAW.encode() in data:
        violations.append("output persisted raw policy literal bytes")
    try:
        text_seen = 0
        for _group, _element, vr, value in _elems(data):
            if vr in {"PN", "LO", "SH", "ST", "LT", "UT"}:
                text_seen += 1
                if RAW in value.decode("utf-8", errors="ignore"):
                    violations.append("text VR persisted raw policy literal")
        if text_seen < 1:
            violations.append("no text VR inspected")
    except Exception as exc:
        violations.append(f"DICOM structural read failed:{type(exc).__name__}")
    return {"passed": not violations, "violations": violations, "evidence": {"output_present": output.is_file(), "receipt_present": receipt_path.is_file()}}
