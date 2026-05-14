"""Tests for POST /api/budget/recompute (lib/server/budget.py).

Tests call handle_budget() directly. No HTTP port allocated.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lib.server.budget import handle_budget
from lib.server.common import TripStore, atomic_write_json


def _req(trip_id: str, day: int | None = None) -> dict:
    req: dict = {"trip_id": trip_id}
    if day is not None:
        req["day"] = day
    return req


# ---------------------------------------------------------------------------
# Correct cost aggregation from day files.
# ---------------------------------------------------------------------------

def test_aggregates_day_costs_correctly(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """trip_total must equal sum of per-day totals across both days."""
    resp = handle_budget(store, _req(trip_id))
    assert resp["trip_id"] == trip_id
    assert "days" in resp
    assert len(resp["days"]) == 2
    day_sum = sum(d["day_total"] for d in resp["days"])
    assert abs(resp["trip_total"] - day_sum) < 0.01


def test_day_filter_returns_single_day(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """When req.day=1, only day 1 totals are returned."""
    resp = handle_budget(store, _req(trip_id, day=1))
    assert len(resp["days"]) == 1
    assert resp["days"][0]["day"] == 1


def test_day_total_matches_known_costs(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """Day 1 total = breakfast(80) + lunch(80) + dinner(80) + 3 activities(50each) = 390."""
    resp = handle_budget(store, _req(trip_id, day=1))
    day1 = resp["days"][0]
    # Breakfast+lunch+dinner selected at 80 CNY each (fixture: slot-1-1 option)
    meals = day1["breakdown"]["meals"]["amount"]
    assert abs(meals - 240.0) < 0.01
    # Three activities at 50 CNY each
    acts = day1["breakdown"]["activities"]["amount"]
    assert abs(acts - 150.0) < 0.01


# ---------------------------------------------------------------------------
# Missing cost (null) -> unknown_count increments, amount stays 0.
# ---------------------------------------------------------------------------

def test_null_cost_counts_as_unknown(
    data_root: Path, store: TripStore
):
    """Options with cost=None contribute unknown_count=1, not crash."""
    trip_id = "null-cost-trip"
    trip_dir = data_root / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema_version": "v2.0", "trip_id": trip_id, "day_count": 1,
        "currency_local": "CNY",
    }
    atomic_write_json(trip_dir / "meta.json", meta)
    null_opt = {
        "slot_id": "breakfast",
        "options": [{"option_id": "b1", "cost": None}],
        "selected_option_id": "b1",
        "skipped": False,
    }
    day = {
        "schema_version": "v2.0", "day": 1, "date": "2026-06-01",
        "breakfast": null_opt,
        "lunch": {"slot_id": "lunch", "options": [], "selected_option_id": None, "skipped": True},
        "dinner": {"slot_id": "dinner", "options": [], "selected_option_id": None, "skipped": True},
        "morning_activity": {"slot_id": "morning_activity", "options": [], "selected_option_id": None, "skipped": True},
        "afternoon_activity": {"slot_id": "afternoon_activity", "options": [], "selected_option_id": None, "skipped": True},
        "evening_activity": {"slot_id": "evening_activity", "options": [], "selected_option_id": None, "skipped": True},
        "accommodation": {"slot_id": "accommodation", "options": [], "selected_option_id": None, "skipped": True},
        "intra_city_routes": [],
    }
    atomic_write_json(trip_dir / "days" / "day-01.json", day)
    atomic_write_json(trip_dir / "transportation.json", {"schema_version": "v2.0", "segments": []})
    resp = handle_budget(store, {"trip_id": trip_id})
    day_entry = resp["days"][0]
    meals = day_entry["breakdown"]["meals"]
    assert meals["amount"] == 0.0
    assert meals["unknown_count"] == 1
