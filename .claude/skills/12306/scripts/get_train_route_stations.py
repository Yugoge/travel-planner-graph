#!/usr/bin/env python3
"""Get all stations along a train route."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Get train route stations."""
    parser = argparse.ArgumentParser(description="Get train route stations")
    parser.add_argument("train_code", help="Train code (e.g., G123)")
    parser.add_argument("from_station", help="Departure station name or code")
    parser.add_argument("to_station", help="Arrival station name or code")
    parser.add_argument("date", help="Travel date (YYYY-MM-DD)")

    args = parser.parse_args()

    server_path = "/tmp/12306-mcp/build/index.js"

    try:
        with MCPClient(server_path) as client:
            result = client.call_tool("get-train-route-stations", {
                "train_code": args.train_code,
                "from_station": args.from_station,
                "to_station": args.to_station,
                "date": args.date
            })
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
