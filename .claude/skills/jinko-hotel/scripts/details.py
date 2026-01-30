#!/usr/bin/env python3
"""
Hotel details and review functionality for Jinko Hotel Booking MCP.
"""

import json
import os
import sys
from typing import Dict, Any, Optional

from mcp_client import MCPClient


def get_hotel_details(hotel_id: str) -> Dict[str, Any]:
    """
    Get comprehensive hotel information.

    Args:
        hotel_id: Unique hotel identifier

    Returns:
        Detailed hotel information including:
        - Name, address, contact
        - Star rating and guest rating
        - Amenities and facilities
        - Policies (check-in/out, cancellation)
        - Photos
        - Description
    """
    api_key = os.environ.get('JINKO_API_KEY')
    if not api_key:
        raise ValueError("JINKO_API_KEY environment variable not set")

    with MCPClient(
        package='@jinko/hotel-booking-mcp-server',
        env_vars={'JINKO_API_KEY': api_key}
    ) as client:
        client.initialize()

        result = client.call_tool('get_hotel_details', {
            'hotelId': hotel_id
        })
        return result


def get_room_types(hotel_id: str, checkin: Optional[str] = None, checkout: Optional[str] = None) -> Dict[str, Any]:
    """
    Get available room types and pricing for a hotel.

    Args:
        hotel_id: Unique hotel identifier
        checkin: Check-in date (YYYY-MM-DD, optional for pricing)
        checkout: Check-out date (YYYY-MM-DD, optional for pricing)

    Returns:
        Room types with:
        - Room name and description
        - Bed configuration
        - Occupancy limits
        - Size
        - Amenities
        - Pricing (if dates provided)
        - Availability
    """
    api_key = os.environ.get('JINKO_API_KEY')
    if not api_key:
        raise ValueError("JINKO_API_KEY environment variable not set")

    with MCPClient(
        package='@jinko/hotel-booking-mcp-server',
        env_vars={'JINKO_API_KEY': api_key}
    ) as client:
        client.initialize()

        params = {'hotelId': hotel_id}
        if checkin:
            params['checkin'] = checkin
        if checkout:
            params['checkout'] = checkout

        result = client.call_tool('get_room_types', params)
        return result


def get_reviews(hotel_id: str, limit: int = 20, sort_by: str = 'recent') -> Dict[str, Any]:
    """
    Get guest reviews for a hotel.

    Args:
        hotel_id: Unique hotel identifier
        limit: Maximum number of reviews to return (default: 20)
        sort_by: Sort order - 'recent', 'rating_high', 'rating_low' (default: 'recent')

    Returns:
        Guest reviews with:
        - Overall rating statistics
        - Category ratings (cleanliness, service, location, etc.)
        - Individual reviews with text, rating, date
        - Reviewer information
        - Verified status
    """
    api_key = os.environ.get('JINKO_API_KEY')
    if not api_key:
        raise ValueError("JINKO_API_KEY environment variable not set")

    with MCPClient(
        package='@jinko/hotel-booking-mcp-server',
        env_vars={'JINKO_API_KEY': api_key}
    ) as client:
        client.initialize()

        result = client.call_tool('get_reviews', {
            'hotelId': hotel_id,
            'limit': limit,
            'sortBy': sort_by
        })
        return result


def main():
    """
    Command-line interface for hotel details.

    Usage:
        python3 details.py details <hotel_id>
        python3 details.py rooms <hotel_id> [checkin] [checkout]
        python3 details.py reviews <hotel_id> [limit] [sort_by]
    """
    if len(sys.argv) < 2:
        print("Usage: python3 details.py <command> [args...]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  details <hotel_id>", file=sys.stderr)
        print("  rooms <hotel_id> [checkin] [checkout]", file=sys.stderr)
        print("  reviews <hotel_id> [limit] [sort_by]", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  python3 details.py details 'hotel_12345'", file=sys.stderr)
        print("  python3 details.py rooms 'hotel_12345' '2026-02-15' '2026-02-17'", file=sys.stderr)
        print("  python3 details.py reviews 'hotel_12345' 20 'recent'", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'details':
            if len(sys.argv) < 3:
                print("Error: details requires hotel_id", file=sys.stderr)
                sys.exit(1)

            hotel_id = sys.argv[2]
            result = get_hotel_details(hotel_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == 'rooms':
            if len(sys.argv) < 3:
                print("Error: rooms requires hotel_id", file=sys.stderr)
                sys.exit(1)

            hotel_id = sys.argv[2]
            checkin = sys.argv[3] if len(sys.argv) > 3 else None
            checkout = sys.argv[4] if len(sys.argv) > 4 else None

            result = get_room_types(hotel_id, checkin, checkout)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == 'reviews':
            if len(sys.argv) < 3:
                print("Error: reviews requires hotel_id", file=sys.stderr)
                sys.exit(1)

            hotel_id = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            sort_by = sys.argv[4] if len(sys.argv) > 4 else 'recent'

            result = get_reviews(hotel_id, limit, sort_by)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
