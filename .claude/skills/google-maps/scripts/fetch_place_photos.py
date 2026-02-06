#!/usr/bin/env python3
"""
Google Maps Place Photos fetcher.
Extends Google Maps skill with Place Photos API capability.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path for mcp_client import
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables from project .env file
import load_env  # noqa: F401
from mcp_client import MCPClient


def fetch_place_photos(
    place_id: str,
    max_results: int = 5,
    max_width: int = 800,
    api_key: Optional[str] = None
) -> List[str]:
    """
    Fetch photo URLs for a Google Maps place.

    Args:
        place_id: Google Maps Place ID
        max_results: Maximum number of photo URLs to return
        max_width: Maximum width of photos in pixels
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        List of photo URLs

    Example:
        photos = fetch_place_photos("ChIJN1t_tDeuEmsRUsoyG83frY4")
        for url in photos:
            print(url)
    """
    api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set", file=sys.stderr)
        return []

    env_vars = {"GOOGLE_MAPS_API_KEY": api_key}
    photo_urls = []

    try:
        with MCPClient("@modelcontextprotocol/server-google-maps", env_vars) as client:
            # Get place details with photos
            result = client.call_tool("maps_place_details", {"place_id": place_id})

            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            # Extract photo references
            photos = result.get("photos", [])
            if not photos:
                return []

            # Convert photo references to URLs
            for photo in photos[:max_results]:
                photo_reference = photo.get("photo_reference")
                if photo_reference:
                    photo_url = (
                        f"https://maps.googleapis.com/maps/api/place/photo"
                        f"?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}"
                    )
                    photo_urls.append(photo_url)

            return photo_urls

    except Exception as e:
        print(f"Error fetching place photos: {e}", file=sys.stderr)
        return []


def search_and_fetch_photos(
    query: str,
    location: Optional[str] = None,
    max_results: int = 3,
    max_width: int = 800,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for a place and fetch its photos.

    Args:
        query: Search query (e.g., "Forbidden City Beijing")
        location: Optional location context
        max_results: Maximum number of photo URLs to return
        max_width: Maximum width of photos in pixels
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with place info and photo URLs

    Example:
        result = search_and_fetch_photos("Forbidden City Beijing")
        print(json.dumps(result, indent=2))
    """
    api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "error": "GOOGLE_MAPS_API_KEY environment variable not set"
        }

    env_vars = {"GOOGLE_MAPS_API_KEY": api_key}

    try:
        with MCPClient("@modelcontextprotocol/server-google-maps", env_vars) as client:
            # Search for place
            search_query = f"{query} {location or ''}".strip()
            search_result = client.call_tool("maps_search_places", {"query": search_query})

            if isinstance(search_result, str):
                try:
                    search_result = json.loads(search_result)
                except json.JSONDecodeError:
                    pass

            if not isinstance(search_result, list) or len(search_result) == 0:
                return {
                    "error": "No places found",
                    "query": search_query
                }

            # Get first result
            place = search_result[0]
            place_id = place.get("place_id")
            if not place_id:
                return {
                    "error": "Place ID not found in search results",
                    "query": search_query
                }

            # Fetch photos
            photo_urls = fetch_place_photos(
                place_id=place_id,
                max_results=max_results,
                max_width=max_width,
                api_key=api_key
            )

            return {
                "place_name": place.get("name"),
                "place_id": place_id,
                "formatted_address": place.get("formatted_address"),
                "photos": photo_urls,
                "photo_count": len(photo_urls),
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "query": query
        }


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python fetch_place_photos.py <place_id|search_query>")
        print("\nExamples:")
        print("  python fetch_place_photos.py ChIJN1t_tDeuEmsRUsoyG83frY4")
        print("  python fetch_place_photos.py 'Forbidden City Beijing'")
        sys.exit(1)

    query_or_id = sys.argv[1]

    # Check if it's a place ID (starts with ChIJ)
    if query_or_id.startswith("ChIJ"):
        photos = fetch_place_photos(query_or_id)
        print(f"Fetched {len(photos)} photos for place ID: {query_or_id}")
        for i, url in enumerate(photos, 1):
            print(f"{i}. {url}")
    else:
        # Search and fetch
        result = search_and_fetch_photos(query_or_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
