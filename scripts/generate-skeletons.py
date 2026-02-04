#!/usr/bin/env python3
"""Generate requirements-skeleton.json and plan-skeleton.json from command-line parameters.

Addresses root cause from dev-20260204-141257: Orchestrator architectural constraint
prevents using Write tool. This script allows orchestrator to delegate file creation
to Bash tool, maintaining architectural separation.

Usage:
    generate-skeletons.py --destination-slug <slug> --dates <start> <end> \\
                          --duration <days> --travelers <count> --budget <amount> \\
                          --preferences <json> --days <json>

Example:
    generate-skeletons.py \\
        --destination-slug "beijing-20260204-145508" \\
        --dates "2026-03-15" "2026-03-24" \\
        --duration 10 \\
        --travelers "2 adults" \\
        --budget "$3000 per person" \\
        --preferences '{"accommodation": "mid-range", "dietary": "vegetarian", "pace": "moderate"}' \\
        --days '[{"day": 1, "date": "2026-03-15", "location": "Beijing", "user_plans": ["Great Wall", "Peking Duck"]}]'
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def validate_preferences(preferences_str: str) -> Dict[str, Any]:
    """Validate and parse preferences JSON string.

    Args:
        preferences_str: JSON string containing preferences dict

    Returns:
        Parsed preferences dictionary

    Raises:
        ValueError: If JSON is invalid or not a dict
    """
    try:
        preferences = json.loads(preferences_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in preferences: {e}")

    if not isinstance(preferences, dict):
        raise ValueError("Preferences must be a JSON object (dict)")

    return preferences


def validate_days(days_str: str) -> List[Dict[str, Any]]:
    """Validate and parse days JSON string.

    Args:
        days_str: JSON string containing days array

    Returns:
        Parsed days list

    Raises:
        ValueError: If JSON is invalid or not a list
    """
    try:
        days = json.loads(days_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in days: {e}")

    if not isinstance(days, list):
        raise ValueError("Days must be a JSON array (list)")

    if not days:
        raise ValueError("Days array cannot be empty")

    # Validate required fields in each day
    for i, day in enumerate(days):
        if not isinstance(day, dict):
            raise ValueError(f"Day {i} must be an object (dict)")

        required_fields = ['day', 'date', 'location']
        for field in required_fields:
            if field not in day:
                raise ValueError(f"Day {i} missing required field: {field}")

    return days


def generate_requirements_skeleton(
    dates_start: str,
    dates_end: str,
    duration_days: int,
    travelers: str,
    budget: str,
    preferences: Dict[str, Any],
    days: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate requirements-skeleton.json structure.

    Args:
        dates_start: Start date (YYYY-MM-DD)
        dates_end: End date (YYYY-MM-DD)
        duration_days: Trip duration in days
        travelers: Traveler description (e.g., "2 adults")
        budget: Budget description (e.g., "$3000 per person")
        preferences: Preferences dict (accommodation, dietary, pace, etc.)
        days: Array of day objects with day, date, location, user_plans

    Returns:
        Requirements skeleton dictionary
    """
    requirements = {
        "trip_summary": {
            "dates": f"{dates_start} to {dates_end}",
            "duration_days": duration_days,
            "travelers": travelers,
            "budget": budget,
            "preferences": preferences
        },
        "days": days
    }

    return requirements


def detect_location_changes(days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect location changes between consecutive days.

    Args:
        days: List of day objects with location field

    Returns:
        Updated days list with location_change objects added
    """
    if len(days) < 2:
        # Single day trip - no location changes
        for day in days:
            day['location_change'] = None
        return days

    updated_days = []
    prev_location = None

    for i, day in enumerate(days):
        # Copy day data
        updated_day = day.copy()

        current_location = day.get('location', '')

        # Check for multi-location day (travel day) with '→' notation
        if '→' in current_location:
            parts = current_location.split('→')
            from_loc = parts[0].strip()
            to_loc = parts[1].strip()

            updated_day['location_change'] = {
                "from": from_loc,
                "to": to_loc,
                "method": "TBD",
                "departure_time": "",
                "arrival_time": "",
                "cost": 0,
                "booking_required": True
            }
            # Update location to destination
            updated_day['location'] = to_loc
            prev_location = to_loc

        elif i > 0 and prev_location and prev_location != current_location:
            # Location changed from previous day
            updated_day['location_change'] = {
                "from": prev_location,
                "to": current_location,
                "method": "TBD",
                "departure_time": "",
                "arrival_time": "",
                "cost": 0,
                "booking_required": True
            }
            prev_location = current_location

        else:
            # No location change
            updated_day['location_change'] = None
            if i == 0:
                prev_location = current_location

        updated_days.append(updated_day)

    return updated_days


def generate_plan_skeleton(
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate plan-skeleton.json structure from requirements.

    Args:
        requirements: Requirements skeleton dictionary

    Returns:
        Plan skeleton dictionary with initialized fields and location changes
    """
    days = []
    prev_location = None

    for day_req in requirements['days']:
        day_num = day_req['day']
        date = day_req['date']
        location = day_req['location']
        user_plans = day_req.get('user_plans', [])

        # Initialize day object with all required fields
        day_obj = {
            "day": day_num,
            "date": date,
            "location": location,
            "location_change": None,  # Will be set by detect_location_changes
            "user_requirements": user_plans,
            "breakfast": {"name": "", "location": "", "cost": 0, "notes": ""},
            "lunch": {"name": "", "location": "", "cost": 0, "notes": ""},
            "dinner": {"name": "", "location": "", "cost": 0, "notes": ""},
            "accommodation": {
                "name": "",
                "location": "",
                "cost": 0,
                "check_in": "",
                "check_out": "",
                "booking_required": True
            },
            "attractions": [],
            "entertainment": [],
            "shopping": [],
            "free_time": [],
            "timeline": {},
            "budget": {
                "meals": 0,
                "accommodation": 0,
                "activities": 0,
                "shopping": 0,
                "transportation": 0,
                "total": 0
            }
        }

        days.append(day_obj)

    # Detect location changes
    days_with_changes = detect_location_changes(days)

    plan_skeleton = {
        "trip_summary": requirements['trip_summary'],
        "days": days_with_changes,
        "emergency_info": {
            "hospitals": [],
            "police_stations": [],
            "embassy": None
        }
    }

    return plan_skeleton


def ensure_directory_exists(file_path: Path) -> None:
    """Ensure parent directory exists for file path.

    Args:
        file_path: Path object for target file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate requirements and plan skeleton files from parameters',
        epilog='Root cause: Orchestrator Write/Edit prohibition requires delegation mechanism',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--destination-slug',
        required=True,
        help='Destination slug (e.g., beijing-20260204-145508)'
    )
    parser.add_argument(
        '--dates',
        nargs=2,
        required=True,
        metavar=('START', 'END'),
        help='Start and end dates (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        required=True,
        help='Trip duration in days'
    )
    parser.add_argument(
        '--travelers',
        required=True,
        help='Traveler description (e.g., "2 adults")'
    )
    parser.add_argument(
        '--budget',
        required=True,
        help='Budget description (e.g., "$3000 per person")'
    )
    parser.add_argument(
        '--preferences',
        required=True,
        help='Preferences as JSON string (e.g., \'{"accommodation": "mid-range"}\')'
    )
    parser.add_argument(
        '--days',
        required=True,
        help='Days array as JSON string with day, date, location, user_plans'
    )
    parser.add_argument(
        '--output-dir',
        default=None,
        help='Output directory (default: data/{destination-slug}/)'
    )

    args = parser.parse_args()

    try:
        # Validate and parse JSON parameters
        preferences = validate_preferences(args.preferences)
        days = validate_days(args.days)

        # Determine output directory
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            output_dir = Path(__file__).parent.parent / 'data' / args.destination_slug

        # Ensure directory exists
        ensure_directory_exists(output_dir / 'placeholder.txt')

        # Generate requirements skeleton
        requirements = generate_requirements_skeleton(
            dates_start=args.dates[0],
            dates_end=args.dates[1],
            duration_days=args.duration,
            travelers=args.travelers,
            budget=args.budget,
            preferences=preferences,
            days=days
        )

        # Write requirements skeleton
        requirements_path = output_dir / 'requirements-skeleton.json'
        with open(requirements_path, 'w', encoding='utf-8') as f:
            json.dump(requirements, f, indent=2, ensure_ascii=False)

        print(f"✓ Requirements skeleton created: {requirements_path}")

        # Generate plan skeleton
        plan_skeleton = generate_plan_skeleton(requirements)

        # Write plan skeleton
        plan_path = output_dir / 'plan-skeleton.json'
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan_skeleton, f, indent=2, ensure_ascii=False)

        print(f"✓ Plan skeleton created: {plan_path}")

        # Report location changes detected
        location_changes = sum(1 for d in plan_skeleton['days'] if d['location_change'])
        print(f"✓ Detected {location_changes} location changes")
        print(f"✓ Initialized {len(plan_skeleton['days'])} days with all required fields")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
