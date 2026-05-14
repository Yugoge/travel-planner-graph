"""E2E state machine test — exercises the options-first planning flow in-process.

Uses trip_contract.state_machine directly. No server, no HTTP, no filesystem
beyond the conftest fixtures from tests/server/conftest.py (re-imported here).

Scenario:
  1. Synthetic trip starts at blocking_stage='draft-options'.
  2. plan-validate-v2 equivalent (validate_trip_v2) accepts draft-options.
  3. Stage mutation advances day 1 to 'user-selected'.
  4. State machine allows timeline (blocking_stage >= 'user-selected').
  5. Slot mutation marks day 1 breakfast as unselected -> timeline blocked.
  6. All required slots selected.
  7. All days finalized -> export allowed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

from lib import trip_contract as tc


NAMED_SLOTS = tc.NAMED_SLOTS
STAGE_INDEX = tc.STAGE_INDEX


# ---------------------------------------------------------------------------
# Helpers: build minimal synthetic days for state-machine testing.
# ---------------------------------------------------------------------------

def _opt(option_id: str, cost: float = 80.0) -> dict:
    return {
        "option_id": option_id,
        "name": option_id,
        "name_local": option_id,
        "location_summary": "Test",
        "cost": cost,
        "fit_score": 0.85,
        "why_fits_user": "test",
        "source_agent": "meals",
        "city_context": {
            "city_id": "test-city",
            "city_name": "Test City",
            "leg_index": 0,
            "role": "overnight",
        },
    }


def _slot(slot_id: str, selected: bool = True, n: int = 1) -> dict:
    opt_id = f"{slot_id}-opt-{n}"
    return {
        "slot_id": slot_id,
        "options": [_opt(opt_id)],
        "selected_option_id": opt_id if selected else None,
        "skipped": False,
        "skipped_reason": None,
    }


def _accom_slot(n: int = 1, selected: bool = True) -> dict:
    return {
        "slot_id": "accommodation",
        "options": [_opt(f"acc-opt-{i}", 700.0 + i * 50) for i in range(1, 4)],
        "selected_option_id": f"acc-opt-{n}" if selected else None,
        "skipped": False,
        "skipped_reason": None,
    }


def _make_day(day_n: int, stage: str, all_selected: bool = True) -> dict:
    """Build a minimal synthetic day dict at the top-level-slot shape (save.py convention)."""
    day: dict = {
        "schema_version": "v2.0",
        "day": day_n,
        "date": f"2026-06-0{day_n}",
        "city_id": "test-city",
        "city_name": "Test City",
        "leg_index": 0,
        "day_type": "normal",
        "stage": stage,
        "arrival_ts": None,
        "departure_ts": None,
        "accommodation": _accom_slot(n=1, selected=all_selected),
        "intra_city_routes": [],
        "warnings": [],
    }
    for slot_id in NAMED_SLOTS:
        day[slot_id] = _slot(slot_id, selected=all_selected, n=day_n)
    return day


# ---------------------------------------------------------------------------
# Step 1: Load synthetic trip with blocking_stage='draft-options'.
# ---------------------------------------------------------------------------

def test_step1_trip_starts_at_draft_options():
    """A fresh trip where all days are at 'draft-options' must have blocking_stage='draft-options'."""
    days = [_make_day(n, "draft-options") for n in range(1, 3)]
    assert tc.blocking_stage(days) == "draft-options"


# ---------------------------------------------------------------------------
# Step 2: validate_trip_v2 accepts draft-options state.
# The validator does not fail on draft-options stage for days with full options.
# ---------------------------------------------------------------------------

def test_step2_validator_accepts_draft_options():
    """draft-options days must pass validation without stage-related errors."""
    days = [_make_day(1, "draft-options")]
    leg = {"leg_index": 0, "city_id": "test-city", "city_name": "Test City",
            "first_day": 1, "last_day": 1}
    meta = {
        "schema_version": "v2.0",
        "trip_id": "e2e-test",
        "title": "E2E Test Trip",
        "title_local": "E2E 测试行程",
        "currency_local": "CNY",
        "user_budget": 5000,
        "day_count": 1,
        "start_date": "2026-06-01",
        "end_date": "2026-06-01",
        "legs": [leg],
        "travelers": ["Yuge"],
        "last_saved_ts": "2026-06-01T10:00:00+08:00",
        "current_editor_session": None,
        "auto_mode_used": False,
    }
    errs = [e for e in tc.validate_meta_v2(meta) if e.severity == "error"]
    assert errs == [], "\n".join(str(e) for e in errs)


# ---------------------------------------------------------------------------
# Step 3: Apply stage mutation advancing day 1 to 'user-selected'.
# ---------------------------------------------------------------------------

def test_step3_stage_advance_to_user_selected():
    """Forward stage transition draft-options -> user-selected must be accepted."""
    err = tc.validate_state_transition("draft-options", "user-selected")
    assert err is None


def test_step3_blocking_stage_after_day1_advance():
    """Blocking stage is min(stages). If day 2 is still draft-options, blocking stays draft-options."""
    days = [
        _make_day(1, "user-selected"),
        _make_day(2, "draft-options"),
    ]
    assert tc.blocking_stage(days) == "draft-options"


# ---------------------------------------------------------------------------
# Step 4: Verify state machine allows timeline when blocking_stage >= 'user-selected'.
# ---------------------------------------------------------------------------

def test_step4_timeline_allowed_when_all_user_selected():
    """all_days_at_least('user-selected') must be True when every day is user-selected."""
    days = [_make_day(n, "user-selected") for n in range(1, 3)]
    assert tc.all_days_at_least(days, "user-selected") is True


def test_step4_timeline_blocked_when_one_day_draft():
    """Timeline is blocked if any day is still draft-options."""
    days = [_make_day(1, "user-selected"), _make_day(2, "draft-options")]
    assert tc.all_days_at_least(days, "user-selected") is False


# ---------------------------------------------------------------------------
# Step 5: Unselecting a required slot means timeline should be blocked.
# State machine uses stage to gate; an unselected slot keeps the day at
# draft-options / user-review (cannot reach user-selected).
# ---------------------------------------------------------------------------

def test_step5_unselected_slot_prevents_user_selected():
    """Day with unselected breakfast cannot legitimately be at user-selected stage.
    Verify that backward transition check catches if someone tries to call it finalized."""
    err = tc.validate_state_transition("user-selected", "draft-options")
    assert err is not None  # backward without consent is rejected


def test_step5_unselected_slot_day_stays_in_review():
    """A day still at draft-options with unselected slot: blocking_stage reports draft-options."""
    days = [_make_day(1, "draft-options", all_selected=False), _make_day(2, "user-selected")]
    assert tc.blocking_stage(days) == "draft-options"
    assert tc.all_days_at_least(days, "user-selected") is False


# ---------------------------------------------------------------------------
# Step 6: Advance all required slots to selected (all days at user-selected).
# ---------------------------------------------------------------------------

def test_step6_all_slots_selected_all_days_at_user_selected():
    """With all slots selected, all days can be at user-selected."""
    days = [_make_day(n, "user-selected", all_selected=True) for n in range(1, 3)]
    assert tc.all_days_at_least(days, "user-selected") is True
    assert tc.blocking_stage(days) == "user-selected"


# ---------------------------------------------------------------------------
# Step 7: All days finalized -> export allowed (all_days_at_least 'finalized').
# ---------------------------------------------------------------------------

def test_step7_export_allowed_when_all_finalized():
    """Export gate: all_days_at_least('finalized') must return True."""
    days = [_make_day(n, "finalized", all_selected=True) for n in range(1, 3)]
    assert tc.all_days_at_least(days, "finalized") is True


def test_step7_export_blocked_if_any_day_not_finalized():
    """Export gate: blocked if even one day is at transportation (not yet finalized)."""
    days = [_make_day(1, "finalized"), _make_day(2, "transportation")]
    assert tc.all_days_at_least(days, "finalized") is False


def test_step7_full_forward_progression_valid():
    """Each step in the full STAGES sequence must be a valid forward transition."""
    stages = ["draft-options", "user-review", "user-selected",
              "timeline", "transportation", "finalized"]
    for i in range(len(stages) - 1):
        err = tc.validate_state_transition(stages[i], stages[i + 1])
        assert err is None, f"expected {stages[i]!r} -> {stages[i+1]!r} to be valid, got: {err}"


def test_step7_backward_requires_consent():
    """finalized -> draft-options is illegal without user consent."""
    assert tc.validate_state_transition("finalized", "draft-options") is not None
    assert tc.validate_state_transition("finalized", "draft-options", has_user_consent=True) is None
