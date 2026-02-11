#!/usr/bin/env python3
"""Remove redundant legacy field names from travel planner JSON data files.

Processes all JSON data files in trip directories and removes legacy field names
wherever the schema-compliant field already exists with the same value.

Rules:
  1. If both legacy and schema fields exist with identical values: delete legacy field.
  2. If only the legacy field exists (no schema version): rename it to the schema name.
  3. If both exist with different values: leave both and print a WARNING.
"""

import json
import sys
from pathlib import Path
from typing import Any


# Legacy -> Schema field mapping, keyed by file type
# Each entry: (legacy_name, schema_name)
FIELD_MAP_BY_FILE = {
    "meals": [
        ("currency", "currency_local"),
        ("cuisine", "cuisine_base"),
        ("notes", "notes_base"),
    ],
    "attractions": [
        ("currency", "currency_local"),
        ("type", "type_base"),
        ("notes", "notes_base"),
    ],
    "entertainment": [
        ("currency", "currency_local"),
        ("type", "type_base"),
        ("notes", "notes_base"),
    ],
    "accommodation": [
        ("currency", "currency_local"),
        ("type", "type_base"),
        ("amenities", "amenities_base"),
        ("notes", "notes_base"),
    ],
    "shopping": [
        ("currency", "currency_local"),
        ("type", "type_base"),
        ("notes", "notes_base"),
    ],
    "transportation": [
        ("currency", "currency_local"),
        ("from", "from_base"),
        ("to", "to_base"),
        ("notes", "notes_base"),
    ],
    "timeline": [
        ("mode", "type_base"),
    ],
}

# How to extract items from each file type
# Each extractor yields (item_dict, description_for_logging) tuples
ITEM_EXTRACTORS = {
    "meals": "meal_items",
    "attractions": "array_items",
    "entertainment": "array_items",
    "shopping": "array_items",
    "accommodation": "accommodation_items",
    "transportation": "transportation_items",
    "timeline": "timeline_items",
}


def meal_items(data: dict, agent: str):
    """Extract meal items: days[].breakfast, days[].lunch, days[].dinner."""
    for day_obj in data.get("data", {}).get("days", []):
        day_num = day_obj.get("day", "?")
        for meal_type in ("breakfast", "lunch", "dinner"):
            item = day_obj.get(meal_type)
            if item and isinstance(item, dict):
                yield item, f"day {day_num} {meal_type}"


def array_items(data: dict, agent: str):
    """Extract array items: days[].{agent}[]."""
    for day_obj in data.get("data", {}).get("days", []):
        day_num = day_obj.get("day", "?")
        items = day_obj.get(agent, [])
        if isinstance(items, list):
            for idx, item in enumerate(items):
                if isinstance(item, dict):
                    yield item, f"day {day_num} {agent}[{idx}]"


def accommodation_items(data: dict, agent: str):
    """Extract accommodation items: days[].accommodation (singular)."""
    for day_obj in data.get("data", {}).get("days", []):
        day_num = day_obj.get("day", "?")
        item = day_obj.get("accommodation")
        if item and isinstance(item, dict):
            yield item, f"day {day_num} accommodation"


def transportation_items(data: dict, agent: str):
    """Extract transportation items: days[].location_change (singular, optional)."""
    for day_obj in data.get("data", {}).get("days", []):
        day_num = day_obj.get("day", "?")
        item = day_obj.get("location_change")
        if item and isinstance(item, dict):
            yield item, f"day {day_num} location_change"


def timeline_items(data: dict, agent: str):
    """Extract timeline travel_segments: days[].travel_segments[]."""
    for day_obj in data.get("data", {}).get("days", []):
        day_num = day_obj.get("day", "?")
        segments = day_obj.get("travel_segments", [])
        if isinstance(segments, list):
            for idx, item in enumerate(segments):
                if isinstance(item, dict):
                    yield item, f"day {day_num} travel_segments[{idx}]"


# Map extractor names to functions
EXTRACTOR_FUNCS = {
    "meal_items": meal_items,
    "array_items": array_items,
    "accommodation_items": accommodation_items,
    "transportation_items": transportation_items,
    "timeline_items": timeline_items,
}


def values_equal(val_a: Any, val_b: Any) -> bool:
    """Compare two values for equality, handling lists and nested structures."""
    return val_a == val_b


def process_item(
    item: dict,
    field_map: list[tuple[str, str]],
    file_label: str,
    item_label: str,
) -> dict:
    """Process a single item dict, removing/renaming legacy fields.

    Returns dict with counts: {removed: int, renamed: int, warnings: int}
    """
    counts = {"removed": 0, "renamed": 0, "warnings": 0}

    for legacy_name, schema_name in field_map:
        if legacy_name not in item:
            continue

        legacy_val = item[legacy_name]
        has_schema = schema_name in item

        if has_schema:
            schema_val = item[schema_name]
            if values_equal(legacy_val, schema_val):
                # Rule 1: Both exist with same value -> delete legacy
                del item[legacy_name]
                counts["removed"] += 1
            else:
                # Rule 3: Both exist with different values -> WARNING
                print(
                    f"  WARNING: {file_label} -> {item_label}: "
                    f"'{legacy_name}' ({legacy_val!r}) != "
                    f"'{schema_name}' ({schema_val!r}) -- keeping both"
                )
                counts["warnings"] += 1
        else:
            # Rule 2: Only legacy exists -> rename to schema name
            item[schema_name] = legacy_val
            del item[legacy_name]
            counts["renamed"] += 1
            print(
                f"  RENAMED: {file_label} -> {item_label}: "
                f"'{legacy_name}' -> '{schema_name}'"
            )

    return counts


def process_file(file_path: Path, agent: str) -> dict:
    """Process a single JSON file, returning summary counts."""
    totals = {"removed": 0, "renamed": 0, "warnings": 0}

    if not file_path.exists():
        print(f"  SKIP: {file_path} does not exist")
        return totals

    field_map = FIELD_MAP_BY_FILE.get(agent, [])
    if not field_map:
        print(f"  SKIP: No field map for agent '{agent}'")
        return totals

    extractor_name = ITEM_EXTRACTORS.get(agent)
    if not extractor_name:
        print(f"  SKIP: No extractor for agent '{agent}'")
        return totals

    extractor_func = EXTRACTOR_FUNCS[extractor_name]

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_label = file_path.name

    for item, item_label in extractor_func(data, agent):
        counts = process_item(item, field_map, file_label, item_label)
        for key in totals:
            totals[key] += counts[key]

    # Write back
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return totals


def validate_file(file_path: Path) -> bool:
    """Validate that a JSON file is still valid after writing."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, OSError) as e:
        print(f"  VALIDATION FAILED: {file_path}: {e}")
        return False


def main():
    trip_dirs = [
        Path("/root/travel-planner/data/china-feb-15-mar-7-2026-20260202-195429"),
        Path("/root/travel-planner/data/beijing-exchange-bucket-list-20260202-232405"),
    ]

    files_to_process = [
        ("meals.json", "meals"),
        ("attractions.json", "attractions"),
        ("entertainment.json", "entertainment"),
        ("accommodation.json", "accommodation"),
        ("shopping.json", "shopping"),
        ("transportation.json", "transportation"),
        ("timeline.json", "timeline"),
    ]

    grand_totals = {"removed": 0, "renamed": 0, "warnings": 0}
    all_valid = True

    for trip_dir in trip_dirs:
        print(f"\n{'='*70}")
        print(f"TRIP: {trip_dir.name}")
        print(f"{'='*70}")

        if not trip_dir.exists():
            print(f"  ERROR: Directory does not exist: {trip_dir}")
            continue

        for filename, agent in files_to_process:
            file_path = trip_dir / filename
            print(f"\n  Processing: {filename}")

            totals = process_file(file_path, agent)

            print(
                f"    Removed: {totals['removed']}, "
                f"Renamed: {totals['renamed']}, "
                f"Warnings: {totals['warnings']}"
            )

            for key in grand_totals:
                grand_totals[key] += totals[key]

            # Validate after writing
            if file_path.exists():
                if not validate_file(file_path):
                    all_valid = False

    # Print grand summary
    print(f"\n{'='*70}")
    print("GRAND SUMMARY")
    print(f"{'='*70}")
    print(f"  Total removed:  {grand_totals['removed']}")
    print(f"  Total renamed:  {grand_totals['renamed']}")
    print(f"  Total warnings: {grand_totals['warnings']}")
    print(f"  All files valid: {'YES' if all_valid else 'NO'}")

    if grand_totals["warnings"] > 0:
        print("\n  NOTE: Review warnings above for field value mismatches.")

    if not all_valid:
        print("\n  ERROR: Some files failed JSON validation!")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
