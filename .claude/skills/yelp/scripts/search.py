#!/usr/bin/env python3
"""
Yelp Restaurant Search Script

Search restaurants using Yelp Fusion AI MCP server.
"""

import json
import os
import sys
from typing import Dict, List, Optional

from mcp_client import MCPClient, format_error


def search_businesses(
    query: str,
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[int] = None,
    categories: Optional[str] = None,
    price: Optional[str] = None,
    open_now: Optional[bool] = None,
    limit: int = 20
) -> Dict:
    """
    Search for restaurants and businesses.

    Args:
        query: Natural language search query or structured filters
        location: City, address, or coordinates (optional if lat/lon provided)
        latitude: Latitude for geographic search
        longitude: Longitude for geographic search
        radius: Search radius in meters (max 40000)
        categories: Comma-separated category aliases
        price: Price levels (1, 2, 3, 4 for $, $$, $$$, $$$$)
        open_now: Filter to currently open businesses
        limit: Number of results (default 20, max 50)

    Returns:
        Search results with businesses list
    """
    api_key = os.environ.get('YELP_API_KEY')
    if not api_key:
        raise ValueError("YELP_API_KEY environment variable not set")

    # Build arguments
    arguments = {'query': query, 'limit': limit}

    if location:
        arguments['location'] = location
    if latitude is not None:
        arguments['latitude'] = latitude
    if longitude is not None:
        arguments['longitude'] = longitude
    if radius is not None:
        arguments['radius'] = radius
    if categories:
        arguments['categories'] = categories
    if price:
        arguments['price'] = price
    if open_now is not None:
        arguments['open_now'] = open_now

    # Call MCP server
    with MCPClient('@yelp/yelp-mcp-server', {'YELP_API_KEY': api_key}) as client:
        result = client.call_tool('search_businesses', arguments)
        return result


def get_business_details(business_id: str) -> Dict:
    """
    Get detailed information about a specific business.

    Args:
        business_id: Yelp business ID

    Returns:
        Business details
    """
    api_key = os.environ.get('YELP_API_KEY')
    if not api_key:
        raise ValueError("YELP_API_KEY environment variable not set")

    with MCPClient('@yelp/yelp-mcp-server', {'YELP_API_KEY': api_key}) as client:
        result = client.call_tool('get_business_details', {'business_id': business_id})
        return result


def search_by_category(
    category: str,
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[int] = None,
    price: Optional[str] = None,
    open_now: Optional[bool] = None,
    limit: int = 20
) -> Dict:
    """
    Search restaurants by cuisine category.

    Args:
        category: Category alias (e.g., 'italian', 'vegetarian')
        location: City, address, or coordinates
        latitude: Latitude for geographic search
        longitude: Longitude for geographic search
        radius: Search radius in meters
        price: Price levels (1, 2, 3, 4)
        open_now: Filter to currently open
        limit: Number of results

    Returns:
        Search results with businesses list
    """
    api_key = os.environ.get('YELP_API_KEY')
    if not api_key:
        raise ValueError("YELP_API_KEY environment variable not set")

    arguments = {'category': category, 'limit': limit}

    if location:
        arguments['location'] = location
    if latitude is not None:
        arguments['latitude'] = latitude
    if longitude is not None:
        arguments['longitude'] = longitude
    if radius is not None:
        arguments['radius'] = radius
    if price:
        arguments['price'] = price
    if open_now is not None:
        arguments['open_now'] = open_now

    with MCPClient('@yelp/yelp-mcp-server', {'YELP_API_KEY': api_key}) as client:
        result = client.call_tool('search_by_category', arguments)
        return result


def format_business(business: Dict) -> str:
    """Format business information for display."""
    name = business.get('name', 'N/A')
    rating = business.get('rating', 'N/A')
    review_count = business.get('review_count', 0)
    price = business.get('price', 'N/A')

    categories = business.get('categories', [])
    category_names = ', '.join([cat.get('title', '') for cat in categories[:3]])

    location = business.get('location', {})
    address = location.get('address1', '')
    city = location.get('city', '')

    url = business.get('url', '')
    phone = business.get('phone', '')

    # Operating hours
    hours = business.get('hours', [])
    is_open = hours[0].get('is_open_now', False) if hours else False
    open_status = "Open" if is_open else "Closed"

    output = f"""
{name}
{'=' * len(name)}
Rating: {rating}★ ({review_count} reviews)
Price: {price}
Categories: {category_names}
Status: {open_status}

Address: {address}, {city}
Phone: {phone}
URL: {url}
"""
    return output.strip()


def format_search_results(results: Dict) -> str:
    """Format search results for display."""
    businesses = results.get('businesses', [])
    total = results.get('total', 0)

    if not businesses:
        return "No restaurants found."

    output = [f"Found {len(businesses)} of {total} restaurants:\n"]

    for i, business in enumerate(businesses, 1):
        output.append(f"{i}. {business.get('name', 'N/A')}")
        output.append(f"   Rating: {business.get('rating', 'N/A')}★ ({business.get('review_count', 0)} reviews)")
        output.append(f"   Price: {business.get('price', 'N/A')}")

        categories = business.get('categories', [])
        if categories:
            category_names = ', '.join([cat.get('title', '') for cat in categories[:2]])
            output.append(f"   Categories: {category_names}")

        location = business.get('location', {})
        address = location.get('address1', '')
        city = location.get('city', '')
        if address:
            output.append(f"   Address: {address}, {city}")

        output.append(f"   ID: {business.get('id', '')}")
        output.append("")

    return "\n".join(output)


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Search: python3 search.py search <query> [location] [--lat=<lat>] [--lon=<lon>] [--radius=<meters>] [--categories=<categories>] [--price=<1,2,3,4>] [--open-now] [--limit=<num>]")
        print("  Details: python3 search.py details <business_id>")
        print("  Category: python3 search.py category <category> [location] [--lat=<lat>] [--lon=<lon>] [--radius=<meters>] [--price=<1,2,3,4>] [--open-now] [--limit=<num>]")
        print("\nExamples:")
        print("  python3 search.py search 'best italian restaurants' 'San Francisco, CA' --price=2,3 --limit=10")
        print("  python3 search.py search 'breakfast near me' --lat=37.7749 --lon=-122.4194 --radius=1000")
        print("  python3 search.py category vegetarian 'New York, NY' --price=1,2 --open-now")
        print("  python3 search.py details gary-danko-san-francisco")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'search':
            if len(sys.argv) < 3:
                print("Error: Query required")
                sys.exit(1)

            query = sys.argv[2]
            location = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None

            # Parse optional arguments
            kwargs = {}
            for arg in sys.argv[3:] if location is None else sys.argv[4:]:
                if arg.startswith('--'):
                    key, value = arg[2:].split('=', 1) if '=' in arg else (arg[2:], True)

                    if key == 'lat':
                        kwargs['latitude'] = float(value)
                    elif key == 'lon':
                        kwargs['longitude'] = float(value)
                    elif key == 'radius':
                        kwargs['radius'] = int(value)
                    elif key == 'categories':
                        kwargs['categories'] = value
                    elif key == 'price':
                        kwargs['price'] = value
                    elif key == 'open-now':
                        kwargs['open_now'] = True
                    elif key == 'limit':
                        kwargs['limit'] = int(value)

            result = search_businesses(query, location, **kwargs)
            print(format_search_results(result))

        elif command == 'details':
            if len(sys.argv) < 3:
                print("Error: Business ID required")
                sys.exit(1)

            business_id = sys.argv[2]
            result = get_business_details(business_id)
            print(format_business(result))

        elif command == 'category':
            if len(sys.argv) < 3:
                print("Error: Category required")
                sys.exit(1)

            category = sys.argv[2]
            location = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None

            # Parse optional arguments
            kwargs = {}
            for arg in sys.argv[3:] if location is None else sys.argv[4:]:
                if arg.startswith('--'):
                    key, value = arg[2:].split('=', 1) if '=' in arg else (arg[2:], True)

                    if key == 'lat':
                        kwargs['latitude'] = float(value)
                    elif key == 'lon':
                        kwargs['longitude'] = float(value)
                    elif key == 'radius':
                        kwargs['radius'] = int(value)
                    elif key == 'price':
                        kwargs['price'] = value
                    elif key == 'open-now':
                        kwargs['open_now'] = True
                    elif key == 'limit':
                        kwargs['limit'] = int(value)

            result = search_by_category(category, location, **kwargs)
            print(format_search_results(result))

        else:
            print(f"Error: Unknown command '{command}'")
            sys.exit(1)

    except Exception as e:
        print(format_error(e), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
