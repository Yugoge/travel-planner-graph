#!/usr/bin/env python3
"""
Hotel booking and availability functionality for Jinko Hotel Booking MCP.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional

from mcp_client import MCPClient


def check_availability(
    hotel_id: str,
    checkin: str,
    checkout: str,
    guests: int = 2,
    rooms: int = 1
) -> Dict[str, Any]:
    """
    Check real-time availability for a hotel.

    Args:
        hotel_id: Unique hotel identifier
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        guests: Number of guests (default: 2)
        rooms: Number of rooms (default: 1)

    Returns:
        Availability status with:
        - Available room types
        - Pricing per night
        - Total cost
        - Restrictions (minimum stay, maximum stay)
        - Cancellation policies
    """
    api_key = os.environ.get('JINKO_API_KEY')
    if not api_key:
        raise ValueError("JINKO_API_KEY environment variable not set")

    with MCPClient(
        package='@jinko/hotel-booking-mcp-server',
        env_vars={'JINKO_API_KEY': api_key}
    ) as client:
        client.initialize()

        result = client.call_tool('check_availability', {
            'hotelId': hotel_id,
            'checkin': checkin,
            'checkout': checkout,
            'guests': guests,
            'rooms': rooms
        })
        return result


def generate_booking_link(
    hotel_id: str,
    room_type_id: str,
    checkin: str,
    checkout: str,
    guests: int = 2,
    rooms: int = 1
) -> Dict[str, Any]:
    """
    Generate booking URL with pricing preserved.

    Args:
        hotel_id: Unique hotel identifier
        room_type_id: Selected room type identifier
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        guests: Number of guests (default: 2)
        rooms: Number of rooms (default: 1)

    Returns:
        Booking link with:
        - Direct booking URL
        - Price guarantee
        - Expiration time
        - Terms and conditions
    """
    api_key = os.environ.get('JINKO_API_KEY')
    if not api_key:
        raise ValueError("JINKO_API_KEY environment variable not set")

    with MCPClient(
        package='@jinko/hotel-booking-mcp-server',
        env_vars={'JINKO_API_KEY': api_key}
    ) as client:
        client.initialize()

        result = client.call_tool('generate_booking_link', {
            'hotelId': hotel_id,
            'roomTypeId': room_type_id,
            'checkin': checkin,
            'checkout': checkout,
            'guests': guests,
            'rooms': rooms
        })
        return result


def compare_prices(
    hotel_id: str,
    checkin: str,
    checkout: str,
    guests: int = 2,
    rooms: int = 1,
    platforms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compare prices across booking platforms.

    Args:
        hotel_id: Unique hotel identifier
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        guests: Number of guests (default: 2)
        rooms: Number of rooms (default: 1)
        platforms: List of platforms to check (e.g., ['booking.com', 'expedia'])
                  If None, checks all available platforms

    Returns:
        Price comparison with:
        - Platform name
        - Price per night
        - Total price
        - Fees breakdown
        - Cancellation policy
        - Best price indicator
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
            'hotelId': hotel_id,
            'checkin': checkin,
            'checkout': checkout,
            'guests': guests,
            'rooms': rooms
        }

        if platforms:
            params['platforms'] = platforms

        result = client.call_tool('compare_prices', params)
        return result


def main():
    """
    Command-line interface for hotel booking.

    Usage:
        python3 booking.py availability <hotel_id> <checkin> <checkout> [guests] [rooms]
        python3 booking.py link <hotel_id> <room_type_id> <checkin> <checkout> [guests] [rooms]
        python3 booking.py compare <hotel_id> <checkin> <checkout> [guests] [rooms] [platforms_csv]
    """
    if len(sys.argv) < 2:
        print("Usage: python3 booking.py <command> [args...]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  availability <hotel_id> <checkin> <checkout> [guests] [rooms]", file=sys.stderr)
        print("  link <hotel_id> <room_type_id> <checkin> <checkout> [guests] [rooms]", file=sys.stderr)
        print("  compare <hotel_id> <checkin> <checkout> [guests] [rooms] [platforms_csv]", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  python3 booking.py availability 'hotel_12345' '2026-02-15' '2026-02-17' 2 1", file=sys.stderr)
        print("  python3 booking.py link 'hotel_12345' 'room_67890' '2026-02-15' '2026-02-17' 2 1", file=sys.stderr)
        print("  python3 booking.py compare 'hotel_12345' '2026-02-15' '2026-02-17' 2 1 'booking.com,expedia'", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'availability':
            if len(sys.argv) < 5:
                print("Error: availability requires hotel_id, checkin, checkout", file=sys.stderr)
                sys.exit(1)

            hotel_id = sys.argv[2]
            checkin = sys.argv[3]
            checkout = sys.argv[4]
            guests = int(sys.argv[5]) if len(sys.argv) > 5 else 2
            rooms = int(sys.argv[6]) if len(sys.argv) > 6 else 1

            result = check_availability(hotel_id, checkin, checkout, guests, rooms)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == 'link':
            if len(sys.argv) < 6:
                print("Error: link requires hotel_id, room_type_id, checkin, checkout", file=sys.stderr)
                sys.exit(1)

            hotel_id = sys.argv[2]
            room_type_id = sys.argv[3]
            checkin = sys.argv[4]
            checkout = sys.argv[5]
            guests = int(sys.argv[6]) if len(sys.argv) > 6 else 2
            rooms = int(sys.argv[7]) if len(sys.argv) > 7 else 1

            result = generate_booking_link(hotel_id, room_type_id, checkin, checkout, guests, rooms)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == 'compare':
            if len(sys.argv) < 5:
                print("Error: compare requires hotel_id, checkin, checkout", file=sys.stderr)
                sys.exit(1)

            hotel_id = sys.argv[2]
            checkin = sys.argv[3]
            checkout = sys.argv[4]
            guests = int(sys.argv[5]) if len(sys.argv) > 5 else 2
            rooms = int(sys.argv[6]) if len(sys.argv) > 6 else 1
            platforms = sys.argv[7].split(',') if len(sys.argv) > 7 else None

            result = compare_prices(hotel_id, checkin, checkout, guests, rooms, platforms)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
