#!/usr/bin/env python3
"""
Weather forecast script for OpenWeatherMap MCP.

Usage:
    python3 forecast.py <location> [--days <1-5>] [--units <metric|imperial>]

Examples:
    python3 forecast.py "New York, US"
    python3 forecast.py "London, GB" --days 3
    python3 forecast.py "Tokyo, JP" --units imperial --days 5
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient


def get_forecast(location: str, days: int = 5, units: str = "metric") -> dict:
    """
    Get weather forecast for a location.

    Args:
        location: Location name (e.g., "New York, US" or "London, GB")
        days: Number of days to forecast (1-5)
        units: Unit system - "metric" (Celsius) or "imperial" (Fahrenheit)

    Returns:
        dict: Parsed forecast data
    """
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        raise Exception("OPENWEATHER_API_KEY environment variable not set")

    # Initialize MCP client
    client = MCPClient(
        package='@modelcontextprotocol/server-openweathermap',
        env_vars={'OPENWEATHER_API_KEY': api_key}
    )

    try:
        # Initialize connection
        client.initialize()

        # Call forecast tool (5-day/3-hour forecast)
        result = client.call_tool(
            tool_name='get-forecast',
            arguments={
                'location': location,
                'units': units
            }
        )

        # Parse JSON response
        if isinstance(result, str):
            data = json.loads(result)
        else:
            data = result

        return data

    finally:
        client.close()


def filter_forecast_by_days(forecast_list: list, days: int) -> list:
    """
    Filter forecast data to specified number of days.

    Args:
        forecast_list: List of forecast items (3-hour intervals)
        days: Number of days to include

    Returns:
        list: Filtered forecast items
    """
    if days >= 5:
        return forecast_list

    # Calculate cutoff timestamp
    from datetime import datetime, timedelta
    now = datetime.now()
    cutoff = now + timedelta(days=days)
    cutoff_timestamp = int(cutoff.timestamp())

    # Filter items within time range
    filtered = [
        item for item in forecast_list
        if item.get('dt', 0) <= cutoff_timestamp
    ]

    return filtered


def format_forecast_output(data: dict, days: int = 5) -> str:
    """
    Format forecast data for human-readable output.

    Args:
        data: Forecast data dictionary
        days: Number of days to display

    Returns:
        str: Formatted forecast information
    """
    lines = []

    # Location
    if 'city' in data:
        city = data['city']
        location_name = city.get('name', 'Unknown')
        country = city.get('country', '')
        lines.append(f"Forecast for: {location_name}, {country}")
        lines.append("")

    # Get forecast list
    forecast_list = data.get('list', [])

    # Filter by days
    if days < 5:
        forecast_list = filter_forecast_by_days(forecast_list, days)

    if not forecast_list:
        return "No forecast data available"

    # Group by date
    daily_forecasts = {}
    for item in forecast_list:
        dt = item.get('dt')
        if not dt:
            continue

        date = datetime.fromtimestamp(dt).date()
        if date not in daily_forecasts:
            daily_forecasts[date] = []
        daily_forecasts[date].append(item)

    # Format each day
    for date in sorted(daily_forecasts.keys())[:days]:
        day_items = daily_forecasts[date]

        # Date header
        date_str = date.strftime('%A, %B %d, %Y')
        lines.append(f"=== {date_str} ===")

        # Aggregate daily data
        temps = [item['main']['temp'] for item in day_items if 'main' in item]
        conditions = [item['weather'][0]['description'] for item in day_items
                      if 'weather' in item and len(item['weather']) > 0]

        if temps:
            unit_symbol = '°C' if max(temps) < 100 else '°F'
            lines.append(f"  Temperature: {min(temps):.1f}{unit_symbol} - {max(temps):.1f}{unit_symbol}")

        if conditions:
            # Most common condition
            from collections import Counter
            most_common = Counter(conditions).most_common(1)[0][0]
            lines.append(f"  Conditions: {most_common.title()}")

        # Show time slots
        lines.append("  Hourly breakdown:")
        for item in day_items[:8]:  # Show up to 8 time slots per day
            dt = datetime.fromtimestamp(item['dt'])
            time_str = dt.strftime('%H:%M')

            temp = item['main']['temp']
            unit_symbol = '°C' if temp < 100 else '°F'

            weather_desc = ""
            if 'weather' in item and len(item['weather']) > 0:
                weather_desc = item['weather'][0]['description']

            humidity = item['main'].get('humidity', 0)
            wind_speed = item.get('wind', {}).get('speed', 0)

            lines.append(
                f"    {time_str}: {temp:.1f}{unit_symbol}, {weather_desc.title()}, "
                f"Humidity {humidity}%, Wind {wind_speed} m/s"
            )

        lines.append("")

    return '\n'.join(lines)


def main():
    """Main entry point for forecast script."""
    parser = argparse.ArgumentParser(
        description='Get weather forecast from OpenWeatherMap',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "New York, US"
  %(prog)s "London, GB" --days 3
  %(prog)s "Tokyo, JP" --units imperial --days 5
  %(prog)s "Paris, FR" --json
        """
    )

    parser.add_argument(
        'location',
        help='Location name (e.g., "New York, US" or "London, GB")'
    )

    parser.add_argument(
        '--days',
        type=int,
        choices=range(1, 6),
        default=5,
        help='Number of days to forecast (1-5, default: 5)'
    )

    parser.add_argument(
        '--units',
        choices=['metric', 'imperial'],
        default='metric',
        help='Unit system (default: metric for Celsius)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output raw JSON response'
    )

    args = parser.parse_args()

    try:
        # Get forecast data
        data = get_forecast(args.location, args.days, args.units)

        # Output format
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(format_forecast_output(data, args.days))

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
