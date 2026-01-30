#!/usr/bin/env python3
"""Get marine weather conditions for coastal areas."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output

parser = argparse.ArgumentParser(description="Get marine conditions")
parser.add_argument("latitude", type=float, help="Latitude (-90 to 90)")
parser.add_argument("longitude", type=float, help="Longitude (-180 to 180)")
args = parser.parse_args()

try:
    with MCPClient("@dangahagan/weather-mcp") as client:
        result = client.call_tool("get_marine_conditions", {"latitude": args.latitude, "longitude": args.longitude})
        print(format_json_output(result))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
