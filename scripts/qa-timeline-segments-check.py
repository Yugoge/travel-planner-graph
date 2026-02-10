#!/usr/bin/env python3
"""Quick check on timeline travel_segments for name_base/name_local compliance."""
import json
import os

BASE_DIR = "/root/travel-planner"
TRIP_DIRS = {
    "itinerary": os.path.join(BASE_DIR, "data", "china-feb-15-mar-7-2026-20260202-195429"),
    "bucket-list": os.path.join(BASE_DIR, "data", "beijing-exchange-bucket-list-20260202-232405"),
}

for trip_name, trip_dir in TRIP_DIRS.items():
    filepath = os.path.join(trip_dir, "timeline.json")
    data = json.load(open(filepath, "r", encoding="utf-8"))
    total_segs = 0
    missing_name_base = 0
    missing_name_local = 0
    missing_type_base = 0
    missing_type_local = 0
    missing_icon = 0
    missing_start = 0
    missing_end = 0

    for day in data.get("data", {}).get("days", []):
        day_num = day.get("day", "?")
        for seg in day.get("travel_segments", []):
            total_segs += 1
            if not seg.get("name_base"):
                missing_name_base += 1
                print(f"  [{trip_name}] Day {day_num}: segment missing name_base -> keys: {list(seg.keys())}")
            if not seg.get("name_local"):
                missing_name_local += 1
            if not seg.get("type_base"):
                missing_type_base += 1
            if not seg.get("type_local"):
                missing_type_local += 1
            if not seg.get("icon"):
                missing_icon += 1
            if not seg.get("start_time"):
                missing_start += 1
            if not seg.get("end_time"):
                missing_end += 1

    print(f"\n[{trip_name}] Travel segments: {total_segs} total")
    print(f"  missing name_base:  {missing_name_base}")
    print(f"  missing name_local: {missing_name_local}")
    print(f"  missing type_base:  {missing_type_base}")
    print(f"  missing type_local: {missing_type_local}")
    print(f"  missing icon:       {missing_icon}")
    print(f"  missing start_time: {missing_start}")
    print(f"  missing end_time:   {missing_end}")
