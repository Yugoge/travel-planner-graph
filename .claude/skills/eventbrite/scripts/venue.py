#!/usr/bin/env python3
"""Get Eventbrite venue details."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output

parser = argparse.ArgumentParser(description="Get venue details")
parser.add_argument("venue_id", help="Venue ID")
args = parser.parse_args()

try:
    with MCPClient("@mseep/eventbrite-mcp") as client:
        result = client.call_tool("get_venue", {"venue_id": args.venue_id})
        print(format_json_output(result))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
