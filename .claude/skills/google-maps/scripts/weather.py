#!/usr/bin/env python3
"""
Google Maps Weather API integration via MCP.

Provides weather lookup functionality using the Google Maps Grounding Lite MCP server.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path for mcp_client import
sys.path.insert(0, os.path.dirname(__file__))
from mcp_client import MCPClient


def lookup_weather(
    location: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lookup current weather information for a location using Google Maps.

    Args:
        location: Location name or address (e.g., "San Francisco, CA", "Paris, France")
        api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)

    Returns:
        Dictionary with weather information including temperature, conditions, humidity, etc.

    Example:
        result = lookup_weather("Tokyo, Japan")
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
                "location": location
            }

            # Call lookup_weather tool
            result = client.call_tool("lookup_weather", arguments)

            # Parse and format result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return {
                "location": location,
                "weather": result,
                "source": "google_maps"
            }

    except Exception as e:
        return {
            "error": str(e),
            "location": location,
            "source": "google_maps"
        }


def format_weather_result(result: Dict[str, Any]) -> str:
    """
    Format weather lookup result for human-readable output.

    Args:
        result: Result from lookup_weather()

    Returns:
        Formatted string
    """
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    output.append(f"Weather for: {result.get('location', 'Unknown')}\n")

    weather = result.get("weather", {})

    # Handle different response formats
    if isinstance(weather, dict):
        # Temperature
        temperature = weather.get("temperature", weather.get("temp", {}))
        if isinstance(temperature, dict):
            current = temperature.get("current", temperature.get("value", "N/A"))
            unit = temperature.get("unit", "°C")
            output.append(f"Temperature: {current}{unit}")

            if "feels_like" in temperature:
                output.append(f"Feels like: {temperature['feels_like']}{unit}")
        elif temperature:
            output.append(f"Temperature: {temperature}")

        # Conditions
        conditions = weather.get("conditions", weather.get("description", ""))
        if conditions:
            output.append(f"Conditions: {conditions}")

        # Humidity
        humidity = weather.get("humidity", "")
        if humidity:
            output.append(f"Humidity: {humidity}%")

        # Wind
        wind = weather.get("wind", {})
        if isinstance(wind, dict):
            speed = wind.get("speed", "")
            direction = wind.get("direction", "")
            if speed:
                output.append(f"Wind: {speed} m/s {direction}".strip())
        elif wind:
            output.append(f"Wind: {wind}")

        # Pressure
        pressure = weather.get("pressure", "")
        if pressure:
            output.append(f"Pressure: {pressure} hPa")

        # Visibility
        visibility = weather.get("visibility", "")
        if visibility:
            output.append(f"Visibility: {visibility} m")

        # Forecast (if available)
        forecast = weather.get("forecast", [])
        if forecast and isinstance(forecast, list):
            output.append("\nForecast:")
            for i, day in enumerate(forecast[:3], 1):
                if isinstance(day, dict):
                    date = day.get("date", f"Day {i}")
                    temp = day.get("temperature", {})
                    cond = day.get("conditions", "")
                    output.append(f"  {date}: {cond}, {temp}")

    elif isinstance(weather, str):
        output.append(f"{weather}")
    else:
        output.append("Weather information not available in expected format")

    return "\n".join(output)


def main():
    """CLI interface for weather lookup."""
    if len(sys.argv) < 2:
        print("Usage: python3 weather.py <location>")
        print("\nExamples:")
        print("  python3 weather.py 'San Francisco, CA'")
        print("  python3 weather.py 'Paris, France'")
        print("  python3 weather.py 'Tokyo, Japan'")
        print("\nEnvironment:")
        print("  GOOGLE_MAPS_API_KEY: Required Google Maps API key")
        sys.exit(1)

    location = sys.argv[1]
    result = lookup_weather(location)

    # Output formatted result
    print(format_weather_result(result))

    # Also output raw JSON to stderr for programmatic use
    print(json.dumps(result, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
