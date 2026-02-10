#!/usr/bin/env python3
"""
Backfill missing days in budget.json using data from other agent files.

Reads meals.json, accommodation.json, attractions.json, entertainment.json,
shopping.json, and transportation.json to compute budget entries for days
that are missing from budget.json. Existing days are preserved as-is.

Usage:
    python backfill-budget-days.py <trip_directory>

Exit codes:
    0 = success
    1 = failure (missing files, invalid data)
"""

import json
import sys
from pathlib import Path


def load_json(filepath: Path) -> dict:
    """Load and return parsed JSON from a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_day_index(data: dict, key: str = "days") -> dict:
    """Build a dict mapping day number to day data from agent file."""
    index = {}
    for day_entry in data.get("data", {}).get(key, []):
        day_num = day_entry.get("day")
        if day_num is not None:
            index[day_num] = day_entry
    return index


def get_meal_cost(meal_day: dict) -> int:
    """Sum breakfast + lunch + dinner costs from a meals.json day entry."""
    total = 0
    for meal_type in ("breakfast", "lunch", "dinner"):
        meal = meal_day.get(meal_type, {})
        if isinstance(meal, dict):
            total += meal.get("cost", 0) or 0
    return total


def get_accommodation_cost(accom_day: dict | None) -> int:
    """Get accommodation cost for a day."""
    if accom_day is None:
        return 0
    accom = accom_day.get("accommodation", {})
    if isinstance(accom, dict):
        return accom.get("cost", 0) or 0
    return 0


def get_list_cost(day_entry: dict | None, list_key: str) -> int:
    """Sum costs from a list of items (attractions, entertainment, shopping)."""
    if day_entry is None:
        return 0
    items = day_entry.get(list_key, [])
    if not isinstance(items, list):
        return 0
    total = 0
    for item in items:
        if isinstance(item, dict):
            total += item.get("cost", 0) or 0
    return total


def get_transportation_cost(transport_day: dict | None) -> int:
    """Get inter-city transportation cost for a day."""
    if transport_day is None:
        return 0
    loc_change = transport_day.get("location_change", {})
    if isinstance(loc_change, dict):
        return loc_change.get("cost", 0) or 0
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: backfill-budget-days.py <trip_directory>", file=sys.stderr)
        sys.exit(1)

    trip_dir = Path(sys.argv[1])
    if not trip_dir.is_dir():
        print(f"Error: Directory not found: {trip_dir}", file=sys.stderr)
        sys.exit(1)

    # Load all source files
    budget_path = trip_dir / "budget.json"
    required_files = {
        "budget": budget_path,
        "meals": trip_dir / "meals.json",
    }
    optional_files = {
        "accommodation": trip_dir / "accommodation.json",
        "attractions": trip_dir / "attractions.json",
        "entertainment": trip_dir / "entertainment.json",
        "shopping": trip_dir / "shopping.json",
        "transportation": trip_dir / "transportation.json",
    }

    for name, path in required_files.items():
        if not path.exists():
            print(f"Error: Required file not found: {path}", file=sys.stderr)
            sys.exit(1)

    budget_data = load_json(budget_path)
    meals_data = load_json(required_files["meals"])

    source_data = {}
    for name, path in optional_files.items():
        if path.exists():
            source_data[name] = load_json(path)
        else:
            print(f"Warning: Optional file not found: {path}", file=sys.stderr)
            source_data[name] = {"data": {"days": []}}

    # Build day indexes
    meals_index = build_day_index(meals_data)
    accom_index = build_day_index(source_data["accommodation"])
    attractions_index = build_day_index(source_data["attractions"])
    entertainment_index = build_day_index(source_data["entertainment"])
    shopping_index = build_day_index(source_data["shopping"])
    transport_index = build_day_index(source_data["transportation"])

    # Get existing budget days
    existing_days = budget_data.get("data", {}).get("days", [])
    existing_day_nums = {d["day"] for d in existing_days}

    print(f"Existing budget days: {sorted(existing_day_nums)}")
    print(f"Meals.json days: {sorted(meals_index.keys())}")

    # Find missing days
    missing_day_nums = sorted(set(meals_index.keys()) - existing_day_nums)
    print(f"Missing days to backfill: {missing_day_nums}")

    if not missing_day_nums:
        print("No missing days. Budget is already complete.")
        sys.exit(0)

    # Generate budget entries for missing days
    new_days = []
    for day_num in missing_day_nums:
        meal_day = meals_index.get(day_num, {})
        date = meal_day.get("date", "")
        location = meal_day.get("location", "")

        meals_cost = get_meal_cost(meal_day)
        accom_cost = get_accommodation_cost(accom_index.get(day_num))
        attractions_cost = get_list_cost(
            attractions_index.get(day_num), "attractions"
        )
        entertainment_cost = get_list_cost(
            entertainment_index.get(day_num), "entertainment"
        )
        activities_cost = attractions_cost + entertainment_cost
        shopping_cost = get_list_cost(shopping_index.get(day_num), "shopping")
        transport_cost = get_transportation_cost(transport_index.get(day_num))

        day_total = (
            meals_cost + accom_cost + activities_cost
            + shopping_cost + transport_cost
        )

        entry = {
            "day": day_num,
            "date": date,
            "location": location,
            "budget": {
                "meals": meals_cost,
                "accommodation": accom_cost,
                "activities": activities_cost,
                "shopping": shopping_cost,
                "transportation": transport_cost,
                "total": day_total,
            },
        }

        new_days.append(entry)
        print(
            f"  Day {day_num} ({date}, {location}): "
            f"meals={meals_cost}, accom={accom_cost}, "
            f"activities={activities_cost}, shopping={shopping_cost}, "
            f"transport={transport_cost}, total={day_total}"
        )

    # Merge existing + new, sort by day number
    all_days = existing_days + new_days
    all_days.sort(key=lambda d: d["day"])

    # Compute trip total
    trip_total = sum(d["budget"]["total"] for d in all_days)
    print(f"\nTrip total (all {len(all_days)} days): {trip_total} CNY")

    # Update budget data
    budget_data["data"]["days"] = all_days
    budget_data["data"]["trip_total"] = trip_total
    budget_data["data"]["total_days"] = len(all_days)

    # Write back
    with open(budget_path, "w", encoding="utf-8") as f:
        json.dump(budget_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved updated budget.json with {len(all_days)} days.")
    print(f"  Preserved: {len(existing_days)} existing days")
    print(f"  Added: {len(new_days)} new days")
    sys.exit(0)


if __name__ == "__main__":
    main()
