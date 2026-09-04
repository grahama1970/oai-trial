"""Independent whole-corpus verification, decoupled from the transform path.

Inputs: the original source corpus directory, the staged output corpus
directory, and the compiled ``Policy``.
Outputs: none on success; raises ``AnonError(VERIFICATION_FAILED)`` on any
mismatch. This module rereads both corpora from disk and never calls the
``transform_*`` functions or trusts their success booleans.
Failure modes: file-set divergence, a surviving sensitive literal in an output
value, or a changed protected-value occurrence count.

Independence: the transform uses the Aho-Corasick matcher; this verifier uses a
plain ``str`` scan over freshly read output, so a matcher bug cannot mask itself.
"""
from __future__ import annotations

from pathlib import Path

from .errors import AnonError, AnonErrorCode
from .policy import Policy


def _relative_files(root: Path) -> set[Path]:
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}


def _searchable(root: Path, relatives: set[Path]) -> list[str]:
    from .formats import iter_searchable_text  # local import avoids a cycle

    texts: list[str] = []
    for rel in sorted(relatives):
        texts.extend(iter_searchable_text(root / rel))
    return texts


def _count(needle: str, texts: list[str], case_sensitive: bool) -> int:
    probe = needle if case_sensitive else needle.casefold()
    return sum((text if case_sensitive else text.casefold()).count(probe) for text in texts)


def verify_corpus(source_corpus: Path, staged_corpus: Path, policy: Policy) -> None:
    """Fail closed unless the staged corpus is a safe release of the source."""
    from .formats import iter_searchable_text

    source_files = _relative_files(source_corpus)
    output_files = _relative_files(staged_corpus)
    if source_files != output_files:
        raise AnonError(AnonErrorCode.VERIFICATION_FAILED, "source and output file sets differ")

    for rel in sorted(output_files):
        for text in iter_searchable_text(staged_corpus / rel):
            for rule in policy.rules:
                haystack = text if rule.case_sensitive else text.casefold()
                needle = rule.value if rule.case_sensitive else rule.value.casefold()
                if needle in haystack:
                    raise AnonError(
                        AnonErrorCode.VERIFICATION_FAILED,
                        f"a sensitive literal survived in {rel.name}",
                    )

    source_texts = _searchable(source_corpus, source_files)
    output_texts = _searchable(staged_corpus, output_files)
    for protected in policy.protected_values:
        if _count(protected, source_texts, True) != _count(protected, output_texts, True):
            raise AnonError(
                AnonErrorCode.VERIFICATION_FAILED, "a protected value occurrence count changed"
            )
