#!/usr/bin/env python3
"""
Google Maps Elevation API integration via MCP.

Get elevation data for locations on earth using the Google Maps MCP server.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for mcp_client import
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables from project .env file
import load_env  # noqa: F401
from mcp_client import MCPClient


def get_elevation(
    locations: List[Tuple[float, float]],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get elevation data for locations on earth.

    Args:
        locations: List of (latitude, longitude) tuples
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with elevation data for each location

    Example:
        result = get_elevation([
            (39.7391536, -104.9847034),  # Denver
            (36.1699, -115.1398)          # Las Vegas
        ])
        print(json.dumps(result, indent=2))
    """
    api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "error": "GOOGLE_MAPS_API_KEY environment variable not set",
            "solution": "Set GOOGLE_MAPS_API_KEY environment variable with your API key"
        }

    env_vars = {"GOOGLE_MAPS_API_KEY": api_key}

    try:
        with MCPClient("@modelcontextprotocol/server-google-maps", env_vars) as client:
            # Convert to format expected by API
            location_objects = [
                {"latitude": lat, "longitude": lng}
                for lat, lng in locations
            ]

            arguments = {"locations": location_objects}
            result = client.call_tool("maps_elevation", arguments)

            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return {
                "locations": locations,
                "elevation_data": result,
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "locations": locations,
            "source": "google_maps"
        }


def format_elevation(result: Dict[str, Any]) -> str:
    """
    Format elevation data for human-readable output.

    Args:
        result: Result from get_elevation()

    Returns:
        Formatted string
    """
    if "error" in result:
        return f"Error: {result['error']}"

    locations = result.get("locations", [])
    elevation_data = result.get("elevation_data", {})

    output = []
    output.append("Elevation Data")
    output.append("=" * 80)

    if isinstance(elevation_data, str):
        try:
            elevation_data = json.loads(elevation_data)
        except json.JSONDecodeError:
            output.append(f"Data: {elevation_data}")
            return "\n".join(output)

    results = elevation_data.get("results", [])

    if not results:
        output.append("No elevation data available")
        return "\n".join(output)

    output.append(f"\nTotal locations: {len(results)}\n")

    for i, elev_result in enumerate(results):
        loc = locations[i] if i < len(locations) else None
        location = elev_result.get("location", {})
        elevation = elev_result.get("elevation", 0)
        resolution = elev_result.get("resolution", 0)

        lat = location.get("lat", location.get("latitude", loc[0] if loc else "?"))
        lng = location.get("lng", location.get("longitude", loc[1] if loc else "?"))

        output.append(f"{i+1}. Location: ({lat}, {lng})")
        output.append(f"   Elevation: {elevation:.2f} meters ({elevation * 3.28084:.2f} feet)")
        output.append(f"   Resolution: {resolution:.2f} meters")
        output.append("")

    return "\n".join(output)


def main():
    """CLI interface for elevation lookup."""
    if len(sys.argv) < 2:
        print("Usage: python3 elevation.py <lat1,lng1> [lat2,lng2] [lat3,lng3] ...")
        print("\nExamples:")
        print("  python3 elevation.py 39.7391536,-104.9847034  # Denver")
        print("  python3 elevation.py 39.7391536,-104.9847034 36.1699,-115.1398  # Denver & Vegas")
        print("\nNote:")
        print("  Coordinates should be in decimal degrees")
        print("  Separate latitude and longitude with comma, no spaces")
        print("\nEnvironment:")
        print("  GOOGLE_MAPS_API_KEY: Required Google Maps API key")
        sys.exit(1)

    locations = []
    for arg in sys.argv[1:]:
        try:
            lat_str, lng_str = arg.split(",")
            lat = float(lat_str.strip())
            lng = float(lng_str.strip())
            locations.append((lat, lng))
        except ValueError:
            print(f"Error: Invalid coordinate format '{arg}'")
            print("Use: latitude,longitude (e.g., 39.7391536,-104.9847034)")
            sys.exit(1)

    result = get_elevation(locations)

    # Output formatted result
    print(format_elevation(result))

    # Also output raw JSON to stderr for programmatic use
    print(json.dumps(result, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
