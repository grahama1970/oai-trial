from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .formats import SUPPORTED_SUFFIXES, iter_searchable_text, transform_file
from .policy import Policy, load_policy


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


def _verify(corpus: Path, policy: Policy) -> None:
    for path in sorted(item for item in corpus.rglob("*") if item.is_file()):
        for text in iter_searchable_text(path):
            for rule in policy.rules:
                haystack = text if rule.case_sensitive else text.casefold()
                needle = rule.value if rule.case_sensitive else rule.value.casefold()
                if needle in haystack:
                    raise PipelineError(f"verification failed in {path.name}")


def run_pipeline(input_root: Path, output_root: Path) -> RunReport:
    started = time.perf_counter()
    corpus = input_root / "corpus"
    if not corpus.is_dir():
        raise PipelineError("input bundle must contain corpus/")
    policy = load_policy(input_root / "policy.json")

    output_corpus = output_root / "corpus"
    if output_root.exists():
        for child in output_root.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        output_root.mkdir(parents=True)
    output_corpus.mkdir(parents=True)

    files = sorted(path for path in corpus.rglob("*") if path.is_file())
    unsupported = [path for path in files if path.suffix.lower() not in SUPPORTED_SUFFIXES]
    if unsupported:
        raise PipelineError(f"unsupported input type: {unsupported[0].suffix}")

    records = 0
    replacements = 0
    bytes_read = 0
    for source in files:
        relative = source.relative_to(corpus)
        destination = output_corpus / relative
        file_records, file_replacements = transform_file(source, destination, policy)
        records += file_records
        replacements += file_replacements
        bytes_read += source.stat().st_size

    _verify(output_corpus, policy)
    bytes_written = sum(path.stat().st_size for path in output_corpus.rglob("*") if path.is_file())
    report = RunReport(
        status="success",
        files_processed=len(files),
        records_processed=records,
        bytes_read=bytes_read,
        bytes_written=bytes_written,
        replacements_applied=replacements,
        verification_passed=True,
        elapsed_seconds=round(time.perf_counter() - started, 6),
    )
    (output_root / "report.json").write_text(
        json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
