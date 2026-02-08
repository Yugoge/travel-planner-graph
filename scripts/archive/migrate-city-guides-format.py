#!/usr/bin/env python3
"""
Migrate legacy city_guides format to new trip_summary + days format.

Root cause: commit 06d35f5 introduced city_guides format for bucket list plans.
This migration unifies all plans to use trip_summary + days format.

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
from typing import Dict, List, Any


def parse_duration(duration_str: str) -> int:
    """Parse duration string like '3-4 days' to get number of days"""
    # Extract first number from string like "3-4 days", "2-3 days", etc.
    parts = duration_str.split('-')
    try:
        return int(parts[0].strip().split()[0])
    except (ValueError, IndexError):
        return 2  # Default to 2 days


def migrate_skeleton(skeleton_path: Path) -> dict:
    """Migrate city_guides skeleton to trip_summary + days format"""

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

    print("Migrating city_guides format to trip_summary + days format...")

    cities = old_skel.get("cities", [])

    # Create trip_summary
    trip_summary = {
        "trip_type": "bucket_list",
        "description": f"China Exchange Bucket List - {len(cities)} Destination Cities",
        "base_location": "Beijing",
        "period": "March-June 2026",
        "travelers": "1 adult",
        "budget_per_trip": "€200-500 per trip",
        "preferences": {
            "trip_style": "Weekend trips and short holidays from Beijing base",
            "focus": "Cultural exploration, natural scenery, food experiences",
            "constraints": "Exchange student budget, weekend availability"
        }
    }

    # Convert cities to days (each city becomes trip with multiple days)
    days = []
    day_counter = 1

    for city in cities:
        city_name = city.get("city", "Unknown")
        city_chinese = city.get("city_chinese", "")
        duration_str = city.get("recommended_duration", "2-3 days")
        num_days = parse_duration(duration_str)

        user_requirements = city.get("user_requirements", [])
        trip_type = city.get("trip_type", "weekend")
        best_months = city.get("best_months", [])
        special_note = city.get("special_note", "")

        # Create days for this city (each day is a separate entry)
        for day_num in range(1, num_days + 1):
            # Build trip_name for first day only
            if day_num == 1:
                trip_name = f"{city_name} / {city_chinese} ({duration_str})"
                if special_note:
                    trip_name += f" - {special_note}"
            else:
                trip_name = None

            # Build user_plans from requirements
            user_plans = []
            if day_num == 1 and user_requirements:
                user_plans = user_requirements
            elif day_num == 1:
                user_plans = [f"Explore {city_name}"]

            # Add metadata to user plans
            if day_num == 1 and best_months:
                user_plans.append(f"Best months: {', '.join(best_months)}")
            if day_num == 1 and trip_type:
                user_plans.append(f"Trip type: {trip_type}")

            days.append({
                "day": day_counter,
                "date": f"Day {day_counter}",
                "location": city_name,
                "trip_name": trip_name,
                "user_plans": user_plans,
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


def migrate_agent_data(data_dir: Path, skeleton: dict):
    """Migrate agent data from cities structure to days structure"""

    # Get city to days mapping from skeleton
    city_to_days = {}
    days_data = skeleton.get("days", [])

    for day in days_data:
        location = day.get("location")
        if location:
            if location not in city_to_days:
                city_to_days[location] = []
            city_to_days[location].append(day.get("day"))

    print(f"\nCity to days mapping: {len(city_to_days)} cities")
    for city, day_nums in city_to_days.items():
        print(f"  {city}: {len(day_nums)} days (days {day_nums[0]}-{day_nums[-1]})")

    agent_files = [
        "attractions.json",
        "meals.json",
        "accommodation.json",
        "entertainment.json",
        "transportation.json",
        "shopping.json"
    ]

    for agent_file in agent_files:
        agent_path = data_dir / agent_file
        if not agent_path.exists():
            print(f"\n⚠ {agent_file} not found, skipping")
            continue

        print(f"\nMigrating {agent_file}...")

        with open(agent_path, 'r', encoding='utf-8') as f:
            agent_data = json.load(f)

        # Check if already has days structure
        if "data" in agent_data and "days" in agent_data["data"]:
            print(f"  ✓ Already has days structure")
            continue

        # Check if has cities structure
        cities_data = None
        if "cities" in agent_data:
            cities_data = agent_data["cities"]
        elif "data" in agent_data and "cities" in agent_data["data"]:
            cities_data = agent_data["data"]["cities"]

        if not cities_data:
            print(f"  ✗ No cities structure found")
            continue

        # Convert cities to days based on agent type
        new_days = []

        if agent_file == "attractions.json":
            new_days = migrate_attractions(cities_data, city_to_days)
        elif agent_file == "meals.json":
            new_days = migrate_meals(cities_data, city_to_days)
        elif agent_file == "accommodation.json":
            new_days = migrate_accommodation(cities_data, city_to_days)
        elif agent_file == "entertainment.json":
            new_days = migrate_entertainment(cities_data, city_to_days)
        elif agent_file == "shopping.json":
            new_days = migrate_shopping(cities_data, city_to_days)
        elif agent_file == "transportation.json":
            new_days = migrate_transportation(cities_data, city_to_days)

        # Update agent data structure
        if "data" in agent_data:
            agent_data["data"]["days"] = new_days
            # Remove old cities structure
            if "cities" in agent_data["data"]:
                agent_data["data"].pop("cities")
        else:
            # Wrap in data structure
            agent_data = {
                "agent": agent_data.get("agent", agent_file.replace(".json", "")),
                "status": agent_data.get("status", "complete"),
                "data": {
                    "days": new_days
                }
            }
            # Preserve other top-level fields
            for key in ["data_sources", "notes"]:
                if key in agent_data:
                    agent_data[key] = agent_data[key]

        # Backup original
        backup_path = agent_path.with_suffix(".json.backup")
        if not backup_path.exists():
            import shutil
            shutil.copy(agent_path, backup_path)
            print(f"  ✓ Backup created: {backup_path.name}")

        # Save migrated data
        with open(agent_path, 'w', encoding='utf-8') as f:
            json.dump(agent_data, f, ensure_ascii=False, indent=2)

        print(f"  ✓ Migrated to {len(new_days)} days")


def migrate_attractions(cities: List[Dict], city_to_days: Dict) -> List[Dict]:
    """Migrate attractions from cities to days structure"""
    days = []

    for city_data in cities:
        city = city_data.get("city")
        day_nums = city_to_days.get(city, [])
        attractions = city_data.get("attractions", [])

        if not attractions or not day_nums:
            continue

        # Distribute attractions across days (3-4 per day)
        attrs_per_day = max(3, len(attractions) // len(day_nums))

        for idx, day_num in enumerate(day_nums):
            start_idx = idx * attrs_per_day
            end_idx = start_idx + attrs_per_day
            day_attrs = attractions[start_idx:end_idx]

            if day_attrs:
                days.append({
                    "day": day_num,
                    "location": city,
                    "attractions": [
                        {
                            "name": attr.get("name", ""),
                            "name_en": attr.get("name_chinese", ""),
                            "type": attr.get("type", ""),
                            "cost": attr.get("ticket_price_eur", 0) * 7.8,  # Convert EUR to CNY
                            "cost_eur": attr.get("ticket_price_eur", 0),
                            "opening_hours": attr.get("opening_hours", ""),
                            "recommended_duration": f"{attr.get('recommended_duration_hours', 2)}h",
                            "highlights": attr.get("tips", [])[:3] if attr.get("tips") else [],
                            "links": {}
                        }
                        for attr in day_attrs
                    ]
                })

    return days


def migrate_meals(cities: List[Dict], city_to_days: Dict) -> List[Dict]:
    """Migrate meals from cities to days structure"""
    days = []

    for city_data in cities:
        city = city_data.get("city")
        day_nums = city_to_days.get(city, [])
        restaurants = city_data.get("restaurants", [])

        if not restaurants or not day_nums:
            continue

        # Distribute restaurants as breakfast/lunch/dinner across days
        meal_types = ["breakfast", "lunch", "dinner"]

        for day_num in day_nums:
            day_meals = {}

            # Assign 3 meals per day
            for meal_idx, meal_type in enumerate(meal_types):
                rest_idx = ((day_num - day_nums[0]) * 3 + meal_idx) % len(restaurants)
                restaurant = restaurants[rest_idx]

                day_meals[meal_type] = {
                    "name": restaurant.get("name", ""),
                    "name_en": restaurant.get("name_chinese", ""),
                    "cost": restaurant.get("average_cost_eur", 0) * 7.8,  # Convert EUR to CNY
                    "cuisine": restaurant.get("cuisine_type", ""),
                    "signature_dishes": ", ".join(restaurant.get("signature_dishes", [])[:3]),
                    "links": {}
                }

            days.append({
                "day": day_num,
                "location": city,
                **day_meals
            })

    return days


def migrate_accommodation(cities: List[Dict], city_to_days: Dict) -> List[Dict]:
    """Migrate accommodation from cities to days structure"""
    days = []

    for city_data in cities:
        city = city_data.get("city")
        day_nums = city_to_days.get(city, [])
        hotels = city_data.get("recommended_hotels", [])

        if not hotels or not day_nums:
            continue

        # Use first recommended hotel for all days in this city
        hotel = hotels[0]

        for day_num in day_nums:
            days.append({
                "day": day_num,
                "location": city,
                "accommodation": {
                    "name": hotel.get("name", ""),
                    "name_cn": hotel.get("name_chinese", ""),
                    "type": hotel.get("hotel_type", "hotel"),
                    "location": hotel.get("location", ""),
                    "cost": hotel.get("price_per_night_eur", 0) * 7.8,  # Convert EUR to CNY
                    "stars": hotel.get("rating", 3),
                    "links": {}
                }
            })

    return days


def migrate_entertainment(cities: List[Dict], city_to_days: Dict) -> List[Dict]:
    """Migrate entertainment from cities to days structure"""
    days = []

    for city_data in cities:
        city = city_data.get("city")
        day_nums = city_to_days.get(city, [])
        entertainment = city_data.get("entertainment", [])

        if not entertainment or not day_nums:
            continue

        # Distribute entertainment across days (1-2 per day in evening)
        for idx, day_num in enumerate(day_nums):
            ent_idx = idx % len(entertainment)
            ent = entertainment[ent_idx]

            days.append({
                "day": day_num,
                "location": city,
                "entertainment": [
                    {
                        "name": ent.get("name", ""),
                        "name_en": ent.get("name_chinese", ""),
                        "type": ent.get("type", ""),
                        "cost": ent.get("cost_eur", 0) * 7.8,  # Convert EUR to CNY
                        "duration": ent.get("duration", "2h"),
                        "note": ent.get("description", ""),
                        "links": {}
                    }
                ]
            })

    return days


def migrate_shopping(cities: List[Dict], city_to_days: Dict) -> List[Dict]:
    """Migrate shopping from cities to days structure"""
    days = []

    for city_data in cities:
        city = city_data.get("city")
        day_nums = city_to_days.get(city, [])
        shopping = city_data.get("shopping", [])

        if not shopping or not day_nums:
            continue

        # Add shopping to days
        for day_num in day_nums:
            days.append({
                "day": day_num,
                "location": city,
                "shopping": shopping
            })

    return days


def migrate_transportation(cities: List[Dict], city_to_days: Dict) -> List[Dict]:
    """Migrate transportation from cities to days structure"""
    days = []

    for city_data in cities:
        city = city_data.get("city")
        day_nums = city_to_days.get(city, [])
        transport = city_data.get("transportation", {})

        if not day_nums:
            continue

        # Add transportation info to first day of city
        if day_nums:
            days.append({
                "day": day_nums[0],
                "location": city,
                "transportation": transport
            })

    return days


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
    print(f"Root cause: commit 06d35f5 - city_guides format")
    print(f"Target: trip_summary + days format")
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
    migrate_agent_data(data_dir, new_skel)

    print(f"\n==================================================")
    print(f"✅ Migration complete!")
    print(f"==================================================")
    print(f"\nBackup files created with .backup extension")
    print(f"Test the HTML generation with:")
    print(f"  python3 scripts/generate-html-interactive.py {destination_slug}")


if __name__ == "__main__":
    main()
