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
            self.base_dir / "venv/bin/python3",
            self.base_dir / ".venv/bin/python3",
            self.base_dir / ".claude/venv/bin/python3",
            Path.home() / ".claude/venv/bin/python3",
            Path("/usr/bin/python3"),
        ]
        for p in candidates:
            if p.exists():
                return str(p)
        return "python3"

    # Cache: city name → ISO2 country code
    _country_cache: dict = {}

    @staticmethod
    def _country_for_coord(lng: float, lat: float) -> str:
        """Return ISO2 country code for a coordinate using geopip.

        Offline reverse geocode via embedded Natural Earth polygons.
        No API calls, no hardcoded lists, no network needed.
        """
        try:
            import geopip
            result = geopip.search(lng=lng, lat=lat)
            return result.get("ISO2", "") if result else ""
        except ImportError:
            return ""

    def _resolve_city_coord(self, city: str) -> tuple:
        """Get (lng, lat) for a city from skeleton POI data or Gaode geocoding."""
        # 1. Try to find a coordinate from any POI in this city's day
        skeleton_path = self.data_dir / "plan-skeleton.json"
        if skeleton_path.exists():
            with open(skeleton_path, 'r', encoding='utf-8') as f:
                skeleton = json.load(f)

            # Find day numbers for this city
            day_nums = [
                d["day"] for d in skeleton.get("days", [])
                if d.get("location", "").lower().strip() == city.lower().strip()
            ]

            if day_nums:
                for agent_file in ["attractions.json", "meals.json", "entertainment.json"]:
                    agent_path = self.data_dir / agent_file
                    if not agent_path.exists():
                        continue
                    with open(agent_path, 'r', encoding='utf-8') as f:
                        agent_data = json.load(f)
                    for d in agent_data.get("data", agent_data).get("days", []):
                        if d.get("day") not in day_nums:
                            continue
                        # Check list-type items
                        for key in ["attractions", "entertainment"]:
                            for item in d.get(key, []):
                                c = item.get("coordinates", {})
                                if c.get("lat") and c.get("lng"):
                                    return (float(c["lng"]), float(c["lat"]))
                        # Check meal items
                        for mk in ["breakfast", "lunch", "dinner"]:
                            meal = d.get(mk, {})
                            if isinstance(meal, dict):
                                c = meal.get("coordinates", {})
                                if c.get("lat") and c.get("lng"):
                                    return (float(c["lng"]), float(c["lat"]))

            # Check bucket-list cities
            for city_data in skeleton.get("cities", []):
                if city_data.get("city", "").lower() == city.lower():
                    c = city_data.get("coordinates", {})
                    if c.get("lat") and c.get("lng"):
                        return (float(c["lng"]), float(c["lat"]))

        # 2. Fallback: Gaode geocoding (single API call)
        import urllib.request
        import urllib.parse
        gaode_key = os.environ.get("GAODE_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")
        params = urllib.parse.urlencode({"key": gaode_key, "address": city, "output": "json"})
        try:
            url = f"https://restapi.amap.com/v3/geocode/geo?{params}"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
            if data.get("geocodes"):
                loc = data["geocodes"][0].get("location", "")
                if "," in loc:
                    lng_s, lat_s = loc.split(",")
                    return (float(lng_s), float(lat_s))
        except Exception:
            pass

        return (0.0, 0.0)

    def _map_service_for(self, city: str) -> str:
        """Return 'gaode' or 'google' based on coordinate-level country detection.

        Universal rule — no config, no hardcoded city lists:
          Mainland China (ISO2=CN) → Gaode (高德)
          Everywhere else (HK, MO, TW, JP, FR, ...) → Google

        Detection: city name → coordinate (from data or geocoding) → geopip → ISO2.
        Results cached per city per session.
        """
        cache_key = city.strip().lower()
        if cache_key in self._country_cache:
            return "gaode" if self._country_cache[cache_key] == "CN" else "google"

        lng, lat = self._resolve_city_coord(city)
        if lng == 0.0 and lat == 0.0:
            self._country_cache[cache_key] = ""
            return "google"

        iso2 = self._country_for_coord(lng, lat)
        self._country_cache[cache_key] = iso2
        return "gaode" if iso2 == "CN" else "google"

    def _load_config(self) -> dict:
        """Load trip config from requirements-skeleton.json"""
        config_path = self.data_dir / "requirements-skeleton.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("trip_summary", {})
        return {}

    def _load_fallback_images(self) -> dict:
        """Load fallback image URLs from config."""
        config_path = self.base_dir / "config" / "fallback-images.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f).get("fallback_unsplash", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "meal": "", "attraction": "",
                "accommodation": "", "entertainment": ""
            }

    def _load_cache(self):
        """Load existing cache or create new"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        return {
            "destination": self.destination_slug,
            "city_covers": {},
            "pois": {},
            "fallback_unsplash": self._load_fallback_images()
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

    def _gaode_search(self, search_name: str, city: str, location_local: str = None) -> Optional[str]:
        """Execute a Gaode POI search and return photo URL if found.

        Fallback strategy:
        1. Try exact name search
        2. Try simplified keywords (remove trailing descriptive words)
        3. Try location/address search if provided

        Example: "外滩夜景散步" → "外滩夜景" → "外滩" → "上海市黄浦区中山东一路"
        """
        import re

        # Try exact name search with keyword fallbacks
        for search_term in self._get_fallback_search_terms(search_name):
            try:
                script_path = self.base_dir / ".claude/skills/gaode-maps/scripts/poi_search.py"
                result = subprocess.run(
                    [self.venv_python, str(script_path), "keyword", search_term, city],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=script_path.parent
                )

                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data.get("pois") and len(data["pois"]) > 0:
                        poi = data["pois"][0]
                        photos = poi.get("photos", {})
                        url = photos.get("url")
                        if url and url.startswith("http"):
                            # Ensure HTTPS (Gaode supports it; avoids mixed-content on HTTPS pages)
                            return url.replace("http://", "https://", 1)
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue

        # FINAL FALLBACK: Try location/address search
        if location_local:
            try:
                script_path = self.base_dir / ".claude/skills/gaode-maps/scripts/poi_search.py"
                result = subprocess.run(
                    [self.venv_python, str(script_path), "keyword", location_local, city],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=script_path.parent
                )

                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data.get("pois") and len(data["pois"]) > 0:
                        poi = data["pois"][0]
                        photos = poi.get("photos", {})
                        url = photos.get("url")
                        if url and url.startswith("http"):
                            return url.replace("http://", "https://", 1)
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass

        return None

    def _get_fallback_search_terms(self, search_name: str) -> list[str]:
        """Generate fallback search terms for POI photo search.

        Strategy: progressively simplify the search term:
        1. Original term (e.g., "外滩夜景散步")
        2. Remove trailing descriptive words (e.g., "外滩夜景")
        3. Core landmark only (e.g., "外滩")
        """
        terms = [search_name]

        # Remove common trailing descriptive phrases
        for suffix in ["散步", "游览", "观光", "体验", "之旅", "路线", "路径", " walkthrough", " tour", " experience"]:
            if search_name.endswith(suffix):
                simplified = search_name[:-len(suffix)].strip()
                if simplified and len(simplified) >= 2:
                    terms.append(simplified)
                break

        # For Chinese, try using just the first 2-4 characters (core name)
        if len(search_name) >= 4:
            # Try progressively shorter versions
            for length in [len(search_name) - 2, len(search_name) - 4, 4, 3, 2]:
                if length >= 2 and length < len(search_name):
                    core = search_name[:length]
                    if core not in terms:
                        terms.append(core)

        return terms

    def fetch_poi_photo(self, poi_name: str, city: str, name_local: str = None, location_local: str = None) -> Optional[str]:
        """Fetch POI photo using map service determined by city location.

        Mainland China → Gaode Maps (高德)
        Everywhere else → Google Maps
        Uses name_local for search (native language), falls back to poi_name.
        FINAL FALLBACK: Uses location_local (address) for search if name fails.
        """
        search_name = name_local if name_local else poi_name
        service = self._map_service_for(city)

        if service == "gaode":
            return self._gaode_search(search_name, city, location_local=location_local)
        else:
            return self.fetch_poi_photo_google(search_name, city)

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

            service = self._map_service_for(city)
            print(f"  Fetching {city} ({service})...", end=" ")
            if service == "gaode":
                # Search for city landmarks/skyline instead of just "景点" (which returns Disney for Shanghai)
                photo_url = self._gaode_search(f"{city} 地标", city)
            else:
                photo_url = self.fetch_city_photo_google(city)

            if photo_url:
                self.cache["city_covers"][city] = photo_url
                self._save_cache()
                print("✓")
                fetched += 1
            else:
                print("✗")

        print(f"  Total fetched: {fetched}/{limit}")

    @staticmethod
    def _parse_day_filter(day_filter: str) -> set:
        """Parse day filter string into a set of day numbers.

        Supports formats:
        - "1" → Day 1 only
        - "1-5" → Days 1, 2, 3, 4, 5
        - "3,5,7" → Days 3, 5, 7
        - "1-3,5,7-9" → Days 1, 2, 3, 5, 7, 8, 9

        Args:
            day_filter: Filter string (e.g., "1", "1-5", "3,5,7")

        Returns:
            Set of day numbers to include
        """
        days = set()

        # Split by comma first (for "1-3,5,7-9" format)
        parts = day_filter.split(",")

        for part in parts:
            part = part.strip()

            if "-" in part:
                # Range format: "1-5"
                start, end = part.split("-")
                try:
                    start_num = int(start.strip())
                    end_num = int(end.strip())
                    days.update(range(start_num, end_num + 1))
                except ValueError:
                    continue
            else:
                # Single day: "1"
                try:
                    days.add(int(part))
                except ValueError:
                    continue

        return days

    def _extract_local_name(self, name: str) -> str:
        """Extract non-Latin local name from bilingual format (backward compat for old JSON).

        Handles two formats:
        - 'English Name (本地名)' → extract from parentheses
        - '本地名 (English Name)' → extract before parentheses

        Args:
            name: POI name, possibly bilingual format

        Returns:
            Local name if found, otherwise empty string

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

        # Detect if text before parentheses contains CJK characters
        # Covers Chinese, Japanese kanji, Korean hanja
        has_cjk_before = bool(re.search(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]', before_paren))

        if has_cjk_before:
            # Format: LocalName (English)
            return before_paren
        else:
            # Format: English (LocalName)
            return inside_paren

    def fetch_pois(self, limit: int = 10, day_filter: str = None):
        """Fetch POI photos from all agent files (limited batch).

        Map service auto-detected per city via coordinates (CN → Gaode, else → Google).
        Searches with name_local (native language) for accurate results.
        Backward compatible: falls back to _extract_local_name() for old JSON format.

        Args:
            limit: Maximum number of POIs to fetch
            day_filter: Optional day filter (e.g., "1", "1-5", "3,5,7")
        """
        print(f"\n📍 Fetching POI photos (max {limit})...")
        if day_filter:
            print(f"  Day filter: {day_filter}")

        # Parse day filter
        filtered_days = self._parse_day_filter(day_filter) if day_filter else None

        # Collect POIs from all agent files with metadata
        pois = []

        # Agent files to read: attractions, meals, accommodation, entertainment
        agent_files = [
            ("attractions.json", "attractions", "attraction"),
            ("meals.json", "meals", "meal"),
            ("accommodation.json", "accommodation", "accommodation"),
            ("entertainment.json", "entertainment", "entertainment"),
            ("shopping.json", "shopping", "shopping"),
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
                day_num = day.get("day", 0)

                # Skip if day filter is set and this day is not in filter
                if filtered_days is not None and day_num not in filtered_days:
                    continue

                location = day.get("location", "")

                if field_name == "attractions":
                    # Attractions: list of items
                    for item in day.get("attractions", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")
                        location_base = item.get("location_base", "")
                        location_local = item.get("location_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
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
                            location_base = meal.get("location_base", "")
                            location_local = meal.get("location_local", "")

                            # Backward compatibility: fallback to old fields
                            if not name_base:
                                name_base = meal.get("name", "")
                            if not name_local:
                                name_local = meal.get("name_chinese", "") or self._extract_local_name(name_base)

                            if name_base:
                                pois.append({
                                    "name": name_base,
                                    "name_local": name_local,
                                    "city": location,
                                    "location_base": location_base,
                                    "location_local": location_local,
                                    "type": poi_type
                                })

                elif field_name == "accommodation":
                    # Accommodation: single dict
                    acc = day.get("accommodation")
                    if acc and isinstance(acc, dict):
                        # New format: name_base and name_local
                        name_base = acc.get("name_base", "")
                        name_local = acc.get("name_local", "")
                        location_base = acc.get("location_base", "")
                        location_local = acc.get("location_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = acc.get("name", "")
                        if not name_local:
                            name_local = acc.get("name_chinese", acc.get("name_cn", "")) or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
                                "type": poi_type
                            })

                elif field_name == "entertainment":
                    # Entertainment: list of items
                    for item in day.get("entertainment", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")
                        location_base = item.get("location_base", "")
                        location_local = item.get("location_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
                                "type": poi_type
                            })

                elif field_name == "shopping":
                    # Shopping: list of items
                    for item in day.get("shopping", []):
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")
                        location_base = item.get("location_base", "")
                        location_local = item.get("location_local", "")

                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
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
                        location_base = item.get("location_base", "")
                        location_local = item.get("location_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
                                "type": poi_type
                            })

                elif field_name == "meals":
                    # Meals: list of items
                    for item in city.get("meals", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")
                        location_base = item.get("location_base", "")
                        location_local = item.get("location_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
                                "type": poi_type
                            })

                elif field_name == "accommodation":
                    # Accommodation: list of items
                    for item in city.get("accommodation", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")
                        location_base = item.get("location_base", "")
                        location_local = item.get("location_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", item.get("name_cn", "")) or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
                                "type": poi_type
                            })

                elif field_name == "entertainment":
                    # Entertainment: list of items
                    for item in city.get("entertainment", []):
                        # New format: name_base and name_local
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")
                        location_base = item.get("location_base", "")
                        location_local = item.get("location_local", "")

                        # Backward compatibility: fallback to old fields
                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
                                "type": poi_type
                            })

                elif field_name == "shopping":
                    for item in city.get("shopping", []):
                        name_base = item.get("name_base", "")
                        name_local = item.get("name_local", "")
                        location_base = item.get("location_base", "")
                        location_local = item.get("location_local", "")

                        if not name_base:
                            name_base = item.get("name", "")
                        if not name_local:
                            name_local = item.get("name_chinese", "") or self._extract_local_name(name_base)

                        if name_base:
                            pois.append({
                                "name": name_base,
                                "name_local": name_local,
                                "city": location,
                                "location_base": location_base,
                                "location_local": location_local,
                                "type": poi_type
                            })

        print(f"  Found {len(pois)} POIs across all agent files")

        fetched = 0
        for poi in pois[:limit]:
            service = self._map_service_for(poi['city'])
            cache_key = f"{service}_{poi['name']}"

            if cache_key in self.cache["pois"] and not self.force_refresh:
                print(f"  ✓ {poi['name']} ({poi['type']}, cached)")
                continue

            print(f"  Fetching {poi['name']} ({poi['type']}, {service})...", end=" ")

            photo_url = self.fetch_poi_photo(
                poi['name'],
                poi['city'],
                name_local=poi.get('name_local'),
                location_local=poi.get('location_local')
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
        print("Usage: python3 fetch-images-batch.py <destination-slug> [city_limit] [poi_limit] [--day FILTER] [--force]")
        print("Examples:")
        print("  python3 fetch-images-batch.py china-exchange-bucket-list-2026 5 10")
        print("  python3 fetch-images-batch.py china-exchange-bucket-list-2026 100 10 --day 1")
        print("  python3 fetch-images-batch.py china-exchange-bucket-list-2026 100 10 --day 1-5")
        print("  python3 fetch-images-batch.py china-exchange-bucket-list-2026 100 10 --day 1,3,5")
        print("")
        print("Day filter formats:")
        print("  --day 1        # Day 1 only")
        print("  --day 1-5      # Days 1 through 5")
        print("  --day 1,3,5    # Days 1, 3, and 5")
        print("  --day 1-3,5,7-9  # Days 1-3, 5, 7-9")
        sys.exit(1)

    import argparse

    parser = argparse.ArgumentParser(
        description='Batch fetch POI images (auto-detects Gaode/Google by city coordinates)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Day filter examples:
  --day 1          Fetch only Day 1 POIs
  --day 1-5         Fetch Days 1-5 POIs
  --day 1,3,5       Fetch Days 1, 3, and 5 POIs
  --day 1-3,5,7-9   Fetch Days 1-3, 5, 7-9 POIs
        '''
    )
    parser.add_argument('destination', help='Destination slug (e.g., china-feb-15-mar-7-2026-20260202-195429)')
    parser.add_argument('city_limit', nargs='?', type=int, default=5, help='Max cities to fetch (default: 5)')
    parser.add_argument('poi_limit', nargs='?', type=int, default=10, help='Max POIs to fetch (default: 10)')
    parser.add_argument('--day', dest='day_filter', type=str, help='Filter by day number(s) (e.g., "1", "1-5", "3,5,7")')
    parser.add_argument('--force', action='store_true', help='Force re-fetch all images (ignore cache)')

    args = parser.parse_args()

    destination = args.destination
    city_limit = args.city_limit
    poi_limit = args.poi_limit
    day_filter = args.day_filter
    force_refresh = args.force

    print("="*60)
    print(f"Batch Image Fetcher - {destination}")
    if force_refresh:
        print("⚡ FORCE MODE: Re-fetching all images (ignoring cache)")
    if day_filter:
        print(f"📅 DAY FILTER: {day_filter}")
    print("="*60)

    fetcher = BatchImageFetcher(destination)
    fetcher.force_refresh = force_refresh
    fetcher.fetch_cities(city_limit)
    fetcher.fetch_pois(poi_limit, day_filter=day_filter)

    print("\n" + "="*60)
    print(f"✅ Batch complete!")
    print(f"  City covers: {len(fetcher.cache['city_covers'])}")
    print(f"  POI photos: {len(fetcher.cache['pois'])}")
    print(f"  Cache: {fetcher.cache_file}")
    print("="*60)


if __name__ == "__main__":
    main()
