#!/usr/bin/env python3
"""
Fetch missing POI images from Gaode Maps API for the travel planner.

Scans all agent JSON files (meals, attractions, entertainment, shopping,
accommodation) and identifies POIs that are missing from images.json.
Then queries the Gaode Maps POI search API to find photos for each.

Usage: python scripts/fetch-gaode-images.py <trip_dir> <api_key>
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

# Parameters
TRIP_DIR = sys.argv[1] if len(sys.argv) > 1 else None
API_KEY = sys.argv[2] if len(sys.argv) > 2 else None
DELAY_SECONDS = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2

if not TRIP_DIR or not API_KEY:
    print("Usage: python fetch-gaode-images.py <trip_dir> <api_key> [delay_seconds]")
    print("  trip_dir: Path to trip data directory containing agent JSON files")
    print("  api_key: Gaode Maps API key")
    print("  delay_seconds: Delay between API calls (default: 0.2)")
    sys.exit(1)

# Agent files to scan for POIs
AGENT_FILES = [
    "meals.json",
    "attractions.json",
    "entertainment.json",
    "shopping.json",
    "accommodation.json",
]

# Home activities that won't have Gaode POI results
HOME_ACTIVITIES = {
    "Making Dumplings Together",
    "Free Time",
    "Reunion Dinner and Spring Festival Gala",
    "Midnight Countdown and First Dumplings",
}

# POIs that need image fixes (search term overrides)
FIX_POIS = {
    "gaode_Always Coffee Roaster": "Always Coffee Roaster 上海",
    "gaode_Shanghai Disneyland In-Park Dining": "上海迪士尼乐园 餐饮",
}

# Cities that need cover images added
# Only add cities that actually appear in the trip data
EXISTING_CITY_COVERS = {"Shanghai", "Beijing", "Bazhong", "Chongqing", "Chengdu"}


def gaode_search(keywords, city="", extensions="all"):
    """Search Gaode Maps POI API and return first result's photo URL."""
    params = {
        "key": API_KEY,
        "keywords": keywords,
        "extensions": extensions,
        "output": "json",
    }
    if city:
        params["city"] = city

    url = "https://restapi.amap.com/v3/place/text?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TravelPlanner/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("status") == "1" and data.get("pois"):
            for poi in data["pois"]:
                photos = poi.get("photos", [])
                if photos and photos[0].get("url"):
                    url = photos[0]["url"]
                    # Ensure HTTPS (Gaode CDN supports it; avoids mixed-content on HTTPS pages)
                    return url.replace("http://", "https://", 1)
        return None
    except Exception as e:
        print(f"  [ERROR] API call failed: {e}")
        return None


def extract_pois_from_meals(data):
    """Extract POI entries from meals agent data."""
    pois = []
    for day_data in data.get("data", {}).get("days", []):
        day_num = day_data.get("day", 0)
        location = day_data.get("location", "")
        for meal_type in ["breakfast", "lunch", "dinner"]:
            meal = day_data.get(meal_type)
            if meal and isinstance(meal, dict):
                name_base = meal.get("name_base", "")
                name_local = meal.get("name_local", "")
                if name_base:
                    pois.append({
                        "name_base": name_base,
                        "name_local": name_local,
                        "city": location,
                        "day": day_num,
                        "type": "meal",
                    })
    return pois


def extract_pois_from_attractions(data):
    """Extract POI entries from attractions agent data."""
    pois = []
    for day_data in data.get("data", {}).get("days", []):
        day_num = day_data.get("day", 0)
        location = day_data.get("location", "")
        for attr in day_data.get("attractions", []):
            if isinstance(attr, dict):
                name_base = attr.get("name_base", "")
                name_local = attr.get("name_local", "")
                if name_base:
                    pois.append({
                        "name_base": name_base,
                        "name_local": name_local,
                        "city": location,
                        "day": day_num,
                        "type": "attraction",
                    })
    return pois


def extract_pois_from_entertainment(data):
    """Extract POI entries from entertainment agent data."""
    pois = []
    for day_data in data.get("data", {}).get("days", []):
        day_num = day_data.get("day", 0)
        location = day_data.get("location", "")
        for ent in day_data.get("entertainment", []):
            if isinstance(ent, dict):
                name_base = ent.get("name_base", "")
                name_local = ent.get("name_local", "")
                if name_base:
                    pois.append({
                        "name_base": name_base,
                        "name_local": name_local,
                        "city": location,
                        "day": day_num,
                        "type": "entertainment",
                    })
    return pois


def extract_pois_from_shopping(data):
    """Extract POI entries from shopping agent data."""
    pois = []
    for day_data in data.get("data", {}).get("days", []):
        day_num = day_data.get("day", 0)
        location = day_data.get("location", "")
        for shop in day_data.get("shopping", []):
            if isinstance(shop, dict):
                name_base = shop.get("name_base", "")
                name_local = shop.get("name_local", "")
                if name_base:
                    pois.append({
                        "name_base": name_base,
                        "name_local": name_local,
                        "city": location,
                        "day": day_num,
                        "type": "shopping",
                    })
    return pois


def extract_pois_from_accommodation(data):
    """Extract POI entries from accommodation agent data."""
    pois = []
    for day_data in data.get("data", {}).get("days", []):
        day_num = day_data.get("day", 0)
        location = day_data.get("location", "")
        acc = day_data.get("accommodation")
        if acc and isinstance(acc, dict):
            name_base = acc.get("name_base", "")
            name_local = acc.get("name_local", "")
            if name_base:
                pois.append({
                    "name_base": name_base,
                    "name_local": name_local,
                    "city": location,
                    "day": day_num,
                    "type": "accommodation",
                })
    return pois


EXTRACTORS = {
    "meals.json": extract_pois_from_meals,
    "attractions.json": extract_pois_from_attractions,
    "entertainment.json": extract_pois_from_entertainment,
    "shopping.json": extract_pois_from_shopping,
    "accommodation.json": extract_pois_from_accommodation,
}


def get_city_for_search(city_str):
    """Extract the primary city name for Gaode search from location strings.

    Some location strings contain slashes like 'Bazhong / Chengdu' or
    'Shanghai / Beijing'. Return the first city.
    """
    if "/" in city_str:
        return city_str.split("/")[0].strip()
    return city_str.strip()


def get_city_chinese(city):
    """Map English city names to Chinese for better Gaode search results."""
    mapping = {
        "Chongqing": "重庆",
        "Bazhong": "巴中",
        "Chengdu": "成都",
        "Shanghai": "上海",
        "Beijing": "北京",
        "Tianjin": "天津",
        "Suzhou": "苏州",
        "Hangzhou": "杭州",
    }
    return mapping.get(city, city)


def main():
    images_path = os.path.join(TRIP_DIR, "images.json")

    # Load current images.json
    with open(images_path, "r", encoding="utf-8") as f:
        images = json.load(f)

    existing_pois = images.get("pois", {})
    city_covers = images.get("city_covers", {})

    print(f"Current images.json has {len(existing_pois)} POI entries")
    print(f"Current city_covers: {list(city_covers.keys())}")
    print()

    # Step 1: Collect all POIs from all agent files
    all_pois = []
    for agent_file in AGENT_FILES:
        filepath = os.path.join(TRIP_DIR, agent_file)
        if not os.path.exists(filepath):
            print(f"[SKIP] {agent_file} not found")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        extractor = EXTRACTORS.get(agent_file)
        if extractor:
            pois = extractor(data)
            all_pois.extend(pois)
            print(f"[LOADED] {agent_file}: {len(pois)} POIs")

    print(f"\nTotal POIs found across all agents: {len(all_pois)}")

    # Deduplicate by name_base
    seen = set()
    unique_pois = []
    for poi in all_pois:
        if poi["name_base"] not in seen:
            seen.add(poi["name_base"])
            unique_pois.append(poi)

    print(f"Unique POIs: {len(unique_pois)}")

    # Step 2: Find POIs missing from images.json
    missing_pois = []
    for poi in unique_pois:
        key = f"gaode_{poi['name_base']}"
        if key not in existing_pois:
            missing_pois.append(poi)

    print(f"POIs missing images: {len(missing_pois)}")
    print()

    # Step 3: Fix specific wrong images
    api_calls = 0
    print("=" * 60)
    print("FIXING WRONG IMAGES")
    print("=" * 60)

    for poi_key, search_term in FIX_POIS.items():
        print(f"\n[FIX] {poi_key}")
        print(f"  Search: {search_term}")
        time.sleep(DELAY_SECONDS)
        photo_url = gaode_search(search_term)
        api_calls += 1
        if photo_url:
            existing_pois[poi_key] = photo_url
            print(f"  FOUND: {photo_url[:80]}...")
        else:
            print(f"  NOT FOUND - keeping existing")

    # Step 4: Fix Bazhong home activities
    print()
    print("=" * 60)
    print("FIXING HOME ACTIVITIES")
    print("=" * 60)

    bazhong_cover = city_covers.get("Bazhong", "")
    for poi in unique_pois:
        if poi["name_base"] in HOME_ACTIVITIES:
            key = f"gaode_{poi['name_base']}"
            if key in existing_pois:
                print(f"\n[HOME] {poi['name_base']}")
                print(f"  Setting to Bazhong city cover (home activity)")
                existing_pois[key] = bazhong_cover
            else:
                print(f"\n[HOME] {poi['name_base']} - not in images.json, adding with Bazhong cover")
                existing_pois[key] = bazhong_cover

    # Step 5: Fetch missing POI images
    print()
    print("=" * 60)
    print("FETCHING MISSING POI IMAGES")
    print("=" * 60)

    fetched = 0
    not_found = 0

    for poi in missing_pois:
        name_base = poi["name_base"]
        name_local = poi["name_local"]
        city = get_city_for_search(poi["city"])
        city_cn = get_city_chinese(city)
        key = f"gaode_{name_base}"

        # Skip home activities (already handled)
        if name_base in HOME_ACTIVITIES:
            continue

        print(f"\n[Day {poi['day']}] [{city}] {name_base}")

        # Strategy 1: Search with name_local (Chinese name) + city
        search_term = name_local if name_local else name_base
        print(f"  Search 1: '{search_term}' in city '{city_cn}'")
        time.sleep(DELAY_SECONDS)
        photo_url = gaode_search(search_term, city=city_cn)
        api_calls += 1

        # Strategy 2: Search with just the name (no city filter)
        if not photo_url and name_local:
            print(f"  Search 2: '{name_local}' (no city)")
            time.sleep(DELAY_SECONDS)
            photo_url = gaode_search(name_local)
            api_calls += 1

        # Strategy 3: Try English name with city
        if not photo_url and name_local != name_base:
            print(f"  Search 3: '{name_base}' in city '{city_cn}'")
            time.sleep(DELAY_SECONDS)
            photo_url = gaode_search(name_base, city=city_cn)
            api_calls += 1

        # Strategy 4: City name as fallback (generic city photo)
        if not photo_url:
            print(f"  Search 4 (fallback): '{city_cn} 景区'")
            time.sleep(DELAY_SECONDS)
            photo_url = gaode_search(f"{city_cn} 景区", city=city_cn)
            api_calls += 1

        if photo_url:
            existing_pois[key] = photo_url
            fetched += 1
            print(f"  FOUND: {photo_url[:80]}...")
        else:
            # Use empty string for items that truly can't be found
            existing_pois[key] = ""
            not_found += 1
            print(f"  NOT FOUND (set empty)")

    # Step 6: Add missing city cover images
    print()
    print("=" * 60)
    print("ADDING MISSING CITY COVER IMAGES")
    print("=" * 60)

    # Collect all unique cities from the trip data
    trip_cities = set()
    for poi in unique_pois:
        city = get_city_for_search(poi["city"])
        if city:
            trip_cities.add(city)

    # Check for Tianjin (mentioned as optional day trip)
    trip_cities.add("Tianjin")

    missing_cities = trip_cities - set(city_covers.keys())
    print(f"Cities in trip data: {sorted(trip_cities)}")
    print(f"Cities with covers: {sorted(city_covers.keys())}")
    print(f"Missing city covers: {sorted(missing_cities)}")

    for city in sorted(missing_cities):
        city_cn = get_city_chinese(city)
        print(f"\n[CITY] {city} ({city_cn})")
        search_term = f"{city_cn} 景区"
        print(f"  Search: '{search_term}'")
        time.sleep(DELAY_SECONDS)
        photo_url = gaode_search(search_term, city=city_cn)
        api_calls += 1

        if photo_url:
            city_covers[city] = photo_url
            print(f"  FOUND: {photo_url[:80]}...")
        else:
            # Try broader search
            print(f"  Search 2: '{city_cn}'")
            time.sleep(DELAY_SECONDS)
            photo_url = gaode_search(city_cn)
            api_calls += 1
            if photo_url:
                city_covers[city] = photo_url
                print(f"  FOUND: {photo_url[:80]}...")
            else:
                print(f"  NOT FOUND")

    # Step 7: Save updated images.json
    images["pois"] = existing_pois
    images["city_covers"] = city_covers

    with open(images_path, "w", encoding="utf-8") as f:
        json.dump(images, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total API calls made: {api_calls}")
    print(f"POIs fetched successfully: {fetched}")
    print(f"POIs not found: {not_found}")
    print(f"POIs fixed (wrong images): {len(FIX_POIS)}")
    print(f"Home activities updated: {len(HOME_ACTIVITIES)}")
    print(f"City covers added: {len(missing_cities)}")
    print(f"Total POI entries now: {len(existing_pois)}")
    print(f"Total city covers now: {len(city_covers)}")
    print(f"\nSaved to: {images_path}")


if __name__ == "__main__":
    main()
