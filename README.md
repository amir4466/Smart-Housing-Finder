# Smart Housing Agent

Smart Housing Agent is a small local tool for comparing rental homes across
housing websites. The user starts each search manually. The tool is not intended
to monitor websites continuously.

## Intended user flow

1. The user describes their housing needs in ordinary language.
2. An LLM (planned: Gemini) proposes structured preferences and a plain-language
   summary of what it understood. It also identifies questions and ambiguities.
3. Python validates the proposed fields. It does not silently discard details it
   cannot represent: unsupported or ambiguous information is shown for review.
4. The user confirms or corrects the summary and answers important questions.
5. The app saves the confirmed preferences to `config/search_preferences.yaml`.
6. Website-specific connectors fetch and parse listings from permitted sources.
7. A matching layer evaluates each listing. Python applies clear hard
   requirements and compares structured fields. The LLM may assess soft,
   semantic preferences from listing text when useful, with evidence and
   uncertainty kept visible. Python combines the signals using an explicit,
   explainable scoring policy. Unknown listing facts remain unknown and do not
   silently pass a hard requirement that depends on them.
8. Python stores results locally in SQLite and exports CSV.

The LLM assists with language understanding and evidence-bound interpretation
of listing text. Python owns schema validation, hard filtering, score
combination, persistence, and export. The model must not invent listing facts,
waive hard requirements, or replace deterministic checks. The result should
show why each listing matched, including which details came from structured
source fields and which were model interpreted.

## Fallback behavior

- If the LLM is unavailable or its response is invalid, do not change the saved
  preferences. Let the user retry, answer structured prompts, or edit YAML.
- If a preference is ambiguous, retain it as unresolved and ask the user. Do not
  guess, silently omit it, or apply it as a filter before clarification.
- If the user skips a question, save only confirmed fields and leave the rest
  unset. Skip checks that require missing information.
- Keep the previous confirmed YAML intact until the user approves a replacement.

## Input caching

Caching confirmed natural-language inputs and their structured interpretations
is a planned optimization to reduce repeated LLM token usage. It is not
implemented yet. Cache behavior must account for paraphrases, stale schemas or
prompts, and personal information such as work addresses. Cached interpretations
must still be reviewable; users need a way to clear cached data. See
[`docs/design.md`](docs/design.md) for the proposed cache boundary.

## Current implementation

The current code is an early skeleton. `models.py` defines basic listing,
preference, and match dataclasses. `settings.py` loads and validates a YAML
preferences file. The app coordinator, Gemini integration, connectors, scoring,
geocoding, SQLite storage, and CSV export modules are placeholders and are not
implemented yet. The target flow above describes intended behavior, not a
working end-to-end feature.

See [`docs/design.md`](docs/design.md) for the proposed preference lifecycle,
hybrid matching and ranking approach, data boundaries, and incremental
implementation plan. Scoring weights, confidence thresholds, and the treatment
of missing data still need agreement before implementation.
