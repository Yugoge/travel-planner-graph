#!/usr/bin/env python3
"""Fix null/missing date fields in bucket-list trip day entries.

For bucket-list trips (no fixed calendar dates), the schema requires
date to be a non-null string. This script sets date to "" for any day
entry where date is null or missing.

Usage: fix-null-dates.py <trip_directory>
"""

import json
import sys
from pathlib import Path


def fix_dates_in_file(filepath: Path) -> int:
    """Fix null/missing date fields in a single JSON file.

    Returns the number of day entries fixed.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Only process files that have data.days[] structure
    if "data" not in data or "days" not in data.get("data", {}):
        return 0

    days = data["data"]["days"]
    fix_count = 0

    for day_entry in days:
        if not isinstance(day_entry, dict):
            continue
        if "date" not in day_entry or day_entry["date"] is None:
            day_entry["date"] = ""
            fix_count += 1

    if fix_count > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return fix_count


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <trip_directory>", file=sys.stderr)
        sys.exit(1)

    trip_dir = Path(sys.argv[1])
    if not trip_dir.is_dir():
        print(f"Error: Not a directory: {trip_dir}", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(trip_dir.glob("*.json"))
    total_fixes = 0

    for filepath in json_files:
        try:
            fix_count = fix_dates_in_file(filepath)
            status = f"fixed {fix_count} days" if fix_count > 0 else "no fixes needed"
            print(f"  {filepath.name}: {status}")
            total_fixes += fix_count
        except json.JSONDecodeError as e:
            print(f"  {filepath.name}: ERROR - invalid JSON: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  {filepath.name}: ERROR - {e}", file=sys.stderr)

    print(f"\nTotal fixes: {total_fixes} day entries across {len(json_files)} files")
    return 0 if total_fixes >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
