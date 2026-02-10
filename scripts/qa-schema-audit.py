#!/usr/bin/env python3
"""
QA Schema Audit Script
Validates all 7 agent data files in both trip directories against their schemas.
Checks required fields, optional fields, special validation rules, and format compliance.
"""

import json
import re
import os
import sys
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = "/root/travel-planner"
SCHEMA_DIR = os.path.join(BASE_DIR, "schemas")

TRIP_DIRS = {
    "itinerary": os.path.join(BASE_DIR, "data", "china-feb-15-mar-7-2026-20260202-195429"),
    "bucket-list": os.path.join(BASE_DIR, "data", "beijing-exchange-bucket-list-20260202-232405"),
}

AGENTS = ["meals", "attractions", "entertainment", "accommodation", "shopping", "transportation", "timeline"]

# ============================================================================
# SCHEMA FIELD DEFINITIONS (extracted from schema files)
# ============================================================================

# For each agent, define required and optional fields at the ITEM level
SCHEMA_FIELDS = {
    "meals": {
        "item_type": "meal_item",
        "required": [
            "name_base", "name_local", "location_base", "location_local",
            "cost", "currency_local", "cuisine_base", "time"
        ],
        "optional": [
            "coordinates", "cuisine_local", "signature_dishes_base",
            "signature_dishes_local", "notes_base", "notes_local", "search_results"
        ],
        "time_fields": ["time"],
        "cost_fields": ["cost"],
    },
    "attractions": {
        "item_type": "attraction_item",
        "required": [
            "name_base", "name_local", "location_base", "location_local",
            "cost", "currency_local", "type_base"
        ],
        "optional": [
            "coordinates", "type_local", "notes_base", "notes_local",
            "opening_hours", "time", "search_results"
        ],
        "time_fields": ["time"],
        "cost_fields": ["cost"],
    },
    "entertainment": {
        "item_type": "entertainment_item",
        "required": [
            "name_base", "name_local", "location_base", "location_local",
            "cost", "currency_local", "type_base"
        ],
        "optional": [
            "coordinates", "time", "type_local", "note_base", "note_local",
            "notes_base", "notes_local", "search_results"
        ],
        "time_fields": ["time"],
        "cost_fields": ["cost"],
    },
    "accommodation": {
        "item_type": "accommodation_item",
        "required": [
            "name_base", "name_local", "location_base", "location_local",
            "cost", "currency_local", "type_base", "amenities_base"
        ],
        "optional": [
            "coordinates", "type_local", "amenities_local", "notes_base",
            "notes_local", "stars", "check_in", "check_out", "search_results"
        ],
        "time_fields": [],
        "cost_fields": ["cost"],
    },
    "shopping": {
        "item_type": "shopping_item",
        "required": [
            "name_base", "name_local", "location_base", "location_local",
            "cost", "currency_local", "type_base", "time"
        ],
        "optional": [
            "coordinates", "type_local", "notes_base", "notes_local", "search_results"
        ],
        "time_fields": ["time"],
        "cost_fields": ["cost"],
    },
    "transportation": {
        "item_type": "location_change",
        "required": [
            "from_base", "to_base", "type_base",
            "departure_time", "arrival_time", "cost"
        ],
        "optional": [
            "from_local", "to_local", "name_base", "name_local",
            "from_location", "to_location", "type_local",
            "currency_local", "cost_type_base", "cost_type_local",
            "company_base", "company_local", "route_number",
            "departure_point_base", "departure_point_local",
            "arrival_point_base", "arrival_point_local",
            "status_base", "status_local",
            "notes_base", "notes_local", "booking_required"
        ],
        "time_fields": [],  # departure_time/arrival_time are plain strings, not time_range objects
        "cost_fields": ["cost"],
    },
    "timeline": {
        "item_type": "timeline_activity",
        "required": ["start_time", "end_time"],
        "optional": ["duration_minutes"],
        "time_fields": [],
        "cost_fields": [],
    },
}

# Timeline travel_segment fields
TRAVEL_SEGMENT_FIELDS = {
    "required": ["name_base", "name_local", "type_base", "start_time", "end_time"],
    "optional": ["type_local", "icon", "duration_minutes"],
}


# ============================================================================
# HELPERS
# ============================================================================

def load_json(path):
    """Load a JSON file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_non_empty(value):
    """Check if a value is present and non-empty (not None, not empty string, not empty list)."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    # 0 is a valid value for cost
    return True


def is_valid_currency(value):
    """Check if value is a 3-letter uppercase currency code."""
    if not isinstance(value, str):
        return False
    return bool(re.match(r'^[A-Z]{3}$', value))


def is_valid_time_range(value):
    """Check if value is a valid {start: HH:MM, end: HH:MM} object."""
    if not isinstance(value, dict):
        return False
    if "start" not in value or "end" not in value:
        return False
    time_pattern = re.compile(r'^[0-2][0-9]:[0-5][0-9]$')
    return bool(time_pattern.match(str(value["start"]))) and bool(time_pattern.match(str(value["end"])))


def is_valid_hhmm(value):
    """Check if a string is in HH:MM format."""
    if not isinstance(value, str):
        return False
    return bool(re.match(r'^[0-2][0-9]:[0-5][0-9]$', value))


def has_english_words(value):
    """Check if a local-language string contains English words like 'Optional', 'Alternative', 'Day'."""
    if not isinstance(value, str) or value.strip() == "":
        return False
    english_keywords = ["Optional", "Alternative", "Day ", "TBD", "N/A", "None"]
    for kw in english_keywords:
        if kw in value:
            return True
    return False


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def extract_items_meals(data):
    """Extract all meal items from meals.json data."""
    items = []
    for day in data.get("data", {}).get("days", []):
        day_num = day.get("day", "?")
        date = day.get("date", "?")
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if meal_type in day:
                item = day[meal_type]
                item_name = item.get("name_base", item.get("name", f"Day {day_num} {meal_type}"))
                items.append({
                    "data": item,
                    "label": f"Day {day_num} ({date}) {meal_type}: {item_name}",
                    "day": day_num,
                    "meal_type": meal_type,
                })
    return items


def extract_items_array(data, array_key):
    """Extract items from a day-based array structure (attractions, entertainment, shopping)."""
    items = []
    for day in data.get("data", {}).get("days", []):
        day_num = day.get("day", "?")
        date = day.get("date", "?")
        for idx, item in enumerate(day.get(array_key, [])):
            item_name = item.get("name_base", item.get("name", f"Item {idx}"))
            items.append({
                "data": item,
                "label": f"Day {day_num} ({date}) [{idx}]: {item_name}",
                "day": day_num,
            })
    return items


def extract_items_accommodation(data):
    """Extract accommodation items from accommodation.json data."""
    items = []
    for day in data.get("data", {}).get("days", []):
        day_num = day.get("day", "?")
        date = day.get("date", "?")
        if "accommodation" in day:
            item = day["accommodation"]
            item_name = item.get("name_base", item.get("name", f"Day {day_num} accommodation"))
            items.append({
                "data": item,
                "label": f"Day {day_num} ({date}): {item_name}",
                "day": day_num,
            })
    return items


def extract_items_transportation(data):
    """Extract location_change items from transportation.json data."""
    items = []
    for day in data.get("data", {}).get("days", []):
        day_num = day.get("day", "?")
        date = day.get("date", "?")
        if "location_change" in day:
            item = day["location_change"]
            from_name = item.get("from_base", item.get("from", "?"))
            to_name = item.get("to_base", item.get("to", "?"))
            items.append({
                "data": item,
                "label": f"Day {day_num} ({date}): {from_name} -> {to_name}",
                "day": day_num,
            })
    return items


def extract_timeline_activities(data):
    """Extract timeline activities and travel_segments from timeline.json data."""
    activities = []
    segments = []
    for day in data.get("data", {}).get("days", []):
        day_num = day.get("day", "?")
        date = day.get("date", "?")
        timeline = day.get("timeline", {})
        for activity_name, activity_data in timeline.items():
            if isinstance(activity_data, dict):
                activities.append({
                    "data": activity_data,
                    "label": f"Day {day_num} ({date}): {activity_name}",
                    "day": day_num,
                    "name": activity_name,
                })
        for idx, seg in enumerate(day.get("travel_segments", [])):
            seg_name = seg.get("name_base", f"Segment {idx}")
            segments.append({
                "data": seg,
                "label": f"Day {day_num} ({date}) segment [{idx}]: {seg_name}",
                "day": day_num,
            })
    return activities, segments


# ============================================================================
# VALIDATION ENGINE
# ============================================================================

class ValidationResult:
    def __init__(self, agent, trip, items_count):
        self.agent = agent
        self.trip = trip
        self.items_count = items_count
        self.required_present = 0
        self.required_total = 0
        self.optional_present = 0
        self.optional_total = 0
        self.high_gaps = []  # Missing required fields
        self.low_gaps = []   # Missing optional fields
        self.special_issues = []  # Special validation failures

    @property
    def req_pct(self):
        return (self.required_present / self.required_total * 100) if self.required_total > 0 else 100.0

    @property
    def opt_pct(self):
        return (self.optional_present / self.optional_total * 100) if self.optional_total > 0 else 100.0

    @property
    def total_present(self):
        return self.required_present + self.optional_present

    @property
    def total_fields(self):
        return self.required_total + self.optional_total

    @property
    def total_pct(self):
        return (self.total_present / self.total_fields * 100) if self.total_fields > 0 else 100.0


def validate_items(agent, trip, items, schema_def):
    """Validate a list of items against their schema definition."""
    result = ValidationResult(agent, trip, len(items))

    required_fields = schema_def["required"]
    optional_fields = schema_def["optional"]

    for item_info in items:
        item = item_info["data"]
        label = item_info["label"]

        # Check required fields
        for field in required_fields:
            result.required_total += 1
            val = item.get(field)
            if field == "cost":
                # cost can be 0, which is valid
                if val is not None and isinstance(val, (int, float)):
                    result.required_present += 1
                else:
                    result.high_gaps.append(f"[MISSING REQUIRED] {label} -> '{field}'")
            elif field == "time":
                if isinstance(val, dict) and "start" in val and "end" in val:
                    result.required_present += 1
                    if not is_valid_time_range(val):
                        result.special_issues.append(
                            f"[INVALID TIME FORMAT] {label} -> 'time' = {val}"
                        )
                else:
                    result.high_gaps.append(f"[MISSING REQUIRED] {label} -> '{field}'")
            elif field in ("amenities_base",):
                if isinstance(val, list) and len(val) > 0:
                    result.required_present += 1
                else:
                    result.high_gaps.append(f"[MISSING REQUIRED] {label} -> '{field}'")
            else:
                if is_non_empty(val):
                    result.required_present += 1
                else:
                    result.high_gaps.append(f"[MISSING REQUIRED] {label} -> '{field}'")

        # Check optional fields
        for field in optional_fields:
            result.optional_total += 1
            val = item.get(field)
            if field == "stars":
                # stars can be 0 or null
                if val is not None:
                    result.optional_present += 1
                else:
                    result.low_gaps.append(f"[MISSING OPTIONAL] {label} -> '{field}'")
            elif field == "coordinates":
                if isinstance(val, dict) and "lat" in val and "lng" in val:
                    result.optional_present += 1
                else:
                    result.low_gaps.append(f"[MISSING OPTIONAL] {label} -> '{field}'")
            elif field == "search_results":
                if isinstance(val, list):
                    result.optional_present += 1
                else:
                    result.low_gaps.append(f"[MISSING OPTIONAL] {label} -> '{field}'")
            elif field in ("amenities_base", "amenities_local"):
                if isinstance(val, list) and len(val) > 0:
                    result.optional_present += 1
                else:
                    result.low_gaps.append(f"[MISSING OPTIONAL] {label} -> '{field}'")
            elif field == "booking_required":
                if isinstance(val, bool):
                    result.optional_present += 1
                else:
                    result.low_gaps.append(f"[MISSING OPTIONAL] {label} -> '{field}'")
            elif field == "time":
                if isinstance(val, dict) and "start" in val and "end" in val:
                    result.optional_present += 1
                else:
                    result.low_gaps.append(f"[MISSING OPTIONAL] {label} -> '{field}'")
            elif field == "cost":
                if val is not None and isinstance(val, (int, float)):
                    result.optional_present += 1
                else:
                    result.low_gaps.append(f"[MISSING OPTIONAL] {label} -> '{field}'")
            else:
                if is_non_empty(val):
                    result.optional_present += 1
                else:
                    result.low_gaps.append(f"[MISSING OPTIONAL] {label} -> '{field}'")

    return result


def run_special_checks(agent, trip, items, result):
    """Run special validation checks beyond field presence."""

    for item_info in items:
        item = item_info["data"]
        label = item_info["label"]

        # currency_local must be present on every item with a cost field
        if "cost" in item and item["cost"] is not None:
            currency = item.get("currency_local")
            if not currency:
                result.special_issues.append(
                    f"[HIGH] {label} -> has 'cost' ({item['cost']}) but missing 'currency_local'"
                )
            elif not is_valid_currency(currency):
                result.special_issues.append(
                    f"[HIGH] {label} -> 'currency_local' = '{currency}' is not a valid 3-letter code"
                )

        # name_local must not contain English keywords
        name_local = item.get("name_local", "")
        if has_english_words(name_local):
            result.special_issues.append(
                f"[MEDIUM] {label} -> 'name_local' contains English: '{name_local}'"
            )

        # Meals-specific: signature_dishes_base / signature_dishes_local
        if agent == "meals":
            for field in ["signature_dishes_base", "signature_dishes_local"]:
                val = item.get(field)
                if not is_non_empty(val):
                    result.special_issues.append(
                        f"[MEDIUM] {label} -> Missing '{field}' on meals item"
                    )

        # Accommodation-specific: stars
        if agent == "accommodation":
            if "stars" not in item:
                result.special_issues.append(
                    f"[LOW] {label} -> Missing 'stars' on accommodation item"
                )

        # Transportation-specific: booking_required
        if agent == "transportation":
            if "booking_required" not in item:
                result.special_issues.append(
                    f"[LOW] {label} -> Missing 'booking_required' on transportation item"
                )

        # Time format validation for departure_time/arrival_time (transportation)
        if agent == "transportation":
            for tf in ["departure_time", "arrival_time"]:
                val = item.get(tf)
                if val and not is_valid_hhmm(val):
                    result.special_issues.append(
                        f"[HIGH] {label} -> '{tf}' = '{val}' is not valid HH:MM format"
                    )


def run_special_checks_timeline_segments(trip, segments, result):
    """Run special checks on timeline travel_segments."""
    for seg_info in segments:
        seg = seg_info["data"]
        label = seg_info["label"]

        # type_local required on travel_segments
        if not is_non_empty(seg.get("type_local")):
            result.special_issues.append(
                f"[MEDIUM] {label} -> Missing 'type_local' on travel_segment"
            )

        # icon required on travel_segments
        if not is_non_empty(seg.get("icon")):
            result.special_issues.append(
                f"[MEDIUM] {label} -> Missing 'icon' on travel_segment"
            )


# ============================================================================
# MAIN AUDIT
# ============================================================================

def run_audit():
    all_results = []
    grand_req_present = 0
    grand_req_total = 0
    grand_opt_present = 0
    grand_opt_total = 0
    all_high_gaps = []
    all_special_issues = []

    for trip_name, trip_dir in TRIP_DIRS.items():
        for agent in AGENTS:
            filepath = os.path.join(trip_dir, f"{agent}.json")
            if not os.path.exists(filepath):
                print(f"WARNING: {filepath} not found, skipping.")
                continue

            data = load_json(filepath)
            schema_def = SCHEMA_FIELDS[agent]

            # Extract items based on agent type
            if agent == "meals":
                items = extract_items_meals(data)
            elif agent in ("attractions", "entertainment", "shopping"):
                items = extract_items_array(data, agent)
            elif agent == "accommodation":
                items = extract_items_accommodation(data)
            elif agent == "transportation":
                items = extract_items_transportation(data)
            elif agent == "timeline":
                activities, segments = extract_timeline_activities(data)
                # Validate timeline activities
                result_activities = validate_items(agent, trip_name, activities, schema_def)
                run_special_checks(agent, trip_name, activities, result_activities)

                # Validate travel_segments separately
                if segments:
                    result_segments = validate_items(
                        f"{agent}_segments", trip_name, segments, TRAVEL_SEGMENT_FIELDS
                    )
                    run_special_checks_timeline_segments(trip_name, segments, result_segments)

                    # Merge segment results into activity results for reporting
                    result_activities.items_count = len(activities)
                    result_activities.special_issues.extend(result_segments.special_issues)

                    # Add a separate row for segments
                    all_results.append(result_segments)
                    grand_req_present += result_segments.required_present
                    grand_req_total += result_segments.required_total
                    grand_opt_present += result_segments.optional_present
                    grand_opt_total += result_segments.optional_total
                    all_high_gaps.extend(
                        [(f"{agent}_segments", trip_name, g) for g in result_segments.high_gaps]
                    )
                    all_special_issues.extend(
                        [(f"{agent}_segments", trip_name, s) for s in result_segments.special_issues]
                    )

                all_results.append(result_activities)
                grand_req_present += result_activities.required_present
                grand_req_total += result_activities.required_total
                grand_opt_present += result_activities.optional_present
                grand_opt_total += result_activities.optional_total
                all_high_gaps.extend(
                    [(agent, trip_name, g) for g in result_activities.high_gaps]
                )
                all_special_issues.extend(
                    [(agent, trip_name, s) for s in result_activities.special_issues]
                )
                continue

            # Standard agent validation
            result = validate_items(agent, trip_name, items, schema_def)
            run_special_checks(agent, trip_name, items, result)
            all_results.append(result)

            grand_req_present += result.required_present
            grand_req_total += result.required_total
            grand_opt_present += result.optional_present
            grand_opt_total += result.optional_total
            all_high_gaps.extend([(agent, trip_name, g) for g in result.high_gaps])
            all_special_issues.extend([(agent, trip_name, s) for s in result.special_issues])

    # ========================================================================
    # OUTPUT
    # ========================================================================

    print("=" * 160)
    print("QA SCHEMA COMPLIANCE AUDIT REPORT")
    print("=" * 160)
    print()

    # Summary table
    header = f"{'AGENT':<22} | {'TRIP':<14} | {'ITEMS':>5} | {'REQUIRED':>12} | {'OPTIONAL':>12} | {'REQ%':>6} | {'OPT%':>6} | {'TOTAL%':>6} | {'HIGH':>4} | {'LOW':>4} | {'SPECIAL':>7}"
    print(header)
    print("-" * 160)

    for r in all_results:
        req_str = f"{r.required_present}/{r.required_total}"
        opt_str = f"{r.optional_present}/{r.optional_total}"
        special_count = len(r.special_issues)
        high_count = len(r.high_gaps)
        low_count = len(r.low_gaps)

        req_pct_str = f"{r.req_pct:5.1f}%"
        opt_pct_str = f"{r.opt_pct:5.1f}%"
        total_pct_str = f"{r.total_pct:5.1f}%"

        # Mark failures
        req_flag = " !!" if r.req_pct < 100 else ""
        row = f"{r.agent:<22} | {r.trip:<14} | {r.items_count:>5} | {req_str:>12} | {opt_str:>12} | {req_pct_str:>6}{req_flag:<3}| {opt_pct_str:>6} | {total_pct_str:>6} | {high_count:>4} | {low_count:>4} | {special_count:>7}"
        print(row)

    print("-" * 160)

    # Grand totals
    grand_total_present = grand_req_present + grand_opt_present
    grand_total_fields = grand_req_total + grand_opt_total
    grand_req_pct = (grand_req_present / grand_req_total * 100) if grand_req_total > 0 else 100.0
    grand_opt_pct = (grand_opt_present / grand_opt_total * 100) if grand_opt_total > 0 else 100.0
    grand_total_pct = (grand_total_present / grand_total_fields * 100) if grand_total_fields > 0 else 100.0

    print(f"{'GRAND TOTAL':<22} | {'ALL':<14} | {'':>5} | {grand_req_present}/{grand_req_total}:>12 | {grand_opt_present}/{grand_opt_total}:>12 | {grand_req_pct:5.1f}% | {grand_opt_pct:5.1f}% | {grand_total_pct:5.1f}%")
    print()

    # ========================================================================
    # HIGH SEVERITY GAPS (Missing Required Fields)
    # ========================================================================

    if all_high_gaps:
        print()
        print("=" * 120)
        print(f"HIGH SEVERITY GAPS -- Missing Required Fields ({len(all_high_gaps)} total)")
        print("=" * 120)
        # Group by agent+trip
        grouped = defaultdict(list)
        for agent, trip, gap in all_high_gaps:
            grouped[(agent, trip)].append(gap)
        for (agent, trip), gaps in sorted(grouped.items()):
            print(f"\n  [{agent}] [{trip}] ({len(gaps)} gaps):")
            for g in gaps:
                print(f"    {g}")
    else:
        print()
        print("HIGH SEVERITY GAPS: NONE -- All required fields present!")

    # ========================================================================
    # SPECIAL VALIDATION ISSUES
    # ========================================================================

    if all_special_issues:
        print()
        print("=" * 120)
        print(f"SPECIAL VALIDATION ISSUES ({len(all_special_issues)} total)")
        print("=" * 120)

        # Categorize by severity
        high_specials = [(a, t, s) for a, t, s in all_special_issues if s.startswith("[HIGH]")]
        medium_specials = [(a, t, s) for a, t, s in all_special_issues if s.startswith("[MEDIUM]")]
        low_specials = [(a, t, s) for a, t, s in all_special_issues if s.startswith("[LOW]")]

        if high_specials:
            print(f"\n  --- HIGH ({len(high_specials)}) ---")
            for agent, trip, issue in high_specials:
                print(f"    [{agent}] [{trip}] {issue}")

        if medium_specials:
            print(f"\n  --- MEDIUM ({len(medium_specials)}) ---")
            for agent, trip, issue in medium_specials:
                print(f"    [{agent}] [{trip}] {issue}")

        if low_specials:
            print(f"\n  --- LOW ({len(low_specials)}) ---")
            for agent, trip, issue in low_specials:
                print(f"    [{agent}] [{trip}] {issue}")
    else:
        print()
        print("SPECIAL VALIDATION ISSUES: NONE")

    # ========================================================================
    # LOW SEVERITY GAPS (Missing Optional Fields) - Summary only
    # ========================================================================

    total_low_gaps = sum(len(r.low_gaps) for r in all_results)
    if total_low_gaps > 0:
        print()
        print("=" * 120)
        print(f"LOW SEVERITY GAPS -- Missing Optional Fields ({total_low_gaps} total) -- Summary by field")
        print("=" * 120)
        field_counts = defaultdict(int)
        for r in all_results:
            for gap in r.low_gaps:
                # Extract field name from gap string
                match = re.search(r"'(\w+)'", gap)
                if match:
                    field_counts[match.group(1)] += 1
        for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
            print(f"    {field:<30} : {count:>4} items missing")

    # ========================================================================
    # FINAL VERDICT
    # ========================================================================

    print()
    print("=" * 160)
    print("FINAL VERDICT")
    print("=" * 160)
    print(f"  Required field compliance:  {grand_req_present}/{grand_req_total} ({grand_req_pct:.1f}%)")
    print(f"  Optional field coverage:    {grand_opt_present}/{grand_opt_total} ({grand_opt_pct:.1f}%)")
    print(f"  Total field coverage:       {grand_total_present}/{grand_total_fields} ({grand_total_pct:.1f}%)")
    print(f"  High severity gaps:         {len(all_high_gaps)}")
    print(f"  Special validation issues:  {len(all_special_issues)}")

    high_special_count = len([s for _, _, s in all_special_issues if s.startswith("[HIGH]")])

    if len(all_high_gaps) == 0 and high_special_count == 0:
        print()
        print("  STATUS: PASS -- All required fields present, no high-severity special issues.")
    elif len(all_high_gaps) == 0:
        print()
        print(f"  STATUS: WARNING -- All required fields present, but {high_special_count} high-severity special issues found.")
    else:
        print()
        print(f"  STATUS: FAIL -- {len(all_high_gaps)} required field gaps and {high_special_count} high-severity special issues found.")

    print("=" * 160)

    # Return exit code
    return 0 if len(all_high_gaps) == 0 and high_special_count == 0 else 1


if __name__ == "__main__":
    sys.exit(run_audit())
