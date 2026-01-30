#!/usr/bin/env python3
"""
TripAdvisor Tours and Activities - Search tours, check availability, and get booking information.

Usage:
    python3 tours.py search <location> [--category <category>] [--time <time>] [--min-rating <rating>]
    python3 tours.py details <tour_id> [--date <YYYY-MM-DD>]
    python3 tours.py reviews <tour_id> [--max-reviews <n>]

Examples:
    python3 tours.py search "Paris, France" --category food-tours --time evening
    python3 tours.py details 67890 --date 2026-02-20
    python3 tours.py reviews 67890 --max-reviews 10
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path to import mcp_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import MCPClient


def search_tours(
    location: str,
    category: Optional[str] = None,
    time_of_day: Optional[str] = None,
    min_rating: float = 4.0,
    max_results: int = 20,
    price_range: Optional[str] = None,
    duration_hours: Optional[int] = None,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for tours and activities by location.

    Args:
        location: City name or address
        category: Tour type (day-trips, walking-tours, food-tours, cultural, adventure, nightlife, shows, water-activities)
        time_of_day: Preferred time (morning, afternoon, evening, full-day)
        min_rating: Minimum rating (1-5 scale)
        max_results: Maximum results to return
        price_range: Price filter (budget, moderate, luxury)
        duration_hours: Preferred duration in hours
        date: Specific date for availability check (YYYY-MM-DD)

    Returns:
        Search results dict
    """
    # Get API key from environment
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        return {
            "error": "TRIPADVISOR_API_KEY environment variable not set",
            "message": "Please set TRIPADVISOR_API_KEY in your environment"
        }

    # Initialize MCP client
    env_vars = {"TRIPADVISOR_API_KEY": api_key}

    try:
        with MCPClient("@tripadvisor/tripadvisor-mcp-server", env_vars) as client:
            # Prepare arguments
            arguments = {
                "location": location,
                "min_rating": min_rating,
                "max_results": max_results
            }

            if category:
                arguments["category"] = category
            if time_of_day:
                arguments["time_of_day"] = time_of_day
            if price_range:
                arguments["price_range"] = price_range
            if duration_hours:
                arguments["duration_hours"] = duration_hours
            if date:
                arguments["date"] = date

            # Call tool
            result = client.call_tool("search_tours", arguments)
            return result

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to search tours"
        }


def get_tour_details(
    tour_id: str,
    check_availability: bool = True,
    date: Optional[str] = None,
    include_reviews: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive details for a specific tour.

    Args:
        tour_id: TripAdvisor tour ID
        check_availability: Check real-time availability
        date: Specific date to check (YYYY-MM-DD)
        include_reviews: Include user reviews

    Returns:
        Tour details dict
    """
    # Get API key from environment
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        return {
            "error": "TRIPADVISOR_API_KEY environment variable not set",
            "message": "Please set TRIPADVISOR_API_KEY in your environment"
        }

    # Initialize MCP client
    env_vars = {"TRIPADVISOR_API_KEY": api_key}

    try:
        with MCPClient("@tripadvisor/tripadvisor-mcp-server", env_vars) as client:
            # Prepare arguments
            arguments = {
                "tour_id": tour_id,
                "check_availability": check_availability,
                "include_reviews": include_reviews
            }

            if date:
                arguments["date"] = date

            # Call tool
            result = client.call_tool("get_tour_details", arguments)
            return result

    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to get details for tour {tour_id}"
        }


def get_reviews(
    tour_id: str,
    max_reviews: int = 10,
    sort_by: str = "recent"
) -> Dict[str, Any]:
    """
    Get user reviews for a tour or attraction.

    Args:
        tour_id: TripAdvisor tour/attraction ID
        max_reviews: Maximum number of reviews to retrieve
        sort_by: Sort order (recent, helpful, rating_high, rating_low)

    Returns:
        Reviews dict
    """
    # Get API key from environment
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        return {
            "error": "TRIPADVISOR_API_KEY environment variable not set",
            "message": "Please set TRIPADVISOR_API_KEY in your environment"
        }

    # Initialize MCP client
    env_vars = {"TRIPADVISOR_API_KEY": api_key}

    try:
        with MCPClient("@tripadvisor/tripadvisor-mcp-server", env_vars) as client:
            # Call tool
            result = client.call_tool("get_reviews", {
                "id": tour_id,
                "max_reviews": max_reviews,
                "sort_by": sort_by
            })
            return result

    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to get reviews for {tour_id}"
        }


def check_booking_availability(
    tour_id: str,
    date: str,
    party_size: int = 2
) -> Dict[str, Any]:
    """
    Check real-time availability and pricing for booking.

    Args:
        tour_id: TripAdvisor tour ID
        date: Date to check (YYYY-MM-DD)
        party_size: Number of people

    Returns:
        Availability and pricing dict
    """
    # Get API key from environment
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        return {
            "error": "TRIPADVISOR_API_KEY environment variable not set",
            "message": "Please set TRIPADVISOR_API_KEY in your environment"
        }

    # Initialize MCP client
    env_vars = {"TRIPADVISOR_API_KEY": api_key}

    try:
        with MCPClient("@tripadvisor/tripadvisor-mcp-server", env_vars) as client:
            # Call tool
            result = client.call_tool("check_availability", {
                "tour_id": tour_id,
                "date": date,
                "party_size": party_size
            })
            return result

    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to check availability for tour {tour_id}"
        }


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="TripAdvisor Tours and Activities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search tours by location")
    search_parser.add_argument("location", help="City name or address")
    search_parser.add_argument("--category", help="Tour category", choices=[
        "day-trips", "walking-tours", "food-tours", "cultural", "adventure",
        "nightlife", "shows", "water-activities"
    ])
    search_parser.add_argument("--time", dest="time_of_day", help="Time of day", choices=[
        "morning", "afternoon", "evening", "full-day"
    ])
    search_parser.add_argument("--min-rating", type=float, default=4.0, help="Minimum rating (1-5)")
    search_parser.add_argument("--max-results", type=int, default=20, help="Maximum results")
    search_parser.add_argument("--price-range", choices=["budget", "moderate", "luxury"])
    search_parser.add_argument("--duration", type=int, help="Preferred duration in hours")
    search_parser.add_argument("--date", help="Check availability for date (YYYY-MM-DD)")

    # Details command
    details_parser = subparsers.add_parser("details", help="Get tour details")
    details_parser.add_argument("tour_id", help="TripAdvisor tour ID")
    details_parser.add_argument("--date", help="Check availability for date (YYYY-MM-DD)")
    details_parser.add_argument("--no-availability", action="store_true", help="Skip availability check")
    details_parser.add_argument("--no-reviews", action="store_true", help="Exclude reviews")

    # Reviews command
    reviews_parser = subparsers.add_parser("reviews", help="Get tour reviews")
    reviews_parser.add_argument("tour_id", help="TripAdvisor tour/attraction ID")
    reviews_parser.add_argument("--max-reviews", type=int, default=10, help="Maximum reviews")
    reviews_parser.add_argument("--sort-by", default="recent", choices=[
        "recent", "helpful", "rating_high", "rating_low"
    ])

    # Booking command
    booking_parser = subparsers.add_parser("booking", help="Check booking availability")
    booking_parser.add_argument("tour_id", help="TripAdvisor tour ID")
    booking_parser.add_argument("date", help="Date to check (YYYY-MM-DD)")
    booking_parser.add_argument("--party-size", type=int, default=2, help="Number of people")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "search":
        result = search_tours(
            location=args.location,
            category=args.category,
            time_of_day=args.time_of_day,
            min_rating=args.min_rating,
            max_results=args.max_results,
            price_range=args.price_range,
            duration_hours=args.duration,
            date=args.date
        )
    elif args.command == "details":
        result = get_tour_details(
            tour_id=args.tour_id,
            check_availability=not args.no_availability,
            date=args.date,
            include_reviews=not args.no_reviews
        )
    elif args.command == "reviews":
        result = get_reviews(
            tour_id=args.tour_id,
            max_reviews=args.max_reviews,
            sort_by=args.sort_by
        )
    elif args.command == "booking":
        result = check_booking_availability(
            tour_id=args.tour_id,
            date=args.date,
            party_size=args.party_size
        )

    # Output result
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
