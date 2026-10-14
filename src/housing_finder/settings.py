"""Load and validate search preferences from the YAML configuration file."""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .models import SearchPreferences


DEFAULT_PREFERENCES_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "search_preferences.yaml"
)


def _get_section(data: dict, name: str) -> dict:
    """Return a named YAML section, or raise a readable error."""
    section = data.get(name, {})

    if not isinstance(section, dict):
        raise ValueError(f"The '{name}' section must contain key-value fields.")

    return section


def _optional_number(value: Any, name: str) -> Optional[float]:
    """Convert a YAML number to float, allowing a blank value."""
    if value is None:
        return None

    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"'{name}' must be a number or left blank.")

    return float(value)


def load_preferences(
    path: str | Path = DEFAULT_PREFERENCES_PATH,
) -> SearchPreferences:
    """Read and validate the user's search preferences."""
    preferences_path = Path(path)

    try:
        data = yaml.safe_load(preferences_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(
            f"Could not read preferences file: {preferences_path}"
        ) from error
    except yaml.YAMLError as error:
        raise ValueError(
            f"Preferences file is not valid YAML: {preferences_path}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError("The preferences file must contain key-value fields.")

    city = data.get("city")
    if not isinstance(city, str) or not city.strip():
        raise ValueError("'city' must contain a city name.")

    must_meet = _get_section(data, "must_meet")
    work = _get_section(data, "work")
    priorities = _get_section(data, "priorities")

    max_rent = _optional_number(
        must_meet.get("max_monthly_rent_eur"),
        "max_monthly_rent_eur",
    )
    min_size = _optional_number(
        must_meet.get("min_size_m2"),
        "min_size_m2",
    )
    max_commute = _optional_number(
        work.get("max_commute_minutes"),
        "max_commute_minutes",
    )

    if max_rent is not None and max_rent < 0:
        raise ValueError("'max_monthly_rent_eur' cannot be negative.")

    if min_size is not None and min_size <= 0:
        raise ValueError("'min_size_m2' must be greater than zero.")

    if max_commute is not None and max_commute <= 0:
        raise ValueError("'max_commute_minutes' must be greater than zero.")

    work_location = work.get("location")
    if work_location is not None:
        if not isinstance(work_location, str):
            raise ValueError("'work.location' must be text or left blank.")
        work_location = work_location.strip() or None

    commute_mode = work.get("commute_mode", "public_transport")
    if not isinstance(commute_mode, str) or not commute_mode.strip():
        raise ValueError("'work.commute_mode' must contain a travel mode.")

    priority_values: Dict[str, float] = {}
    for name in ("commute", "public_transport", "groceries"):
        weight = _optional_number(priorities.get(name, 0), f"priorities.{name}")
        if weight is None or weight < 0:
            raise ValueError(f"'priorities.{name}' must be zero or greater.")
        priority_values[name] = weight

    if priority_values["commute"] > 0 and not work_location:
        raise ValueError(
            "Add 'work.location' because commute has a priority above zero."
        )

    return SearchPreferences(
        city=city.strip(),
        max_monthly_rent_eur=max_rent,
        min_size_m2=min_size,
        work_location=work_location,
        commute_mode=commute_mode.strip(),
        max_commute_minutes=max_commute,
        priorities=priority_values,
    )
