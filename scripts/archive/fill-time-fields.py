#!/usr/bin/env python3
"""
Fill missing time fields in attractions.json and entertainment.json.

Matches items against timeline.json using fuzzy name matching, then assigns
start/end times. Items without timeline matches get reasonable defaults
based on their position in the day's schedule.

Usage: python fill-time-fields.py <trip_directory>
"""

import json
import re
import sys
import os


def load_json(filepath: str) -> dict:
    """Load and return parsed JSON from filepath."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: dict) -> None:
    """Save data as formatted JSON to filepath."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {filepath}")


def is_logistics_entry(timeline_key: str) -> bool:
    """Check if a timeline key is a logistics/meal entry (not a sightseeing activity)."""
    key_lower = timeline_key.lower()

    # Travel/hotel patterns
    if re.match(r'^(travel |hotel check|return to )', key_lower):
        return True

    # Meal suffixes: "- Breakfast", "- Lunch", "- Dinner", "- Late Lunch"
    if re.search(r'\s*-\s*(breakfast|lunch|dinner|brunch|late lunch|late dinner)\s*$',
                 key_lower, re.IGNORECASE):
        return True

    # Restaurant/food patterns with Chinese names followed by meal indicator
    meal_suffixes = [
        "breakfast", "lunch", "dinner", "brunch",
        "late lunch", "late dinner",
    ]
    for suffix in meal_suffixes:
        if key_lower.endswith(suffix):
            return True

    # Food-specific keywords that indicate restaurant entries
    food_keywords = [
        "noodles", "dumplings", "bakery", "nata", "dim sum",
        "paomo", "roast goose", "beer fish", "rice noodles",
        "egg tarts", "cuisine", "restaurant",
    ]
    for kw in food_keywords:
        if kw in key_lower:
            return True

    # Deep-check: pattern "Chinese / English - Meal"
    if re.search(r'/.+\s*-\s*(breakfast|lunch|dinner|brunch)', key_lower, re.IGNORECASE):
        return True

    # Breakfast in scenic area
    if "breakfast" in key_lower:
        return True

    return False


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip punctuation."""
    text = text.lower().strip()
    text = re.sub(r'[·/\-–—()（）\[\]【】"\'·,，。!！?？:：;；]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_chinese_chars(text: str) -> str:
    """Extract only Chinese characters from text."""
    return re.sub(r'[^\u4e00-\u9fff]', '', text)


def strip_modifiers(name: str) -> str:
    """
    Strip trailing modifiers like 'Night Walk', 'Night Ride',
    'Night View', 'Night Viewing', etc. from the name for core matching.
    """
    # Remove common suffixes that distinguish entertainment variants
    patterns = [
        r'\s*-?\s*night\s*(walk|ride|view|viewing|illumination|cruise|market).*$',
        r'\s*-?\s*(optional|alternative).*$',
        r'\s*\(optional\).*$',
        r'\s*\(alternative\).*$',
    ]
    result = name
    for pat in patterns:
        result = re.sub(pat, '', result, flags=re.IGNORECASE)
    return result.strip()


def compute_chinese_similarity(item_chinese: str, key_chinese: str) -> float:
    """
    Compute similarity between two Chinese strings.
    Requires the shorter to be substantially contained in the longer.
    """
    if not item_chinese or not key_chinese:
        return 0.0

    if len(item_chinese) < 2 or len(key_chinese) < 2:
        return 0.0

    # Exact match
    if item_chinese == key_chinese:
        return 1.0

    # Find longest common substring
    shorter = item_chinese if len(item_chinese) <= len(key_chinese) else key_chinese
    longer = item_chinese if len(item_chinese) > len(key_chinese) else key_chinese

    best_len = 0
    for i in range(len(shorter)):
        for j in range(i + 2, len(shorter) + 1):
            if shorter[i:j] in longer:
                best_len = max(best_len, j - i)

    # The overlap must cover most of the shorter string
    # Also consider how much of the LONGER string is covered to avoid
    # matching short names against long unrelated strings
    if len(shorter) > 0 and len(longer) > 0:
        coverage_short = best_len / len(shorter)
        coverage_long = best_len / len(longer)

        # Both strings must be substantially represented
        # Require best_len >= 3 to avoid 2-char Chinese matches creating false positives
        if coverage_short >= 0.8 and coverage_long >= 0.5 and best_len >= 3:
            return 0.95
        if coverage_short >= 0.8 and coverage_long >= 0.4 and best_len >= 3:
            return 0.85
        if coverage_short >= 0.6 and coverage_long >= 0.3 and best_len >= 3:
            return 0.7
        # For 2-char matches, only accept if both strings are very short (2-3 chars)
        if best_len == 2 and len(shorter) == 2 and len(longer) <= 3:
            return 0.85

    return 0.0


def compute_english_similarity(item_name: str, key_name: str) -> float:
    """
    Compute similarity between two English names.
    Uses word overlap with filtering.
    """
    stopwords = {
        "the", "a", "an", "of", "in", "at", "to", "for", "and", "or",
        "is", "on", "by", "with", "from", "as", "its", "it",
    }
    # Also exclude modifiers and location names that cause false matches
    generic_words = {
        "night", "view", "walk", "ride", "show", "optional", "alternative",
        "quick", "visit", "experience", "area", "district", "city",
        "street", "tower", "bar", "cruise", "lake", "river", "mountain",
        "dynasty", "tang", "impression", "west", "south", "north", "east",
        # Location names that appear in many timeline keys
        "yangshuo", "guilin", "hangzhou", "suzhou", "guangzhou",
        "shenzhen", "tianjin", "harbin", "macau", "hong", "kong",
    }

    def get_words(text):
        normalized = normalize_text(text)
        words = set(normalized.split())
        return {w for w in words if len(w) > 1 and w not in stopwords and w not in generic_words}

    item_words = get_words(item_name)
    key_words = get_words(key_name)

    if not item_words or not key_words:
        return 0.0

    overlap = item_words & key_words
    if not overlap:
        return 0.0

    # Require substantial meaningful overlap
    smaller_set_size = min(len(item_words), len(key_words))
    overlap_ratio = len(overlap) / smaller_set_size

    if overlap_ratio >= 0.8 and len(overlap) >= 2:
        return 0.85
    if overlap_ratio >= 0.6 and len(overlap) >= 2:
        return 0.7
    if len(overlap) >= 2:
        return 0.6

    # Single word overlap: only if it's very distinctive (8+ chars)
    if len(overlap) == 1:
        word = list(overlap)[0]
        if len(word) >= 8:
            return 0.55
        if len(word) >= 6:
            return 0.4  # Below threshold, won't match

    return 0.0


def fuzzy_match_score(item_name: str, timeline_key: str) -> float:
    """
    Compute a match score between item name and timeline key.
    Returns 0.0 (no match) to 1.0 (perfect match).

    Priority: Chinese chars > full name substring > word overlap
    """
    # Strategy 1: Chinese character matching (most reliable)
    item_chinese = extract_chinese_chars(item_name)
    key_chinese = extract_chinese_chars(timeline_key)
    chinese_score = compute_chinese_similarity(item_chinese, key_chinese)

    if chinese_score >= 0.7:
        return chinese_score

    # Strategy 2: Full normalized name matching
    norm_item = normalize_text(strip_modifiers(item_name))
    norm_key = normalize_text(timeline_key)

    # Substring match -- but verify the name has meaningful non-generic words
    generic_set = {
        "west", "east", "north", "south", "lake", "river", "mountain",
        "street", "road", "tower", "city", "night", "view", "walk",
        "tang", "dynasty", "impression", "bar", "cruise", "show",
    }

    def has_meaningful_content(normalized_name: str) -> bool:
        words = set(normalized_name.split())
        non_generic = {w for w in words if len(w) > 1 and w not in generic_set}
        return len(non_generic) >= 1

    if len(norm_item) >= 8 and norm_item in norm_key and has_meaningful_content(norm_item):
        return 0.85
    if len(norm_key) >= 8 and norm_key in norm_item and has_meaningful_content(norm_key):
        return 0.85

    # Strategy 3: English word overlap
    english_score = compute_english_similarity(
        strip_modifiers(item_name), timeline_key
    )

    # Return the best score across all strategies
    return max(chinese_score, english_score)


def find_timeline_match(item: dict, timeline: dict) -> tuple:
    """
    Find the best matching timeline entry for an item.

    Filters out logistics entries (travel, hotels, meals) and returns
    the highest-scoring match above threshold.

    Returns (start_time, end_time, matched_key) or (None, None, None).
    """
    # Collect name variants from the item
    name_variants = []
    for field in ["name_base", "name_local", "name", "name_chinese", "name_english"]:
        val = item.get(field)
        if val and val not in name_variants:
            name_variants.append(val)

    best_score = 0.0
    best_match = None

    for timeline_key, times in timeline.items():
        # Skip logistics/meal entries
        if is_logistics_entry(timeline_key):
            continue

        for name in name_variants:
            score = fuzzy_match_score(name, timeline_key)
            if score > best_score:
                best_score = score
                best_match = (times["start_time"], times["end_time"], timeline_key)

    # Threshold: only accept matches with score >= 0.55
    if best_score >= 0.55 and best_match:
        return best_match

    return None, None, None


def determine_time_block(item: dict) -> str:
    """
    Determine whether an item is morning, afternoon, or evening based on
    its name, type, and notes.

    Returns "morning", "afternoon", or "evening".
    """
    name = (item.get("name_base", "") + " " + item.get("name", "")).lower()
    item_type = (item.get("type_base", "") + " " + item.get("type", "")).lower()
    notes = (item.get("notes_base", "") + " " + item.get("notes", "")).lower()
    best_time = item.get("best_time_to_visit", "").lower()

    # Night/evening indicators
    evening_words = ["night", "evening", "sunset", "illuminat", "lit at night",
                     "after dark", "bar", "nightlife", "light show", "cruise"]
    for w in evening_words:
        if w in name or w in item_type or w in best_time:
            return "evening"

    # Morning indicators
    morning_words = ["morning", "sunrise", "early"]
    for w in morning_words:
        if w in best_time:
            return "morning"

    # Afternoon indicators
    afternoon_words = ["afternoon", "midday"]
    for w in afternoon_words:
        if w in best_time:
            return "afternoon"

    return "afternoon"  # Default to afternoon


def assign_default_times(items: list, day_timeline: dict) -> list:
    """
    Assign default times to unmatched items based on type and position.

    Uses item metadata (name, type, best_time_to_visit) to determine
    morning/afternoon/evening placement, then staggers within blocks.
    """
    # Find unmatched items
    unmatched = []
    for i, item in enumerate(items):
        t = item.get("time")
        if not isinstance(t, dict) or not t.get("start"):
            unmatched.append((i, item))

    if not unmatched:
        return items

    # Define time blocks
    blocks = {
        "morning": ("09:00", "11:00"),
        "afternoon": ("14:00", "16:00"),
        "evening": ("18:00", "20:00"),
    }

    # Categorize unmatched items into blocks
    categorized = {}
    for idx, (orig_idx, item) in enumerate(unmatched):
        block = determine_time_block(item)
        if block not in categorized:
            categorized[block] = []
        categorized[block].append((idx, orig_idx, item))

    # Assign times within each block
    for block_name, block_items in categorized.items():
        base_start, base_end = blocks[block_name]
        start_hour, start_min = map(int, base_start.split(":"))
        end_hour, end_min = map(int, base_end.split(":"))
        total_block_minutes = (end_hour - start_hour) * 60 + (end_min - start_min)

        for pos, (idx, orig_idx, item) in enumerate(block_items):
            if len(block_items) > 1:
                offset = int(total_block_minutes * pos / len(block_items))
            else:
                offset = 0

            item_start_minutes = start_hour * 60 + start_min + offset
            duration = item.get("duration_minutes", 60)
            if not isinstance(duration, (int, float)):
                duration = 60
            item_end_minutes = item_start_minutes + int(duration)

            start_time = f"{item_start_minutes // 60:02d}:{item_start_minutes % 60:02d}"
            end_time = f"{item_end_minutes // 60:02d}:{item_end_minutes % 60:02d}"

            items[orig_idx]["time"] = {"start": start_time, "end": end_time}
            name = item.get("name_base", item.get("name", "Unknown"))
            print(f"    [DEFAULT]  {name}")
            print(f"               -> {start_time} - {end_time} ({block_name} block)")

    return items


def process_file(filepath: str, item_key: str, timeline_data: dict) -> int:
    """
    Process attractions.json or entertainment.json, filling time fields.

    Returns total number of items processed.
    """
    data = load_json(filepath)
    timeline_days = {d["day"]: d for d in timeline_data["data"]["days"]}

    total_items = 0
    matched_count = 0
    default_count = 0

    for day_entry in data["data"]["days"]:
        day_num = day_entry["day"]
        items = day_entry.get(item_key, [])

        if not items:
            continue

        print(f"\n  Day {day_num} ({day_entry.get('location', 'Unknown')}):")
        print(f"  {'=' * 60}")

        tl_day = timeline_days.get(day_num, {})
        timeline = tl_day.get("timeline", {})

        for item in items:
            total_items += 1
            name = item.get("name_base", item.get("name", "Unknown"))

            start, end, matched_key = find_timeline_match(item, timeline)

            if start and end:
                item["time"] = {"start": start, "end": end}
                matched_count += 1
                print(f"    [MATCHED]  {name}")
                print(f"               -> {start} - {end}")
                if matched_key:
                    print(f"               (timeline: {matched_key[:65]})")
            else:
                item["_needs_default"] = True

        # Assign defaults for unmatched items
        unmatched_items = [i for i in items if i.get("_needs_default")]
        if unmatched_items:
            assign_default_times(items, timeline)
            default_count += len(unmatched_items)

        # Clean up temporary markers
        for item in items:
            item.pop("_needs_default", None)

    save_json(filepath, data)

    print(f"\n  Summary for {item_key}:")
    print(f"    Total items:    {total_items}")
    print(f"    Matched:        {matched_count}")
    print(f"    Default:        {default_count}")

    return total_items


def validate_json(filepath: str) -> bool:
    """Validate that all items have properly structured time fields."""
    try:
        data = load_json(filepath)
    except json.JSONDecodeError as e:
        print(f"  INVALID JSON in {filepath}: {e}")
        return False

    errors = []
    for day_entry in data["data"]["days"]:
        day_num = day_entry["day"]
        for key in ["attractions", "entertainment"]:
            items = day_entry.get(key, [])
            for i, item in enumerate(items):
                name = item.get("name_base", item.get("name", f"item-{i}"))
                time_val = item.get("time")
                if not isinstance(time_val, dict):
                    errors.append(f"Day {day_num}, {name}: time is not a dict ({time_val})")
                elif not time_val.get("start") or not time_val.get("end"):
                    errors.append(f"Day {day_num}, {name}: time missing start/end")
                else:
                    for field in ["start", "end"]:
                        val = time_val[field]
                        if not re.match(r'^\d{2}:\d{2}$', val):
                            errors.append(
                                f"Day {day_num}, {name}: time.{field} "
                                f"bad format ({val})"
                            )

    if errors:
        print(f"  Validation errors in {filepath}:")
        for err in errors:
            print(f"    - {err}")
        return False

    print(f"  VALID: {filepath}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python fill-time-fields.py <trip_directory>")
        sys.exit(1)

    trip_dir = sys.argv[1]

    if not os.path.isdir(trip_dir):
        print(f"Error: Directory not found: {trip_dir}")
        sys.exit(1)

    attractions_path = os.path.join(trip_dir, "attractions.json")
    entertainment_path = os.path.join(trip_dir, "entertainment.json")
    timeline_path = os.path.join(trip_dir, "timeline.json")

    for p in [attractions_path, entertainment_path, timeline_path]:
        if not os.path.isfile(p):
            print(f"Error: File not found: {p}")
            sys.exit(1)

    timeline_data = load_json(timeline_path)

    print("=" * 70)
    print("PROCESSING ATTRACTIONS")
    print("=" * 70)
    attr_count = process_file(attractions_path, "attractions", timeline_data)

    print("\n" + "=" * 70)
    print("PROCESSING ENTERTAINMENT")
    print("=" * 70)
    ent_count = process_file(entertainment_path, "entertainment", timeline_data)

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    attr_valid = validate_json(attractions_path)
    ent_valid = validate_json(entertainment_path)

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Attractions processed:   {attr_count}")
    print(f"  Entertainment processed: {ent_count}")
    print(f"  Attractions valid:       {'YES' if attr_valid else 'NO'}")
    print(f"  Entertainment valid:     {'YES' if ent_valid else 'NO'}")

    if attr_valid and ent_valid:
        print("\n  All files updated and validated successfully.")
        sys.exit(0)
    else:
        print("\n  WARNING: Some validation errors detected.")
        sys.exit(2)


if __name__ == "__main__":
    main()
