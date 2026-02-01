#!/usr/bin/env python3
"""Get radar and satellite imagery links."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from project .env file
import load_env  # noqa: F401
from mcp_client import MCPClient, format_json_output

parser = argparse.ArgumentParser(description="Get weather imagery")
parser.add_argument("latitude", type=float, help="Latitude (-90 to 90)")
parser.add_argument("longitude", type=float, help="Longitude (-180 to 180)")
parser.add_argument("--type", choices=["radar", "satellite"], default="radar", help="Imagery type")
args = parser.parse_args()

try:
    with MCPClient("@dangahagan/weather-mcp") as client:
        result = client.call_tool("get_weather_imagery", {"latitude": args.latitude, "longitude": args.longitude, "type": args.type})
        print(format_json_output(result))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
