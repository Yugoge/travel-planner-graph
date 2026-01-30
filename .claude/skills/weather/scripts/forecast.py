#!/usr/bin/env python3
"""
Weather Forecast Script

Get future weather forecast for a location with global coverage.

Usage:
    python3 forecast.py <latitude> <longitude> [options]

Examples:
    python3 forecast.py 39.9042 116.4074
    python3 forecast.py 40.7128 -74.0060 --days 7 --granularity hourly
    python3 forecast.py 51.5074 -0.1278 --include-normals
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output


def get_forecast(
    latitude: float,
    longitude: float,
    days: int = 7,
    granularity: str = "daily",
    include_precipitation: bool = True,
    include_severe: bool = False,
    include_normals: bool = False,
    source: str = "auto"
) -> dict:
    """
    Get weather forecast for a location.

    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        days: Number of days (1-16 for global, 1-7 for US NOAA)
        granularity: "daily" or "hourly"
        include_precipitation: Include precipitation probability
        include_severe: Include severe weather probabilities (US only)
        include_normals: Include climate normals for comparison
        source: "auto", "noaa" (US only), or "openmeteo" (global)

    Returns:
        Forecast data dictionary
    """
    arguments = {
        "latitude": latitude,
        "longitude": longitude,
        "days": days,
        "granularity": granularity,
        "include_precipitation_probability": include_precipitation,
        "include_severe_weather": include_severe,
        "include_normals": include_normals,
        "source": source
    }

    with MCPClient("@dangahagan/weather-mcp") as client:
        result = client.call_tool("get_forecast", arguments)
        return result


def main():
    parser = argparse.ArgumentParser(description="Get weather forecast for a location")
    parser.add_argument("latitude", type=float, help="Latitude (-90 to 90)")
    parser.add_argument("longitude", type=float, help="Longitude (-180 to 180)")
    parser.add_argument("--days", type=int, default=7, help="Number of days (default: 7)")
    parser.add_argument("--granularity", choices=["daily", "hourly"], default="daily",
                       help="Forecast granularity (default: daily)")
    parser.add_argument("--include-precipitation", action="store_true", default=True,
                       help="Include precipitation probability")
    parser.add_argument("--include-severe", action="store_true",
                       help="Include severe weather probabilities (US only)")
    parser.add_argument("--include-normals", action="store_true",
                       help="Include climate normals")
    parser.add_argument("--source", choices=["auto", "noaa", "openmeteo"], default="auto",
                       help="Data source (default: auto)")

    args = parser.parse_args()

    try:
        result = get_forecast(
            args.latitude,
            args.longitude,
            args.days,
            args.granularity,
            args.include_precipitation,
            args.include_severe,
            args.include_normals,
            args.source
        )
        print(format_json_output(result))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
