# Historical reuse audit — pre-existing projects, skills, and OSS repos

**Historical design record, not the current contract.** The shipped exact matcher
is the local `_Aho` implementation; no comparative FlashText benchmark established
that choice as superior. The notes below about protected-first precedence and
HMAC-style local replacement were superseded by overlap rejection and a public
SHA-256 namespace. Current opt-in RapidFuzz behavior is in `../DISCOVERY.md`.

Goal: borrow proven ideas, bespoke as little new code as possible.

## Pre-existing skills (agent-skills)
| Skill | Relevant capability | Decision |
|---|---|---|
| `extract-entities` | Flashtext (Aho-Corasick trie) + RapidFuzz, O(text) longest-match, `entity_match_policy.py` fragment/boundary rules | **Borrow the idea** (single-pass longest-match), not the code — it's tuned for fuzzy *identifier rejection*, not literal replacement. Flashtext not installed; stdlib matcher is enough at trial policy size. Flashtext = documented scale upgrade. |
| `clean-text` | Unicode normalization, homoglyph/mixed-script detection, encoding fixes (`clean_text.py`) | **Reference for encoding policy** (BOM, homoglyph evasion) in file 03. Do not import; our contract is UTF-8 literal. |
| `cui-marker` | CUI detection/marking (32 CFR 2002) | Not needed — we get sensitive values from `policy.json`, not detection. |
| `best-practices-security`, `best-practices-python` | Trust-boundary + repo Python conventions | **Apply as review gates.** |

No existing project has a reusable multi-format anonymization engine (grep of
373 projects found only log-redaction in tau, nothing to import).

## OSS repos cloned to /tmp/oai-refs (ideas to borrow)
| Repo | Idea borrowed | Notes |
|---|---|---|
| **microsoft/presidio** | **Overlap/conflict resolution algorithm** — `anonymizer_engine._remove_conflicts_and_get_text_manipulation_data` + `RecognizerResult.intersects/contains/__gt__` + `ConflictResolutionStrategy.REMOVE_INTERSECTIONS` | This is the canonical solution to our overlap-precedence requirement: sort by start; when spans intersect, the higher-score/longer span wins and the loser's start is pushed to the winner's end (no cascade). We reimplement this logic in stdlib over policy literals (protected = highest priority). MIT license. |
| **AnonShield/anonshield** | **Deterministic HMAC pseudonym operator** — `CustomSlugAnonymizer.operate` returns `[ENTITY_TYPE_hash]` from `HMAC(secret, clean_text)`; schema-aware per-field force/skip/auto for CSV/XLSX/JSON/XML | Confirms our `HMAC(key, subject:type)` design and the `[REDACTED-…]`/typed-slug shape. Closest analog to the trial. |
| **mysto/python-fpe** | **FF3-1 format-preserving encryption** (NIST SP 800-38G) | Optional upgrade for phone/email/id so pseudonyms keep the original *format* (a phone stays a valid-looking phone). Adds a `pycryptodome` dep — only if we want format preservation; document as tradeoff, not default. |
| **subhash-holla/pii-anon** | Deterministic pseudonymization **scope** + re-identification audit trail concept | Informs the "identity coherence across contexts" and key-management notes for SUBMISSION production design. |
| **elastic/anonymize-it** | Config-driven pipeline (source → mappings → destination) | Confirms the policy-as-config boundary; nothing to import. |

## Key algorithm notes (captured verbatim intent)
- **Presidio precedence (reimplement in stdlib):** build candidate spans for every
  policy literal + protected value over the text; sort by start; resolve
  intersections by priority = (protected > sensitive, then longer span, then
  stable order); emit replacements left-to-right; **never re-scan emitted text** →
  no replacement-to-source cascade.
- **AnonShield determinism:** `display_hash, full_hash = HMAC(secret, clean_text)`;
  same input → same slug; typed prefix keeps entity types distinct.

## Net build decision
Write a small stdlib matcher that encodes Presidio's precedence rules over the
policy literals, keep the starter's stateless HMAC-style `replacement_for`
(validated by AnonShield), and reserve FF3 (python-fpe) as an optional
format-preserving mode. No heavyweight dependency (spaCy/presidio) needed —
the trial supplies the sensitive values, so we skip all the NLP detection those
frameworks carry.
