#!/usr/bin/env python3
"""Get detailed information about a flight offer."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Get flight offer details."""
    parser = argparse.ArgumentParser(description="Get flight offer details from Duffel")
    parser.add_argument("offer_id", help="Flight offer ID from search results")

    args = parser.parse_args()

    command = "flights-mcp"

    arguments = {
        "params": {
            "offer_id": args.offer_id
        }
    }

    try:
        with MCPClient(command) as client:
            result = client.call_tool("get_offer_details", arguments)
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
