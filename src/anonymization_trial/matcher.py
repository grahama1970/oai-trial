"""Exact multi-pattern literal matcher with deterministic overlap resolution.

Inputs: compiled patterns (literal, replacement, case-sensitivity) built from a
policy; text to scan.
Outputs: ``replace(text) -> (new_text, count)`` performs a single left-to-right
pass replacing selected non-overlapping spans and never rescanning emitted
replacements; ``find(text) -> list[Span]`` reports selected spans for
verification/detection.
Failure modes: none at runtime; construction is pure. Correctness relies on the
policy layer having rejected protected/sensitive overlaps and non-ASCII
case-insensitive literals first.

Algorithm: two Aho-Corasick automata (case-sensitive over original text,
case-insensitive over an ASCII-lowered, length-preserving view). Candidate spans
from both are merged, then selected leftmost-longest with a stable rule_id
tie-break, giving deterministic, cascade-free replacement.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

# ASCII A-Z -> a-z only; length-preserving so match offsets map 1:1 to original.
_ASCII_LOWER = {c: c + 32 for c in range(ord("A"), ord("Z") + 1)}


def ascii_lower(text: str) -> str:
    """Lowercase only ASCII A-Z; leave all other code points unchanged."""
    return text.translate(_ASCII_LOWER)


@dataclass(frozen=True, slots=True)
class Span:
    start: int
    end: int
    replacement: str
    rule_id: str


@dataclass(frozen=True, slots=True)
class _Pattern:
    literal: str
    replacement: str
    rule_id: str


class _Aho:
    """Minimal Aho-Corasick automaton over exact character sequences."""

    def __init__(self, patterns: list[_Pattern]) -> None:
        self._goto: list[dict[str, int]] = [{}]
        self._fail: list[int] = [0]
        # node -> list of (pattern_length, replacement, rule_id)
        self._out: list[list[tuple[int, str, str]]] = [[]]
        for pat in patterns:
            self._add(pat)
        self._build()

    def _add(self, pat: _Pattern) -> None:
        node = 0
        for ch in pat.literal:
            nxt = self._goto[node].get(ch)
            if nxt is None:
                nxt = len(self._goto)
                self._goto.append({})
                self._fail.append(0)
                self._out.append([])
                self._goto[node][ch] = nxt
            node = nxt
        self._out[node].append((len(pat.literal), pat.replacement, pat.rule_id))

    def _build(self) -> None:
        queue: deque[int] = deque()
        for nxt in self._goto[0].values():
            self._fail[nxt] = 0
            queue.append(nxt)
        while queue:
            node = queue.popleft()
            for ch, nxt in self._goto[node].items():
                queue.append(nxt)
                fail = self._fail[node]
                while fail and ch not in self._goto[fail]:
                    fail = self._fail[fail]
                self._fail[nxt] = self._goto[fail].get(ch, 0) if fail or ch in self._goto[0] else 0
                self._out[nxt] = self._out[nxt] + self._out[self._fail[nxt]]

    def scan(self, text: str) -> list[tuple[int, int, str, str]]:
        """Return (start, end, replacement, rule_id) for every occurrence."""
        spans: list[tuple[int, int, str, str]] = []
        node = 0
        for i, ch in enumerate(text):
            while node and ch not in self._goto[node]:
                node = self._fail[node]
            node = self._goto[node].get(ch, 0)
            for length, replacement, rule_id in self._out[node]:
                start = i - length + 1
                spans.append((start, i + 1, replacement, rule_id))
        return spans


class Matcher:
    """Compiled matcher: case-sensitive + case-insensitive exact literals."""

    def __init__(
        self,
        sensitive_cs: list[_Pattern],
        sensitive_ci: list[_Pattern],
    ) -> None:
        self._cs = _Aho(sensitive_cs) if sensitive_cs else None
        self._ci = _Aho(sensitive_ci) if sensitive_ci else None

    def find(self, text: str) -> list[Span]:
        raw: list[tuple[int, int, str, str]] = []
        if self._cs is not None:
            raw.extend(self._cs.scan(text))
        if self._ci is not None:
            raw.extend(self._ci.scan(ascii_lower(text)))
        return _select(raw)

    def replace(self, text: str) -> tuple[str, int]:
        spans = self.find(text)
        if not spans:
            return text, 0
        out: list[str] = []
        cursor = 0
        for span in spans:
            out.append(text[cursor:span.start])
            out.append(span.replacement)
            cursor = span.end
        out.append(text[cursor:])
        return "".join(out), len(spans)


def _select(raw: list[tuple[int, int, str, str]]) -> list[Span]:
    """Leftmost-longest, stable rule_id tie-break, non-overlapping."""
    # Sort: earliest start, then longest span, then stable rule_id.
    ordered = sorted(raw, key=lambda s: (s[0], -(s[1] - s[0]), s[3]))
    selected: list[Span] = []
    cursor = 0
    for start, end, replacement, rule_id in ordered:
        if start < cursor:
            continue  # overlaps an already-selected span
        selected.append(Span(start, end, replacement, rule_id))
        cursor = end
    return selected


def build_matcher(
    rules_cs: list[tuple[str, str, str]],
    rules_ci: list[tuple[str, str, str]],
) -> Matcher:
    """Build from (literal, replacement, rule_id) triples.

    ``rules_ci`` literals must already be ASCII (enforced by the policy layer);
    they are ASCII-lowered here to match the lowered text view.
    """
    cs = [_Pattern(lit, rep, rid) for lit, rep, rid in rules_cs]
    ci = [_Pattern(ascii_lower(lit), rep, rid) for lit, rep, rid in rules_ci]
    return Matcher(cs, ci)
