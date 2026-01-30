#!/usr/bin/env python3
"""
Hotel search and filtering functionality for Jinko Hotel Booking MCP.
"""

import json
import os
import sys
from typing import Dict, Any, Optional

from mcp_client import MCPClient


def search_hotels(
    location: str,
    checkin: str,
    checkout: str,
    guests: int = 2,
    rooms: int = 1,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None
) -> Dict[str, Any]:
    """
    Search for hotels by location, dates, and filters.

    Args:
        location: City or area name (e.g., "Beijing", "Shanghai Pudong")
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        guests: Number of guests (default: 2)
        rooms: Number of rooms (default: 1)
        min_price: Minimum price per night (optional)
        max_price: Maximum price per night (optional)
        min_rating: Minimum rating (0-5, optional)

    Returns:
        Hotel search results with pricing and availability
    """
    api_key = os.environ.get('JINKO_API_KEY')
    if not api_key:
        raise ValueError("JINKO_API_KEY environment variable not set")

    with MCPClient(
        package='@jinko/hotel-booking-mcp-server',
        env_vars={'JINKO_API_KEY': api_key}
    ) as client:
        # Initialize connection
        client.initialize()

        # Build search parameters
        params = {
            'location': location,
            'checkin': checkin,
            'checkout': checkout,
            'guests': guests,
            'rooms': rooms
        }

        if min_price is not None:
            params['minPrice'] = min_price
        if max_price is not None:
            params['maxPrice'] = max_price
        if min_rating is not None:
            params['minRating'] = min_rating

        # Call search tool
        result = client.call_tool('search_hotels', params)
        return result


def filter_by_facilities(
    hotels: list,
    facilities: list
) -> list:
    """
    Filter hotels by required facilities.

    Args:
        hotels: List of hotel objects from search results
        facilities: List of required facilities (e.g., ['wifi', 'parking', 'pool'])

    Returns:
        Filtered list of hotels matching all facility requirements
    """
    api_key = os.environ.get('JINKO_API_KEY')
    if not api_key:
        raise ValueError("JINKO_API_KEY environment variable not set")

    with MCPClient(
        package='@jinko/hotel-booking-mcp-server',
        env_vars={'JINKO_API_KEY': api_key}
    ) as client:
        client.initialize()

        result = client.call_tool('filter_by_facilities', {
            'hotels': hotels,
            'facilities': facilities
        })
        return result


def search_nearby(
    location: str,
    poi: str,
    radius_km: float = 5.0,
    checkin: str = None,
    checkout: str = None,
    guests: int = 2,
    rooms: int = 1
) -> Dict[str, Any]:
    """
    Search for hotels near a specific point of interest.

    Args:
        location: City name
        poi: Point of interest (e.g., "Tiananmen Square", "Shanghai Tower")
        radius_km: Search radius in kilometers (default: 5.0)
        checkin: Check-in date (YYYY-MM-DD, optional)
        checkout: Check-out date (YYYY-MM-DD, optional)
        guests: Number of guests (default: 2)
        rooms: Number of rooms (default: 1)

    Returns:
        Hotels near the specified POI
    """
    api_key = os.environ.get('JINKO_API_KEY')
    if not api_key:
        raise ValueError("JINKO_API_KEY environment variable not set")

    with MCPClient(
        package='@jinko/hotel-booking-mcp-server',
        env_vars={'JINKO_API_KEY': api_key}
    ) as client:
        client.initialize()

        params = {
            'location': location,
            'poi': poi,
            'radius': radius_km,
            'guests': guests,
            'rooms': rooms
        }

        if checkin:
            params['checkin'] = checkin
        if checkout:
            params['checkout'] = checkout

        result = client.call_tool('search_nearby', params)
        return result


def main():
    """
    Command-line interface for hotel search.

    Usage:
        python3 search.py search <location> <checkin> <checkout> [guests] [rooms] [min_price] [max_price] [min_rating]
        python3 search.py filter <hotels_json> <facilities_csv>
        python3 search.py nearby <location> <poi> [radius_km] [checkin] [checkout] [guests] [rooms]
    """
    if len(sys.argv) < 2:
        print("Usage: python3 search.py <command> [args...]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  search <location> <checkin> <checkout> [guests] [rooms] [min_price] [max_price] [min_rating]", file=sys.stderr)
        print("  filter <hotels_json> <facilities_csv>", file=sys.stderr)
        print("  nearby <location> <poi> [radius_km] [checkin] [checkout] [guests] [rooms]", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  python3 search.py search 'Beijing' '2026-02-15' '2026-02-17' 2 1 200 500 4.0", file=sys.stderr)
        print("  python3 search.py filter '[{...}]' 'wifi,parking,pool'", file=sys.stderr)
        print("  python3 search.py nearby 'Beijing' 'Tiananmen Square' 3.0", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'search':
            if len(sys.argv) < 5:
                print("Error: search requires location, checkin, checkout", file=sys.stderr)
                sys.exit(1)

            location = sys.argv[2]
            checkin = sys.argv[3]
            checkout = sys.argv[4]
            guests = int(sys.argv[5]) if len(sys.argv) > 5 else 2
            rooms = int(sys.argv[6]) if len(sys.argv) > 6 else 1
            min_price = float(sys.argv[7]) if len(sys.argv) > 7 else None
            max_price = float(sys.argv[8]) if len(sys.argv) > 8 else None
            min_rating = float(sys.argv[9]) if len(sys.argv) > 9 else None

            result = search_hotels(
                location=location,
                checkin=checkin,
                checkout=checkout,
                guests=guests,
                rooms=rooms,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == 'filter':
            if len(sys.argv) < 4:
                print("Error: filter requires hotels_json and facilities_csv", file=sys.stderr)
                sys.exit(1)

            hotels = json.loads(sys.argv[2])
            facilities = sys.argv[3].split(',')

            result = filter_by_facilities(hotels, facilities)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == 'nearby':
            if len(sys.argv) < 4:
                print("Error: nearby requires location and poi", file=sys.stderr)
                sys.exit(1)

            location = sys.argv[2]
            poi = sys.argv[3]
            radius_km = float(sys.argv[4]) if len(sys.argv) > 4 else 5.0
            checkin = sys.argv[5] if len(sys.argv) > 5 else None
            checkout = sys.argv[6] if len(sys.argv) > 6 else None
            guests = int(sys.argv[7]) if len(sys.argv) > 7 else 2
            rooms = int(sys.argv[8]) if len(sys.argv) > 8 else 1

            result = search_nearby(
                location=location,
                poi=poi,
                radius_km=radius_km,
                checkin=checkin,
                checkout=checkout,
                guests=guests,
                rooms=rooms
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
