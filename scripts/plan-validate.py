#!/usr/bin/env python3
"""
Plan Data Validation — pre-HTML-generation gate
=================================================
Single source of truth for validating all agent data files against schemas.
Run this as the last step before generate-html-interactive.py.

Checks 7 categories:
  1. Schema Structure  (envelope, day-level keys)
  2. Field Presence    (required=HIGH, optional=LOW)
  3. Field Format      (type, pattern, range)
  4. Semantic Content  (name_local English, currency region, timeline overlaps, budget sums)
  5. Legacy Fields     (old field names - now HIGH severity for redundancy)
  6. Cross-Agent       (day count, date, location consistency)
  7. Additional Properties (redundant fields not in schema - NEW for 100% coverage)

Usage:
  source venv/bin/activate && python scripts/plan-validate.py                     # all trips
  source venv/bin/activate && python scripts/plan-validate.py china-feb-15-...    # one trip
  source venv/bin/activate && python scripts/plan-validate.py --json              # JSON to stdout
  source venv/bin/activate && python scripts/plan-validate.py --min-severity MEDIUM  # filter
  source venv/bin/activate && python scripts/plan-validate.py --agent meals          # one agent
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
CONFIG_FILE = PROJECT_ROOT / "config" / "validation.json"

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

# ---------------------------------------------------------------------------
# Configuration — loaded from config/validation.json (required, raises if missing)
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load validation configuration. Raises if config file is missing or malformed."""
    with open(CONFIG_FILE, encoding="utf-8") as f:
        config_data = json.load(f)
    return {
        "enforce_title_case": config_data.get("enforce_title_case", True),
        "travel_segment_required_fields": config_data["travel_segment_required_fields"],
    }

CONFIG = load_config()

# Fix 8: AGENTS_WITH_LOCAL (line 67) - REMOVED, now inferred from schemas
# This will be populated dynamically by inspecting schema required fields
# See _infer_agents_with_local() below
AGENTS_WITH_LOCAL = set()


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


def _is_data_prop(prop_def: dict) -> bool:
    """True if a day_entry property references an item schema (not a structural field)."""
    if "$ref" in prop_def:
        return True
    if prop_def.get("type") == "array":
        return "$ref" in prop_def.get("items", {})
    return False


def _derive_agent_configs(schema_dir: Path) -> dict:
    """Build AGENT_CONFIGS by inspecting each agent schema's day_entry structure."""
    result = {}
    for schema_file in schema_dir.glob("*.schema.json"):
        agent = schema_file.name.replace(".schema.json", "")
        if agent in ("poi-common", "timeline"):
            continue  # timeline has TIMELINE_CONFIGS; poi-common is shared defs
        schema = json.loads(schema_file.read_text())
        defs = schema.get("$defs", {})
        day_entry = defs.get("day_entry")
        if not day_entry:
            continue
        # Exactly one item def (not day_entry) is required
        item_defs = [k for k in defs if k != "day_entry"]
        if len(item_defs) != 1:
            continue
        item_def = item_defs[0]

        day_required = set(day_entry.get("required", []))
        data_keys = []
        has_array = False
        for key, prop in day_entry.get("properties", {}).items():
            if not _is_data_prop(prop):
                continue
            data_keys.append(key)
            if prop.get("type") == "array":
                has_array = True

        if not data_keys:
            continue

        if len(data_keys) > 1 and not has_array:
            mode = "named_keys"
        elif has_array:
            mode = "array"
        else:
            mode = "singular"

        optional_key = not all(k in day_required for k in data_keys)
        result[agent] = AgentConfig(item_def, mode, data_keys, optional_key=optional_key)
    return result


# AGENT_CONFIGS derived from schemas — no hardcoding. Adding a new agent only
# requires a correctly structured schema file in schemas/. No code change needed.
AGENT_CONFIGS = _derive_agent_configs(SCHEMA_DIR)

# Timeline is special — two item types in one file (excluded from auto-derivation)
TIMELINE_CONFIGS = {
    "timeline_activity": AgentConfig("timeline_activity", "object_map", ["timeline"]),
    "travel_segment": AgentConfig("travel_segment", "array", ["travel_segments"], optional_key=True),
}

# Fix 7: Transport types (line 136) - SCHEMA-DRIVEN (no change needed)
# Root cause fix: Commit 74e660d0 added "meal" to travel_segments (schema violation)
# VALID_TRANSPORT_TYPES will be populated from transportation schema at runtime
# See _load_valid_transport_types() below
VALID_TRANSPORT_TYPES = set()

# Invalid types are now detected dynamically: any type_base not in VALID_TRANSPORT_TYPES
# that matches known non-transport patterns is flagged with HIGH severity
INVALID_TRANSPORT_TYPES = {
    "meal", "breakfast", "lunch", "dinner",  # Meals
    "attraction", "temple", "museum", "park",  # Attractions
    "entertainment", "show", "activity"  # Entertainment
}


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

class SchemaRegistry:
    def __init__(self):
        self._schemas = {}
        self._load_all()
        # Initialize schema-driven configuration after loading schemas
        self._init_schema_driven_config()

    def _load_all(self):
        for f in SCHEMA_DIR.glob("*.schema.json"):
            with open(f, encoding="utf-8") as fh:
                schema = json.load(fh)
            self._schemas[f.name] = schema

    def _init_schema_driven_config(self):
        """Initialize configuration values derived from schemas.

        Fix 8: Infer AGENTS_WITH_LOCAL from schemas instead of hardcoding
        Fix 7: Load valid transport types from transportation schema
        Fix 5: Extract budget categories from budget schema
        """
        global AGENTS_WITH_LOCAL, VALID_TRANSPORT_TYPES

        # Fix 8: Infer which agents require name_local
        # Check each agent schema for name_local in properties
        agent_item_mapping = {
            "meals": "meal_item",
            "attractions": "attraction_item",
            "entertainment": "entertainment_item",
            "accommodation": "accommodation_item",
            "shopping": "shopping_item",
            "cafe": "cafe_item",
        }

        for agent_name, item_key in agent_item_mapping.items():
            schema_file = f"{agent_name}.schema.json"
            schema = self._schemas.get(schema_file, {})
            defs = schema.get("$defs", {})
            item_schema = defs.get(item_key, {})
            properties = item_schema.get("properties", {})

            # If name_local exists in properties (even if optional), add to set
            if "name_local" in properties:
                AGENTS_WITH_LOCAL.add(agent_name)

        # Fix 7: Load valid transport types from timeline schema (travel_segment)
        # Extract from schema description which lists valid types
        timeline_schema = self._schemas.get("timeline.schema.json", {})
        travel_segment = timeline_schema.get("$defs", {}).get("travel_segment", {})
        type_base_schema = travel_segment.get("properties", {}).get("type_base", {})

        # Check for enum in type_base
        if "enum" in type_base_schema:
            VALID_TRANSPORT_TYPES.update(type_base_schema["enum"])
        else:
            # Extract from description if available
            description = type_base_schema.get("description", "")
            # Description format: "Transport type in base language (e.g., 'walk', 'taxi', ...)"
            if "e.g.," in description:
                examples_part = description.split("e.g.,")[1].strip(" )")
                # Parse comma-separated quoted values
                import re
                types = re.findall(r"'([^']+)'", examples_part)
                if types:
                    VALID_TRANSPORT_TYPES.update(types)

            # Fallback to hardcoded if schema doesn't specify
            if not VALID_TRANSPORT_TYPES:
                VALID_TRANSPORT_TYPES.update({"walk", "taxi", "metro", "bus", "train", "car", "ferry"})

    def get_budget_categories(self) -> list:
        """Fix 5: Extract budget categories from budget schema instead of hardcoding.

        Returns list of category names from schemas/budget.json $defs/budget_categories/properties.
        Excludes 'total' as it's a computed field, not a category.
        """
        budget_schema = self._schemas.get("budget.schema.json", {})
        budget_cats = budget_schema.get("$defs", {}).get("budget_categories", {})
        props = budget_cats.get("properties", {})

        # Return all properties except 'total'
        categories = [k for k in props.keys() if k != "total"]

        # Fallback if schema doesn't have expected structure
        if not categories:
            categories = ["meals", "accommodation", "activities", "shopping", "transportation"]

        return categories

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


def check_travel_segments(timeline_data: dict, trip: str) -> list:
    """Category 4d: Validate travel_segments for invalid content.

    BUG FIX: Prevents meals/attractions in travel_segments array.
    Root cause reference: Commit 74e660d0 manual merge error added "meal" to travel_segments.

    Schema specification: travel_segments should ONLY contain intra-city transportation.
    Valid types: walk, taxi, metro, bus, train, car, ferry
    Invalid: meal, breakfast, lunch, dinner, attraction, entertainment, etc.
    """
    issues = []
    days = timeline_data.get("data", {}).get("days", [])

    for day in days:
        dn = day.get("day", 0)
        segments = day.get("travel_segments", [])

        for idx, segment in enumerate(segments):
            if not isinstance(segment, dict):
                continue

            seg_name = segment.get("name_base", f"segment-{idx}")
            seg_type = segment.get("type_base", "").lower()

            # Check 1: Invalid transport type
            if seg_type and seg_type not in VALID_TRANSPORT_TYPES:
                if seg_type in INVALID_TRANSPORT_TYPES:
                    issues.append(Issue(
                        Severity.HIGH, Category.SEMANTIC, "timeline", trip, dn,
                        f"Day {dn} travel_segments[{idx}]", "type_base",
                        f"SCHEMA VIOLATION: Invalid type '{seg_type}' in travel_segments "
                        f"(travel_segments must only contain transport types: "
                        f"{', '.join(sorted(VALID_TRANSPORT_TYPES))})"
                    ))
                else:
                    issues.append(Issue(
                        Severity.MEDIUM, Category.SEMANTIC, "timeline", trip, dn,
                        f"Day {dn} travel_segments[{idx}]", "type_base",
                        f"Unknown transport type '{seg_type}' (expected: {', '.join(sorted(VALID_TRANSPORT_TYPES))})"
                    ))

            # Check 2: Required fields
            required = CONFIG.get("travel_segment_required_fields", ["name_base", "name_local", "type_base", "start_time", "end_time"])
            for field in required:
                if field not in segment or not segment[field]:
                    issues.append(Issue(
                        Severity.HIGH, Category.PRESENCE, "timeline", trip, dn,
                        f"Day {dn} travel_segments[{idx}]", field,
                        f"Required field '{field}' missing in travel_segment"
                    ))

    return issues


def check_semantics(items: list, agent: str, all_data: dict, trip: str, trip_dir: Path, registry: SchemaRegistry) -> list:
    """Category 4: Semantic / content checks."""
    issues = []

    # 4b. type_base Title Case (attractions) - Fix 6: now configurable
    if agent == "attractions" and CONFIG.get("enforce_title_case", True):
        for ei in items:
            tb = ei.data.get("type_base", "")
            if isinstance(tb, str) and tb and tb != _smart_title(tb):
                issues.append(Issue(Severity.MEDIUM, Category.SEMANTIC, agent, ei.trip,
                                    ei.day_num, ei.label, "type_base",
                                    f"Not Title Case: '{tb}' (expected '{_smart_title(tb)}')"))

    # 4d. Timeline validation
    if agent == "timeline":
        timeline_data = all_data.get("timeline", {})

        # 4d-2. Travel segments validation (NEW - prevents breakfast-in-travel_segments bug)
        issues.extend(check_travel_segments(timeline_data, trip))

        # 4d-3. Required activities validation — schema-based, no hardcoded keyword lists.
        # Both meals and accommodation use explicit ref fields on timeline entries:
        #   meal_ref: "breakfast" | "lunch" | "dinner"
        #   accommodation_ref: true
        # This eliminates keyword lists and works for any language / accommodation type.

        # Pre-compute which days have accommodation (only those need accommodation_ref check).
        acc_raw = all_data.get("accommodation", {})
        acc_days_list = acc_raw.get("data", {}).get("days", acc_raw.get("days", []))
        days_with_acc = {
            d["day"] for d in acc_days_list
            if d.get("accommodation", {}).get("name_base", "")
        }

        days = timeline_data.get("data", {}).get("days", [])
        for day in days:
            dn = day.get("day", 0)
            tl = day.get("timeline", {})
            tl_values = list(tl.values())

            # Meals: each meal type must have exactly one timeline entry with meal_ref set.
            for meal_type in ("breakfast", "lunch", "dinner"):
                has_meal = any(v.get("meal_ref") == meal_type for v in tl_values)
                if not has_meal:
                    issues.append(Issue(
                        Severity.HIGH, Category.PRESENCE, "timeline", trip, dn,
                        f"Day {dn}", "timeline",
                        f'Missing timeline entry with "meal_ref": "{meal_type}"'
                    ))

            # Accommodation: days with lodging must have one timeline entry with accommodation_ref: true.
            if dn in days_with_acc:
                has_acc_ref = any(v.get("accommodation_ref") is True for v in tl_values)
                if not has_acc_ref:
                    issues.append(Issue(
                        Severity.HIGH, Category.PRESENCE, "timeline", trip, dn,
                        f"Day {dn}", "timeline",
                        'Missing timeline entry with "accommodation_ref": true'
                    ))

    # 4e. Transportation departure < arrival
    if agent == "transportation":
        for ei in items:
            dep = ei.data.get("departure_time", "")
            arr = ei.data.get("arrival_time", "")
            if dep and arr and dep >= arr:
                issues.append(Issue(Severity.MEDIUM, Category.SEMANTIC, agent, ei.trip,
                                    ei.day_num, ei.label, "departure_time",
                                    f"Departure ({dep}) >= arrival ({arr})"))

    # 4f. Budget sum consistency - Fix 5: uses schema-driven categories
    if agent == "budget":
        cats = registry.get_budget_categories()
        for ei in items:
            # ei.data is the "budget" object from day_entry.budget (which refs budget_categories)
            stated = ei.data.get("total", 0)
            if not stated:
                continue
            # Sum only numeric values (skip any dict/breakdown fields)
            computed = 0
            for c in cats:
                val = ei.data.get(c, 0)
                if isinstance(val, (int, float)):
                    computed += val
                elif val != 0:
                    # Non-zero, non-numeric value - log warning
                    issues.append(Issue(Severity.LOW, Category.FORMAT, agent, ei.trip,
                                        ei.day_num, ei.label, f"budget.{c}",
                                        f"Expected number, got {type(val).__name__}: {val}"))
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


def check_additional_properties(items: list, agent: str, registry: SchemaRegistry) -> list:
    """Category 7: Detect fields not defined in schema (redundant/invalid structure).

    This check enforces schema completeness by detecting:
    - Extra fields not in schema (e.g., duration when time is required)
    - Redundant legacy fields (e.g., name + name_base coexisting)
    - Any field that violates additionalProperties: false

    Critical for 100% structure validation coverage.
    """
    issues = []

    if not items:
        return issues

    item_def = items[0].item_def
    required, optional, properties = registry.get_item_fields(
        "timeline" if agent in ("timeline", "timeline_segs") else agent,
        item_def)

    # All fields defined in schema (allowed fields)
    allowed_fields = set(properties.keys())

    for ei in items:
        actual_fields = set(ei.data.keys())
        extra_fields = actual_fields - allowed_fields

        if extra_fields:
            # Check if schema has additionalProperties: false
            schema_file = f"{'timeline' if agent in ('timeline', 'timeline_segs') else agent}.schema.json"
            schema = registry._schemas.get(schema_file, {})
            defs = schema.get("$defs", {})
            item_schema = defs.get(item_def, {})
            additional_allowed = item_schema.get("additionalProperties", True)

            # Severity based on additionalProperties setting
            severity = Severity.HIGH if not additional_allowed else Severity.MEDIUM

            issues.append(Issue(
                severity,
                Category.STRUCTURE,
                agent,
                ei.trip,
                ei.day_num,
                ei.label,
                "additional_properties",
                f"Unexpected fields: {', '.join(sorted(extra_fields))} "
                f"(schema {'forbids' if not additional_allowed else 'discourages'} extra fields)"
            ))

    return issues


def check_legacy_fields(items: list, agent: str) -> list:
    """Category 5: Detect legacy field names."""
    issues = []
    for ei in items:
        for legacy, schema_name in LEGACY_FIELD_MAP.items():
            if legacy in ei.data:
                has_schema = schema_name in ei.data
                if has_schema:
                    # Both present - this is HIGH severity (data redundancy)
                    old_val = ei.data[legacy]
                    new_val = ei.data[schema_name]
                    if old_val != new_val:
                        issues.append(Issue(Severity.HIGH, Category.LEGACY, agent, ei.trip,
                                            ei.day_num, ei.label, legacy,
                                            f"MISMATCH: '{legacy}'={_trunc(old_val)} vs '{schema_name}'={_trunc(new_val)}"))
                    else:
                        issues.append(Issue(Severity.HIGH, Category.LEGACY, agent, ei.trip,
                                            ei.day_num, ei.label, legacy,
                                            f"REDUNDANT: both '{legacy}' and '{schema_name}' present (must remove '{legacy}')"))
                else:
                    # Legacy only — schema field missing
                    issues.append(Issue(Severity.MEDIUM, Category.LEGACY, agent, ei.trip,
                                        ei.day_num, ei.label, legacy,
                                        f"LEGACY_ONLY: has '{legacy}' but not '{schema_name}'"))
    return issues


def _check_time_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """Check if two time ranges overlap.

    Args:
        start1, end1: First time range (HH:MM format)
        start2, end2: Second time range (HH:MM format)

    Returns:
        True if ranges overlap, False otherwise

    Examples:
        _check_time_overlap("10:00", "12:00", "11:00", "13:00") → True (overlap 11:00-12:00)
        _check_time_overlap("10:00", "11:00", "11:00", "12:00") → False (adjacent, not overlapping)
        _check_time_overlap("10:00", "12:00", "09:00", "10:00") → False (no overlap)
    """
    # Normalize times (handle both "8:00" and "08:00")
    def normalize_time(t):
        if not t or ":" not in t:
            return "00:00"
        parts = t.split(":")
        return f"{int(parts[0]):02d}:{parts[1]}"

    start1 = normalize_time(start1)
    end1 = normalize_time(end1)
    start2 = normalize_time(start2)
    end2 = normalize_time(end2)

    # Overlap condition: start1 < end2 AND start2 < end1
    # Note: Using < not <= to treat adjacent times (11:00-12:00 vs 12:00-13:00) as non-overlapping
    return start1 < end2 and start2 < end1


def _collect_all_activities_for_day(all_data: dict, day_num: int) -> list:
    """Collect ALL activities for a specific day from timeline.json only.

    timeline.json is the single source of truth for all scheduling data.
    POI agent files no longer contain time fields.

    Returns unified format: [{
        "agent": "timeline",
        "name": "Activity Name",
        "start": "18:00",
        "end": "19:30",
        "optional": false
    }, ...]
    """
    activities = []

    # Timeline is the single source of truth for all scheduling
    timeline_data = all_data.get("timeline", {})
    if timeline_data:
        for day in timeline_data.get("data", {}).get("days", []):
            if day.get("day") == day_num:
                timeline_dict = day.get("timeline", {})
                for activity_name, sched in timeline_dict.items():
                    if isinstance(sched, dict) and sched.get("start_time"):
                        activities.append({
                            "agent": "timeline",
                            "name": activity_name,
                            "start": sched["start_time"],
                            "end": sched["end_time"],
                            "optional": False
                        })

    return activities



def _is_same_activity(act1: dict, act2: dict) -> bool:
    """Detect if two activities from different agents refer to the same real-world event.

    The same activity often appears in both timeline.json AND the individual agent file
    (e.g., meals, attractions). This causes false positive overlap reports.

    Returns True if the pair should be skipped (same event from two sources).
    """
    poi_agents = {"meals", "attractions", "entertainment", "shopping"}

    # Case 1: Exact same start AND end time → same scheduled event from two sources
    if act1["start"] == act2["start"] and act1["end"] == act2["end"]:
        # Only skip if one is timeline and the other is a POI agent, or both are
        # from different sources for the same slot
        agents = {act1["agent"], act2["agent"]}
        if "timeline" in agents and agents & poi_agents:
            return True

    # Case 2: One is timeline, the other is a POI agent, and names share a substring
    if not ({act1["agent"], act2["agent"]} >= {"timeline"} and
            {act1["agent"], act2["agent"]} & poi_agents):
        return False

    # Check if activity names share a meaningful common substring (>= 2 chars)
    name1 = act1["name"]
    name2 = act2["name"]
    # Direct containment check (one name contains the other or vice versa)
    if name1 in name2 or name2 in name1:
        return True

    # Check for shared Chinese/meaningful substring (at least 2 characters)
    shorter, longer = (name1, name2) if len(name1) <= len(name2) else (name2, name1)
    for length in range(len(shorter), 1, -1):
        for start in range(len(shorter) - length + 1):
            substr = shorter[start:start + length]
            if substr in longer:
                return True

    return False


def check_all_activity_overlaps(all_data: dict, trip: str) -> list:
    """Detect ALL time overlaps across ALL agents including timeline.

    Unifies data from 5 agents (meals, attractions, entertainment, shopping, timeline)
    into common format, then performs comprehensive pairwise overlap detection.
    """
    issues = []

    # Collect ALL activities from ALL agents per day
    # Dynamically determine max day count from loaded data
    max_day = max(
        (d.get("day", 0) for adata in all_data.values() for d in adata.get("data", adata).get("days", [])),
        default=0
    )
    for day_num in range(1, max_day + 1):
        activities = _collect_all_activities_for_day(all_data, day_num)

        if not activities:
            continue

        # Pairwise overlap detection
        for i in range(len(activities)):
            for j in range(i + 1, len(activities)):
                act1, act2 = activities[i], activities[j]

                # Skip pairs that refer to the same real-world event from two sources
                if _is_same_activity(act1, act2):
                    continue

                overlap = _check_time_overlap(act1["start"], act1["end"],
                                               act2["start"], act2["end"])

                if overlap:
                    # At least one optional → INFO severity (alternatives don't conflict)
                    if act1["optional"] or act2["optional"]:
                        severity = Severity.INFO
                    # Both non-optional with ANY overlap → HIGH severity (blocks save)
                    else:
                        severity = Severity.HIGH

                    issues.append(Issue(
                        severity, Category.CROSS_AGENT,
                        f"{act1['agent']}+{act2['agent']}", trip, day_num,
                        f"Day {day_num}", "time",
                        f"TIME OVERLAP: '{act1['name']}' ({act1['agent']}, "
                        f"{act1['start']}-{act1['end']}) overlaps with "
                        f"'{act2['name']}' ({act2['agent']}, {act2['start']}-{act2['end']})"
                    ))

    return issues


def check_travel_segment_continuity(all_data: dict, trip: str) -> list:
    """Check that travel_segment end_time connects to the next activity start_time.

    For each day, merges timeline activities and travel_segments chronologically,
    then checks consecutive (travel_segment -> activity) pairs for gaps or overlaps.
    Gaps >5 minutes: MEDIUM severity. Overlaps (segment ends after activity starts): HIGH.
    """
    issues = []
    hhmm_re = re.compile(r"^[0-2]?[0-9]:[0-5][0-9]$")

    def to_minutes(t: str) -> int:
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    timeline_data = all_data.get("timeline", {})
    if not timeline_data:
        return issues

    for day in timeline_data.get("data", {}).get("days", []):
        dn = day.get("day", 0)

        # Collect all events with start/end times into a unified list
        events = []  # [(start_min, end_min, type, name)]

        # Timeline activities
        for act_name, act_data in day.get("timeline", {}).items():
            if not isinstance(act_data, dict):
                continue
            st = act_data.get("start_time", "")
            et = act_data.get("end_time", "")
            if st and et and hhmm_re.match(st) and hhmm_re.match(et):
                events.append((to_minutes(st), to_minutes(et), "activity", act_name))

        # Travel segments
        for idx, seg in enumerate(day.get("travel_segments", [])):
            if not isinstance(seg, dict):
                continue
            st = seg.get("start_time", "")
            et = seg.get("end_time", "")
            name = seg.get("name_base", f"segment-{idx}")
            if st and et and hhmm_re.match(st) and hhmm_re.match(et):
                events.append((to_minutes(st), to_minutes(et), "travel_segment", name))

        if len(events) < 2:
            continue

        # Sort chronologically by start time, then by end time
        events.sort(key=lambda e: (e[0], e[1]))

        # Check consecutive pairs where a travel_segment precedes an activity
        for k in range(len(events) - 1):
            curr_start, curr_end, curr_type, curr_name = events[k]
            next_start, next_end, next_type, next_name = events[k + 1]

            # Only check travel_segment -> activity transitions
            if curr_type != "travel_segment" or next_type != "activity":
                continue

            gap_minutes = next_start - curr_end

            if gap_minutes < 0:
                # Overlap: segment ends AFTER activity starts
                issues.append(Issue(
                    Severity.HIGH, Category.SEMANTIC, "timeline", trip, dn,
                    f"Day {dn}", "travel_segment",
                    f"TRAVEL OVERLAP: segment '{curr_name}' ends at "
                    f"{curr_end // 60:02d}:{curr_end % 60:02d} but next activity "
                    f"'{next_name}' starts at {next_start // 60:02d}:{next_start % 60:02d} "
                    f"(overlap of {-gap_minutes} min)"
                ))
            elif gap_minutes > 5:
                # Gap > 5 minutes tolerance
                issues.append(Issue(
                    Severity.MEDIUM, Category.SEMANTIC, "timeline", trip, dn,
                    f"Day {dn}", "travel_segment",
                    f"TRAVEL GAP: segment '{curr_name}' ends at "
                    f"{curr_end // 60:02d}:{curr_end % 60:02d} but next activity "
                    f"'{next_name}' starts at {next_start // 60:02d}:{next_start % 60:02d} "
                    f"(gap of {gap_minutes} min)"
                ))

    return issues



def _get_day_end_location(day_info: dict, transport_day: dict) -> str:
    """Determine a day's END location considering location_change."""
    end = day_info["location"]
    # Transportation.json uses from_base/to_base
    t_lc = transport_day.get("location_change") if transport_day else None
    if isinstance(t_lc, dict) and t_lc.get("to_base"):
        end = t_lc["to_base"]
    # Plan-skeleton uses from/to
    ps_lc = day_info.get("location_change")
    if isinstance(ps_lc, dict) and (ps_lc.get("to") or ps_lc.get("to_base")):
        end = ps_lc.get("to") or ps_lc.get("to_base")
    return end


def _day_has_incoming_location_change(day_info: dict, transport_day: dict) -> bool:
    """Check if a day has a location_change that accounts for incoming travel."""
    t_lc = transport_day.get("location_change") if transport_day else None
    if isinstance(t_lc, dict) and t_lc.get("from_base"):
        return True
    ps_lc = day_info.get("location_change")
    if isinstance(ps_lc, dict) and (ps_lc.get("from") or ps_lc.get("from_base")):
        return True
    return False


def _build_day_info_map(all_data: dict) -> dict:
    """Build unified day info map from all agents' day data."""
    day_info = {}
    for adata in all_data.values():
        for d in adata.get("data", {}).get("days", []):
            dn = d.get("day", 0)
            if dn not in day_info:
                day_info[dn] = {
                    "location": d.get("location", ""),
                    "location_change": d.get("location_change"),
                }
    return day_info


def _norm_city(name: str) -> str:
    """Normalize city name for comparison (handles apostrophe variants, spaces)."""
    s = name.strip().lower()
    # Remove all apostrophe variants and spaces for fuzzy match
    for ch in ("'", "\u2019", "\u2018", "`", " "):
        s = s.replace(ch, "")
    return s


def check_location_continuity(all_data: dict, trip: str) -> list:
    """Adjacent day location continuity: Day N end must match Day N+1 start."""
    issues = []
    transport_data = all_data.get("transportation", {})
    transport_days = {
        d.get("day", 0): d
        for d in transport_data.get("data", {}).get("days", [])
    }
    day_info = _build_day_info_map(all_data)
    sorted_days = sorted(day_info.keys())

    for i in range(len(sorted_days) - 1):
        dn, dn1 = sorted_days[i], sorted_days[i + 1]
        if dn1 != dn + 1:
            continue
        end_loc = _get_day_end_location(day_info[dn], transport_days.get(dn, {}))
        start_loc = day_info[dn1]["location"]
        if not end_loc or not start_loc or _norm_city(end_loc) == _norm_city(start_loc):
            continue
        if _day_has_incoming_location_change(day_info[dn1], transport_days.get(dn1, {})):
            continue
        issues.append(Issue(
            Severity.HIGH, Category.CROSS_AGENT, "transportation", trip, dn,
            f"Day {dn}-{dn1}", "location_change",
            f"Day {dn} ends in {end_loc} but Day {dn1} starts in "
            f"{start_loc}, missing intercity transport"
        ))
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
            # Skip if budget_meals is not a number
            if not isinstance(budget_meals, (int, float)):
                continue
            actual = 0
            for mt in ("breakfast", "lunch", "dinner"):
                meal = mdays[dn].get(mt, {})
                if isinstance(meal, dict):
                    actual += meal.get("cost", 0)
            if budget_meals and actual and abs(budget_meals - actual) / max(budget_meals, 1) > 0.25:
                issues.append(Issue(Severity.LOW, Category.CROSS_AGENT, "budget", trip, dn,
                                    f"Day {dn}", "budget.meals",
                                    f"Budget meals={budget_meals:.0f} vs actual={actual:.0f} (>25% diff)"))

    # Cross-category duplicate POI detection
    for dn in ref_days:
        name_to_agents = defaultdict(list)
        for agent_name in ['attractions', 'entertainment', 'shopping']:
            agent_data = all_data.get(agent_name, {})
            if not agent_data:
                continue
            for day in agent_data.get('data', {}).get('days', []):
                if day.get('day') != dn:
                    continue
                for poi in day.get(agent_name, []):
                    if not isinstance(poi, dict):
                        continue
                    name = poi.get('name_local') or poi.get('name_base', '')
                    if name:
                        name_to_agents[name].append(agent_name)
        for name, agents in name_to_agents.items():
            if len(agents) > 1:
                issues.append(Issue(
                    Severity.HIGH, Category.CROSS_AGENT,
                    '+'.join(agents), trip, dn,
                    f'Day {dn}', 'name_local',
                    f"DUPLICATE POI: '{name}' appears in {', '.join(agents)} "
                    f'(each POI must belong to exactly one category)'
                ))

    # POI time conflict detection — removed.
    # Time fields no longer exist in POI agent files.
    # All time conflict detection is now handled by check_all_activity_overlaps()
    # which sources times exclusively from timeline.json.

    return issues



# Location -> expected currency mapping (keys normalized via _norm_city: no spaces/apostrophes)
LOCATION_CURRENCY_MAP = {
    'china': 'CNY', 'beijing': 'CNY', 'shanghai': 'CNY', 'chengdu': 'CNY',
    'xian': 'CNY', 'datong': 'CNY', 'chongqing': 'CNY', 'lijiang': 'CNY',
    'guangzhou': 'CNY', 'shenzhen': 'CNY', 'hangzhou': 'CNY', 'nanjing': 'CNY',
    'japan': 'JPY', 'tokyo': 'JPY', 'osaka': 'JPY', 'kyoto': 'JPY',
    'korea': 'KRW', 'seoul': 'KRW', 'busan': 'KRW',
    'uk': 'GBP', 'london': 'GBP', 'edinburgh': 'GBP',
    'usa': 'USD', 'newyork': 'USD', 'losangeles': 'USD',
}

LEGACY_COST_FIELDS = {'cost_cny', 'cost_usd', 'cost_eur'}


def _load_plan_currency(trip_dir: Path) -> str:
    """Load plan-level currency_local from requirements-skeleton.json."""
    req_path = trip_dir / 'requirements-skeleton.json'
    if req_path.exists():
        try:
            req = json.loads(req_path.read_text(encoding='utf-8'))
            return req.get('trip_summary', {}).get('currency_local', '')
        except (json.JSONDecodeError, OSError):
            pass
    return ''


def _load_skeleton_day_currencies(trip_dir: Path) -> dict:
    """Load day-level currency_local overrides from plan-skeleton.json."""
    skel_path = trip_dir / 'plan-skeleton.json'
    if not skel_path.exists():
        return {}
    try:
        skel = json.loads(skel_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {}
    return {d.get('day', 0): d['currency_local'] for d in skel.get('days', []) if d.get('currency_local')}


def _collect_validate_meal_pois(day: dict) -> list:
    """Collect POIs from meal slots including alternatives for currency check."""
    pois = []
    for mt in ('breakfast', 'lunch', 'dinner'):
        m = day.get(mt)
        if not isinstance(m, dict):
            continue
        pois.append((mt, m.get('primary', m)))
        for i, a in enumerate(m.get('alternatives', [])):
            if isinstance(a, dict):
                pois.append((f'{mt}.alt[{i}]', a))
    return pois


def _collect_validate_pois(agent_name: str, day: dict) -> list:
    """Collect all POIs needing currency validation from a day."""
    if agent_name == 'meals':
        return _collect_validate_meal_pois(day)
    if agent_name == 'accommodation':
        acc = day.get('accommodation')
        return [('accommodation', acc)] if isinstance(acc, dict) else []
    if agent_name == 'transportation':
        pois = []
        lc = day.get('location_change')
        if isinstance(lc, dict):
            pois.append(('location_change', lc))
        for rk, rv in (day.get('intra_city_routes') or {}).items():
            if isinstance(rv, dict):
                pois.append((rk, rv))
        return pois
    return [(p.get('name_base', '?'), p) for p in day.get(agent_name, []) if isinstance(p, dict)]


def _check_poi_currency(poi, label, expected, agent_name, trip, dn, issues):
    """Check a single POI's currency_local and legacy cost fields."""
    poi_currency = poi.get('currency_local', '')
    if poi_currency and poi_currency != expected:
        issues.append(Issue(
            Severity.HIGH, Category.SEMANTIC, agent_name, trip, dn,
            label, 'currency_local',
            f'POI currency_local={poi_currency} does not match expected currency_local={expected}'
        ))
    legacy_fields_present = LEGACY_COST_FIELDS & set(poi.keys())
    if legacy_fields_present:
        issues.append(Issue(
            Severity.LOW, Category.LEGACY, agent_name, trip, dn,
            label, ','.join(sorted(legacy_fields_present)),
            f'Legacy cost fields {sorted(legacy_fields_present)} found. '
            f'Migrate to single cost + currency_local model.'
        ))


def check_currency_consistency(all_data: dict, trip: str, trip_dir: Path) -> list:
    """Check currency_local consistency across all POI agents.

    Resolution order: day.currency_local (plan-skeleton) -> plan.trip_summary.currency_local
    """
    issues = []
    plan_currency = _load_plan_currency(trip_dir)
    day_currencies = _load_skeleton_day_currencies(trip_dir)
    if not plan_currency and not day_currencies:
        return issues
    poi_agents = ['meals', 'attractions', 'entertainment', 'accommodation', 'shopping', 'cafe', 'transportation']

    for agent_name in poi_agents:
        adata = all_data.get(agent_name, {})
        for day in adata.get('data', {}).get('days', []):
            dn = day.get('day', 0)
            effective_currency = day_currencies.get(dn, plan_currency)

            # Location-currency validation
            loc_key = _norm_city(day.get('location', ''))
            expected_for_loc = LOCATION_CURRENCY_MAP.get(loc_key)
            if expected_for_loc and expected_for_loc != effective_currency:
                issues.append(Issue(
                    Severity.HIGH, Category.SEMANTIC, agent_name, trip, dn,
                    f'Day {dn}', 'currency_local',
                    f'Location {day.get("location", "")} expects {expected_for_loc} '
                    f'but effective currency_local is {effective_currency}. '
                    f'Add day-level currency_local override.'
                ))

            for label, poi in _collect_validate_pois(agent_name, day):
                _check_poi_currency(poi, label, effective_currency, agent_name, trip, dn, issues)

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

                    # Additional properties (redundant fields)
                    all_issues.extend(check_additional_properties(items, display_agent, registry))

                    # Legacy
                    all_issues.extend(check_legacy_fields(items, display_agent))

                # Semantics (timeline overlaps) — once for whole timeline
                all_issues.extend(check_semantics([], "timeline", all_data, trip, trip_dir, registry))

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
                all_issues.extend(check_semantics(items, agent, all_data, trip, trip_dir, registry))

                # Additional properties (redundant fields)
                all_issues.extend(check_additional_properties(items, agent, registry))

                # Legacy
                all_issues.extend(check_legacy_fields(items, agent))

        # Cross-agent (once per trip)
        if not agent_filter:
            # Travel segment continuity (gap/overlap between segments and activities)
            all_issues.extend(check_travel_segment_continuity(all_data, trip))
            # Adjacent day location continuity (missing return trips)
            all_issues.extend(check_location_continuity(all_data, trip))
            # Comprehensive overlap detection across ALL agents (including timeline)
            all_issues.extend(check_all_activity_overlaps(all_data, trip))
            # Legacy cross-agent checks (day count, date, location, budget consistency)
            all_issues.extend(check_cross_agent(all_data, trip))
            # Currency consistency (POI currency_local must match plan/day level)
            all_issues.extend(check_currency_consistency(all_data, trip, trip_dir))

    return all_issues, metrics


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def format_table(issues: list, metrics: dict, min_severity: Severity, trips: list):
    """Print human-readable report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    import shutil
    w = min(shutil.get_terminal_size().columns, 160)
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
    """Fix 9: Remove hardcoded trip-specific labels.

    Previously hardcoded patterns like 'china-feb' -> 'itinerary'.
    Now uses simple heuristic: 'bucket' -> 'bucket-list', else truncate.
    Trip-specific labels should come from trip metadata, not code patterns.
    """
    # Simple heuristic: only check for 'bucket' pattern
    if "bucket" in trip.lower():
        return "bucket-list"
    # Default: truncate long trip names for display
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
    # M2 (spec-20260508-221237): forward --v2 invocations to the v2 validator,
    # which lives in a separate file (scripts/validate-trip-contract.py) to keep the
    # legacy v1 validator's quality-gate baseline unchanged.
    if "--v2" in sys.argv:
        import os
        v2_args = [a for a in sys.argv[1:] if a != "--v2"]
        os.execvp(sys.executable, [sys.executable, str(Path(__file__).parent / "validate-trip-contract.py"), *v2_args])
    main()
