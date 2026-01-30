#!/usr/bin/env python3
"""Search for train tickets on 12306."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Search for train tickets."""
    parser = argparse.ArgumentParser(description="Search for 12306 train tickets")
    parser.add_argument("from_station", help="Departure station name or code")
    parser.add_argument("to_station", help="Arrival station name or code")
    parser.add_argument("date", help="Travel date (YYYY-MM-DD)")
    parser.add_argument("--train-filter", nargs="+", help="Train type filter (e.g., G D C)")
    parser.add_argument("--earliest-time", type=int, help="Earliest departure time (0-24)")
    parser.add_argument("--latest-time", type=int, help="Latest departure time (0-24)")
    parser.add_argument("--sort", choices=["lishi", "start-time"], help="Sort method")
    parser.add_argument("--reverse", action="store_true", help="Reverse sort order")
    parser.add_argument("--limit", type=int, help="Limit number of results")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")

    args = parser.parse_args()

    server_path = "/tmp/12306-mcp/build/index.js"

    arguments = {
        "from_station": args.from_station,
        "to_station": args.to_station,
        "date": args.date
    }

    if args.train_filter:
        arguments["train_filter_flag"] = args.train_filter
    if args.earliest_time is not None:
        arguments["earliest_start_time"] = args.earliest_time
    if args.latest_time is not None:
        arguments["latest_start_time"] = args.latest_time
    if args.sort:
        arguments["sort_flag"] = args.sort
    if args.reverse:
        arguments["sort_reverse"] = True
    if args.limit:
        arguments["limit"] = args.limit
    if args.format:
        arguments["format"] = args.format

    try:
        with MCPClient(server_path) as client:
            result = client.call_tool("get-tickets", arguments)
            if args.format == "json":
                print(format_json_output(result))
            else:
                print(result if isinstance(result, str) else format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
