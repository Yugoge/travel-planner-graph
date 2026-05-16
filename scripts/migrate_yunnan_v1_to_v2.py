#!/usr/bin/env python3
"""
migrate_yunnan_v1_to_v2.py

Migrates beijing-lijiang-dali-20260418-100846 trip data from v1 agent JSON
format to v2 per-day schema.

Input files (read-only, never modified):
  data/{TRIP_ID}/meals.json
  data/{TRIP_ID}/accommodation.json
  data/{TRIP_ID}/attractions.json
  data/{TRIP_ID}/entertainment.json

Output files (new):
  data/{TRIP_ID}/meta.json
  data/{TRIP_ID}/days/day-01.json  ...  days/day-09.json
"""

import json
import pathlib
import sys

# ---------------------------------------------------------------------------
# Constants / configuration
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TRIP_ID   = "beijing-lijiang-dali-20260418-100846"
DATA_DIR  = REPO_ROOT / "data" / TRIP_ID
DAYS_DIR  = DATA_DIR / "days"

# Day-level configuration (from spec)
DAY_CONFIG = {
    1: {
        "date": "2026-06-20",
        "city_id": "kunming",
        "city_name": "Kunming",
        "leg_index": 0,
        "day_type": "arrival",
        "arrival_ts": "2026-06-20T18:50:00+08:00",
        "departure_ts": None,
    },
    2: {
        "date": "2026-06-21",
        "city_id": "kunming",
        "city_name": "Kunming",
        "leg_index": 0,
        "day_type": "normal",
        "arrival_ts": None,
        "departure_ts": None,
    },
    3: {
        "date": "2026-06-22",
        "city_id": "lijiang",
        "city_name": "Lijiang",
        "leg_index": 1,
        "day_type": "city-change",
        "arrival_ts": "2026-06-22T12:22:00+08:00",
        "departure_ts": "2026-06-22T09:14:00+08:00",
    },
    4: {
        "date": "2026-06-23",
        "city_id": "lijiang",
        "city_name": "Lijiang",
        "leg_index": 1,
        "day_type": "normal",
        "arrival_ts": None,
        "departure_ts": None,
    },
    5: {
        "date": "2026-06-24",
        "city_id": "dali",
        "city_name": "Dali",
        "leg_index": 2,
        "day_type": "city-change",
        "arrival_ts": "2026-06-24T12:00:00+08:00",
        "departure_ts": "2026-06-24T09:00:00+08:00",
    },
    6: {
        "date": "2026-06-25",
        "city_id": "dali",
        "city_name": "Dali",
        "leg_index": 2,
        "day_type": "normal",
        "arrival_ts": None,
        "departure_ts": None,
    },
    7: {
        "date": "2026-06-26",
        "city_id": "kunming",
        "city_name": "Kunming",
        "leg_index": 3,
        "day_type": "city-change",
        "arrival_ts": "2026-06-26T17:23:00+08:00",
        "departure_ts": "2026-06-26T15:24:00+08:00",
    },
    8: {
        "date": "2026-06-27",
        "city_id": "beijing",
        "city_name": "Beijing",
        "leg_index": 4,
        "day_type": "city-change",
        "arrival_ts": "2026-06-27T15:15:00+08:00",
        "departure_ts": "2026-06-27T11:35:00+08:00",
    },
    9: {
        "date": "2026-06-28",
        "city_id": "beijing",
        "city_name": "Beijing",
        "leg_index": 4,
        "day_type": "departure",
        "arrival_ts": None,
        "departure_ts": "2026-06-28T13:30:00+08:00",
    },
}

# fit_score defaults by source_agent
FIT_SCORES = {
    "meals": 0.85,
    "accommodation": 0.90,
    "attractions": 0.80,
    "entertainment": 0.78,
}

# city_context.role derived from day_type
ROLE_MAP = {
    "arrival": "destination",
    "departure": "origin",
    "city-change": "destination",
    "normal": "overnight",
}

DAY_9_WARNING = (
    "Day 9: M.B Mexican lunch at 11:30 conflicts with CA933 departure "
    "13:30 from PEK — confirm timeline before committing"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: pathlib.Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"  Written: {path.relative_to(REPO_ROOT)}")


def why_fits_user(item: dict) -> str:
    """
    Extract first sentence of notes_base, max 120 chars.
    Falls back to note_base (entertainment uses that field name).
    """
    raw = item.get("notes_base") or item.get("note_base") or ""
    raw = raw.strip()
    if not raw:
        return "Verified authentic local recommendation."
    # Split on first period followed by space or end-of-string
    for sep in (". ", ".\n", "。"):
        idx = raw.find(sep)
        if idx != -1:
            sentence = raw[: idx + 1].strip()
            return sentence[:120] if len(sentence) > 120 else sentence
    return raw[:120]


def city_context(cfg: dict) -> dict:
    return {
        "city_id": cfg["city_id"],
        "city_name": cfg["city_name"],
        "leg_index": cfg["leg_index"],
        "role": ROLE_MAP[cfg["day_type"]],
    }


def make_option(slot_id: str, day_num: int, option_index: int,
                item: dict, source_agent: str, cfg: dict) -> dict:
    """Build a v2 option object from a v1 item dict."""
    opt_id = f"{slot_id}-{day_num}-{option_index}"
    return {
        "option_id": opt_id,
        "name": item.get("name_base", ""),
        "name_local": item.get("name_local", ""),
        "location_summary": item.get("location_base") or item.get("location_local", ""),
        "cost": float(item.get("cost", 0) or 0),
        "fit_score": FIT_SCORES[source_agent],
        "why_fits_user": why_fits_user(item),
        "source_agent": source_agent,
        "city_context": city_context(cfg),
        # pass-through v1 fields (schema allows additionalProperties)
        **{k: v for k, v in item.items()
           if k not in {"name_base", "name_local", "location_base",
                        "cost", "notes_base", "note_base"}},
    }


def skipped_slot(slot_id: str, reason: str) -> dict:
    return {
        "slot_id": slot_id,
        "options": [],
        "selected_option_id": None,
        "skipped": True,
        "skipped_reason": reason,
    }


def meal_slot(slot_id: str, day_num: int, meal_dict, cfg: dict,
              skip_reason: str = None) -> dict:
    """
    meal_dict: the v1 meal sub-object, e.g. {"primary": {...}, "alternatives": [...]}
    or None/empty.
    """
    # If no meal data or no 'primary' key, apply skip
    if not meal_dict or "primary" not in meal_dict:
        reason = skip_reason or "user-omit"
        return skipped_slot(slot_id, reason)

    options = []
    primary = meal_dict["primary"]
    options.append(make_option(slot_id, day_num, 1, primary, "meals", cfg))

    for i, alt in enumerate(meal_dict.get("alternatives", []), start=2):
        options.append(make_option(slot_id, day_num, i, alt, "meals", cfg))

    return {
        "slot_id": slot_id,
        "options": options,
        "selected_option_id": options[0]["option_id"] if options else None,
        "skipped": False,
        "skipped_reason": None,
    }


def attraction_slot(slot_id: str, day_num: int,
                    attractions: list, idx: int, cfg: dict,
                    skip_reason: str = None) -> dict:
    """
    Build morning_activity or afternoon_activity from attractions[idx].
    If skip_reason is provided, slot is always skipped with that reason.
    If attraction at idx doesn't exist, skip with "user-omit".
    """
    if skip_reason is not None:
        return skipped_slot(slot_id, skip_reason)

    if idx >= len(attractions) or attractions[idx] is None:
        return skipped_slot(slot_id, "user-omit")

    item = attractions[idx]
    options = [make_option(slot_id, day_num, 1, item, "attractions", cfg)]
    return {
        "slot_id": slot_id,
        "options": options,
        "selected_option_id": options[0]["option_id"],
        "skipped": False,
        "skipped_reason": None,
    }


def entertainment_slot(slot_id: str, day_num: int,
                       ent_list: list, cfg: dict,
                       skip_reason: str = None) -> dict:
    """
    All entertainment items become options.
    """
    if skip_reason is not None:
        return skipped_slot(slot_id, skip_reason)

    if not ent_list:
        return skipped_slot(slot_id, "user-omit")

    options = []
    for i, item in enumerate(ent_list, start=1):
        options.append(make_option(slot_id, day_num, i, item, "entertainment", cfg))

    return {
        "slot_id": slot_id,
        "options": options,
        "selected_option_id": options[0]["option_id"],
        "skipped": False,
        "skipped_reason": None,
    }


def accommodation_slot(day_num: int, acc_dict, cfg: dict,
                       skip_reason: str = None) -> dict:
    """
    v1 accommodation is a flat dict (single object, no primary/alternatives).
    """
    slot_id = "accommodation"

    if skip_reason is not None:
        return skipped_slot(slot_id, skip_reason)

    if not acc_dict:
        return skipped_slot(slot_id, "user-omit")

    option = make_option(slot_id, day_num, 1, acc_dict, "accommodation", cfg)
    return {
        "slot_id": slot_id,
        "options": [option],
        "selected_option_id": option["option_id"],
        "skipped": False,
        "skipped_reason": None,
    }


# ---------------------------------------------------------------------------
# Main migration logic
# ---------------------------------------------------------------------------

def build_meta() -> dict:
    return {
        "schema_version": "v2.0",
        "trip_id": TRIP_ID,
        "title": "Beijing · Lijiang · Dali",
        "title_local": "北京·丽江·大理",
        "currency_local": "CNY",
        "user_budget": 20000,
        "day_count": 9,
        "start_date": "2026-06-20",
        "end_date": "2026-06-28",
        "legs": [
            {"leg_index": 0, "city_id": "kunming",  "city_name": "Kunming",  "first_day": 1, "last_day": 2},
            {"leg_index": 1, "city_id": "lijiang",  "city_name": "Lijiang",  "first_day": 3, "last_day": 4},
            {"leg_index": 2, "city_id": "dali",     "city_name": "Dali",     "first_day": 5, "last_day": 6},
            {"leg_index": 3, "city_id": "kunming",  "city_name": "Kunming",  "first_day": 7, "last_day": 7},
            {"leg_index": 4, "city_id": "beijing",  "city_name": "Beijing",  "first_day": 8, "last_day": 9},
        ],
        "travelers": ["Yuge", "Jade"],
        "last_saved_ts": "2026-05-16T00:00:00+08:00",
        "current_editor_session": None,
        "auto_mode_used": False,
    }


def build_day(day_num: int, meals_by_day: dict, acc_by_day: dict,
              attr_by_day: dict, ent_by_day: dict) -> dict:
    cfg = DAY_CONFIG[day_num]
    day_type = cfg["day_type"]

    # Retrieve v1 data for this day (keyed by day number)
    meals_day  = meals_by_day.get(day_num, {})
    acc_day    = acc_by_day.get(day_num)
    attr_list  = attr_by_day.get(day_num, [])
    ent_list   = ent_by_day.get(day_num, [])

    # ------------------------------------------------------------------
    # Breakfast
    # ------------------------------------------------------------------
    if day_num == 1:
        bkf_skip = "pre-arrival"
    elif day_num == 9:
        bkf_skip = "post-departure"
    else:
        bkf_skip = None

    if bkf_skip:
        breakfast = skipped_slot("breakfast", bkf_skip)
    else:
        breakfast = meal_slot("breakfast", day_num, meals_day.get("breakfast"), cfg)

    # ------------------------------------------------------------------
    # Lunch
    # ------------------------------------------------------------------
    if day_num == 9:
        lun_skip = None   # include if exists (day 9 has lunch data)
    elif day_num == 1:
        lun_skip = "pre-arrival"
    else:
        lun_skip = None

    if lun_skip:
        lunch = skipped_slot("lunch", lun_skip)
    elif day_num == 8:
        # In-flight 11:35-15:15 — include data but note in-transit context
        lunch = meal_slot("lunch", day_num, meals_day.get("lunch"), cfg,
                          skip_reason="in-transit" if not meals_day.get("lunch") else None)
    else:
        lunch = meal_slot("lunch", day_num, meals_day.get("lunch"), cfg)

    # ------------------------------------------------------------------
    # Dinner
    # ------------------------------------------------------------------
    dinner_warnings = []
    if day_num == 9:
        dinner = meal_slot("dinner", day_num, meals_day.get("dinner"), cfg)
        if not dinner["skipped"]:
            dinner_warnings.append(DAY_9_WARNING)
    else:
        dinner = meal_slot("dinner", day_num, meals_day.get("dinner"), cfg)

    # ------------------------------------------------------------------
    # Morning activity
    # ------------------------------------------------------------------
    if day_num == 1:
        morn = skipped_slot("morning_activity", "pre-arrival")
    elif day_num == 3:
        morn = skipped_slot("morning_activity", "city-change")  # train departs 09:14
    elif day_num == 7:
        # Day 7: use attractions[0] if present (Xizhou — morning before train at 15:24)
        morn = attraction_slot("morning_activity", day_num, attr_list, 0, cfg)
    elif day_num == 8:
        morn = skipped_slot("morning_activity", "city-change")
    elif day_num == 9:
        morn = skipped_slot("morning_activity", "post-departure")
    else:
        morn = attraction_slot("morning_activity", day_num, attr_list, 0, cfg)

    # ------------------------------------------------------------------
    # Afternoon activity
    # ------------------------------------------------------------------
    if day_num == 1:
        aft = skipped_slot("afternoon_activity", "pre-arrival")
    elif day_num == 3:
        aft = skipped_slot("afternoon_activity", "city-change")
    elif day_num == 7:
        aft = skipped_slot("afternoon_activity", "in-transit")  # C90 train 15:24-17:23
    elif day_num == 8:
        aft = skipped_slot("afternoon_activity", "city-change")
    elif day_num == 9:
        aft = skipped_slot("afternoon_activity", "post-departure")
    else:
        # Use attractions[1]; if no second attraction but first exists → user-omit
        aft = attraction_slot("afternoon_activity", day_num, attr_list, 1, cfg)

    # ------------------------------------------------------------------
    # Evening activity
    # ------------------------------------------------------------------
    if day_num == 1:
        eve = skipped_slot("evening_activity", "pre-arrival")
    elif day_num == 8:
        eve = skipped_slot("evening_activity", "user-omit")  # arrival day, early night
    elif day_num == 9:
        eve = skipped_slot("evening_activity", "post-departure")
    else:
        eve = entertainment_slot("evening_activity", day_num, ent_list, cfg)

    # ------------------------------------------------------------------
    # Accommodation
    # ------------------------------------------------------------------
    if day_num == 9:
        acc = skipped_slot("accommodation", "post-departure")
    else:
        acc = accommodation_slot(day_num, acc_day, cfg)

    # ------------------------------------------------------------------
    # Day-level warnings
    # ------------------------------------------------------------------
    warnings = []
    if day_num == 9:
        warnings.append(DAY_9_WARNING)

    # Compose day document
    day_doc = {
        "schema_version": "v2.0",
        "day": day_num,
        "date": cfg["date"],
        "city_id": cfg["city_id"],
        "city_name": cfg["city_name"],
        "leg_index": cfg["leg_index"],
        "day_type": day_type,
        "stage": "user-selected",
        "arrival_ts": cfg["arrival_ts"],
        "departure_ts": cfg["departure_ts"],
        "slots": {
            "breakfast":          breakfast,
            "morning_activity":   morn,
            "lunch":              lunch,
            "afternoon_activity": aft,
            "dinner":             dinner,
            "evening_activity":   eve,
        },
        "accommodation": acc,
        "intra_city_routes": {},
        "warnings": warnings,
    }
    return day_doc


# ---------------------------------------------------------------------------
# Index v1 data by day number
# ---------------------------------------------------------------------------

def index_by_day(days_list: list, key: str = None) -> dict:
    """
    If key is None, returns {day_num: day_dict}.
    If key is provided, returns {day_num: day_dict[key]}.
    """
    result = {}
    for d in days_list:
        day_num = d["day"]
        if key is None:
            result[day_num] = d
        else:
            result[day_num] = d.get(key)
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print(f"Loading v1 data from {DATA_DIR}")

    meals_raw   = load_json(DATA_DIR / "meals.json")
    acc_raw     = load_json(DATA_DIR / "accommodation.json")
    attr_raw    = load_json(DATA_DIR / "attractions.json")
    ent_raw     = load_json(DATA_DIR / "entertainment.json")

    # Index by day number
    meals_by_day = {}
    for d in meals_raw["data"]["days"]:
        meals_by_day[d["day"]] = d   # keys: breakfast, lunch, dinner

    acc_by_day  = index_by_day(acc_raw["data"]["days"],  key="accommodation")
    attr_by_day = index_by_day(attr_raw["data"]["days"], key="attractions")
    ent_by_day  = index_by_day(ent_raw["data"]["days"],  key="entertainment")

    # Create output dirs
    DAYS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {DAYS_DIR.relative_to(REPO_ROOT)}")

    # Write meta.json
    meta = build_meta()
    save_json(DATA_DIR / "meta.json", meta)

    # Write day files
    skipped_summary = []
    for day_num in range(1, 10):
        day_doc = build_day(day_num, meals_by_day, acc_by_day, attr_by_day, ent_by_day)
        filename = f"day-{day_num:02d}.json"
        save_json(DAYS_DIR / filename, day_doc)

        # Collect skipped slots for report
        for slot_id, slot in day_doc["slots"].items():
            if slot["skipped"]:
                skipped_summary.append(
                    f"  day {day_num} / {slot_id}: {slot['skipped_reason']}"
                )
        if day_doc["accommodation"]["skipped"]:
            skipped_summary.append(
                f"  day {day_num} / accommodation: {day_doc['accommodation']['skipped_reason']}"
            )

    # Summary report
    print()
    print("=" * 60)
    print("Migration complete")
    print(f"  meta.json : 1 file")
    print(f"  day files : 9 files (day-01.json ... day-09.json)")
    print()
    print("Skipped slots:")
    for line in skipped_summary:
        print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
