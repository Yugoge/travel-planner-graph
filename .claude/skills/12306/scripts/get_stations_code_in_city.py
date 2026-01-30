#!/usr/bin/env python3
"""Get all stations within a single city."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Get stations in a city."""
    parser = argparse.ArgumentParser(description="Get stations in a city")
    parser.add_argument("city_name", help="City name")

    args = parser.parse_args()

    server_path = "/tmp/12306-mcp/build/index.js"

    try:
        with MCPClient(server_path) as client:
            result = client.call_tool("get-stations-code-in-city", {
                "city_name": args.city_name
            })
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
