#!/usr/bin/env python3
"""
Image Fetcher Module
Fetches real photos from Google Maps and Gaode Maps APIs for travel plan POIs and cities.
Replaces hardcoded Unsplash placeholders with actual location photos.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from project root .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))


class ImageFetcher:
    """Fetch and cache images from Google Maps and Gaode Maps APIs"""

    # Mainland China cities (use Gaode Maps first)
    CHINA_CITIES = {
        "beijing", "shanghai", "guangzhou", "shenzhen", "chengdu", "chongqing",
        "tianjin", "wuhan", "xian", "hangzhou", "nanjing", "suzhou", "zhengzhou",
        "changsha", "shenyang", "qingdao", "xiamen", "harbin", "kunming", "dalian",
        "济南", "青岛", "郑州", "石家庄", "太原", "呼和浩特", "沈阳", "长春", "哈尔滨",
        "南京", "杭州", "合肥", "福州", "南昌", "武汉", "长沙", "广州", "南宁",
        "海口", "成都", "贵阳", "昆明", "拉萨", "西安", "兰州", "西宁", "银川",
        "乌鲁木齐", "北京", "天津", "上海", "重庆", "深圳", "厦门", "大连", "苏州"
    }

    def __init__(self, destination_slug: str, data_dir: Optional[Path] = None):
        """
        Initialize image fetcher.

        Args:
            destination_slug: Destination identifier (e.g., 'beijing-exchange-bucket-list')
            data_dir: Path to data directory (defaults to data/{destination_slug})
        """
        self.destination_slug = destination_slug
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = data_dir or (self.base_dir / "data" / destination_slug)
        self.cache_file = self.data_dir / "images.json"

        # Image cache structure
        self.cache = self._load_cache()

    def _is_china_location(self, location: str) -> bool:
        """
        Check if location is in mainland China.

        Args:
            location: City or location name

        Returns:
            True if in mainland China, False otherwise
        """
        if not location:
            return False

        location_lower = location.lower().strip()

        # Check against known China cities
        for city in self.CHINA_CITIES:
            if city in location_lower:
                return True

        return False

    def _load_cache(self) -> Dict[str, Any]:
        """Load existing image cache or create new structure"""
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

    def _save_cache(self) -> None:
        """Save image cache to disk"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def fetch_gaode_poi_photos(self, gaode_id: str, poi_name: str) -> Optional[str]:
        """
        Fetch POI photos from Gaode Maps API.

        Args:
            gaode_id: Gaode Maps POI ID
            poi_name: POI name for cache key

        Returns:
            First photo URL or None if unavailable
        """
        # Check cache first
        cache_key = f"gaode_{gaode_id}"
        if cache_key in self.cache["pois"]:
            return self.cache["pois"][cache_key]

        try:
            # Import MCP client
            google_maps_script_dir = self.base_dir / ".claude" / "skills" / "google-maps" / "scripts"
            sys.path.insert(0, str(google_maps_script_dir))
            from mcp_client import MCPClient

            # Fetch POI details from Gaode Maps via MCP
            api_key = os.environ.get("AMAP_MAPS_API_KEY")
            if not api_key:
                print(f"Warning: AMAP_MAPS_API_KEY not set, cannot fetch Gaode photos for {poi_name}")
                return None

            env_vars = {"AMAP_MAPS_API_KEY": api_key}

            with MCPClient("@plugin/amap-maps", env_vars) as client:
                result = client.call_tool("poi_detail", {"id": gaode_id, "extensions": "all"})

                # Parse result
                if isinstance(result, str):
                    result = json.loads(result)

                # Extract photos from result
                if "photos" in result and isinstance(result["photos"], list) and len(result["photos"]) > 0:
                    photo_url = result["photos"][0].get("url")
                    if photo_url:
                        # Cache the result
                        self.cache["pois"][cache_key] = photo_url
                        self._save_cache()
                        return photo_url

        except Exception as e:
            print(f"Error fetching Gaode photos for {poi_name} ({gaode_id}): {e}")

        return None

    def fetch_google_place_photos(
        self,
        place_id: Optional[str] = None,
        place_name: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetch place photos from Google Maps Place Photos API.

        Args:
            place_id: Google Maps Place ID (if known)
            place_name: Place name to search for
            location: Location context for search

        Returns:
            First photo URL or None if unavailable
        """
        # Check cache first
        cache_key = f"google_{place_id or place_name}"
        if cache_key in self.cache["pois"]:
            return self.cache["pois"][cache_key]

        try:
            # Import MCP client
            google_maps_script_dir = self.base_dir / ".claude" / "skills" / "google-maps" / "scripts"
            sys.path.insert(0, str(google_maps_script_dir))
            from mcp_client import MCPClient

            api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
            if not api_key:
                print(f"Warning: GOOGLE_MAPS_API_KEY not set, cannot fetch Google photos for {place_name}")
                return None

            env_vars = {"GOOGLE_MAPS_API_KEY": api_key}

            with MCPClient("@modelcontextprotocol/server-google-maps", env_vars) as client:
                # If place_id not provided, search for place first
                if not place_id and place_name:
                    search_result = client.call_tool("maps_search_places", {
                        "query": f"{place_name} {location or ''}".strip()
                    })

                    if isinstance(search_result, str):
                        search_result = json.loads(search_result)

                    if isinstance(search_result, list) and len(search_result) > 0:
                        place_id = search_result[0].get("place_id")

                if not place_id:
                    return None

                # Get place details with photos
                details_result = client.call_tool("maps_place_details", {"place_id": place_id})

                if isinstance(details_result, str):
                    details_result = json.loads(details_result)

                # Extract first photo reference
                photos = details_result.get("photos", [])
                if photos and len(photos) > 0:
                    photo_reference = photos[0].get("photo_reference")
                    if photo_reference:
                        # Construct photo URL using Google Maps Static API
                        photo_url = (
                            f"https://maps.googleapis.com/maps/api/place/photo"
                            f"?maxwidth=800&photoreference={photo_reference}&key={api_key}"
                        )

                        # Cache the result
                        self.cache["pois"][cache_key] = photo_url
                        self._save_cache()
                        return photo_url

        except Exception as e:
            print(f"Error fetching Google photos for {place_name}: {e}")

        return None

    def fetch_city_cover_image(self, city_name: str) -> Optional[str]:
        """
        Fetch city cover image from Gaode Maps or Google Maps based on location.

        Args:
            city_name: City name (e.g., 'Beijing', 'Harbin', 'Hong Kong')

        Returns:
            City cover photo URL or None
        """
        # Check cache first
        if city_name in self.cache["city_covers"]:
            return self.cache["city_covers"][city_name]

        is_china = self._is_china_location(city_name)
        photo_url = None

        if is_china:
            # China: Try Gaode first, fallback to Google
            photo_url = self._fetch_gaode_city_cover(city_name)
            if not photo_url:
                print(f"Gaode Maps failed for {city_name}, trying Google Maps")
                photo_url = self._fetch_google_city_cover(city_name)
        else:
            # International: Try Google first, fallback to Gaode
            photo_url = self._fetch_google_city_cover(city_name)
            if not photo_url:
                print(f"Google Maps failed for {city_name}, trying Gaode Maps")
                photo_url = self._fetch_gaode_city_cover(city_name)

        if photo_url:
            self.cache["city_covers"][city_name] = photo_url
            self._save_cache()
            return photo_url

        return None

    def _fetch_gaode_city_cover(self, city_name: str) -> Optional[str]:
        """Fetch city cover from Gaode Maps"""
        try:
            google_maps_script_dir = self.base_dir / ".claude" / "skills" / "google-maps" / "scripts"
            sys.path.insert(0, str(google_maps_script_dir))
            from mcp_client import MCPClient

            api_key = os.environ.get("AMAP_MAPS_API_KEY")
            if not api_key:
                return None

            env_vars = {"AMAP_MAPS_API_KEY": api_key}

            with MCPClient("@plugin/amap-maps", env_vars) as client:
                # Search for city POI
                result = client.call_tool("poi_search_keyword", {
                    "keywords": city_name,
                    "city": city_name,
                    "types": "110000",  # Tourist attractions category
                    "offset": 1,
                    "extensions": "all"
                })

                if isinstance(result, str):
                    result = json.loads(result)

                # Get first POI's photos
                if "pois" in result and isinstance(result["pois"], list) and len(result["pois"]) > 0:
                    poi = result["pois"][0]
                    if "photos" in poi and isinstance(poi["photos"], list) and len(poi["photos"]) > 0:
                        return poi["photos"][0].get("url")
        except Exception as e:
            print(f"Gaode Maps city cover error for {city_name}: {e}")

        return None

    def _fetch_google_city_cover(self, city_name: str) -> Optional[str]:
        """Fetch city cover from Google Maps"""
        return self.fetch_google_place_photos(
            place_name=city_name,
            location="China"
        )

    def fetch_all_images(self, parallel: bool = True) -> Dict[str, Any]:
        """
        Fetch all images for the travel plan.

        Args:
            parallel: Use parallel API calls for faster fetching

        Returns:
            Summary of fetched images
        """
        summary = {
            "city_covers_fetched": 0,
            "pois_fetched": 0,
            "errors": []
        }

        # Load agent data files
        agent_files = ["attractions.json", "meals.json", "accommodation.json", "entertainment.json"]
        all_pois = []
        cities = set()

        for filename in agent_files:
            filepath = self.data_dir / filename
            if not filepath.exists():
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract actual data from agent wrapper
            if isinstance(data, dict) and 'data' in data:
                data = data['data']

            # Extract POIs from days structure
            if "days" in data:
                for day in data["days"]:
                    cities.add(day.get("location", ""))

                    # Extract attractions
                    if "attractions" in day:
                        for item in day["attractions"]:
                            all_pois.append({
                                "type": "attraction",
                                "name": item.get("name", ""),
                                "gaode_id": item.get("gaode_id"),
                                "address": item.get("address", ""),
                                "location": item.get("location", "")
                            })

                    # Extract meals
                    for meal_type in ["breakfast", "lunch", "dinner"]:
                        if meal_type in day:
                            item = day[meal_type]
                            all_pois.append({
                                "type": "meal",
                                "name": item.get("name", ""),
                                "gaode_id": item.get("gaode_id"),
                                "address": item.get("address", ""),
                                "location": item.get("location", "")
                            })

                    # Extract entertainment
                    if "entertainment" in day:
                        for item in day["entertainment"]:
                            all_pois.append({
                                "type": "entertainment",
                                "name": item.get("name", ""),
                                "gaode_id": item.get("gaode_id"),
                                "address": item.get("address", ""),
                                "location": item.get("location", "")
                            })

                    # Extract accommodation
                    if "accommodation" in day:
                        item = day["accommodation"]
                        all_pois.append({
                            "type": "accommodation",
                            "name": item.get("name", ""),
                            "gaode_id": item.get("gaode_id"),
                            "address": item.get("address", ""),
                            "location": item.get("location", "")
                        })

        # Fetch city covers
        print(f"\nFetching city cover images for {len(cities)} cities...")
        for city in cities:
            if not city:
                continue

            print(f"  Fetching cover for: {city}")
            photo_url = self.fetch_city_cover_image(city)
            if photo_url:
                summary["city_covers_fetched"] += 1
                print(f"    ✓ Fetched")
            else:
                print(f"    ✗ Failed")

        # Fetch POI photos
        print(f"\nFetching POI photos for {len(all_pois)} POIs...")

        def fetch_poi_photo(poi: Dict[str, Any]) -> Optional[str]:
            """Fetch single POI photo based on location"""
            name = poi.get("name", "Unknown")
            gaode_id = poi.get("gaode_id")
            location = poi.get("location") or poi.get("address", "")

            # Determine if POI is in China
            is_china = self._is_china_location(location)

            if is_china:
                # China: Try Gaode first, fallback to Google
                if gaode_id:
                    photo_url = self.fetch_gaode_poi_photos(gaode_id, name)
                    if photo_url:
                        return photo_url

                # Fallback to Google Maps
                photo_url = self.fetch_google_place_photos(
                    place_name=name,
                    location=location
                )
                return photo_url
            else:
                # International: Try Google first, fallback to Gaode
                photo_url = self.fetch_google_place_photos(
                    place_name=name,
                    location=location
                )
                if photo_url:
                    return photo_url

                # Fallback to Gaode (if has gaode_id)
                if gaode_id:
                    photo_url = self.fetch_gaode_poi_photos(gaode_id, name)
                    return photo_url

                return None

        if parallel:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(fetch_poi_photo, poi): poi for poi in all_pois}
                for future in as_completed(futures):
                    poi = futures[future]
                    try:
                        photo_url = future.result()
                        if photo_url:
                            summary["pois_fetched"] += 1
                            print(f"  ✓ {poi.get('name')}")
                        else:
                            print(f"  ✗ {poi.get('name')}")
                    except Exception as e:
                        summary["errors"].append(f"{poi.get('name')}: {str(e)}")
                        print(f"  ✗ {poi.get('name')}: {e}")
        else:
            for poi in all_pois:
                photo_url = fetch_poi_photo(poi)
                if photo_url:
                    summary["pois_fetched"] += 1
                    print(f"  ✓ {poi.get('name')}")
                else:
                    print(f"  ✗ {poi.get('name')}")

        # Save final cache
        self._save_cache()

        return summary

    def get_image_url(
        self,
        poi_name: Optional[str] = None,
        gaode_id: Optional[str] = None,
        category: Optional[str] = None,
        city: Optional[str] = None
    ) -> str:
        """
        Get image URL from cache or fallback to Unsplash placeholder.

        Args:
            poi_name: POI name
            gaode_id: Gaode Maps POI ID
            category: POI category (meal, attraction, accommodation, entertainment)
            city: City name (for city covers)

        Returns:
            Image URL (from cache or Unsplash fallback)
        """
        # Check city covers
        if city and city in self.cache["city_covers"]:
            return self.cache["city_covers"][city]

        # Check POI cache
        if gaode_id:
            cache_key = f"gaode_{gaode_id}"
            if cache_key in self.cache["pois"]:
                return self.cache["pois"][cache_key]

        if poi_name:
            cache_key = f"google_{poi_name}"
            if cache_key in self.cache["pois"]:
                return self.cache["pois"][cache_key]

        # Fallback to Unsplash
        if category and category in self.cache["fallback_unsplash"]:
            return self.cache["fallback_unsplash"][category]

        # Default fallback
        return self.cache["fallback_unsplash"]["attraction"]


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python image_fetcher.py <destination-slug>")
        print("Example: python image_fetcher.py beijing-exchange-bucket-list-20260202-232405")
        sys.exit(1)

    destination_slug = sys.argv[1]

    print(f"="*60)
    print(f"Image Fetcher - {destination_slug}")
    print(f"="*60)

    fetcher = ImageFetcher(destination_slug)
    summary = fetcher.fetch_all_images(parallel=True)

    print(f"\n" + "="*60)
    print(f"✅ Image fetching complete!")
    print(f"  City covers fetched: {summary['city_covers_fetched']}")
    print(f"  POI photos fetched: {summary['pois_fetched']}")
    if summary['errors']:
        print(f"  Errors: {len(summary['errors'])}")
        for error in summary['errors'][:5]:  # Show first 5 errors
            print(f"    - {error}")
    print(f"  Cache saved to: {fetcher.cache_file}")
    print(f"="*60)


if __name__ == "__main__":
    main()
