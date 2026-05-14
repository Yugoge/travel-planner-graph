"""M2 v2 fixture validation tests (spec-20260508-221237).

Loads each fixture under tests/fixtures/trip-contract/ and verifies the M2
validator returns the expected verdict.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import trip_contract as tc


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "trip-contract"


def _load(name: str) -> dict:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)


def _meta() -> dict:
    return _load("meta.json")


def _errors(day_name: str, is_first_night: bool = False) -> list[tc.ValidationError]:
    return tc.validate_day_v2(_load(day_name), _meta(), position=f"$.{day_name}", is_first_night=is_first_night)


def test_normal_day_passes_when_first_night():
    """normal-day.json is leg-0 day-1; needs >=3 accommodation options."""
    errs = [e for e in _errors("normal-day.json", is_first_night=True) if e.severity == "error"]
    assert errs == [], "\n".join(str(e) for e in errs)


def test_arrival_day_passes():
    """arrival_ts=15:30 mandates pre-lunch slots skipped; lunch also (>=13:30)."""
    errs = [e for e in _errors("arrival-day.json") if e.severity == "error"]
    assert errs == [], "\n".join(str(e) for e in errs)


def test_city_change_day_passes():
    """arrival 11:00, departure 08:30; pre-arrival breakfast/morning skipped only."""
    errs = [e for e in _errors("city-change-day.json") if e.severity == "error"]
    assert errs == [], "\n".join(str(e) for e in errs)


def test_red_eye_day_passes():
    """departure 22:30 red-eye; accommodation skipped (owned by next day's destination)."""
    errs = [e for e in _errors("red-eye-day.json") if e.severity == "error"]
    assert errs == [], "\n".join(str(e) for e in errs)


def test_late_arrival_day_passes():
    """arrival 21:30; dinner late_arrival_placeholder=true; evening user-omit."""
    errs = [e for e in _errors("late-arrival-day.json") if e.severity == "error"]
    assert errs == [], "\n".join(str(e) for e in errs)


def test_legacy_shape_fails_with_forbidden_error():
    errs = _errors("legacy-shape-day.json")
    codes = {e.code for e in errs}
    assert "LEGACY_SHAPE_FORBIDDEN" in codes


def test_meta_passes():
    errs = tc.validate_meta_v2(_meta())
    error_severity = [e for e in errs if e.severity == "error"]
    assert error_severity == [], "\n".join(str(e) for e in error_severity)


def test_state_machine_forward_ok():
    assert tc.validate_state_transition("draft-options", "user-review") is None
    assert tc.validate_state_transition("user-selected", "finalized") is None


def test_state_machine_backward_blocked_without_consent():
    assert tc.validate_state_transition("finalized", "draft-options") is not None


def test_state_machine_backward_with_consent():
    assert tc.validate_state_transition("finalized", "draft-options", has_user_consent=True) is None


def test_blocking_stage_uses_min():
    days = [{"stage": "finalized"}, {"stage": "draft-options"}, {"stage": "user-selected"}]
    assert tc.blocking_stage(days) == "draft-options"


def test_furthest_stage_uses_max():
    days = [{"stage": "finalized"}, {"stage": "draft-options"}, {"stage": "user-selected"}]
    assert tc.furthest_stage(days) == "finalized"


def test_pick_owning_day_returns_depart_day():
    seg = {"segment_id": "s1", "depart_day": 2, "arrive_day": 3}
    assert tc.pick_owning_day(seg) == 2


def test_legacy_detection_finds_nested():
    obj = {"slots": {"breakfast": {"primary": {"x": 1}, "alternatives": []}}}
    paths = tc.detect_legacy_shape(obj)
    assert any("breakfast" in p for p in paths)


def test_skip_threshold_lunch():
    """arrival_ts=13:30 should mandate lunch skip."""
    day = {"day_type": "arrival", "arrival_ts": "2026-06-04T13:30:00+08:00"}
    expected = tc.expected_skips_for_day(day)
    assert expected["lunch"] == "pre-arrival"
    assert expected["afternoon_activity"] is None  # 13:30 < 16:00


def test_skip_threshold_afternoon():
    day = {"day_type": "arrival", "arrival_ts": "2026-06-04T16:00:00+08:00"}
    expected = tc.expected_skips_for_day(day)
    assert expected["lunch"] == "pre-arrival"
    assert expected["afternoon_activity"] == "pre-arrival"
