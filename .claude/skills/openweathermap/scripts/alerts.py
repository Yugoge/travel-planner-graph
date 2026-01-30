#!/usr/bin/env python3
"""
Weather alerts script for OpenWeatherMap MCP.

Usage:
    python3 alerts.py <location>

Examples:
    python3 alerts.py "New York, US"
    python3 alerts.py "London, GB"
    python3 alerts.py "Tokyo, JP" --json
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


def get_weather_alerts(location: str) -> dict:
    """
    Get weather alerts for a location.

    Args:
        location: Location name (e.g., "New York, US" or "London, GB")

    Returns:
        dict: Parsed weather alerts data
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

        # Call alerts tool
        result = client.call_tool(
            tool_name='get-alerts',
            arguments={
                'location': location
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


def format_alerts_output(data: dict) -> str:
    """
    Format weather alerts for human-readable output.

    Args:
        data: Weather alerts data dictionary

    Returns:
        str: Formatted alerts information
    """
    lines = []

    # Location
    if 'timezone' in data:
        lines.append(f"Location Timezone: {data['timezone']}")

    # Check for alerts
    alerts = data.get('alerts', [])

    if not alerts:
        lines.append("\nNo active weather alerts for this location.")
        return '\n'.join(lines)

    lines.append(f"\n{len(alerts)} Active Weather Alert(s):")
    lines.append("=" * 60)

    for idx, alert in enumerate(alerts, 1):
        lines.append(f"\nAlert #{idx}")
        lines.append("-" * 40)

        # Sender
        if 'sender_name' in alert:
            lines.append(f"Issued by: {alert['sender_name']}")

        # Event type
        if 'event' in alert:
            lines.append(f"Event: {alert['event']}")

        # Time range
        if 'start' in alert:
            start_time = datetime.fromtimestamp(alert['start']).strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"Start: {start_time}")

        if 'end' in alert:
            end_time = datetime.fromtimestamp(alert['end']).strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"End: {end_time}")

        # Description
        if 'description' in alert:
            description = alert['description']
            lines.append(f"\nDescription:")
            # Wrap description for readability
            lines.append(description)

        # Tags
        if 'tags' in alert and alert['tags']:
            lines.append(f"\nTags: {', '.join(alert['tags'])}")

        lines.append("")

    return '\n'.join(lines)


def get_severity_summary(data: dict) -> str:
    """
    Get summary of alert severities.

    Args:
        data: Weather alerts data dictionary

    Returns:
        str: Severity summary
    """
    alerts = data.get('alerts', [])

    if not alerts:
        return "No alerts"

    # Count by severity (if available)
    from collections import Counter
    events = [alert.get('event', 'Unknown') for alert in alerts]
    event_counts = Counter(events)

    summary_parts = [f"{count} {event}" for event, count in event_counts.most_common()]
    return ', '.join(summary_parts)


def main():
    """Main entry point for alerts script."""
    parser = argparse.ArgumentParser(
        description='Get weather alerts from OpenWeatherMap',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "New York, US"
  %(prog)s "London, GB"
  %(prog)s "Tokyo, JP" --json
  %(prog)s "Miami, US" --summary
        """
    )

    parser.add_argument(
        'location',
        help='Location name (e.g., "New York, US" or "London, GB")'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output raw JSON response'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show brief summary only'
    )

    args = parser.parse_args()

    try:
        # Get alerts data
        data = get_weather_alerts(args.location)

        # Output format
        if args.json:
            print(json.dumps(data, indent=2))
        elif args.summary:
            print(get_severity_summary(data))
        else:
            print(format_alerts_output(data))

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
