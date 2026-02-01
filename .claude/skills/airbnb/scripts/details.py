#!/usr/bin/env python3
"""
Airbnb Listing Details Script

Retrieve comprehensive information about specific Airbnb listings including
amenities, house rules, policies, host details, and pricing.

Usage:
    python3 details.py <listing_id> [options]

Examples:
    python3 details.py 12345678
    python3 details.py 12345678 --checkin 2026-06-15 --checkout 2026-06-22
    python3 details.py 12345678 --adults 2 --children 2
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from project .env file
import load_env  # noqa: F401

from mcp_client import MCPClient, format_json_output


def get_listing_details(
    listing_id: str,
    checkin: str = None,
    checkout: str = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
    ignore_robots: bool = False
) -> dict:
    """
    Get detailed information about an Airbnb listing.

    Args:
        listing_id: Airbnb listing ID (from search results)
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        adults: Number of adults
        children: Number of children
        infants: Number of infants
        pets: Number of pets
        ignore_robots: Override robots.txt (use sparingly)

    Returns:
        Detailed listing information
    """
    client = MCPClient("@openbnb/mcp-server-airbnb")

    try:
        # Connect to MCP server
        client.connect()

        # Build arguments
        arguments = {
            "id": listing_id
        }

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
        if ignore_robots:
            arguments["ignoreRobotsText"] = True

        # Call listing details tool
        result = client.call_tool("airbnb_listing_details", arguments)

        return result

    finally:
        client.close()


def main():
    """Command-line interface for Airbnb listing details."""
    parser = argparse.ArgumentParser(
        description="Get detailed information about Airbnb listings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 details.py 12345678
  python3 details.py 12345678 --checkin 2026-06-15 --checkout 2026-06-22
  python3 details.py 12345678 --adults 2 --children 2
        """
    )

    parser.add_argument("listing_id", help="Airbnb listing ID")
    parser.add_argument("--checkin", help="Check-in date (YYYY-MM-DD)")
    parser.add_argument("--checkout", help="Check-out date (YYYY-MM-DD)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adults (default: 1)")
    parser.add_argument("--children", type=int, default=0, help="Number of children")
    parser.add_argument("--infants", type=int, default=0, help="Number of infants")
    parser.add_argument("--pets", type=int, default=0, help="Number of pets")
    parser.add_argument("--ignore-robots", action="store_true", help="Override robots.txt")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    try:
        result = get_listing_details(
            listing_id=args.listing_id,
            checkin=args.checkin,
            checkout=args.checkout,
            adults=args.adults,
            children=args.children,
            infants=args.infants,
            pets=args.pets,
            ignore_robots=args.ignore_robots
        )

        if args.raw:
            print(format_json_output(result))
        else:
            # Format output for readability
            if isinstance(result, dict) and "listing" in result:
                listing = result["listing"]

                print(f"=== {listing.get('name', 'Unnamed Property')} ===\n")

                # Basic Info
                print(f"ID: {listing.get('id')}")
                print(f"Type: {listing.get('propertyType', 'Unknown')}")
                print(f"URL: {listing.get('url', 'N/A')}\n")

                # Location
                if "location" in listing:
                    loc = listing["location"]
                    print(f"Location: {loc.get('city', 'Unknown')}")
                    if loc.get('neighborhood'):
                        print(f"Neighborhood: {loc['neighborhood']}")
                    if loc.get('latitude') and loc.get('longitude'):
                        print(f"Coordinates: {loc['latitude']}, {loc['longitude']}")
                    print()

                # Capacity
                if "capacity" in listing:
                    cap = listing["capacity"]
                    print(f"Capacity:")
                    print(f"  Bedrooms: {cap.get('bedrooms', 'N/A')}")
                    print(f"  Beds: {cap.get('beds', 'N/A')}")
                    print(f"  Bathrooms: {cap.get('bathrooms', 'N/A')}")
                    print(f"  Max Guests: {cap.get('maxGuests', 'N/A')}\n")

                # Host
                if "host" in listing:
                    host = listing["host"]
                    print(f"Host: {host.get('name', 'Unknown')}")
                    if host.get('isSuperhost'):
                        print(f"  ⭐ Superhost")
                    if host.get('responseRate'):
                        print(f"  Response Rate: {host['responseRate']}%")
                    if host.get('responseTime'):
                        print(f"  Response Time: {host['responseTime']}")
                    print()

                # Rating
                print(f"Rating: {listing.get('rating', 'N/A')} ({listing.get('reviewCount', 0)} reviews)\n")

                # Pricing
                if "pricing" in listing:
                    pricing = listing["pricing"]
                    print(f"Pricing:")
                    if pricing.get('basePrice'):
                        print(f"  Base Price: ${pricing['basePrice']}/night")
                    if pricing.get('cleaningFee'):
                        print(f"  Cleaning Fee: ${pricing['cleaningFee']}")
                    if pricing.get('serviceFee'):
                        print(f"  Service Fee: ${pricing['serviceFee']}")
                    if pricing.get('total'):
                        print(f"  Total: ${pricing['total']}")
                        # Calculate nights if dates provided
                        if args.checkin and args.checkout:
                            from datetime import datetime
                            checkin_date = datetime.strptime(args.checkin, "%Y-%m-%d")
                            checkout_date = datetime.strptime(args.checkout, "%Y-%m-%d")
                            nights = (checkout_date - checkin_date).days
                            if nights > 0:
                                avg_per_night = pricing['total'] / nights
                                print(f"  Average per Night: ${avg_per_night:.2f} ({nights} nights)")
                    print()

                # Amenities
                if "amenities" in listing and listing["amenities"]:
                    print(f"Amenities ({len(listing['amenities'])}):")
                    for amenity in listing["amenities"][:20]:  # Show first 20
                        print(f"  • {amenity}")
                    if len(listing['amenities']) > 20:
                        print(f"  ... and {len(listing['amenities']) - 20} more")
                    print()

                # Policies
                if "policies" in listing:
                    policies = listing["policies"]
                    print(f"Policies:")
                    if policies.get('checkIn'):
                        print(f"  Check-in: {policies['checkIn']}")
                    if policies.get('checkOut'):
                        print(f"  Check-out: {policies['checkOut']}")
                    if policies.get('cancellationPolicy'):
                        print(f"  Cancellation: {policies['cancellationPolicy']}")
                    if policies.get('houseRules') and policies['houseRules']:
                        print(f"  House Rules:")
                        for rule in policies['houseRules'][:10]:  # Show first 10
                            print(f"    - {rule}")
                    print()

                # Description
                if listing.get('description'):
                    print(f"Description:")
                    desc = listing['description']
                    # Truncate if too long
                    if len(desc) > 500:
                        print(f"{desc[:500]}...\n")
                    else:
                        print(f"{desc}\n")

                # Recent Reviews
                if "reviews" in listing and listing["reviews"]:
                    print(f"Recent Reviews ({min(3, len(listing['reviews']))}):")
                    for review in listing["reviews"][:3]:
                        if isinstance(review, dict):
                            print(f"  • {review.get('text', 'No text')}")
                            if review.get('date'):
                                print(f"    Date: {review['date']}")
                        elif isinstance(review, str):
                            print(f"  • {review}")
                        print()

            else:
                print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
