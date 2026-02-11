#!/usr/bin/env python3
"""
Add 'optional' field to all POI entries in agent JSON files.

This script reads agent JSON files (attractions, meals, accommodation, etc.)
and adds the 'optional' field to each POI based on:
1. Existing 'optional' field (if present)
2. '- Optional' suffix in name
3. 'optional' keyword in notes_base/notes_local
Default: false (not optional)
"""

import json
import sys
import re
from pathlib import Path


def detect_optional(poi):
    """Detect if a POI should be marked as optional."""
    # Check explicit optional field
    if 'optional' in poi:
        return poi['optional']

    # Check for - Optional suffix in name (case-insensitive)
    for name_field in ['name_base', 'name_local', 'name']:
        if name_field in poi:
            name = poi[name_field]
            if isinstance(name, str):
                # Check English pattern
                if re.search(r'[-–—]\s*Optional\b', name, re.IGNORECASE):
                    return True
                # Check Chinese patterns
                if '（可选）' in name or '（非必选）' in name or '备选' in name:
                    return True

    # Check for optional keyword in notes (case-insensitive)
    for notes_field in ['notes_base', 'notes_local', 'notes', 'note_base', 'note_local']:
        if notes_field in poi:
            notes = poi[notes_field]
            if isinstance(notes, str):
                # Check for "optional" at start of sentence or with word boundary
                if re.search(r'\bOptional\b', notes, re.IGNORECASE):
                    return True

    return False


def process_attractions(data):
    """Process attractions array."""
    for day in data.get('days', []):
        for attraction in day.get('attractions', []):
            if 'optional' not in attraction:
                attraction['optional'] = detect_optional(attraction)
    return data


def process_meals(data):
    """Process meals (breakfast/lunch/dinner)."""
    for day in data.get('days', []):
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            meal = day.get(meal_type)
            if meal and isinstance(meal, dict):
                if 'optional' not in meal:
                    meal['optional'] = detect_optional(meal)
    return data


def process_entertainment(data):
    """Process entertainment array."""
    for day in data.get('days', []):
        for ent in day.get('entertainment', []):
            if 'optional' not in ent:
                ent['optional'] = detect_optional(ent)
    return data


def process_shopping(data):
    """Process shopping array."""
    for day in data.get('days', []):
        for shop in day.get('shopping', []):
            if 'optional' not in shop:
                shop['optional'] = detect_optional(shop)
    return data


def process_accommodation(data):
    """Process accommodation (single item per day)."""
    for day in data.get('days', []):
        acc = day.get('accommodation')
        if acc and isinstance(acc, dict):
            if 'optional' not in acc:
                acc['optional'] = False  # Accommodation is never optional
    return data


def process_file(file_path, processor_func, agent_name):
    """Process a single agent file."""
    print(f"\n{'='*60}")
    print(f"Processing: {file_path.name} ({agent_name})")
    print(f"{'='*60}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Count before
    optional_count_before = 0
    total_count = 0

    # Get structure - handle both formats
    days = data.get('days', data.get('data', {}).get('days', []))

    if agent_name == 'accommodation':
        for day in days:
            acc = day.get('accommodation')
            if acc:
                total_count += 1
                if acc.get('optional'):
                    optional_count_before += 1
    elif agent_name == 'meals':
        for day in days:
            for mt in ['breakfast', 'lunch', 'dinner']:
                meal = day.get(mt)
                if meal:
                    total_count += 1
                    if meal.get('optional'):
                        optional_count_before += 1
    else:
        key = agent_name
        for day in days:
            items = day.get(key, [])
            total_count += len(items)
            for item in items:
                if item.get('optional'):
                    optional_count_before += 1

    # Process
    data = processor_func(data)

    # Count after
    optional_count_after = 0
    if agent_name == 'accommodation':
        for day in days:
            acc = day.get('accommodation')
            if acc and acc.get('optional'):
                optional_count_after += 1
    elif agent_name == 'meals':
        for day in days:
            for mt in ['breakfast', 'lunch', 'dinner']:
                meal = day.get(mt)
                if meal and meal.get('optional'):
                    optional_count_after += 1
    else:
        key = agent_name
        for day in days:
            items = day.get(key, [])
            for item in items:
                if item.get('optional'):
                    optional_count_after += 1

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Total items: {total_count}")
    print(f"Optional (before): {optional_count_before}")
    print(f"Optional (after): {optional_count_after}")
    print(f"Added: {optional_count_after - optional_count_before}")

    return data


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 add-optional-field.py <destination-slug>")
        sys.exit(1)

    destination = sys.argv[1]
    data_dir = Path(__file__).parent.parent / 'data' / destination

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    # Process each agent file
    agents = [
        ('attractions.json', process_attractions, 'attractions'),
        ('meals.json', process_meals, 'meals'),
        ('accommodation.json', process_accommodation, 'accommodation'),
        ('entertainment.json', process_entertainment, 'entertainment'),
        ('shopping.json', process_shopping, 'shopping'),
    ]

    total_optional_added = 0

    for filename, processor, agent_name in agents:
        file_path = data_dir / filename
        if file_path.exists():
            try:
                process_file(file_path, processor, agent_name)
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        else:
            print(f"Skipping {filename} (not found)")

    print(f"\n{'='*60}")
    print("✅ All files processed!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
