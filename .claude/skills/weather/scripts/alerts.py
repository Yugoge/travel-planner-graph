#!/usr/bin/env python3
"""
Weather Alerts Script

Get active weather alerts, watches, warnings for a location (US only).

Usage:
    python3 alerts.py <latitude> <longitude> [--all]

Examples:
    python3 alerts.py 40.7128 -74.0060
    python3 alerts.py 25.7617 -80.1918 --all
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from project .env file
import load_env  # noqa: F401
from mcp_client import MCPClient, format_json_output


def get_alerts(
    latitude: float,
    longitude: float,
    active_only: bool = True
) -> dict:
    """
    Get weather alerts for a location.

    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        active_only: Show only active alerts (default: True)

    Returns:
        Alerts dictionary
    """
    arguments = {
        "latitude": latitude,
        "longitude": longitude,
        "active_only": active_only
    }

    with MCPClient("@dangahagan/weather-mcp") as client:
        result = client.call_tool("get_alerts", arguments)
        return result


def main():
    parser = argparse.ArgumentParser(description="Get weather alerts for a location")
    parser.add_argument("latitude", type=float, help="Latitude (-90 to 90)")
    parser.add_argument("longitude", type=float, help="Longitude (-180 to 180)")
    parser.add_argument("--all", action="store_true",
                       help="Show all alerts (including inactive)")

    args = parser.parse_args()

    try:
        result = get_alerts(args.latitude, args.longitude, not args.all)
        print(format_json_output(result))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
