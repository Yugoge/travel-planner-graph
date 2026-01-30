#!/usr/bin/env python3
"""Get station codes by station names."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Get station codes by names."""
    parser = argparse.ArgumentParser(description="Get station codes by names")
    parser.add_argument("station_names", nargs="+", help="Station names")

    args = parser.parse_args()

    server_path = "/tmp/12306-mcp/build/index.js"

    try:
        with MCPClient(server_path) as client:
            result = client.call_tool("get-station-code-by-names", {
                "station_names": args.station_names
            })
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
