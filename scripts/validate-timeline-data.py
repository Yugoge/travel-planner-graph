#!/usr/bin/env python3
"""
Validate timeline.json data completeness and structure.

Root Cause Reference (commit ef0ed28): timeline.json was cleared to empty
dictionaries, causing HTML generation to fail. This script validates timeline
data is present and non-empty.

Usage: validate-timeline-data.py <timeline_json_path>

Exit Codes:
  0 - Timeline data valid (>50% coverage)
  1 - Timeline data invalid (most days empty or file errors)
  2 - File not found or JSON parse error
"""

import sys
import json
from pathlib import Path


def validate_timeline_data(timeline_path: str) -> int:
    """
    Validate timeline.json structure and data completeness.

    Args:
        timeline_path: Path to timeline.json file

    Returns:
        0 if valid, 1 if invalid, 2 if file errors
    """
    path = Path(timeline_path)

    # Check file exists
    if not path.exists():
        print(f"✗ Timeline validation FAILED")
        print(f"  Error: File not found: {timeline_path}")
        return 2

    # Read and parse JSON
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"✗ Timeline validation FAILED")
        print(f"  Error: Invalid JSON: {e}")
        return 2
    except Exception as e:
        print(f"✗ Timeline validation FAILED")
        print(f"  Error: Cannot read file: {e}")
        return 2

    # Validate structure
    if 'data' not in data:
        print(f"✗ Timeline validation FAILED")
        print(f"  Error: Missing 'data' field in JSON")
        return 1

    if 'days' not in data['data']:
        print(f"✗ Timeline validation FAILED")
        print(f"  Error: Missing 'data.days' array in JSON")
        return 1

    days = data['data']['days']
    if not isinstance(days, list):
        print(f"✗ Timeline validation FAILED")
        print(f"  Error: 'data.days' is not an array")
        return 1

    total_days = len(days)
    if total_days == 0:
        print(f"✗ Timeline validation FAILED")
        print(f"  Error: No days found in timeline data")
        return 1

    # Count days with timeline data
    days_with_data = 0
    days_empty = 0
    empty_day_numbers = []

    for day in days:
        day_num = day.get('day', '?')
        timeline = day.get('timeline', {})

        if not isinstance(timeline, dict):
            print(f"✗ Timeline validation FAILED")
            print(f"  Error: Day {day_num} timeline is not a dictionary")
            return 1

        # Check if timeline has any activities
        if timeline and len(timeline) > 0:
            days_with_data += 1
        else:
            days_empty += 1
            empty_day_numbers.append(day_num)

    # Calculate coverage
    coverage_pct = (days_with_data / total_days) * 100 if total_days > 0 else 0

    # Print report
    print(f"✓ Timeline data validation")
    print(f"  - Total days: {total_days}")
    print(f"  - Days with timeline data: {days_with_data}/{total_days}")
    print(f"  - Days with empty timeline: {days_empty}/{total_days}")

    if empty_day_numbers:
        # Show first 10 empty days to avoid clutter
        display_empty = empty_day_numbers[:10]
        if len(empty_day_numbers) > 10:
            print(f"  - Empty day numbers: {display_empty} ... (and {len(empty_day_numbers) - 10} more)")
        else:
            print(f"  - Empty day numbers: {empty_day_numbers}")

    print(f"  - Coverage: {coverage_pct:.1f}%")

    # Determine pass/fail (>50% coverage threshold)
    if coverage_pct > 50:
        print(f"  - Status: PASS (>50% coverage)")
        return 0
    else:
        print(f"  - Status: FAIL (≤50% coverage)")
        print(f"  - Action Required: Re-invoke timeline-agent with explicit Write instruction")
        return 1


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-timeline-data.py <timeline_json_path>")
        print("")
        print("Example:")
        print("  python validate-timeline-data.py data/china-feb-15-mar-7-2026-20260202-195429/timeline.json")
        sys.exit(2)

    timeline_path = sys.argv[1]
    exit_code = validate_timeline_data(timeline_path)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
