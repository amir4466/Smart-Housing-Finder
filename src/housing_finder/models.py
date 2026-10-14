"""Shared data classes used by the housing finder.

These objects keep the user's request, an LLM proposal, confirmed criteria,
and listing-match evidence distinct from one another.
"""

from dataclasses import dataclass, field
from typing import Dict, Literal, Optional


PreferenceTarget = str | int | float | bool


@dataclass
class TravelNeed:
    """A requested travel-time check to a destination or place type."""

    destination: str
    mode: Optional[str] = None
    max_minutes: Optional[float] = None


@dataclass
class PreferenceCriterion:
    """A soft preference used to rank listings that meet hard requirements."""

    name: str
    target: PreferenceTarget
    weight: float


@dataclass
class HomeListing:
    """Facts collected about one housing listing.

    Fields that a source does not provide should be left as ``None`` rather
    than guessed.
    """

    # Identity
    source: str
    url: str
    source_listing_id: Optional[str] = None
    title: Optional[str] = None

    # Home details
    monthly_rent_eur: Optional[float] = None
    extra_monthly_costs_eur: Optional[float] = None
    size_m2: Optional[float] = None
    bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    furnished_status: Optional[str] = None

    # Place
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Original listing text
    description: Optional[str] = None


@dataclass
class MatchResult:
    """The result of comparing a listing with the current search preferences."""

    listing: HomeListing
    fit_score: float
    tier: str
    reasons: list[str] = field(default_factory=list)
    assessments: list["CriterionAssessment"] = field(default_factory=list)

    # Optional details added by a map service, when available
    commute_minutes: Optional[float] = None
    grocery_distance_m: Optional[float] = None
    nearest_transit_distance_m: Optional[float] = None


@dataclass
class SearchPreferences:
    """Validated criteria used to search for and compare listings.

    The original fields remain available for the current YAML loader. New
    structured fields can be adopted as that loader and YAML schema evolve.
    """

    city: str
    max_monthly_rent_eur: Optional[float]
    min_size_m2: Optional[float]
    work_location: Optional[str]
    commute_mode: str
    max_commute_minutes: Optional[float]
    priorities: Dict[str, float] = field(default_factory=dict)
    household_size: Optional[int] = None
    property_type: Optional[str] = None
    rooms_total: Optional[int] = None
    bedrooms: Optional[int] = None
    min_bathrooms: Optional[int] = None
    living_room: Optional[bool] = None
    backyard: Optional[bool] = None
    travel_needs: list[TravelNeed] = field(default_factory=list)
    preference_criteria: list[PreferenceCriterion] = field(default_factory=list)


@dataclass
class PreferenceDraft:
    """An LLM's proposed interpretation, awaiting Python checks and user review."""

    original_input: str
    model_summary: str
    proposed_preferences: SearchPreferences
    questions: list[str] = field(default_factory=list)
    unsupported_details: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class CriterionAssessment:
    """Evidence and uncertainty for one listing against one criterion."""

    criterion: str
    match: Literal["match", "partial", "no_match", "unknown"]
    source: Literal["listing_field", "listing_text", "routing_data", "llm"]
    evidence: Optional[str] = None
    confidence: Optional[float] = None
    uncertainty: Optional[str] = None


@dataclass
class LLMCallMetrics:
    """Non-sensitive measurements for one model API call."""

    provider: str
    model: str
    operation: str
    duration_ms: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached_input_tokens: Optional[int] = None
    succeeded: bool = False
    error_category: Optional[str] = None
