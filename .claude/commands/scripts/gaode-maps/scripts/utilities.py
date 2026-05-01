#!/usr/bin/env python3
"""
Gaode Maps utility functions: weather information and distance measurement.

Usage:
    python3 utilities.py weather <city> [extensions]
    python3 utilities.py distance <origins> <destination> [type]
"""

import sys
import os
from typing import Optional

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from project .env file
import load_env  # noqa: F401

from mcp_client import MCPClient, parse_json_response, format_output


def weather_info(city: str, extensions: str = "base") -> dict:
    """
    Get weather forecast for a city.

    Args:
        city: City name or city code (e.g., "成都" or "028")
        extensions: Forecast type ("base" for live weather, "all" for 3-4 day forecast)

    Returns:
        Dict containing weather information (temp, conditions, forecast)
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY")}
    )

    try:
        client.initialize()

        arguments = {
            "city": city,
            "extensions": extensions
        }

        response = client.call_tool("maps_weather", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def distance_measure(origins: str, destination: str, distance_type: int = 1) -> dict:
    """
    Calculate distance and travel time between points.

    Args:
        origins: Starting point coordinates (e.g., "116.481488,39.990464")
        destination: Destination coordinates
        distance_type: Travel mode (0=straight-line, 1=driving, 3=walking)

    Returns:
        Dict containing distance (meters) and duration (seconds)
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY")}
    )

    try:
        client.initialize()

        arguments = {
            "origins": origins,
            "destination": destination,
            "type": str(distance_type)
        }

        response = client.call_tool("maps_distance", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def main():
    """Command-line interface for utility functions."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  utilities.py weather <city> [extensions]")
        print("  utilities.py distance <origins> <destination> [type]")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "weather":
            if len(sys.argv) < 3:
                print("Error: city required")
                sys.exit(1)

            city = sys.argv[2]
            extensions = sys.argv[3] if len(sys.argv) > 3 else "base"
            result = weather_info(city, extensions)
            print(format_output(result))

        elif command == "distance":
            if len(sys.argv) < 4:
                print("Error: origins and destination required")
                sys.exit(1)

            origins = sys.argv[2]
            destination = sys.argv[3]
            distance_type = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            result = distance_measure(origins, destination, distance_type)
            print(format_output(result))

        else:
            print(f"Error: Unknown command '{command}'")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
