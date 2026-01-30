#!/usr/bin/env python3
"""Conversational Yelp business agent for restaurant and business queries."""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_client import MCPClient, format_json_output


def main():
    """Query Yelp via intelligent conversational agent."""
    parser = argparse.ArgumentParser(
        description="Intelligent Yelp agent for business queries",
        epilog="""
Examples:
  # Basic search
  python3 yelp_agent.py "Find Italian restaurants in San Francisco"

  # With location coordinates
  python3 yelp_agent.py "Best coffee shops nearby" --lat 37.7749 --lon -122.4194

  # Follow-up question (use chat_id from previous response)
  python3 yelp_agent.py "What are their hours?" --chat-id abc123

  # Complex query
  python3 yelp_agent.py "Plan a progressive dinner in Mission District"

  # Booking
  python3 yelp_agent.py "Book table for 2 at Mama Nachas tonight at 7pm"
        """
    )
    parser.add_argument("query", help="Natural language query about businesses")
    parser.add_argument("--lat", "--latitude", type=float, dest="latitude",
                       help="Search latitude for precise location")
    parser.add_argument("--lon", "--longitude", type=float, dest="longitude",
                       help="Search longitude for precise location")
    parser.add_argument("--chat-id", dest="chat_id",
                       help="Previous chat ID for follow-up questions")

    args = parser.parse_args()

    command = "mcp-yelp-agent"

    arguments = {
        "natural_language_query": args.query
    }

    if args.latitude is not None and args.longitude is not None:
        arguments["search_latitude"] = args.latitude
        arguments["search_longitude"] = args.longitude

    if args.chat_id:
        arguments["chat_id"] = args.chat_id

    try:
        with MCPClient(command) as client:
            result = client.call_tool("yelp_agent", arguments)
            print(format_json_output(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
