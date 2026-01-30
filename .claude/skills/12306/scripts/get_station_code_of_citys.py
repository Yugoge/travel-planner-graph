#!/usr/bin/env python3
"""Get all station codes in specified cities."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Get station codes of cities."""
    parser = argparse.ArgumentParser(description="Get station codes in cities")
    parser.add_argument("city_names", nargs="+", help="City names")

    args = parser.parse_args()

    server_path = "/tmp/12306-mcp/build/index.js"

    try:
        with MCPClient(server_path) as client:
            result = client.call_tool("get-station-code-of-citys", {
                "city_names": args.city_names
            })
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
