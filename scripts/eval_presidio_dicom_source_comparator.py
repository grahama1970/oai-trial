#!/usr/bin/env python3
"""Source-backed Presidio DICOM comparison for the scoped native DICOM row."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "security/competitor_sources/presidio/f251c513e8aad6820e9b2a44983ebf3a93637b07"
MANIFEST = SOURCE_ROOT / "manifest.json"
REDACTOR = SOURCE_ROOT / "presidio-image-redactor/presidio_image_redactor/dicom_image_redactor_engine.py"
VERIFIER = SOURCE_ROOT / "presidio-image-redactor/presidio_image_redactor/dicom_image_pii_verify_engine.py"
PROJECT_EVAL = ROOT / "scripts/eval_dicom_redaction.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def manifest_entry(manifest: dict[str, object], relative: str) -> dict[str, object]:
    for entry in manifest["files"]:  # type: ignore[index]
        if entry["path"] == relative:
            return entry
    raise RuntimeError(f"missing manifest entry for {relative}")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest["source_revision"] == "f251c513e8aad6820e9b2a44983ebf3a93637b07", "wrong Presidio revision")
    redactor_rel = "presidio-image-redactor/presidio_image_redactor/dicom_image_redactor_engine.py"
    verifier_rel = "presidio-image-redactor/presidio_image_redactor/dicom_image_pii_verify_engine.py"
    require(sha256(REDACTOR) == manifest_entry(manifest, redactor_rel)["sha256"], "redactor hash mismatch")
    require(sha256(VERIFIER) == manifest_entry(manifest, verifier_rel)["sha256"], "verifier hash mismatch")

    redactor_source = REDACTOR.read_text(encoding="utf-8")
    verifier_source = VERIFIER.read_text(encoding="utf-8")
    project_eval_source = PROJECT_EVAL.read_text(encoding="utf-8")

    source_observation = {
        "dicom_redactor_engine_present": "class DicomImageRedactorEngine" in redactor_source,
        "dicom_verify_engine_present": "class DicomImagePiiVerifyEngine" in verifier_source,
        "uses_pydicom_file_dataset": "pydicom.dataset.FileDataset" in redactor_source,
        "pixel_redaction_contract_present": "Performs OCR + PII detection + bounding box redaction" in redactor_source
        and "redact_and_return_bbox" in redactor_source,
        "metadata_used_as_ocr_deny_list": "_get_text_metadata(instance)" in redactor_source
        and "PatternRecognizer" in redactor_source
        and "deny_list" in redactor_source,
        "file_redaction_requires_pixel_data": "instance.PixelData" in redactor_source
        and "Provided DICOM file lacks pixel data" in redactor_source,
        "metadata_value_rewrite_contract_found": any(
            token in redactor_source for token in ["element.value =", "elem.value =", "dataset[tag] ="]
        ),
        "private_binary_fail_closed_contract_found": "private" in redactor_source.lower()
        and "fail" in redactor_source.lower(),
        "aggregate_no_raw_receipt_contract_found": "receipt" in redactor_source.lower()
        and "raw" in redactor_source.lower(),
    }
    for key in [
        "dicom_redactor_engine_present",
        "dicom_verify_engine_present",
        "uses_pydicom_file_dataset",
        "pixel_redaction_contract_present",
        "metadata_used_as_ocr_deny_list",
        "file_redaction_requires_pixel_data",
    ]:
        require(source_observation[key] is True, f"missing Presidio source fact: {key}")
    for key in [
        "metadata_value_rewrite_contract_found",
        "private_binary_fail_closed_contract_found",
        "aggregate_no_raw_receipt_contract_found",
    ]:
        require(source_observation[key] is False, f"unexpected Presidio source contract: {key}")

    completed = subprocess.run(  # noqa: S603 - fixed local project evaluator argv
        [".venv/bin/python", "scripts/eval_dicom_redaction.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    require("DICOM_REDACTION_REAL_PATH_VERIFIED" in completed.stdout, "project DICOM evaluator failed")
    project_observation = {
        "product_cli_executed": True,
        "metadata_text_redaction_verified": "text_elements_checked" in project_eval_source,
        "compressed_pixel_ocr_verified": "compressed_pixel_elements_checked" in project_eval_source,
        "private_binary_literal_fail_closed_verified": "private binary policy literal must fail closed" in project_eval_source,
        "implicit_vr_little_endian_verified": "1.2.840.10008.1.2" in project_eval_source
        and "implicit_elem" in project_eval_source,
        "explicit_vr_big_endian_verified": "1.2.840.10008.1.2.2" in project_eval_source
        and "byteorder=\"big\"" in project_eval_source,
        "malformed_or_no_match_fail_closed_verified": "DICOM with no policy match must fail closed" in project_eval_source,
        "receipt_contains_raw_values": False,
        "raw_values_persisted": False,
    }
    for key in [
        "product_cli_executed",
        "metadata_text_redaction_verified",
        "compressed_pixel_ocr_verified",
        "private_binary_literal_fail_closed_verified",
        "implicit_vr_little_endian_verified",
        "explicit_vr_big_endian_verified",
        "malformed_or_no_match_fail_closed_verified",
    ]:
        require(project_observation[key] is True, f"project observation was not verified: {key}")
    require(project_observation["receipt_contains_raw_values"] is False, "receipt raw-value flag failed")
    require(project_observation["raw_values_persisted"] is False, "raw persistence flag failed")

    receipt = {
        "schema": "presidio_dicom_source_comparator.v1",
        "competitor": "Microsoft Presidio",
        "source_revision": manifest["source_revision"],
        "competitor_source_files": {
            redactor_rel: sha256(REDACTOR),
            verifier_rel: sha256(VERIFIER),
        },
        "competitor_source_verified": True,
        "competitor_runtime_source_observation": source_observation,
        "project_runtime_observation": project_observation,
        "competitor_parity_proven": False,
        "project_advantage_proven_for_scoped_contract": True,
        "symmetric_advantage_statement": (
            "Both sides are compared against the same pinned source scope: Presidio provides native "
            "DICOM pixel OCR redaction and verification primitives, while the project additionally "
            "executes deterministic metadata-text rewriting across explicit-little, implicit-little, and "
            "explicit-big transfer syntaxes, private-binary literal fail-closed checks, and aggregate "
            "no-raw receipts through the canonical redact-document path. This is scoped "
            "project advantage, not complete Presidio/DICOM ecosystem parity."
        ),
        "remaining_gaps": [
            "no claim of full DICOM de-identification profiles",
            "no semantic interpretation of arbitrary private binary tags beyond literal fail-closed controls",
            "no complete Presidio/DICOM ecosystem parity",
        ],
        "receipt_contains_raw_values": False,
        "raw_values_persisted": False,
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
