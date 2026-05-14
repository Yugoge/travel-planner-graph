"""Canonical constants for the M2 v2 trip contract."""

SCHEMA_VERSION = "v2.0"

STAGES: list[str] = [
    "draft-options",
    "user-review",
    "user-selected",
    "timeline",
    "transportation",
    "finalized",
]

STAGE_INDEX = {stage: i for i, stage in enumerate(STAGES)}

DAY_TYPES: list[str] = [
    "normal",
    "arrival",
    "departure",
    "city-change",
    "red-eye",
    "transit-only",
    "buffer",
]

NAMED_SLOTS: list[str] = [
    "breakfast",
    "morning_activity",
    "lunch",
    "afternoon_activity",
    "dinner",
    "evening_activity",
]

ACCOMMODATION_SLOT = "accommodation"

# Q3b arrival-time skip thresholds (HH:MM local).
SKIP_THRESHOLDS = {
    "lunch_skip_at_or_after": "13:30",
    "afternoon_skip_at_or_after": "16:00",
    "dinner_late_placeholder_at_or_after": "21:00",
}

VALID_SKIP_REASONS = {
    "pre-arrival",
    "post-departure",
    "in-transit",
    "city-change",
    "red-eye-spans-prior-day",
    "user-omit",
    "buffer-rest",
}

CITY_ROLES = {"origin", "destination", "en_route", "overnight"}

LEGACY_SHAPE_KEYS = {"primary", "alternatives"}
