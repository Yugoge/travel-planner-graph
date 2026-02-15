#!/usr/bin/env python3
"""
Fix Day 2 Hotel Check-in Script
================================
Add missing hotel check-in activity to Day 2 timeline from accommodation.json.

Usage:
    python3 scripts/fix-day2-hotel-checkin.py --trip TRIP_SLUG
    python3 scripts/fix-day2-hotel-checkin.py --trip TRIP_SLUG --dry-run

Design:
    - Reads accommodation.json Day 2
    - Extracts hotel check-in time (14:00)
    - Inserts into Day 2 timeline
    - Uses scripts/save.py for final save
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SAVE_PY = SCRIPTS_DIR / "save.py"

# i18n constants
CHECKIN_TEXT_ZH = "办理入住"


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file."""
    try:
        with open(filepath, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to read {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def save_timeline_with_savepy(trip_slug: str, timeline_data: Dict[str, Any]) -> bool:
    """Save timeline using scripts/save.py."""
    # Use tempfile to avoid collision risks
    temp_fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="fix_day2_hotel_")
    temp_file = Path(temp_path)

    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(timeline_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Failed to create temp file: {e}", file=sys.stderr)
        return False

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

    parser = argparse.ArgumentParser(description="Add Day 2 hotel check-in to timeline")
    parser.add_argument("--trip", required=True, help="Trip slug")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")

    args = parser.parse_args()

    trip_dir = DATA_DIR / args.trip

    if not trip_dir.exists():
        print(f"❌ Trip directory not found: {trip_dir}", file=sys.stderr)
        sys.exit(1)

    # Load files
    print("📖 Loading accommodation.json and timeline.json...", file=sys.stderr)
    accommodation_data = load_json(trip_dir / "accommodation.json")
    timeline_data = load_json(trip_dir / "timeline.json")

    # Get Day 2 accommodation details
    if len(accommodation_data['data']['days']) < 2:
        print("❌ accommodation.json has less than 2 days", file=sys.stderr)
        sys.exit(1)

    day2_accom = accommodation_data['data']['days'][1]
    accom_info = day2_accom.get('accommodation', {})

    if not accom_info:
        print("❌ Day 2 has no accommodation info", file=sys.stderr)
        sys.exit(1)

    hotel_name_base = accom_info.get('name_base', 'Hotel')
    hotel_name_local = accom_info.get('name_local', '')
    check_in_time = accom_info.get('check_in')

    if not check_in_time:
        print("❌ Day 2 accommodation has no check_in time", file=sys.stderr)
        sys.exit(1)

    print(f"   Hotel: {hotel_name_base} ({hotel_name_local})", file=sys.stderr)
    print(f"   Check-in: {check_in_time}", file=sys.stderr)

    # Get Day 2 timeline
    if len(timeline_data['data']['days']) < 2:
        print("❌ timeline.json has less than 2 days", file=sys.stderr)
        sys.exit(1)

    day2_timeline = timeline_data['data']['days'][1]['timeline']

    # Check if already exists
    existing_checkin = [k for k in day2_timeline.keys() if 'check-in' in k.lower() and 'xinghe' in k.lower() or 'hotel check-in at bazhong' in k.lower()]

    if existing_checkin:
        print(f"✓ Day 2 already has hotel check-in: {existing_checkin[0]}", file=sys.stderr)
        sys.exit(0)

    # Create hotel check-in activity
    activity_name = f"Hotel check-in at {hotel_name_base}"
    activity_data = {
        'start_time': check_in_time,
        'end_time': check_in_time,
        'duration_minutes': 0
    }

    if hotel_name_local:
        activity_data['name_local'] = f"{hotel_name_local}{CHECKIN_TEXT_ZH}"

    print(f"\n➕ Adding: {activity_name} at {check_in_time}", file=sys.stderr)

    # Add to timeline
    day2_timeline[activity_name] = activity_data

    if args.dry_run:
        print(f"\n🔍 DRY RUN - Changes not saved", file=sys.stderr)
        print(f"   Would add: {activity_name}", file=sys.stderr)
        print(f"   Data: {activity_data}", file=sys.stderr)
        sys.exit(0)

    # Save
    print(f"\n💾 Saving timeline using scripts/save.py...", file=sys.stderr)

    if not save_timeline_with_savepy(args.trip, timeline_data):
        sys.exit(1)

    print(f"\n✅ Day 2 hotel check-in added successfully", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
