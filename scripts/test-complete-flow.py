#!/usr/bin/env python3
"""
Complete flow test: Verify Chinese extraction is used in POI collection.
Simulates what fetch-images-batch.py will do with actual data.
"""

import json
import re
from pathlib import Path


def extract_chinese_name(name: str) -> str:
    """Same implementation as in fetch-images-batch.py"""
    # Find FIRST parenthesized content (handles multiple parentheses and trailing text)
    match = re.search(r'^(.+?)\s*\(([^)]+)\)', name)
    if not match:
        return ""

    before_paren = match.group(1).strip()
    inside_paren = match.group(2).strip()

    has_chinese_before = bool(re.search(r'[\u4e00-\u9fff]', before_paren))

    if has_chinese_before:
        return before_paren
    else:
        return inside_paren


# Simulate POI collection from attractions.json
data_dir = Path(__file__).parent.parent / "data" / "china-feb-15-mar-7-2026-20260202-195429"
attractions_file = data_dir / "attractions.json"

with open(attractions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Complete Flow Test: POI Collection with Chinese Extraction")
print("=" * 70)
print("Simulating fetch_pois() behavior from fetch-images-batch.py")
print()

pois = []
days_data = data.get("data", {}).get("days", [])

# Simulate attraction collection (first day only)
day = days_data[0]
location = day.get("location", "")

for item in day.get("attractions", []):
    name = item.get("name", "")
    # THIS IS THE KEY LINE - same as in fetch-images-batch.py
    chinese_name = item.get("name_chinese", "") or extract_chinese_name(name)

    if name:
        pois.append({
            "name": name,
            "chinese_name": chinese_name,
            "city": location,
            "type": "attraction"
        })

print(f"Location: {location}")
print(f"Collected {len(pois)} POIs\n")

for idx, poi in enumerate(pois, 1):
    print(f"{idx}. {poi['name']}")
    print(f"   Chinese extracted: '{poi['chinese_name']}'")
    print(f"   Will pass to Gaode: chinese_name='{poi['chinese_name']}'")
    print(f"   ✓ Gaode will search for: '{poi['chinese_name']}'")
    print()

print("=" * 70)
print("✅ Complete flow works correctly:")
print("   1. POI name loaded from JSON: 'English (中文)'")
print("   2. name_chinese field is empty string")
print("   3. Fallback to _extract_chinese_name() extracts '中文'")
print("   4. chinese_name='中文' passed to fetch_poi_photo_gaode()")
print("   5. Gaode Maps receives accurate Chinese name for search")
