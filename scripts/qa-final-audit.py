#!/usr/bin/env python3
"""
FINAL QA SCHEMA COMPLIANCE AUDIT
=================================
Comprehensive audit of all 7 agent data files in both trip directories.
Checks schema-required fields, optional fields, special validation rules,
and identifies the root cause of each compliance gap.
"""

import json
import re
import os
import sys
from collections import defaultdict

BASE_DIR = "/root/travel-planner"
SCHEMA_DIR = os.path.join(BASE_DIR, "schemas")

TRIP_DIRS = {
    "itinerary": os.path.join(BASE_DIR, "data", "china-feb-15-mar-7-2026-20260202-195429"),
    "bucket-list": os.path.join(BASE_DIR, "data", "beijing-exchange-bucket-list-20260202-232405"),
}

# ============================================================================
# SCHEMA FIELD DEFINITIONS
# ============================================================================

SCHEMA_FIELDS = {
    "meals": {
        "required": ["name_base", "name_local", "location_base", "location_local",
                      "cost", "currency_local", "cuisine_base", "time"],
        "optional": ["coordinates", "cuisine_local", "signature_dishes_base",
                      "signature_dishes_local", "notes_base", "notes_local", "search_results"],
    },
    "attractions": {
        "required": ["name_base", "name_local", "location_base", "location_local",
                      "cost", "currency_local", "type_base"],
        "optional": ["coordinates", "type_local", "notes_base", "notes_local",
                      "opening_hours", "time", "search_results"],
    },
    "entertainment": {
        "required": ["name_base", "name_local", "location_base", "location_local",
                      "cost", "currency_local", "type_base"],
        "optional": ["coordinates", "time", "type_local", "note_base", "note_local",
                      "notes_base", "notes_local", "search_results"],
    },
    "accommodation": {
        "required": ["name_base", "name_local", "location_base", "location_local",
                      "cost", "currency_local", "type_base", "amenities_base"],
        "optional": ["coordinates", "type_local", "amenities_local", "notes_base",
                      "notes_local", "stars", "check_in", "check_out", "search_results"],
    },
    "shopping": {
        "required": ["name_base", "name_local", "location_base", "location_local",
                      "cost", "currency_local", "type_base", "time"],
        "optional": ["coordinates", "type_local", "notes_base", "notes_local", "search_results"],
    },
    "transportation": {
        "required": ["from_base", "to_base", "type_base",
                      "departure_time", "arrival_time", "cost"],
        "optional": ["from_local", "to_local", "name_base", "name_local",
                      "from_location", "to_location", "type_local",
                      "currency_local", "cost_type_base", "cost_type_local",
                      "company_base", "company_local", "route_number",
                      "departure_point_base", "departure_point_local",
                      "arrival_point_base", "arrival_point_local",
                      "status_base", "status_local",
                      "notes_base", "notes_local", "booking_required"],
    },
    "timeline_activity": {
        "required": ["start_time", "end_time"],
        "optional": ["duration_minutes"],
    },
    "travel_segment": {
        "required": ["name_base", "name_local", "type_base", "start_time", "end_time"],
        "optional": ["type_local", "icon", "duration_minutes"],
    },
}

# Known legacy -> schema field name mappings
# Note: type_base has TWO legacy aliases: 'type' (most agents) and 'mode' (travel_segments)
LEGACY_ALIASES_MULTI = {
    "currency_local": ["currency"],
    "type_base": ["type", "mode"],
    "amenities_base": ["amenities"],
    "cuisine_base": ["cuisine"],
    "notes_base": ["notes"],
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_non_empty(value):
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    return True


def is_valid_currency(value):
    return isinstance(value, str) and bool(re.match(r'^[A-Z]{3}$', value))


def is_valid_time_range(value):
    if not isinstance(value, dict):
        return False
    tp = re.compile(r'^[0-2][0-9]:[0-5][0-9]$')
    return ("start" in value and "end" in value
            and bool(tp.match(str(value["start"])))
            and bool(tp.match(str(value["end"]))))


def is_valid_hhmm(value):
    return isinstance(value, str) and bool(re.match(r'^[0-2][0-9]:[0-5][0-9]$', value))


def has_english_words(value):
    if not isinstance(value, str) or value.strip() == "":
        return False
    for kw in ["Optional", "Alternative", "Day ", "TBD", "N/A"]:
        if kw in value:
            return True
    return False


# ============================================================================
# ITEM EXTRACTION
# ============================================================================

def extract_all_items(agent, data):
    """Extract all items for an agent from its data structure. Returns list of (item_dict, label)."""
    items = []
    days = data.get("data", {}).get("days", [])

    if agent == "meals":
        for day in days:
            dn = day.get("day", "?")
            dt = day.get("date", "?")
            for mt in ["breakfast", "lunch", "dinner"]:
                if mt in day:
                    item = day[mt]
                    name = item.get("name_base", item.get("name", f"Day{dn}-{mt}"))
                    items.append((item, f"Day {dn} ({dt}) {mt}: {name}"))

    elif agent in ("attractions", "entertainment", "shopping"):
        for day in days:
            dn = day.get("day", "?")
            dt = day.get("date", "?")
            for idx, item in enumerate(day.get(agent, [])):
                name = item.get("name_base", item.get("name", f"Item{idx}"))
                items.append((item, f"Day {dn} ({dt}) [{idx}]: {name}"))

    elif agent == "accommodation":
        for day in days:
            dn = day.get("day", "?")
            dt = day.get("date", "?")
            if "accommodation" in day:
                item = day["accommodation"]
                name = item.get("name_base", item.get("name", f"Day{dn}"))
                items.append((item, f"Day {dn} ({dt}): {name}"))

    elif agent == "transportation":
        for day in days:
            dn = day.get("day", "?")
            dt = day.get("date", "?")
            if "location_change" in day:
                item = day["location_change"]
                fr = item.get("from_base", item.get("from", "?"))
                to = item.get("to_base", item.get("to", "?"))
                items.append((item, f"Day {dn} ({dt}): {fr} -> {to}"))

    return items


def extract_timeline_items(data):
    """Extract timeline activities and travel_segments separately."""
    activities = []
    segments = []
    for day in data.get("data", {}).get("days", []):
        dn = day.get("day", "?")
        dt = day.get("date", "?")
        tl = day.get("timeline", {})
        for name, entry in tl.items():
            if isinstance(entry, dict):
                activities.append((entry, f"Day {dn} ({dt}): {name}"))
        for idx, seg in enumerate(day.get("travel_segments", [])):
            sn = seg.get("name_base", f"Seg{idx}")
            segments.append((seg, f"Day {dn} ({dt}) seg[{idx}]: {sn}"))
    return activities, segments


# ============================================================================
# FIELD VALIDATION
# ============================================================================

def check_field_present(item, field):
    """Check if a field is present with a valid non-empty value."""
    val = item.get(field)

    if field == "cost":
        return val is not None and isinstance(val, (int, float))
    elif field == "time":
        return isinstance(val, dict) and "start" in val and "end" in val
    elif field in ("amenities_base", "amenities_local"):
        return isinstance(val, list) and len(val) > 0
    elif field == "stars":
        return val is not None  # can be 0
    elif field == "booking_required":
        return isinstance(val, bool)
    elif field == "coordinates":
        return isinstance(val, dict) and "lat" in val and "lng" in val
    elif field == "search_results":
        return isinstance(val, list)
    elif field == "duration_minutes":
        return val is not None and isinstance(val, (int, float))
    else:
        return is_non_empty(val)


def get_legacy_aliases(field):
    """Return all legacy field names for a schema field, if any."""
    return LEGACY_ALIASES_MULTI.get(field, [])


def has_any_legacy_alias(item, field):
    """Check if item has any legacy alias for the given schema field."""
    for alias in get_legacy_aliases(field):
        if alias in item:
            return alias
    return None


# ============================================================================
# MAIN AUDIT
# ============================================================================

def run_audit():
    print("=" * 160)
    print("COMPREHENSIVE QA SCHEMA COMPLIANCE AUDIT")
    print("=" * 160)
    print()

    # Collect all results
    rows = []  # (agent, trip, items_count, req_present, req_total, opt_present, opt_total, high_gaps, low_gaps, special_issues)
    all_high_gaps = []
    all_special = []
    root_cause_summary = defaultdict(int)  # field_name -> count of gaps caused by legacy naming

    for trip_name, trip_dir in TRIP_DIRS.items():
        for agent in ["meals", "attractions", "entertainment", "accommodation", "shopping", "transportation", "timeline"]:
            filepath = os.path.join(trip_dir, f"{agent}.json")
            if not os.path.exists(filepath):
                print(f"WARNING: {filepath} not found")
                continue

            data = load_json(filepath)

            if agent == "timeline":
                # Handle timeline activities + travel_segments
                activities, segments = extract_timeline_items(data)

                # Activities
                schema = SCHEMA_FIELDS["timeline_activity"]
                rp, rt, op, ot = 0, 0, 0, 0
                high, low, special = [], [], []
                for item, label in activities:
                    for f in schema["required"]:
                        rt += 1
                        if check_field_present(item, f):
                            rp += 1
                        else:
                            high.append(f"MISSING REQ: {label} -> '{f}'")
                    for f in schema["optional"]:
                        ot += 1
                        if check_field_present(item, f):
                            op += 1
                        else:
                            low.append(f"MISSING OPT: {label} -> '{f}'")

                rows.append(("timeline", trip_name, len(activities), rp, rt, op, ot, high, low, special))
                all_high_gaps.extend([(agent, trip_name, g) for g in high])

                # Travel segments
                schema_seg = SCHEMA_FIELDS["travel_segment"]
                rp2, rt2, op2, ot2 = 0, 0, 0, 0
                high2, low2, special2 = [], [], []
                for item, label in segments:
                    for f in schema_seg["required"]:
                        rt2 += 1
                        if check_field_present(item, f):
                            rp2 += 1
                        else:
                            # Check if legacy alias exists
                            legacy = has_any_legacy_alias(item, f)
                            if legacy:
                                high2.append(f"LEGACY NAME: {label} -> has '{legacy}' but not '{f}'")
                                root_cause_summary[f"travel_segment.{f} (legacy='{legacy}')"] += 1
                            else:
                                high2.append(f"MISSING REQ: {label} -> '{f}'")
                    for f in schema_seg["optional"]:
                        ot2 += 1
                        if check_field_present(item, f):
                            op2 += 1
                        else:
                            low2.append(f"MISSING OPT: {label} -> '{f}'")

                    # Special: icon and type_local
                    if not item.get("icon"):
                        special2.append(f"[MEDIUM] {label} -> missing 'icon'")
                    if not item.get("type_local"):
                        special2.append(f"[MEDIUM] {label} -> missing 'type_local'")

                rows.append(("timeline_segs", trip_name, len(segments), rp2, rt2, op2, ot2, high2, low2, special2))
                all_high_gaps.extend([("timeline_segs", trip_name, g) for g in high2])
                all_special.extend([("timeline_segs", trip_name, s) for s in special2])
                continue

            # Standard agents
            items = extract_all_items(agent, data)
            schema = SCHEMA_FIELDS[agent]
            rp, rt, op, ot = 0, 0, 0, 0
            high, low, special = [], [], []

            for item, label in items:
                # Required fields
                for f in schema["required"]:
                    rt += 1
                    if check_field_present(item, f):
                        rp += 1
                    else:
                        legacy = has_any_legacy_alias(item, f)
                        if legacy:
                            high.append(f"LEGACY NAME: {label} -> has '{legacy}' but not '{f}'")
                            root_cause_summary[f"{agent}.{f} (legacy='{legacy}')"] += 1
                        else:
                            high.append(f"MISSING REQ: {label} -> '{f}'")

                # Optional fields
                for f in schema["optional"]:
                    ot += 1
                    if check_field_present(item, f):
                        op += 1
                    else:
                        legacy = has_any_legacy_alias(item, f)
                        if legacy:
                            low.append(f"LEGACY OPT: {label} -> has '{legacy}' but not '{f}'")
                            root_cause_summary[f"{agent}.{f} (legacy='{legacy}', optional)"] += 1
                        else:
                            low.append(f"MISSING OPT: {label} -> '{f}'")

                # === SPECIAL CHECKS ===
                # currency_local on items with cost
                if item.get("cost") is not None:
                    cl = item.get("currency_local")
                    if not cl:
                        if item.get("currency"):
                            special.append(f"[HIGH] {label} -> has 'currency'={item['currency']} but no 'currency_local'")
                        else:
                            special.append(f"[HIGH] {label} -> has cost but no currency at all")
                    elif not is_valid_currency(cl):
                        special.append(f"[HIGH] {label} -> currency_local='{cl}' invalid format")

                # name_local should not contain English keywords
                nl = item.get("name_local", "")
                if has_english_words(nl):
                    special.append(f"[MEDIUM] {label} -> name_local has English: '{nl}'")

                # Meals: signature_dishes
                if agent == "meals":
                    for sf in ["signature_dishes_base", "signature_dishes_local"]:
                        if not is_non_empty(item.get(sf)):
                            special.append(f"[MEDIUM] {label} -> missing '{sf}'")

                # Accommodation: stars
                if agent == "accommodation":
                    if "stars" not in item:
                        special.append(f"[LOW] {label} -> missing 'stars'")

                # Transportation: booking_required
                if agent == "transportation":
                    if "booking_required" not in item:
                        special.append(f"[LOW] {label} -> missing 'booking_required'")
                    for tf in ["departure_time", "arrival_time"]:
                        v = item.get(tf)
                        if v and not is_valid_hhmm(v):
                            special.append(f"[HIGH] {label} -> '{tf}'='{v}' invalid HH:MM")

                # Time range validation
                if "time" in schema["required"] or "time" in schema["optional"]:
                    t = item.get("time")
                    if isinstance(t, dict) and not is_valid_time_range(t):
                        special.append(f"[HIGH] {label} -> time format invalid: {t}")

            rows.append((agent, trip_name, len(items), rp, rt, op, ot, high, low, special))
            all_high_gaps.extend([(agent, trip_name, g) for g in high])
            all_special.extend([(agent, trip_name, s) for s in special])

    # ========================================================================
    # OUTPUT TABLE
    # ========================================================================

    header = f"{'AGENT':<18} | {'TRIP':<14} | {'ITEMS':>5} | {'REQUIRED':>12} | {'OPTIONAL':>12} | {'REQ%':>7} | {'OPT%':>7} | {'TOTAL%':>7} | {'HIGH':>4} | {'LOW':>4} | {'SPEC':>4}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    grand_rp = grand_rt = grand_op = grand_ot = 0
    for agent, trip, count, rp, rt, op, ot, high, low, special in rows:
        grand_rp += rp; grand_rt += rt; grand_op += op; grand_ot += ot
        req_str = f"{rp}/{rt}"
        opt_str = f"{op}/{ot}"
        req_pct = (rp / rt * 100) if rt else 100.0
        opt_pct = (op / ot * 100) if ot else 100.0
        tot_pct = ((rp + op) / (rt + ot) * 100) if (rt + ot) else 100.0
        flag = " !!" if req_pct < 100 else "   "
        print(f"{agent:<18} | {trip:<14} | {count:>5} | {req_str:>12} | {opt_str:>12} | {req_pct:6.1f}%{flag}| {opt_pct:6.1f}% | {tot_pct:6.1f}% | {len(high):>4} | {len(low):>4} | {len(special):>4}")

    print(sep)
    grand_tot_pct = ((grand_rp + grand_op) / (grand_rt + grand_ot) * 100) if (grand_rt + grand_ot) else 100.0
    grand_req_pct = (grand_rp / grand_rt * 100) if grand_rt else 100.0
    grand_opt_pct = (grand_op / grand_ot * 100) if grand_ot else 100.0
    print(f"{'GRAND TOTAL':<18} | {'ALL':<14} | {'':>5} | {grand_rp}/{grand_rt}:>12 | {grand_op}/{grand_ot}:>12 | {grand_req_pct:6.1f}%   | {grand_opt_pct:6.1f}% | {grand_tot_pct:6.1f}%")
    print()

    # ========================================================================
    # ROOT CAUSE ANALYSIS
    # ========================================================================

    print("=" * 120)
    print("ROOT CAUSE ANALYSIS: Legacy Field Names Not Renamed to Schema-Compliant Names")
    print("=" * 120)

    # Count: how many high gaps are LEGACY NAME vs truly MISSING
    legacy_gaps = [g for _, _, g in all_high_gaps if g.startswith("LEGACY NAME")]
    missing_gaps = [g for _, _, g in all_high_gaps if g.startswith("MISSING REQ")]
    print(f"\n  Total HIGH severity required-field gaps:  {len(all_high_gaps)}")
    print(f"    Caused by legacy field naming:           {len(legacy_gaps)}  ({len(legacy_gaps)/max(len(all_high_gaps),1)*100:.1f}%)")
    print(f"    Truly missing (no data at all):           {len(missing_gaps)}  ({len(missing_gaps)/max(len(all_high_gaps),1)*100:.1f}%)")

    print(f"\n  Breakdown by field rename needed:")
    for key, count in sorted(root_cause_summary.items(), key=lambda x: -x[1]):
        print(f"    {key:<60} : {count:>4} items")

    # ========================================================================
    # HIGH SEVERITY GAPS (show first 30)
    # ========================================================================

    if all_high_gaps:
        print(f"\n{'='*120}")
        print(f"HIGH SEVERITY GAPS ({len(all_high_gaps)} total) -- First 50")
        print("=" * 120)

        grouped = defaultdict(list)
        for agent, trip, gap in all_high_gaps:
            grouped[(agent, trip)].append(gap)

        shown = 0
        for (agent, trip), gaps in sorted(grouped.items()):
            print(f"\n  [{agent}] [{trip}] ({len(gaps)} gaps):")
            for g in gaps[:8]:
                print(f"    {g}")
            if len(gaps) > 8:
                print(f"    ... and {len(gaps) - 8} more in this group")
            shown += min(len(gaps), 8)
            if shown > 50:
                break

    # ========================================================================
    # SPECIAL VALIDATION ISSUES
    # ========================================================================

    high_special = [(a, t, s) for a, t, s in all_special if "[HIGH]" in s]
    medium_special = [(a, t, s) for a, t, s in all_special if "[MEDIUM]" in s]
    low_special = [(a, t, s) for a, t, s in all_special if "[LOW]" in s]

    if all_special:
        print(f"\n{'='*120}")
        print(f"SPECIAL VALIDATION ISSUES ({len(all_special)} total: {len(high_special)} HIGH, {len(medium_special)} MEDIUM, {len(low_special)} LOW)")
        print("=" * 120)

        if high_special:
            print(f"\n  --- HIGH SPECIAL ({len(high_special)}) ---")
            # Group by pattern
            pattern_counts = defaultdict(int)
            for a, t, s in high_special:
                # Extract pattern: "has 'currency'=CNY but no 'currency_local'"
                if "currency" in s and "currency_local" in s:
                    pattern_counts[f"[{a}][{t}] has 'currency' but no 'currency_local'"] += 1
                elif "no currency at all" in s:
                    pattern_counts[f"[{a}][{t}] has cost but no currency at all"] += 1
                else:
                    pattern_counts[s] += 1
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
                print(f"    {pattern}  (x{count})")

        if medium_special:
            print(f"\n  --- MEDIUM SPECIAL ({len(medium_special)}) ---")
            pattern_counts = defaultdict(int)
            for a, t, s in medium_special:
                if "signature_dishes" in s:
                    field = "signature_dishes_base" if "base" in s else "signature_dishes_local"
                    pattern_counts[f"[{a}][{t}] missing '{field}'"] += 1
                elif "name_local has English" in s:
                    pattern_counts[f"[{a}][{t}] name_local contains English"] += 1
                elif "missing 'icon'" in s:
                    pattern_counts[f"[{a}][{t}] travel_segment missing 'icon'"] += 1
                elif "missing 'type_local'" in s:
                    pattern_counts[f"[{a}][{t}] travel_segment missing 'type_local'"] += 1
                else:
                    pattern_counts[s[:80]] += 1
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
                print(f"    {pattern}  (x{count})")

        if low_special:
            print(f"\n  --- LOW SPECIAL ({len(low_special)}) ---")
            pattern_counts = defaultdict(int)
            for a, t, s in low_special:
                if "stars" in s:
                    pattern_counts[f"[{a}][{t}] missing 'stars'"] += 1
                elif "booking_required" in s:
                    pattern_counts[f"[{a}][{t}] missing 'booking_required'"] += 1
                else:
                    pattern_counts[s[:80]] += 1
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
                print(f"    {pattern}  (x{count})")

    # ========================================================================
    # LOW SEVERITY (Optional) GAPS - Summary
    # ========================================================================

    all_low = []
    for agent, trip, count, rp, rt, op, ot, high, low, special in rows:
        all_low.extend(low)

    total_legacy_opt = len([g for g in all_low if g.startswith("LEGACY OPT")])
    total_missing_opt = len([g for g in all_low if g.startswith("MISSING OPT")])

    print(f"\n{'='*120}")
    print(f"LOW SEVERITY GAPS -- Optional Fields ({len(all_low)} total)")
    print("=" * 120)
    print(f"  Caused by legacy field naming: {total_legacy_opt}")
    print(f"  Truly missing (no data):       {total_missing_opt}")

    # Summarize by field name
    field_counts = defaultdict(lambda: {"legacy": 0, "missing": 0})
    for g in all_low:
        match = re.search(r"'(\w+)'", g)
        if match:
            f = match.group(1)
            if g.startswith("LEGACY"):
                field_counts[f]["legacy"] += 1
            else:
                field_counts[f]["missing"] += 1
    print(f"\n  {'OPTIONAL FIELD':<30} {'LEGACY':>8} {'MISSING':>8} {'TOTAL':>8}")
    print(f"  {'-'*60}")
    for field, counts in sorted(field_counts.items(), key=lambda x: -(x[1]["legacy"] + x[1]["missing"])):
        total = counts["legacy"] + counts["missing"]
        print(f"  {field:<30} {counts['legacy']:>8} {counts['missing']:>8} {total:>8}")

    # ========================================================================
    # FINAL VERDICT
    # ========================================================================

    print(f"\n{'='*160}")
    print("FINAL VERDICT")
    print("=" * 160)
    print(f"  Required field compliance:   {grand_rp}/{grand_rt} ({grand_req_pct:.1f}%)")
    print(f"  Optional field coverage:     {grand_op}/{grand_ot} ({grand_opt_pct:.1f}%)")
    print(f"  Total field coverage:        {grand_rp + grand_op}/{grand_rt + grand_ot} ({grand_tot_pct:.1f}%)")
    print(f"  HIGH severity req gaps:      {len(all_high_gaps)}")
    print(f"    - Legacy field names:      {len(legacy_gaps)}")
    print(f"    - Truly missing:           {len(missing_gaps)}")
    print(f"  Special HIGH issues:         {len(high_special)}")
    print(f"  Special MEDIUM issues:       {len(medium_special)}")
    print(f"  Special LOW issues:          {len(low_special)}")

    if len(all_high_gaps) == 0 and len(high_special) == 0:
        print(f"\n  STATUS: PASS")
    elif len(all_high_gaps) > 0:
        print(f"\n  STATUS: FAIL")
        print(f"\n  PRIMARY ROOT CAUSE: Dev agents added schema-required fields to SOME files but")
        print(f"  failed to rename legacy fields (e.g., 'currency'->'currency_local', 'type'->'type_base',")
        print(f"  'cuisine'->'cuisine_base', 'amenities'->'amenities_base') in others.")
        print(f"  {len(legacy_gaps)}/{len(all_high_gaps)} ({len(legacy_gaps)/max(len(all_high_gaps),1)*100:.1f}%) of required-field gaps are caused by legacy field names.")
    else:
        print(f"\n  STATUS: WARNING -- Required fields OK but {len(high_special)} high special issues")

    print("=" * 160)

    return 1 if (len(all_high_gaps) > 0 or len(high_special) > 0) else 0


if __name__ == "__main__":
    sys.exit(run_audit())
