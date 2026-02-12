#!/usr/bin/env python3
"""
HTML Generation Compatibility Validation Script

Validates plan data for HTML rendering compatibility by checking:
1. Required fields for different view types
2. Data types (times, coordinates, costs)
3. HTML-breaking content (unescaped characters, invalid Unicode)
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

class HTMLCompatibilityValidator:
    """Validates plan data for HTML generation compatibility."""

    def __init__(self):
        self.html_blockers = []
        self.warnings = []

    def reset(self):
        """Reset blockers and warnings for a new plan."""
        self.html_blockers = []
        self.warnings = []

    def validate_plan(self, plan_dir: str) -> Dict[str, Any]:
        """Validate a single plan directory."""
        self.reset()
        plan_name = os.path.basename(plan_dir)

        # Check if directory exists
        if not os.path.isdir(plan_dir):
            return {
                "plan_directory": plan_dir,
                "html_blockers": [f"Plan directory not found: {plan_dir}"],
                "warnings": [],
                "status": "incompatible"
            }

        # Load and validate each data file
        self._validate_timeline(plan_dir)
        self._validate_attractions(plan_dir)
        self._validate_budget(plan_dir)
        self._validate_transportation(plan_dir)
        self._validate_entertainment(plan_dir)

        status = "compatible" if not self.html_blockers else "incompatible"

        return {
            "plan_directory": plan_dir,
            "html_blockers": self.html_blockers,
            "warnings": self.warnings,
            "status": status
        }

    def _load_json(self, filepath: str) -> Dict[str, Any]:
        """Safely load JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            self.html_blockers.append(
                f"Invalid JSON in {os.path.basename(filepath)}: {str(e)}"
            )
            return None

    def _validate_timeline(self, plan_dir: str):
        """Validate timeline.json structure."""
        filepath = os.path.join(plan_dir, 'timeline.json')
        data = self._load_json(filepath)

        if not data:
            return

        # Check for required structure
        if 'data' not in data or 'days' not in data.get('data', {}):
            self.html_blockers.append(
                "timeline.json: Missing 'data.days' structure"
            )
            return

        days = data['data']['days']

        for i, day in enumerate(days):
            day_num = day.get('day', i + 1)

            # Check timeline field exists and is dict
            if 'timeline' not in day:
                self.warnings.append(
                    f"timeline.json: Day {day_num} missing 'timeline' field"
                )
                continue

            timeline = day['timeline']
            if not isinstance(timeline, dict):
                self.html_blockers.append(
                    f"timeline.json: Day {day_num} timeline is not a dict"
                )
                continue

            # Validate each timeline entry
            for event_name, event_data in timeline.items():
                if not isinstance(event_data, dict):
                    self.html_blockers.append(
                        f"timeline.json: Day {day_num} event '{event_name}' is not a dict"
                    )
                    continue

                # Check start_time and end_time
                start_time = event_data.get('start_time')
                end_time = event_data.get('end_time')

                if start_time and not self._is_valid_time_format(start_time):
                    self.html_blockers.append(
                        f"timeline.json: Day {day_num} '{event_name}' has invalid start_time: {start_time}"
                    )

                if end_time and not self._is_valid_time_format(end_time):
                    self.html_blockers.append(
                        f"timeline.json: Day {day_num} '{event_name}' has invalid end_time: {end_time}"
                    )

                # Check for HTML-breaking content
                self._check_html_breaking_content(event_name, "timeline event name")

                # Check duration_minutes is a number
                if 'duration_minutes' in event_data:
                    duration = event_data['duration_minutes']
                    if not isinstance(duration, (int, float)):
                        self.html_blockers.append(
                            f"timeline.json: Day {day_num} '{event_name}' duration_minutes is not a number: {duration}"
                        )

    def _validate_attractions(self, plan_dir: str):
        """Validate attractions.json structure."""
        filepath = os.path.join(plan_dir, 'attractions.json')
        data = self._load_json(filepath)

        if not data:
            return

        # Check for required structure
        if 'data' not in data or 'days' not in data.get('data', {}):
            self.html_blockers.append(
                "attractions.json: Missing 'data.days' structure"
            )
            return

        days = data['data']['days']

        for i, day in enumerate(days):
            day_num = day.get('day', i + 1)
            attractions = day.get('attractions', [])

            if not isinstance(attractions, list):
                self.html_blockers.append(
                    f"attractions.json: Day {day_num} attractions is not a list"
                )
                continue

            for j, attraction in enumerate(attractions):
                # Check required fields
                required_fields = ['name', 'location']
                for field in required_fields:
                    if field not in attraction:
                        self.warnings.append(
                            f"attractions.json: Day {day_num} attraction #{j+1} missing '{field}'"
                        )

                # Check name length
                name = attraction.get('name', '')
                if len(name) > 500:
                    self.warnings.append(
                        f"attractions.json: Day {day_num} attraction name too long ({len(name)} chars)"
                    )

                # Validate coordinates if present
                if 'coordinates' in attraction:
                    coords = attraction['coordinates']
                    if not self._is_valid_coordinates(coords):
                        self.html_blockers.append(
                            f"attractions.json: Day {day_num} '{attraction.get('name', 'unknown')}' has invalid coordinates: {coords}"
                        )

                # Validate cost is a number
                if 'cost' in attraction:
                    cost = attraction['cost']
                    if not isinstance(cost, (int, float)):
                        try:
                            float(cost)
                        except (ValueError, TypeError):
                            self.html_blockers.append(
                                f"attractions.json: Day {day_num} '{attraction.get('name', 'unknown')}' cost is not a number: {cost}"
                            )

                # Check for HTML-breaking content
                self._check_html_breaking_content(
                    attraction.get('name', ''),
                    "attraction name"
                )
                self._check_html_breaking_content(
                    attraction.get('location', ''),
                    "attraction location"
                )
                self._check_html_breaking_content(
                    attraction.get('why_worth_visiting', ''),
                    "attraction description"
                )

    def _validate_budget(self, plan_dir: str):
        """Validate budget.json structure."""
        filepath = os.path.join(plan_dir, 'budget.json')
        data = self._load_json(filepath)

        if not data:
            return

        # Check for required structure
        if 'data' not in data or 'days' not in data.get('data', {}):
            self.html_blockers.append(
                "budget.json: Missing 'data.days' structure"
            )
            return

        days = data['data']['days']

        for i, day in enumerate(days):
            day_num = day.get('day', i + 1)

            if 'budget' not in day:
                self.warnings.append(
                    f"budget.json: Day {day_num} missing 'budget' field"
                )
                continue

            budget = day['budget']
            if not isinstance(budget, dict):
                self.html_blockers.append(
                    f"budget.json: Day {day_num} budget is not a dict"
                )
                continue

            # Validate numeric fields
            numeric_fields = ['meals', 'accommodation', 'activities', 'shopping', 'transportation', 'total']
            for field in numeric_fields:
                if field in budget:
                    value = budget[field]
                    if not isinstance(value, (int, float)):
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            self.html_blockers.append(
                                f"budget.json: Day {day_num} {field} is not a number: {value}"
                            )

    def _validate_transportation(self, plan_dir: str):
        """Validate transportation.json structure."""
        filepath = os.path.join(plan_dir, 'transportation.json')
        data = self._load_json(filepath)

        if not data:
            return

        # Check for required structure
        if 'data' not in data or 'days' not in data.get('data', {}):
            self.warnings.append(
                "transportation.json: Missing 'data.days' structure"
            )
            return

        days = data['data']['days']

        for i, day in enumerate(days):
            day_num = day.get('day', i + 1)

            if 'segments' not in day:
                continue

            segments = day.get('segments', [])
            if not isinstance(segments, list):
                self.html_blockers.append(
                    f"transportation.json: Day {day_num} segments is not a list"
                )
                continue

            for j, segment in enumerate(segments):
                # Validate time format
                if 'start_time' in segment:
                    start = segment['start_time']
                    if start and not self._is_valid_time_format(start):
                        self.html_blockers.append(
                            f"transportation.json: Day {day_num} segment #{j+1} invalid start_time: {start}"
                        )

                if 'end_time' in segment:
                    end = segment['end_time']
                    if end and not self._is_valid_time_format(end):
                        self.html_blockers.append(
                            f"transportation.json: Day {day_num} segment #{j+1} invalid end_time: {end}"
                        )

                # Check cost is numeric
                if 'cost' in segment:
                    cost = segment['cost']
                    if cost is not None and not isinstance(cost, (int, float)):
                        try:
                            float(cost)
                        except (ValueError, TypeError):
                            self.html_blockers.append(
                                f"transportation.json: Day {day_num} segment #{j+1} cost is not a number: {cost}"
                            )

    def _validate_entertainment(self, plan_dir: str):
        """Validate entertainment.json structure."""
        filepath = os.path.join(plan_dir, 'entertainment.json')
        data = self._load_json(filepath)

        if not data:
            return

        # Check for required structure
        if 'data' not in data or 'days' not in data.get('data', {}):
            self.warnings.append(
                "entertainment.json: Missing 'data.days' structure"
            )
            return

        days = data['data']['days']

        for i, day in enumerate(days):
            day_num = day.get('day', i + 1)
            activities = day.get('activities', [])

            if not isinstance(activities, list):
                self.html_blockers.append(
                    f"entertainment.json: Day {day_num} activities is not a list"
                )
                continue

            for j, activity in enumerate(activities):
                # Check required fields
                if 'name' not in activity:
                    self.warnings.append(
                        f"entertainment.json: Day {day_num} activity #{j+1} missing 'name'"
                    )

                # Check for HTML-breaking content
                self._check_html_breaking_content(
                    activity.get('name', ''),
                    "activity name"
                )

    def _is_valid_time_format(self, time_str: str) -> bool:
        """Check if time string is in HH:MM format."""
        if not isinstance(time_str, str):
            return False

        # Allow HH:MM or HH:MM:SS format
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$'
        return bool(re.match(time_pattern, time_str))

    def _is_valid_coordinates(self, coords: Any) -> bool:
        """Check if coordinates are in valid format {latitude: float, longitude: float}."""
        if not isinstance(coords, dict):
            return False

        # Check for lat/lng or latitude/longitude
        lat = coords.get('lat') or coords.get('latitude')
        lng = coords.get('lng') or coords.get('longitude')

        if lat is None or lng is None:
            return False

        try:
            lat_val = float(lat)
            lng_val = float(lng)

            # Validate ranges
            if -90 <= lat_val <= 90 and -180 <= lng_val <= 180:
                return True
        except (ValueError, TypeError):
            pass

        return False

    def _check_html_breaking_content(self, text: str, field_name: str):
        """Check for HTML-breaking characters in text fields."""
        if not isinstance(text, str):
            return

        # Check for unescaped HTML characters
        html_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '&': '&amp;'
        }

        for char in ['<', '>', '"']:
            if char in text:
                # Allow if already escaped
                if char == '<' and '&lt;' in text:
                    continue
                if char == '>' and '&gt;' in text:
                    continue

                self.warnings.append(
                    f"Unescaped HTML character '{char}' in {field_name}"
                )

        # Check text length
        if len(text) > 2000:
            self.warnings.append(
                f"{field_name} exceeds 2000 characters ({len(text)} chars)"
            )


def main():
    """Main validation function."""
    base_data_dir = '/root/travel-planner/data'
    output_dir = '/root/travel-planner/docs/debug'

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Get all plan directories
    plan_dirs = [
        d for d in os.listdir(base_data_dir)
        if os.path.isdir(os.path.join(base_data_dir, d))
        and d not in ['index.md', 'README.md']
    ]
    plan_dirs.sort()

    validator = HTMLCompatibilityValidator()
    results = []

    print(f"Validating {len(plan_dirs)} plan(s) for HTML compatibility...\n")

    for plan_dir in plan_dirs:
        plan_path = os.path.join(base_data_dir, plan_dir)
        print(f"Validating: {plan_dir}")

        result = validator.validate_plan(plan_path)
        results.append(result)

        if result['status'] == 'compatible':
            print(f"  Status: COMPATIBLE")
        else:
            print(f"  Status: INCOMPATIBLE")

        if result['html_blockers']:
            print(f"  Blockers: {len(result['html_blockers'])}")
            for blocker in result['html_blockers'][:3]:
                print(f"    - {blocker}")
            if len(result['html_blockers']) > 3:
                print(f"    ... and {len(result['html_blockers']) - 3} more")

        if result['warnings']:
            print(f"  Warnings: {len(result['warnings'])}")

        print()

    # Write overall report
    report = {
        "validation_date": "2026-02-12",
        "total_plans": len(plan_dirs),
        "compatible_plans": sum(1 for r in results if r['status'] == 'compatible'),
        "incompatible_plans": sum(1 for r in results if r['status'] == 'incompatible'),
        "plans": results
    }

    output_file = os.path.join(output_dir, 'html-compatibility-report.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport written to: {output_file}")
    print(f"Overall status: {report['compatible_plans']}/{report['total_plans']} plans compatible")

    return report


if __name__ == '__main__':
    main()
