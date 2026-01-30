#!/usr/bin/env python3
"""
Current weather conditions script for OpenWeatherMap MCP.

Usage:
    python3 current.py <location> [--units <metric|imperial>]

Examples:
    python3 current.py "New York, US"
    python3 current.py "London, GB" --units metric
    python3 current.py "Beijing, CN"
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient


def get_current_weather(location: str, units: str = "metric") -> dict:
    """
    Get current weather conditions for a location.

    Args:
        location: Location name (e.g., "New York, US" or "London, GB")
        units: Unit system - "metric" (Celsius) or "imperial" (Fahrenheit)

    Returns:
        dict: Parsed weather data
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

        # Call current weather tool
        result = client.call_tool(
            tool_name='get-current-weather',
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


def format_weather_output(data: dict) -> str:
    """
    Format weather data for human-readable output.

    Args:
        data: Weather data dictionary

    Returns:
        str: Formatted weather information
    """
    lines = []

    # Location
    if 'name' in data:
        lines.append(f"Location: {data['name']}")
        if 'sys' in data and 'country' in data['sys']:
            lines[-1] += f", {data['sys']['country']}"

    # Current conditions
    if 'weather' in data and len(data['weather']) > 0:
        weather = data['weather'][0]
        lines.append(f"Conditions: {weather.get('description', 'Unknown').title()}")

    # Temperature
    if 'main' in data:
        main = data['main']
        temp = main.get('temp')
        feels_like = main.get('feels_like')
        unit_symbol = '°C' if temp and temp < 100 else '°F'

        if temp is not None:
            lines.append(f"Temperature: {temp}{unit_symbol}")
        if feels_like is not None:
            lines.append(f"Feels Like: {feels_like}{unit_symbol}")
        if 'temp_min' in main and 'temp_max' in main:
            lines.append(f"Range: {main['temp_min']}{unit_symbol} - {main['temp_max']}{unit_symbol}")
        if 'humidity' in main:
            lines.append(f"Humidity: {main['humidity']}%")
        if 'pressure' in main:
            lines.append(f"Pressure: {main['pressure']} hPa")

    # Wind
    if 'wind' in data:
        wind = data['wind']
        if 'speed' in wind:
            unit = 'm/s' if wind['speed'] < 50 else 'mph'
            lines.append(f"Wind: {wind['speed']} {unit}")
            if 'deg' in wind:
                lines[-1] += f" at {wind['deg']}°"

    # Visibility
    if 'visibility' in data:
        visibility_km = data['visibility'] / 1000
        lines.append(f"Visibility: {visibility_km:.1f} km")

    # Clouds
    if 'clouds' in data and 'all' in data['clouds']:
        lines.append(f"Cloud Cover: {data['clouds']['all']}%")

    # Sunrise/Sunset
    if 'sys' in data:
        sys_data = data['sys']
        if 'sunrise' in sys_data:
            from datetime import datetime
            sunrise = datetime.fromtimestamp(sys_data['sunrise']).strftime('%H:%M')
            lines.append(f"Sunrise: {sunrise}")
        if 'sunset' in sys_data:
            from datetime import datetime
            sunset = datetime.fromtimestamp(sys_data['sunset']).strftime('%H:%M')
            lines.append(f"Sunset: {sunset}")

    return '\n'.join(lines)


def main():
    """Main entry point for current weather script."""
    parser = argparse.ArgumentParser(
        description='Get current weather conditions from OpenWeatherMap',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "New York, US"
  %(prog)s "London, GB" --units metric
  %(prog)s "Tokyo, JP" --units imperial
  %(prog)s "Paris, FR" --json
        """
    )

    parser.add_argument(
        'location',
        help='Location name (e.g., "New York, US" or "London, GB")'
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
        # Get weather data
        data = get_current_weather(args.location, args.units)

        # Output format
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(format_weather_output(data))

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
