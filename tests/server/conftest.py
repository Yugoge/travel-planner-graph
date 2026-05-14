"""Fixtures for M4a server endpoint tests.

Handlers are called directly (not over HTTP) to avoid port allocation in CI.
Synthetic trip data matches the v2 per-day-file schema from schemas/v2/day.schema.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

from lib.server.common import TripStore  # noqa: E402


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _build_slot(slot_id: str, options: list[dict], selected_id: str | None,
                skipped: bool = False, skipped_reason: str | None = None) -> dict:
    return {
        "slot_id": slot_id,
        "options": options,
        "selected_option_id": selected_id,
        "skipped": skipped,
        "skipped_reason": skipped_reason,
    }


def _city_ctx() -> dict:
    return {"city_id": "test-city", "city_name": "Test City", "leg_index": 0, "role": "overnight"}


def _opt(option_id: str, name: str, cost: float | None) -> dict:
    return {
        "option_id": option_id,
        "name": name,
        "name_local": name,
        "location_summary": "Test Location",
        "cost": cost,
        "fit_score": 0.9,
        "why_fits_user": "test fixture",
        "source_agent": "meals",
        "city_context": _city_ctx(),
    }


def _meal_slot(slot_id: str, day_n: int) -> dict:
    opts = [_opt(f"{slot_id}-{day_n}-1", f"{slot_id.title()} A", 80.0),
            _opt(f"{slot_id}-{day_n}-2", f"{slot_id.title()} B", 95.0)]
    return _build_slot(slot_id, opts, f"{slot_id}-{day_n}-1")


def _activity_slot(slot_id: str, day_n: int) -> dict:
    label = slot_id.replace("_", " ").title()
    opts = [_opt(f"{slot_id}-{day_n}-1", label, 50.0)]
    return _build_slot(slot_id, opts, f"{slot_id}-{day_n}-1")


def _accom_slot(day_n: int) -> dict:
    opts = [_opt(f"acc-{day_n}-{i}", f"Hotel {i}", 700.0 + i * 50) for i in range(1, 4)]
    return _build_slot("accommodation", opts, f"acc-{day_n}-2")


def _build_day(day_n: int, date_str: str, stage: str = "draft-options") -> dict:
    """Build a synthetic v2 day file. Slots sit at top-level day keys (save.py shape)."""
    return {
        "schema_version": "v2.0",
        "day": day_n,
        "date": date_str,
        "city_id": "test-city",
        "city_name": "Test City",
        "leg_index": 0,
        "day_type": "normal",
        "stage": stage,
        "arrival_ts": None,
        "departure_ts": None,
        "breakfast": _meal_slot("breakfast", day_n),
        "morning_activity": _activity_slot("morning_activity", day_n),
        "lunch": _meal_slot("lunch", day_n),
        "afternoon_activity": _activity_slot("afternoon_activity", day_n),
        "dinner": _meal_slot("dinner", day_n),
        "evening_activity": _activity_slot("evening_activity", day_n),
        "accommodation": _accom_slot(day_n),
        "intra_city_routes": [],
        "warnings": [],
    }


def _leg(day_count: int) -> dict:
    return {"leg_index": 0, "city_id": "test-city",
            "city_name": "Test City", "first_day": 1, "last_day": day_count}


def _build_meta(trip_id: str, day_count: int) -> dict:
    return {
        "schema_version": "v2.0",
        "trip_id": trip_id,
        "title": "Test Trip",
        "title_local": "测试行程",
        "currency_local": "CNY",
        "user_budget": 10000,
        "day_count": day_count,
        "start_date": "2026-06-01",
        "end_date": "2026-06-03",
        "legs": [_leg(day_count)],
        "travelers": ["Yuge", "Jade"],
        "last_saved_ts": "2026-06-01T10:00:00+08:00",
        "current_editor_session": None,
        "auto_mode_used": False,
    }


def _scaffold_trip(data_root: Path, trip_id: str, day_count: int = 2) -> Path:
    """Write a minimal v2 trip layout and return the trip directory."""
    trip_dir = data_root / trip_id
    trip_dir.mkdir(parents=True, exist_ok=True)
    _write_json(trip_dir / "meta.json", _build_meta(trip_id, day_count))
    dates = ["2026-06-01", "2026-06-02", "2026-06-03"]
    for n in range(1, day_count + 1):
        _write_json(trip_dir / "days" / f"day-{n:02d}.json", _build_day(n, dates[n - 1]))
    _write_json(trip_dir / "transportation.json",
                {"schema_version": "v2.0", "segments": []})
    return trip_dir


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def store(data_root: Path) -> TripStore:
    data_root.mkdir(parents=True, exist_ok=True)
    return TripStore(data_root)


@pytest.fixture
def trip_id() -> str:
    return "test-trip-001"


@pytest.fixture
def scaffolded_trip(store: TripStore, data_root: Path, trip_id: str) -> Path:
    """Two-day trip scaffolded on disk; returns trip dir."""
    return _scaffold_trip(data_root, trip_id, day_count=2)


@pytest.fixture
def route_cache_entry() -> dict:
    """A pre-populated route cache entry for test injection."""
    return {
        "duration_min": 12,
        "distance_km": 2.3,
        "mode": "walk",
        "cost": None,
        "polyline": "",
        "fetched_ts": "2026-06-01T10:00:00+08:00",
        "status": "ok",
    }
