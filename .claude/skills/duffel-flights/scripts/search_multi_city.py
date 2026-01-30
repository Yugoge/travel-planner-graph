#!/usr/bin/env python3
"""Search for multi-city flights using Duffel API."""

import sys
import os
import argparse
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Search for multi-city flights."""
    parser = argparse.ArgumentParser(
        description="Search for multi-city flights via Duffel",
        epilog="""
Example:
  python3 search_multi_city.py \\
    --segment JFK LAX 2026-03-01 \\
    --segment LAX SFO 2026-03-05 \\
    --segment SFO JFK 2026-03-10 \\
    --adults 2 --cabin-class business
        """
    )
    parser.add_argument("--segment", action="append", nargs=3, required=True,
                       metavar=("ORIGIN", "DEST", "DATE"),
                       help="Flight segment: origin dest date (can be repeated)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adult passengers")
    parser.add_argument("--cabin-class",
                       choices=["economy", "premium_economy", "business", "first"],
                       default="economy", help="Cabin class")
    parser.add_argument("--max-connections", type=int, default=2,
                       help="Maximum connections per segment")

    args = parser.parse_args()

    if len(args.segment) < 2:
        print("Error: At least 2 segments required for multi-city", file=sys.stderr)
        sys.exit(1)

    command = "flights-mcp"

    segments = []
    for origin, dest, date in args.segment:
        segments.append({
            "origin": origin,
            "destination": dest,
            "departure_date": date
        })

    arguments = {
        "params": {
            "segments": segments,
            "adults": args.adults,
            "cabin_class": args.cabin_class,
            "max_connections": args.max_connections
        }
    }

    try:
        with MCPClient(command) as client:
            result = client.call_tool("search_multi_city", arguments)
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
