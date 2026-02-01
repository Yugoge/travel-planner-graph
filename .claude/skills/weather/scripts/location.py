#!/usr/bin/env python3
"""Search for location coordinates by name."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from project .env file
import load_env  # noqa: F401
from mcp_client import MCPClient, format_json_output

parser = argparse.ArgumentParser(description="Search location coordinates")
parser.add_argument("query", help="Location name (e.g., 'Beijing, China')")
parser.add_argument("--limit", type=int, default=5, help="Max results")
args = parser.parse_args()

try:
    with MCPClient("@dangahagan/weather-mcp") as client:
        result = client.call_tool("search_location", {"query": args.query, "limit": args.limit})
        print(format_json_output(result))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
