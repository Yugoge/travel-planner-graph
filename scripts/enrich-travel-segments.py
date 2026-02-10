#!/usr/bin/env python3
"""Enrich timeline.json with structured travel_segments data for each day.

Reads the timeline, transportation, and POI data files from a trip data directory,
identifies travel/transit activities from the timeline, and adds a travel_segments
array to each day with structured mode, name_base, name_local fields.

Usage: python3 scripts/enrich-travel-segments.py <data-dir>
Exit codes: 0=success, 1=failure
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional


# --- Travel activity detection patterns ---

TRAVEL_PREFIXES = [
    "Travel to ",
    "Travel from ",
    "Walk to ",
    "Drive to ",
    "Taxi to ",
    "Bus to ",
    "Metro to ",
    "Transfer to ",
    "Return to ",
    "Travel back",
    "Taxi back",
]

# Activity names that look like travel but are NOT travel segments
NOT_TRAVEL_PATTERNS = [
    r"^Return home and pack",
    r"^Return to Beijing -",  # This is a meal/activity label, not travel
    r"^Move to rental apartment",  # Moving/settling in, not transit display
]

# Patterns that indicate main inter-city transport (to be excluded)
MAIN_TRANSPORT_PATTERNS = [
    r"^High-speed train",
    r"^Board train",
    r"^Flight\b",
    r"^Train to\b",
    r"^Li River Cruise",
    r"Travel .+\(High-speed train",
]

# Activities with "Travel" in name that are actually inter-city main transport
MAIN_TRANSPORT_ACTIVITY_PATTERNS = [
    r"^Travel from Beijing to Harbin",
    r"^Travel from Harbin to Tianjin",
    r"^Travel from Tianjin to Xi'an",
    r"^Travel from Xi'an to Suzhou",
    r"^Travel from Suzhou to Hangzhou",
    r"^Travel from Hangzhou to Guilin",
    r"^Travel from Yangshuo to Zhangjiajie",
    r"^Travel from Zhangjiajie to Guangzhou",
    r"^Travel from Guangzhou to Shenzhen",
    r"^Travel from Shenzhen to Hong Kong",
]

# Mode keywords found in activity name
MODE_KEYWORDS = {
    "Walk to ": "walk",
    "Walk ": "walk",
    "Taxi to ": "taxi",
    "Taxi back": "taxi",
    "Bus to ": "bus",
    "Metro to ": "metro",
    "Drive to ": "car",
}

# Mode verb prefixes for name_local
MODE_VERB_PREFIX = {
    "walk": "步行前往",
    "taxi": "打车前往",
    "bus": "乘公交前往",
    "metro": "乘地铁前往",
    "train": "乘火车前往",
    "flight": "乘飞机前往",
    "car": "开车前往",
    "bike": "骑行前往",
    "transit": "前往",
}

# Known station name mappings
STATION_MAPPINGS = {
    "Chongqing North Station": "重庆北站",
    "Bazhong East Station": "巴中东站",
    "Bazhong West Station": "巴中西站",
    "Chengdu East Station": "成都东站",
    "Shuangliu Airport": "双流机场",
    "Pudong Airport": "浦东机场",
    "Daxing Airport": "大兴机场",
    "Beijing Daxing Airport": "北京大兴机场",
    "Shanghai Disneyland": "上海迪士尼乐园",
    "Chongqing Jiangbei Airport": "重庆江北机场",
    "Harbin West Station": "哈尔滨西站",
    "Tianjin West Station": "天津西站",
    "Xi'an North Station": "西安北站",
    "Suzhou North Station": "苏州北站",
    "Suzhou Station": "苏州站",
    "Hangzhou East Station": "杭州东站",
    "Guilin North Station": "桂林北站",
    "Yangshuo Station": "阳朔站",
    "Zhangjiajie West Station": "张家界西站",
    "Guangzhou Baiyun Station": "广州白云站",
    "Guangzhou South Station": "广州南站",
    "Shenzhen Futian": "深圳福田",
}

# City name mappings
CITY_MAPPINGS = {
    "Chongqing": "重庆",
    "Bazhong": "巴中",
    "Chengdu": "成都",
    "Shanghai": "上海",
    "Beijing": "北京",
    "Tianjin": "天津",
    "Harbin": "哈尔滨",
    "Xi'an": "西安",
    "Suzhou": "苏州",
    "Hangzhou": "杭州",
    "Guilin": "桂林",
    "Yangshuo": "阳朔",
    "Zhangjiajie": "张家界",
    "Guangzhou": "广州",
    "Shenzhen": "深圳",
    "Hong Kong": "香港",
    "Macau": "澳门",
    "Nanjing": "南京",
}

# Generic destination translations
GENERIC_DEST_TRANSLATIONS = {
    "hotel": "酒店",
    "restaurant": "餐厅",
    "theater": "剧场",
    "theatre": "剧场",
    "spa": "水疗中心",
    "airport": "机场",
    "station": "车站",
    "apartment": "公寓",
    "home": "家",
    "family home": "家",
    "shopping area": "购物区",
    "breakfast restaurant": "早餐餐厅",
    "lunch restaurant": "午餐餐厅",
    "dinner restaurant": "晚餐餐厅",
    "roast duck restaurant": "烤鸭店",
    "university area": "大学区域",
    "Bund": "外滩",
    "Giant Panda Base": "大熊猫繁育研究基地",
    "Forbidden City": "故宫",
    "Terracotta Warriors": "兵马俑",
    "Sun Island": "太阳岛",
    "Lantau Island": "大屿山",
}

# Additional well-known POI translations not in data files
KNOWN_POI_TRANSLATIONS = {
    "Raffles City InterContinental": "来福士洲际酒店",
    "Gregorius SHADE": "Gregorius SHADE",
    "Garden Books": "Garden Books书店",
    "Taikoo Li": "太古里",
    "TOP TOY": "TOP TOY",
    "Tianzifang": "田子坊",
    "Nanluoguxiang": "南锣鼓巷",
    "Wukang Road": "武康路",
    "Beijing Dance Academy": "北京舞蹈学院",
    "Aimuniu Restaurant": "爱牧牛餐厅",
    "Nanshan hotpot restaurant": "南山火锅餐厅",
    "roast duck restaurant": "烤鸭店",
    "theater": "剧场",
    "theatre": "剧场",
}


def load_json(filepath: str) -> Optional[dict]:
    """Load a JSON file, returning None if it doesn't exist."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_poi_lookup(data_dir: str) -> dict[str, str]:
    """Build a lookup dict mapping POI name_base -> name_local from all data files.

    Scans meals, attractions, entertainment, shopping, accommodation JSON files
    and extracts name_base/name_local pairs. Handles different field naming
    conventions across data files.
    """
    lookup = {}

    # Load all POI source files
    poi_files = [
        "meals.json",
        "attractions.json",
        "entertainment.json",
        "shopping.json",
        "accommodation.json",
    ]

    for filename in poi_files:
        filepath = os.path.join(data_dir, filename)
        data = load_json(filepath)
        if not data or "data" not in data:
            continue

        days = data["data"].get("days", [])
        for day in days:
            # Extract POIs from different structures
            pois = _extract_pois_from_day(day, filename)
            for poi in pois:
                name_base = _get_name_base(poi)
                name_local = _get_name_local(poi)
                if name_base and name_local:
                    lookup[name_base] = name_local
                    # Also store without parenthetical suffixes for fuzzy matching
                    clean_name = re.sub(r"\s*\(.*?\)\s*$", "", name_base).strip()
                    if clean_name and clean_name != name_base:
                        lookup[clean_name] = name_local

    return lookup


def _extract_pois_from_day(day: dict, filename: str) -> list[dict]:
    """Extract POI dicts from a day entry based on the file type."""
    pois = []

    if filename == "meals.json":
        for meal_type in ["breakfast", "lunch", "dinner", "snack", "late_lunch"]:
            meal = day.get(meal_type)
            if meal:
                pois.append(meal)

    elif filename == "attractions.json":
        attractions = day.get("attractions", [])
        pois.extend(attractions)

    elif filename == "entertainment.json":
        entertainment = day.get("entertainment", [])
        pois.extend(entertainment)

    elif filename == "shopping.json":
        shopping = day.get("shopping", [])
        pois.extend(shopping)

    elif filename == "accommodation.json":
        acc = day.get("accommodation")
        if acc:
            pois.append(acc)

    return pois


def _get_name_base(poi: dict) -> Optional[str]:
    """Extract the base name from a POI dict, handling different field names."""
    for key in ["name_base", "name", "name_english"]:
        val = poi.get(key)
        if val:
            return val
    return None


def _get_name_local(poi: dict) -> Optional[str]:
    """Extract the local name from a POI dict, handling different field names."""
    for key in ["name_local", "name_cn", "name_chinese"]:
        val = poi.get(key)
        if val:
            return val
    return None


def build_transport_time_ranges(transport_data: Optional[dict]) -> dict[int, list[dict]]:
    """Build a mapping of day number to main transport time ranges.

    These are the inter-city transport segments that should be EXCLUDED
    from travel_segments (they appear as the main transport card).
    """
    ranges = {}
    if not transport_data or "data" not in transport_data:
        return ranges

    days = transport_data["data"].get("days", [])
    for day_data in days:
        day_num = day_data.get("day")
        if day_num is None:
            continue

        ranges.setdefault(day_num, [])

        # Extract main transport time range from location_change
        loc_change = day_data.get("location_change", day_data)
        dep_time = loc_change.get("departure_time")
        arr_time = loc_change.get("arrival_time")

        if dep_time and arr_time:
            ranges[day_num].append({
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "transport_type": loc_change.get("transportation", ""),
            })

    return ranges


def _parse_recommended_transport(recommended: str) -> str:
    """Convert a recommended_transport string to a mode value."""
    rt = recommended.lower()
    if "metro" in rt or "mtr" in rt:
        return "metro"
    if "bus" in rt:
        return "bus"
    if "walk" in rt:
        return "walk"
    if "taxi" in rt or "didi" in rt:
        return "taxi"
    if "ferry" in rt:
        return "transit"
    if "train" in rt:
        return "train"
    return ""


def build_intra_city_routes(transport_data: Optional[dict]) -> dict[int, list[dict]]:
    """Build a mapping of day number to intra-city route details.

    Extracts routes from transportation.json fields:
    - location_change.morning_routes / evening_routes (Day 4 format)
    - intra_city_routes (Day 5 format)

    Returns: { day_num: [ { "from": ..., "to": ..., "mode": ..., "start_time": ... }, ... ] }
    """
    routes_by_day: dict[int, list[dict]] = {}
    if not transport_data:
        return routes_by_day

    raw_data = transport_data.get("data", transport_data)
    days = raw_data.get("days", [])

    for day_data in days:
        day_num = day_data.get("day")
        if day_num is None:
            continue

        day_routes: list[dict] = []

        # Format 1: morning_routes / evening_routes inside location_change
        loc_change = day_data.get("location_change", {})
        for route_group_key in ("morning_routes", "evening_routes", "local_routes"):
            route_group = loc_change.get(route_group_key, {})
            if isinstance(route_group, dict):
                for route_key, route_val in route_group.items():
                    if not isinstance(route_val, dict):
                        continue
                    rec = route_val.get("recommended_transport", "")
                    mode = _parse_recommended_transport(rec)
                    if mode:
                        day_routes.append({
                            "from": route_val.get("from", ""),
                            "to": route_val.get("to", ""),
                            "mode": mode,
                            "duration_minutes": route_val.get("duration_minutes", 0),
                        })

        # Format 2: intra_city_routes at day level (Day 5 format)
        intra_routes = day_data.get("intra_city_routes", {})
        if isinstance(intra_routes, dict):
            for route_key, route_val in intra_routes.items():
                if not isinstance(route_val, dict):
                    continue
                rec = route_val.get("recommended_transport", "")
                mode = _parse_recommended_transport(rec)
                if mode:
                    day_routes.append({
                        "from": route_val.get("from", ""),
                        "to": route_val.get("to", ""),
                        "mode": mode,
                        "duration_minutes": route_val.get("duration_minutes", 0),
                    })

        if day_routes:
            routes_by_day[day_num] = day_routes

    return routes_by_day


def match_intra_city_route(
    activity_name: str,
    destination: str,
    intra_routes: list[dict],
) -> str:
    """Try to match a travel activity to an intra-city route by destination.

    Returns mode string if matched, empty string if no match.
    """
    if not intra_routes:
        return ""

    dest_lower = destination.lower()
    act_lower = activity_name.lower()

    for route in intra_routes:
        route_to = route.get("to", "").lower()
        route_from = route.get("from", "").lower()

        # Match by destination name overlap
        if dest_lower and route_to:
            # Check if destination appears in route.to or vice versa
            if dest_lower in route_to or route_to in dest_lower:
                return route["mode"]
            # Word overlap: extract significant words (exclude generic venue types)
            generic_words = {
                "to", "the", "a", "at", "in", "and", "of", "(", ")",
                "restaurant", "hotel", "station", "airport", "road",
                "street", "area", "center", "mall", "market",
            }
            dest_words = set(dest_lower.split()) - generic_words
            route_words = set(route_to.split()) - generic_words
            shared = dest_words & route_words
            if len(shared) >= 1 and dest_words:
                return route["mode"]

        # Match by activity name containing route destination
        if route_to and route_to in act_lower:
            return route["mode"]

    return ""


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def overlaps_transport(
    start_time: str,
    end_time: str,
    transport_ranges: list[dict],
) -> bool:
    """Check if a time range overlaps with any main transport segment."""
    start_min = time_to_minutes(start_time)
    end_min = time_to_minutes(end_time)
    # Handle overnight activities
    if end_min < start_min:
        end_min += 24 * 60

    for tr in transport_ranges:
        tr_start = time_to_minutes(tr["departure_time"])
        tr_end = time_to_minutes(tr["arrival_time"])
        if tr_end < tr_start:
            tr_end += 24 * 60

        # Check overlap: segments overlap if one starts before the other ends
        if start_min < tr_end and end_min > tr_start:
            return True

    return False


def is_travel_activity(name: str) -> bool:
    """Determine if an activity name represents a travel/transit segment."""
    name_lower = name.lower()

    # Exclude activities that look like travel but are not
    for pattern in NOT_TRAVEL_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return False

    # Check main transport patterns (these are EXCLUDED later, but first
    # we need to identify them as travel-related)
    for pattern in MAIN_TRANSPORT_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return True

    # Check travel prefixes
    for prefix in TRAVEL_PREFIXES:
        if name_lower.startswith(prefix.lower()):
            return True

    # Check for " travel to " in the middle
    if " travel to " in name_lower:
        return True

    # Check for "travel from" in the middle
    if " travel from " in name_lower:
        return True

    return False


def is_main_transport(name: str) -> bool:
    """Check if activity is a main inter-city transport segment."""
    for pattern in MAIN_TRANSPORT_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return True
    for pattern in MAIN_TRANSPORT_ACTIVITY_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return True
    return False


def _clean_destination(dest: str) -> str:
    """Remove parenthetical qualifiers from destination names.

    E.g., "Tianjin (if day trip)" -> "Tianjin"
          "Terracotta Warriors (40km, 1-1.5 hours)" -> "Terracotta Warriors"
    """
    # Remove trailing parenthetical qualifiers
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", dest).strip()
    return cleaned if cleaned else dest


def extract_destination(name: str) -> str:
    """Extract the destination from a travel activity name."""
    name_stripped = name.strip()

    # "Travel from X to Y" -> Y (must come before generic "travel to" match)
    match = re.match(r"Travel\s+from\s+.+?\s+to\s+(.+)$", name_stripped, re.IGNORECASE)
    if match:
        return _clean_destination(match.group(1).strip())

    # "Hotel check-out and travel to X" -> X
    match = re.search(r"(?:and\s+)?travel\s+to\s+(.+)$", name_stripped, re.IGNORECASE)
    if match:
        return _clean_destination(match.group(1).strip())

    # "Walk to X", "Taxi to X", "Bus to X", "Metro to X", etc.
    match = re.match(
        r"(?:Walk|Taxi|Bus|Metro|Drive|Transfer)\s+to\s+(.+)$",
        name_stripped,
        re.IGNORECASE,
    )
    if match:
        return _clean_destination(match.group(1).strip())

    # "Taxi back to X"
    match = re.match(r"Taxi\s+back\s+to\s+(.+)$", name_stripped, re.IGNORECASE)
    if match:
        return _clean_destination(match.group(1).strip())

    # "Return to X"
    match = re.match(r"Return\s+to\s+(.+)$", name_stripped, re.IGNORECASE)
    if match:
        return _clean_destination(match.group(1).strip())

    # "Travel back to X"
    match = re.match(r"Travel\s+back\s+to\s+(.+)$", name_stripped, re.IGNORECASE)
    if match:
        return _clean_destination(match.group(1).strip())

    # "Travel back" without "to"
    if name_stripped.lower().startswith("travel back"):
        return "hotel"

    return _clean_destination(name_stripped)


def determine_mode(
    name: str,
    destination: str,
    duration_minutes: int,
    day_transport_ranges: list[dict],
    intra_routes: list[dict] | None = None,
) -> str:
    """Determine the transport mode for a travel segment.

    Priority:
    0. Intra-city route data from transportation.json (most authoritative)
    1. Explicit mode keywords in name
    2. Station/Airport destination -> taxi
    3. Short walking-distance segments -> walk
    4. Default for urban travel -> taxi
    """
    # Priority 0: Check intra-city route data from transportation.json
    if intra_routes:
        matched = match_intra_city_route(name, destination, intra_routes)
        if matched:
            return matched

    name_lower = name.lower()

    # Check for mode hints in parenthetical notes
    paren_match = re.search(r"\(([^)]+)\)", name)
    if paren_match:
        paren_text = paren_match.group(1).lower()
        if "mtr" in paren_text or "metro" in paren_text:
            return "metro"
        if "bus" in paren_text:
            return "bus"
        if "ferry" in paren_text:
            return "transit"
        if "taxi" in paren_text or "didi" in paren_text:
            return "taxi"
        if "walk" in paren_text:
            return "walk"

    # Check explicit mode keywords
    for keyword, mode in MODE_KEYWORDS.items():
        if name_lower.startswith(keyword.lower()):
            return mode

    # "Taxi back" anywhere in name
    if "taxi back" in name_lower:
        return "taxi"

    # "Return to hotel/apartment/home" -> taxi
    if re.match(r"return\s+to\s+(hotel|apartment|home|family)", name_lower):
        return "taxi"

    # "Return home" -> taxi
    if name_lower.startswith("return home"):
        return "taxi"

    # "Travel back to hotel" -> taxi
    if "travel back" in name_lower:
        return "taxi"

    # Destination is a station or airport -> taxi (getting to hub)
    dest_lower = destination.lower()
    if "station" in dest_lower or "airport" in dest_lower:
        return "taxi"

    # City-to-city travel -> train
    for city in CITY_MAPPINGS:
        if dest_lower == city.lower():
            return "train"

    # "Travel to X city center" -> train
    if "city center" in dest_lower:
        return "taxi"

    # Short distance (< 15 min) -> walk
    if duration_minutes <= 15:
        return "walk"

    # Default for urban travel: taxi
    return "taxi"


def resolve_destination_local(
    destination: str,
    poi_lookup: dict[str, str],
) -> Optional[str]:
    """Resolve the local name for a destination.

    Resolution order (most specific to least specific):
    1. Known POI translations (hardcoded well-known places)
    2. Exact match in POI lookup
    3. Station/airport mappings
    4. City name mappings
    5. Generic destination word translations
    6. Selective partial POI matching (only for long, specific destination names)
    7. Chinese characters already in the name
    """
    dest_lower = destination.lower()

    # Step 1: Known POI translations (hardcoded)
    for known_en, known_cn in KNOWN_POI_TRANSLATIONS.items():
        if known_en.lower() == dest_lower:
            return known_cn

    # Step 2: Exact match in POI lookup
    if destination in poi_lookup:
        return poi_lookup[destination]

    # Step 3: Station/airport mappings
    for station_en, station_cn in STATION_MAPPINGS.items():
        if station_en.lower() == dest_lower:
            return station_cn
        # Also check if station name is contained in destination
        if station_en.lower() in dest_lower:
            return station_cn

    # Step 4: City name mappings (exact match only)
    for city_en, city_cn in CITY_MAPPINGS.items():
        if dest_lower == city_en.lower():
            return city_cn

    # Step 5: Generic destination word translations
    # Check longer phrases first (more specific)
    sorted_generics = sorted(GENERIC_DEST_TRANSLATIONS.items(), key=lambda x: -len(x[0]))
    for generic_en, generic_cn in sorted_generics:
        if generic_en.lower() == dest_lower:
            return generic_cn
        # For multi-word generics, check if they appear as a complete phrase
        if " " in generic_en and generic_en.lower() in dest_lower:
            return generic_cn

    # For single-word generics, only match if the destination IS that word
    # (avoids "hotel" matching in "Hotel Breakfast")
    for generic_en, generic_cn in sorted_generics:
        if " " not in generic_en and dest_lower == generic_en.lower():
            return generic_cn

    # Step 6: Selective partial POI matching
    # Only use partial matching for specific destination names (> 8 chars)
    # to avoid false positives like "hotel" matching "Hotel Breakfast"
    if len(destination) > 8:
        # Prefer exact substring match where destination matches start of POI name
        best_match = None
        best_match_len = 0
        for poi_name, poi_local in poi_lookup.items():
            poi_lower = poi_name.lower()
            # Destination matches beginning of POI name
            if poi_lower.startswith(dest_lower):
                if len(poi_name) > best_match_len:
                    best_match = poi_local
                    best_match_len = len(poi_name)
            # POI name matches beginning of destination
            elif dest_lower.startswith(poi_lower) and len(poi_name) > 8:
                if len(poi_name) > best_match_len:
                    best_match = poi_local
                    best_match_len = len(poi_name)

        if best_match:
            return best_match

    # Step 7: Try to extract Chinese characters already in the name
    chinese_match = re.search(r"[\u4e00-\u9fff]+(?:[·\s·]?[\u4e00-\u9fff]+)*", destination)
    if chinese_match:
        return chinese_match.group(0)

    # Step 8: Check if destination contains a city name (e.g., "Xi'an city center")
    for city_en, city_cn in CITY_MAPPINGS.items():
        if city_en.lower() in dest_lower:
            # Replace city name with Chinese and keep the rest
            rest = dest_lower.replace(city_en.lower(), "").strip()
            if rest == "city center":
                return f"{city_cn}市中心"
            return city_cn

    # Step 9: Last resort - check if any generic keyword appears in destination
    for generic_en, generic_cn in sorted_generics:
        if generic_en.lower() in dest_lower:
            return generic_cn

    return None


def build_name_local(
    mode: str,
    destination: str,
    destination_local: Optional[str],
) -> str:
    """Build the full name_local string with mode verb prefix.

    Format: {verb_prefix}{destination_local}
    """
    verb = MODE_VERB_PREFIX.get(mode, "前往")

    if destination_local:
        return f"{verb}{destination_local}"

    # Fallback: use the English destination name
    return f"{verb}{destination}"


def process_day(
    day: dict,
    transport_ranges: dict[int, list[dict]],
    poi_lookup: dict[str, str],
    intra_city_routes: dict[int, list[dict]] | None = None,
) -> list[dict]:
    """Process a single day's timeline and extract travel segments."""
    day_num = day.get("day")
    timeline = day.get("timeline", {})
    day_transport = transport_ranges.get(day_num, [])
    day_intra = (intra_city_routes or {}).get(day_num, [])
    segments = []

    for activity_name, activity_data in timeline.items():
        # Skip non-travel activities
        if not is_travel_activity(activity_name):
            continue

        # Skip main transport (inter-city trains, flights)
        if is_main_transport(activity_name):
            continue

        start_time = activity_data.get("start_time", "")
        end_time = activity_data.get("end_time", "")
        duration = activity_data.get("duration_minutes", 0)

        # Skip "Board train" activities
        if activity_name.lower().startswith("board train"):
            continue

        # Skip activities that overlap with main transport time ranges
        if start_time and end_time and day_transport:
            if overlaps_transport(start_time, end_time, day_transport):
                # Only skip if the activity name also suggests main transport
                if any(
                    kw in activity_name.lower()
                    for kw in ["high-speed", "flight", "board train", "li river cruise"]
                ):
                    continue

        # Extract destination
        destination = extract_destination(activity_name)

        # Determine mode
        mode = determine_mode(activity_name, destination, duration, day_transport, day_intra)

        # Resolve local destination name
        dest_local = resolve_destination_local(destination, poi_lookup)

        # Build name_base (use original activity name)
        name_base = activity_name

        # Build name_local
        name_local = build_name_local(mode, destination, dest_local)

        segment = {
            "name_base": name_base,
            "name_local": name_local,
            "mode": mode,
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration,
        }
        segments.append(segment)

    return segments


def enrich_timeline(data_dir: str) -> None:
    """Main function: enrich timeline.json with travel_segments."""
    data_dir = os.path.abspath(data_dir)

    if not os.path.isdir(data_dir):
        print(f"Error: Directory not found: {data_dir}", file=sys.stderr)
        sys.exit(1)

    timeline_path = os.path.join(data_dir, "timeline.json")
    if not os.path.exists(timeline_path):
        print(f"Error: timeline.json not found in {data_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing: {data_dir}")
    print(f"  Loading timeline.json...")

    # Load timeline
    with open(timeline_path, "r", encoding="utf-8") as f:
        timeline_data = json.load(f)

    # Load transportation data
    transport_path = os.path.join(data_dir, "transportation.json")
    transport_data = load_json(transport_path)
    transport_ranges = build_transport_time_ranges(transport_data)
    print(f"  Loaded transport ranges for {len(transport_ranges)} days")

    # Build intra-city route lookup from transportation.json
    intra_city_routes = build_intra_city_routes(transport_data)
    print(f"  Loaded intra-city routes for {len(intra_city_routes)} days")

    # Build POI lookup
    poi_lookup = build_poi_lookup(data_dir)
    print(f"  Built POI lookup with {len(poi_lookup)} entries")

    # Process each day
    days = timeline_data.get("data", {}).get("days", [])
    total_segments = 0

    for day in days:
        day_num = day.get("day", "?")
        segments = process_day(day, transport_ranges, poi_lookup, intra_city_routes)
        day["travel_segments"] = segments
        total_segments += len(segments)
        if segments:
            print(f"  Day {day_num}: {len(segments)} travel segment(s)")

    # Write back to timeline.json
    with open(timeline_path, "w", encoding="utf-8") as f:
        json.dump(timeline_data, f, ensure_ascii=False, indent=2)

    print(f"  Total: {total_segments} travel segments across {len(days)} days")
    print(f"  Written to: {timeline_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/enrich-travel-segments.py <data-dir>", file=sys.stderr)
        sys.exit(1)

    data_dir = sys.argv[1]
    enrich_timeline(data_dir)
    print("Done.")


if __name__ == "__main__":
    main()
