"""Battle Judge for native DICOM redaction receipts and output metadata."""
from __future__ import annotations

import json
from pathlib import Path

RAW = "Alice Example"
IMPLICIT = "1.2.840.10008.1.2"
BIG = "1.2.840.10008.1.2.2"
TEXT_VRS = {"AE", "AS", "CS", "DA", "DS", "DT", "LO", "LT", "PN", "SH", "ST", "TM", "UC", "UI", "UR", "UT"}
LONG_VRS = {"OB", "OD", "OF", "OL", "OW", "SQ", "UC", "UN", "UR", "UT"}
KNOWN_VRS = {
    (0x0002, 0x0010): "UI",
    (0x0008, 0x0020): "DA",
    (0x0008, 0x1030): "LO",
    (0x0010, 0x0010): "PN",
    (0x7FE0, 0x0010): "OB",
}


def _explicit_little(data: bytes, offset: int):
    group = int.from_bytes(data[offset : offset + 2], "little")
    element = int.from_bytes(data[offset + 2 : offset + 4], "little")
    vr = data[offset + 4 : offset + 6].decode("ascii")
    offset += 6
    if vr in LONG_VRS:
        length = int.from_bytes(data[offset + 2 : offset + 6], "little")
        offset += 6
    else:
        length = int.from_bytes(data[offset : offset + 2], "little")
        offset += 2
    return group, element, vr, offset, length


def _transfer_syntax(data: bytes) -> str:
    if len(data) < 132 or data[128:132] != b"DICM":
        raise ValueError("not dicom")
    offset = 132
    while offset + 8 <= len(data):
        group, element, vr, value_offset, length = _explicit_little(data, offset)
        if group != 0x0002:
            return ""
        if (group, element) == (0x0002, 0x0010) and vr in TEXT_VRS:
            return data[value_offset : value_offset + length].rstrip(b" \0").decode("ascii", errors="ignore")
        offset = value_offset + length
    return ""


def _encoding(group: int, transfer_syntax: str) -> tuple[str, bool]:
    if group == 0x0002:
        return "little", True
    if transfer_syntax == BIG:
        return "big", True
    return "little", transfer_syntax != IMPLICIT


def _elems(data: bytes):
    if len(data) < 132 or data[128:132] != b"DICM":
        raise ValueError("not dicom")
    transfer_syntax = _transfer_syntax(data)
    offset = 132
    while offset + 8 <= len(data):
        little_group = int.from_bytes(data[offset : offset + 2], "little")
        byteorder, explicit = _encoding(little_group, transfer_syntax)
        group = int.from_bytes(data[offset : offset + 2], byteorder)
        byteorder, explicit = _encoding(group, transfer_syntax)
        element = int.from_bytes(data[offset + 2 : offset + 4], byteorder)
        offset += 4
        if explicit:
            vr = data[offset : offset + 2].decode("ascii")
            offset += 2
            if vr in LONG_VRS:
                length = int.from_bytes(data[offset + 2 : offset + 6], byteorder)
                offset += 6
            else:
                length = int.from_bytes(data[offset : offset + 2], byteorder)
                offset += 2
        else:
            vr = KNOWN_VRS.get((group, element), "UN")
            length = int.from_bytes(data[offset : offset + 4], byteorder)
            offset += 4
        value_offset = offset
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
            if vr in TEXT_VRS:
                text_seen += 1
                if RAW in value.decode("utf-8", errors="ignore"):
                    violations.append("text VR persisted raw policy literal")
        if text_seen < 1:
            violations.append("no text VR inspected")
    except Exception as exc:
        violations.append(f"DICOM structural read failed:{type(exc).__name__}")
    return {"passed": not violations, "violations": violations, "evidence": {"output_present": output.is_file(), "receipt_present": receipt_path.is_file()}}
