#!/usr/bin/env python3
"""
Flight Details Script for Amadeus Flight MCP

Provides detailed flight information including airline details, aircraft info,
seat availability, and schedule information via MCP server.

Usage:
    python3 details.py flight_details <flight_number> <departure_date>
    python3 details.py seat_availability <flight_offer_id>
    python3 details.py airline_info <airline_code>

Examples:
    # Get flight details
    python3 details.py flight_details AF123 2026-03-15

    # Check seat availability
    python3 details.py seat_availability ABC123XYZ

    # Get airline information
    python3 details.py airline_info AF
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for mcp_client import
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient, retry_with_backoff


def get_flight_details(
    flight_number: str,
    departure_date: str
) -> dict:
    """
    Get detailed information about a specific flight

    Args:
        flight_number: Flight number (e.g., 'AF123')
        departure_date: Departure date in ISO format (YYYY-MM-DD)

    Returns:
        Detailed flight information including schedule, aircraft, etc.
    """
    client = MCPClient()

    try:
        # Initialize client
        def init():
            client.initialize()

        retry_with_backoff(init)

        # Get flight details
        def get_details():
            return client.call_tool("flight_details", {
                "flightNumber": flight_number.upper(),
                "departureDate": departure_date
            })

        result = retry_with_backoff(get_details)

        return result

    finally:
        client.close()


def check_seat_availability(flight_offer_id: str) -> dict:
    """
    Check seat and cabin availability for a flight offer

    Args:
        flight_offer_id: Flight offer ID from search results

    Returns:
        Seat availability information by cabin class
    """
    client = MCPClient()

    try:
        # Initialize client
        def init():
            client.initialize()

        retry_with_backoff(init)

        # Check availability
        def check():
            return client.call_tool("seat_availability", {
                "flightOfferId": flight_offer_id
            })

        result = retry_with_backoff(check)

        return result

    finally:
        client.close()


def get_airline_info(airline_code: str) -> dict:
    """
    Get information about an airline

    Args:
        airline_code: IATA airline code (e.g., 'AF', 'BA', 'CA')

    Returns:
        Airline information including name, contact, etc.
    """
    client = MCPClient()

    try:
        # Initialize client
        def init():
            client.initialize()

        retry_with_backoff(init)

        # Get airline info
        def get_info():
            return client.call_tool("airline_info", {
                "airlineCode": airline_code.upper()
            })

        result = retry_with_backoff(get_info)

        return result

    finally:
        client.close()


def format_flight_details(results: dict) -> str:
    """
    Format flight details for human-readable output

    Args:
        results: Raw flight details results from MCP

    Returns:
        Formatted string output
    """
    if not results:
        return "No flight details available"

    output_lines = []

    # Extract data
    data = results.get('data', [])
    if not data:
        return "No flight details available"

    flight = data[0] if isinstance(data, list) else data

    output_lines.append("Flight Details:")
    output_lines.append("")

    # Flight number and date
    output_lines.append(f"Flight: {flight.get('flightNumber', 'N/A')}")
    output_lines.append(f"Date: {flight.get('departureDate', 'N/A')}")
    output_lines.append("")

    # Departure and arrival
    departure = flight.get('departure', {})
    arrival = flight.get('arrival', {})

    output_lines.append(f"Departure: {departure.get('airport', 'N/A')} "
                       f"at {departure.get('time', 'N/A')}")
    output_lines.append(f"Arrival: {arrival.get('airport', 'N/A')} "
                       f"at {arrival.get('time', 'N/A')}")
    output_lines.append("")

    # Aircraft
    aircraft = flight.get('aircraft', {})
    if aircraft:
        output_lines.append(f"Aircraft: {aircraft.get('type', 'N/A')} "
                           f"({aircraft.get('model', 'N/A')})")
        output_lines.append("")

    # Duration
    if 'duration' in flight:
        output_lines.append(f"Duration: {flight['duration']}")
        output_lines.append("")

    # Status
    if 'status' in flight:
        output_lines.append(f"Status: {flight['status']}")
        output_lines.append("")

    return "\n".join(output_lines)


def format_seat_availability(results: dict) -> str:
    """
    Format seat availability for human-readable output

    Args:
        results: Raw seat availability results from MCP

    Returns:
        Formatted string output
    """
    if not results:
        return "No seat availability information"

    output_lines = []

    # Extract data
    data = results.get('data', {})
    if not data:
        return "No seat availability information"

    output_lines.append("Seat Availability:")
    output_lines.append("")

    # Cabin classes
    cabins = data.get('cabins', [])
    for cabin in cabins:
        cabin_class = cabin.get('class', 'N/A')
        available = cabin.get('available', 'N/A')
        total = cabin.get('total', 'N/A')

        output_lines.append(f"{cabin_class}: {available}/{total} seats available")

    return "\n".join(output_lines)


def format_airline_info(results: dict) -> str:
    """
    Format airline information for human-readable output

    Args:
        results: Raw airline info results from MCP

    Returns:
        Formatted string output
    """
    if not results:
        return "No airline information available"

    output_lines = []

    # Extract data
    data = results.get('data', {})
    if not data:
        return "No airline information available"

    output_lines.append("Airline Information:")
    output_lines.append("")

    # Basic info
    output_lines.append(f"Code: {data.get('code', 'N/A')}")
    output_lines.append(f"Name: {data.get('name', 'N/A')}")

    # Contact info
    if 'contact' in data:
        contact = data['contact']
        output_lines.append(f"Website: {contact.get('website', 'N/A')}")
        output_lines.append(f"Phone: {contact.get('phone', 'N/A')}")

    return "\n".join(output_lines)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "flight_details":
            # Parse arguments
            if len(sys.argv) < 4:
                print("Usage: details.py flight_details <flight_number> <departure_date>")
                sys.exit(1)

            flight_number = sys.argv[2]
            departure_date = sys.argv[3]

            # Get flight details
            results = get_flight_details(
                flight_number=flight_number,
                departure_date=departure_date
            )

            # Output results
            print(json.dumps(results, indent=2))

        elif command == "seat_availability":
            if len(sys.argv) < 3:
                print("Usage: details.py seat_availability <flight_offer_id>")
                sys.exit(1)

            flight_offer_id = sys.argv[2]

            # Check seat availability
            results = check_seat_availability(flight_offer_id)

            # Output results
            print(json.dumps(results, indent=2))

        elif command == "airline_info":
            if len(sys.argv) < 3:
                print("Usage: details.py airline_info <airline_code>")
                sys.exit(1)

            airline_code = sys.argv[2]

            # Get airline info
            results = get_airline_info(airline_code)

            # Output results
            print(json.dumps(results, indent=2))

        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
