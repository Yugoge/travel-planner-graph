#!/usr/bin/env python3
"""
Rename legacy field names to schema-compliant names across travel data JSON files.

Handles the structural differences between file types:
- meals.json: items nested under day.breakfast, day.lunch, day.dinner
- attractions/entertainment/shopping: items in day.<agent_name> list
- accommodation: single item in day.accommodation dict
- timeline: travel_segments[] entries in each day
- transportation: location_change object in each day

Rules:
- NEVER overwrite existing schema-compliant fields
- KEEP old fields for backward compatibility (copy, not move)
- Process ALL items in ALL days for ALL files
"""

import json
import sys
from pathlib import Path


def safe_rename(obj: dict, old_key: str, new_key: str) -> int:
    """Copy old_key to new_key if old exists and new does not. Returns 1 if renamed, 0 otherwise."""
    if old_key in obj and new_key not in obj:
        obj[new_key] = obj[old_key]
        return 1
    return 0


def process_poi_item(item: dict, agent: str) -> int:
    """Apply rename rules to a single POI item. Returns count of renames."""
    count = 0
    # Common to all POI agents
    count += safe_rename(item, "currency", "currency_local")
    count += safe_rename(item, "notes", "notes_base")

    # Agent-specific renames
    if agent == "meals":
        count += safe_rename(item, "cuisine", "cuisine_base")
    elif agent in ("attractions", "entertainment", "shopping"):
        count += safe_rename(item, "type", "type_base")
    elif agent == "accommodation":
        count += safe_rename(item, "type", "type_base")
        count += safe_rename(item, "amenities", "amenities_base")

    return count


def process_meals(data: dict) -> int:
    """Process meals.json: items are day.breakfast, day.lunch, day.dinner."""
    count = 0
    for day in data.get("data", {}).get("days", []):
        for slot in ("breakfast", "lunch", "dinner", "snack", "supper"):
            meal = day.get(slot)
            if isinstance(meal, dict):
                count += process_poi_item(meal, "meals")
    return count


def process_poi_list(data: dict, agent: str) -> int:
    """Process attractions/entertainment/shopping: items in day.<agent> list."""
    count = 0
    for day in data.get("data", {}).get("days", []):
        items = day.get(agent)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    count += process_poi_item(item, agent)
    return count


def process_accommodation(data: dict) -> int:
    """Process accommodation.json: single dict at day.accommodation."""
    count = 0
    for day in data.get("data", {}).get("days", []):
        acc = day.get("accommodation")
        if isinstance(acc, dict):
            count += process_poi_item(acc, "accommodation")
    return count


def process_timeline(data: dict) -> int:
    """Process timeline.json: rename mode -> type_base in travel_segments[]."""
    count = 0
    for day in data.get("data", {}).get("days", []):
        segments = day.get("travel_segments", [])
        if isinstance(segments, list):
            for seg in segments:
                if isinstance(seg, dict):
                    count += safe_rename(seg, "mode", "type_base")
    return count


def process_transportation(data: dict) -> int:
    """Process transportation.json: rename notes -> notes_base in location_change objects."""
    count = 0
    for day in data.get("data", {}).get("days", []):
        lc = day.get("location_change")
        if isinstance(lc, dict):
            count += safe_rename(lc, "notes", "notes_base")
    return count


def process_file(filepath: Path) -> int:
    """Load, process, write, and validate a single JSON file. Returns rename count."""
    agent = filepath.stem  # e.g., "meals", "attractions", etc.

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dispatch to the correct processor
    processors = {
        "meals": process_meals,
        "attractions": lambda d: process_poi_list(d, "attractions"),
        "entertainment": lambda d: process_poi_list(d, "entertainment"),
        "shopping": lambda d: process_poi_list(d, "shopping"),
        "accommodation": process_accommodation,
        "timeline": process_timeline,
        "transportation": process_transportation,
    }

    processor = processors.get(agent)
    if processor is None:
        return -1  # Not a file we process

    rename_count = processor(data)

    # Write back with consistent formatting
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Validate: re-read and parse to confirm valid JSON
    with open(filepath, "r", encoding="utf-8") as f:
        json.load(f)

    return rename_count


def main():
    trip_dirs = [
        Path("/root/travel-planner/data/china-feb-15-mar-7-2026-20260202-195429"),
        Path("/root/travel-planner/data/beijing-exchange-bucket-list-20260202-232405"),
    ]

    target_files = [
        "meals.json",
        "attractions.json",
        "entertainment.json",
        "accommodation.json",
        "shopping.json",
        "transportation.json",
        "timeline.json",
    ]

    total_renames = 0
    total_files = 0
    errors = []

    print("=" * 70)
    print("LEGACY FIELD RENAME REPORT")
    print("=" * 70)

    for trip_dir in trip_dirs:
        trip_name = trip_dir.name
        print(f"\n--- Trip: {trip_name} ---")

        for filename in target_files:
            filepath = trip_dir / filename
            if not filepath.exists():
                print(f"  SKIP  {filename:25s}  (file not found)")
                continue

            try:
                count = process_file(filepath)
                if count < 0:
                    print(f"  SKIP  {filename:25s}  (not a target file)")
                    continue

                total_renames += count
                total_files += 1
                status = f"{count} renames" if count > 0 else "no changes needed"
                print(f"  OK    {filename:25s}  {status}")

            except Exception as e:
                errors.append((filepath, str(e)))
                print(f"  ERROR {filename:25s}  {e}")

    print()
    print("=" * 70)
    print(f"SUMMARY: {total_files} files processed, {total_renames} total renames")
    if errors:
        print(f"ERRORS: {len(errors)} files had errors:")
        for path, err in errors:
            print(f"  - {path}: {err}")
        sys.exit(1)
    else:
        print("VALIDATION: All files re-read successfully as valid JSON")
    print("=" * 70)


if __name__ == "__main__":
    main()
