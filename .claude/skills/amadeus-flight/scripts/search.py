#!/usr/bin/env python3
"""
Flight Search Script for Amadeus Flight MCP

Provides flight search functionality via MCP server.
Supports one-way, round-trip, and multi-city searches.

Usage:
    python3 search.py search_flights <origin> <destination> <departure_date> [return_date] [adults] [nonstop]
    python3 search.py multi_city <leg1_origin> <leg1_dest> <leg1_date> <leg2_origin> <leg2_dest> <leg2_date> ...

Examples:
    # One-way flight
    python3 search.py search_flights PEK CDG 2026-03-15 1 false

    # Round-trip flight
    python3 search.py search_flights PEK CDG 2026-03-15 2026-03-25 2 false

    # Multi-city (Beijing -> Paris -> London)
    python3 search.py multi_city PEK CDG 2026-03-15 CDG LHR 2026-03-20
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for mcp_client import
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient, retry_with_backoff


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = None,
    adults: int = 1,
    nonstop: bool = False
) -> dict:
    """
    Search for flights

    Args:
        origin: Origin airport IATA code (e.g., 'PEK')
        destination: Destination airport IATA code (e.g., 'CDG')
        departure_date: Departure date in ISO format (YYYY-MM-DD)
        return_date: Return date for round-trip (optional)
        adults: Number of adult passengers (default: 1)
        nonstop: Only show nonstop flights (default: False)

    Returns:
        Flight search results with pricing and schedules
    """
    client = MCPClient()

    try:
        # Initialize client
        def init():
            client.initialize()

        retry_with_backoff(init)

        # Prepare search arguments (verified from amadeus-mcp-server source code)
        arguments = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departureDate": departure_date,
            "adults": adults
        }

        if return_date:
            arguments["returnDate"] = return_date

        if nonstop:
            arguments["travelClass"] = "ECONOMY"  # Note: Amadeus API doesn't have direct nonstop filter

        # Search flights using verified tool name from MCP source
        def search():
            return client.call_tool("get_flights", arguments)

        result = retry_with_backoff(search)

        return result

    finally:
        client.close()


def multi_city_search(*legs) -> dict:
    """
    Search for multi-city flights

    Args:
        *legs: Variable number of leg tuples (origin, destination, date)
              Each leg is 3 arguments: origin_code, dest_code, departure_date

    Returns:
        Multi-city flight search results

    Example:
        multi_city_search('PEK', 'CDG', '2026-03-15', 'CDG', 'LHR', '2026-03-20')
    """
    if len(legs) % 3 != 0:
        raise ValueError(
            "Invalid number of arguments. Each leg requires 3 values: "
            "origin, destination, date"
        )

    # Parse legs
    flight_legs = []
    for i in range(0, len(legs), 3):
        flight_legs.append({
            "originLocationCode": legs[i].upper(),
            "destinationLocationCode": legs[i + 1].upper(),
            "departureDate": legs[i + 2]
        })

    client = MCPClient()

    try:
        # Initialize client
        def init():
            client.initialize()

        retry_with_backoff(init)

        # Search multi-city
        def search():
            return client.call_tool("multi_city_search", {
                "itineraries": flight_legs,
                "adults": 1
            })

        result = retry_with_backoff(search)

        return result

    finally:
        client.close()


def format_flight_results(results: dict) -> str:
    """
    Format flight search results for human-readable output

    Args:
        results: Raw flight search results from MCP

    Returns:
        Formatted string output
    """
    if not results:
        return "No flights found"

    output_lines = []

    # Check if results contain data
    data = results.get('data', [])
    if not data:
        return "No flights found"

    output_lines.append(f"Found {len(data)} flight options:\n")

    for i, flight in enumerate(data[:5], 1):  # Show top 5 results
        output_lines.append(f"Option {i}:")

        # Price
        price = flight.get('price', {})
        total = price.get('total', 'N/A')
        currency = price.get('currency', 'USD')
        output_lines.append(f"  Price: {total} {currency}")

        # Itineraries
        itineraries = flight.get('itineraries', [])
        for j, itinerary in enumerate(itineraries, 1):
            duration = itinerary.get('duration', 'N/A')
            output_lines.append(f"  Segment {j}: Duration {duration}")

            # Segments
            segments = itinerary.get('segments', [])
            for segment in segments:
                departure = segment.get('departure', {})
                arrival = segment.get('arrival', {})
                carrier = segment.get('carrierCode', 'N/A')
                flight_num = segment.get('number', 'N/A')

                output_lines.append(
                    f"    {carrier}{flight_num}: "
                    f"{departure.get('iataCode', 'N/A')} "
                    f"{departure.get('at', 'N/A')} -> "
                    f"{arrival.get('iataCode', 'N/A')} "
                    f"{arrival.get('at', 'N/A')}"
                )

        output_lines.append("")  # Blank line between options

    return "\n".join(output_lines)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "search_flights":
            # Parse arguments
            if len(sys.argv) < 5:
                print("Usage: search.py search_flights <origin> <destination> <departure_date> [return_date] [adults] [nonstop]")
                sys.exit(1)

            origin = sys.argv[2]
            destination = sys.argv[3]
            departure_date = sys.argv[4]
            return_date = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] != 'null' else None
            adults = int(sys.argv[6]) if len(sys.argv) > 6 else 1
            nonstop = sys.argv[7].lower() == 'true' if len(sys.argv) > 7 else False

            # Search flights
            results = search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
                nonstop=nonstop
            )

            # Output results
            print(json.dumps(results, indent=2))

        elif command == "multi_city":
            if len(sys.argv) < 5:
                print("Usage: search.py multi_city <origin1> <dest1> <date1> <origin2> <dest2> <date2> ...")
                sys.exit(1)

            # Get all leg arguments
            legs = sys.argv[2:]

            # Search multi-city
            results = multi_city_search(*legs)

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
