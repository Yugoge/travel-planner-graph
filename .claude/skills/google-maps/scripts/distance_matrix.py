#!/usr/bin/env python3
"""
Google Maps Distance Matrix API integration via MCP.

Calculate travel distance and time for multiple origins and destinations
using the Google Maps MCP server.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path for mcp_client import
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCPClient


def calculate_distance_matrix(
    origins: List[str],
    destinations: List[str],
    mode: str = "driving",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate travel distance and time for multiple origins and destinations.

    Args:
        origins: List of origin addresses or coordinates
        destinations: List of destination addresses or coordinates
        mode: Travel mode - "driving", "walking", "bicycling", "transit" (default: "driving")
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with distance matrix including distances and durations
        between each origin-destination pair

    Example:
        result = calculate_distance_matrix(
            origins=["San Francisco, CA", "Los Angeles, CA"],
            destinations=["Seattle, WA", "Portland, OR"],
            mode="driving"
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

    # Validate mode
    valid_modes = ["driving", "walking", "bicycling", "transit"]
    mode_lower = mode.lower()
    if mode_lower not in valid_modes:
        return {
            "error": f"Invalid travel mode: {mode}",
            "valid_modes": valid_modes
        }

    try:
        with MCPClient("@modelcontextprotocol/server-google-maps", env_vars) as client:
            arguments = {
                "origins": origins,
                "destinations": destinations,
                "mode": mode_lower
            }
            result = client.call_tool("maps_distance_matrix", arguments)

            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return {
                "origins": origins,
                "destinations": destinations,
                "mode": mode_lower,
                "matrix": result,
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "origins": origins,
            "destinations": destinations,
            "mode": mode_lower,
            "source": "google_maps"
        }


def format_distance_matrix(result: Dict[str, Any]) -> str:
    """
    Format distance matrix for human-readable output.

    Args:
        result: Result from calculate_distance_matrix()

    Returns:
        Formatted string
    """
    if "error" in result:
        return f"Error: {result['error']}"

    origins = result.get("origins", [])
    destinations = result.get("destinations", [])
    mode = result.get("mode", "unknown")
    matrix = result.get("matrix", {})

    output = []
    output.append(f"Distance Matrix (Mode: {mode})")
    output.append("=" * 80)

    if isinstance(matrix, str):
        try:
            matrix = json.loads(matrix)
        except json.JSONDecodeError:
            output.append(f"Matrix: {matrix}")
            return "\n".join(output)

    # Extract data
    origin_addresses = matrix.get("origin_addresses", origins)
    dest_addresses = matrix.get("destination_addresses", destinations)
    results = matrix.get("results", [])

    # Display as table
    output.append(f"\nOrigins ({len(origin_addresses)}):")
    for i, addr in enumerate(origin_addresses, 1):
        output.append(f"  {i}. {addr}")

    output.append(f"\nDestinations ({len(dest_addresses)}):")
    for i, addr in enumerate(dest_addresses, 1):
        output.append(f"  {i}. {addr}")

    output.append("\nDistances and Durations:")
    output.append("-" * 80)

    for i, row in enumerate(results):
        origin_addr = origin_addresses[i] if i < len(origin_addresses) else f"Origin {i+1}"
        output.append(f"\nFrom: {origin_addr}")

        elements = row.get("elements", [])
        for j, element in enumerate(elements):
            dest_addr = dest_addresses[j] if j < len(dest_addresses) else f"Destination {j+1}"
            status = element.get("status", "UNKNOWN")

            if status == "OK":
                distance = element.get("distance", {})
                duration = element.get("duration", {})

                dist_text = distance.get("text", "?")
                dist_value = distance.get("value", 0)
                dur_text = duration.get("text", "?")
                dur_value = duration.get("value", 0)

                output.append(f"  To {dest_addr}:")
                output.append(f"    Distance: {dist_text} ({dist_value} meters)")
                output.append(f"    Duration: {dur_text} ({dur_value} seconds)")
            else:
                output.append(f"  To {dest_addr}: {status}")

    return "\n".join(output)


def main():
    """CLI interface for distance matrix calculation."""
    if len(sys.argv) < 3:
        print("Usage: python3 distance_matrix.py <origins> <destinations> [mode]")
        print("\nArguments:")
        print("  origins:      Comma-separated list of origin addresses")
        print("  destinations: Comma-separated list of destination addresses")
        print("  mode:         driving (default), walking, bicycling, transit")
        print("\nExamples:")
        print("  python3 distance_matrix.py 'San Francisco,Los Angeles' 'Seattle,Portland'")
        print("  python3 distance_matrix.py 'New York' 'Boston,Philadelphia' transit")
        print("\nEnvironment:")
        print("  GOOGLE_MAPS_API_KEY: Required Google Maps API key")
        sys.exit(1)

    origins = [o.strip() for o in sys.argv[1].split(",")]
    destinations = [d.strip() for d in sys.argv[2].split(",")]
    mode = sys.argv[3] if len(sys.argv) > 3 else "driving"

    result = calculate_distance_matrix(origins, destinations, mode)

    # Output formatted result
    print(format_distance_matrix(result))

    # Also output raw JSON to stderr for programmatic use
    print(json.dumps(result, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
