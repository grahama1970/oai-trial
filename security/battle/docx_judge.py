"""Battle Judge for native DOCX redaction receipts and output structure."""
from __future__ import annotations

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

FORBIDDEN_REL_MARKERS = ("vbaProject", "oleObject", "package", "activeX", "externalLink", "attachedTemplate")
FORBIDDEN_CT_MARKERS = ("vbaProject", "macroEnabled", "oleObject", "activeX", "externalLink")
RAW_TOKENS = ("alice@example.com", "alice@", "example.com")


def _canonical(value: str) -> str:
    return "".join(ch.casefold() for ch in value if ch.isalnum())


def _xml(data: bytes):
    return ET.fromstring(data)


def _zip_text(value: bytes) -> str:
    return value.decode("utf-8", errors="ignore")


def judge(target_dir: str, params: dict) -> dict:
    root = Path(target_dir)
    output = root / "out.docx"
    receipt_path = root / "receipt.json"
    violations: list[str] = []
    stdout_path = root / ".battle-execution" / "stdout.txt"
    stderr_path = root / ".battle-execution" / "stderr.txt"
    stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.is_file() else ""
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.is_file() else ""
    evidence = {"output_present": output.is_file(), "receipt_present": receipt_path.is_file()}
    if not output.is_file() or not receipt_path.is_file():
        rejection_surface = stdout + "\n" + stderr
        violations = []
        if "BATTLE_CONTRACT_REJECT" not in rejection_surface:
            violations.append("docx output and receipt are required")
        if any(token in rejection_surface for token in RAW_TOKENS) or _canonical("alice@example.com") in _canonical(rejection_surface):
            violations.append("rejection surface persisted raw policy literal")
        return {"passed": not violations, "violations": violations, "evidence": evidence}
    try:
        receipt_text = receipt_path.read_text(encoding="utf-8")
        receipt = json.loads(receipt_text)
    except Exception as exc:
        return {"passed": False, "violations": [f"docx receipt unreadable: {type(exc).__name__}"], "evidence": evidence}
    if any(token in receipt_text for token in RAW_TOKENS):
        violations.append("receipt persisted raw policy literal")
    if receipt.get("schema") != "multimodal_redaction.v1" or receipt.get("status") != "ready":
        violations.append("receipt must be a ready multimodal_redaction.v1 release")
    structural = receipt.get("structural_verification")
    if not isinstance(structural, dict):
        violations.append("receipt must include structural verification")
    else:
        for key in (
            "forbidden_structures_absent",
            "policy_literals_absent",
            "zip_metadata_policy_literals_absent",
        ):
            if structural.get(key) is not True:
                violations.append(f"structural verification missing {key}")
        if not isinstance(structural.get("xml_parts_valid"), int) or structural.get("xml_parts_valid", 0) < 3:
            violations.append("XML validity verification must cover package XML parts")
    try:
        with zipfile.ZipFile(output) as archive:
            evidence["member_count"] = len(archive.infolist())
            metadata_text = _zip_text(archive.comment) + "\n" + "\n".join(
                item.filename + "\n" + _zip_text(item.comment) for item in archive.infolist()
            )
            if any(token in metadata_text for token in RAW_TOKENS) or _canonical("alice@example.com") in _canonical(metadata_text):
                violations.append("ZIP metadata persists policy literal")
            for name in archive.namelist():
                data = archive.read(name)
                text = _zip_text(data)
                if any(token in text for token in RAW_TOKENS):
                    violations.append(f"payload persists raw literal:{name}")
                if name.endswith((".xml", ".rels")) or name == "[Content_Types].xml":
                    parsed = _xml(data)
                    decoded = "".join(parsed.itertext())
                    if _canonical("alice@example.com") in _canonical(decoded):
                        violations.append(f"decoded XML text persists policy literal:{name}")
                    for element in parsed.iter():
                        content_type = element.attrib.get("ContentType", "")
                        rel_type = element.attrib.get("Type", "")
                        target_mode = element.attrib.get("TargetMode", "")
                        if any(marker in content_type for marker in FORBIDDEN_CT_MARKERS):
                            violations.append(f"active content type:{name}")
                        if any(marker in rel_type for marker in FORBIDDEN_REL_MARKERS):
                            violations.append(f"active relationship:{name}")
                        if target_mode.casefold() == "external":
                            violations.append(f"external relationship:{name}")
    except Exception as exc:
        violations.append(f"docx structural read failed:{type(exc).__name__}")
    return {"passed": not violations, "violations": violations, "evidence": evidence}
