""" Create and connect to the local Smart Housing Agent  DB """

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = ( 
    Path(__file__).resolve().parents[3]
    / "data"
    / "smart_housing_agent.sqlite3"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    profile_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS preference_revisions (
    revision_id INTEGER PRIMARY KEY,
    profile_id INTEGER NOT NULL,
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    original_input TEXT NOT NULL,
    model_summary TEXT,
    clarifications TEXT NOT NULL DEFAULT '',
    schema_version TEXT NOT NULL,
    confirmed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id)
        ON DELETE CASCADE,
    UNIQUE (profile_id, revision_number)
);

CREATE TABLE IF NOT EXISTS preference_criteria (
    criterion_id INTEGER PRIMARY KEY,
    revision_id INTEGER NOT NULL,
    criterion_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    criterion_type TEXT NOT NULL
        CHECK (criterion_type IN ('hard', 'soft')),
    target_type TEXT NOT NULL
        CHECK (target_type IN ('text', 'integer', 'number', 'boolean')),
    target_text TEXT,
    target_integer INTEGER,
    target_number REAL,
    target_boolean INTEGER CHECK (
        target_boolean IS NULL OR target_boolean IN (0, 1)
    ),
    weight REAL CHECK (weight IS NULL OR weight >= 0),
    FOREIGN KEY (revision_id) REFERENCES preference_revisions(revision_id)
        ON DELETE CASCADE,
    UNIQUE (revision_id, criterion_key),
    CHECK (
        (criterion_type = 'hard' AND weight IS NULL)
        OR
        (criterion_type = 'soft' AND weight IS NOT NULL)
    ),
    CHECK (
        (target_type = 'text'
            AND target_text IS NOT NULL
            AND target_integer IS NULL
            AND target_number IS NULL
            AND target_boolean IS NULL)
        OR
        (target_type = 'integer'
            AND target_text IS NULL
            AND target_integer IS NOT NULL
            AND target_number IS NULL
            AND target_boolean IS NULL)
        OR
        (target_type = 'number'
            AND target_text IS NULL
            AND target_integer IS NULL
            AND target_number IS NOT NULL
            AND target_boolean IS NULL)
        OR
        (target_type = 'boolean'
            AND target_text IS NULL
            AND target_integer IS NULL
            AND target_number IS NULL
            AND target_boolean IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS travel_needs (
    criterion_id INTEGER PRIMARY KEY,
    destination TEXT NOT NULL,
    mode TEXT,
    max_minutes REAL CHECK (max_minutes IS NULL OR max_minutes > 0),
    FOREIGN KEY (criterion_id) REFERENCES preference_criteria(criterion_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_runs (
    search_run_id INTEGER PRIMARY KEY,
    revision_id INTEGER NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('running', 'completed', 'failed')),
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY (revision_id) REFERENCES preference_revisions(revision_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS listings (
    listing_id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    source_listing_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source, source_listing_id)
);

CREATE TABLE IF NOT EXISTS listing_observations (
    observation_id INTEGER PRIMARY KEY,
    search_run_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    url TEXT NOT NULL,
    title TEXT,
    monthly_rent_eur REAL,
    extra_monthly_costs_eur REAL,
    size_m2 REAL,
    rooms_total INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,
    property_type TEXT,
    furnished_status TEXT,
    city TEXT,
    neighborhood TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    living_room INTEGER CHECK (
        living_room IS NULL OR living_room IN (0, 1)
    ),
    backyard INTEGER CHECK (
        backyard IS NULL OR backyard IN (0, 1)
    ),
    description TEXT,
    FOREIGN KEY (search_run_id) REFERENCES search_runs(search_run_id)
        ON DELETE CASCADE,
    FOREIGN KEY (listing_id) REFERENCES listings(listing_id)
        ON DELETE CASCADE,
    UNIQUE (search_run_id, listing_id)
);

CREATE TABLE IF NOT EXISTS match_results (
    match_result_id INTEGER PRIMARY KEY,
    observation_id INTEGER NOT NULL UNIQUE,
    hard_filter_status TEXT NOT NULL
        CHECK (hard_filter_status IN ('eligible', 'excluded', 'needs_review')),
    fit_score REAL,
    tier TEXT,
    FOREIGN KEY (observation_id) REFERENCES listing_observations(observation_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS criterion_assessments (
    assessment_id INTEGER PRIMARY KEY,
    match_result_id INTEGER NOT NULL,
    criterion_id INTEGER NOT NULL,
    match_status TEXT NOT NULL
        CHECK (match_status IN ('match', 'partial', 'no_match', 'unknown')),
    assessment_source TEXT NOT NULL
        CHECK (assessment_source IN (
            'listing_field', 'listing_text', 'routing_data', 'llm'
        )),
    evidence TEXT,
    confidence REAL CHECK (
        confidence IS NULL OR (confidence >= 0 AND confidence <= 1)
    ),
    uncertainty TEXT,
    FOREIGN KEY (match_result_id) REFERENCES match_results(match_result_id)
        ON DELETE CASCADE,
    FOREIGN KEY (criterion_id) REFERENCES preference_criteria(criterion_id)
        ON DELETE CASCADE,
    UNIQUE (match_result_id, criterion_id)
);

CREATE TABLE IF NOT EXISTS user_feedback (
    feedback_id INTEGER PRIMARY KEY,
    match_result_id INTEGER NOT NULL,
    action TEXT NOT NULL
        CHECK (action IN ('saved', 'dismissed', 'contacted', 'viewed')),
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_result_id) REFERENCES match_results(match_result_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_call_metrics (
    call_id INTEGER PRIMARY KEY,
    revision_id INTEGER,
    search_run_id INTEGER,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    operation TEXT NOT NULL,
    duration_ms REAL,
    input_tokens INTEGER CHECK (
        input_tokens IS NULL OR input_tokens >= 0
    ),
    output_tokens INTEGER CHECK (
        output_tokens IS NULL OR output_tokens >= 0
    ),
    cached_input_tokens INTEGER CHECK (
        cached_input_tokens IS NULL OR cached_input_tokens >= 0
    ),
    succeeded INTEGER NOT NULL CHECK (succeeded IN (0, 1)),
    error_category TEXT,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (revision_id) REFERENCES preference_revisions(revision_id)
        ON DELETE SET NULL,
    FOREIGN KEY (search_run_id) REFERENCES search_runs(search_run_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_revisions_profile
    ON preference_revisions(profile_id, revision_number);

CREATE INDEX IF NOT EXISTS idx_search_runs_revision
    ON search_runs(revision_id, started_at);

CREATE INDEX IF NOT EXISTS idx_observations_listing
    ON listing_observations(listing_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_assessments_result
    ON criterion_assessments(match_result_id);

CREATE INDEX IF NOT EXISTS idx_llm_metrics_run
    ON llm_call_metrics(search_run_id);
"""


def connect_database(
    path: str | Path = DEFAULT_DB_PATH,
) -> sqlite3.Connection:
    """Open the DB and enable row access by column name and foreign key constraints."""
    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection

def initialize_database(
    path: str | Path = DEFAULT_DB_PATH,
) -> None:
    """Create the DB schema if it doesn't exist."""
    connection = connect_database(path)
    try: 
        connection.executescript(SCHEMA)
        connection.commit()
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        connection.close()