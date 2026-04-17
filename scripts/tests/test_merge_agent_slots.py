#!/usr/bin/env python3
"""Integration tests for merge_agent_slots() — the sole merge path in save.py.

Root Cause Fix reference (L4): the former merge_agent_days() performed full
day-object replacement, wiping sibling slots on partial-day updates. Confirmed
data loss: commit 47fccd4 (2026-04-13 13:14). merge_agent_slots() is now the
automatic default merge behavior (no flag needed).

Run with:
    source venv/bin/activate && python -m pytest scripts/tests/test_merge_agent_slots.py -v
or:
    source venv/bin/activate && python scripts/tests/test_merge_agent_slots.py
"""

import sys
from pathlib import Path

# Make scripts/ importable so lib.json_io resolves
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.json_io import merge_agent_slots  # noqa: E402


# ---------- fixture builders (kept shallow to respect quality gate) ----------

def _make_meal_slot(name_base, name_local):
    return {"name_base": name_base, "name_local": name_local}


def _make_day_entry(day, **kwargs):
    entry = {"day": day}
    entry.update(kwargs)
    return entry


def _make_meals_existing():
    breakfast = _make_meal_slot("Youyouju", "二友居")
    lunch = _make_meal_slot("Mutianyu Restaurant", "慕田峪长城")
    dinner = _make_meal_slot("Yaoji Chaogan", "姚记炒肝店")
    d2 = _make_day_entry(
        2, date="2026-05-09", location="Beijing",
        breakfast=breakfast, lunch=lunch, dinner=dinner,
    )
    return {"trip_name": "test-trip", "days": [d2]}


def _make_meals_dinner_update():
    new_dinner = _make_meal_slot("Nanmen Shuan", "南门涮肉")
    return {"days": [_make_day_entry(2, dinner=new_dinner)]}


# ---------- named-slot agents (meals, accommodation) ----------

def test_meals_partial_dinner_preserves_breakfast_and_lunch():
    """AC1: updating only dinner must not wipe breakfast or lunch."""
    existing = _make_meals_existing()
    update = _make_meals_dinner_update()

    result = merge_agent_slots(existing, update, "meals")
    d2 = result["days"][0]
    orig_d2 = existing["days"][0]
    assert d2["breakfast"] == orig_d2["breakfast"], "breakfast was wiped"
    assert d2["lunch"] == orig_d2["lunch"], "lunch was wiped"
    assert d2["dinner"]["name_local"] == "南门涮肉", "dinner not updated"
    assert d2["date"] == "2026-05-09", "date metadata lost"
    assert d2["location"] == "Beijing", "location metadata lost"
    assert result["trip_name"] == "test-trip", "trip metadata lost"


def test_accommodation_partial_update_preserves_metadata():
    """Updating only `accommodation` key on a day must preserve `date`/`location`."""
    d1 = _make_day_entry(
        1, date="2026-05-08", location="Beijing",
        accommodation={"name": "Old Hotel"},
    )
    existing = {"days": [d1]}
    update_day = _make_day_entry(1, accommodation={"name": "New Hotel"})
    update = {"days": [update_day]}

    result = merge_agent_slots(existing, update, "accommodation")
    got = result["days"][0]
    assert got["accommodation"] == {"name": "New Hotel"}
    assert got["date"] == "2026-05-08"
    assert got["location"] == "Beijing"


def test_untouched_days_are_preserved():
    """Days not referenced by update must pass through unchanged."""
    existing = {"days": [
        _make_day_entry(1, dinner={"name": "A"}),
        _make_day_entry(2, dinner={"name": "B"}),
        _make_day_entry(3, dinner={"name": "C"}),
    ]}
    update = {"days": [_make_day_entry(2, dinner={"name": "B-UPDATED"})]}

    result = merge_agent_slots(existing, update, "meals")
    by_day = {d["day"]: d for d in result["days"]}
    assert by_day[1]["dinner"] == {"name": "A"}
    assert by_day[2]["dinner"] == {"name": "B-UPDATED"}
    assert by_day[3]["dinner"] == {"name": "C"}


# ---------- array-based agents (attractions, entertainment, shopping, cafe) ----------

def test_attractions_array_replacement_preserves_day_metadata():
    """AC7: updating `attractions` replaces the array but keeps `date`/`location`."""
    orig_attr = [{"name": "A1"}, {"name": "A2"}, {"name": "A3"}, {"name": "A4"}]
    d3 = _make_day_entry(
        3, date="2026-05-10", location="Beijing", attractions=orig_attr,
    )
    existing = {"days": [d3]}
    new_attr = [{"name": "NEW1"}, {"name": "NEW2"}]
    update = {"days": [_make_day_entry(3, attractions=new_attr)]}

    result = merge_agent_slots(existing, update, "attractions")
    got = result["days"][0]
    assert got["attractions"] == new_attr, "array not replaced"
    assert got["date"] == "2026-05-10", "date metadata lost"
    assert got["location"] == "Beijing", "location metadata lost"


def test_array_agent_without_array_key_preserves_existing_array():
    """If update day has no `cafe` key, existing cafe array survives."""
    d4 = _make_day_entry(
        4, location="Xian", cafe=[{"name": "OldCafe"}], other_meta="keep-me",
    )
    existing = {"days": [d4]}
    update = {"days": [_make_day_entry(4, location="Xian-Updated")]}

    result = merge_agent_slots(existing, update, "cafe")
    got = result["days"][0]
    assert got["cafe"] == [{"name": "OldCafe"}], "existing cafe array wiped"
    assert got["location"] == "Xian-Updated"
    assert got["other_meta"] == "keep-me"


# ---------- edge cases ----------

def test_new_day_inserted_when_absent_in_existing():
    """If update introduces a day not in existing, it is inserted."""
    existing = {"days": [_make_day_entry(1, breakfast={"name": "A"})]}
    update = {"days": [_make_day_entry(2, lunch={"name": "L"})]}

    result = merge_agent_slots(existing, update, "meals")
    by_day = {d["day"]: d for d in result["days"]}
    assert 1 in by_day and 2 in by_day
    assert by_day[2]["lunch"] == {"name": "L"}


def test_missing_day_number_raises():
    """Update day without `day` key must raise ValueError."""
    existing = {"days": [{"day": 1}]}
    update = {"days": [{"breakfast": {"name": "x"}}]}
    try:
        merge_agent_slots(existing, update, "meals")
    except ValueError:
        return
    raise AssertionError("Expected ValueError for day entry missing 'day' field")


def test_auto_merge_without_flags():
    """Verify slot-level merge works as the default (no flag needed).

    After the simplification refactor, merge_agent_slots() is the sole merge
    path and is invoked automatically when the target file exists. This test
    validates the function directly: partial dinner update preserves sibling
    slots, matching the behavior that save.py triggers without any flag.
    """
    existing = {"days": [_make_day_entry(2, breakfast={"name": "X"}, lunch={"name": "Y"})]}
    update = {"days": [_make_day_entry(2, dinner={"name": "D"})]}

    result = merge_agent_slots(existing, update, "meals")
    got = result["days"][0]
    assert got["breakfast"] == {"name": "X"}, "breakfast should be preserved (auto-merge)"
    assert got["lunch"] == {"name": "Y"}, "lunch should be preserved (auto-merge)"
    assert got["dinner"] == {"name": "D"}, "dinner should be updated"


# ---------- minimal test harness (lets the file run standalone) ----------

TESTS = [
    test_meals_partial_dinner_preserves_breakfast_and_lunch,
    test_accommodation_partial_update_preserves_metadata,
    test_untouched_days_are_preserved,
    test_attractions_array_replacement_preserves_day_metadata,
    test_array_agent_without_array_key_preserves_existing_array,
    test_new_day_inserted_when_absent_in_existing,
    test_missing_day_number_raises,
    test_auto_merge_without_flags,
]


def _run_one(fn):
    """Execute a single test; return (passed: bool, message: str)."""
    try:
        fn()
        return True, ""
    except AssertionError as exc:
        return False, f"FAIL: {exc}"
    except Exception as exc:
        return False, f"ERROR: {exc!r}"


def _run_all():
    failed = []
    for fn in TESTS:
        ok, msg = _run_one(fn)
        tag = "PASS " if ok else "FAIL "
        print(f"  {tag} {fn.__name__}{' — ' + msg if msg else ''}")
        if not ok:
            failed.append(fn.__name__)
    print()
    if failed:
        print(f"{len(failed)} test(s) failed: {failed}")
        return 1
    print(f"All {len(TESTS)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run_all())
