#!/usr/bin/env python3
"""Get station information by telecode."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Get station information by telecode."""
    parser = argparse.ArgumentParser(description="Get station info by telecode")
    parser.add_argument("telecode", help="Station telecode (e.g., BJP for Beijing)")

    args = parser.parse_args()

    server_path = "/tmp/12306-mcp/build/index.js"

    try:
        with MCPClient(server_path) as client:
            result = client.call_tool("get-station-by-telecode", {
                "telecode": args.telecode
            })
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
