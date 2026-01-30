#!/usr/bin/env python3
"""
Gaode Maps POI search functions: keyword search, nearby search, POI details.

Usage:
    python3 poi_search.py keyword <keywords> [city] [types] [page_size]
    python3 poi_search.py nearby <location> [keywords] [types] [radius] [page_size]
    python3 poi_search.py detail <poi_id>
"""

import sys
import os
from typing import Optional

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import MCPClient, parse_json_response, format_output


def poi_search_keyword(keywords: str, city: Optional[str] = None,
                       types: Optional[str] = None, page_size: int = 20) -> dict:
    """
    Search for POIs using keywords and filters.

    Args:
        keywords: Search keywords (e.g., "火锅", "hotel")
        city: City name or code (e.g., "成都" or "028")
        types: POI category codes (e.g., "050100" for restaurants)
        page_size: Results per page (default 20, max 50)

    Returns:
        Dict containing POI search results
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        client.initialize()

        arguments = {
            "keywords": keywords,
            "page_size": str(page_size)
        }

        if city:
            arguments["city"] = city
        if types:
            arguments["types"] = types

        response = client.call_tool("maps_text_search", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def poi_search_nearby(location: str, keywords: Optional[str] = None,
                      types: Optional[str] = None, radius: int = 1000,
                      page_size: int = 20) -> dict:
    """
    Search for POIs near a specific location.

    Args:
        location: Center point coordinates (e.g., "116.481488,39.990464")
        keywords: Optional filter keywords
        types: Optional POI category codes
        radius: Search radius in meters (default 1000, max 50000)
        page_size: Results per page (default 20, max 50)

    Returns:
        Dict containing nearby POI search results with distances
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        client.initialize()

        arguments = {
            "location": location,
            "radius": str(radius),
            "page_size": str(page_size)
        }

        if keywords:
            arguments["keywords"] = keywords
        if types:
            arguments["types"] = types

        response = client.call_tool("maps_around_search", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def poi_detail(poi_id: str) -> dict:
    """
    Get detailed information about a specific POI.

    Args:
        poi_id: POI ID from search results

    Returns:
        Dict containing detailed POI information (photos, hours, reviews)
    """
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        client.initialize()

        arguments = {
            "id": poi_id
        }

        response = client.call_tool("maps_search_detail", arguments)
        result = parse_json_response(response)

        return result

    finally:
        client.close()


def main():
    """Command-line interface for POI search functions."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  poi_search.py keyword <keywords> [city] [types] [page_size]")
        print("  poi_search.py nearby <location> [keywords] [types] [radius] [page_size]")
        print("  poi_search.py detail <poi_id>")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "keyword":
            if len(sys.argv) < 3:
                print("Error: keywords required")
                sys.exit(1)

            keywords = sys.argv[2]
            city = sys.argv[3] if len(sys.argv) > 3 else None
            types = sys.argv[4] if len(sys.argv) > 4 else None
            page_size = int(sys.argv[5]) if len(sys.argv) > 5 else 20
            result = poi_search_keyword(keywords, city, types, page_size)
            print(format_output(result))

        elif command == "nearby":
            if len(sys.argv) < 3:
                print("Error: location required (format: longitude,latitude)")
                sys.exit(1)

            location = sys.argv[2]
            keywords = sys.argv[3] if len(sys.argv) > 3 else None
            types = sys.argv[4] if len(sys.argv) > 4 else None
            radius = int(sys.argv[5]) if len(sys.argv) > 5 else 1000
            page_size = int(sys.argv[6]) if len(sys.argv) > 6 else 20
            result = poi_search_nearby(location, keywords, types, radius, page_size)
            print(format_output(result))

        elif command == "detail":
            if len(sys.argv) < 3:
                print("Error: poi_id required")
                sys.exit(1)

            poi_id = sys.argv[2]
            result = poi_detail(poi_id)
            print(format_output(result))

        else:
            print(f"Error: Unknown command '{command}'")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
