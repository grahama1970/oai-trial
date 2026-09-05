# Historical matcher/discovery proposal — superseded

**Not an implementation inventory.** FlashText, classifier flags, protected-first
precedence and full Unicode case folding below were proposals, not shipped
behavior. The exact engine uses local `_Aho`, rejects protected overlap, and folds
ASCII only. The implemented RapidFuzz workflow is review-only whole-value alias
discovery followed by explicit policy approval: see `../DISCOVERY.md`.

## No regex for matching/classification
best-practices-python `correctness-regex-only-known-grammar`: regex is brittle
against real data and slow at scale. The starter uses it at
`src/anonymization_trial/policy.py:92`
(`re.compile(re.escape(value), re.IGNORECASE)`) for case-insensitive replace —
**to be removed** in the hardened matcher. Regex stays allowed only for a
documented, anchored, fixture-covered grammar (none needed here).

## Runtime matcher: Flashtext (exact, longest-match, single-pass)
- **Flashtext `KeywordProcessor`** (Aho-Corasick trie): O(text), deterministic,
  pure-Python, self-contained. Replaces known policy literals in one
  left-to-right pass, longest-match wins, and — critically — **does not re-scan
  emitted replacement text**, so there is no replacement-to-source cascade.
- **Overlap precedence** (Presidio `_remove_conflicts` logic, reimplemented over
  policy literals): protected spans first (protected > sensitive), then longer
  span, then stable order. Case-insensitive rules use `str.casefold()`, not
  locale `.lower()`.
- Deterministic + self-contained → satisfies the container contract.

## Gated discovery: RapidFuzz (name aliases only)
- **RapidFuzz** (edit distance) for the optional discovery boundary: typo/spelling
  variants of a **known** seeded identity value. High threshold, ties = refuse,
  **never applied to identifiers** — per `extract-entities`
  `entity_match_policy.py` (a fuzzy identifier match is a confident substitution
  of a *different* real entity). Additive to policy literals, never a general
  fuzzy sweep.

## Optional classifier discovery (opt-in, extra credit)
Determinism is the constraint, not "no ML." A classifier is allowed and
self-contained when run deterministically.
- **Flag:** `--discovery none|classifier` (default `none`). Env: `ANON_DISCOVERY`.
  Default off = literal-only deterministic baseline the trial scores.
- **When on:** a bundled PII NER/classifier (candidate:
  `gravitee-io/bert-small-pii-detection`, sourced via `$ops-huggingface`) or
  spaCy proposes candidate sensitive spans in text fields, additive to policy.
- **Determinism config:** pinned model revision + recorded model hash in
  `report.json`, argmax (no sampling), fixed threshold with margin, CPU,
  `torch.use_deterministic_algorithms(True)`, single thread. (Cross-hardware
  bit-exactness isn't guaranteed; label decisions are stable at a fixed
  threshold — documented honestly.)
- **Fail-closed:** a discovered candidate not in policy is replaced *and* flagged
  for review, or quarantined — never silently dropped; protected values still
  win. Feeds the Tier-2/Tier-3 cascade (`11_verification-cascade.md`).

## Packaging impact (pyproject)
- Base runtime deps gain `flashtext` + `rapidfuzz` when the matcher module lands
  (add on import, per `conventions-pyproject-deps-complete`). Both are small,
  self-contained, deterministic.
- Classifier extras (`spacy`/`transformers`/`torch`, a bundled model) go in a
  separate `[project.optional-dependencies] discovery` group + a separate image
  build target, so the default image stays small and only the opt-in
  extra-credit build pulls them.

## Net
Runtime = Flashtext literal replacement with deterministic overlap precedence
(no regex). Discovery = RapidFuzz name aliases + optional deterministic
classifier, both behind an off-by-default flag, fail-closed, for extra credit.
