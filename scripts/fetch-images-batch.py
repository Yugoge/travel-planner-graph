#!/usr/bin/env python3
"""
Batch image fetcher using skill scripts directly.
More reliable than MCP Client for large batch operations.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


class BatchImageFetcher:
    """Fetch images using skill scripts in small batches"""

    def __init__(self, destination_slug: str):
        self.destination_slug = destination_slug
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data" / destination_slug
        self.cache_file = self.data_dir / "images.json"
        self.venv_python = self._find_venv_python()
        self.force_refresh = False  # Set to True to ignore cache and re-fetch all

        # Load config from requirements-skeleton.json
        self.config = self._load_config()

        # Load cache
        self.cache = self._load_cache()

    def _find_venv_python(self) -> str:
        """Find Python in venv or fallback to system python3"""
        candidates = [
            self.base_dir / ".venv/bin/python3",
            Path.home() / ".claude/venv/bin/python3",
            Path("/usr/bin/python3"),
        ]
        for p in candidates:
            if p.exists():
                return str(p)
        return "python3"

    def _load_config(self) -> dict:
        """Load trip config from requirements-skeleton.json"""
        config_path = self.data_dir / "requirements-skeleton.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("trip_summary", {})
        return {}

    def _load_cache(self):
        """Load existing cache or create new"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        return {
            "destination": self.destination_slug,
            "city_covers": {},
            "pois": {},
            "fallback_unsplash": {
                "meal": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=300&h=200&fit=crop",
                "attraction": "https://images.unsplash.com/photo-1548013146-72479768bada?w=400&h=300&fit=crop",
                "accommodation": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=400&h=300&fit=crop",
                "entertainment": "https://images.unsplash.com/photo-1499364615650-ec38552f4f34?w=400&h=300&fit=crop"
            }
        }

    def _save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def fetch_city_photo_google(self, city_name: str) -> Optional[str]:
        """Fetch city photo using Google Maps Place Details API

        Root cause fix: Place Search returns place_id but not photos.
        Need to call Place Details API with fields=photos to get photo_reference.
        Follows same pattern as fetch_poi_photo_google() (lines 93-161).
        """
        import requests

        # Load Google Maps API key from environment
        google_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if not google_api_key:
            return None

        # Disable proxy for Google Maps API (proxy blocks it)
        proxies = {
            "http": None,
            "https": None
        }

        try:
            # Step 1: Search for city to get place_id
            script_path = self.base_dir / ".claude/skills/google-maps/scripts/places.py"
            result = subprocess.run(
                [self.venv_python, str(script_path), city_name, "1"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=script_path.parent
            )

            if result.returncode != 0:
                return None

            # Parse JSON from stderr to get place_id
            data = json.loads(result.stderr)
            if not data.get("results", {}).get("places"):
                return None

            place = data["results"]["places"][0]
            place_id = place.get("place_id")
            if not place_id:
                return None

            # Step 2: Get place details with photos field
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": place_id,
                "fields": "photos",
                "key": google_api_key
            }

            details_response = requests.get(details_url, params=details_params, timeout=10, proxies=proxies)
            details_data = details_response.json()

            if details_data.get("status") != "OK":
                return None

            # Extract photo reference
            photos = details_data.get("result", {}).get("photos", [])
            if not photos:
                return None

            photo_reference = photos[0].get("photo_reference")
            if not photo_reference:
                return None

            # Step 3: Construct photo URL
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={google_api_key}"

            return photo_url

        except Exception as e:
            print(f"  Google Maps error for {city_name}: {e}")
            return None

    def fetch_poi_photo_google(self, poi_name: str, city: str) -> Optional[str]:
        """Fetch POI photo using Google Maps Place Details API (for Hong Kong/Macau)

        User principle: Hong Kong/Macau use English names with Google Maps
        Uses direct API call to get photo reference, then constructs photo URL
        """
        import requests

        # Load Google Maps API key from environment
        google_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if not google_api_key:
            return None

        # Disable proxy for Google Maps API (proxy blocks it)
        proxies = {
            "http": None,
            "https": None
        }

        try:
            # Step 1: Search for place to get place_id
            search_query = f"{poi_name} {city}"
            search_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            search_params = {
                "input": search_query,
                "inputtype": "textquery",
                "fields": "place_id,name",
                "key": google_api_key
            }

            search_response = requests.get(search_url, params=search_params, timeout=10, proxies=proxies)
            search_data = search_response.json()

            if search_data.get("status") != "OK" or not search_data.get("candidates"):
                return None

            place_id = search_data["candidates"][0]["place_id"]

            # Step 2: Get place details with photos field
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": place_id,
                "fields": "photos",
                "key": google_api_key
            }

            details_response = requests.get(details_url, params=details_params, timeout=10, proxies=proxies)
            details_data = details_response.json()

            if details_data.get("status") != "OK":
                return None

            # Extract photo reference
            photos = details_data.get("result", {}).get("photos", [])
            if not photos:
                return None

            photo_reference = photos[0].get("photo_reference")
            if not photo_reference:
                return None

            # Step 3: Construct photo URL
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={google_api_key}"

            return photo_url

        except Exception as e:
            print(f"  Google Maps error for {poi_name}: {e}")
            return None

    def _gaode_search(self, search_name: str, city: str, typecodes: str) -> Optional[str]:
        """Execute a single Gaode POI search and return photo URL if found"""
        try:
            script_path = self.base_dir / ".claude/skills/gaode-maps/scripts/poi_search.py"
            result = subprocess.run(
                [self.venv_python, str(script_path), "keyword", search_name, city, typecodes],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=script_path.parent
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            if data.get("pois") and len(data["pois"]) > 0:
                poi = data["pois"][0]
                photos = poi.get("photos", {})
                url = photos.get("url")
                if url and url.startswith("http"):
                    return url
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

        return None

    def fetch_poi_photo_gaode(self, poi_name: str, city: str, name_local: str = None) -> Optional[str]:
        """Fetch POI photo using Gaode Maps skill script

        Root cause fix (commit 8f2bddd): Use name_local for native-language searches
        User principle: 搜索哪一国景点就用哪一国自己的语言
        """
        search_name = name_local if name_local else poi_name
        typecodes = "餐饮服务|风景名胜|购物服务|生活服务|体育休闲服务|住宿服务|科教文化服务"
        return self._gaode_search(search_name, city, typecodes)

    def fetch_cities(self, limit: int = 5):
        """Fetch city cover photos (limited batch)"""
        print(f"\n🏙️  Fetching city covers (max {limit})...")

        # Get unique cities from skeleton
        skeleton_path = self.data_dir / "plan-skeleton.json"
        if not skeleton_path.exists():
            return

        with open(skeleton_path, 'r', encoding='utf-8') as f:
            skeleton = json.load(f)

        cities = set()
        for day in skeleton.get("days", []):
            loc = day.get("location")
            if loc:
                cities.add(loc)

        fetched = 0
        for city in list(cities)[:limit]:
            if city in self.cache["city_covers"] and not self.force_refresh:
                print(f"  ✓ {city} (cached)")
                continue

            print(f"  Fetching {city}...", end=" ")
            photo_url = self.fetch_city_photo_google(city)

            if photo_url:
                self.cache["city_covers"][city] = photo_url
                self._save_cache()
                print("✓")
                fetched += 1
            else:
                print("✗")

        print(f"  Total fetched: {fetched}/{limit}")

    def _is_hong_kong_macau(self, location: str) -> bool:
        """Detect if location is Hong Kong or Macau (use Google Maps)"""
        location_lower = location.lower()
        return "hong kong" in location_lower or "hongkong" in location_lower or \
               "macau" in location_lower or "macao" in location_lower or \
               "香港" in location or "澳门" in location

    def _extract_chinese_name(self, name: str) -> str:
        """Extract Chinese name from bilingual format

        Root cause fix (Issue #3): Agent outputs use bilingual format in single field.
        Gaode Maps requires Chinese names for accurate mainland China POI search.

        Handles two formats:
        - Format 1 (attractions): 'English Name (中文名)' → extract from parentheses
        - Format 2 (entertainment): '中文名 (English Name)' → extract before parentheses

        Also handles trailing text like " - Optional" after parentheses.

        Args:
            name: POI name, possibly bilingual format or plain name

        Returns:
            Chinese text if found, otherwise empty string

        Examples:
            'Raffles City Observation Deck (来福士观景台)' -> '来福士观景台'
            'Liziba Station (李子坝单轨穿楼) - Optional' -> '李子坝单轨穿楼'
            '静·serene SPA 泰式按摩足疗 (Serene Thai SPA)' -> '静·serene SPA 泰式按摩足疗'
            'Some Place' -> ''
        """
        import re

        # Find FIRST parenthesized content (handles multiple parentheses)
        match = re.search(r'^(.+?)\s*\(([^)]+)\)', name)
        if not match:
            return ""

        before_paren = match.group(1).strip()
        inside_paren = match.group(2).strip()

        # Detect if text before parentheses contains Chinese characters
        # Chinese Unicode ranges: \u4e00-\u9fff (CJK Unified Ideographs)
        has_chinese_before = bool(re.search(r'[\u4e00-\u9fff]', before_paren))

        if has_chinese_before:
            # Format 2: Chinese (English) - entertainment style
            return before_paren
        else:
            # Format 1: English (Chinese) - attractions style
            return inside_paren

    def fetch_pois(self, limit: int = 10):
        """Fetch POI photos from all agent files (limited batch)

        Root cause fix (commit 8f2bddd): Use standardized name_local field for native-language search
        - Mainland China → use name_local (Chinese) + Gaode Maps
        - Hong Kong/Macau → use name_base (English) + Google Maps
        - Hotels → fetch images for accommodation
        - Backward compatible: Falls back to name_chinese or _extract_chinese_name() for old JSON

        Supports both days format (itinerary) and cities format (bucket list).
        """
        print(f"\n📍 Fetching POI photos (max {limit})...")

        # Collect POIs from all agent files with metadata
        pois = []

        # Agent files to read: attractions, meals, accommodation, entertainment
        agent_files = [
            ("attractions.json", "attractions", "attraction"),
            ("meals.json", "meals", "meal"),
            ("accommodation.json", "accommodation", "accommodation"),
            ("entertainment.json", "entertainment", "entertainment")
        ]

        for filename, field_name, poi_type in agent_files:
            agent_path = self.data_dir / filename
            if not agent_path.exists():
                continue

            with open(agent_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract POIs from days structure (itinerary format)
            days_data = data.get("data", {}).get("days", [])
            # OR cities structure (bucket list format)
            cities_data = data.get("cities", [])

            # Process days format
            for day in days_data:
                location = day.get("location", "")

                if field_name == "attractions":
                    # Attractions: list of items
                    for item in day.get("attractions", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_chinese_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "type": poi_type
                            })

                elif field_name == "meals":
                    # Meals: breakfast/lunch/dinner dict
                    for meal_type in ["breakfast", "lunch", "dinner"]:
                        meal = day.get(meal_type)
                        if meal and isinstance(meal, dict):
                            # New format: name_base and name_local
                            name_base = meal.get("name_base", "")
                            name_local = meal.get("name_local", "")

                            # Backward compatibility: fallback to old fields
                            if not name_base:
                                name_base = meal.get("name", "")
                            if not name_local:
                                name_local = meal.get("name_chinese", "") or self._extract_chinese_name(name_base)

                            if name_base:
                                pois.append({
                                    "name": name_base,
                                    "name_local": name_local,
                                    "city": location,
                                    "type": poi_type
                                })

                elif field_name == "accommodation":
                    # Accommodation: single dict
                    acc = day.get("accommodation")
                    if acc and isinstance(acc, dict):
                        # New format: name_base and name_local
                        name_base = acc.get("name_base", "")
                        name_local = acc.get("name_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = acc.get("name", "")
                        if not name_local:
                            name_local = acc.get("name_chinese", acc.get("name_cn", "")) or self._extract_chinese_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "type": poi_type
                            })

                elif field_name == "entertainment":
                    # Entertainment: list of items
                    for item in day.get("entertainment", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_chinese_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "type": poi_type
                            })

            # Process cities format (bucket list)
            for city in cities_data:
                location = city.get("city", "")

                if field_name == "attractions":
                    # Attractions: list of items
                    for item in city.get("attractions", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_chinese_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "type": poi_type
                            })

                elif field_name == "meals":
                    # Meals: list of items
                    for item in city.get("meals", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_chinese_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "type": poi_type
                            })

                elif field_name == "accommodation":
                    # Accommodation: list of items
                    for item in city.get("accommodation", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", item.get("name_cn", "")) or self._extract_chinese_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "type": poi_type
                            })

                elif field_name == "entertainment":
                    # Entertainment: list of items
                    for item in city.get("entertainment", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_chinese_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "type": poi_type
                            })

        print(f"  Found {len(pois)} POIs across all agent files")

        fetched = 0
        for poi in pois[:limit]:
            is_hk_macau = self._is_hong_kong_macau(poi['city'])

            # Determine cache key and search method based on location
            if is_hk_macau:
                cache_key = f"google_{poi['name']}"
                service = "Google"
            else:
                cache_key = f"gaode_{poi['name']}"
                service = "Gaode"

            if cache_key in self.cache["pois"] and not self.force_refresh:
                print(f"  ✓ {poi['name']} ({poi['type']}, cached, {service})")
                continue

            print(f"  Fetching {poi['name']} ({poi['type']}, {service})...", end=" ")

            # Use appropriate search method
            if is_hk_macau:
                # Use Google Maps for Hong Kong/Macau with English name
                photo_url = self.fetch_poi_photo_google(poi['name'], poi['city'])
            else:
                # Use Gaode Maps for mainland China with native language name
                photo_url = self.fetch_poi_photo_gaode(
                    poi['name'],
                    poi['city'],
                    name_local=poi.get('name_local')
                )

            if photo_url:
                self.cache["pois"][cache_key] = photo_url
                self._save_cache()
                print("✓")
                fetched += 1
            else:
                print("✗")

        print(f"  Total fetched: {fetched}/{limit}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch-images-batch.py <destination-slug> [city_limit] [poi_limit]")
        print("Example: python3 fetch-images-batch.py china-exchange-bucket-list-2026 5 10")
        sys.exit(1)

    import argparse

    parser = argparse.ArgumentParser(description='Batch fetch images from Google Maps and Gaode Maps')
    parser.add_argument('destination', help='Destination slug (e.g., china-feb-15-mar-7-2026-20260202-195429)')
    parser.add_argument('city_limit', nargs='?', type=int, default=5, help='Max cities to fetch (default: 5)')
    parser.add_argument('poi_limit', nargs='?', type=int, default=10, help='Max POIs to fetch (default: 10)')
    parser.add_argument('--force', action='store_true', help='Force re-fetch all images (ignore cache)')

    args = parser.parse_args()

    destination = args.destination
    city_limit = args.city_limit
    poi_limit = args.poi_limit
    force_refresh = args.force

    print("="*60)
    print(f"Batch Image Fetcher - {destination}")
    if force_refresh:
        print("⚡ FORCE MODE: Re-fetching all images (ignoring cache)")
    print("="*60)

    fetcher = BatchImageFetcher(destination)
    fetcher.force_refresh = force_refresh
    fetcher.fetch_cities(city_limit)
    fetcher.fetch_pois(poi_limit)

    print("\n" + "="*60)
    print(f"✅ Batch complete!")
    print(f"  City covers: {len(fetcher.cache['city_covers'])}")
    print(f"  POI photos: {len(fetcher.cache['pois'])}")
    print(f"  Cache: {fetcher.cache_file}")
    print("="*60)


if __name__ == "__main__":
    main()
