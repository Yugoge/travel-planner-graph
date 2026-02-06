#!/usr/bin/env python3
"""
Batch image fetcher using skill scripts directly.
More reliable than MCP Client for large batch operations.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


class BatchImageFetcher:
    """Fetch images using skill scripts in small batches"""

    def __init__(self, destination_slug: str):
        self.destination_slug = destination_slug
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data" / destination_slug
        self.cache_file = self.data_dir / "images.json"
        self.venv_python = "/root/.claude/venv/bin/python3"

        # Load cache
        self.cache = self._load_cache()

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
        """Fetch city photo using Google Maps skill script"""
        try:
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

            # Parse JSON from stderr
            try:
                data = json.loads(result.stderr)
                if data.get("results", {}).get("places"):
                    place = data["results"]["places"][0]
                    place_id = place.get("place_id")
                    # For now, we don't have photo URLs in place search
                    # Would need place details API
                    return None
            except:
                pass

        except Exception as e:
            print(f"  Google Maps error for {city_name}: {e}")

        return None

    def fetch_poi_photo_gaode(self, poi_name: str, city: str) -> Optional[str]:
        """Fetch POI photo using Gaode Maps skill script"""
        try:
            script_path = self.base_dir / ".claude/skills/gaode-maps/scripts/poi_search.py"
            result = subprocess.run(
                [self.venv_python, str(script_path), "keyword", poi_name, city, "餐饮服务|风景名胜"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=script_path.parent
            )

            if result.returncode != 0:
                return None

            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                if data.get("pois") and len(data["pois"]) > 0:
                    poi = data["pois"][0]
                    photos = poi.get("photos", {})
                    url = photos.get("url")
                    if url and url.startswith("http"):
                        return url
            except:
                pass

        except subprocess.TimeoutExpired:
            print(f"  Timeout for {poi_name}")
        except Exception as e:
            print(f"  Gaode error for {poi_name}: {e}")

        return None

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
            if city in self.cache["city_covers"]:
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

    def fetch_pois(self, limit: int = 10):
        """Fetch POI photos (limited batch)"""
        print(f"\n📍 Fetching POI photos (max {limit})...")

        # Get POIs from attractions
        attractions_path = self.data_dir / "attractions.json"
        if not attractions_path.exists():
            return

        with open(attractions_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        pois = []
        for day in data.get("data", {}).get("days", []):
            location = day.get("location", "")
            for attraction in day.get("attractions", []):
                name = attraction.get("name", "")
                if name:
                    pois.append({"name": name, "city": location})

        fetched = 0
        for poi in pois[:limit]:
            cache_key = f"gaode_{poi['name']}"
            if cache_key in self.cache["pois"]:
                print(f"  ✓ {poi['name']} (cached)")
                continue

            print(f"  Fetching {poi['name']}...", end=" ")
            photo_url = self.fetch_poi_photo_gaode(poi['name'], poi['city'])

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

    destination = sys.argv[1]
    city_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    poi_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    print("="*60)
    print(f"Batch Image Fetcher - {destination}")
    print("="*60)

    fetcher = BatchImageFetcher(destination)
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
