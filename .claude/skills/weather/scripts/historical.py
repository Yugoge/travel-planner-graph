#!/usr/bin/env python3
"""
Historical Weather Script

Get historical weather data for specific past dates.

Usage:
    python3 historical.py <latitude> <longitude> <start_date> [end_date]

Examples:
    python3 historical.py 40.7128 -74.0060 2024-01-15
    python3 historical.py 51.5074 -0.1278 2024-01-01 2024-01-07
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from project .env file
import load_env  # noqa: F401
from mcp_client import MCPClient, format_json_output


def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str = None
) -> dict:
    """
    Get historical weather data for a date range.

    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), optional

    Returns:
        Historical weather dictionary
    """
    arguments = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date
    }
    if end_date:
        arguments["end_date"] = end_date

    with MCPClient("@dangahagan/weather-mcp") as client:
        result = client.call_tool("get_historical_weather", arguments)
        return result


def main():
    parser = argparse.ArgumentParser(description="Get historical weather data")
    parser.add_argument("latitude", type=float, help="Latitude (-90 to 90)")
    parser.add_argument("longitude", type=float, help="Longitude (-180 to 180)")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", nargs="?", help="End date (YYYY-MM-DD), optional")

    args = parser.parse_args()

    try:
        result = get_historical_weather(
            args.latitude,
            args.longitude,
            args.start_date,
            args.end_date
        )
        print(format_json_output(result))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
