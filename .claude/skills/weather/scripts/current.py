#!/usr/bin/env python3
"""
Current Weather Conditions Script

Get the most recent weather observation for a location (US only).

Usage:
    python3 current.py <latitude> <longitude> [options]

Examples:
    python3 current.py 40.7128 -74.0060
    python3 current.py 34.0522 -118.2437 --include-fire-weather
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output


def get_current_conditions(
    latitude: float,
    longitude: float,
    include_fire_weather: bool = False,
    include_normals: bool = False
) -> dict:
    """
    Get current weather conditions for a location.

    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        include_fire_weather: Include fire weather indices (US only)
        include_normals: Include climate normals for comparison

    Returns:
        Current conditions dictionary
    """
    arguments = {
        "latitude": latitude,
        "longitude": longitude,
        "include_fire_weather": include_fire_weather,
        "include_normals": include_normals
    }

    with MCPClient("@dangahagan/weather-mcp") as client:
        result = client.call_tool("get_current_conditions", arguments)
        return result


def main():
    parser = argparse.ArgumentParser(description="Get current weather conditions")
    parser.add_argument("latitude", type=float, help="Latitude (-90 to 90)")
    parser.add_argument("longitude", type=float, help="Longitude (-180 to 180)")
    parser.add_argument("--include-fire-weather", action="store_true",
                       help="Include fire weather indices (US only)")
    parser.add_argument("--include-normals", action="store_true",
                       help="Include climate normals")

    args = parser.parse_args()

    try:
        result = get_current_conditions(
            args.latitude,
            args.longitude,
            args.include_fire_weather,
            args.include_normals
        )
        print(format_json_output(result))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
