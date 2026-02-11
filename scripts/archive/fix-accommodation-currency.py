#!/usr/bin/env python3
"""
Fix currency_local and currency fields for Hong Kong (HKD) and Macau (MOP)
accommodations that were incorrectly set to CNY.

Usage: python fix-accommodation-currency.py <accommodation_json_path> [<additional_paths>...]
       If no paths given, processes both known trip accommodation files.

Exit codes: 0=success (changes made), 1=error, 2=no changes needed
"""

import json
import sys
from pathlib import Path

# Location-to-currency mapping for Special Administrative Regions
# Mainland China locations use CNY (default), so only SAR overrides listed
LOCATION_CURRENCY_MAP = {
    "Hong Kong": "HKD",
    "Macau": "MOP",
    "Macao": "MOP",
}

DEFAULT_PATHS = [
    "/root/travel-planner/data/beijing-exchange-bucket-list-20260202-232405/accommodation.json",
    "/root/travel-planner/data/china-feb-15-mar-7-2026-20260202-195429/accommodation.json",
]


def get_correct_currency(location: str) -> str | None:
    """Return the correct currency for a location, or None if CNY is correct."""
    for keyword, currency in LOCATION_CURRENCY_MAP.items():
        if keyword.lower() in location.lower():
            return currency
    return None


def fix_currencies(file_path: str) -> list[dict]:
    """Fix currency fields in an accommodation JSON file.

    Returns a list of changes made (each is a dict with day, name, field, old, new).
    """
    path = Path(file_path)
    if not path.exists():
        print(f"SKIP: File not found: {file_path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changes = []

    for day_entry in data.get("data", {}).get("days", []):
        day_num = day_entry.get("day", "?")
        location = day_entry.get("location", "")
        acc = day_entry.get("accommodation", {})
        name = acc.get("name_base") or acc.get("name", "Unknown")

        correct_currency = get_correct_currency(location)
        if correct_currency is None:
            # Location is mainland China; CNY is correct
            continue

        # Fix currency_local
        current_local = acc.get("currency_local", "")
        if current_local != correct_currency:
            changes.append({
                "file": str(path.name),
                "day": day_num,
                "name": name,
                "location": location,
                "field": "currency_local",
                "old": current_local,
                "new": correct_currency,
            })
            acc["currency_local"] = correct_currency

        # Fix legacy currency field if present
        current_legacy = acc.get("currency")
        if current_legacy is not None and current_legacy != correct_currency:
            changes.append({
                "file": str(path.name),
                "day": day_num,
                "name": name,
                "location": location,
                "field": "currency",
                "old": current_legacy,
                "new": correct_currency,
            })
            acc["currency"] = correct_currency

    if changes:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Ensure trailing newline
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n")

    return changes


def validate_json(file_path: str) -> bool:
    """Validate that the file is still valid JSON after edits."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"VALIDATION FAILED: {file_path} - {e}")
        return False


def main():
    paths = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_PATHS

    all_changes = []
    all_valid = True

    for file_path in paths:
        print(f"\n{'=' * 60}")
        print(f"Processing: {file_path}")
        print(f"{'=' * 60}")

        changes = fix_currencies(file_path)
        all_changes.extend(changes)

        if changes:
            for c in changes:
                print(
                    f"  FIXED Day {c['day']}: {c['name']} ({c['location']})"
                    f" - {c['field']}: {c['old']} -> {c['new']}"
                )

            if validate_json(file_path):
                print(f"  VALIDATED: JSON is valid after changes")
            else:
                all_valid = False
        else:
            print("  No currency fixes needed in this file.")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {len(all_changes)} field(s) fixed across {len(paths)} file(s)")
    print(f"{'=' * 60}")

    if not all_valid:
        print("ERROR: One or more files failed validation!")
        sys.exit(1)
    elif not all_changes:
        print("No changes were needed.")
        sys.exit(2)
    else:
        print("All changes applied and validated successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
