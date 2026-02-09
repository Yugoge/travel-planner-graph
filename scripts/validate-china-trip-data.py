#!/usr/bin/env python3
"""
Validate all 7 data files for the China trip.
Read-only validation: checks JSON validity, coordinates, and required fields.
Usage: python validate-china-trip-data.py <data_directory>
"""

import json
import sys
import os
from pathlib import Path
from typing import Any


def load_json(filepath: str) -> tuple[Any | None, str | None]:
    """Load and parse a JSON file. Returns (data, error)."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except FileNotFoundError:
        return None, "File not found"
    except Exception as e:
        return None, f"Error: {e}"


def check_coordinates(item: dict, item_name: str) -> list[str]:
    """Check if coordinates are present and valid."""
    issues = []
    coords = item.get("coordinates")
    if coords is None:
        issues.append(f"  MISSING coordinates: {item_name}")
    elif not isinstance(coords, dict):
        issues.append(f"  INVALID coordinates (not object): {item_name}")
    else:
        lat = coords.get("lat")
        lng = coords.get("lng")
        if lat is None:
            issues.append(f"  MISSING lat in coordinates: {item_name}")
        if lng is None:
            issues.append(f"  MISSING lng in coordinates: {item_name}")
        if lat is not None and (lat < -90 or lat > 90):
            issues.append(f"  INVALID lat={lat}: {item_name}")
        if lng is not None and (lng < -180 or lng > 180):
            issues.append(f"  INVALID lng={lng}: {item_name}")
    return issues


def check_required_fields(item: dict, required: list[str], item_name: str) -> list[str]:
    """Check that required fields are present and non-null."""
    issues = []
    for field in required:
        if field not in item:
            issues.append(f"  MISSING field '{field}': {item_name}")
        elif item[field] is None:
            issues.append(f"  NULL field '{field}': {item_name}")
        elif isinstance(item[field], str) and item[field].strip() == "":
            issues.append(f"  EMPTY field '{field}': {item_name}")
    return issues


def get_item_label(item: dict, fallback: str = "unknown") -> str:
    """Get a readable label for an item."""
    return item.get("name_base") or item.get("name_local") or fallback


def validate_meals(data: dict) -> dict:
    """Validate meals.json structure and content."""
    required_per_meal = [
        "name_base", "name_local", "location_base", "location_local",
        "coordinates", "cost", "cuisine", "time", "currency"
    ]
    meal_types = ["breakfast", "lunch", "dinner"]

    total_items = 0
    with_coords = 0
    missing_coords = 0
    coord_issues = []
    field_issues = []
    days_found = []

    days = data.get("data", {}).get("days", [])
    for day_entry in days:
        day_num = day_entry.get("day", "?")
        date = day_entry.get("date", "?")
        days_found.append(day_num)

        # Check day header fields
        for df in ["day", "date", "location"]:
            if df not in day_entry:
                field_issues.append(f"  Day {day_num}: MISSING day header field '{df}'")

        for meal_type in meal_types:
            meal = day_entry.get(meal_type)
            if meal is None:
                continue  # Some days may not have all meals
            if isinstance(meal, list):
                meals_list = meal
            else:
                meals_list = [meal]

            for meal_item in meals_list:
                total_items += 1
                label = f"Day {day_num} {meal_type}: {get_item_label(meal_item)}"

                # Check coordinates
                ci = check_coordinates(meal_item, label)
                if ci:
                    missing_coords += 1
                    coord_issues.extend(ci)
                else:
                    with_coords += 1

                # Check required fields
                fi = check_required_fields(meal_item, required_per_meal, label)
                field_issues.extend(fi)

        # Check for snacks array
        snacks = day_entry.get("snacks", [])
        if isinstance(snacks, list):
            for snack in snacks:
                total_items += 1
                label = f"Day {day_num} snack: {get_item_label(snack)}"
                ci = check_coordinates(snack, label)
                if ci:
                    missing_coords += 1
                    coord_issues.extend(ci)
                else:
                    with_coords += 1
                fi = check_required_fields(snack, required_per_meal, label)
                field_issues.extend(fi)

    return {
        "total_items": total_items,
        "with_coords": with_coords,
        "missing_coords": missing_coords,
        "coord_issues": coord_issues,
        "field_issues": field_issues,
        "days_found": sorted(days_found),
    }


def validate_attractions(data: dict) -> dict:
    """Validate attractions.json structure and content."""
    required = [
        "name_base", "name_local", "location_base", "location_local",
        "coordinates", "cost", "duration_minutes", "type", "time", "currency"
    ]

    total_items = 0
    with_coords = 0
    missing_coords = 0
    coord_issues = []
    field_issues = []
    days_found = []

    days = data.get("data", {}).get("days", [])
    for day_entry in days:
        day_num = day_entry.get("day", "?")
        days_found.append(day_num)

        for df in ["day", "date", "location"]:
            if df not in day_entry:
                field_issues.append(f"  Day {day_num}: MISSING day header field '{df}'")

        attractions = day_entry.get("attractions", [])
        for item in attractions:
            total_items += 1
            label = f"Day {day_num}: {get_item_label(item)}"

            ci = check_coordinates(item, label)
            if ci:
                missing_coords += 1
                coord_issues.extend(ci)
            else:
                with_coords += 1

            fi = check_required_fields(item, required, label)
            field_issues.extend(fi)

    return {
        "total_items": total_items,
        "with_coords": with_coords,
        "missing_coords": missing_coords,
        "coord_issues": coord_issues,
        "field_issues": field_issues,
        "days_found": sorted(days_found),
    }


def validate_entertainment(data: dict) -> dict:
    """Validate entertainment.json structure and content."""
    required = [
        "name_base", "name_local", "location_base", "location_local",
        "coordinates", "cost", "type", "time", "currency"
    ]

    total_items = 0
    with_coords = 0
    missing_coords = 0
    coord_issues = []
    field_issues = []
    days_found = []

    days = data.get("data", {}).get("days", [])
    for day_entry in days:
        day_num = day_entry.get("day", "?")
        days_found.append(day_num)

        for df in ["day", "date", "location"]:
            if df not in day_entry:
                field_issues.append(f"  Day {day_num}: MISSING day header field '{df}'")

        items = day_entry.get("entertainment", [])
        for item in items:
            total_items += 1
            label = f"Day {day_num}: {get_item_label(item)}"

            ci = check_coordinates(item, label)
            if ci:
                missing_coords += 1
                coord_issues.extend(ci)
            else:
                with_coords += 1

            fi = check_required_fields(item, required, label)
            field_issues.extend(fi)

    return {
        "total_items": total_items,
        "with_coords": with_coords,
        "missing_coords": missing_coords,
        "coord_issues": coord_issues,
        "field_issues": field_issues,
        "days_found": sorted(days_found),
    }


def validate_shopping(data: dict) -> dict:
    """Validate shopping.json structure and content."""
    required = [
        "name_base", "name_local", "location_base", "location_local",
        "coordinates", "cost", "type", "time", "currency"
    ]

    total_items = 0
    with_coords = 0
    missing_coords = 0
    coord_issues = []
    field_issues = []
    days_found = []

    days = data.get("data", {}).get("days", [])
    for day_entry in days:
        day_num = day_entry.get("day", "?")
        days_found.append(day_num)

        for df in ["day", "date"]:
            if df not in day_entry:
                field_issues.append(f"  Day {day_num}: MISSING day header field '{df}'")

        items = day_entry.get("shopping", [])
        for item in items:
            total_items += 1
            label = f"Day {day_num}: {get_item_label(item)}"

            ci = check_coordinates(item, label)
            if ci:
                missing_coords += 1
                coord_issues.extend(ci)
            else:
                with_coords += 1

            fi = check_required_fields(item, required, label)
            field_issues.extend(fi)

    return {
        "total_items": total_items,
        "with_coords": with_coords,
        "missing_coords": missing_coords,
        "coord_issues": coord_issues,
        "field_issues": field_issues,
        "days_found": sorted(days_found),
    }


def validate_accommodation(data: dict) -> dict:
    """Validate accommodation.json structure and content."""
    required = [
        "name_base", "name_local", "location_base", "location_local",
        "coordinates", "cost", "type", "check_in", "check_out", "currency"
    ]

    total_items = 0
    with_coords = 0
    missing_coords = 0
    coord_issues = []
    field_issues = []
    days_found = []

    days = data.get("data", {}).get("days", [])
    for day_entry in days:
        day_num = day_entry.get("day", "?")
        days_found.append(day_num)

        for df in ["day", "date", "location"]:
            if df not in day_entry:
                field_issues.append(f"  Day {day_num}: MISSING day header field '{df}'")

        accom = day_entry.get("accommodation")
        if accom is None:
            field_issues.append(f"  Day {day_num}: MISSING accommodation entry")
            continue

        total_items += 1
        label = f"Day {day_num}: {get_item_label(accom)}"

        ci = check_coordinates(accom, label)
        if ci:
            missing_coords += 1
            coord_issues.extend(ci)
        else:
            with_coords += 1

        fi = check_required_fields(accom, required, label)
        field_issues.extend(fi)

    return {
        "total_items": total_items,
        "with_coords": with_coords,
        "missing_coords": missing_coords,
        "coord_issues": coord_issues,
        "field_issues": field_issues,
        "days_found": sorted(days_found),
    }


def validate_transportation(data: dict) -> dict:
    """Validate transportation.json structure and content."""
    required_location_change = [
        "from", "to", "transportation", "departure_time", "arrival_time",
        "duration_minutes", "cost", "currency"
    ]

    total_items = 0
    with_coords = 0  # Transportation uses from/to stations, not POI coords
    missing_coords = 0
    coord_issues = []
    field_issues = []
    days_found = []

    days = data.get("data", {}).get("days", [])
    for day_entry in days:
        day_num = day_entry.get("day", "?")
        days_found.append(day_num)

        loc_change = day_entry.get("location_change")
        if loc_change is None:
            continue

        total_items += 1
        from_loc = loc_change.get("from", "?")
        to_loc = loc_change.get("to", "?")
        label = f"Day {day_num}: {from_loc} -> {to_loc}"

        fi = check_required_fields(loc_change, required_location_change, label)
        field_issues.extend(fi)

        # Transportation doesn't necessarily have coordinates at the top level
        # but check route_details for station info
        route = loc_change.get("route_details", {})
        if not route:
            field_issues.append(f"  MISSING route_details: {label}")

    return {
        "total_items": total_items,
        "with_coords": "N/A (uses station names)",
        "missing_coords": "N/A",
        "coord_issues": coord_issues,
        "field_issues": field_issues,
        "days_found": sorted(days_found),
    }


def validate_timeline(data: dict) -> dict:
    """Validate timeline.json structure and content."""
    required_per_event = ["start_time", "end_time", "duration_minutes"]

    total_items = 0
    field_issues = []
    days_found = []
    time_issues = []

    days = data.get("data", {}).get("days", [])
    for day_entry in days:
        day_num = day_entry.get("day", "?")
        date = day_entry.get("date", "?")
        days_found.append(day_num)

        for df in ["day", "date"]:
            if df not in day_entry:
                field_issues.append(f"  Day {day_num}: MISSING day header field '{df}'")

        timeline = day_entry.get("timeline", {})
        if not isinstance(timeline, dict):
            field_issues.append(f"  Day {day_num}: timeline is not a dict")
            continue

        prev_end = None
        for event_name, event_data in timeline.items():
            total_items += 1
            label = f"Day {day_num}: {event_name}"

            if not isinstance(event_data, dict):
                field_issues.append(f"  NOT a dict: {label}")
                continue

            fi = check_required_fields(event_data, required_per_event, label)
            field_issues.extend(fi)

            # Check time format
            start = event_data.get("start_time", "")
            end = event_data.get("end_time", "")

            # Check for time overlaps/gaps
            if prev_end and start:
                if start < prev_end:
                    time_issues.append(f"  TIME OVERLAP: Day {day_num}: '{event_name}' starts at {start} but previous event ends at {prev_end}")
            prev_end = end

    return {
        "total_items": total_items,
        "with_coords": "N/A (timeline has no coordinates)",
        "missing_coords": "N/A",
        "coord_issues": [],
        "field_issues": field_issues,
        "time_issues": time_issues,
        "days_found": sorted(days_found),
    }


def print_separator(char: str = "=", width: int = 90):
    print(char * width)


def print_file_report(filename: str, json_valid: bool, error: str | None, result: dict | None):
    """Print validation report for a single file."""
    print()
    print_separator("=")
    print(f"  FILE: {filename}")
    print_separator("=")

    if not json_valid:
        print(f"  JSON Valid:       NO  ({error})")
        print(f"  -- Skipping further checks --")
        return

    print(f"  JSON Valid:       YES")
    print(f"  Days found:       {result['days_found']}")
    print(f"  Total items:      {result['total_items']}")
    print(f"  With coordinates: {result['with_coords']}")
    print(f"  Missing coords:   {result['missing_coords']}")

    if result.get("coord_issues"):
        print()
        print(f"  --- Coordinate Issues ({len(result['coord_issues'])}) ---")
        for issue in result["coord_issues"]:
            print(issue)

    if result.get("field_issues"):
        print()
        print(f"  --- Field Issues ({len(result['field_issues'])}) ---")
        for issue in result["field_issues"]:
            print(issue)

    if result.get("time_issues"):
        print()
        print(f"  --- Time Issues ({len(result['time_issues'])}) ---")
        for issue in result["time_issues"]:
            print(issue)

    if not result.get("coord_issues") and not result.get("field_issues") and not result.get("time_issues"):
        print()
        print("  >> ALL CHECKS PASSED <<")


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate-china-trip-data.py <data_directory>")
        sys.exit(1)

    data_dir = Path(sys.argv[1])
    if not data_dir.is_dir():
        print(f"Error: Not a directory: {data_dir}")
        sys.exit(1)

    files_and_validators = {
        "meals.json": validate_meals,
        "attractions.json": validate_attractions,
        "entertainment.json": validate_entertainment,
        "shopping.json": validate_shopping,
        "accommodation.json": validate_accommodation,
        "transportation.json": validate_transportation,
        "timeline.json": validate_timeline,
    }

    print()
    print_separator("#")
    print("  COMPREHENSIVE DATA VALIDATION REPORT")
    print(f"  Directory: {data_dir}")
    print_separator("#")

    summary_rows = []
    total_issues = 0

    for filename, validator in files_and_validators.items():
        filepath = data_dir / filename
        data, error = load_json(str(filepath))

        if error:
            print_file_report(filename, False, error, None)
            summary_rows.append({
                "file": filename,
                "json_valid": "NO",
                "items": "-",
                "coords_ok": "-",
                "coords_missing": "-",
                "field_issues": "-",
                "status": "FAIL"
            })
            total_issues += 1
            continue

        result = validator(data)

        coord_issue_count = len(result.get("coord_issues", []))
        field_issue_count = len(result.get("field_issues", []))
        time_issue_count = len(result.get("time_issues", []))
        all_issues = coord_issue_count + field_issue_count + time_issue_count
        total_issues += all_issues

        print_file_report(filename, True, None, result)

        status = "PASS" if all_issues == 0 else f"WARN ({all_issues} issues)"

        summary_rows.append({
            "file": filename,
            "json_valid": "YES",
            "items": str(result["total_items"]),
            "coords_ok": str(result["with_coords"]),
            "coords_missing": str(result["missing_coords"]),
            "field_issues": str(field_issue_count),
            "time_issues": str(time_issue_count) if "time_issues" in result else "-",
            "status": status
        })

    # Print summary table
    print()
    print()
    print_separator("#")
    print("  SUMMARY TABLE")
    print_separator("#")
    print()

    # Header
    header = f"{'File':<24} {'JSON':>5} {'Items':>6} {'Coords OK':>10} {'Coords Miss':>12} {'Field Iss':>10} {'Status':<20}"
    print(header)
    print("-" * len(header))

    for row in summary_rows:
        print(
            f"{row['file']:<24} {row['json_valid']:>5} {row['items']:>6} "
            f"{row['coords_ok']:>10} {row['coords_missing']:>12} "
            f"{row['field_issues']:>10} {row['status']:<20}"
        )

    print("-" * len(header))
    print()

    if total_issues == 0:
        print("  OVERALL RESULT: ALL 7 FILES PASSED VALIDATION")
    else:
        print(f"  OVERALL RESULT: {total_issues} TOTAL ISSUES FOUND")

    print()
    print_separator("#")
    print()

    sys.exit(0 if total_issues == 0 else 1)


if __name__ == "__main__":
    main()
