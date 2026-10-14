# Smart Housing Agent: current design direction

This document records the current intended design and separates it from what is
already implemented. It is a learning project as well as a housing finder: we
want to understand how AI helps, where it fails, what it costs, and how it
compares with ordinary code. Prefer small, measurable integrations over
unnecessary model calls or infrastructure.

## Product goals

- Help a user compare rental homes against their needs and see an understandable
  ranked list.
- Teach AI integration through visible, incremental experiments.
- Begin with a manually run local base application. Add continuous monitoring
  only after the base flow works.

## Base workflow

1. Capture the user's ordinary-language request.
2. Ask an LLM to propose structured preferences, summarize its understanding,
   and list ambiguity or missing details.
3. Validate the response in Python. Do not silently discard unsupported,
   invalid, or ambiguous information.
4. Let the user review and correct the interpretation, answer questions, and
   confirm the proposed profile.
5. Fetch listings through permitted, website-specific connectors and parse
   available facts into a shared listing representation.
6. Apply explicit hard requirements deterministically. For soft preferences,
   compare structured listing fields first; use an LLM only where semantic
   interpretation of listing text adds value.
7. Combine criteria in Python using an explainable scoring policy. Preserve
   per-criterion evidence, source, and uncertainty.
8. Save profile revisions, searches, results, and feedback in local SQLite.
   Export results to CSV when useful.

The LLM can help interpret language; it does not own validation, hard filtering,
scoring, persistence, or export. Listing facts absent from source data stay
unknown. Model-extracted details must remain attributed to their text evidence,
not presented as independently verified facts.

## Data relationships

Use nested Python objects for live execution and relational SQLite records for
durable data. These are two representations of the same concepts; the app maps
between them when loading and saving. SQLite is not only an archive: it holds
the current confirmed profile and current operational state as well as
historical revisions and search results.

Conceptual flow:

```text
User text
  -> PreferenceDraft
       -> proposed SearchPreferences
            -> TravelNeed list
            -> PreferenceCriterion list
  -> Python validation and user confirmation
       -> confirmed SearchPreferences
  -> matcher compares preferences with each HomeListing
       -> MatchResult per listing
            -> CriterionAssessment list
  -> persistence links the profile revision, search run, listing results,
     assessments, feedback, and relevant model-call metrics
```

Keep the following information distinct and linked:

- Original user wording.
- Model summary and proposed structured interpretation.
- Clarifications and corrections from the user.
- The confirmed preference revision used for a search.
- Each search run and the listings observed in that run.
- Per-criterion match results and evidence.
- User actions such as save, dismiss, or contact.
- Model-call measurements that do not duplicate raw prompts.

The current `PreferenceCriterion` has a display `name` but no stable key. Before
implementing assessment persistence, add a stable criterion key and have
`CriterionAssessment` refer to it. The `HomeListing` model also needs structured
facts for criteria such as total rooms, bathrooms, living room, and backyard, or
an explicit evidence-based way to assess them from listing text.

## Proposed SQLite records

Exact table names and columns are still to be reviewed before code is written.
The initial schema should represent these concepts:

- **Profile:** stable identity/name for a reusable search profile.
- **Preference revision:** original wording, model summary/proposal,
  clarifications, confirmed preference snapshot, model/prompt/schema versions,
  and timestamps. A changed profile creates a new revision.
- **Search run:** one execution linked to the exact preference revision used.
- **Listing:** source identity and stable listing identity where available.
- **Search result / listing observation:** what the source reported in that run,
  along with the result for that run. Keep observations so changed price or
  availability can be detected later.
- **Criterion assessment:** one criterion's match level, source, evidence, and
  uncertainty for a listing result; link by stable criterion key.
- **User feedback:** actions on a listing, linked to the relevant profile/run.
- **LLM call metrics:** provider/model/operation, elapsed time, token counts,
  cached token counts when available, outcome, and error category. Avoid storing
  secrets or raw prompt text in this metrics record.
- **Input cache (later):** separate cache records with versioned identity and
  retention/deletion policy. A cache entry is never the confirmed profile.

These concepts need not all be implemented in the first database slice. Start
with the smallest schema that can preserve a preference revision, one search
run, listing observations/results, and assessments. Add feedback and cache when
their behavior is ready to implement.

## Matching and ranking

Use a hybrid matcher, and make the source of each judgment visible.

1. Python applies explicit hard requirements. If a required fact is missing,
   report it as unknown and apply a documented policy such as “needs review” or
   “cannot confirm”; never silently treat unknown as a pass.
2. Compare normalized listing fields with confirmed preferences.
3. Where useful, ask an LLM to assess one soft criterion from provided listing
   text. Require an evidence excerpt or explanation tied to that text, a bounded
   match result, and uncertainty. Do not ask it to invent rooms, rent, address,
   travel times, or other absent facts.
4. Let Python combine eligible signals with agreed weights and missing-data
   rules. Keep hard-filter outcomes separate from ranking scores.
5. Show per-criterion reasons, data source, and uncertainty to the user.

An LLM is not a general-purpose exception handler. Ambiguous user intent needs
clarification; insufficient listing evidence stays unknown. The weight scale,
score formula, confidence handling, and treatment of missing soft criteria are
open design decisions.

## Learning and efficiency plan

Build a small deterministic baseline, then compare it with LLM-assisted
behavior on the same examples. Keep calls narrow and avoid using a model where
ordinary code can give the needed result.

Record what the provider exposes: input/output tokens, cached-token usage,
latency, failures, and retries. Measure local Python process memory and SQLite
size for relevant runs. A hosted model API generally does not expose its
internal GPU memory use or full internal reasoning state; distinguish those
unavailable measurements from app-side measurements.

The model-usage object is instrumentation data, not memory for the model. The
local database stores confirmed user/profile history. Provider context caching
is a separate API feature from the app's own exact-repeat input cache.

## Input caching (planned)

Cache confirmed input interpretations only when reuse is likely to avoid a
repeat model call. Start with exact-repeat lookup; similar/paraphrase matching
can be evaluated later because a near match can change meaning.

- Include model, prompt, and schema versions in cache identity.
- Revalidate cached structures and show them for review; a cache hit never
  confirms or changes preferences on the user's behalf.
- Decide whether to retain raw text, how long to retain it, and how to clear it.
  Housing needs may include identifying work or home addresses.
- Compare hit rate, token savings, latency, and incorrect-reuse risk. Provider
  context caching is useful for substantial repeated context, while a local
  exact-match cache is likely the first experiment for short preference input.

## Google ecosystem and later monitoring

Google is the preferred ecosystem to investigate, not yet a locked-in API or
hosting design. Google AI Plus is a consumer subscription; it does not by itself
confirm Gemini Developer API billing, quotas, or Google Cloud runtime access.
Verify each service, model capability, setup requirement, and cost when that
integration becomes a task. Gemini Live is for real-time interactive streaming
and is not required for ordinary text preference parsing or scheduled checks.

Continuous listing monitoring is a later layer. It should run only after the
base search works end to end for one permitted source. It should use the
confirmed preference revision and approved user feedback, detect new or
materially changed listings, deduplicate alerts, and send a source link. Listing
choices may suggest soft-preference changes for approval; never silently change
hard requirements.

If monitoring must continue while the user's computer is off, it needs a hosted
worker and persistent hosted storage. That is a separate cost, privacy, and
operations decision. Local manual refresh is the fallback if hosting is not
available or wanted. Website alerts or Gmail can be candidate inputs, but
receiving inbox change notifications and sending outbound email are different
integrations. Site terms, documented APIs, robots/access rules, login needs, and
page changes must be checked for every connector.

## Failure and fallback behavior

- **No API key, quota, or service outage:** preserve confirmed preferences;
  offer a retry or structured/manual entry path.
- **Malformed or unsupported model response:** show the validation issue and
  allow correction; do not persist the invalid proposal.
- **Ambiguous input:** ask a focused question. If skipped, leave the value
  unknown and skip dependent checks.
- **Insufficient listing evidence:** mark that criterion unknown and expose it
  for review.
- **Source unavailable or access disallowed:** preserve existing results and
  explain that the source was skipped or monitoring paused.
- **Duplicate or repeated update:** deduplicate by source identity and listing
  state before notifying.

Never put passwords, API keys, cookies, or session tokens in source, YAML,
prompts stored as examples, or listing exports. Use appropriate local secret
storage or environment configuration.

## Current implementation status

The repository is an early skeleton. `models.py` now contains dataclasses for
listings, preferences, drafts, criterion assessments, and model-call metrics.
`settings.py` still loads and validates the existing YAML preference format.
The app coordinator, Gemini service, connectors, scoring, geocoding, SQLite
storage, and CSV export are placeholders. No end-to-end search, database
persistence, input cache, or monitoring is implemented.

The existing `config/search_preferences.yaml` is a sample/legacy profile. Its
values, including Enschede and the commute settings, are not confirmed as final
user requirements. Keep it readable until a migration/import role is agreed.

## Step-by-step development process

1. Review the Python data model and agree on stable preference/criterion keys.
2. Agree on the SQLite concepts and relationships before writing persistence
   code.
3. Present each functional file's proposed code in chat, explain the flow and
   logic, and let the user review it before adding that one file to the project.
4. Map dataclasses to SQLite records and implement the preference draft,
   validation, confirmation, and persistence flow.
5. Add a stub model response, then integrate Gemini and inspect usage and
   failure behavior.
6. Compare deterministic matching with LLM-assisted soft matching.
7. Complete one permitted source vertical slice, then add CSV export.
8. Evaluate continuous monitoring and hosting as a separate later task.

Do not rebuild working files wholesale or add an agent framework, frontend,
hosted database, or background monitoring before a concrete learning or product
need is agreed.
