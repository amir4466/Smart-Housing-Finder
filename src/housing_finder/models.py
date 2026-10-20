"""Data classes for housing preferences, listings, and match evidence."""

from dataclasses import dataclass, field
from typing import Dict, Literal, Optional


PreferenceTarget = str | int | float | bool
CriterionType = Literal["hard", "soft"]
MatchStatus = Literal["match", "partial", "no_match", "unknown"]
AssessmentSource = Literal[
    "listing_field",
    "listing_text",
    "routing_data",
    "llm",
]
HardFilterStatus = Literal["eligible", "excluded", "needs_review"]


@dataclass
class TravelNeed:
    """A travel check associated with one preference criterion."""

    criterion_key: str
    destination: str
    mode: Optional[str] = None
    max_minutes: Optional[float] = None


@dataclass
class PreferenceCriterion:
    """One hard requirement or weighted soft preference."""

    criterion_key: str
    display_name: str
    criterion_type: CriterionType
    target: PreferenceTarget
    weight: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.criterion_key.strip():
            raise ValueError("A criterion needs a stable key.")

        if not self.display_name.strip():
            raise ValueError("A criterion needs a display name.")

        if self.criterion_type == "hard" and self.weight is not None:
            raise ValueError("Hard requirements must not have a weight.")

        if self.criterion_type == "soft":
            if self.weight is None or self.weight < 0:
                raise ValueError(
                    "Soft preferences need a non-negative weight."
                )


@dataclass
class HomeListing:
    """Facts collected about one housing listing.

    Fields not provided by a source stay as None; they are not guessed.
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
    rooms_total: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = None
    furnished_status: Optional[str] = None
    living_room: Optional[bool] = None
    backyard: Optional[bool] = None

    # Place
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Original listing text
    description: Optional[str] = None


@dataclass
class CriterionAssessment:
    """Evidence and uncertainty for one listing against one criterion."""

    criterion_key: str
    match: MatchStatus
    source: AssessmentSource
    evidence: Optional[str] = None
    confidence: Optional[float] = None
    uncertainty: Optional[str] = None


@dataclass
class MatchResult:
    """The result of checking and ranking one listing."""

    listing: HomeListing
    hard_filter_status: HardFilterStatus
    fit_score: Optional[float] = None
    tier: Optional[str] = None
    reasons: list[str] = field(default_factory=list)
    assessments: list[CriterionAssessment] = field(default_factory=list)

    # Optional details from a map or routing service
    commute_minutes: Optional[float] = None
    grocery_distance_m: Optional[float] = None
    nearest_transit_distance_m: Optional[float] = None


@dataclass
class SearchPreferences:
    """Validated preferences used for a housing search."""

    # Existing YAML fields retained while the input flow is updated
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

    def __post_init__(self) -> None:
        criterion_keys = {
            criterion.criterion_key
            for criterion in self.preference_criteria
        }

        if len(criterion_keys) != len(self.preference_criteria):
            raise ValueError("Preference criterion keys must be unique.")

        for travel_need in self.travel_needs:
            if travel_need.criterion_key not in criterion_keys:
                raise ValueError(
                    f"Travel need '{travel_need.criterion_key}' must refer "
                    "to a preference criterion with the same key."
                )


@dataclass
class PreferenceDraft:
    """An LLM interpretation awaiting Python validation and user review."""

    original_input: str
    model_summary: str
    proposed_preferences: SearchPreferences
    questions: list[str] = field(default_factory=list)
    unsupported_details: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)


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