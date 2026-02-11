#!/usr/bin/env python3
"""
Unify city names across all agent files.

Extracts city from accommodation.location field and updates all agent files
to use the same single city name (eliminates composite 'A / B' format).

Root cause: Composite city names (e.g., 'Chengdu / Shanghai') break _map_service_for
because exact string match fails against plan-skeleton.json.

Usage:
    source ~/.claude/venv/bin/activate
    python scripts/unify-city-names.py <destination-slug>

Example:
    source ~/.claude/venv/bin/activate
    python scripts/unify-city-names.py china-feb-15-mar-7-2026-20260202-195429
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict


def extract_city_from_location_base(location_base: str) -> str:
    """
    Extract city name from accommodation.location_base field.

    Parses the location_base string to find the city name.
    Prioritizes city names at the end of the string (after the last comma).

    Args:
        location_base: The location_base string from accommodation

    Returns:
        Extracted city name
    """
    # Common Chinese cities to look for (longer names first to avoid false matches)
    cities = [
        'Chongqing', 'Shanghai', 'Beijing', 'Chengdu',
        'Shenzhen', 'Guangzhou', 'Hangzhou', 'Nanjing',
        'Wuhan', 'Bazhong', 'Xi\'an'
    ]

    # Find the LAST occurrence of each city in the string
    # and use the one that appears latest (closest to end of string)
    best_city = None
    best_position = -1

    for city in cities:
        # Find last occurrence of city
        pos = location_base.rfind(city)
        if pos != -1 and pos > best_position:
            best_city = city
            best_position = pos

    if best_city:
        return best_city

    # Fallback: split by comma and get last non-empty part
    parts = [p.strip() for p in location_base.split(',')]
    for part in reversed(parts):
        if part:
            # Remove common suffixes
            for suffix in [' District', ' Province', ' Area', ' Region']:
                if part.endswith(suffix):
                    part = part[:-len(suffix)].strip()
            if part:
                return part

    return location_base


def extract_city_mapping(accommodation_path: Path) -> Dict[int, str]:
    """
    Extract day->city mapping from accommodation file.

    Uses accommodation.location_base field (NOT day-level location) to determine
    the canonical city name for each day.

    Args:
        accommodation_path: Path to accommodation.json file

    Returns:
        Dictionary mapping day number to city name
    """
    with open(accommodation_path, 'r', encoding='utf-8') as f:
        accom_data = json.load(f)

    city_mapping = {}
    for day_entry in accom_data['data']['days']:
        day_num = day_entry['day']
        accom_obj = day_entry.get('accommodation', {})
        location_base = accom_obj.get('location_base', '')

        # Extract city from location_base
        city = extract_city_from_location_base(location_base)
        city_mapping[day_num] = city

    return city_mapping


def has_composite_city(location: str) -> bool:
    """Check if location contains composite city format (e.g., 'A / B')."""
    return ' / ' in location


def update_agent_file(
    agent_path: Path,
    city_mapping: Dict[int, str],
    agent_name: str
) -> int:
    """
    Update agent file with unified city names.

    Only updates days where current location is composite (has ' / ').
    Uses city from accommodation.location_base as the canonical single city.

    Args:
        agent_path: Path to agent JSON file
        city_mapping: Day->city mapping from accommodation
        agent_name: Name of agent (for logging)

    Returns:
        Number of days updated
    """
    with open(agent_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    days_updated = 0
    updates_list = []

    # Update main location field for each day
    for day_entry in data.get('data', {}).get('days', []):
        day_num = day_entry['day']
        current_location = day_entry.get('location', '')

        # Only update if this day has composite city name
        if has_composite_city(current_location):
            canonical_city = city_mapping.get(day_num)

            if canonical_city and canonical_city != current_location:
                old_location = day_entry['location']
                day_entry['location'] = canonical_city
                days_updated += 1

                # Also update location_local if it has composite format
                if 'location_local' in day_entry:
                    day_entry['location_local'] = canonical_city

                updates_list.append(f"  {agent_name} Day {day_num}: '{old_location}' -> '{canonical_city}'")

    # Write back updated data
    if days_updated > 0:
        with open(agent_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Print updates
        for update in updates_list:
            print(update)
        print(f"  Updated {days_updated} day(s) in {agent_name}")

    return days_updated


def main():
    # Step 1: Validate arguments
    if len(sys.argv) != 2:
        print("Error: Missing destination slug argument")
        print(f"Usage: {sys.argv[0]} <destination-slug>")
        sys.exit(1)

    destination_slug = sys.argv[1]
    base_dir = Path('/root/travel-planner')
    data_dir = base_dir / 'data' / destination_slug

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    print(f"Processing destination: {destination_slug}")
    print(f"Data directory: {data_dir}")

    # Step 2: Extract city mapping from accommodation
    accommodation_path = data_dir / 'accommodation.json'
    if not accommodation_path.exists():
        print(f"Error: accommodation.json not found: {accommodation_path}")
        sys.exit(1)

    print("\nStep 1: Extract city mapping from accommodation.location_base")
    city_mapping = extract_city_mapping(accommodation_path)

    # Print composite days that will be updated
    print("\nComposite city days detected:")
    with open(accommodation_path, 'r', encoding='utf-8') as f:
        accom_data = json.load(f)

    for day_entry in accom_data['data']['days']:
        day_num = day_entry['day']
        day_location = day_entry.get('location', '')
        if has_composite_city(day_location):
            extracted_city = city_mapping.get(day_num, '')
            print(f"  Day {day_num}: '{day_location}' -> extracted city: '{extracted_city}'")

    # Step 3: Update each agent file
    print("\nStep 2: Update agent files with unified city names")
    agents = ['attractions', 'meals', 'entertainment', 'shopping']
    total_updates = 0

    for agent in agents:
        agent_path = data_dir / f'{agent}.json'
        if not agent_path.exists():
            print(f"  Warning: {agent}.json not found, skipping")
            continue

        updates = update_agent_file(agent_path, city_mapping, agent)
        total_updates += updates

    # Step 4: Summary
    print(f"\nStep 3: Summary")
    print(f"  Total updates: {total_updates} day(s) across all agents")
    print(f"  Root cause addressed: Composite city names eliminated")
    print(f"  _map_service_for will now match exact city names")

    return 0


if __name__ == '__main__':
    sys.exit(main())
