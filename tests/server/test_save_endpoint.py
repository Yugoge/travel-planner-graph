"""Tests for POST /api/save (lib/server/save.py).

Tests call handle_save() directly. No HTTP port allocated.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lib.server.save import handle_save
from lib.server.common import TripStore, atomic_write_json, load_json_or_default


def _make_save_req(trip_id: str, day: int, mutations: list[dict],
                   editor_session: str = "sess-abc") -> dict:
    return {
        "trip_id": trip_id,
        "day": day,
        "mutations": mutations,
        "editor_session": editor_session,
    }


def _read_day(store: TripStore, trip_id: str, day_n: int) -> dict:
    p = store.trip_dir(trip_id) / "days" / f"day-{day_n:02d}.json"
    return load_json_or_default(p, {})


def _read_meta(store: TripStore, trip_id: str) -> dict:
    p = store.trip_dir(trip_id) / "meta.json"
    return load_json_or_default(p, {})


# ---------------------------------------------------------------------------
# Valid payload writes to data dir atomically.
# ---------------------------------------------------------------------------

def test_valid_save_writes_selected_option(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """select mutation must persist selected_option_id to the day file."""
    req = _make_save_req(trip_id, 1, [
        {"type": "select", "slot": "breakfast", "option_id": "breakfast-1-2"},
    ])
    resp = handle_save(store, req)
    assert resp["conflict"] is None
    day = _read_day(store, trip_id, 1)
    slot = day["slots"]["breakfast"]
    assert slot.get("selected_option_id") == "breakfast-1-2"


def test_valid_save_writes_stage_mutation(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """stage mutation must persist day.stage."""
    req = _make_save_req(trip_id, 1, [
        {"type": "stage", "to_stage": "user-selected"},
    ])
    handle_save(store, req)
    day = _read_day(store, trip_id, 1)
    assert day.get("stage") == "user-selected"


def test_valid_save_updates_meta_last_saved_ts(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """A successful save must update meta.json last_saved_ts."""
    before = _read_meta(store, trip_id).get("last_saved_ts", "")
    req = _make_save_req(trip_id, 1, [{"type": "stage", "to_stage": "user-selected"}])
    handle_save(store, req)
    after = _read_meta(store, trip_id).get("last_saved_ts", "")
    assert after != "" and after != before


# ---------------------------------------------------------------------------
# Conflicting editor_session returns 409-soft (but save still proceeds).
# ---------------------------------------------------------------------------

def test_409_soft_on_session_conflict(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """When editor_session differs from meta's current_editor_session, return 409-soft."""
    # First save establishes sess-alpha as current_editor_session.
    req1 = _make_save_req(trip_id, 1, [{"type": "stage", "to_stage": "user-review"}],
                          editor_session="sess-alpha")
    resp1 = handle_save(store, req1)
    assert resp1["conflict"] is None

    # Second save from a different session gets 409-soft.
    req2 = _make_save_req(trip_id, 1, [{"type": "stage", "to_stage": "user-selected"}],
                          editor_session="sess-beta")
    resp2 = handle_save(store, req2)
    assert resp2["conflict"] == "409-soft"


def test_409_soft_save_still_persists(
    scaffolded_trip: Path, store: TripStore, trip_id: str
):
    """409-soft is advisory; the mutation must still be written (last-writer-wins)."""
    req1 = _make_save_req(trip_id, 1, [], editor_session="sess-alpha")
    handle_save(store, req1)
    req2 = _make_save_req(trip_id, 1, [{"type": "stage", "to_stage": "finalized"}],
                          editor_session="sess-beta")
    handle_save(store, req2)
    day = _read_day(store, trip_id, 1)
    assert day.get("stage") == "finalized"


# ---------------------------------------------------------------------------
# Missing trip_id: save.py creates the day file regardless (mkdir -p behavior).
# Verify that a missing meta does not crash the handler.
# ---------------------------------------------------------------------------

def test_save_missing_trip_dir_does_not_crash(store: TripStore):
    """Saving to a nonexistent trip dir should create the file, not raise."""
    req = _make_save_req("brand-new-trip", 1, [{"type": "stage", "to_stage": "draft-options"}])
    resp = handle_save(store, req)
    assert "saved_ts" in resp
