#!/usr/bin/env python3
"""
Diagnostic script to identify legacy field name usage vs. schema-compliant field names.
Answers: Did the dev agents add schema-required fields, or are the old field names still in use?
"""

import json
import os
from collections import defaultdict

BASE_DIR = "/root/travel-planner"
TRIP_DIRS = {
    "itinerary": os.path.join(BASE_DIR, "data", "china-feb-15-mar-7-2026-20260202-195429"),
    "bucket-list": os.path.join(BASE_DIR, "data", "beijing-exchange-bucket-list-20260202-232405"),
}

# Legacy -> schema-required mapping
FIELD_RENAMES = {
    "currency": "currency_local",
    "type": "type_base",
    "amenities": "amenities_base",
    "cuisine": "cuisine_base",
    "notes": "notes_base",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_item_fields(item, item_label, agent):
    """Check which legacy and schema fields are present on an item."""
    findings = []
    for legacy, schema in FIELD_RENAMES.items():
        has_legacy = legacy in item
        has_schema = schema in item
        if has_legacy and not has_schema:
            findings.append(f"  LEGACY ONLY: '{legacy}' present, '{schema}' MISSING -> {item_label}")
        elif has_legacy and has_schema:
            findings.append(f"  BOTH PRESENT: '{legacy}' and '{schema}' -> {item_label}")
        elif not has_legacy and has_schema:
            pass  # Good - only schema field present
        # neither present is handled by main audit

    # Check for 'currency' specifically when cost exists
    if "cost" in item and item["cost"] is not None:
        has_currency = "currency" in item
        has_currency_local = "currency_local" in item
        if has_currency and not has_currency_local:
            findings.append(f"  CURRENCY GAP: has 'currency'={item.get('currency')} but NO 'currency_local' -> {item_label}")

    return findings


def analyze_agent(agent, trip_name, trip_dir):
    filepath = os.path.join(trip_dir, f"{agent}.json")
    if not os.path.exists(filepath):
        return []

    data = load_json(filepath)
    findings = []

    if agent == "meals":
        for day in data.get("data", {}).get("days", []):
            day_num = day.get("day", "?")
            for meal_type in ["breakfast", "lunch", "dinner"]:
                if meal_type in day:
                    item = day[meal_type]
                    label = f"Day {day_num} {meal_type}: {item.get('name_base', item.get('name', '?'))}"
                    findings.extend(check_item_fields(item, label, agent))

    elif agent in ("attractions", "entertainment", "shopping"):
        for day in data.get("data", {}).get("days", []):
            day_num = day.get("day", "?")
            for idx, item in enumerate(day.get(agent, [])):
                label = f"Day {day_num} [{idx}]: {item.get('name_base', item.get('name', '?'))}"
                findings.extend(check_item_fields(item, label, agent))

    elif agent == "accommodation":
        for day in data.get("data", {}).get("days", []):
            day_num = day.get("day", "?")
            if "accommodation" in day:
                item = day["accommodation"]
                label = f"Day {day_num}: {item.get('name_base', item.get('name', '?'))}"
                findings.extend(check_item_fields(item, label, agent))

    elif agent == "transportation":
        for day in data.get("data", {}).get("days", []):
            day_num = day.get("day", "?")
            if "location_change" in day:
                item = day["location_change"]
                label = f"Day {day_num}: {item.get('from_base', '?')} -> {item.get('to_base', '?')}"
                findings.extend(check_item_fields(item, label, agent))

    elif agent == "timeline":
        for day in data.get("data", {}).get("days", []):
            day_num = day.get("day", "?")
            for seg in day.get("travel_segments", []):
                label = f"Day {day_num} segment: {seg.get('name_base', '?')}"
                findings.extend(check_item_fields(seg, label, agent))

    return findings


def main():
    print("=" * 120)
    print("FIELD NAME DIAGNOSTIC: Legacy vs Schema-Compliant Fields")
    print("=" * 120)

    agents = ["meals", "attractions", "entertainment", "accommodation", "shopping", "transportation", "timeline"]

    for trip_name, trip_dir in TRIP_DIRS.items():
        print(f"\n{'='*60}")
        print(f"TRIP: {trip_name}")
        print(f"{'='*60}")

        for agent in agents:
            findings = analyze_agent(agent, trip_name, trip_dir)
            if findings:
                print(f"\n  [{agent}] ({len(findings)} findings):")
                # Show first 10, then summary
                for f in findings[:10]:
                    print(f"    {f}")
                if len(findings) > 10:
                    print(f"    ... and {len(findings) - 10} more")

                    # Summarize by pattern
                    legacy_only = [f for f in findings if "LEGACY ONLY" in f]
                    both = [f for f in findings if "BOTH PRESENT" in f]
                    currency_gap = [f for f in findings if "CURRENCY GAP" in f]
                    print(f"    SUMMARY: {len(legacy_only)} legacy-only, {len(both)} both-present, {len(currency_gap)} currency-gaps")
            else:
                print(f"\n  [{agent}] All items use schema-compliant field names")

    # Quick count of items with old field "type" (not "type_base")
    print(f"\n\n{'='*120}")
    print("DETAILED CHECK: Items with 'type' field but no 'type_base'")
    print("=" * 120)

    for trip_name, trip_dir in TRIP_DIRS.items():
        for agent in ["attractions", "entertainment", "accommodation", "shopping"]:
            filepath = os.path.join(trip_dir, f"{agent}.json")
            if not os.path.exists(filepath):
                continue
            data = load_json(filepath)
            count_legacy_only = 0
            count_both = 0
            count_schema_only = 0
            total = 0

            if agent == "accommodation":
                items_list = [day.get("accommodation", {}) for day in data.get("data", {}).get("days", []) if "accommodation" in day]
            else:
                items_list = []
                for day in data.get("data", {}).get("days", []):
                    items_list.extend(day.get(agent, []))

            for item in items_list:
                total += 1
                has_legacy = "type" in item
                has_schema = "type_base" in item
                if has_legacy and not has_schema:
                    count_legacy_only += 1
                elif has_legacy and has_schema:
                    count_both += 1
                elif not has_legacy and has_schema:
                    count_schema_only += 1

            print(f"  [{trip_name}] [{agent}] total={total}: legacy_only_type={count_legacy_only}, both={count_both}, schema_only={count_schema_only}")

    # Check currency field pattern
    print(f"\n{'='*120}")
    print("DETAILED CHECK: Items with 'currency' field but no 'currency_local'")
    print("=" * 120)

    for trip_name, trip_dir in TRIP_DIRS.items():
        for agent in ["meals", "attractions", "entertainment", "accommodation", "shopping"]:
            filepath = os.path.join(trip_dir, f"{agent}.json")
            if not os.path.exists(filepath):
                continue
            data = load_json(filepath)
            count_legacy_only = 0
            count_both = 0
            count_schema_only = 0
            count_neither = 0
            total = 0

            if agent == "meals":
                items_list = []
                for day in data.get("data", {}).get("days", []):
                    for mt in ["breakfast", "lunch", "dinner"]:
                        if mt in day:
                            items_list.append(day[mt])
            elif agent == "accommodation":
                items_list = [day.get("accommodation", {}) for day in data.get("data", {}).get("days", []) if "accommodation" in day]
            else:
                items_list = []
                for day in data.get("data", {}).get("days", []):
                    items_list.extend(day.get(agent, []))

            for item in items_list:
                total += 1
                has_legacy = "currency" in item
                has_schema = "currency_local" in item
                if has_legacy and not has_schema:
                    count_legacy_only += 1
                elif has_legacy and has_schema:
                    count_both += 1
                elif not has_legacy and has_schema:
                    count_schema_only += 1
                else:
                    count_neither += 1

            print(f"  [{trip_name}] [{agent}] total={total}: currency_legacy_only={count_legacy_only}, both={count_both}, schema_only={count_schema_only}, neither={count_neither}")

    # Check cuisine vs cuisine_base in meals
    print(f"\n{'='*120}")
    print("DETAILED CHECK: meals 'cuisine' vs 'cuisine_base'")
    print("=" * 120)

    for trip_name, trip_dir in TRIP_DIRS.items():
        filepath = os.path.join(trip_dir, "meals.json")
        data = load_json(filepath)
        count_legacy_only = 0
        count_both = 0
        count_schema_only = 0
        total = 0
        for day in data.get("data", {}).get("days", []):
            for mt in ["breakfast", "lunch", "dinner"]:
                if mt in day:
                    item = day[mt]
                    total += 1
                    has_legacy = "cuisine" in item
                    has_schema = "cuisine_base" in item
                    if has_legacy and not has_schema:
                        count_legacy_only += 1
                    elif has_legacy and has_schema:
                        count_both += 1
                    elif not has_legacy and has_schema:
                        count_schema_only += 1
        print(f"  [{trip_name}] meals cuisine: total={total}: legacy_only={count_legacy_only}, both={count_both}, schema_only={count_schema_only}")

    # Check amenities vs amenities_base in accommodation
    print(f"\n{'='*120}")
    print("DETAILED CHECK: accommodation 'amenities' vs 'amenities_base'")
    print("=" * 120)

    for trip_name, trip_dir in TRIP_DIRS.items():
        filepath = os.path.join(trip_dir, "accommodation.json")
        data = load_json(filepath)
        count_legacy_only = 0
        count_both = 0
        count_schema_only = 0
        total = 0
        for day in data.get("data", {}).get("days", []):
            if "accommodation" in day:
                item = day["accommodation"]
                total += 1
                has_legacy = "amenities" in item
                has_schema = "amenities_base" in item
                if has_legacy and not has_schema:
                    count_legacy_only += 1
                elif has_legacy and has_schema:
                    count_both += 1
                elif not has_legacy and has_schema:
                    count_schema_only += 1
        print(f"  [{trip_name}] accommodation amenities: total={total}: legacy_only={count_legacy_only}, both={count_both}, schema_only={count_schema_only}")


if __name__ == "__main__":
    main()
