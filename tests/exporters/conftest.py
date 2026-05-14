"""Fixture builder for M6 exporter tests.

Builds a v2 trip bundle layout on disk (data/<trip>/meta.json + days/day-NN.json
+ transportation.json + cache/images/...) so the exporters can load via the
canonical trip_contract.load_trip path.
"""

from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path

import pytest

# Ensure project root on sys.path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


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


def _city_ctx(city_id: str = "beijing") -> dict:
    return {
        "city_id": city_id,
        "city_name": city_id.title(),
        "leg_index": 0,
        "role": "overnight",
    }


def _opt(option_id: str, name: str, name_local: str | None, cost: float | None,
         **extras) -> dict:
    return {
        "option_id": option_id,
        "name": name,
        "name_local": name_local,
        "location_summary": extras.get("location_summary", "Dongcheng"),
        "cost": cost,
        "fit_score": extras.get("fit_score", 0.85),
        "why_fits_user": extras.get("why_fits_user", "matches preferences"),
        "source_agent": extras.get("source_agent", "meals"),
        "city_context": extras.get("city_context", _city_ctx()),
    }


def _meal_options(slot_id: str, day_n: int) -> list[dict]:
    return [
        _opt(f"{slot_id}-{day_n}-1", f"{slot_id.title()} A", f"{slot_id}A CJK-Name", 80.0),
        _opt(f"{slot_id}-{day_n}-2", f"{slot_id.title()} B", f"{slot_id}B CJK-Name", 95.0),
    ]


def _activity_options(slot_id: str, day_n: int, cost: float | None = 50.0) -> list[dict]:
    return [
        _opt(f"{slot_id}-{day_n}-1", f"{slot_id.title()} Spot",
             f"{slot_id} CJK-Attraction", cost,
             source_agent="attractions"),
    ]


def _accom_options(day_n: int, cost: float = 700.0) -> list[dict]:
    return [
        _opt(f"acc-{day_n}-{i}", f"Hotel {i}", f"Hotel-CJK {i}", cost + i * 50,
             source_agent="accommodation")
        for i in range(1, 4)
    ]


def _build_six_slots(day_n: int) -> dict:
    sel = lambda s: f"{s}-{day_n}-1"  # noqa: E731
    return {
        "breakfast": _build_slot("breakfast", _meal_options("breakfast", day_n),
                                 sel("breakfast")),
        "morning_activity": _build_slot(
            "morning_activity", _activity_options("morning_activity", day_n),
            sel("morning_activity")),
        "lunch": _build_slot("lunch", _meal_options("lunch", day_n), sel("lunch")),
        "afternoon_activity": _build_slot(
            "afternoon_activity",
            _activity_options("afternoon_activity", day_n, 30.0),
            sel("afternoon_activity")),
        "dinner": _build_slot("dinner", _meal_options("dinner", day_n), sel("dinner")),
        "evening_activity": _build_slot(
            "evening_activity",
            _activity_options("evening_activity", day_n, 0.0),
            sel("evening_activity")),
    }


def _normal_day(day_n: int, date_str: str) -> dict:
    accom = _build_slot("accommodation", _accom_options(day_n), f"acc-{day_n}-2")
    return {
        "schema_version": "v2.0",
        "day": day_n,
        "date": date_str,
        "city_id": "beijing",
        "city_name": "Beijing",
        "leg_index": 0,
        "day_type": "normal",
        "stage": "user-selected",
        "arrival_ts": None,
        "departure_ts": None,
        "slots": _build_six_slots(day_n),
        "accommodation": accom,
        "intra_city_routes": {},
        "warnings": [],
    }


def _red_eye_day(day_n: int, date_str: str) -> dict:
    day = _normal_day(day_n, date_str)
    day["day_type"] = "red-eye"
    day["departure_ts"] = f"{date_str}T23:30:00+08:00"
    return day


def _next_day_after_red_eye(day_n: int, date_str: str) -> dict:
    day = _normal_day(day_n, date_str)
    day["day_type"] = "arrival"
    day["arrival_ts"] = f"{date_str}T02:15:00+08:00"
    day["accommodation"]["skipped"] = True
    day["accommodation"]["selected_option_id"] = None
    day["accommodation"]["skipped_reason"] = "red-eye-spans-prior-day"
    return day


def _write_minimal_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = b"IHDR" + ihdr_data
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + ihdr + struct.pack(
        ">I", zlib.crc32(ihdr))
    raw = b"\x00\xff\xff\xff"
    comp = zlib.compress(raw)
    idat_body = b"IDAT" + comp
    idat_chunk = struct.pack(">I", len(comp)) + idat_body + struct.pack(
        ">I", zlib.crc32(idat_body))
    iend_body = b"IEND"
    iend_chunk = struct.pack(">I", 0) + iend_body + struct.pack(
        ">I", zlib.crc32(iend_body))
    path.write_bytes(header + ihdr_chunk + idat_chunk + iend_chunk)


def _build_meta(trip_id: str, day_count: int, start_date: str, end_date: str) -> dict:
    return {
        "schema_version": "v2.0",
        "trip_id": trip_id,
        "title": "Exporter Test Trip",
        "title_local": "导出测试行程",
        "currency_local": "CNY",
        "user_budget": 12000,
        "day_count": day_count,
        "start_date": start_date,
        "end_date": end_date,
        "legs": [{
            "leg_index": 0, "city_id": "beijing", "city_name": "Beijing",
            "first_day": 1, "last_day": day_count,
        }],
        "travelers": ["Matilde", "Jade"],
        "last_saved_ts": "2026-05-14T10:00:00+08:00",
        "current_editor_session": None,
        "auto_mode_used": False,
    }


def _scaffold_trip(trip_dir: Path, trip_id: str, days: list[dict],
                   transportation: dict | None = None) -> None:
    trip_dir.mkdir(parents=True, exist_ok=True)
    start_date = days[0]["date"]
    end_date = days[-1]["date"]
    _write_json(trip_dir / "meta.json",
                _build_meta(trip_id, len(days), start_date, end_date))
    for day in days:
        _write_json(trip_dir / "days" / f"day-{day['day']:02d}.json", day)
    transport = transportation or {"schema_version": "v2.0", "segments": []}
    _write_json(trip_dir / "transportation.json", transport)


@pytest.fixture
def normal_trip(tmp_path):
    trip_id = "exporter-normal"
    trip_dir = tmp_path / trip_id
    days = [
        _normal_day(1, "2026-06-01"),
        _normal_day(2, "2026-06-02"),
        _normal_day(3, "2026-06-03"),
    ]
    _scaffold_trip(trip_dir, trip_id, days)
    return trip_dir


@pytest.fixture
def red_eye_trip(tmp_path):
    trip_id = "exporter-red-eye"
    trip_dir = tmp_path / trip_id
    days = [
        _normal_day(1, "2026-06-01"),
        _red_eye_day(2, "2026-06-02"),
        _next_day_after_red_eye(3, "2026-06-03"),
    ]
    transportation = {
        "schema_version": "v2.0",
        "segments": [{
            "segment_id": "seg-bj-lj-red",
            "from_city": "Beijing",
            "to_city": "Lijiang",
            "mode": "flight",
            "depart_day": 2,
            "arrive_day": 3,
            "depart_ts": "2026-06-02T23:30:00+08:00",
            "arrive_ts": "2026-06-03T02:15:00+08:00",
            "cost": 1200,
            "status": "ok",
            "duration_minutes": 165,
        }],
    }
    _scaffold_trip(trip_dir, trip_id, days, transportation)
    return trip_dir


@pytest.fixture
def missing_image_trip(tmp_path):
    trip_id = "exporter-missing-img"
    trip_dir = tmp_path / trip_id
    days = [_normal_day(1, "2026-06-01")]
    _scaffold_trip(trip_dir, trip_id, days)
    return trip_dir


@pytest.fixture
def with_cached_image_trip(tmp_path):
    trip_id = "exporter-with-img"
    trip_dir = tmp_path / trip_id
    days = [_normal_day(1, "2026-06-01")]
    _scaffold_trip(trip_dir, trip_id, days)
    _write_minimal_png(trip_dir / "cache" / "images" / "breakfast-1-1.png")
    return trip_dir
