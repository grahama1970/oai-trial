"""Pipeline orchestration: preflight, stage, verify, atomically publish, report.

Inputs: an input bundle root containing ``policy.json`` and ``corpus/``, and an
output root.
Outputs: an anonymized ``corpus/`` mirroring input paths plus a sanitized
``report.json`` written LAST as the sole readiness marker; returns a
``RunReport``.
Failure modes: raises ``AnonError``/``PipelineError`` (fail closed) on unsafe
input, unsupported type, a sensitive literal in a path, verification failure, or
publication failure. On any failure the staging tree is removed and no
``report.json`` is written, so ``/trial/output`` holds no ready release.

State machine: preflight -> inventoried -> staged -> verified ->
corpus_published -> ready. Only a valid report.json means ready. A previously
valid release is never mutated until publication succeeds.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat as statmod
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .errors import AnonError, AnonErrorCode
from .formats import SUPPORTED_SUFFIXES, transform_file
from .policy import Policy, load_policy
from .pseudonyms import ALGORITHM_VERSION, KEY_MODE, SCOPE_ID
from .verification import verify_corpus

# Explicit non-claims in the readiness report. A literal-policy pipeline proves
# declared-literal replacement + structural preservation, not re-identification
# resistance (RAT-Bench arXiv:2602.12806; SPIA arXiv:2604.21211; "Why Data
# Anonymization Has Not Taken Off" arXiv:2509.10165).
_DOES_NOT_ESTABLISH = (
    "discovery_of_unlisted_sensitive_data",
    "resistance_to_all_external_linkage",
    "quasi_identifier_anonymity",
    "formal_anonymity_or_differential_privacy",
)


class PipelineError(RuntimeError):
    pass


@dataclass
class RunReport:
    status: str
    files_processed: int
    records_processed: int
    bytes_read: int
    bytes_written: int
    replacements_applied: int
    verification_passed: bool
    elapsed_seconds: float
    policy_sha256: str = ""
    corpus_manifest_sha256: str = ""
    algorithm_version: str = ALGORITHM_VERSION
    scope_id: str = SCOPE_ID
    key_mode: str = KEY_MODE
    does_not_establish: tuple[str, ...] = _DOES_NOT_ESTABLISH


def _reject(code: AnonErrorCode, message: str) -> None:
    raise AnonError(code, message)


def _preflight(input_root: Path, output_root: Path, policy: Policy) -> list[tuple[Path, Path]]:
    """Validate trust boundaries and return sorted (source, relative) files."""
    in_r = input_root.resolve()
    out_r = output_root.resolve()
    if in_r == out_r or in_r.is_relative_to(out_r) or out_r.is_relative_to(in_r):
        _reject(
            AnonErrorCode.UNSAFE_INPUT,
            "input and output roots must be distinct and non-nested",
        )

    corpus = input_root / "corpus"
    if corpus.is_symlink() or not corpus.is_dir():
        _reject(AnonErrorCode.UNSAFE_INPUT, "input bundle must contain a regular corpus/ directory")
    policy_file = input_root / "policy.json"
    if policy_file.is_symlink() or not policy_file.is_file():
        _reject(AnonErrorCode.UNSAFE_INPUT, "input bundle must contain a regular policy.json")

    files: list[tuple[Path, Path]] = []
    for entry in sorted(corpus.rglob("*")):
        mode = os.lstat(entry).st_mode
        if statmod.S_ISLNK(mode):
            _reject(AnonErrorCode.UNSAFE_INPUT, "symlinks are not allowed in the corpus")
        if statmod.S_ISDIR(mode):
            continue
        if not statmod.S_ISREG(mode):
            _reject(AnonErrorCode.UNSAFE_INPUT, "only regular files are allowed in the corpus")
        relative = entry.relative_to(corpus)
        if entry.suffix.lower() not in SUPPORTED_SUFFIXES:
            _reject(AnonErrorCode.UNSUPPORTED_FORMAT, f"unsupported input type: {entry.suffix}")
        if policy.matcher.find(relative.as_posix()):
            _reject(
                AnonErrorCode.SENSITIVE_IN_SCHEMA,
                "a sensitive literal occurs in a corpus path",
            )
        files.append((entry, relative))
    return files


def _manifest_digest(corpus: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in corpus.rglob("*") if p.is_file()):
        digest.update(path.relative_to(corpus).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _publish(staging: Path, output_root: Path, report: RunReport) -> None:
    """Atomically promote the staged corpus and write report.json last."""
    output_corpus = output_root / "corpus"
    for child in output_root.iterdir():
        if child == staging:
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    os.replace(staging / "corpus", output_corpus)  # same-filesystem atomic rename
    (output_root / "report.json").write_text(
        json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_pipeline(input_root: Path, output_root: Path) -> RunReport:
    started = time.perf_counter()
    policy = load_policy(input_root / "policy.json")
    files = _preflight(input_root, output_root, policy)

    output_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=output_root, prefix=".staging-"))
    try:
        staged_corpus = staging / "corpus"
        staged_corpus.mkdir()
        records = replacements = bytes_read = 0
        for source, relative in files:
            file_records, file_replacements = transform_file(
                source, staged_corpus / relative, policy
            )
            records += file_records
            replacements += file_replacements
            bytes_read += source.stat().st_size

        verify_corpus(input_root / "corpus", staged_corpus, policy)
        bytes_written = sum(p.stat().st_size for p in staged_corpus.rglob("*") if p.is_file())
        report = RunReport(
            status="ready",
            files_processed=len(files),
            records_processed=records,
            bytes_read=bytes_read,
            bytes_written=bytes_written,
            replacements_applied=replacements,
            verification_passed=True,
            elapsed_seconds=round(time.perf_counter() - started, 6),
            policy_sha256=hashlib.sha256((input_root / "policy.json").read_bytes()).hexdigest(),
            corpus_manifest_sha256=_manifest_digest(staged_corpus),
        )
        _publish(staging, output_root, report)
        return report
    finally:
        shutil.rmtree(staging, ignore_errors=True)
