#!/usr/bin/env python3
"""
Airbnb Search Script

Search Airbnb vacation rental listings with comprehensive filtering options.

Usage:
    python3 search.py <location> [options]

Examples:
    python3 search.py "San Francisco, CA"
    python3 search.py "Austin, TX" --checkin 2026-06-15 --checkout 2026-06-22
    python3 search.py "Portland, OR" --adults 2 --children 2 --min-price 100 --max-price 250
    python3 search.py "Seattle, WA" --cursor "pagination_token_here"
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from project .env file
import load_env  # noqa: F401

from mcp_client import MCPClient, format_json_output


def search(
    location: str,
    place_id: str = None,
    checkin: str = None,
    checkout: str = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
    min_price: int = None,
    max_price: int = None,
    cursor: str = None,
    ignore_robots: bool = False
) -> dict:
    """
    Search Airbnb listings with filters.

    Args:
        location: Location to search (e.g., "San Francisco, CA")
        place_id: Google Maps Place ID (optional, overrides location)
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        adults: Number of adults
        children: Number of children
        infants: Number of infants
        pets: Number of pets
        min_price: Minimum price per night (USD)
        max_price: Maximum price per night (USD)
        cursor: Pagination cursor for next page
        ignore_robots: Override robots.txt (use sparingly)

    Returns:
        Search results with listings array and pagination cursor
    """
    client = MCPClient("@openbnb/mcp-server-airbnb")

    try:
        # Connect to MCP server
        client.connect()

        # Build arguments
        arguments = {
            "location": location
        }

        if place_id:
            arguments["placeId"] = place_id
        if checkin:
            arguments["checkin"] = checkin
        if checkout:
            arguments["checkout"] = checkout
        if adults and adults != 1:
            arguments["adults"] = adults
        if children:
            arguments["children"] = children
        if infants:
            arguments["infants"] = infants
        if pets:
            arguments["pets"] = pets
        if min_price:
            arguments["minPrice"] = min_price
        if max_price:
            arguments["maxPrice"] = max_price
        if cursor:
            arguments["cursor"] = cursor
        if ignore_robots:
            arguments["ignoreRobotsText"] = True

        # Call search tool
        result = client.call_tool("airbnb_search", arguments)

        return result

    finally:
        client.close()


def main():
    """Command-line interface for Airbnb search."""
    parser = argparse.ArgumentParser(
        description="Search Airbnb vacation rental listings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 search.py "San Francisco, CA"
  python3 search.py "Austin, TX" --checkin 2026-06-15 --checkout 2026-06-22
  python3 search.py "Portland, OR" --adults 2 --children 2 --min-price 100 --max-price 250
  python3 search.py "Seattle, WA" --cursor "pagination_token"
        """
    )

    parser.add_argument("location", help="Location to search (e.g., 'San Francisco, CA')")
    parser.add_argument("--place-id", help="Google Maps Place ID (overrides location)")
    parser.add_argument("--checkin", help="Check-in date (YYYY-MM-DD)")
    parser.add_argument("--checkout", help="Check-out date (YYYY-MM-DD)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adults (default: 1)")
    parser.add_argument("--children", type=int, default=0, help="Number of children")
    parser.add_argument("--infants", type=int, default=0, help="Number of infants")
    parser.add_argument("--pets", type=int, default=0, help="Number of pets")
    parser.add_argument("--min-price", type=int, help="Minimum price per night (USD)")
    parser.add_argument("--max-price", type=int, help="Maximum price per night (USD)")
    parser.add_argument("--cursor", help="Pagination cursor for next page")
    parser.add_argument("--ignore-robots", action="store_true", help="Override robots.txt")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    try:
        result = search(
            location=args.location,
            place_id=args.place_id,
            checkin=args.checkin,
            checkout=args.checkout,
            adults=args.adults,
            children=args.children,
            infants=args.infants,
            pets=args.pets,
            min_price=args.min_price,
            max_price=args.max_price,
            cursor=args.cursor,
            ignore_robots=args.ignore_robots
        )

        if args.raw:
            print(format_json_output(result))
        else:
            # Format output for readability
            if isinstance(result, dict) and "listings" in result:
                listings = result.get("listings", [])
                print(f"Found {len(listings)} listings\n")

                for i, listing in enumerate(listings, 1):
                    print(f"{i}. {listing.get('name', 'Unnamed')}")
                    print(f"   ID: {listing.get('id')}")
                    print(f"   Location: {listing.get('location', 'Unknown')}")
                    print(f"   Type: {listing.get('propertyType', 'Unknown')}")
                    print(f"   Price: ${listing.get('price', 'N/A')}/night")
                    print(f"   Bedrooms: {listing.get('bedrooms', 'N/A')} | Beds: {listing.get('beds', 'N/A')} | Bathrooms: {listing.get('bathrooms', 'N/A')}")
                    print(f"   Max Guests: {listing.get('maxGuests', 'N/A')}")
                    print(f"   Rating: {listing.get('rating', 'N/A')} ({listing.get('reviewCount', 0)} reviews)")
                    if listing.get('isSuperhost'):
                        print(f"   ⭐ Superhost")
                    print(f"   URL: {listing.get('url', 'N/A')}")
                    print()

                if result.get("cursor"):
                    print(f"More results available. Use --cursor '{result['cursor']}' to see next page")

                if result.get("searchUrl"):
                    print(f"\nView on Airbnb: {result['searchUrl']}")
            else:
                print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
