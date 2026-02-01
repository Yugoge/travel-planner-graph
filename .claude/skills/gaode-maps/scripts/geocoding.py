#!/usr/bin/env python3
"""
Gaode Maps geocoding functions: address <-> coordinates conversion.

Usage:
    python3 geocoding.py geocode <address> [city]
    python3 geocoding.py regeocode <longitude,latitude> [radius]
    python3 geocoding.py ip_location [ip_address]
"""

import sys
import os
from typing import Optional

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from project .env file
import load_env  # noqa: F401

from mcp_client import MCPClient, parse_json_response, format_output


def geocode(address: str, city: Optional[str] = None) -> dict:
    """
    Convert address to coordinates (forward geocoding).

    Args:
        address: Address to geocode (e.g., "北京市朝阳区国贸")
        city: Optional city name to improve accuracy

    Returns:
        Dict containing coordinates and address components
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        # Initialize connection
        client.initialize()

        # Call geocode tool
        arguments = {"address": address}
        if city:
            arguments["city"] = city

        response = client.call_tool("maps_geo", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def regeocode(location: str, radius: int = 1000) -> dict:
    """
    Convert coordinates to address (reverse geocoding).

    Args:
        location: Coordinates in "longitude,latitude" format
        radius: Search radius in meters (default 1000, max 3000)

    Returns:
        Dict containing address and POI information
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        # Initialize connection
        client.initialize()

        # Call reverse_geocode tool
        arguments = {
            "location": location,
            "radius": str(radius)
        }

        response = client.call_tool("maps_regeocode", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def ip_location(ip: Optional[str] = None) -> dict:
    """
    Get location from IP address.

    Args:
        ip: IP address (if omitted, uses requester's IP)

    Returns:
        Dict containing province, city, and region information
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        # Initialize connection
        client.initialize()

        # Call ip_location tool
        arguments = {}
        if ip:
            arguments["ip"] = ip

        response = client.call_tool("maps_ip_location", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def main():
    """Command-line interface for geocoding functions."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  geocoding.py geocode <address> [city]")
        print("  geocoding.py regeocode <longitude,latitude> [radius]")
        print("  geocoding.py ip_location [ip_address]")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "geocode":
            if len(sys.argv) < 3:
                print("Error: address required")
                sys.exit(1)

            address = sys.argv[2]
            city = sys.argv[3] if len(sys.argv) > 3 else None
            result = geocode(address, city)
            print(format_output(result))

        elif command == "regeocode":
            if len(sys.argv) < 3:
                print("Error: coordinates required (format: longitude,latitude)")
                sys.exit(1)

            location = sys.argv[2]
            radius = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
            result = regeocode(location, radius)
            print(format_output(result))

        elif command == "ip_location":
            ip = sys.argv[2] if len(sys.argv) > 2 else None
            result = ip_location(ip)
            print(format_output(result))

        else:
            print(f"Error: Unknown command '{command}'")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
