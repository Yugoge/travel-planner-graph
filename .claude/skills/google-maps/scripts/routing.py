#!/usr/bin/env python3
"""
Google Maps Routes API integration via MCP.

Provides route computation functionality using the Google Maps Grounding Lite MCP server.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path for mcp_client import
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables from project .env file
import load_env  # noqa: F401
from mcp_client import MCPClient


def compute_routes(
    origin: str,
    destination: str,
    travel_mode: str = "DRIVE",
    waypoints: Optional[List[str]] = None,
    optimize_waypoints: bool = False,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute routes between origin and destination using Google Maps.

    Args:
        origin: Starting location (address or place name)
        destination: Ending location (address or place name)
        travel_mode: Travel mode - "DRIVE", "WALK", "BICYCLE", "TRANSIT" (default: "DRIVE")
        waypoints: Optional list of intermediate waypoints
        optimize_waypoints: Whether to optimize waypoint order (default: False)
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with route information including distance, duration, steps, etc.

    Example:
        result = compute_routes(
            "San Francisco, CA",
            "Los Angeles, CA",
            travel_mode="DRIVE"
        )
        print(json.dumps(result, indent=2))
    """
    api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "error": "GOOGLE_MAPS_API_KEY environment variable not set",
            "solution": "Set GOOGLE_MAPS_API_KEY environment variable with your API key"
        }

    env_vars = {"GOOGLE_MAPS_API_KEY": api_key}

    # Validate travel mode - accept both uppercase and lowercase
    mode_mapping = {
        "DRIVE": "driving",
        "DRIVING": "driving",
        "WALK": "walking",
        "WALKING": "walking",
        "BICYCLE": "bicycling",
        "BICYCLING": "bicycling",
        "TRANSIT": "transit"
    }
    travel_mode_upper = travel_mode.upper()
    if travel_mode_upper not in mode_mapping:
        return {
            "error": f"Invalid travel mode: {travel_mode}",
            "valid_modes": ["driving", "walking", "bicycling", "transit"]
        }

    mode = mode_mapping[travel_mode_upper]

    try:
        with MCPClient("@modelcontextprotocol/server-google-maps", env_vars) as client:
            # Build arguments - Google Maps Directions API format
            arguments = {
                "origin": origin,
                "destination": destination,
                "mode": mode
            }

            # Note: waypoints and optimizeWaypoints not supported by basic Directions API
            # They would require Routes API which is not in this MCP server

            # Call maps_directions tool
            result = client.call_tool("maps_directions", arguments)

            # Parse and format result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return {
                "origin": origin,
                "destination": destination,
                "travel_mode": travel_mode,
                "route": result,
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "origin": origin,
            "destination": destination,
            "travel_mode": travel_mode,
            "source": "google_maps"
        }


def format_route_result(result: Dict[str, Any]) -> str:
    """
    Format route computation result for human-readable output.

    Args:
        result: Result from compute_routes()

    Returns:
        Formatted string
    """
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    output.append(f"Route: {result.get('origin')} → {result.get('destination')}")
    output.append(f"Travel Mode: {result.get('travel_mode', 'N/A')}\n")

    route = result.get("route", {})

    # Handle different response formats
    if isinstance(route, dict):
        # Extract key information
        distance = route.get("distance", route.get("distanceMeters", "Unknown"))
        duration = route.get("duration", route.get("duration", "Unknown"))
        polyline = route.get("polyline", {})

        # Format distance
        if isinstance(distance, int):
            distance_km = distance / 1000
            output.append(f"Distance: {distance_km:.1f} km ({distance} meters)")
        else:
            output.append(f"Distance: {distance}")

        # Format duration
        if isinstance(duration, str) and duration.endswith("s"):
            # Duration in seconds format like "3600s"
            seconds = int(duration.rstrip("s"))
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if hours > 0:
                output.append(f"Duration: {hours}h {minutes}m ({seconds}s)")
            else:
                output.append(f"Duration: {minutes}m ({seconds}s)")
        else:
            output.append(f"Duration: {duration}")

        # Add polyline info if available
        if polyline:
            output.append(f"Polyline available: Yes")

        # Add steps if available
        steps = route.get("legs", [{}])[0].get("steps", []) if route.get("legs") else []
        if steps:
            output.append(f"\nRoute Steps ({len(steps)} steps):")
            for i, step in enumerate(steps[:5], 1):  # Show first 5 steps
                instruction = step.get("navigationInstruction", {}).get("instructions", "")
                step_distance = step.get("distanceMeters", 0)
                if instruction:
                    output.append(f"  {i}. {instruction} ({step_distance}m)")

            if len(steps) > 5:
                output.append(f"  ... and {len(steps) - 5} more steps")

    elif isinstance(route, str):
        output.append(f"Route: {route}")
    else:
        output.append("Route information not available in expected format")

    return "\n".join(output)


def main():
    """CLI interface for route computation."""
    if len(sys.argv) < 3:
        print("Usage: python3 routing.py <origin> <destination> [travel_mode] [waypoint1,waypoint2,...]")
        print("\nExamples:")
        print("  python3 routing.py 'San Francisco, CA' 'Los Angeles, CA'")
        print("  python3 routing.py 'New York' 'Boston' TRANSIT")
        print("  python3 routing.py 'Paris' 'Berlin' DRIVE 'Brussels,Amsterdam'")
        print("\nTravel Modes:")
        print("  DRIVE (default), WALK, BICYCLE, TRANSIT")
        print("\nEnvironment:")
        print("  GOOGLE_MAPS_API_KEY: Required Google Maps API key")
        sys.exit(1)

    origin = sys.argv[1]
    destination = sys.argv[2]
    travel_mode = sys.argv[3] if len(sys.argv) > 3 else "DRIVE"
    waypoints = None

    if len(sys.argv) > 4:
        waypoints = sys.argv[4].split(",")

    result = compute_routes(origin, destination, travel_mode, waypoints)

    # Output formatted result
    print(format_route_result(result))

    # Also output raw JSON to stderr for programmatic use
    print(json.dumps(result, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
