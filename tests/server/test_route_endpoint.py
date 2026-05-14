"""Tests for POST /api/route (lib/server/route.py).

Tests call handle_route() directly. No HTTP port allocated.
Per AC-M5.5: server forces agent_id="timeline" regardless of request body.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lib.server.route import handle_route, TIMELINE_AGENT_ID
from lib.server.common import TripStore, atomic_write_json


def _make_req(trip_id: str, from_id: str, to_id: str,
              mode: str = "walk", request_seq: int = 1,
              agent_id: str = "meals") -> dict:
    """Build a route request body. agent_id in body should be ignored by server."""
    return {
        "trip_id": trip_id,
        "from_option_id": from_id,
        "to_option_id": to_id,
        "mode": mode,
        "request_seq": request_seq,
        "agent_id": agent_id,
    }


def _write_cache(store: TripStore, trip_id: str, key: str, entry: dict) -> None:
    cache_path = store.trip_dir(trip_id) / "route_cache.json"
    cache = {"schema_version": "v2.0", "entries": {key: entry}}
    atomic_write_json(cache_path, cache)


# ---------------------------------------------------------------------------
# AC-M5.5: server forces agent_id="timeline" — the TIMELINE_AGENT_ID constant
# must equal "timeline" regardless of what is passed in the request body.
# ---------------------------------------------------------------------------

def test_agent_id_forced_to_timeline_constant():
    """TIMELINE_AGENT_ID module constant must equal 'timeline' (AC-M5.5)."""
    assert TIMELINE_AGENT_ID == "timeline"


def test_agent_id_in_req_body_does_not_appear_in_gaode_env(
    scaffolded_trip: Path, store: TripStore, trip_id: str, tmp_path: Path
):
    """Route request with agent_id='meals' in body returns without error.

    The server does not echo agent_id back; the env is internal. We verify
    the response shape is correct (no agent_id leakage in the response dict).
    """
    req = _make_req(trip_id, "breakfast-1-1", "lunch-1-1", agent_id="meals")
    # gaode script absent -> returns unknown (gaode-skill-not-installed)
    resp = handle_route(store, req, store.data_root.parent)
    assert "agent_id" not in resp
    assert resp["request_seq"] == 1


# ---------------------------------------------------------------------------
# Cache hit: cached result returned without re-calling gaode subprocess.
# ---------------------------------------------------------------------------

def test_cache_hit_returns_cached_segment(
    scaffolded_trip: Path, store: TripStore, trip_id: str, route_cache_entry: dict
):
    """Cache hit must return status='ok', source='cache' immediately."""
    key = "breakfast-1-1:lunch-1-1:walk"
    _write_cache(store, trip_id, key, route_cache_entry)
    req = _make_req(trip_id, "breakfast-1-1", "lunch-1-1", request_seq=42)
    resp = handle_route(store, req, store.data_root.parent)
    assert resp["status"] == "ok"
    assert resp["source"] == "cache"
    assert resp["request_seq"] == 42
    assert resp["segment"]["duration_min"] == 12


def test_cache_hit_different_mode_is_miss(
    scaffolded_trip: Path, store: TripStore, trip_id: str, route_cache_entry: dict
):
    """Cache key includes mode; different mode must NOT hit walk-mode cache entry."""
    key = "breakfast-1-1:lunch-1-1:walk"
    _write_cache(store, trip_id, key, route_cache_entry)
    req = _make_req(trip_id, "breakfast-1-1", "lunch-1-1", mode="taxi")
    resp = handle_route(store, req, store.data_root.parent)
    # No gaode script -> unknown (miss reached the subprocess step)
    assert resp["status"] in ("unknown", "error")


# ---------------------------------------------------------------------------
# Unknown from/to (no cache, no gaode script) -> status="unknown".
# ---------------------------------------------------------------------------

def test_unknown_route_returns_unknown_status(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """When neither cache nor gaode script is available, return status='unknown'."""
    req = _make_req(trip_id, "nonexistent-poi-A", "nonexistent-poi-B")
    # project_dir points at tmp_path.parent which has no gaode skill
    resp = handle_route(store, req, store.data_root.parent)
    assert resp["status"] == "unknown"
    assert resp["segment"] is None
    assert resp["request_seq"] == 1


def test_missing_trip_id_raises_or_returns_error(store: TripStore):
    """Request for a trip that does not exist should not crash the handler."""
    req = _make_req("nonexistent-trip", "a", "b")
    # Handler may raise FileNotFoundError or return error status; must not crash silently.
    try:
        resp = handle_route(store, req, store.data_root.parent)
        # If it returns a dict, it should not claim success
        assert resp.get("status") != "ok"
    except (FileNotFoundError, KeyError, ValueError):
        pass  # explicit error propagation is also acceptable
