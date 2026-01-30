#!/usr/bin/env python3
"""Search for flights using Duffel API."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Search for flights."""
    parser = argparse.ArgumentParser(description="Search for flights via Duffel")
    parser.add_argument("origin", help="Origin airport code (IATA, e.g., JFK)")
    parser.add_argument("destination", help="Destination airport code (IATA, e.g., LAX)")
    parser.add_argument("departure_date", help="Departure date (YYYY-MM-DD)")
    parser.add_argument("--type", choices=["one_way", "round_trip", "multi_city"],
                       default="one_way", help="Flight type")
    parser.add_argument("--return-date", help="Return date for round-trip (YYYY-MM-DD)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adult passengers")
    parser.add_argument("--cabin-class",
                       choices=["economy", "premium_economy", "business", "first"],
                       default="economy", help="Cabin class")
    parser.add_argument("--max-connections", type=int, default=2,
                       help="Maximum number of connections")

    args = parser.parse_args()

    if args.type == "round_trip" and not args.return_date:
        print("Error: --return-date required for round-trip flights", file=sys.stderr)
        sys.exit(1)

    command = "flights-mcp"

    arguments = {
        "params": {
            "type": args.type,
            "origin": args.origin,
            "destination": args.destination,
            "departure_date": args.departure_date,
            "adults": args.adults,
            "cabin_class": args.cabin_class,
            "max_connections": args.max_connections
        }
    }

    if args.return_date:
        arguments["params"]["return_date"] = args.return_date

    try:
        with MCPClient(command) as client:
            result = client.call_tool("search_flights", arguments)
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
