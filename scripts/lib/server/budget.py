"""POST /api/budget/recompute pure aggregation handler (spec §5.10, M2 §9).

Aggregates costs from day.json, transportation.json, route_cache.json. No
gaode calls. Returns per-day total + per-trip total + per-slot breakdown.

Lock posture (codex Q2): hold per-trip lock only while reading the snapshot,
release before serializing the response.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import TripStore, load_json_or_default

SCHEMA_VERSION = "v2.0"
_MEAL_SLOTS = ("breakfast", "lunch", "dinner")
_ACTIVITY_SLOTS = ("morning_activity", "afternoon_activity", "evening_activity")


def _try_load_day_file(days_dir: Path, n: int) -> dict | None:
    p = days_dir / f"day-{n:02d}.json"
    if not p.exists():
        return None
    return load_json_or_default(p, {})


def _load_all_days(trip_dir: Path, meta: dict) -> list[dict]:
    days_dir = trip_dir / "days"
    day_count = meta.get("day_count", 0)
    raw = [_try_load_day_file(days_dir, n) for n in range(1, day_count + 1)]
    return [d for d in raw if d is not None]


def _read_trip_snapshot(
    store: TripStore, trip_id: str
) -> tuple[dict, list[dict], dict, dict]:
    with store.lock(trip_id):
        return _do_read_snapshot(store, trip_id)


def _do_read_snapshot(
    store: TripStore, trip_id: str
) -> tuple[dict, list[dict], dict, dict]:
    trip_dir = store.trip_dir(trip_id)
    meta = load_json_or_default(trip_dir / "meta.json", {})
    days = _load_all_days(trip_dir, meta)
    transportation = load_json_or_default(
        trip_dir / "transportation.json",
        {"schema_version": SCHEMA_VERSION, "segments": []},
    )
    route_cache = load_json_or_default(
        trip_dir / "route_cache.json",
        {"schema_version": SCHEMA_VERSION, "entries": {}},
    )
    return meta, days, transportation, route_cache


def _option_cost(opt: dict) -> tuple[float, int]:
    cost = opt.get("cost")
    if cost is None:
        return 0.0, 1
    return float(cost), 0


def _find_selected_option(slot: dict) -> dict | None:
    sel_id = slot.get("selected_option_id")
    if not sel_id:
        return None
    for opt in slot.get("options", []):
        if opt.get("option_id") == sel_id:
            return opt
    return None


def _slot_cost(slot: dict) -> tuple[float, int]:
    if slot.get("skipped"):
        return 0.0, 0
    sel = _find_selected_option(slot)
    if sel is None:
        return 0.0, 0
    return _option_cost(sel)


def _sum_slots(day: dict, slot_ids: tuple[str, ...]) -> tuple[float, int]:
    pairs = [_slot_cost(day.get("slots", {}).get(sid, {})) for sid in slot_ids]
    return sum(a for a, _ in pairs), sum(u for _, u in pairs)


def _is_segment_owning(seg: dict, day_n: int) -> bool:
    return seg.get("owning_day") == day_n


def _segment_cost(seg: dict) -> tuple[float, int]:
    cost = seg.get("cost")
    if cost is None:
        return 0.0, 1
    return float(cost), 0


def _transport_cost_for_day(transportation: dict, day_n: int) -> tuple[float, int]:
    segs = [s for s in transportation.get("segments", []) if _is_segment_owning(s, day_n)]
    pairs = [_segment_cost(s) for s in segs]
    return sum(a for a, _ in pairs), sum(u for _, u in pairs)


def _intra_seg_cost(ref: dict, entries: dict) -> tuple[float, int]:
    key = f"{ref.get('from_option_id')}:{ref.get('to_option_id')}:{ref.get('mode')}"
    seg = entries.get(key)
    if seg is None:
        return 0.0, 1
    return _segment_cost(seg)


def _intra_city_cost_for_day(day: dict, route_cache: dict) -> tuple[float, int]:
    entries = route_cache.get("entries", {})
    refs = day.get("intra_city_routes", [])
    pairs = [_intra_seg_cost(r, entries) for r in refs]
    return sum(a for a, _ in pairs), sum(u for _, u in pairs)


def _build_breakdown(
    day: dict, day_n: int, transportation: dict, route_cache: dict
) -> dict:
    meals_amt, meals_unk = _sum_slots(day, _MEAL_SLOTS)
    acts_amt, acts_unk = _sum_slots(day, _ACTIVITY_SLOTS)
    accom_amt, accom_unk = _slot_cost(day.get("accommodation", {}))
    trans_amt, trans_unk = _transport_cost_for_day(transportation, day_n)
    intra_amt, intra_unk = _intra_city_cost_for_day(day, route_cache)
    return {
        "meals": {"amount": meals_amt, "unknown_count": meals_unk},
        "activities": {"amount": acts_amt, "unknown_count": acts_unk},
        "accommodation": {"amount": accom_amt, "unknown_count": accom_unk},
        "transportation": {"amount": trans_amt, "unknown_count": trans_unk},
        "intra_city": {"amount": intra_amt, "unknown_count": intra_unk},
    }


def _compute_day_entry(
    day: dict, day_n: int, transportation: dict, route_cache: dict
) -> dict:
    breakdown = _build_breakdown(day, day_n, transportation, route_cache)
    return {
        "day": day_n,
        "day_total": sum(b["amount"] for b in breakdown.values()),
        "breakdown": breakdown,
    }


def _select_target_days(
    days: list[dict], requested_day: Any
) -> list[tuple[int, dict]]:
    pairs = list(enumerate(days, start=1))
    if requested_day is None:
        return pairs
    return [(n, d) for n, d in pairs if n == requested_day]


def handle_budget(store: TripStore, req: dict) -> dict[str, Any]:
    """Handle POST /api/budget/recompute. Returns BudgetResponse-shaped dict.

    `req.day` filters to single day if provided. `req.delta` is accepted for
    forward-compatibility but currently triggers full recompute (codex Q2:
    simplest correct).
    """
    trip_id = req["trip_id"]
    meta, days, transportation, route_cache = _read_trip_snapshot(store, trip_id)
    # Compute all days unconditionally so trip_total always covers the full trip.
    all_pairs = list(enumerate(days, start=1))
    all_day_entries = [
        _compute_day_entry(d, n, transportation, route_cache) for n, d in all_pairs
    ]
    trip_total = sum(e["day_total"] for e in all_day_entries)
    # Filter for the response breakdown only if a specific day is requested.
    req_day = req.get("day")
    if req_day is not None:
        day_entries = [e for e in all_day_entries if e["day"] == req_day]
    else:
        day_entries = all_day_entries
    return {
        "schema_version": SCHEMA_VERSION,
        "trip_id": trip_id,
        "trip_total": trip_total,
        "currency_local": meta.get("currency_local", "CNY"),
        "days": day_entries,
    }
