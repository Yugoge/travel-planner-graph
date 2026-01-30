#!/usr/bin/env python3
"""
Google Maps Place Details API integration via MCP.

Provides detailed information about specific places using the Google Maps MCP server.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path for mcp_client import
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCPClient


def get_place_details(
    place_id: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific place.

    Args:
        place_id: The place ID (from search results or geocoding)
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with place details including:
        - name, formatted_address, location
        - formatted_phone_number, website
        - rating, reviews
        - opening_hours

    Example:
        result = get_place_details("ChIJN1t_tDeuEmsRUsoyG83frY4")  # Google Australia
        print(json.dumps(result, indent=2))
    """
    api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "error": "GOOGLE_MAPS_API_KEY environment variable not set",
            "solution": "Set GOOGLE_MAPS_API_KEY environment variable with your API key"
        }

    env_vars = {"GOOGLE_MAPS_API_KEY": api_key}

    try:
        with MCPClient("@modelcontextprotocol/server-google-maps", env_vars) as client:
            arguments = {"place_id": place_id}
            result = client.call_tool("maps_place_details", arguments)

            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return {
                "place_id": place_id,
                "details": result,
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "place_id": place_id,
            "source": "google_maps"
        }


def format_place_details(result: Dict[str, Any]) -> str:
    """
    Format place details for human-readable output.

    Args:
        result: Result from get_place_details()

    Returns:
        Formatted string
    """
    if "error" in result:
        return f"Error: {result['error']}"

    details = result.get("details", {})
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except json.JSONDecodeError:
            return f"Details: {details}"

    output = []
    output.append(f"Place ID: {result.get('place_id', 'N/A')}\n")

    name = details.get("name", "Unknown")
    address = details.get("formatted_address", "No address")
    phone = details.get("formatted_phone_number", "No phone")
    website = details.get("website", "No website")
    rating = details.get("rating", "No rating")

    output.append(f"Name: {name}")
    output.append(f"Address: {address}")
    output.append(f"Phone: {phone}")
    output.append(f"Website: {website}")
    output.append(f"Rating: {rating}")

    # Opening hours
    opening_hours = details.get("opening_hours", {})
    if opening_hours:
        weekday_text = opening_hours.get("weekday_text", [])
        if weekday_text:
            output.append("\nOpening Hours:")
            for hours in weekday_text:
                output.append(f"  {hours}")

    # Reviews (first 3)
    reviews = details.get("reviews", [])
    if reviews:
        output.append("\nReviews (top 3):")
        for i, review in enumerate(reviews[:3], 1):
            author = review.get("author_name", "Anonymous")
            rating_val = review.get("rating", "?")
            text = review.get("text", "")[:100]  # First 100 chars
            output.append(f"  {i}. {author} ({rating_val}★): {text}...")

    # Location
    location = details.get("location", {})
    if location:
        lat = location.get("lat", location.get("latitude", "?"))
        lng = location.get("lng", location.get("longitude", "?"))
        output.append(f"\nLocation: {lat}, {lng}")

    return "\n".join(output)


def main():
    """CLI interface for place details lookup."""
    if len(sys.argv) < 2:
        print("Usage: python3 place_details.py <place_id>")
        print("\nExample:")
        print("  python3 place_details.py ChIJN1t_tDeuEmsRUsoyG83frY4")
        print("\nNote:")
        print("  Place IDs can be obtained from search results or geocoding")
        print("\nEnvironment:")
        print("  GOOGLE_MAPS_API_KEY: Required Google Maps API key")
        sys.exit(1)

    place_id = sys.argv[1]
    result = get_place_details(place_id)

    # Output formatted result
    print(format_place_details(result))

    # Also output raw JSON to stderr for programmatic use
    print(json.dumps(result, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
