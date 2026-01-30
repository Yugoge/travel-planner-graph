#!/usr/bin/env python3
"""
Gaode Maps routing functions: driving, transit, walking, cycling routes.

Usage:
    python3 routing.py driving <origin> <destination> [strategy]
    python3 routing.py transit <origin> <destination> [city] [dest_city] [strategy]
    python3 routing.py walking <origin> <destination>
    python3 routing.py cycling <origin> <destination>
"""

import sys
import os
from typing import Optional

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import MCPClient, parse_json_response, format_output


def driving_route(origin: str, destination: str, strategy: int = 0) -> dict:
    """
    Plan driving route with real-time traffic.

    Args:
        origin: Starting point (address or coordinates)
        destination: Destination (address or coordinates)
        strategy: Route strategy (0=fastest, 1=avoid highways, 2=avoid tolls, 3=shortest, 4=avoid congestion)

    Returns:
        Dict containing route details (distance, duration, tolls, directions)
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        client.initialize()

        arguments = {
            "origin": origin,
            "destination": destination,
            "strategy": str(strategy)
        }

        response = client.call_tool("maps_direction_driving", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def transit_route(origin: str, destination: str, city: Optional[str] = None,
                  cityd: Optional[str] = None, strategy: int = 3) -> dict:
    """
    Plan public transportation route (bus, subway, trains).

    Args:
        origin: Starting point (address or coordinates)
        destination: Destination (address or coordinates)
        city: Origin city name or code
        cityd: Destination city name or code (for inter-city)
        strategy: Route strategy (0=fastest, 1=fewest transfers, 2=shortest walk, 3=most comfortable, 5=avoid subway)

    Returns:
        Dict containing transit route details (segments, duration, cost)
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        client.initialize()

        arguments = {
            "origin": origin,
            "destination": destination,
            "strategy": str(strategy)
        }

        if city:
            arguments["city"] = city
        if cityd:
            arguments["cityd"] = cityd

        response = client.call_tool("maps_direction_transit_integrated", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def walking_route(origin: str, destination: str) -> dict:
    """
    Plan walking route.

    Args:
        origin: Starting point (address or coordinates)
        destination: Destination (address or coordinates)

    Returns:
        Dict containing walking route details (distance, duration, directions)
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        client.initialize()

        arguments = {
            "origin": origin,
            "destination": destination
        }

        response = client.call_tool("maps_direction_walking", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def cycling_route(origin: str, destination: str) -> dict:
    """
    Plan cycling route.

    Args:
        origin: Starting point (address or coordinates)
        destination: Destination (address or coordinates)

    Returns:
        Dict containing cycling route details (distance, duration, directions)
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        client.initialize()

        arguments = {
            "origin": origin,
            "destination": destination
        }

        response = client.call_tool("maps_bicycling", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def main():
    """Command-line interface for routing functions."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  routing.py driving <origin> <destination> [strategy]")
        print("  routing.py transit <origin> <destination> [city] [dest_city] [strategy]")
        print("  routing.py walking <origin> <destination>")
        print("  routing.py cycling <origin> <destination>")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "driving":
            if len(sys.argv) < 4:
                print("Error: origin and destination required")
                sys.exit(1)

            origin = sys.argv[2]
            destination = sys.argv[3]
            strategy = int(sys.argv[4]) if len(sys.argv) > 4 else 0
            result = driving_route(origin, destination, strategy)
            print(format_output(result))

        elif command == "transit":
            if len(sys.argv) < 4:
                print("Error: origin and destination required")
                sys.exit(1)

            origin = sys.argv[2]
            destination = sys.argv[3]
            city = sys.argv[4] if len(sys.argv) > 4 else None
            cityd = sys.argv[5] if len(sys.argv) > 5 else None
            strategy = int(sys.argv[6]) if len(sys.argv) > 6 else 3
            result = transit_route(origin, destination, city, cityd, strategy)
            print(format_output(result))

        elif command == "walking":
            if len(sys.argv) < 4:
                print("Error: origin and destination required")
                sys.exit(1)

            origin = sys.argv[2]
            destination = sys.argv[3]
            result = walking_route(origin, destination)
            print(format_output(result))

        elif command == "cycling":
            if len(sys.argv) < 4:
                print("Error: origin and destination required")
                sys.exit(1)

            origin = sys.argv[2]
            destination = sys.argv[3]
            result = cycling_route(origin, destination)
            print(format_output(result))

        else:
            print(f"Error: Unknown command '{command}'")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
