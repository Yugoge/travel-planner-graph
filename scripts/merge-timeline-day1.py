#!/usr/bin/env python3
"""
Timeline Day 1 Merge Script
============================
Merge 3 missing travel segments from backup into current 21-day timeline.
Also fix Day 2 missing hotel check-in activity.

Missing from Day 1 (need to merge back):
1. "Walk to Danzishi Ferry Pier" - 步行到弹子石码头 (15:20-15:35)
2. "Taxi from Hongyadong to Laojun Dong Temple" - 从洪崖洞打车到老君洞 (15:50-16:05)
3. "Walk to Hongyadong" - 步行到洪崖洞 (20:50-21:05)

Day 2 Missing:
- Hotel check-in activity at 14:00 (from accommodation.json)

Usage:
    python3 scripts/merge-timeline-day1.py --trip TRIP_SLUG
    python3 scripts/merge-timeline-day1.py --trip TRIP_SLUG --fix-day2-hotel
    python3 scripts/merge-timeline-day1.py --trip TRIP_SLUG --dry-run

Design:
    - Reads backup timeline (1-day version)
    - Extracts 3 missing segments
    - Inserts into current timeline in chronological order
    - Validates no time conflicts
    - Uses scripts/save.py for final save
    - Adds Day 2 hotel check-in from accommodation.json
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SAVE_PY = SCRIPTS_DIR / "save.py"

# Missing segments to merge
MISSING_SEGMENTS = [
    {
        "name_base": "Walk to Danzishi Ferry Pier",
        "name_local": "步行到弹子石码头",
        "start_time": "15:20",
        "end_time": "15:35"
    },
    {
        "name_base": "Taxi from Hongyadong to Laojun Dong Temple",
        "name_local": "从洪崖洞打车到老君洞",
        "start_time": "15:50",
        "end_time": "16:05"
    },
    {
        "name_base": "Walk to Hongyadong",
        "name_local": "步行到洪崖洞",
        "start_time": "20:50",
        "end_time": "21:05"
    }
]


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m


def check_time_overlap(activity1: Dict[str, Any], activity2: Dict[str, Any]) -> bool:
    """Check if two activities overlap in time.

    Returns:
        True if overlap detected, False otherwise
    """
    start1 = time_to_minutes(activity1['start_time'])
    end1 = time_to_minutes(activity1['end_time'])
    start2 = time_to_minutes(activity2['start_time'])
    end2 = time_to_minutes(activity2['end_time'])

    # Overlap if: start1 < end2 AND start2 < end1
    return start1 < end2 and start2 < end1


def merge_segments_into_day(day_timeline: Dict[str, Any], segments: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Merge segments into day timeline, checking for conflicts.

    Returns:
        (success, error_messages)
    """
    errors = []

    for segment in segments:
        # Check for conflicts with existing activities
        for activity_name, activity_data in day_timeline.items():
            if check_time_overlap(segment, activity_data):
                errors.append(
                    f"CONFLICT: {segment['name_base']} ({segment['start_time']}-{segment['end_time']}) "
                    f"overlaps with {activity_name} ({activity_data['start_time']}-{activity_data['end_time']})"
                )

    if errors:
        return False, errors

    # No conflicts, merge segments
    for segment in segments:
        # Use name_base as key (consistent with existing timeline format)
        key = segment['name_base']
        day_timeline[key] = {
            'start_time': segment['start_time'],
            'end_time': segment['end_time'],
            'duration_minutes': time_to_minutes(segment['end_time']) - time_to_minutes(segment['start_time'])
        }

        # Add name_local if available
        if 'name_local' in segment:
            day_timeline[key]['name_local'] = segment['name_local']

    return True, []


def add_day2_hotel_checkin(timeline_data: Dict[str, Any], trip_dir: Path) -> Tuple[bool, List[str]]:
    """Add Day 2 hotel check-in activity from accommodation.json.

    Returns:
        (success, error_messages)
    """
    errors = []

    # Read accommodation.json
    accommodation_file = trip_dir / "accommodation.json"
    if not accommodation_file.exists():
        errors.append(f"accommodation.json not found at {accommodation_file}")
        return False, errors

    try:
        with open(accommodation_file, encoding='utf-8') as f:
            accommodation_data = json.load(f)
    except Exception as e:
        errors.append(f"Failed to read accommodation.json: {e}")
        return False, errors

    # Extract Day 2 accommodation
    if 'data' not in accommodation_data or 'days' not in accommodation_data['data']:
        errors.append("accommodation.json missing expected structure (data.days)")
        return False, errors

    days = accommodation_data['data']['days']
    if len(days) < 2:
        errors.append(f"accommodation.json has only {len(days)} days, need at least 2")
        return False, errors

    day2_accom = days[1]  # Index 1 = Day 2

    # Get hotel check-in time
    if 'check_in_time' not in day2_accom:
        errors.append("Day 2 accommodation missing check_in_time")
        return False, errors

    check_in_time = day2_accom['check_in_time']
    hotel_name_base = day2_accom.get('name_base', 'Hotel')
    hotel_name_local = day2_accom.get('name_local', '')

    # Create hotel check-in activity
    hotel_activity = {
        'start_time': check_in_time,
        'end_time': check_in_time,  # Check-in is a point-in-time event
        'duration_minutes': 0
    }

    if hotel_name_local:
        hotel_activity['name_local'] = f"{hotel_name_local}办理入住"

    # Insert into Day 2 timeline
    if len(timeline_data['data']['days']) < 2:
        errors.append(f"Timeline has only {len(timeline_data['data']['days'])} days, need at least 2")
        return False, errors

    day2_timeline = timeline_data['data']['days'][1]['timeline']

    # Check for conflicts
    activity_name = f"Hotel check-in at {hotel_name_base}"

    for existing_name, existing_data in day2_timeline.items():
        if check_time_overlap(hotel_activity, existing_data):
            # Warn but don't block (check-in is point-in-time, may "overlap" on paper)
            print(f"⚠️  Note: {activity_name} at {check_in_time} overlaps with {existing_name}", file=sys.stderr)

    # Add to timeline
    day2_timeline[activity_name] = hotel_activity

    return True, []


def load_timeline(trip_dir: Path, filename: str) -> Optional[Dict[str, Any]]:
    """Load timeline JSON file.

    Returns:
        Timeline data dict or None if failed
    """
    timeline_file = trip_dir / filename

    if not timeline_file.exists():
        print(f"❌ Timeline file not found: {timeline_file}", file=sys.stderr)
        return None

    try:
        with open(timeline_file, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to read {filename}: {e}", file=sys.stderr)
        return None


def save_timeline_with_savepy(trip_slug: str, timeline_data: Dict[str, Any]) -> bool:
    """Save timeline using scripts/save.py.

    Returns:
        True if successful, False otherwise
    """
    # Create temp file
    temp_file = Path("/tmp/timeline_merge_update.json")

    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(timeline_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Failed to create temp file: {e}", file=sys.stderr)
        return False

    # Call save.py via venv
    venv_activate = PROJECT_ROOT / "venv" / "bin" / "activate"

    if not venv_activate.exists():
        print(f"❌ Virtual environment not found at {venv_activate}", file=sys.stderr)
        return False

    cmd = f"source {venv_activate} && python {SAVE_PY} --trip {trip_slug} --agent timeline --input {temp_file}"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            executable='/bin/bash',
            capture_output=True,
            text=True
        )

        # Print save.py output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(f"❌ save.py failed with exit code {result.returncode}", file=sys.stderr)
            return False

        return True

    except Exception as e:
        print(f"❌ Failed to execute save.py: {e}", file=sys.stderr)
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge 3 missing Day 1 travel segments and fix Day 2 hotel check-in",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge Day 1 segments only
  python3 scripts/merge-timeline-day1.py --trip china-feb-15-mar-7-2026-20260202-195429

  # Merge Day 1 + fix Day 2 hotel check-in
  python3 scripts/merge-timeline-day1.py --trip china-feb-15-mar-7-2026-20260202-195429 --fix-day2-hotel

  # Preview changes without saving
  python3 scripts/merge-timeline-day1.py --trip china-feb-15-mar-7-2026-20260202-195429 --dry-run
        """
    )

    parser.add_argument("--trip", required=True, help="Trip slug (directory name in data/)")
    parser.add_argument("--fix-day2-hotel", action="store_true", help="Also add Day 2 hotel check-in activity")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")

    args = parser.parse_args()

    trip_dir = DATA_DIR / args.trip

    if not trip_dir.exists():
        print(f"❌ Trip directory not found: {trip_dir}", file=sys.stderr)
        sys.exit(1)

    # Load current timeline (21-day version)
    print(f"📖 Loading current timeline from {trip_dir / 'timeline.json'}...", file=sys.stderr)
    timeline_data = load_timeline(trip_dir, "timeline.json")

    if timeline_data is None:
        sys.exit(1)

    # Verify it's 21-day version
    days_count = len(timeline_data.get('data', {}).get('days', []))
    print(f"   Current timeline has {days_count} days", file=sys.stderr)

    if days_count != 21:
        print(f"⚠️  WARNING: Expected 21 days, found {days_count}", file=sys.stderr)

    # Get Day 1 timeline
    if days_count < 1:
        print(f"❌ Timeline has no days", file=sys.stderr)
        sys.exit(1)

    day1_timeline = timeline_data['data']['days'][0]['timeline']
    original_day1_count = len(day1_timeline)

    print(f"   Day 1 currently has {original_day1_count} activities", file=sys.stderr)

    # Merge 3 missing segments into Day 1
    print(f"\n🔀 Merging 3 missing segments into Day 1...", file=sys.stderr)

    success, errors = merge_segments_into_day(day1_timeline, MISSING_SEGMENTS)

    if not success:
        print(f"❌ Merge failed due to time conflicts:", file=sys.stderr)
        for error in errors:
            print(f"   {error}", file=sys.stderr)
        sys.exit(1)

    new_day1_count = len(day1_timeline)
    print(f"✅ Day 1 now has {new_day1_count} activities (+{new_day1_count - original_day1_count})", file=sys.stderr)

    for segment in MISSING_SEGMENTS:
        print(f"   ✓ {segment['name_base']} ({segment['start_time']}-{segment['end_time']})", file=sys.stderr)

    # Fix Day 2 hotel check-in if requested
    if args.fix_day2_hotel:
        print(f"\n🏨 Adding Day 2 hotel check-in activity...", file=sys.stderr)

        success, errors = add_day2_hotel_checkin(timeline_data, trip_dir)

        if not success:
            print(f"❌ Failed to add Day 2 hotel check-in:", file=sys.stderr)
            for error in errors:
                print(f"   {error}", file=sys.stderr)
            sys.exit(1)

        day2_timeline = timeline_data['data']['days'][1]['timeline']
        print(f"✅ Day 2 hotel check-in added", file=sys.stderr)
        print(f"   Day 2 now has {len(day2_timeline)} activities", file=sys.stderr)

    # Dry-run mode: show changes and exit
    if args.dry_run:
        print(f"\n🔍 DRY RUN MODE - Changes not saved", file=sys.stderr)
        print(f"\nDay 1 activities (sorted by time):", file=sys.stderr)

        sorted_activities = sorted(
            day1_timeline.items(),
            key=lambda x: time_to_minutes(x[1]['start_time'])
        )

        for name, data in sorted_activities:
            print(f"  {data['start_time']}-{data['end_time']}: {name}", file=sys.stderr)

        if args.fix_day2_hotel:
            print(f"\nDay 2 activities (first 5):", file=sys.stderr)
            day2_timeline = timeline_data['data']['days'][1]['timeline']
            sorted_day2 = sorted(
                day2_timeline.items(),
                key=lambda x: time_to_minutes(x[1]['start_time'])
            )[:5]

            for name, data in sorted_day2:
                print(f"  {data['start_time']}-{data['end_time']}: {name}", file=sys.stderr)

        sys.exit(0)

    # Save using scripts/save.py
    print(f"\n💾 Saving merged timeline using scripts/save.py...", file=sys.stderr)

    if not save_timeline_with_savepy(args.trip, timeline_data):
        print(f"❌ Save failed", file=sys.stderr)
        sys.exit(1)

    print(f"\n✅ Merge complete!", file=sys.stderr)
    print(f"   Day 1: {original_day1_count} → {new_day1_count} activities", file=sys.stderr)

    if args.fix_day2_hotel:
        print(f"   Day 2: Hotel check-in added", file=sys.stderr)

    print(f"\n📋 Next steps:", file=sys.stderr)
    print(f"  1. Verify merge: jq '.data.days[0].timeline | length' {trip_dir / 'timeline.json'}", file=sys.stderr)
    print(f"  2. Validate: python3 scripts/plan-validate.py {trip_dir} --agent timeline", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
