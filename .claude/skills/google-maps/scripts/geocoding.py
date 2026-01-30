#!/usr/bin/env python3
"""
Google Maps Geocoding API integration via MCP.

Provides address-to-coordinates and coordinates-to-address conversion
using the Google Maps MCP server.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path for mcp_client import
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCPClient


def geocode(
    address: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert an address into geographic coordinates.

    Args:
        address: The address to geocode (e.g., "1600 Amphitheatre Parkway, Mountain View, CA")
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with location coordinates, formatted address, and place_id

    Example:
        result = geocode("Eiffel Tower, Paris")
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
            arguments = {"address": address}
            result = client.call_tool("maps_geocode", arguments)

            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return {
                "address": address,
                "geocoding": result,
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "address": address,
            "source": "google_maps"
        }


def reverse_geocode(
    latitude: float,
    longitude: float,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert coordinates into an address.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with formatted address and address components

    Example:
        result = reverse_geocode(48.8584, 2.2945)  # Eiffel Tower
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
            arguments = {
                "latitude": latitude,
                "longitude": longitude
            }
            result = client.call_tool("maps_reverse_geocode", arguments)

            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return {
                "latitude": latitude,
                "longitude": longitude,
                "reverse_geocoding": result,
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "latitude": latitude,
            "longitude": longitude,
            "source": "google_maps"
        }


def main():
    """CLI interface for geocoding operations."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Geocode: python3 geocoding.py geocode <address>")
        print("  Reverse: python3 geocoding.py reverse <latitude> <longitude>")
        print("\nExamples:")
        print("  python3 geocoding.py geocode 'Eiffel Tower, Paris'")
        print("  python3 geocoding.py reverse 48.8584 2.2945")
        print("\nEnvironment:")
        print("  GOOGLE_MAPS_API_KEY: Required Google Maps API key")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "geocode":
        if len(sys.argv) < 3:
            print("Error: Address required for geocoding")
            sys.exit(1)
        address = sys.argv[2]
        result = geocode(address)
        print(json.dumps(result, indent=2))

    elif command == "reverse":
        if len(sys.argv) < 4:
            print("Error: Latitude and longitude required for reverse geocoding")
            sys.exit(1)
        try:
            latitude = float(sys.argv[2])
            longitude = float(sys.argv[3])
        except ValueError:
            print("Error: Latitude and longitude must be numbers")
            sys.exit(1)
        result = reverse_geocode(latitude, longitude)
        print(json.dumps(result, indent=2))

    else:
        print(f"Error: Unknown command '{command}'")
        print("Use 'geocode' or 'reverse'")
        sys.exit(1)


if __name__ == "__main__":
    main()
