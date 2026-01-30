#!/usr/bin/env python3
"""
Google Maps Places API integration via MCP.

Provides place search functionality using the Google Maps Grounding Lite MCP server.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path for mcp_client import
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCPClient


def search_places(
    query: str,
    location_bias: Optional[str] = None,
    max_results: int = 5,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for places using Google Maps.

    Args:
        query: Search query (e.g., "restaurants in San Francisco", "Eiffel Tower")
        location_bias: Optional location bias for results (e.g., "37.7749,-122.4194" for SF)
        max_results: Maximum number of results to return (default: 5)
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with search results including place names, addresses, ratings, etc.

    Example:
        result = search_places("coffee shops near times square", max_results=3)
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
            # Build arguments
            arguments = {
                "query": query,
                "maxResults": max_results
            }

            if location_bias:
                arguments["locationBias"] = location_bias

            # Call search_places tool
            result = client.call_tool("search_places", arguments)

            # Parse and format result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return {
                "query": query,
                "results": result,
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "query": query,
            "source": "google_maps"
        }


def format_place_result(result: Dict[str, Any]) -> str:
    """
    Format place search result for human-readable output.

    Args:
        result: Result from search_places()

    Returns:
        Formatted string
    """
    if "error" in result:
        return f"Error: {result['error']}"

    output = [f"Search: {result.get('query', 'N/A')}\n"]

    results = result.get("results", [])
    if isinstance(results, dict):
        results = [results]

    if not results:
        output.append("No results found.")
        return "\n".join(output)

    for i, place in enumerate(results, 1):
        if isinstance(place, str):
            output.append(f"{i}. {place}")
            continue

        name = place.get("name", "Unknown")
        address = place.get("address", "No address")
        rating = place.get("rating", "No rating")
        types = place.get("types", [])

        output.append(f"{i}. {name}")
        output.append(f"   Address: {address}")
        output.append(f"   Rating: {rating}")
        if types:
            output.append(f"   Types: {', '.join(types[:3])}")
        output.append("")

    return "\n".join(output)


def main():
    """CLI interface for place search."""
    if len(sys.argv) < 2:
        print("Usage: python3 places.py <query> [max_results] [location_bias]")
        print("\nExamples:")
        print("  python3 places.py 'restaurants in San Francisco'")
        print("  python3 places.py 'coffee shops' 10")
        print("  python3 places.py 'hotels in Paris' 5 '48.8566,2.3522'")
        print("\nEnvironment:")
        print("  GOOGLE_MAPS_API_KEY: Required Google Maps API key")
        sys.exit(1)

    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    location_bias = sys.argv[3] if len(sys.argv) > 3 else None

    result = search_places(query, location_bias, max_results)

    # Output formatted result
    print(format_place_result(result))

    # Also output raw JSON to stderr for programmatic use
    print(json.dumps(result, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
