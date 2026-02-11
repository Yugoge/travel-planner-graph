#!/usr/bin/env python3
"""
Plan Data Validation — pre-HTML-generation gate
=================================================
Single source of truth for validating all agent data files against schemas.
Run this as the last step before generate-html-interactive.py.

Checks 6 categories:
  1. Schema Structure  (envelope, day-level keys)
  2. Field Presence    (required=HIGH, optional=LOW)
  3. Field Format      (type, pattern, range)
  4. Semantic Content  (name_local English, currency region, timeline overlaps, budget sums)
  5. Legacy Fields     (old field names that should be renamed)
  6. Cross-Agent       (day count, date, location consistency)

Usage:
  python3 plan-validate.py                              # all trips
  python3 plan-validate.py china-feb-15-mar-7-2026-...  # one trip
  python3 plan-validate.py --json                       # JSON to stdout
  python3 plan-validate.py --min-severity MEDIUM        # filter
  python3 plan-validate.py --agent meals                # one agent
"""

import json
import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "schemas"
DATA_DIR = PROJECT_ROOT / "data"

LEGACY_FIELD_MAP = {
    "currency": "currency_local",
    "type": "type_base",
    "cuisine": "cuisine_base",
    "amenities": "amenities_base",
    "notes": "notes_base",
    "mode": "type_base",
    "from": "from_base",
    "to": "to_base",
    "name": "name_base",  # DEPRECATED: Use name_base or name_local
}

CURRENCY_REGION = {
    "chongqing": "CNY", "beijing": "CNY", "shanghai": "CNY", "chengdu": "CNY",
    "bazhong": "CNY", "guangzhou": "CNY", "shenzhen": "CNY", "xi'an": "CNY",
    "hangzhou": "CNY", "nanjing": "CNY", "kunming": "CNY", "harbin": "CNY",
    "sanya": "CNY", "guilin": "CNY", "suzhou": "CNY", "wuhan": "CNY",
    "changsha": "CNY", "lhasa": "CNY", "zhangjiajie": "CNY",
    "hong kong": "HKD", "macau": "MOP", "taipei": "TWD",
}

ENGLISH_PLACEHOLDERS = ["Optional", "Alternative", "TBD", "N/A", "None", "Item "]

# Agents that don't have the standard "name_local contains English" check
AGENTS_WITH_LOCAL = {"meals", "attractions", "entertainment", "accommodation", "shopping"}


class Severity(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    def __ge__(self, other):
        order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
        return order[self.value] <= order[other.value]


class Category(Enum):
    STRUCTURE = "structure"
    PRESENCE = "presence"
    FORMAT = "format"
    SEMANTIC = "semantic"
    LEGACY = "legacy"
    CROSS_AGENT = "cross_agent"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    severity: Severity
    category: Category
    agent: str
    trip: str
    day: int
    label: str
    field: str
    message: str


@dataclass
class AgentConfig:
    """How to extract items from an agent's data.days[] entries."""
    item_def: str           # key in schema $defs for item schema
    mode: str               # "named_keys" | "array" | "singular" | "object_map"
    keys: list              # day-level keys to extract from
    optional_key: bool = False  # key may be absent (e.g., location_change)


AGENT_CONFIGS = {
    "meals": AgentConfig("meal_item", "named_keys", ["breakfast", "lunch", "dinner"]),
    "attractions": AgentConfig("attraction_item", "array", ["attractions"]),
    "entertainment": AgentConfig("entertainment_item", "array", ["entertainment"]),
    "accommodation": AgentConfig("accommodation_item", "singular", ["accommodation"]),
    "shopping": AgentConfig("shopping_item", "array", ["shopping"]),
    "transportation": AgentConfig("location_change", "singular", ["location_change"], optional_key=True),
    "budget": AgentConfig("budget_categories", "singular", ["budget"]),
}

# Timeline is special — two item types in one file
TIMELINE_CONFIGS = {
    "timeline_activity": AgentConfig("timeline_activity", "object_map", ["timeline"]),
    "travel_segment": AgentConfig("travel_segment", "array", ["travel_segments"], optional_key=True),
}


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

class SchemaRegistry:
    def __init__(self):
        self._schemas = {}
        self._load_all()

    def _load_all(self):
        for f in SCHEMA_DIR.glob("*.schema.json"):
            with open(f, encoding="utf-8") as fh:
                schema = json.load(fh)
            self._schemas[f.name] = schema

    def _resolve_ref(self, ref: str) -> dict:
        """Resolve a $ref string like 'poi-common.schema.json#/$defs/coordinates'."""
        if "#" not in ref:
            return {}
        file_part, path_part = ref.split("#", 1)
        schema = self._schemas.get(file_part, {})
        for seg in path_part.strip("/").split("/"):
            schema = schema.get(seg, {})
        return schema

    def get_item_fields(self, agent: str, item_def: str):
        """Return (required_fields, optional_fields, properties_dict) for an item def."""
        schema_file = f"{agent}.schema.json"
        schema = self._schemas.get(schema_file, {})
        defs = schema.get("$defs", {})
        item_schema = defs.get(item_def, {})
        required = list(item_schema.get("required", []))
        props = dict(item_schema.get("properties", {}))
        optional = [k for k in props if k not in required]
        return required, optional, props

    def resolve_field_type(self, field_schema: dict) -> dict:
        """Resolve a field schema, following $ref if needed."""
        if "$ref" in field_schema:
            return self._resolve_ref(field_schema["$ref"])
        return field_schema

    def get_day_entry_required(self, agent: str) -> list:
        schema_file = f"{agent}.schema.json"
        schema = self._schemas.get(schema_file, {})
        day_entry = schema.get("$defs", {}).get("day_entry", {})
        return list(day_entry.get("required", []))

    def get_envelope_agent_name(self, agent: str) -> str:
        schema_file = f"{agent}.schema.json"
        schema = self._schemas.get(schema_file, {})
        return schema.get("properties", {}).get("agent", {}).get("const", agent)


# ---------------------------------------------------------------------------
# Item extraction
# ---------------------------------------------------------------------------

@dataclass
class ExtractedItem:
    data: dict
    agent: str
    item_def: str
    trip: str
    day_num: int
    date: str
    location: str
    label: str


def extract_items(agent: str, config: AgentConfig, data: dict, trip: str) -> list:
    days = data.get("data", {}).get("days", [])
    items = []

    for day in days:
        dn = day.get("day", 0)
        dt = day.get("date", "")
        loc = day.get("location", "")

        if config.mode == "named_keys":
            for key in config.keys:
                if key in day and isinstance(day[key], dict):
                    name = day[key].get("name_base", key)
                    items.append(ExtractedItem(
                        day[key], agent, config.item_def, trip,
                        dn, dt, loc, f"Day {dn} ({dt}) {key}: {name}"))

        elif config.mode == "array":
            key = config.keys[0]
            for idx, item in enumerate(day.get(key, [])):
                name = item.get("name_base", f"#{idx}")
                items.append(ExtractedItem(
                    item, agent, config.item_def, trip,
                    dn, dt, loc, f"Day {dn} ({dt}) {key}[{idx}]: {name}"))

        elif config.mode == "singular":
            key = config.keys[0]
            if key in day and isinstance(day[key], dict):
                name = day[key].get("name_base", day[key].get("from_base", key))
                items.append(ExtractedItem(
                    day[key], agent, config.item_def, trip,
                    dn, dt, loc, f"Day {dn} ({dt}) {key}: {name}"))

        elif config.mode == "object_map":
            key = config.keys[0]
            obj = day.get(key, {})
            for act_name, act_data in obj.items():
                if isinstance(act_data, dict):
                    items.append(ExtractedItem(
                        act_data, agent, config.item_def, trip,
                        dn, dt, loc, f"Day {dn} ({dt}) {act_name}"))

    return items


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def check_envelope(agent: str, data: dict, trip: str, registry: SchemaRegistry) -> list:
    """Category 1: Envelope validation."""
    issues = []
    expected_name = registry.get_envelope_agent_name(agent)

    if data.get("agent") != expected_name:
        issues.append(Issue(Severity.HIGH, Category.STRUCTURE, agent, trip, 0, "",
                            "agent", f"Expected agent='{expected_name}', got '{data.get('agent')}'"))
    if data.get("status") != "complete":
        issues.append(Issue(Severity.HIGH, Category.STRUCTURE, agent, trip, 0, "",
                            "status", f"Expected status='complete', got '{data.get('status')}'"))
    d = data.get("data")
    if not isinstance(d, dict):
        issues.append(Issue(Severity.HIGH, Category.STRUCTURE, agent, trip, 0, "",
                            "data", "Missing or non-object 'data' field"))
        return issues
    days = d.get("days")
    if not isinstance(days, list) or len(days) == 0:
        issues.append(Issue(Severity.HIGH, Category.STRUCTURE, agent, trip, 0, "",
                            "data.days", "Missing or empty 'data.days' array"))
    return issues


def check_day_structure(agent: str, data: dict, trip: str, registry: SchemaRegistry) -> list:
    """Category 1: Day-level required keys."""
    issues = []
    required_keys = registry.get_day_entry_required(agent)
    days = data.get("data", {}).get("days", [])

    for day in days:
        dn = day.get("day", 0)
        for key in required_keys:
            if key == "day":
                continue  # trivially present
            if key not in day:
                issues.append(Issue(Severity.HIGH, Category.STRUCTURE, agent, trip, dn,
                                    f"Day {dn}", key, f"Day-level required key '{key}' missing"))
    return issues


def _field_present(item: dict, field: str) -> bool:
    """Check if a field is present with a valid non-empty value."""
    val = item.get(field)
    if val is None:
        return False
    if field == "cost":
        return isinstance(val, (int, float))
    if field == "time":
        return isinstance(val, dict) and "start" in val and "end" in val
    if field in ("amenities_base", "amenities_local"):
        return isinstance(val, list) and len(val) > 0
    if field == "stars":
        return True  # None already filtered above; 0 is valid
    if field == "booking_required":
        return isinstance(val, bool)
    if field == "coordinates":
        return isinstance(val, dict) and "lat" in val and "lng" in val
    if field == "search_results":
        return isinstance(val, list)
    if field == "duration_minutes":
        return isinstance(val, (int, float))
    if isinstance(val, str):
        return val.strip() != ""
    return True


def check_field_presence(items: list, agent: str, registry: SchemaRegistry) -> tuple:
    """Category 2: Required and optional field presence.
    Returns (issues, req_present, req_total, opt_present, opt_total)."""
    issues = []
    rp = rt = op = ot = 0

    if not items:
        return issues, rp, rt, op, ot

    item_def = items[0].item_def
    required, optional, _ = registry.get_item_fields(
        "timeline" if agent in ("timeline", "timeline_segs") else agent,
        item_def)

    for ei in items:
        for f in required:
            rt += 1
            if _field_present(ei.data, f):
                rp += 1
            else:
                issues.append(Issue(Severity.HIGH, Category.PRESENCE, agent, ei.trip,
                                    ei.day_num, ei.label, f, f"Required field '{f}' missing"))
        for f in optional:
            ot += 1
            if _field_present(ei.data, f):
                op += 1
            else:
                issues.append(Issue(Severity.LOW, Category.PRESENCE, agent, ei.trip,
                                    ei.day_num, ei.label, f, f"Optional field '{f}' missing"))

    return issues, rp, rt, op, ot


def check_field_format(items: list, agent: str, registry: SchemaRegistry) -> list:
    """Category 3: Type and format validation on present fields."""
    issues = []
    hhmm = re.compile(r"^[0-2][0-9]:[0-5][0-9]$")
    currency_re = re.compile(r"^[A-Z]{3}$")

    for ei in items:
        d = ei.data

        # cost: number >= 0
        cost = d.get("cost")
        if cost is not None:
            if not isinstance(cost, (int, float)):
                issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                    ei.day_num, ei.label, "cost", f"cost is not a number: {type(cost).__name__}"))
            elif cost < 0:
                issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                    ei.day_num, ei.label, "cost", f"cost is negative: {cost}"))

        # currency_local: ^[A-Z]{3}$
        cl = d.get("currency_local")
        if cl is not None and not currency_re.match(str(cl)):
            issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                ei.day_num, ei.label, "currency_local", f"Invalid currency code: '{cl}'"))

        # time object: {start: HH:MM, end: HH:MM}
        t = d.get("time")
        if isinstance(t, dict):
            for k in ("start", "end"):
                v = t.get(k, "")
                if v and not hhmm.match(str(v)):
                    issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                        ei.day_num, ei.label, f"time.{k}", f"Invalid HH:MM: '{v}'"))

        # departure_time / arrival_time: plain HH:MM strings
        for tf in ("departure_time", "arrival_time", "start_time", "end_time"):
            v = d.get(tf)
            if v is not None:
                if isinstance(v, dict):
                    issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                        ei.day_num, ei.label, tf, f"Should be HH:MM string, got object"))
                elif isinstance(v, str) and v and not hhmm.match(v):
                    issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                        ei.day_num, ei.label, tf, f"Invalid HH:MM: '{v}'"))

        # coordinates: {lat: [-90,90], lng: [-180,180]}
        coords = d.get("coordinates")
        if isinstance(coords, dict) and "lat" in coords and "lng" in coords:
            lat, lng = coords.get("lat"), coords.get("lng")
            if isinstance(lat, (int, float)) and not (-90 <= lat <= 90):
                issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                    ei.day_num, ei.label, "coordinates.lat", f"Out of range: {lat}"))
            if isinstance(lng, (int, float)) and not (-180 <= lng <= 180):
                issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                    ei.day_num, ei.label, "coordinates.lng", f"Out of range: {lng}"))

        # stars: number 0-5 or null
        stars = d.get("stars")
        if stars is not None and isinstance(stars, (int, float)):
            if not (0 <= stars <= 5):
                issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                    ei.day_num, ei.label, "stars", f"Out of range 0-5: {stars}"))

        # booking_required: boolean
        br = d.get("booking_required")
        if br is not None and not isinstance(br, bool):
            issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                ei.day_num, ei.label, "booking_required", f"Not boolean: {type(br).__name__}"))

        # search_results[]: each needs {skill, type, url, display_text}
        sr = d.get("search_results")
        if isinstance(sr, list):
            for idx, entry in enumerate(sr):
                if isinstance(entry, dict):
                    for k in ("skill", "type", "url", "display_text"):
                        if k not in entry:
                            issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                                ei.day_num, ei.label, f"search_results[{idx}].{k}",
                                                f"Missing key '{k}' in search_result"))

        # amenities_base/local: array of strings
        for af in ("amenities_base", "amenities_local"):
            av = d.get(af)
            if isinstance(av, list):
                for idx, elem in enumerate(av):
                    if not isinstance(elem, str):
                        issues.append(Issue(Severity.MEDIUM, Category.FORMAT, agent, ei.trip,
                                            ei.day_num, ei.label, f"{af}[{idx}]",
                                            f"Expected string, got {type(elem).__name__}"))

    return issues


# Small words that stay lowercase in title case (unless first word of a segment)
_TITLE_SMALL_WORDS = {"a", "an", "and", "at", "but", "by", "for", "in", "nor",
                       "of", "on", "or", "so", "the", "to", "up", "yet"}


def _smart_title(text: str) -> str:
    """Apply smart Title Case that preserves acronyms and keeps small words lowercase.

    Splits on ' / ' first (category separators), then applies per-segment:
      - All-uppercase words (acronyms like UNESCO, AAAA+) stay uppercase
      - Small words (and, or, of, the, ...) stay lowercase unless first word
      - Everything else gets standard Title Case
    """
    segments = text.split(" / ")
    result_segments = []
    for segment in segments:
        words = segment.split()
        titled_words = []
        for idx, word in enumerate(words):
            # Preserve acronyms: all-uppercase words (allow trailing +)
            stripped = word.rstrip("+")
            if stripped.isupper() and len(stripped) > 1:
                titled_words.append(word)
            # Small words stay lowercase unless first word of segment
            elif word.lower() in _TITLE_SMALL_WORDS and idx > 0:
                titled_words.append(word.lower())
            # Normal words get title case
            else:
                titled_words.append(word.capitalize())
        result_segments.append(" ".join(titled_words))
    return " / ".join(result_segments)


def check_semantics(items: list, agent: str, all_data: dict, trip: str, trip_dir: Path) -> list:
    """Category 4: Semantic / content checks."""
    issues = []

    # 4a. name_local should not contain English placeholders
    if agent in AGENTS_WITH_LOCAL:
        for ei in items:
            nl = ei.data.get("name_local", "")
            if isinstance(nl, str):
                for kw in ENGLISH_PLACEHOLDERS:
                    if kw in nl:
                        issues.append(Issue(Severity.MEDIUM, Category.SEMANTIC, agent, ei.trip,
                                            ei.day_num, ei.label, "name_local",
                                            f"Contains English placeholder: '{kw}' in '{nl}'"))
                        break

    # 4b. type_base Title Case (attractions)
    if agent == "attractions":
        for ei in items:
            tb = ei.data.get("type_base", "")
            if isinstance(tb, str) and tb and tb != _smart_title(tb):
                issues.append(Issue(Severity.MEDIUM, Category.SEMANTIC, agent, ei.trip,
                                    ei.day_num, ei.label, "type_base",
                                    f"Not Title Case: '{tb}' (expected '{_smart_title(tb)}')"))

    # 4c. Currency-region consistency
    if agent in AGENTS_WITH_LOCAL:
        for ei in items:
            cl = ei.data.get("currency_local", "")
            loc = (ei.location or "").lower()
            expected = CURRENCY_REGION.get(loc)
            if expected and cl and cl != expected:
                issues.append(Issue(Severity.MEDIUM, Category.SEMANTIC, agent, ei.trip,
                                    ei.day_num, ei.label, "currency_local",
                                    f"Expected '{expected}' for {ei.location}, got '{cl}'"))

    # 4d. Timeline chronological ordering
    if agent == "timeline":
        timeline_data = all_data.get("timeline", {})
        days = timeline_data.get("data", {}).get("days", [])
        intentional_kw = ["optional", "alternative", " or ", "in-park"]

        for day in days:
            dn = day.get("day", 0)
            tl = day.get("timeline", {})
            timed = []
            for name, sched in tl.items():
                if isinstance(sched, dict):
                    s, e = sched.get("start_time", ""), sched.get("end_time", "")
                    if s and e:
                        timed.append((name, s, e))
            timed.sort(key=lambda x: x[1])
            for i in range(len(timed) - 1):
                cn, cs, ce = timed[i]
                nn, ns, ne = timed[i + 1]
                if ce > ns:
                    combined = (cn + " " + nn).lower()
                    intentional = any(kw in combined for kw in intentional_kw)
                    sev = Severity.INFO if intentional else Severity.MEDIUM
                    issues.append(Issue(sev, Category.SEMANTIC, "timeline", trip, dn,
                                        f"Day {dn}", "timeline",
                                        f"'{cn}' ({cs}-{ce}) overlaps '{nn}' ({ns}-{ne})"
                                        + (" [intentional]" if intentional else "")))

    # 4e. Transportation departure < arrival
    if agent == "transportation":
        for ei in items:
            dep = ei.data.get("departure_time", "")
            arr = ei.data.get("arrival_time", "")
            if dep and arr and dep >= arr:
                issues.append(Issue(Severity.MEDIUM, Category.SEMANTIC, agent, ei.trip,
                                    ei.day_num, ei.label, "departure_time",
                                    f"Departure ({dep}) >= arrival ({arr})"))

    # 4f. Budget sum consistency
    if agent == "budget":
        cats = ["meals", "accommodation", "activities", "shopping", "transportation"]
        for ei in items:
            stated = ei.data.get("total", 0)
            if not stated:
                continue
            computed = sum(ei.data.get(c, 0) for c in cats)
            if abs(computed - stated) > 1.0:
                issues.append(Issue(Severity.MEDIUM, Category.SEMANTIC, agent, ei.trip,
                                    ei.day_num, ei.label, "budget.total",
                                    f"Category sum={computed:.0f} != total={stated:.0f} (diff={abs(computed - stated):.0f})"))

    # 4g. Conditional _base/_local pair consistency
    # If a _base field has content, the corresponding _local field must also exist and be non-empty.
    for ei in items:
        for key, val in ei.data.items():
            if not key.endswith("_base"):
                continue
            local_key = key[:-5] + "_local"
            # Check if the _base field has meaningful content
            base_has_content = False
            if isinstance(val, str) and val.strip():
                base_has_content = True
            elif isinstance(val, list) and len(val) > 0:
                base_has_content = True
            if not base_has_content:
                continue
            # _base has content; check _local
            local_val = ei.data.get(local_key)
            local_missing = False
            if local_val is None:
                local_missing = True
            elif isinstance(local_val, str) and not local_val.strip():
                local_missing = True
            elif isinstance(local_val, list) and len(local_val) == 0:
                local_missing = True
            if local_missing:
                issues.append(Issue(
                    Severity.MEDIUM, Category.SEMANTIC, agent, ei.trip,
                    ei.day_num, ei.label, local_key,
                    f"'{key}' has content but '{local_key}' is missing or empty"))

    return issues


def check_legacy_fields(items: list, agent: str) -> list:
    """Category 5: Detect legacy field names."""
    issues = []
    for ei in items:
        for legacy, schema_name in LEGACY_FIELD_MAP.items():
            if legacy in ei.data:
                has_schema = schema_name in ei.data
                if has_schema:
                    # Both present
                    old_val = ei.data[legacy]
                    new_val = ei.data[schema_name]
                    if old_val != new_val:
                        issues.append(Issue(Severity.MEDIUM, Category.LEGACY, agent, ei.trip,
                                            ei.day_num, ei.label, legacy,
                                            f"MISMATCH: '{legacy}'={_trunc(old_val)} vs '{schema_name}'={_trunc(new_val)}"))
                    else:
                        issues.append(Issue(Severity.INFO, Category.LEGACY, agent, ei.trip,
                                            ei.day_num, ei.label, legacy,
                                            f"BOTH: '{legacy}' and '{schema_name}' both present (redundant)"))
                else:
                    # Legacy only — schema field missing
                    issues.append(Issue(Severity.INFO, Category.LEGACY, agent, ei.trip,
                                        ei.day_num, ei.label, legacy,
                                        f"LEGACY_ONLY: has '{legacy}' but not '{schema_name}'"))
    return issues


def check_cross_agent(all_data: dict, trip: str) -> list:
    """Category 6: Cross-agent consistency."""
    issues = []

    # Collect day counts and dates per agent
    day_info = {}  # agent -> {day_num: {date, location}}
    for agent_name, adata in all_data.items():
        days = adata.get("data", {}).get("days", [])
        info = {}
        for day in days:
            dn = day.get("day", 0)
            info[dn] = {"date": day.get("date", ""), "location": day.get("location", "")}
        day_info[agent_name] = info

    # Find reference agent (one with most days)
    if not day_info:
        return issues
    ref_agent = max(day_info, key=lambda a: len(day_info[a]))
    ref_days = day_info[ref_agent]

    # Check day count consistency (skip transportation — may have fewer entries)
    for agent_name, info in day_info.items():
        if agent_name == "transportation":
            continue
        if len(info) != len(ref_days):
            issues.append(Issue(Severity.HIGH, Category.CROSS_AGENT, agent_name, trip, 0, "",
                                "days", f"Day count={len(info)}, expected {len(ref_days)} (ref: {ref_agent})"))

    # Check date consistency
    for dn, ref in ref_days.items():
        for agent_name, info in day_info.items():
            if dn in info and info[dn]["date"] and ref["date"]:
                if info[dn]["date"] != ref["date"]:
                    issues.append(Issue(Severity.HIGH, Category.CROSS_AGENT, agent_name, trip, dn,
                                        f"Day {dn}", "date",
                                        f"Date='{info[dn]['date']}', expected '{ref['date']}' (ref: {ref_agent})"))

    # Check location consistency
    for dn, ref in ref_days.items():
        if not ref["location"]:
            continue
        for agent_name, info in day_info.items():
            if dn in info and info[dn]["location"]:
                if info[dn]["location"].lower() != ref["location"].lower():
                    issues.append(Issue(Severity.MEDIUM, Category.CROSS_AGENT, agent_name, trip, dn,
                                        f"Day {dn}", "location",
                                        f"Location='{info[dn]['location']}', ref='{ref['location']}' ({ref_agent})"))

    # Budget sum vs actual costs
    budget_data = all_data.get("budget", {})
    meals_data = all_data.get("meals", {})
    if budget_data and meals_data:
        bdays = {d.get("day"): d for d in budget_data.get("data", {}).get("days", [])}
        mdays = {d.get("day"): d for d in meals_data.get("data", {}).get("days", [])}
        for dn in bdays:
            if dn not in mdays:
                continue
            budget_meals = bdays[dn].get("budget", {}).get("meals", 0)
            actual = 0
            for mt in ("breakfast", "lunch", "dinner"):
                meal = mdays[dn].get(mt, {})
                if isinstance(meal, dict):
                    actual += meal.get("cost", 0)
            if budget_meals and actual and abs(budget_meals - actual) / max(budget_meals, 1) > 0.25:
                issues.append(Issue(Severity.LOW, Category.CROSS_AGENT, "budget", trip, dn,
                                    f"Day {dn}", "budget.meals",
                                    f"Budget meals={budget_meals:.0f} vs actual={actual:.0f} (>25% diff)"))

    return issues


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def _trunc(val, maxlen=40):
    s = str(val)
    return s if len(s) <= maxlen else s[:maxlen] + "..."


def load_agent_data(trip_dir: Path, agent: str) -> dict:
    path = trip_dir / f"{agent}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_pipeline(trip_dirs: list, registry: SchemaRegistry,
                 agent_filter: str = None) -> tuple:
    """Run all validators. Returns (all_issues, metrics)."""
    all_issues = []
    metrics = {}  # (agent, trip) -> {items, rp, rt, op, ot}

    agents_to_check = list(AGENT_CONFIGS.keys()) + ["timeline"]
    if agent_filter:
        agents_to_check = [a for a in agents_to_check if a == agent_filter]

    for trip_dir in trip_dirs:
        trip = trip_dir.name

        # Load all agent data for cross-agent checks
        all_data = {}
        for a in list(AGENT_CONFIGS.keys()) + ["timeline"]:
            d = load_agent_data(trip_dir, a)
            if d:
                all_data[a] = d

        for agent in agents_to_check:
            if agent not in all_data:
                all_issues.append(Issue(Severity.HIGH, Category.STRUCTURE, agent, trip, 0,
                                        "", "", f"File {agent}.json not found"))
                continue

            data = all_data[agent]

            # 1. Envelope
            all_issues.extend(check_envelope(agent, data, trip, registry))

            # 2. Day structure
            all_issues.extend(check_day_structure(agent, data, trip, registry))

            if agent == "timeline":
                # Timeline has two item types
                for sub_name, config in TIMELINE_CONFIGS.items():
                    display_agent = "timeline" if sub_name == "timeline_activity" else "timeline_segs"
                    items = extract_items("timeline", config, data, trip)

                    # Field presence
                    pres_issues, rp, rt, op, ot = check_field_presence(items, display_agent, registry)
                    all_issues.extend(pres_issues)
                    metrics[(display_agent, trip)] = {"items": len(items), "rp": rp, "rt": rt, "op": op, "ot": ot}

                    # Field format
                    all_issues.extend(check_field_format(items, display_agent, registry))

                    # Legacy
                    all_issues.extend(check_legacy_fields(items, display_agent))

                # Semantics (timeline overlaps) — once for whole timeline
                all_issues.extend(check_semantics([], "timeline", all_data, trip, trip_dir))

            else:
                config = AGENT_CONFIGS[agent]
                items = extract_items(agent, config, data, trip)

                # Field presence
                pres_issues, rp, rt, op, ot = check_field_presence(items, agent, registry)
                all_issues.extend(pres_issues)
                metrics[(agent, trip)] = {"items": len(items), "rp": rp, "rt": rt, "op": op, "ot": ot}

                # Field format
                all_issues.extend(check_field_format(items, agent, registry))

                # Semantics
                all_issues.extend(check_semantics(items, agent, all_data, trip, trip_dir))

                # Legacy
                all_issues.extend(check_legacy_fields(items, agent))

        # Cross-agent (once per trip)
        if not agent_filter:
            all_issues.extend(check_cross_agent(all_data, trip))

    return all_issues, metrics


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def format_table(issues: list, metrics: dict, min_severity: Severity, trips: list):
    """Print human-readable report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    w = 140
    print("=" * w)
    print(f"UNIFIED DATA VALIDATION REPORT — {now}")
    print("=" * w)
    print()

    # Summary table
    header = (f"{'AGENT':<18} | {'TRIP':<30} | {'ITEMS':>5} | {'REQ':>9} | {'OPT':>9} "
              f"| {'REQ%':>6} | {'OPT%':>6} | {'HIGH':>4} | {'MED':>4} | {'LOW':>4} | {'INFO':>4}")
    sep = "-" * len(header)
    print(header)
    print(sep)

    grand_rp = grand_rt = grand_op = grand_ot = 0

    agent_order = ["meals", "attractions", "entertainment", "accommodation", "shopping",
                   "transportation", "budget", "timeline", "timeline_segs"]

    for trip_dir in trips:
        trip = trip_dir.name
        for agent in agent_order:
            m = metrics.get((agent, trip))
            if not m:
                continue
            rp, rt, op, ot = m["rp"], m["rt"], m["op"], m["ot"]
            grand_rp += rp; grand_rt += rt; grand_op += op; grand_ot += ot

            agent_issues = [i for i in issues if i.agent == agent and i.trip == trip]
            high_c = sum(1 for i in agent_issues if i.severity == Severity.HIGH)
            med_c = sum(1 for i in agent_issues if i.severity == Severity.MEDIUM)
            low_c = sum(1 for i in agent_issues if i.severity == Severity.LOW)
            info_c = sum(1 for i in agent_issues if i.severity == Severity.INFO)

            req_pct = (rp / rt * 100) if rt else 100.0
            opt_pct = (op / ot * 100) if ot else 100.0
            flag = " !!" if req_pct < 100 else ""

            # Shorten trip name for display
            trip_short = trip[:28] + ".." if len(trip) > 30 else trip

            print(f"{agent:<18} | {trip_short:<30} | {m['items']:>5} | {rp:>4}/{rt:<4}"
                  f" | {op:>4}/{ot:<4} | {req_pct:5.1f}%{flag} | {opt_pct:5.1f}%"
                  f" | {high_c:>4} | {med_c:>4} | {low_c:>4} | {info_c:>4}")

    print(sep)
    grand_req = (grand_rp / grand_rt * 100) if grand_rt else 100.0
    grand_opt = (grand_op / grand_ot * 100) if grand_ot else 100.0
    print(f"{'TOTAL':<18} | {'':<30} | {'':>5} | {grand_rp:>4}/{grand_rt:<4}"
          f" | {grand_op:>4}/{grand_ot:<4} | {grand_req:5.1f}%  | {grand_opt:5.1f}%"
          f" | {'':>4} | {'':>4} | {'':>4} | {'':>4}")
    print()

    # HIGH issues
    high_issues = [i for i in issues if i.severity == Severity.HIGH]
    if high_issues:
        print("=" * w)
        print(f"HIGH SEVERITY ISSUES ({len(high_issues)})")
        print("=" * w)
        grouped = defaultdict(list)
        for i in high_issues:
            grouped[(i.agent, i.trip)].append(i)
        for (a, t), group in sorted(grouped.items()):
            print(f"\n  [{a}] [{_trip_label(t)}] ({len(group)} issues):")
            for g in group[:10]:
                print(f"    {g.label}: {g.field} — {g.message}")
            if len(group) > 10:
                print(f"    ... and {len(group) - 10} more")
    else:
        print(f"HIGH SEVERITY: 0 issues — all required fields present.")
    print()

    # MEDIUM issues
    if min_severity >= Severity.MEDIUM:
        med_issues = [i for i in issues if i.severity == Severity.MEDIUM]
        if med_issues:
            print("=" * w)
            print(f"MEDIUM SEVERITY ISSUES ({len(med_issues)})")
            print("=" * w)
            grouped = defaultdict(list)
            for i in med_issues:
                grouped[(i.category.value, i.agent)].append(i)
            for (cat, a), group in sorted(grouped.items()):
                print(f"\n  [{cat}][{a}] ({len(group)} issues):")
                for g in group[:8]:
                    print(f"    {g.label}: {g.field} — {g.message}")
                if len(group) > 8:
                    print(f"    ... and {len(group) - 8} more")
        print()

    # Legacy field summary
    legacy_issues = [i for i in issues if i.category == Category.LEGACY]
    if legacy_issues:
        print("=" * w)
        print(f"LEGACY FIELD REPORT ({len(legacy_issues)} items)")
        print("=" * w)
        # Summary by rename pair
        rename_counts = defaultdict(lambda: {"both": 0, "legacy_only": 0, "mismatch": 0})
        for i in legacy_issues:
            legacy_name = i.field
            schema_name = LEGACY_FIELD_MAP.get(legacy_name, "?")
            key = f"{legacy_name} -> {schema_name}"
            if "BOTH" in i.message:
                rename_counts[key]["both"] += 1
            elif "LEGACY_ONLY" in i.message:
                rename_counts[key]["legacy_only"] += 1
            elif "MISMATCH" in i.message:
                rename_counts[key]["mismatch"] += 1

        print(f"\n  {'Rename':<35} | {'LEGACY_ONLY':>11} | {'BOTH':>6} | {'MISMATCH':>8}")
        print(f"  {'-'*35}-+-{'-'*11}-+-{'-'*6}-+-{'-'*8}")
        for key, counts in sorted(rename_counts.items()):
            print(f"  {key:<35} | {counts['legacy_only']:>11} | {counts['both']:>6} | {counts['mismatch']:>8}")
        print()

    # Completeness metrics
    print("=" * w)
    print("COMPLETENESS METRICS")
    print("=" * w)
    field_coverage = defaultdict(lambda: {"present": 0, "total": 0})
    low_issues = [i for i in issues if i.severity == Severity.LOW and i.category == Category.PRESENCE]
    for i in low_issues:
        field_coverage[i.field]["total"] += 1
    # total for present = total_items - missing
    for (agent, trip), m in metrics.items():
        pass  # already tracked above

    # Group LOW presence issues by field
    missing_by_field = defaultdict(int)
    for i in low_issues:
        missing_by_field[i.field] += 1
    if missing_by_field:
        print(f"\n  {'Optional Field':<25} | {'Missing':>8}")
        print(f"  {'-'*25}-+-{'-'*8}")
        for field, count in sorted(missing_by_field.items(), key=lambda x: -x[1]):
            print(f"  {field:<25} | {count:>8}")
    print()

    # Verdict
    has_high = any(i.severity == Severity.HIGH for i in issues)
    print("=" * w)
    print(f"  Required: {grand_rp}/{grand_rt} ({grand_req:.1f}%)  |  Optional: {grand_op}/{grand_ot} ({grand_opt:.1f}%)")
    print(f"  HIGH: {len(high_issues)}  |  MEDIUM: {len([i for i in issues if i.severity == Severity.MEDIUM])}"
          f"  |  LOW: {len(low_issues)}  |  INFO: {len([i for i in issues if i.severity == Severity.INFO])}")
    print(f"\n  VERDICT: {'FAIL' if has_high else 'PASS'}")
    print("=" * w)


def _trip_label(trip: str) -> str:
    if "bucket" in trip.lower():
        return "bucket-list"
    if "china-feb" in trip.lower():
        return "itinerary"
    return trip[:20]


def to_json(issues: list, metrics: dict) -> dict:
    has_high = any(i.severity == Severity.HIGH for i in issues)
    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total": len(issues),
            "by_severity": {s.value: len([i for i in issues if i.severity == s]) for s in Severity},
            "by_category": {c.value: len([i for i in issues if i.category == c]) for c in Category},
            "pass": not has_high,
        },
        "metrics": {
            f"{a}|{t}": m for (a, t), m in metrics.items()
        },
        "issues": [
            {"severity": i.severity.value, "category": i.category.value, "agent": i.agent,
             "trip": i.trip, "day": i.day, "label": i.label, "field": i.field, "message": i.message}
            for i in issues
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Unified data validation for travel planner.")
    parser.add_argument("trips", nargs="*", help="Trip directory names (default: all)")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--json-file", type=str, help="Write JSON report to file")
    parser.add_argument("--min-severity", choices=["HIGH", "MEDIUM", "LOW", "INFO"],
                        default="LOW", help="Minimum severity to display (default: LOW)")
    parser.add_argument("--agent", type=str, help="Validate only this agent")
    args = parser.parse_args()

    # Discover trips
    if args.trips:
        trip_dirs = []
        for t in args.trips:
            p = Path(t) if Path(t).is_absolute() else DATA_DIR / t
            if p.is_dir():
                trip_dirs.append(p)
            else:
                print(f"Warning: {p} not found, skipping", file=sys.stderr)
    else:
        trip_dirs = sorted([d for d in DATA_DIR.iterdir()
                            if d.is_dir() and (d / "meals.json").exists()])

    if not trip_dirs:
        print("No trip directories found.", file=sys.stderr)
        sys.exit(2)

    registry = SchemaRegistry()
    all_issues, metrics = run_pipeline(trip_dirs, registry, agent_filter=args.agent)

    min_sev = Severity[args.min_severity]

    if args.json:
        print(json.dumps(to_json(all_issues, metrics), indent=2, ensure_ascii=False))
    else:
        format_table(all_issues, metrics, min_sev, trip_dirs)

    if args.json_file:
        with open(args.json_file, "w", encoding="utf-8") as f:
            json.dump(to_json(all_issues, metrics), f, indent=2, ensure_ascii=False)
        print(f"\nJSON report written to: {args.json_file}")

    sys.exit(1 if any(i.severity == Severity.HIGH for i in all_issues) else 0)


if __name__ == "__main__":
    main()
