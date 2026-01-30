#!/usr/bin/env python3
"""Search Eventbrite events."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output

parser = argparse.ArgumentParser(description="Search Eventbrite events")
parser.add_argument("query", help="Search query (e.g., 'concerts in New York')")
parser.add_argument("--location", help="Location filter")
parser.add_argument("--category", help="Category ID")
parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
args = parser.parse_args()

try:
    arguments = {"q": args.query}
    if args.location:
        arguments["location"] = args.location
    if args.category:
        arguments["category_id"] = args.category
    if args.start_date:
        arguments["start_date"] = args.start_date
    if args.end_date:
        arguments["end_date"] = args.end_date
    
    with MCPClient("@mseep/eventbrite-mcp") as client:
        result = client.call_tool("search_events", arguments)
        print(format_json_output(result))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
