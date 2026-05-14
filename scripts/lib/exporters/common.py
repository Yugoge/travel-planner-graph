"""Shared utilities for M6 exporters.

Trip-loading wraps `trip_contract.load_trip`. Slot iteration unifies the 6
named time-slots + accommodation. Image lookup obeys Q3f (local cache only,
no download). Atomic write uses .tmp + rename. Owning-day logic delegates
to `trip_contract.pick_owning_day` (§5.13 B).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from scripts.lib import trip_contract as tc


EXPORTER_AGENT_IDS = {"pdf-export", "ical-export"}


# Per-slot canonical anchor times (codex confirmed: DTEND non-inclusive, so
# 08:00+1.5h=09:30 is adjacent to morning_activity 09:30, not overlapping).
SLOT_ANCHORS: dict[str, tuple[int, int]] = {
    "breakfast":          (8, 0),
    "morning_activity":   (9, 30),
    "lunch":              (12, 0),
    "afternoon_activity": (14, 0),
    "dinner":             (18, 30),
    "evening_activity":   (20, 0),
}

SLOT_DEFAULT_DURATION_MIN = 90

CITY_TZ_MAP: dict[str, str] = {
    "beijing":   "Asia/Shanghai",
    "shanghai":  "Asia/Shanghai",
    "lijiang":   "Asia/Shanghai",
    "dali":      "Asia/Shanghai",
    "kunming":   "Asia/Shanghai",
    "chengdu":   "Asia/Shanghai",
    "xian":      "Asia/Shanghai",
    "guangzhou": "Asia/Shanghai",
    "shenzhen":  "Asia/Shanghai",
    "hangzhou":  "Asia/Shanghai",
    "suzhou":    "Asia/Shanghai",
    "hongkong":  "Asia/Hong_Kong",
    "macau":     "Asia/Macau",
    "taipei":    "Asia/Taipei",
}

DEFAULT_TZ = "Asia/Shanghai"
DEFAULT_DAY_ANCHOR = (9, 0)


@dataclass
class Trip:
    trip_id: str
    trip_dir: Path
    bundle: tc.TripBundle

    @property
    def meta(self) -> dict:
        return self.bundle.meta

    @property
    def days(self) -> list[dict]:
        return self.bundle.days

    @property
    def transportation(self) -> dict:
        return self.bundle.transportation

    @property
    def route_cache(self) -> dict:
        return self.bundle.route_cache


def _resolve_trip_dir(trip_arg: str) -> tuple[Path, str]:
    candidate = Path(trip_arg)
    if candidate.is_absolute() and candidate.exists():
        return candidate, candidate.name
    rel = Path("data") / trip_arg
    if rel.exists():
        return rel, trip_arg
    if candidate.exists():
        return candidate, candidate.name
    raise FileNotFoundError(
        f"trip directory not found for '{trip_arg}' "
        f"(checked: {rel.resolve()}, {candidate.resolve()})"
    )


def load_trip_for_export(trip_arg: str) -> Trip:
    """Resolve <trip_arg> to a Trip bundle (bare id or path)."""
    trip_dir, fallback_id = _resolve_trip_dir(trip_arg)
    bundle = tc.load_trip(trip_dir)
    meta_trip_id = bundle.meta.get("trip_id") or fallback_id
    return Trip(trip_id=meta_trip_id, trip_dir=trip_dir, bundle=bundle)


def iter_day_slots(day: dict) -> Iterator[tuple[str, dict]]:
    """Yield (slot_id, slot_dict) for the 6 named slots in canonical order."""
    slots = day.get("slots", {}) or {}
    for slot_id in tc.NAMED_SLOTS:
        slot = slots.get(slot_id)
        if slot is None:
            continue
        yield slot_id, slot


def selected_option(slot: dict) -> Optional[dict]:
    """Return the slot's selected option dict, or None."""
    sel_id = slot.get("selected_option_id")
    if not sel_id:
        return None
    for opt in slot.get("options", []):
        if opt.get("option_id") == sel_id:
            return opt
    return None


def image_path_for_option(trip_dir: Path, option: dict) -> Optional[Path]:
    """Return cached image path for an option, or None (Q3f, no download)."""
    option_id = option.get("option_id")
    if not option_id:
        return None
    cache_dir = trip_dir / "cache" / "images"
    if not cache_dir.exists():
        return None
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidate = cache_dir / f"{option_id}.{ext}"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def atomic_write_bytes(target: Path, data: bytes) -> int:
    """Write bytes to target via <target>.tmp + rename."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)
    return target.stat().st_size


def _segment_owning_day(seg: dict) -> Optional[int]:
    """Safe wrapper: returns owning_day or None for malformed segments."""
    try:
        return tc.pick_owning_day(seg)
    except tc.TripContractError:
        return None


def segments_for_day(trip: Trip, day_n: int) -> list[dict]:
    """Return inter-city segments where owning_day == day_n."""
    return [
        seg for seg in (trip.transportation.get("segments", []) or [])
        if _segment_owning_day(seg) == day_n
    ]


def _is_prior_day_arrival(seg: dict, day_n: int) -> bool:
    depart_day = seg.get("depart_day")
    arrive_day = seg.get("arrive_day")
    if not isinstance(depart_day, int) or not isinstance(arrive_day, int):
        return False
    return arrive_day == day_n and depart_day < day_n


def arriving_from_prior_day(trip: Trip, day_n: int) -> list[dict]:
    """Return segments where arrive_day == day_n AND depart_day < day_n."""
    return [
        seg for seg in (trip.transportation.get("segments", []) or [])
        if _is_prior_day_arrival(seg, day_n)
    ]


def _accum_cost(cost, total: float, unknown: int) -> tuple[float, int]:
    if cost is None:
        return total, unknown + 1
    return total + float(cost), unknown


def _accum_slot_cost(slot: dict, total: float, unknown: int) -> tuple[float, int]:
    if slot.get("skipped"):
        return total, unknown
    opt = selected_option(slot)
    if opt is None:
        return total, unknown
    return _accum_cost(opt.get("cost"), total, unknown)


def day_total_for_export(day: dict, segments: list[dict]) -> tuple[float, int]:
    """Compute (day_total, unknown_count) matching the M2 budget contract."""
    total, unknown = 0.0, 0
    for _slot_id, slot in iter_day_slots(day):
        total, unknown = _accum_slot_cost(slot, total, unknown)
    accom = day.get("accommodation")
    if accom is not None:
        total, unknown = _accum_slot_cost(accom, total, unknown)
    for seg in segments:
        total, unknown = _accum_cost(seg.get("cost"), total, unknown)
    return total, unknown


def city_tz_for(city_id: Optional[str]) -> str:
    """Look up IANA TZID for a city_id, defaulting to Asia/Shanghai."""
    if not city_id:
        return DEFAULT_TZ
    return CITY_TZ_MAP.get(city_id.lower(), DEFAULT_TZ)
