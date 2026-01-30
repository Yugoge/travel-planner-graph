#!/usr/bin/env python3
"""Get Eventbrite event details."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output

parser = argparse.ArgumentParser(description="Get event details")
parser.add_argument("event_id", help="Event ID")
args = parser.parse_args()

try:
    with MCPClient("@mseep/eventbrite-mcp") as client:
        result = client.call_tool("get_event", {"event_id": args.event_id})
        print(format_json_output(result))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
