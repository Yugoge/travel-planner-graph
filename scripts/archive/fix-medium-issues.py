#!/usr/bin/env python3
"""
Fix all 23 MEDIUM severity issues across both trips.

Issues addressed:
  1. Cross-agent location mismatches (21 issues) - standardize location strings
  2. Accommodation currency error (1 issue) - Day 13 bucket-list CNY -> HKD
  3. Timeline overlap (1 issue) - Day 12 bucket-list Victoria Peak end_time 20:30 -> 19:50

Usage: fix-medium-issues.py <data_root>
  data_root: path containing trip subdirectories
"""

import json
import os
import sys


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def get_days(data):
    """Navigate to the days array in data.days."""
    d = data.get("data", data)
    if isinstance(d, dict):
        return d.get("days", [])
    return []


def fix_location(days, day_num, standard_location):
    """Set location field for a specific day. Returns True if changed or added."""
    for day in days:
        if day.get("day") == day_num:
            old = day.get("location", None)
            if old != standard_location:
                day["location"] = standard_location
                return True, old
    return False, None


def fix_cross_agent_locations(trip_dir, location_map, agent_files):
    """Standardize location across all agent files for given days."""
    changes = []
    for af in agent_files:
        filepath = os.path.join(trip_dir, af)
        if not os.path.exists(filepath):
            continue
        data = load_json(filepath)
        days = get_days(data)
        modified = False
        for day_num, standard_location in location_map.items():
            changed, old_val = fix_location(days, day_num, standard_location)
            if changed:
                modified = True
                action = "updated" if old_val is not None else "added"
                changes.append(
                    f"  {af} day {day_num}: {action} location "
                    f"'{old_val}' -> '{standard_location}'"
                )
        if modified:
            save_json(filepath, data)
    return changes


def fix_accommodation_currency(trip_dir):
    """Fix Day 13 accommodation currency_local from CNY to HKD."""
    filepath = os.path.join(trip_dir, "accommodation.json")
    data = load_json(filepath)
    days = get_days(data)
    for day in days:
        if day.get("day") == 13:
            acc = day.get("accommodation", {})
            old_currency = acc.get("currency_local", "")
            if old_currency == "CNY":
                acc["currency_local"] = "HKD"
                save_json(filepath, data)
                return f"  accommodation.json day 13: currency_local '{old_currency}' -> 'HKD'"
            elif old_currency == "HKD":
                return "  accommodation.json day 13: already HKD (no change needed)"
    return "  accommodation.json day 13: day not found or no accommodation key"


def fix_timeline_overlap(trip_dir):
    """Fix Day 12 Victoria Peak end_time from 20:30 to 19:50 and update duration."""
    filepath = os.path.join(trip_dir, "timeline.json")
    data = load_json(filepath)
    days = get_days(data)
    changes = []
    for day in days:
        if day.get("day") == 12:
            timeline = day.get("timeline", {})
            # Find the Victoria Peak entry
            for event_name, event_data in timeline.items():
                if "Victoria Peak" in event_name or "太平山" in event_name:
                    old_end = event_data.get("end_time", "")
                    old_duration = event_data.get("duration_minutes", 0)
                    if old_end == "20:30":
                        event_data["end_time"] = "19:50"
                        # start_time is 18:00, new end is 19:50 = 110 minutes
                        start = event_data.get("start_time", "18:00")
                        sh, sm = map(int, start.split(":"))
                        new_duration = (19 * 60 + 50) - (sh * 60 + sm)
                        event_data["duration_minutes"] = new_duration
                        changes.append(
                            f"  timeline.json day 12 '{event_name}': "
                            f"end_time '{old_end}' -> '19:50', "
                            f"duration {old_duration} -> {new_duration}"
                        )
                    elif old_end == "19:50":
                        changes.append(
                            f"  timeline.json day 12 '{event_name}': already 19:50"
                        )
                    else:
                        changes.append(
                            f"  timeline.json day 12 '{event_name}': "
                            f"unexpected end_time '{old_end}'"
                        )
                    break
            break
    if changes:
        save_json(filepath, data)
    return changes


def main():
    data_root = sys.argv[1] if len(sys.argv) > 1 else "/root/travel-planner/data"

    agent_files = [
        "meals.json",
        "attractions.json",
        "entertainment.json",
        "accommodation.json",
        "shopping.json",
        "budget.json",
        "timeline.json",
        "transportation.json",
    ]

    all_changes = []

    # --- Itinerary trip ---
    itinerary_dir = os.path.join(
        data_root, "china-feb-15-mar-7-2026-20260202-195429"
    )
    itinerary_locations = {
        3: "Bazhong / Chengdu",
        4: "Chengdu / Shanghai",
        8: "Shanghai / Beijing",
        16: "Beijing",
    }

    print("=== Itinerary Trip: Cross-Agent Location Fixes ===")
    changes = fix_cross_agent_locations(itinerary_dir, itinerary_locations, agent_files)
    all_changes.extend(changes)
    for c in changes:
        print(c)
    if not changes:
        print("  No changes needed")

    # --- Bucket-list trip ---
    bucket_dir = os.path.join(
        data_root, "beijing-exchange-bucket-list-20260202-232405"
    )
    bucket_locations = {
        8: "Guilin / Yangshuo",
        12: "Shenzhen / Hong Kong",
        13: "Hong Kong / Macau",
    }

    print("\n=== Bucket-List Trip: Cross-Agent Location Fixes ===")
    changes = fix_cross_agent_locations(bucket_dir, bucket_locations, agent_files)
    all_changes.extend(changes)
    for c in changes:
        print(c)
    if not changes:
        print("  No changes needed")

    # --- Accommodation currency fix ---
    print("\n=== Bucket-List Trip: Accommodation Currency Fix ===")
    result = fix_accommodation_currency(bucket_dir)
    print(result)
    all_changes.append(result)

    # --- Timeline overlap fix ---
    print("\n=== Bucket-List Trip: Timeline Overlap Fix ===")
    results = fix_timeline_overlap(bucket_dir)
    all_changes.extend(results)
    for r in results:
        print(r)
    if not results:
        print("  No changes needed")

    print(f"\n=== Summary: {len(all_changes)} changes applied ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
