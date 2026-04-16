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

        # Load China cities from config (raises if config missing)
        china_cfg = self.base_dir / "config" / "china-cities.json"
        with open(china_cfg, 'r') as f:
            self._china_cities = set(json.load(f)["cities"])

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
        return any(city in location_lower for city in self._china_cities)

    def _load_fallback_images(self) -> dict:
        """Load fallback image URLs from config."""
        config_path = Path(__file__).parent.parent.parent / "config" / "fallback-images.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f).get("fallback_unsplash", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "meal": "", "attraction": "",
                "accommodation": "", "entertainment": ""
            }

    def _load_cache(self) -> Dict[str, Any]:
        """Load existing image cache or create new structure"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        return {
            "destination": self.destination_slug,
            "city_covers": {},
            "pois": {},
            "fallback_unsplash": self._load_fallback_images()
        }

    def _save_cache(self) -> None:
        """Save image cache to disk"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _get_gaode_api_key(self) -> Optional[str]:
        """Return Gaode Maps API key from environment, or None."""
        return os.environ.get("AMAP_MAPS_API_KEY")

    def _get_mcp_client(self):
        """Import and return MCPClient class lazily."""
        google_maps_script_dir = self.base_dir / ".claude" / "skills" / "google-maps" / "scripts"
        sys.path.insert(0, str(google_maps_script_dir))
        from mcp_client import MCPClient
        return MCPClient

    @staticmethod
    def _extract_first_photo_url(result: Any) -> Optional[str]:
        """Extract the first photo URL from a Gaode POI result structure."""
        if isinstance(result, str):
            result = json.loads(result)
        photos = result.get("photos") if isinstance(result, dict) else None
        if isinstance(photos, list) and photos:
            return photos[0].get("url")
        return None

    def fetch_gaode_poi_photos(self, gaode_id: str, poi_name: str) -> Optional[str]:
        """
        Fetch POI photos from Gaode Maps API.

        Args:
            gaode_id: Gaode Maps POI ID
            poi_name: POI name for cache key

        Returns:
            First photo URL or None if unavailable
        """
        cache_key = f"gaode_{gaode_id}"
        if cache_key in self.cache["pois"]:
            return self.cache["pois"][cache_key]

        api_key = self._get_gaode_api_key()
        if not api_key:
            print(f"Warning: AMAP_MAPS_API_KEY not set, cannot fetch Gaode photos for {poi_name}")
            return None

        try:
            MCPClient = self._get_mcp_client()
            with MCPClient("@plugin/amap-maps", {"AMAP_MAPS_API_KEY": api_key}) as client:
                result = client.call_tool("poi_detail", {"id": gaode_id, "extensions": "all"})
                photo_url = self._extract_first_photo_url(result)
                if photo_url:
                    self.cache["pois"][cache_key] = photo_url
                    self._save_cache()
                    return photo_url
        except Exception as e:
            print(f"Error fetching Gaode photos for {poi_name} ({gaode_id}): {e}")

        return None

    def _resolve_google_place_id(self, client, place_name: str, location: Optional[str]) -> Optional[str]:
        """Search Google Maps for a place and return first place_id."""
        search_result = client.call_tool("maps_search_places", {
            "query": f"{place_name} {location or ''}".strip()
        })
        if isinstance(search_result, str):
            search_result = json.loads(search_result)
        if isinstance(search_result, list) and search_result:
            return search_result[0].get("place_id")
        return None

    @staticmethod
    def _build_google_photo_url(photo_reference: str, api_key: str) -> str:
        """Build a Google Maps Static API photo URL."""
        return (
            f"https://maps.googleapis.com/maps/api/place/photo"
            f"?maxwidth=800&photoreference={photo_reference}&key={api_key}"
        )

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
        cache_key = f"google_{place_id or place_name}"
        if cache_key in self.cache["pois"]:
            return self.cache["pois"][cache_key]

        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if not api_key:
            print(f"Warning: GOOGLE_MAPS_API_KEY not set, cannot fetch Google photos for {place_name}")
            return None

        try:
            MCPClient = self._get_mcp_client()
            with MCPClient("@modelcontextprotocol/server-google-maps", {"GOOGLE_MAPS_API_KEY": api_key}) as client:
                if not place_id and place_name:
                    place_id = self._resolve_google_place_id(client, place_name, location)
                if not place_id:
                    return None

                details_result = client.call_tool("maps_place_details", {"place_id": place_id})
                if isinstance(details_result, str):
                    details_result = json.loads(details_result)

                photos = details_result.get("photos", [])
                if photos:
                    photo_reference = photos[0].get("photo_reference")
                    if photo_reference:
                        photo_url = self._build_google_photo_url(photo_reference, api_key)
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
        if city_name in self.cache["city_covers"]:
            return self.cache["city_covers"][city_name]

        is_china = self._is_china_location(city_name)
        photo_url = self._fetch_city_cover_preferred(city_name, is_china)

        if photo_url:
            self.cache["city_covers"][city_name] = photo_url
            self._save_cache()
            return photo_url

        return None

    def _fetch_city_cover_preferred(self, city_name: str, is_china: bool) -> Optional[str]:
        """Try preferred provider first, fall back to the other."""
        if is_china:
            photo_url = self._fetch_gaode_city_cover(city_name)
            if photo_url:
                return photo_url
            print(f"Gaode Maps failed for {city_name}, trying Google Maps")
            return self._fetch_google_city_cover(city_name)

        photo_url = self._fetch_google_city_cover(city_name)
        if photo_url:
            return photo_url
        print(f"Google Maps failed for {city_name}, trying Gaode Maps")
        return self._fetch_gaode_city_cover(city_name)

    @staticmethod
    def _extract_first_poi_photo(result: Any) -> Optional[str]:
        """Extract first photo URL from a Gaode POI search result."""
        if isinstance(result, str):
            result = json.loads(result)
        pois = result.get("pois") if isinstance(result, dict) else None
        if not (isinstance(pois, list) and pois):
            return None
        poi = pois[0]
        photos = poi.get("photos") if isinstance(poi, dict) else None
        if isinstance(photos, list) and photos:
            return photos[0].get("url")
        return None

    def _fetch_gaode_city_cover(self, city_name: str) -> Optional[str]:
        """Fetch city cover from Gaode Maps"""
        api_key = self._get_gaode_api_key()
        if not api_key:
            return None
        try:
            MCPClient = self._get_mcp_client()
            with MCPClient("@plugin/amap-maps", {"AMAP_MAPS_API_KEY": api_key}) as client:
                result = client.call_tool("poi_search_keyword", {
                    "keywords": city_name,
                    "city": city_name,
                    "types": "110000",  # Tourist attractions category
                    "offset": 1,
                    "extensions": "all"
                })
                return self._extract_first_poi_photo(result)
        except Exception as e:
            print(f"Gaode Maps city cover error for {city_name}: {e}")
        return None

    def _fetch_google_city_cover(self, city_name: str) -> Optional[str]:
        """Fetch city cover from Google Maps"""
        return self.fetch_google_place_photos(
            place_name=city_name,
            location="China"
        )

    @staticmethod
    def _make_poi_dict(poi_type: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Build a normalized POI dict from a raw item."""
        return {
            "type": poi_type,
            "name": item.get("name", ""),
            "gaode_id": item.get("gaode_id"),
            "address": item.get("address", ""),
            "location": item.get("location", "")
        }

    def _extract_pois_from_day(self, day: Dict[str, Any], all_pois: List[Dict[str, Any]]) -> None:
        """Extract all POIs from a single day entry into all_pois."""
        # Attractions (array-based)
        for item in day.get("attractions", []):
            all_pois.append(self._make_poi_dict("attraction", item))

        # Meals (keyed by breakfast/lunch/dinner)
        for meal_type in ("breakfast", "lunch", "dinner"):
            if meal_type in day:
                all_pois.append(self._make_poi_dict("meal", day[meal_type]))

        # Entertainment (array-based)
        for item in day.get("entertainment", []):
            all_pois.append(self._make_poi_dict("entertainment", item))

        # Cafe (array-based, symmetric to entertainment)
        for item in day.get("cafe", []):
            all_pois.append(self._make_poi_dict("cafe", item))

        # Accommodation (single object)
        if "accommodation" in day:
            all_pois.append(self._make_poi_dict("accommodation", day["accommodation"]))

    def _load_all_pois(self, agent_files: List[str]) -> tuple:
        """Load POIs and cities from agent data files."""
        all_pois: List[Dict[str, Any]] = []
        cities: set = set()

        for filename in agent_files:
            filepath = self.data_dir / filename
            if not filepath.exists():
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract actual data from agent wrapper
            if isinstance(data, dict) and 'data' in data:
                data = data['data']

            if "days" in data:
                for day in data["days"]:
                    cities.add(day.get("location", ""))
                    self._extract_pois_from_day(day, all_pois)

        return all_pois, cities

    def _fetch_city_covers(self, cities: set, summary: Dict[str, Any]) -> None:
        """Fetch city cover images for all cities."""
        print(f"\nFetching city cover images for {len(cities)} cities...")
        for city in cities:
            if not city:
                continue
            print(f"  Fetching cover for: {city}")
            photo_url = self.fetch_city_cover_image(city)
            if photo_url:
                summary["city_covers_fetched"] += 1
                print(f"    \u2713 Fetched")
            else:
                print(f"    \u2717 Failed")

    def _fetch_poi_photo(self, poi: Dict[str, Any]) -> Optional[str]:
        """Fetch a single POI photo choosing provider by location."""
        name = poi.get("name", "Unknown")
        gaode_id = poi.get("gaode_id")
        location = poi.get("location") or poi.get("address", "")
        is_china = self._is_china_location(location)

        if is_china:
            if gaode_id:
                photo_url = self.fetch_gaode_poi_photos(gaode_id, name)
                if photo_url:
                    return photo_url
            return self.fetch_google_place_photos(place_name=name, location=location)

        photo_url = self.fetch_google_place_photos(place_name=name, location=location)
        if photo_url:
            return photo_url
        if gaode_id:
            return self.fetch_gaode_poi_photos(gaode_id, name)
        return None

    def _fetch_pois_parallel(self, all_pois: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
        """Fetch POI photos in parallel."""
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._fetch_poi_photo, poi): poi for poi in all_pois}
            for future in as_completed(futures):
                poi = futures[future]
                try:
                    photo_url = future.result()
                    if photo_url:
                        summary["pois_fetched"] += 1
                        print(f"  \u2713 {poi.get('name')}")
                    else:
                        print(f"  \u2717 {poi.get('name')}")
                except Exception as e:
                    summary["errors"].append(f"{poi.get('name')}: {str(e)}")
                    print(f"  \u2717 {poi.get('name')}: {e}")

    def _fetch_pois_sequential(self, all_pois: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
        """Fetch POI photos sequentially."""
        for poi in all_pois:
            photo_url = self._fetch_poi_photo(poi)
            if photo_url:
                summary["pois_fetched"] += 1
                print(f"  \u2713 {poi.get('name')}")
            else:
                print(f"  \u2717 {poi.get('name')}")

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

        # Load agent data files (cafe.json added symmetrically to entertainment)
        agent_files = [
            "attractions.json",
            "meals.json",
            "accommodation.json",
            "entertainment.json",
            "cafe.json",
        ]
        all_pois, cities = self._load_all_pois(agent_files)

        self._fetch_city_covers(cities, summary)

        print(f"\nFetching POI photos for {len(all_pois)} POIs...")
        if parallel:
            self._fetch_pois_parallel(all_pois, summary)
        else:
            self._fetch_pois_sequential(all_pois, summary)

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
            category: POI category (meal, attraction, accommodation, entertainment, cafe)
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
    print(f"\u2705 Image fetching complete!")
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
