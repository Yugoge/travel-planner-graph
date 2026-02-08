#!/usr/bin/env python3
"""
Validate timeline fidelity between timeline.json and PLAN_DATA in HTML.

Compares time entries (start/end) for meals, attractions, and entertainment
between the canonical timeline.json and the regenerated HTML's embedded PLAN_DATA.

Usage:
    python validate-timeline-fidelity.py <timeline_json> <html_file>

Exit codes:
    0 = 100% fidelity
    1 = Error / could not run
    2 = Less than 100% fidelity (report printed)
"""

import json
import re
import sys
from pathlib import Path


# Transit/logistic prefixes to exclude from timeline comparison
TRANSIT_PREFIXES = (
    "Travel to",
    "Travel from",
    "Walk to",
    "Walk from",
    "Wake up",
    "Board train",
    "High-speed train",
    "Hotel check",
    "Check luggage",
    "Check in",
    "Arrive ",
    "Return home",
    "Return to",
    "Say goodbye",
    "Rest at",
    "Free Time",
    "Pack ",
    "Return home",
    "Midnight Countdown",
    "Settle in",
    "Drive to",
    "Drive from",
    "Metro to",
    "Metro from",
    "Bus to",
    "Bus from",
    "Taxi to",
    "Taxi from",
    "Prepare ",
    "Pack and",
)


def is_transit_entry(name: str) -> bool:
    """Check if a timeline entry is a transit/logistic entry to skip."""
    for prefix in TRANSIT_PREFIXES:
        if name.startswith(prefix):
            return True
    # Also skip entries that contain "check-out" or "check-in" case insensitive
    lower = name.lower()
    if "check-out" in lower or "check-in" in lower:
        return True
    return False


def extract_plan_data(html_path: str) -> dict:
    """Extract the PLAN_DATA JavaScript object from the HTML file."""
    html_content = Path(html_path).read_text(encoding="utf-8")

    # Find the PLAN_DATA assignment
    match = re.search(r'const\s+PLAN_DATA\s*=\s*(\{)', html_content)
    if not match:
        print("ERROR: Could not find PLAN_DATA in HTML file", file=sys.stderr)
        sys.exit(1)

    # Find the matching closing brace by counting braces
    start_idx = match.start(1)
    brace_count = 0
    end_idx = start_idx
    in_string = False
    escape_next = False

    for i in range(start_idx, len(html_content)):
        ch = html_content[i]

        if escape_next:
            escape_next = False
            continue

        if ch == '\\' and in_string:
            escape_next = True
            continue

        if ch == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break

    json_str = html_content[start_idx:end_idx]

    # Clean up JavaScript-specific syntax that isn't valid JSON
    # Remove trailing commas before } or ]
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse PLAN_DATA as JSON: {e}", file=sys.stderr)
        # Try to show context around error
        pos = e.pos if hasattr(e, 'pos') and e.pos else 0
        context = json_str[max(0, pos - 50):pos + 50]
        print(f"Context around error: ...{context}...", file=sys.stderr)
        sys.exit(1)


def normalize_name(name: str) -> str:
    """Normalize a name for fuzzy matching by removing parenthetical Chinese,
    optional markers, punctuation, and extra whitespace."""
    # Remove " - Optional" suffix
    name = re.sub(r'\s*-\s*Optional\s*$', '', name)
    # Remove parenthetical content (Chinese characters, pinyin, etc.)
    name = re.sub(r'\s*[\(（].*?[\)）]', '', name)
    # Remove special unicode characters
    name = re.sub(r'[·\u00b7\u2022\u30fb]', ' ', name)
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    # Lowercase for comparison
    return name.lower()


def get_plan_items_for_day(day_data: dict) -> list:
    """Extract all timed items from a PLAN_DATA day (meals, attractions, entertainment)."""
    items = []

    # Meals
    meals = day_data.get("meals", {})
    if meals:
        for meal_type in ["breakfast", "lunch", "dinner"]:
            meal = meals.get(meal_type)
            if meal and isinstance(meal, dict) and meal.get("time"):
                time_info = meal["time"]
                if time_info.get("start") and time_info.get("end"):
                    items.append({
                        "category": f"meal/{meal_type}",
                        "name": meal.get("name", ""),
                        "name_base": meal.get("name_base", ""),
                        "name_local": meal.get("name_local", ""),
                        "start": time_info["start"],
                        "end": time_info["end"],
                    })

    # Attractions
    for attr in day_data.get("attractions", []):
        if attr.get("time") and attr["time"].get("start") and attr["time"].get("end"):
            items.append({
                "category": "attraction",
                "name": attr.get("name", ""),
                "name_base": attr.get("name_base", ""),
                "name_local": attr.get("name_local", ""),
                "start": attr["time"]["start"],
                "end": attr["time"]["end"],
            })

    # Entertainment
    for ent in day_data.get("entertainment", []):
        if ent.get("time") and ent["time"].get("start") and ent["time"].get("end"):
            items.append({
                "category": "entertainment",
                "name": ent.get("name", ""),
                "name_base": ent.get("name_base", ""),
                "name_local": ent.get("name_local", ""),
                "start": ent["time"]["start"],
                "end": ent["time"]["end"],
            })

    return items


def find_timeline_match(item: dict, timeline_entries: dict) -> tuple:
    """Try to match a PLAN_DATA item to a timeline entry.

    Returns:
        (match_name, matched_entry) if found, or (None, None) if not found.
    """
    item_names = [
        item.get("name_base", ""),
        item.get("name", ""),
        item.get("name_local", ""),
    ]
    item_names_normalized = [normalize_name(n) for n in item_names if n]

    for tl_name, tl_entry in timeline_entries.items():
        if is_transit_entry(tl_name):
            continue

        tl_normalized = normalize_name(tl_name)

        for item_norm in item_names_normalized:
            # Exact normalized match
            if item_norm == tl_normalized:
                return tl_name, tl_entry

            # Check if one contains the other
            if item_norm in tl_normalized or tl_normalized in item_norm:
                return tl_name, tl_entry

        # Also try matching raw names (without normalization) for Chinese names
        for raw_name in item_names:
            if raw_name and raw_name in tl_name:
                return tl_name, tl_entry
            if raw_name and tl_name in raw_name:
                return tl_name, tl_entry

    return None, None


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <timeline_json> <html_file>")
        sys.exit(1)

    timeline_path = sys.argv[1]
    html_path = sys.argv[2]

    # Load timeline.json
    with open(timeline_path, "r", encoding="utf-8") as f:
        timeline_data = json.load(f)

    # Extract PLAN_DATA from HTML
    plan_data = extract_plan_data(html_path)

    # Build a flat list of all days from PLAN_DATA
    plan_days = {}
    for trip in plan_data.get("trips", []):
        for day in trip.get("days", []):
            day_num = day.get("day")
            if day_num is not None:
                plan_days[day_num] = day

    # Build timeline days lookup
    timeline_days = {}
    for tl_day in timeline_data.get("data", {}).get("days", []):
        day_num = tl_day.get("day")
        if day_num is not None:
            timeline_days[day_num] = tl_day.get("timeline", {})

    # Compare
    total_items = 0
    matches = 0
    mismatches = []
    not_found = []

    all_days = sorted(set(plan_days.keys()) | set(timeline_days.keys()))

    print("=" * 80)
    print("TIMELINE FIDELITY VALIDATION REPORT")
    print("=" * 80)
    print(f"Timeline source: {timeline_path}")
    print(f"HTML source:     {html_path}")
    print(f"Days in timeline: {len(timeline_days)}")
    print(f"Days in PLAN_DATA: {len(plan_days)}")
    print("=" * 80)

    for day_num in all_days:
        if day_num not in plan_days:
            print(f"\n  Day {day_num}: MISSING from PLAN_DATA")
            continue
        if day_num not in timeline_days:
            print(f"\n  Day {day_num}: MISSING from timeline.json")
            continue

        day_data = plan_days[day_num]
        timeline = timeline_days[day_num]
        items = get_plan_items_for_day(day_data)

        day_matches = 0
        day_mismatches = []
        day_not_found = []

        for item in items:
            total_items += 1
            tl_name, tl_entry = find_timeline_match(item, timeline)

            if tl_name is None:
                day_not_found.append(item)
                not_found.append((day_num, item))
            else:
                tl_start = tl_entry["start_time"]
                tl_end = tl_entry["end_time"]
                item_start = item["start"]
                item_end = item["end"]

                if tl_start == item_start and tl_end == item_end:
                    day_matches += 1
                    matches += 1
                else:
                    mismatch_info = {
                        "item": item,
                        "timeline_name": tl_name,
                        "timeline_start": tl_start,
                        "timeline_end": tl_end,
                        "plan_start": item_start,
                        "plan_end": item_end,
                    }
                    day_mismatches.append(mismatch_info)
                    mismatches.append((day_num, mismatch_info))

        # Print day summary
        day_total = len(items)
        day_status = "OK" if day_matches == day_total and day_total > 0 else "ISSUES" if day_total > 0 else "EMPTY"
        date_str = day_data.get("date", "")
        location = day_data.get("location", "")

        print(f"\n  Day {day_num:2d} ({date_str}) {location}")
        print(f"    Items: {day_total}  |  Matches: {day_matches}  |  Mismatches: {len(day_mismatches)}  |  Not found: {len(day_not_found)}  [{day_status}]")

        for mm in day_mismatches:
            item_display = mm["item"]["name_base"] or mm["item"]["name"]
            print(f"      MISMATCH: {item_display}")
            print(f"        Timeline: {mm['timeline_start']}-{mm['timeline_end']}  |  PLAN_DATA: {mm['plan_start']}-{mm['plan_end']}")
            print(f"        (matched to timeline entry: \"{mm['timeline_name']}\")")

        for nf in day_not_found:
            nf_display = nf["name_base"] or nf["name"]
            print(f"      NOT FOUND: {nf_display} [{nf['category']}] ({nf['start']}-{nf['end']})")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Total items checked:  {total_items}")
    print(f"  Matches:              {matches}")
    print(f"  Mismatches:           {len(mismatches)}")
    print(f"  Not found:            {len(not_found)}")

    if total_items > 0:
        fidelity = (matches / total_items) * 100
        print(f"  Fidelity:             {fidelity:.1f}%")
    else:
        fidelity = 0.0
        print("  Fidelity:             N/A (no items)")

    print("=" * 80)

    if len(mismatches) > 0:
        print(f"\nDETAILED MISMATCHES ({len(mismatches)} total):")
        print("-" * 80)
        for day_num, mm in mismatches:
            item_display = mm["item"]["name_base"] or mm["item"]["name"]
            print(f"  Day {day_num:2d} | {item_display}")
            print(f"           Timeline: {mm['timeline_start']}-{mm['timeline_end']}  vs  PLAN_DATA: {mm['plan_start']}-{mm['plan_end']}")

    if len(not_found) > 0:
        print(f"\nNOT FOUND IN TIMELINE ({len(not_found)} total):")
        print("-" * 80)
        for day_num, nf in not_found:
            nf_display = nf["name_base"] or nf["name"]
            print(f"  Day {day_num:2d} | {nf_display} [{nf['category']}] ({nf['start']}-{nf['end']})")

    # Exit code
    if fidelity == 100.0:
        print("\nRESULT: PERFECT FIDELITY")
        sys.exit(0)
    else:
        print(f"\nRESULT: FIDELITY {fidelity:.1f}% - needs attention")
        sys.exit(2)


if __name__ == "__main__":
    main()
