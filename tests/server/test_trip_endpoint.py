"""Tests for GET /api/trip/<trip_id> (lib/server/trip.py hydrate_trip).

Tests call hydrate_trip() directly. No HTTP port allocated.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lib.server.trip import hydrate_trip
from lib.server.common import TripStore, atomic_write_json


# ---------------------------------------------------------------------------
# Happy path: merged JSON with days, meta, route_cache returned.
# ---------------------------------------------------------------------------

def test_hydrate_trip_returns_required_keys(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """hydrate_trip must return a dict with meta, days, transportation, route_cache."""
    result = hydrate_trip(store, trip_id)
    assert "meta" in result
    assert "days" in result
    assert "transportation" in result
    assert "route_cache" in result


def test_hydrate_trip_meta_contains_trip_id(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """meta.trip_id must match the requested trip_id."""
    result = hydrate_trip(store, trip_id)
    assert result["meta"]["trip_id"] == trip_id


def test_hydrate_trip_days_count(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """Fixture has 2 days; hydrated days list must have 2 entries."""
    result = hydrate_trip(store, trip_id)
    assert len(result["days"]) == 2


def test_hydrate_trip_route_cache_starts_empty(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """Fixture has no route_cache.json; result must still be a non-null dict."""
    result = hydrate_trip(store, trip_id)
    rc = result["route_cache"]
    assert isinstance(rc, dict)


def test_hydrate_trip_includes_cached_route(
    scaffolded_trip: Path, store: TripStore, trip_id: str, route_cache_entry: dict
):
    """If route_cache.json exists with entries, hydrated result must include them."""
    cache = {"schema_version": "v2.0", "entries": {"a:b:walk": route_cache_entry}}
    atomic_write_json(store.trip_dir(trip_id) / "route_cache.json", cache)
    result = hydrate_trip(store, trip_id)
    rc = result["route_cache"]
    # route_cache may be returned as {schema_version, entries} or flat entries dict.
    entries = rc.get("entries", rc)
    assert "a:b:walk" in entries


# ---------------------------------------------------------------------------
# Missing trip raises FileNotFoundError (serves as 404 signal to the caller).
# ---------------------------------------------------------------------------

def test_hydrate_missing_trip_raises_file_not_found(store: TripStore):
    """Requesting a trip that has no meta.json must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        hydrate_trip(store, "does-not-exist")
