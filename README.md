# Smart Housing Agent

Smart Housing Agent has two goals: build a useful rental-housing finder and
learn how to integrate AI into software thoughtfully. The project should make
the model's contribution, benefits, costs, failures, and limits visible. It
should use an LLM only where language understanding adds value; Python handles
clear rules and repeatable decisions.

## Intended base workflow

1. The user describes housing needs in ordinary language.
2. An LLM proposes structured preferences, a summary of its understanding, and
   questions about missing or ambiguous details.
3. Python validates the proposal. It reports unsupported or invalid details
   instead of silently discarding them.
4. The user reviews the summary, answers questions, and confirms or corrects
   the proposed preferences.
5. The app searches permitted housing sources and parses their listings into a
   shared model.
6. Python applies explicit hard requirements. A hybrid matching layer can use
   the LLM to assess soft, semantic preferences from listing evidence, then
   Python combines the results using an explainable scoring policy.
7. Results, evidence, and user feedback are saved in local SQLite and can be
   exported to CSV.

Unknown listing facts remain unknown. An LLM must not invent listing facts,
waive hard requirements, or replace deterministic checks. Show why each
listing matched, including evidence source and uncertainty.

## Data and storage direction

Python uses nested objects while a search is running. SQLite is the durable
source of truth for current confirmed profiles as well as their revisions,
search runs, listing results, feedback, and history. On startup, the app loads
records into Python objects and saves changes back to SQLite.

Preserve these as separate linked data: the original user wording, the model's
summary and proposed structure, user clarifications or corrections, and the
confirmed preferences used for a search. YAML is optional for import/export or
as a starter template; it is not the live source of truth. The existing YAML
loader and sample file are legacy parts to review during the persistence work.

## Learning and efficiency

Start with a small deterministic baseline, then add LLM behavior so the same
examples can be compared. Record API-reported input/output tokens, cached
tokens when available, latency, errors, and cache hits. Measure Python process
memory and local database growth where relevant. A hosted model's internal GPU
memory is generally not exposed by its API.

Application-level caching of confirmed input interpretations is a planned
optimization. It is distinct from provider context caching. Start with exact
repeat lookup, include model/prompt/schema versions, keep cached results
reviewable, and define privacy and deletion behavior. Do not add an LLM call
where deterministic code is sufficient.

## Later monitoring layer

Continuous monitoring is a future layer, added after the base search works for
one permitted source. It should use the confirmed preferences and
user-approved feedback on chosen listings, detect new or changed listings, and
send a link when a relevant update is found. Listing choices may suggest changes
to soft preferences, but must not silently change hard requirements.

Monitoring while the user's computer is off requires a hosted worker and
persistent hosted storage; that introduces separate deployment, privacy, and
cost decisions. Google is the preferred ecosystem to investigate. A Google AI
Plus consumer subscription does not by itself confirm Gemini API billing,
quotas, or Google Cloud hosting access. Verify each developer service and its
costs when that integration becomes a task. Gmail inbox-change notifications
and outbound email notifications are separate integrations.

## Current implementation

The project is an early skeleton. `models.py` contains listing, preference,
draft, assessment, and model-usage dataclasses. `settings.py` loads and
validates the current YAML preferences. The app coordinator, Gemini service,
connectors, scoring, geocoding, SQLite storage, and CSV export are still
placeholders; there is no end-to-end search yet. See
[`docs/design.md`](docs/design.md) for the proposed data relationships and
incremental plan.

## Development approach

Work one task and one file at a time. Before adding functional code, present the
proposed code in chat, explain its logic, and let the user review it. Then add
only the reviewed change to the project.
