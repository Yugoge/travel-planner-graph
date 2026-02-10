#!/usr/bin/env python3
"""Incrementally update requirements-skeleton.json and plan-skeleton.json.

Performs atomic mutations on existing skeleton files without regenerating from
scratch. Used by the /plan orchestrator for Type 2 Major Restructure operations
where the orchestrator is forbidden from directly editing data files.

Usage:
    update-skeleton.py --destination-slug <slug> <operation> [arguments]

Operations:
    --update-day N --location "City"          Change day N's location
    --update-day N --add-plan "Plan text"     Add a user plan to day N
    --update-day N --remove-plan "Plan text"  Remove matching plan from day N
    --update-day N --set-plans '[...]'        Replace all plans for day N
    --update-budget "amount"                  Update trip budget
    --update-travelers "description"          Update travelers field
    --update-preferences '{...}'             Update preferences object
    --add-day --day N --date YYYY-MM-DD --location "City" --plans '[...]'
    --remove-day N                            Remove day N, re-number remaining
    --update-dates "YYYY-MM-DD" "YYYY-MM-DD" Update trip start/end dates
    --set-note "key" "value"                  Set a supplemental note
    --remove-note "key"                       Remove a supplemental note
    --list-notes                              List all supplemental notes

Exit codes:
    0 = success
    1 = validation error (invalid day, file not found, bad JSON)
    2 = unexpected error
"""

import argparse
import copy
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import detect_location_changes from generate-skeletons.py
# Add parent dir to sys.path so we can import from sibling script
_scripts_dir = Path(__file__).parent
sys.path.insert(0, str(_scripts_dir))

try:
    from importlib import util as importlib_util

    spec = importlib_util.spec_from_file_location(
        "generate_skeletons",
        _scripts_dir / "generate-skeletons.py"
    )
    generate_skeletons = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(generate_skeletons)
    detect_location_changes = generate_skeletons.detect_location_changes
except Exception:
    # Fallback: duplicate the function if import fails
    def detect_location_changes(days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect location changes between consecutive days."""
        if len(days) < 2:
            for day in days:
                day['location_change'] = None
            return days

        updated_days = []
        prev_location = None

        for i, day in enumerate(days):
            updated_day = day.copy()
            current_location = day.get('location', '')

            if '\u2192' in current_location:
                parts = current_location.split('\u2192')
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
                updated_day['location'] = to_loc
                prev_location = to_loc
            elif i > 0 and prev_location and prev_location != current_location:
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
                updated_day['location_change'] = None
                if i == 0:
                    prev_location = current_location

            updated_days.append(updated_day)

        return updated_days


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Write JSON data to file.

    Args:
        path: Target file path
        data: Data to serialize
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def find_day_index(days: List[Dict[str, Any]], day_number: int) -> int:
    """Find the index of a day by its day number.

    Args:
        days: List of day objects
        day_number: The day number to find

    Returns:
        Index of the day in the list

    Raises:
        ValueError: If day number not found
    """
    for i, day in enumerate(days):
        if day.get('day') == day_number:
            return i

    available = [d.get('day') for d in days]
    raise ValueError(
        f"Day {day_number} not found. Available days: {available}"
    )


def redetect_location_changes_preserving_data(
    plan_days: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Re-run location change detection while preserving existing plan day data.

    The detect_location_changes function uses .copy() which is shallow.
    We need to preserve all existing fields (meals, accommodation, etc.)
    while only updating the location_change field.

    Args:
        plan_days: Plan skeleton day objects with full data

    Returns:
        Updated plan days with recalculated location_change fields
    """
    # Build a minimal list for detection (only needs location field)
    minimal_days = [
        {"day": d["day"], "location": d["location"]}
        for d in plan_days
    ]
    detected = detect_location_changes(minimal_days)

    # Apply detected location_change back to original days
    for i, plan_day in enumerate(plan_days):
        plan_day['location_change'] = detected[i]['location_change']
        # Also update location in case arrow notation was resolved
        plan_day['location'] = detected[i]['location']

    return plan_days


def op_update_day_location(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    day_number: int,
    new_location: str
) -> List[str]:
    """Change a day's location in both skeleton files.

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        day_number: Day to update
        new_location: New location string

    Returns:
        List of change summary messages
    """
    changes = []

    # Update requirements-skeleton
    req_idx = find_day_index(req['days'], day_number)
    old_location = req['days'][req_idx].get('location', '')
    req['days'][req_idx]['location'] = new_location
    changes.append(
        f"Updated day {day_number} location: \"{old_location}\" -> \"{new_location}\""
    )

    # Update plan-skeleton
    plan_idx = find_day_index(plan['days'], day_number)
    plan['days'][plan_idx]['location'] = new_location

    # Re-detect location changes for ALL days in both files
    req['days'] = detect_location_changes(req['days'])
    plan['days'] = redetect_location_changes_preserving_data(plan['days'])

    loc_count = sum(1 for d in plan['days'] if d.get('location_change'))
    changes.append(f"Re-detected location changes: {loc_count} found")

    return changes


def op_add_plan(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    day_number: int,
    plan_text: str
) -> List[str]:
    """Add a user plan to a day.

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        day_number: Day to update
        plan_text: Plan text to append

    Returns:
        List of change summary messages
    """
    changes = []

    req_idx = find_day_index(req['days'], day_number)
    if 'user_plans' not in req['days'][req_idx]:
        req['days'][req_idx]['user_plans'] = []
    req['days'][req_idx]['user_plans'].append(plan_text)

    plan_idx = find_day_index(plan['days'], day_number)
    if 'user_requirements' not in plan['days'][plan_idx]:
        plan['days'][plan_idx]['user_requirements'] = []
    plan['days'][plan_idx]['user_requirements'].append(plan_text)

    changes.append(f"Added plan to day {day_number}: \"{plan_text}\"")
    return changes


def op_remove_plan(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    day_number: int,
    plan_text: str
) -> List[str]:
    """Remove a matching user plan from a day (case-insensitive contains).

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        day_number: Day to update
        plan_text: Text to match (partial, case-insensitive)

    Returns:
        List of change summary messages
    """
    changes = []
    search_lower = plan_text.lower()

    # Remove from requirements-skeleton
    req_idx = find_day_index(req['days'], day_number)
    req_plans = req['days'][req_idx].get('user_plans', [])
    original_count = len(req_plans)
    req['days'][req_idx]['user_plans'] = [
        p for p in req_plans if search_lower not in p.lower()
    ]
    removed_req = original_count - len(req['days'][req_idx]['user_plans'])

    # Remove from plan-skeleton
    plan_idx = find_day_index(plan['days'], day_number)
    plan_reqs = plan['days'][plan_idx].get('user_requirements', [])
    original_count = len(plan_reqs)
    plan['days'][plan_idx]['user_requirements'] = [
        p for p in plan_reqs if search_lower not in p.lower()
    ]
    removed_plan = original_count - len(plan['days'][plan_idx]['user_requirements'])

    if removed_req == 0 and removed_plan == 0:
        changes.append(
            f"No matching plans found for \"{plan_text}\" in day {day_number}"
        )
    else:
        changes.append(
            f"Removed {max(removed_req, removed_plan)} plan(s) matching "
            f"\"{plan_text}\" from day {day_number}"
        )

    return changes


def op_set_plans(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    day_number: int,
    plans_json: str
) -> List[str]:
    """Replace all user plans for a day.

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        day_number: Day to update
        plans_json: JSON array string of new plans

    Returns:
        List of change summary messages
    """
    try:
        new_plans = json.loads(plans_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for --set-plans: {e}")

    if not isinstance(new_plans, list):
        raise ValueError("--set-plans must be a JSON array")

    for i, item in enumerate(new_plans):
        if not isinstance(item, str):
            raise ValueError(f"Plan item {i} must be a string, got {type(item).__name__}")

    changes = []

    req_idx = find_day_index(req['days'], day_number)
    old_count = len(req['days'][req_idx].get('user_plans', []))
    req['days'][req_idx]['user_plans'] = new_plans

    plan_idx = find_day_index(plan['days'], day_number)
    plan['days'][plan_idx]['user_requirements'] = new_plans

    changes.append(
        f"Replaced day {day_number} plans: {old_count} -> {len(new_plans)} items"
    )
    return changes


def op_update_budget(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    new_budget: str
) -> List[str]:
    """Update the trip budget in both files.

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        new_budget: New budget string

    Returns:
        List of change summary messages
    """
    old_budget = req.get('trip_summary', {}).get('budget', '')
    req.setdefault('trip_summary', {})['budget'] = new_budget
    plan.setdefault('trip_summary', {})['budget'] = new_budget

    return [f"Updated budget: \"{old_budget}\" -> \"{new_budget}\""]


def op_update_travelers(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    new_travelers: str
) -> List[str]:
    """Update the travelers field in both files.

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        new_travelers: New travelers description

    Returns:
        List of change summary messages
    """
    old_travelers = req.get('trip_summary', {}).get('travelers', '')
    req.setdefault('trip_summary', {})['travelers'] = new_travelers
    plan.setdefault('trip_summary', {})['travelers'] = new_travelers

    return [f"Updated travelers: \"{old_travelers}\" -> \"{new_travelers}\""]


def op_update_preferences(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    prefs_json: str
) -> List[str]:
    """Update the preferences object in both files (merge, not replace).

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        prefs_json: JSON object string with preference keys to update

    Returns:
        List of change summary messages
    """
    try:
        new_prefs = json.loads(prefs_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for --update-preferences: {e}")

    if not isinstance(new_prefs, dict):
        raise ValueError("--update-preferences must be a JSON object")

    changes = []

    req_prefs = req.setdefault('trip_summary', {}).setdefault('preferences', {})
    plan_prefs = plan.setdefault('trip_summary', {}).setdefault('preferences', {})

    for key, value in new_prefs.items():
        old_val = req_prefs.get(key, '<not set>')
        req_prefs[key] = value
        plan_prefs[key] = value
        changes.append(f"Updated preference '{key}': \"{old_val}\" -> \"{value}\"")

    return changes


def parse_date(date_str: str) -> date:
    """Parse a YYYY-MM-DD date string.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Parsed date object

    Raises:
        ValueError: If date string is not valid YYYY-MM-DD
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD."
        )


def op_update_dates(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    start_date_str: str,
    end_date_str: str
) -> List[str]:
    """Update trip dates and recalculate duration in both skeleton files.

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        start_date_str: New start date (YYYY-MM-DD)
        end_date_str: New end date (YYYY-MM-DD)

    Returns:
        List of change summary messages

    Raises:
        ValueError: If dates are invalid or end is before start
    """
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)

    if end_date < start_date:
        raise ValueError(
            f"End date ({end_date_str}) cannot be before "
            f"start date ({start_date_str})"
        )

    new_dates_str = f"{start_date_str} to {end_date_str}"
    # Duration is inclusive of both start and end dates
    new_duration = (end_date - start_date).days + 1

    changes = []

    # Read old values for reporting
    old_dates = req.get('trip_summary', {}).get('dates', '')
    old_duration = req.get('trip_summary', {}).get('duration_days', 0)

    # Update both files
    req.setdefault('trip_summary', {})['dates'] = new_dates_str
    req['trip_summary']['duration_days'] = new_duration
    plan.setdefault('trip_summary', {})['dates'] = new_dates_str
    plan['trip_summary']['duration_days'] = new_duration

    changes.append(f"Updated dates: \"{old_dates}\" -> \"{new_dates_str}\"")
    changes.append(
        f"Updated duration: {old_duration} -> {new_duration} days"
    )

    return changes


def op_set_note(
    req: Dict[str, Any],
    key: str,
    value: str
) -> List[str]:
    """Set a supplemental note in requirements-skeleton.json.

    Creates the supplemental_notes dict if it doesn't exist.

    Args:
        req: Requirements skeleton data
        key: Note key name
        value: Note value text

    Returns:
        List of change summary messages
    """
    notes = req.setdefault('supplemental_notes', {})
    is_update = key in notes
    old_value = notes.get(key, '')
    notes[key] = value

    if is_update:
        return [f"Updated note '{key}': \"{old_value}\" -> \"{value}\""]
    return [f"Set note '{key}': \"{value}\""]


def op_remove_note(
    req: Dict[str, Any],
    key: str
) -> List[str]:
    """Remove a supplemental note from requirements-skeleton.json.

    Args:
        req: Requirements skeleton data
        key: Note key name to remove

    Returns:
        List of change summary messages

    Raises:
        ValueError: If key doesn't exist in supplemental_notes
    """
    notes = req.get('supplemental_notes', {})
    if key not in notes:
        available = list(notes.keys()) if notes else []
        raise ValueError(
            f"Note key '{key}' not found in supplemental_notes. "
            f"Available keys: {available}"
        )

    removed_value = notes.pop(key)
    return [f"Removed note '{key}' (was: \"{removed_value}\")"]


def op_list_notes(req: Dict[str, Any]) -> List[str]:
    """List all supplemental notes from requirements-skeleton.json.

    Args:
        req: Requirements skeleton data

    Returns:
        List of formatted note entries (or message if none exist)
    """
    notes = req.get('supplemental_notes', {})
    if not notes:
        return ["No supplemental_notes found"]

    lines = [f"supplemental_notes ({len(notes)} entries):"]
    for key, value in notes.items():
        # Truncate long values for display
        display_value = value if len(value) <= 120 else value[:117] + "..."
        lines.append(f"  {key}: \"{display_value}\"")

    return lines


def make_empty_plan_day(
    day_number: int,
    date: str,
    location: str,
    user_plans: List[str]
) -> Dict[str, Any]:
    """Create a new empty plan-skeleton day object with all required fields.

    Args:
        day_number: Day number
        date: Date string (YYYY-MM-DD)
        location: Location name
        user_plans: User requirement strings

    Returns:
        Complete plan day object with empty slots
    """
    return {
        "day": day_number,
        "date": date,
        "location": location,
        "location_change": None,
        "user_requirements": user_plans,
        "breakfast": {"name": "", "location": "", "cost": 0, "notes": ""},
        "lunch": {"name": "", "location": "", "cost": 0, "notes": ""},
        "dinner": {"name": "", "location": "", "cost": 0, "notes": ""},
        "accommodation": {
            "name": "", "location": "", "cost": 0,
            "check_in": "", "check_out": "", "booking_required": True
        },
        "attractions": [],
        "entertainment": [],
        "shopping": [],
        "free_time": [],
        "timeline": {},
        "budget": {
            "meals": 0, "accommodation": 0, "activities": 0,
            "shopping": 0, "transportation": 0, "total": 0
        }
    }


def op_add_day(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    day_number: int,
    date: str,
    location: str,
    plans_json: Optional[str]
) -> List[str]:
    """Add a new day to both skeleton files.

    Inserts the day at the correct position based on day number, then
    re-detects location changes.

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        day_number: Day number for the new day
        date: Date string (YYYY-MM-DD)
        location: Location name
        plans_json: Optional JSON array string of user plans

    Returns:
        List of change summary messages
    """
    user_plans: List[str] = []
    if plans_json:
        try:
            user_plans = json.loads(plans_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for --plans: {e}")
        if not isinstance(user_plans, list):
            raise ValueError("--plans must be a JSON array")

    changes = []

    # Check for duplicate day number
    existing_days = [d.get('day') for d in req.get('days', [])]
    if day_number in existing_days:
        raise ValueError(
            f"Day {day_number} already exists. Use --update-day to modify it."
        )

    # Create requirements day
    req_day = {
        "day": day_number,
        "date": date,
        "location": location,
        "user_plans": user_plans
    }

    # Create plan day
    plan_day = make_empty_plan_day(day_number, date, location, user_plans)

    # Insert at correct position (sorted by day number)
    req['days'].append(req_day)
    req['days'].sort(key=lambda d: d['day'])

    plan['days'].append(plan_day)
    plan['days'].sort(key=lambda d: d['day'])

    # Update duration_days
    req['trip_summary']['duration_days'] = len(req['days'])
    plan['trip_summary']['duration_days'] = len(plan['days'])

    # Re-detect location changes
    req['days'] = detect_location_changes(req['days'])
    plan['days'] = redetect_location_changes_preserving_data(plan['days'])

    loc_count = sum(1 for d in plan['days'] if d.get('location_change'))
    changes.append(
        f"Added day {day_number} ({date}, {location}) "
        f"with {len(user_plans)} plan(s)"
    )
    changes.append(f"Updated duration_days: {len(req['days'])}")
    changes.append(f"Re-detected location changes: {loc_count} found")

    return changes


def op_remove_day(
    req: Dict[str, Any],
    plan: Dict[str, Any],
    day_number: int
) -> List[str]:
    """Remove a day and re-number remaining days.

    Args:
        req: Requirements skeleton data
        plan: Plan skeleton data
        day_number: Day number to remove

    Returns:
        List of change summary messages
    """
    changes = []

    # Validate day exists in both
    req_idx = find_day_index(req['days'], day_number)
    plan_idx = find_day_index(plan['days'], day_number)

    removed_location = req['days'][req_idx].get('location', 'unknown')

    # Remove from both
    req['days'].pop(req_idx)
    plan['days'].pop(plan_idx)

    # Re-number remaining days sequentially
    for i, day in enumerate(req['days']):
        day['day'] = i + 1
    for i, day in enumerate(plan['days']):
        day['day'] = i + 1

    # Update duration_days
    req['trip_summary']['duration_days'] = len(req['days'])
    plan['trip_summary']['duration_days'] = len(plan['days'])

    # Re-detect location changes
    req['days'] = detect_location_changes(req['days'])
    plan['days'] = redetect_location_changes_preserving_data(plan['days'])

    loc_count = sum(1 for d in plan['days'] if d.get('location_change'))
    changes.append(
        f"Removed day {day_number} ({removed_location})"
    )
    changes.append(
        f"Re-numbered {len(req['days'])} remaining days"
    )
    changes.append(f"Updated duration_days: {len(req['days'])}")
    changes.append(f"Re-detected location changes: {loc_count} found")

    return changes


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all supported operations.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description='Incrementally update skeleton files for travel plans',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --destination-slug my-trip --update-day 3 --location Shanghai\n"
            "  %(prog)s --destination-slug my-trip --update-day 5 --add-plan 'Visit temple'\n"
            "  %(prog)s --destination-slug my-trip --remove-day 22\n"
            "  %(prog)s --destination-slug my-trip --update-budget '$5000 total'\n"
            "  %(prog)s --destination-slug my-trip --update-dates 2026-03-01 2026-03-15\n"
            "  %(prog)s --destination-slug my-trip --set-note diet 'No shellfish'\n"
            "  %(prog)s --destination-slug my-trip --remove-note diet\n"
            "  %(prog)s --destination-slug my-trip --list-notes\n"
        )
    )

    # Required
    parser.add_argument(
        '--destination-slug',
        required=True,
        help='Destination folder slug under data/'
    )

    parser.add_argument(
        '--data-dir',
        default=None,
        help='Override data directory (default: data/{destination-slug}/)'
    )

    # Day-level operations
    parser.add_argument(
        '--update-day',
        type=int,
        metavar='N',
        help='Day number to update (used with --location, --add-plan, --remove-plan, --set-plans)'
    )
    parser.add_argument(
        '--location',
        help='New location for the day (requires --update-day)'
    )
    parser.add_argument(
        '--add-plan',
        help='Plan text to add to the day (requires --update-day)'
    )
    parser.add_argument(
        '--remove-plan',
        help='Plan text to remove by partial match (requires --update-day)'
    )
    parser.add_argument(
        '--set-plans',
        metavar='JSON',
        help='JSON array to replace all plans for the day (requires --update-day)'
    )

    # Trip summary operations
    parser.add_argument(
        '--update-budget',
        metavar='BUDGET',
        help='New budget string'
    )
    parser.add_argument(
        '--update-travelers',
        metavar='TRAVELERS',
        help='New travelers description'
    )
    parser.add_argument(
        '--update-preferences',
        metavar='JSON',
        help='JSON object with preference keys to merge'
    )

    # Add/remove day operations
    parser.add_argument(
        '--add-day',
        action='store_true',
        help='Add a new day (requires --day, --date, --location)'
    )
    parser.add_argument(
        '--day',
        type=int,
        help='Day number for the new day (requires --add-day)'
    )
    parser.add_argument(
        '--date',
        help='Date for the new day YYYY-MM-DD (requires --add-day)'
    )
    parser.add_argument(
        '--plans',
        metavar='JSON',
        help='JSON array of user plans for new day (requires --add-day)'
    )

    parser.add_argument(
        '--remove-day',
        type=int,
        metavar='N',
        help='Day number to remove'
    )

    # Date update operation
    parser.add_argument(
        '--update-dates',
        nargs=2,
        metavar=('START', 'END'),
        help='New trip start and end dates (YYYY-MM-DD YYYY-MM-DD)'
    )

    # Supplemental notes operations (requirements-skeleton.json only)
    parser.add_argument(
        '--set-note',
        nargs=2,
        metavar=('KEY', 'VALUE'),
        help='Set a supplemental note (key and value)'
    )
    parser.add_argument(
        '--remove-note',
        metavar='KEY',
        help='Remove a supplemental note by key'
    )
    parser.add_argument(
        '--list-notes',
        action='store_true',
        help='List all supplemental notes'
    )

    return parser


def validate_args(args: argparse.Namespace) -> str:
    """Validate argument combinations and determine which operation to run.

    Args:
        args: Parsed arguments

    Returns:
        Operation name string

    Raises:
        ValueError: If arguments are invalid or ambiguous
    """
    # Count how many top-level operations are specified
    operations = []

    if args.update_day is not None:
        sub_ops = [args.location, args.add_plan, args.remove_plan, args.set_plans]
        specified = [op for op in sub_ops if op is not None]
        if len(specified) == 0:
            raise ValueError(
                "--update-day requires one of: --location, --add-plan, "
                "--remove-plan, --set-plans"
            )
        if len(specified) > 1:
            raise ValueError(
                "--update-day accepts only one sub-operation at a time"
            )

        if args.location is not None:
            operations.append('update_day_location')
        elif args.add_plan is not None:
            operations.append('add_plan')
        elif args.remove_plan is not None:
            operations.append('remove_plan')
        elif args.set_plans is not None:
            operations.append('set_plans')

    if args.update_budget is not None:
        operations.append('update_budget')
    if args.update_travelers is not None:
        operations.append('update_travelers')
    if args.update_preferences is not None:
        operations.append('update_preferences')

    if args.add_day:
        if args.day is None or args.date is None or args.location is None:
            raise ValueError(
                "--add-day requires --day, --date, and --location"
            )
        # Prevent conflict: --add-day uses --location for the new day,
        # --update-day also uses --location for updating.
        # If --update-day is also set, that's ambiguous.
        if args.update_day is not None:
            raise ValueError(
                "Cannot use --add-day and --update-day simultaneously"
            )
        operations.append('add_day')

    if args.remove_day is not None:
        operations.append('remove_day')

    if args.update_dates is not None:
        operations.append('update_dates')

    if args.set_note is not None:
        operations.append('set_note')
    if args.remove_note is not None:
        operations.append('remove_note')
    if args.list_notes:
        operations.append('list_notes')

    if len(operations) == 0:
        raise ValueError(
            "No operation specified. Use --update-day, --update-budget, "
            "--update-travelers, --update-preferences, --add-day, "
            "--remove-day, --update-dates, --set-note, --remove-note, "
            "or --list-notes"
        )

    # Allow multiple non-conflicting summary updates in one call
    summary_ops = {
        'update_budget', 'update_travelers', 'update_preferences',
        'update_dates'
    }
    non_summary = [op for op in operations if op not in summary_ops]
    summary = [op for op in operations if op in summary_ops]

    if len(non_summary) > 1:
        raise ValueError(
            f"Conflicting operations: {non_summary}. Run them separately."
        )

    if non_summary and summary:
        raise ValueError(
            f"Cannot combine {non_summary[0]} with summary updates. "
            "Run them separately."
        )

    # Return the primary operation (or first summary op if only summaries)
    if non_summary:
        return non_summary[0]

    return 'summary_updates'


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code: 0=success, 1=validation error, 2=unexpected error
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        operation = validate_args(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Resolve data directory
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = Path(__file__).parent.parent / 'data' / args.destination_slug

    req_path = data_dir / 'requirements-skeleton.json'
    plan_path = data_dir / 'plan-skeleton.json'

    # Load both files
    try:
        req = load_json_file(req_path)
        plan = load_json_file(plan_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in skeleton file: {e}", file=sys.stderr)
        return 1

    # Keep backups for atomic write (rollback on partial failure)
    req_backup = copy.deepcopy(req)
    plan_backup = copy.deepcopy(plan)

    try:
        all_changes: List[str] = []

        if operation == 'update_day_location':
            all_changes = op_update_day_location(
                req, plan, args.update_day, args.location
            )

        elif operation == 'add_plan':
            all_changes = op_add_plan(
                req, plan, args.update_day, args.add_plan
            )

        elif operation == 'remove_plan':
            all_changes = op_remove_plan(
                req, plan, args.update_day, args.remove_plan
            )

        elif operation == 'set_plans':
            all_changes = op_set_plans(
                req, plan, args.update_day, args.set_plans
            )

        elif operation == 'update_budget':
            all_changes = op_update_budget(req, plan, args.update_budget)

        elif operation == 'update_travelers':
            all_changes = op_update_travelers(req, plan, args.update_travelers)

        elif operation == 'update_preferences':
            all_changes = op_update_preferences(
                req, plan, args.update_preferences
            )

        elif operation == 'summary_updates':
            # Handle multiple summary updates in one call
            if args.update_budget is not None:
                all_changes.extend(
                    op_update_budget(req, plan, args.update_budget)
                )
            if args.update_travelers is not None:
                all_changes.extend(
                    op_update_travelers(req, plan, args.update_travelers)
                )
            if args.update_preferences is not None:
                all_changes.extend(
                    op_update_preferences(req, plan, args.update_preferences)
                )
            if args.update_dates is not None:
                all_changes.extend(
                    op_update_dates(
                        req, plan,
                        args.update_dates[0], args.update_dates[1]
                    )
                )

        elif operation == 'add_day':
            all_changes = op_add_day(
                req, plan,
                args.day, args.date, args.location, args.plans
            )

        elif operation == 'remove_day':
            all_changes = op_remove_day(req, plan, args.remove_day)

        elif operation == 'update_dates':
            all_changes = op_update_dates(
                req, plan, args.update_dates[0], args.update_dates[1]
            )

        elif operation == 'set_note':
            all_changes = op_set_note(req, args.set_note[0], args.set_note[1])

        elif operation == 'remove_note':
            all_changes = op_remove_note(req, args.remove_note)

        elif operation == 'list_notes':
            all_changes = op_list_notes(req)

        # Determine which files were modified
        # Note operations only affect requirements-skeleton.json
        req_only_ops = {'set_note', 'remove_note'}
        list_only_ops = {'list_notes'}
        writes_req = operation not in list_only_ops
        writes_plan = operation not in req_only_ops and operation not in list_only_ops

        # Write files
        if writes_req:
            save_json_file(req_path, req)
        if writes_plan:
            save_json_file(plan_path, plan)

        # Print change summary
        for change in all_changes:
            print(f"\u2713 {change}")
        if writes_req:
            print(f"\u2713 Updated {req_path.name}")
        if writes_plan:
            print(f"\u2713 Updated {plan_path.name}")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        # Attempt rollback: restore original files
        try:
            save_json_file(req_path, req_backup)
            save_json_file(plan_path, plan_backup)
            print("Rolled back files to original state.", file=sys.stderr)
        except Exception:
            print(
                "WARNING: Rollback failed. Files may be in inconsistent state.",
                file=sys.stderr
            )
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
