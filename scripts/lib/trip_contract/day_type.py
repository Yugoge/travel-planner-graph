"""§5.13 B day-type tolerance + Q3b arrival-time skip thresholds.

Computes which slots a day is EXPECTED to skip given its day_type and
arrival_ts/departure_ts. Validators (validators.py) compare actual to expected
and emit MISSING_REQUIRED_SKIP / UNJUSTIFIED_SKIP errors. We never auto-mutate.
"""

from __future__ import annotations

import re
from typing import Optional

from .constants import (
    ACCOMMODATION_SLOT,
    NAMED_SLOTS,
    SKIP_THRESHOLDS,
)
from .errors import TripContractError


_HHMM_RE = re.compile(r"^(\d{2}):(\d{2})$")


def _hhmm_to_minutes(hhmm: str) -> int:
    m = _HHMM_RE.match(hhmm)
    if not m:
        raise TripContractError(f"not HH:MM: {hhmm!r}")
    return int(m.group(1)) * 60 + int(m.group(2))


def _ts_to_hhmm(ts: Optional[str]) -> Optional[str]:
    """Best-effort extraction of HH:MM from an ISO timestamp."""
    if ts is None:
        return None
    m = re.search(r"T(\d{2}):(\d{2})", ts)
    if not m:
        return None
    return f"{m.group(1)}:{m.group(2)}"


def _expect_arrival_skips(arr_min: int, expected: dict[str, Optional[str]]) -> None:
    """Mutate `expected` for an arrival-style day given local arrival minute-of-day."""
    lunch_threshold = _hhmm_to_minutes(SKIP_THRESHOLDS["lunch_skip_at_or_after"])
    afternoon_threshold = _hhmm_to_minutes(SKIP_THRESHOLDS["afternoon_skip_at_or_after"])
    expected["breakfast"] = "pre-arrival"
    expected["morning_activity"] = "pre-arrival"
    if arr_min >= lunch_threshold:
        expected["lunch"] = "pre-arrival"
    if arr_min >= afternoon_threshold:
        expected["afternoon_activity"] = "pre-arrival"


def _expect_departure_skips(dep_min: int, expected: dict[str, Optional[str]]) -> None:
    """Mutate `expected` for a departure-style day given local departure minute-of-day."""
    if dep_min < _hhmm_to_minutes("19:00"):
        expected["evening_activity"] = "post-departure"
    if dep_min < _hhmm_to_minutes("17:00"):
        expected["dinner"] = "post-departure"


def expected_skips_for_day(day_dict: dict) -> dict[str, Optional[str]]:
    """Compute expected skipped_reason per named slot from day_type + arrival/departure.

    Per Q3b: lunch >=13:30, afternoon >=16:00 are SKIPS; dinner >=21:00 is a
    late_arrival_placeholder (NOT skipped) per codex Q3 correction. The validator
    handles late_arrival_placeholder separately.
    """
    expected: dict[str, Optional[str]] = {s: None for s in NAMED_SLOTS}
    day_type = day_dict.get("day_type", "normal")

    if day_type in {"arrival", "city-change"}:
        arr_hhmm = _ts_to_hhmm(day_dict.get("arrival_ts"))
        if arr_hhmm is not None:
            _expect_arrival_skips(_hhmm_to_minutes(arr_hhmm), expected)

    if day_type in {"departure", "city-change"}:
        dep_hhmm = _ts_to_hhmm(day_dict.get("departure_ts"))
        if dep_hhmm is not None:
            _expect_departure_skips(_hhmm_to_minutes(dep_hhmm), expected)

    if day_type == "transit-only":
        for s in NAMED_SLOTS:
            expected[s] = "in-transit"

    return expected


def is_slot_skipped(day_dict: dict, slot_id: str) -> bool:
    """True if the given slot on this day is currently marked skipped."""
    if slot_id == ACCOMMODATION_SLOT:
        slot = day_dict.get(ACCOMMODATION_SLOT, {})
    else:
        slot = day_dict.get("slots", {}).get(slot_id, {})
    return bool(slot.get("skipped", False))


def get_day_type(day_dict: dict) -> str:
    return day_dict.get("day_type", "normal")
