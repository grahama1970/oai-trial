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

Subject-level coverage (SPIA arXiv:2604.21211): span-absence alone is a weak
unit of protection. This verifier additionally recomputes the expected
pseudonym per canonical identity and requires every selected source occurrence
to appear as its replacement in output, and requires distinct same-type
identities to hold distinct replacements.
"""
from __future__ import annotations

from pathlib import Path

from .errors import AnonError, AnonErrorCode
from .policy import Policy, replace_text
from .pseudonyms import build_replacements


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

    # Value-level skeleton for text files: independently recompute the expected
    # output from source+policy and compare. Catches swapped/wrong pseudonyms
    # and partial replacement that presence/count checks miss. (Text only;
    # other formats keep structural + count checks.)
    for rel in sorted(output_files):
        if rel.suffix == ".txt":
            src_text = (source_corpus / rel).read_text(encoding="utf-8")
            out_text = (staged_corpus / rel).read_text(encoding="utf-8")
            if replace_text(src_text, policy)[0] != out_text:
                raise AnonError(
                    AnonErrorCode.VERIFICATION_FAILED, f"text value skeleton mismatch in {rel.name}"
                )

    source_texts = _searchable(source_corpus, source_files)
    output_texts = _searchable(staged_corpus, output_files)
    for protected in policy.protected_values:
        if _count(protected, source_texts, True) != _count(protected, output_texts, True):
            raise AnonError(
                AnonErrorCode.VERIFICATION_FAILED, "a protected value occurrence count changed"
            )

    _verify_subject_level(policy, source_texts, output_texts)


def _verify_subject_level(policy: Policy, source_texts: list[str], output_texts: list[str]) -> None:
    """Subject-level coverage + same-type distinctness (independent recompute)."""
    replacements = build_replacements([rule.identity for rule in policy.rules], policy.version)

    # Distinctness: no two identities of the same data type share a replacement.
    by_type: dict[str, set[str]] = {}
    for (data_type, _identity), replacement in replacements.items():
        seen = by_type.setdefault(data_type, set())
        if replacement in seen:
            raise AnonError(
                AnonErrorCode.VERIFICATION_FAILED, "two identities share a type replacement"
            )
        seen.add(replacement)

    # Coverage (presence-based, nesting-safe): any identity whose alias appears in
    # the source must have its pseudonym present in output. Exact removal is
    # already proven by the literal-absence scan above; counting per-rule would
    # double-count nested aliases ("Ada" inside "Ada Lovelace").
    present: set[tuple[str, str]] = set()
    for rule in policy.rules:
        if _count(rule.value, source_texts, rule.case_sensitive) > 0:
            present.add(rule.identity)
    for identity in present:
        if _count(replacements[identity], output_texts, True) < 1:
            raise AnonError(
                AnonErrorCode.VERIFICATION_FAILED, "a subject's pseudonym is missing from output"
            )
