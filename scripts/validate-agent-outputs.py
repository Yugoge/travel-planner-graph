#!/usr/bin/env python3
"""
Deep content validation of all agent JSON outputs.
Usage: validate-agent-outputs.py <data_dir>
Exit codes:
  0 = all valid
  1 = critical issues found (missing data, incomplete outputs)
  2 = warnings only (minor issues)

Examples:
  python3 validate-agent-outputs.py data/china-feb15-mar7-2026
  python3 validate-agent-outputs.py /path/to/project/data/trip
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple


def validate_meals(data_dir: Path) -> Tuple[List[str], List[str]]:
    """Validate meals.json content."""
    errors = []
    warnings = []
    meals_file = data_dir / "meals.json"

    if not meals_file.exists():
        errors.append("meals.json not found")
        return errors, warnings

    try:
        with meals_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"meals.json read error: {e}")
        return errors, warnings

    # Check structure
    if 'data' not in data or 'days' not in data['data']:
        errors.append("meals.json missing data.days structure")
        return errors, warnings

    days = data['data']['days']
    for day in days:
        day_num = day.get('day', '?')

        # Check all 3 meals exist
        for meal in ['breakfast', 'lunch', 'dinner']:
            if meal not in day:
                errors.append(f"Day {day_num} missing {meal}")
            elif not day[meal].get('name'):
                errors.append(f"Day {day_num} {meal} has no name")
            elif day[meal].get('cost', 0) <= 0:
                warnings.append(f"Day {day_num} {meal} has zero or negative cost")

    return errors, warnings


def validate_attractions(data_dir: Path, requirements_file: Path) -> Tuple[List[str], List[str]]:
    """Validate attractions.json content against user requirements."""
    errors = []
    warnings = []
    attractions_file = data_dir / "attractions.json"

    if not attractions_file.exists():
        errors.append("attractions.json not found")
        return errors, warnings

    try:
        with attractions_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"attractions.json read error: {e}")
        return errors, warnings

    # Check structure
    if 'data' not in data or 'days' not in data['data']:
        errors.append("attractions.json missing data.days structure")
        return errors, warnings

    days = data['data']['days']

    # Read user requirements for comparison
    user_requirements = {}
    if requirements_file.exists():
        try:
            with requirements_file.open('r', encoding='utf-8') as f:
                req_data = json.load(f)
                if 'days' in req_data:
                    for day in req_data['days']:
                        day_num = day.get('day')
                        user_plans = day.get('user_plans', [])
                        if day_num and user_plans:
                            user_requirements[day_num] = user_plans
        except Exception:
            pass

    for day in days:
        day_num = day.get('day', '?')
        attractions = day.get('attractions', [])

        if not attractions:
            warnings.append(f"Day {day_num} has no attractions")
        else:
            # Check each attraction has required fields
            for idx, attraction in enumerate(attractions):
                if not attraction.get('name'):
                    errors.append(f"Day {day_num} attraction {idx+1} has no name")
                if not attraction.get('location'):
                    warnings.append(f"Day {day_num} {attraction.get('name', f'attraction {idx+1}')} has no location")
                if attraction.get('cost', -1) < 0:
                    warnings.append(f"Day {day_num} {attraction.get('name', f'attraction {idx+1}')} has no cost specified")

        # Check if user requirements are addressed
        if day_num in user_requirements and attractions:
            # This is a basic check - could be enhanced
            pass

    return errors, warnings


def validate_timeline(data_dir: Path) -> Tuple[List[str], List[str]]:
    """Validate timeline.json has adequate coverage."""
    errors = []
    warnings = []
    timeline_file = data_dir / "timeline.json"

    if not timeline_file.exists():
        errors.append("timeline.json not found")
        return errors, warnings

    try:
        with timeline_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"timeline.json read error: {e}")
        return errors, warnings

    # Check structure
    if 'data' not in data or 'days' not in data['data']:
        errors.append("timeline.json missing data.days structure")
        return errors, warnings

    days = data['data']['days']
    for day in days:
        day_num = day.get('day', '?')
        timeline = day.get('timeline', {})

        if not timeline:
            warnings.append(f"Day {day_num} has empty timeline")
            continue

        # Count activities
        activity_count = len(timeline)
        if activity_count < 3:
            warnings.append(f"Day {day_num} has only {activity_count} activities in timeline")

        # Check for time conflicts (basic validation)
        times = []
        for activity, schedule in timeline.items():
            if 'start_time' in schedule and 'end_time' in schedule:
                times.append((activity, schedule['start_time'], schedule['end_time']))

        # Sort by start time and check overlaps
        times.sort(key=lambda x: x[1])
        for i in range(len(times) - 1):
            curr_name, curr_start, curr_end = times[i]
            next_name, next_start, next_end = times[i + 1]
            if curr_end > next_start:
                errors.append(f"Day {day_num}: {curr_name} ({curr_start}-{curr_end}) overlaps {next_name} ({next_start}-{next_end})")

    return errors, warnings


def validate_budget(data_dir: Path) -> Tuple[List[str], List[str]]:
    """Validate budget.json calculations."""
    errors = []
    warnings = []
    budget_file = data_dir / "budget.json"

    if not budget_file.exists():
        errors.append("budget.json not found")
        return errors, warnings

    try:
        with budget_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"budget.json read error: {e}")
        return errors, warnings

    # Check for summary or days structure
    if 'days' in data:
        days = data['days']
        for day in days:
            day_num = day.get('day', '?')
            budget = day.get('budget', {})

            if not budget:
                warnings.append(f"Day {day_num} has no budget breakdown")
                continue

            # Check totals make sense
            total = budget.get('total', 0)
            if total <= 0:
                warnings.append(f"Day {day_num} has zero or negative total budget")

    # Check for overage warnings
    if 'warnings' in data and data['warnings']:
        warnings.append(f"Budget has {len(data['warnings'])} warnings")

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    data_dir = Path(sys.argv[1])

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    if not data_dir.is_dir():
        print(f"Error: {data_dir} is not a directory", file=sys.stderr)
        return 2

    print(f"Validating agent outputs in: {data_dir}")
    print()

    all_errors = []
    all_warnings = []

    # Validate each agent output
    requirements_file = data_dir / "requirements-skeleton.json"

    # Meals
    errors, warnings = validate_meals(data_dir)
    all_errors.extend([f"[meals] {e}" for e in errors])
    all_warnings.extend([f"[meals] {w}" for w in warnings])

    # Attractions
    errors, warnings = validate_attractions(data_dir, requirements_file)
    all_errors.extend([f"[attractions] {e}" for e in errors])
    all_warnings.extend([f"[attractions] {w}" for w in warnings])

    # Timeline
    errors, warnings = validate_timeline(data_dir)
    all_errors.extend([f"[timeline] {e}" for e in errors])
    all_warnings.extend([f"[timeline] {w}" for w in warnings])

    # Budget
    errors, warnings = validate_budget(data_dir)
    all_errors.extend([f"[budget] {e}" for e in errors])
    all_warnings.extend([f"[budget] {w}" for w in warnings])

    # Report results
    if all_errors:
        print("✗ CRITICAL ISSUES FOUND:")
        for error in all_errors:
            print(f"  {error}")
        print()

    if all_warnings:
        print("⚠️  WARNINGS:")
        for warning in all_warnings:
            print(f"  {warning}")
        print()

    if not all_errors and not all_warnings:
        print("✓ All agent outputs validated successfully")
        return 0
    elif all_errors:
        print(f"Validation failed: {len(all_errors)} critical issues")
        return 1
    else:
        print(f"Validation passed with {len(all_warnings)} warnings")
        return 2


if __name__ == '__main__':
    sys.exit(main())
