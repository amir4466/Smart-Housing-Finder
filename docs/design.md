# Preference input and interpretation design

This document records the agreed direction for the early-stage Smart Housing
Agent. It describes intended behavior; the Gemini input flow and cache are not
implemented yet.

## Preference lifecycle

Keep the user's request, the model's proposal, and the saved search preferences
as distinct concepts:

1. **User input:** preserve the original text while processing a request so the
   user can compare it with the interpretation. Treat it as potentially
   sensitive, especially if it includes an address.
2. **LLM proposal:** ask the model for structured fields, a concise confirmation
   summary, unresolved questions, and any unsupported details. Require a defined
   schema rather than accepting arbitrary generated YAML.
3. **Python validation:** validate types, allowed values, numeric ranges, and
   relationships between fields. Return actionable errors and unresolved items;
   do not silently drop input that the schema cannot represent.
4. **User confirmation:** display the interpretation and ask the user to confirm
   or correct it. Ask focused questions for ambiguity (for example, whether
   “three rooms” means three rooms total or three bedrooms).
5. **Persistence:** only after confirmation, serialize the validated structure
   to YAML. Write a temporary draft and replace the saved file only after the
   write succeeds, preserving the previous confirmed file on failure.

If the user skips an unresolved item, keep it unset and do not use it for a
filter or score. The app may proceed using other confirmed preferences when
that is meaningful, while making clear which requested checks could not run.

## Proposed preference shape

The eventual schema should make these distinctions explicit:

- `schema_version` so saved files can be migrated deliberately.
- `location` for a confirmed city or search area.
- `household_size` and `property_type` when specified.
- `hard_requirements` for explicit deal-breakers, such as maximum rent or
  minimum bedrooms.
- `preferences` for weighted criteria such as a preferred living room or
  proximity to shops.
- Separate `rooms_total` and `bedrooms` fields; never map ambiguous “rooms” to
  either without clarification.
- Structured travel needs with destination, mode, and maximum time. A travel
  time criterion requires a usable destination, a listing location, a travel
  mode, and a routing source.
- `unresolved` or `questions` in an in-memory draft. Do not treat these as
  active search criteria. Confirmed YAML should contain only understood values
  plus any intentionally retained notes needed to explain what remains unset.

This is a design target, not a migration instruction. Keep the current YAML
readable until a schema migration is implemented and the user has reviewed the
meaning of existing values. In particular, the current sample commute mode is
free text and contains multiple modes; it should not be automatically converted
to a single mode.

## LLM and deterministic boundaries

The LLM may:

- Convert ordinary language into a proposed preference structure.
- Summarize its interpretation for user confirmation.
- Identify missing or ambiguous details.
- Extract candidate facts from listing descriptions that are not consistently
  represented by the source, such as whether a living room is mentioned. Keep
  the source text or excerpt as evidence and mark the extraction as model
  interpreted, not a verified source field.
- Estimate semantic fit for a confirmed soft preference when simple fields
  cannot express it (for example, whether a description suggests a bright or
  quiet home). Return a bounded structured assessment, evidence, and uncertainty
  rather than an ungrounded overall recommendation.

Python must:

- Validate the model response against the current schema.
- Require user review before saving a proposed profile.
- Apply explicit filters and explainable scoring.
- Enforce clear hard requirements (such as maximum rent) with deterministic
  rules. An LLM must not waive or reinterpret these requirements.
- Combine eligible deterministic and model-assisted soft-preference signals
  using an explicit scoring policy, and retain per-criterion reasons so the
  user can see why an option ranked well.
- Keep facts absent from a listing unknown; never let the LLM fill them in as
  verified facts. Model-extracted candidate details remain attributed to the
  description and may be marked unknown or uncertain.
- Own database writes and CSV export.

## Matching and ranking layer

Matching should be hybrid. A language model can be more useful than a fixed
rule for interpreting flexible descriptions and criteria with varied wording,
but it can also misread text or overstate what a listing says. It should add
evidence-bound signals for soft preferences, not replace the deterministic
checks that are clear and testable.

For each listing, the matcher should:

1. Apply explicit hard requirements in Python. If a required fact is missing,
   represent the result as unknown and ask the chosen policy whether that means
   “needs review” or “cannot confirm”; do not silently treat missing as a pass.
2. Compare available normalized listing fields against confirmed preferences.
3. Where useful, ask the LLM to assess a specific soft criterion from the
   listing text provided to it. Require a response tied to evidence from that
   text, with a match level and uncertainty. Do not ask it to invent distances,
   travel times, room counts, or other facts absent from the source.
4. Have Python combine scores according to explicit weights and missing-data
   rules. Keep hard-filter outcomes separate from ranking scores.
5. Show the user the per-criterion result, its source (structured listing field
   or model interpretation), and any uncertainty.

The LLM may help with exceptions that are genuinely semantic, but it must not
be an open-ended exception handler for unclear rules. If the preference itself
is ambiguous, ask the user. If the listing evidence is insufficient, leave that
criterion unknown and let the documented missing-data policy handle it. Score
weights, confidence thresholds, and how unknown soft criteria affect ranking
remain product decisions to agree before implementation.

## LLM failure paths

- Missing credentials, network/API failure, or unavailable model: preserve the
  current confirmed preferences and offer retry, structured CLI questions, or
  direct YAML editing.
- Malformed response or schema mismatch: do not save it; report the issue and
  offer a retry or manual correction.
- Ambiguity: ask the user rather than guessing. If skipped, leave the value
  unset and skip dependent checks.
- User correction: update the proposal, validate again, and request confirmation
  of the corrected summary before saving.

The API key belongs in a local secret store or environment configuration, never
in YAML preferences, source code, or listing exports.

## Input cache requirement (planned)

Cache user input and its structured interpretation where doing so avoids a
repeat model call. This is a future requirement, not part of the first LLM
integration.

Design constraints for that cache:

- Only reuse a result that the user confirmed. Do not promote an unconfirmed
  draft into saved preferences through a cache hit.
- Exact-repeat lookup can be introduced first. Similarity matching is a later
  choice and must have a conservative threshold; show cached interpretations
  for review because a near match can change meaning.
- Include schema and prompt/model version in the cache identity so changed
  parsing behavior does not silently reuse stale structures.
- Choose local storage and retention deliberately. Minimize retention of raw
  input, protect potentially identifying details, and provide a way to clear
  the cache.
- A cache hit saves model tokens but does not bypass Python validation or user
  confirmation.

## Incremental implementation plan

1. Agree on the preference schema and resolve product questions (city, hard
   requirements versus preferences, room terminology, and travel needs).
2. Implement the input-to-proposal-to-confirmation flow with a fake/stub model
   response first, so validation and correction behavior can be reviewed without
   API credentials.
3. Add the Gemini API behind a small service interface, with explicit setup and
   failure handling.
4. Save only confirmed, validated preferences to YAML; preserve existing values
   until a deliberate migration is agreed.
5. Implement one permitted listing source and a deterministic filter/score
   vertical slice.
6. Add SQLite and CSV, then add input caching after the interpretation schema
   and confirmation lifecycle have stabilized.

Do not add a multi-agent framework, hosted database, frontend, or background
monitoring without a concrete requirement.
