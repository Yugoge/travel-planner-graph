#!/usr/bin/env python3
"""
Migrate legacy city_guides format to new trip_summary + days format.

Legacy format (city_guides):
{
  "bucket_list_type": "city_guides",
  "cities": [...]
}

New format (bucket_list):
{
  "trip_summary": {...},
  "days": [...]
}
"""

import json
import sys
from pathlib import Path


def migrate_skeleton(skeleton_path: Path) -> dict:
    """Migrate city_guides skeleton to new format"""

    with open(skeleton_path, 'r', encoding='utf-8') as f:
        old_skel = json.load(f)

    # Check if already new format
    if "trip_summary" in old_skel and "days" in old_skel:
        print("✓ Already in new format, no migration needed")
        return old_skel

    # Check if it's city_guides format
    if "bucket_list_type" not in old_skel or old_skel.get("bucket_list_type") != "city_guides":
        print("✗ Not a city_guides format skeleton")
        return old_skel

    print("Migrating city_guides format to new format...")

    cities = old_skel.get("cities", [])

    # Create trip_summary
    trip_summary = {
        "trip_type": "bucket_list",
        "description": f"City Guides - {len(cities)} cities",
        "base_location": "Beijing",
        "period": "",
        "travelers": "1 adult",
        "budget_per_trip": "€500",
        "preferences": {}
    }

    # Convert cities to days
    days = []
    day_counter = 1

    for city in cities:
        city_name = city.get("city", "Unknown")
        city_chinese = city.get("city_chinese", "")
        duration = city.get("recommended_duration", "2-3 days")

        # Get sample itinerary
        sample_itinerary = city.get("sample_itinerary", {})

        # Convert each day in sample_itinerary
        day_keys = sorted([k for k in sample_itinerary.keys() if k.startswith("day_")])

        for day_key in day_keys:
            activities = sample_itinerary[day_key]

            if isinstance(activities, list) and len(activities) > 0:
                days.append({
                    "day": day_counter,
                    "date": f"Day {day_counter}",
                    "location": city_name,
                    "trip_name": f"{city_name} / {city_chinese} ({duration})",
                    "user_plans": activities,
                    "location_change": None
                })
                day_counter += 1

    # Create new skeleton
    new_skel = {
        "trip_summary": trip_summary,
        "days": days
    }

    print(f"✓ Migrated {len(cities)} cities to {len(days)} days")

    return new_skel


def migrate_agent_data(data_dir: Path):
    """Migrate agent data from cities structure to days structure"""

    agent_files = ["attractions.json", "meals.json", "accommodation.json",
                   "entertainment.json", "transportation.json", "shopping.json"]

    for agent_file in agent_files:
        agent_path = data_dir / agent_file
        if not agent_path.exists():
            continue

        print(f"\nMigrating {agent_file}...")

        with open(agent_path, 'r', encoding='utf-8') as f:
            agent_data = json.load(f)

        # Extract actual data
        if "data" in agent_data:
            actual_data = agent_data["data"]
        else:
            actual_data = agent_data

        # Check if already has days structure
        if "days" in actual_data:
            print(f"  ✓ Already has days structure")
            continue

        # Check if has cities structure
        if "cities" not in actual_data:
            print(f"  ✗ No cities structure found")
            continue

        # Convert cities to days
        cities = actual_data.get("cities", [])
        days = []
        day_counter = 1

        for city in cities:
            city_name = city.get("city", "Unknown")

            # Determine how many days for this city (based on agent type)
            if agent_file == "attractions.json":
                items = city.get("attractions", [])
            elif agent_file == "meals.json":
                # Meals typically have breakfast/lunch/dinner per day
                # Estimate days based on meal count
                items = []
            elif agent_file == "accommodation.json":
                items = city.get("accommodations", [])
            elif agent_file == "entertainment.json":
                items = city.get("entertainment", [])
            elif agent_file == "shopping.json":
                items = city.get("shopping", [])
            elif agent_file == "transportation.json":
                items = []
            else:
                items = []

            # Create days for this city (estimate 2-3 days per city)
            num_days = max(2, min(4, len(items) // 3 + 1)) if items else 2

            for day_num in range(1, num_days + 1):
                day_data = {
                    "day": day_counter,
                    "location": city_name
                }

                # Add agent-specific data structure
                if agent_file == "attractions.json":
                    # Split attractions across days
                    start_idx = (day_num - 1) * 3
                    end_idx = day_num * 3
                    day_data["attractions"] = items[start_idx:end_idx]

                # Add to days list
                if agent_file == "attractions.json" and day_data.get("attractions"):
                    days.append(day_data)
                    day_counter += 1

        # Update agent data with days structure
        if "data" in agent_data:
            agent_data["data"]["days"] = days
            # Remove old cities structure
            if "cities" in agent_data["data"]:
                agent_data["data"].pop("cities")
        else:
            agent_data["days"] = days
            if "cities" in agent_data:
                agent_data.pop("cities")

        # Save migrated data
        backup_path = agent_path.with_suffix(".json.backup")
        if not backup_path.exists():
            import shutil
            shutil.copy(agent_path, backup_path)
            print(f"  ✓ Backup created: {backup_path.name}")

        with open(agent_path, 'w', encoding='utf-8') as f:
            json.dump(agent_data, f, ensure_ascii=False, indent=2)

        print(f"  ✓ Migrated to {len(days)} days")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 migrate-city-guides-format.py <destination-slug>")
        print("Example: python3 migrate-city-guides-format.py china-exchange-bucket-list-2026")
        sys.exit(1)

    destination_slug = sys.argv[1]
    data_dir = Path(__file__).parent.parent / "data" / destination_slug

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    skeleton_path = data_dir / "plan-skeleton.json"

    if not skeleton_path.exists():
        print(f"Error: Skeleton file not found: {skeleton_path}")
        sys.exit(1)

    print(f"==================================================")
    print(f"Migrating: {destination_slug}")
    print(f"==================================================\n")

    # Migrate skeleton
    print("Step 1: Migrating plan-skeleton.json...")
    new_skel = migrate_skeleton(skeleton_path)

    # Backup original
    backup_path = skeleton_path.with_suffix(".json.backup")
    if not backup_path.exists():
        import shutil
        shutil.copy(skeleton_path, backup_path)
        print(f"✓ Backup created: {backup_path.name}")

    # Save migrated skeleton
    with open(skeleton_path, 'w', encoding='utf-8') as f:
        json.dump(new_skel, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved migrated skeleton\n")

    # Migrate agent data
    print("Step 2: Migrating agent data files...")
    migrate_agent_data(data_dir)

    print(f"\n==================================================")
    print(f"✅ Migration complete!")
    print(f"==================================================")
    print(f"\nBackup files created with .backup extension")
    print(f"Test the HTML generation with:")
    print(f"  python3 scripts/generate-html-interactive.py {destination_slug}")


if __name__ == "__main__":
    main()
