"""
Shared meal type utilities — single source of truth for extracting meal types.

All scripts that need to know which keys in a day_entry are meal slots
should import from here instead of hardcoding ["breakfast", "lunch", "dinner"].
"""

import json
from pathlib import Path

# Keys that are structural (non-meal) in a day_entry
_NON_MEAL_KEYS = frozenset({"day", "date", "location", "notes"})

# Default fallback when schema is unavailable and data is empty
_DEFAULT_MEAL_TYPES = ["breakfast", "lunch", "dinner"]

# Default fallback times for standard and unknown meal types
DEFAULT_MEAL_TIMES = {
    "breakfast": {"start": "08:00", "end": "09:00"},
    "lunch": {"start": "12:00", "end": "13:30"},
    "dinner": {"start": "18:30", "end": "20:00"},
    "brunch": {"start": "10:30", "end": "12:00"},
    "afternoon_tea": {"start": "15:00", "end": "16:00"},
    "mid_morning_cafe": {"start": "10:00", "end": "10:30"},
    "late_night_snack": {"start": "21:30", "end": "22:30"},
    "supper": {"start": "20:30", "end": "21:30"},
}
_FALLBACK_TIME = {"start": "12:00", "end": "13:00"}

# Emoji map for meal types (with fallback)
MEAL_EMOJI = {
    "breakfast": "🌅",
    "lunch": "☀️",
    "dinner": "🌙",
    "brunch": "🍳",
    "afternoon_tea": "🍵",
    "mid_morning_cafe": "☕",
    "late_night_snack": "🌃",
    "supper": "🍽️",
}
_FALLBACK_EMOJI = "🍴"


def get_meal_types(day_data: dict) -> list:
    """Dynamically extract meal type keys from a day object.

    Excludes non-meal keys (day, date, location, notes) and returns
    only keys whose values are dicts (i.e., meal slots).
    """
    return [
        k for k, v in day_data.items()
        if k not in _NON_MEAL_KEYS and isinstance(v, dict)
    ]


def get_meal_types_from_schema(schema_path: Path = None) -> list:
    """Read meal types from the meals schema's day_entry definition.

    With additionalProperties-based schema, falls back to _DEFAULT_MEAL_TYPES
    since the schema no longer enumerates specific meal keys.
    """
    if schema_path is None:
        schema_path = Path(__file__).resolve().parent.parent.parent / "schemas" / "meals.schema.json"
    if not schema_path.exists():
        return list(_DEFAULT_MEAL_TYPES)
    try:
        schema = json.loads(schema_path.read_text())
        day_props = schema.get("$defs", {}).get("day_entry", {}).get("properties", {})
        # Extract keys that reference meal_slot (for backward compat with old schema)
        meal_keys = [k for k, v in day_props.items() if v.get("$ref") == "#/$defs/meal_slot"]
        if meal_keys:
            return meal_keys
    except (json.JSONDecodeError, OSError):
        pass
    return list(_DEFAULT_MEAL_TYPES)


def get_default_time(meal_type: str) -> dict:
    """Get default time for a meal type, with fallback for unknown types."""
    return DEFAULT_MEAL_TIMES.get(meal_type, _FALLBACK_TIME)


def get_meal_emoji(meal_type: str) -> str:
    """Get emoji for a meal type, with fallback for unknown types."""
    return MEAL_EMOJI.get(meal_type, _FALLBACK_EMOJI)


def format_meal_type_label(meal_type: str) -> str:
    """Convert meal type key to a human-readable label.

    Examples:
        "breakfast" -> "Breakfast"
        "mid_morning_cafe" -> "Mid Morning Cafe"
        "afternoon_tea" -> "Afternoon Tea"
        "late_night_snack" -> "Late Night Snack"
    """
    return meal_type.replace("_", " ").title()
