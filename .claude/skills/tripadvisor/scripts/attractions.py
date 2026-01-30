#!/usr/bin/env python3
"""
TripAdvisor Attractions - Search and retrieve attraction information.

Usage:
    python3 attractions.py search <location> [--category <category>] [--min-rating <rating>] [--max-results <n>]
    python3 attractions.py details <attraction_id>
    python3 attractions.py nearby <latitude> <longitude> [--radius <km>] [--min-rating <rating>]

Examples:
    python3 attractions.py search "Paris, France" --category museums --min-rating 4.0
    python3 attractions.py details 12345
    python3 attractions.py nearby 48.8584 2.2945 --radius 2
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path to import mcp_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import MCPClient


def search_attractions(
    location: str,
    category: Optional[str] = None,
    min_rating: float = 3.0,
    max_results: int = 20,
    price_level: Optional[str] = None,
    sort_by: str = "rating"
) -> Dict[str, Any]:
    """
    Search for attractions by location.

    Args:
        location: City name, address, or coordinates
        category: Attraction type (museums, landmarks, parks, tours, outdoor, entertainment)
        min_rating: Minimum rating (1-5 scale)
        max_results: Maximum results to return
        price_level: Price range filter (free, budget, moderate, expensive)
        sort_by: Sort order (rating, popularity, distance, price)

    Returns:
        Search results dict
    """
    # Get API key from environment
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        return {
            "error": "TRIPADVISOR_API_KEY environment variable not set",
            "message": "Please set TRIPADVISOR_API_KEY in your environment"
        }

    # Initialize MCP client
    env_vars = {"TRIPADVISOR_API_KEY": api_key}

    try:
        with MCPClient("@tripadvisor/tripadvisor-mcp-server", env_vars) as client:
            # Prepare arguments
            arguments = {
                "location": location,
                "min_rating": min_rating,
                "max_results": max_results,
                "sort_by": sort_by
            }

            if category:
                arguments["category"] = category
            if price_level:
                arguments["price_level"] = price_level

            # Call tool
            result = client.call_tool("search_attractions", arguments)
            return result

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to search attractions"
        }


def get_attraction_details(
    attraction_id: str,
    include_reviews: bool = True,
    include_photos: bool = True
) -> Dict[str, Any]:
    """
    Get detailed information for a specific attraction.

    Args:
        attraction_id: TripAdvisor attraction ID
        include_reviews: Include user reviews
        include_photos: Include photo URLs

    Returns:
        Attraction details dict
    """
    # Get API key from environment
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        return {
            "error": "TRIPADVISOR_API_KEY environment variable not set",
            "message": "Please set TRIPADVISOR_API_KEY in your environment"
        }

    # Initialize MCP client
    env_vars = {"TRIPADVISOR_API_KEY": api_key}

    try:
        with MCPClient("@tripadvisor/tripadvisor-mcp-server", env_vars) as client:
            # Call tool
            result = client.call_tool("get_attraction_details", {
                "attraction_id": attraction_id,
                "include_reviews": include_reviews,
                "include_photos": include_photos
            })
            return result

    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to get details for attraction {attraction_id}"
        }


def search_by_coordinates(
    latitude: float,
    longitude: float,
    radius_km: int = 5,
    category: Optional[str] = None,
    min_rating: float = 3.0,
    max_results: int = 20
) -> Dict[str, Any]:
    """
    Find attractions near specific GPS coordinates.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        radius_km: Search radius in kilometers
        category: Filter by category
        min_rating: Minimum rating filter
        max_results: Maximum results

    Returns:
        Search results dict
    """
    # Get API key from environment
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        return {
            "error": "TRIPADVISOR_API_KEY environment variable not set",
            "message": "Please set TRIPADVISOR_API_KEY in your environment"
        }

    # Initialize MCP client
    env_vars = {"TRIPADVISOR_API_KEY": api_key}

    try:
        with MCPClient("@tripadvisor/tripadvisor-mcp-server", env_vars) as client:
            # Prepare arguments
            arguments = {
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius_km,
                "min_rating": min_rating,
                "max_results": max_results
            }

            if category:
                arguments["category"] = category

            # Call tool
            result = client.call_tool("search_by_coordinates", arguments)
            return result

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to search attractions by coordinates"
        }


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="TripAdvisor Attractions Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search attractions by location")
    search_parser.add_argument("location", help="City name, address, or coordinates")
    search_parser.add_argument("--category", help="Attraction category", choices=[
        "museums", "landmarks", "parks", "tours", "outdoor", "entertainment"
    ])
    search_parser.add_argument("--min-rating", type=float, default=3.0, help="Minimum rating (1-5)")
    search_parser.add_argument("--max-results", type=int, default=20, help="Maximum results")
    search_parser.add_argument("--price-level", choices=["free", "budget", "moderate", "expensive"])
    search_parser.add_argument("--sort-by", default="rating", choices=[
        "rating", "popularity", "distance", "price"
    ])

    # Details command
    details_parser = subparsers.add_parser("details", help="Get attraction details")
    details_parser.add_argument("attraction_id", help="TripAdvisor attraction ID")
    details_parser.add_argument("--no-reviews", action="store_true", help="Exclude reviews")
    details_parser.add_argument("--no-photos", action="store_true", help="Exclude photos")

    # Nearby command
    nearby_parser = subparsers.add_parser("nearby", help="Search attractions near coordinates")
    nearby_parser.add_argument("latitude", type=float, help="Latitude")
    nearby_parser.add_argument("longitude", type=float, help="Longitude")
    nearby_parser.add_argument("--radius", type=int, default=5, help="Search radius in km")
    nearby_parser.add_argument("--category", help="Attraction category")
    nearby_parser.add_argument("--min-rating", type=float, default=3.0, help="Minimum rating")
    nearby_parser.add_argument("--max-results", type=int, default=20, help="Maximum results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "search":
        result = search_attractions(
            location=args.location,
            category=args.category,
            min_rating=args.min_rating,
            max_results=args.max_results,
            price_level=args.price_level,
            sort_by=args.sort_by
        )
    elif args.command == "details":
        result = get_attraction_details(
            attraction_id=args.attraction_id,
            include_reviews=not args.no_reviews,
            include_photos=not args.no_photos
        )
    elif args.command == "nearby":
        result = search_by_coordinates(
            latitude=args.latitude,
            longitude=args.longitude,
            radius_km=args.radius,
            category=args.category,
            min_rating=args.min_rating,
            max_results=args.max_results
        )

    # Output result
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
