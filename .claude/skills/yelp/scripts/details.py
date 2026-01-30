#!/usr/bin/env python3
"""
Yelp Business Details Script

Get detailed information for specific businesses.
"""

import json
import os
import sys
from typing import Dict

from mcp_client import MCPClient, format_error


def get_business_details(business_id: str) -> Dict:
    """
    Get detailed information about a specific business.

    Args:
        business_id: Yelp business ID

    Returns:
        Business details including hours, photos, transactions
    """
    api_key = os.environ.get('YELP_API_KEY')
    if not api_key:
        raise ValueError("YELP_API_KEY environment variable not set")

    with MCPClient('@yelp/yelp-mcp-server', {'YELP_API_KEY': api_key}) as client:
        result = client.call_tool('get_business_details', {'business_id': business_id})
        return result


def format_hours(hours: list) -> str:
    """Format operating hours for display."""
    if not hours:
        return "Hours not available"

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    schedule = hours[0]

    if schedule.get('is_open_now'):
        status = "Currently Open"
    else:
        status = "Currently Closed"

    output = [f"Status: {status}\n"]

    open_hours = schedule.get('open', [])
    if not open_hours:
        return "Hours not available"

    # Group by day
    schedule_by_day = {}
    for slot in open_hours:
        day = slot['day']
        start = slot['start']
        end = slot['end']

        # Format time
        start_time = f"{start[:2]}:{start[2:]}"
        end_time = f"{end[:2]}:{end[2:]}"

        if day not in schedule_by_day:
            schedule_by_day[day] = []
        schedule_by_day[day].append(f"{start_time}-{end_time}")

    for day_num in range(7):
        day_name = days[day_num]
        if day_num in schedule_by_day:
            times = ', '.join(schedule_by_day[day_num])
            output.append(f"{day_name}: {times}")
        else:
            output.append(f"{day_name}: Closed")

    return '\n'.join(output)


def format_business_details(business: Dict) -> str:
    """Format complete business details for display."""
    name = business.get('name', 'N/A')
    rating = business.get('rating', 'N/A')
    review_count = business.get('review_count', 0)
    price = business.get('price', 'N/A')

    categories = business.get('categories', [])
    category_names = ', '.join([cat.get('title', '') for cat in categories])

    location = business.get('location', {})
    address_parts = [
        location.get('address1', ''),
        location.get('city', ''),
        location.get('state', ''),
        location.get('zip_code', '')
    ]
    address = ', '.join([p for p in address_parts if p])

    coordinates = business.get('coordinates', {})
    lat = coordinates.get('latitude', 'N/A')
    lon = coordinates.get('longitude', 'N/A')

    url = business.get('url', '')
    phone = business.get('phone', 'N/A')

    # Transactions
    transactions = business.get('transactions', [])
    transaction_str = ', '.join(transactions) if transactions else 'None'

    # Photos
    photos = business.get('photos', [])
    photo_count = len(photos)

    # Hours
    hours = business.get('hours', [])
    hours_str = format_hours(hours)

    output = f"""
{name}
{'=' * len(name)}

Rating: {rating}★ ({review_count} reviews)
Price: {price}
Categories: {category_names}

Address:
{address}

Coordinates: {lat}, {lon}

Contact:
Phone: {phone}
Website: {url}

Transactions: {transaction_str}
Photos: {photo_count} available

Operating Hours:
{hours_str}
"""
    return output.strip()


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: python3 details.py <business_id>")
        print("\nExample:")
        print("  python3 details.py gary-danko-san-francisco")
        print("\nNote: Business ID can be found from search results")
        sys.exit(1)

    business_id = sys.argv[1]

    try:
        result = get_business_details(business_id)
        print(format_business_details(result))

    except Exception as e:
        print(format_error(e), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
