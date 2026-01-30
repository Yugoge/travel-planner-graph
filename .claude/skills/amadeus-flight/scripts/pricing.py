#!/usr/bin/env python3
"""
Flight Pricing Script for Amadeus Flight MCP

Provides flight pricing and price analysis functionality via MCP server.
Supports price analysis, predictions, and detailed pricing breakdowns.

Usage:
    python3 pricing.py price_analysis <origin> <destination> <departure_date>
    python3 pricing.py get_price <flight_offer_id>

Examples:
    # Get price analysis for route
    python3 pricing.py price_analysis PEK CDG 2026-03-15

    # Get detailed pricing for specific offer
    python3 pricing.py get_price ABC123XYZ
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for mcp_client import
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient, retry_with_backoff


def price_analysis(
    origin: str,
    destination: str,
    departure_date: str
) -> dict:
    """
    Get price analysis and trends for a route

    Args:
        origin: Origin airport IATA code (e.g., 'PEK')
        destination: Destination airport IATA code (e.g., 'CDG')
        departure_date: Departure date in ISO format (YYYY-MM-DD)

    Returns:
        Price analysis with trends and predictions
    """
    client = MCPClient()

    try:
        # Initialize client
        def init():
            client.initialize()

        retry_with_backoff(init)

        # Get price analysis
        def analyze():
            return client.call_tool("price_analysis", {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date
            })

        result = retry_with_backoff(analyze)

        return result

    finally:
        client.close()


def get_flight_price(flight_offer_id: str) -> dict:
    """
    Get detailed pricing for a specific flight offer

    Args:
        flight_offer_id: Flight offer ID from search results

    Returns:
        Detailed pricing breakdown including taxes and fees
    """
    client = MCPClient()

    try:
        # Initialize client
        def init():
            client.initialize()

        retry_with_backoff(init)

        # Get pricing
        def get_price():
            return client.call_tool("get_flight_price", {
                "flightOfferId": flight_offer_id
            })

        result = retry_with_backoff(get_price)

        return result

    finally:
        client.close()


def format_price_analysis(results: dict) -> str:
    """
    Format price analysis results for human-readable output

    Args:
        results: Raw price analysis results from MCP

    Returns:
        Formatted string output
    """
    if not results:
        return "No price analysis available"

    output_lines = []

    # Extract data
    data = results.get('data', [])
    if not data:
        return "No price analysis available"

    analysis = data[0] if isinstance(data, list) else data

    output_lines.append("Price Analysis:")
    output_lines.append("")

    # Current prices
    if 'currentPrice' in analysis:
        current = analysis['currentPrice']
        output_lines.append(f"Current Price Range:")
        output_lines.append(f"  Minimum: {current.get('min', 'N/A')} {current.get('currency', 'USD')}")
        output_lines.append(f"  Average: {current.get('avg', 'N/A')} {current.get('currency', 'USD')}")
        output_lines.append(f"  Maximum: {current.get('max', 'N/A')} {current.get('currency', 'USD')}")
        output_lines.append("")

    # Price trend
    if 'trend' in analysis:
        trend = analysis['trend']
        direction = trend.get('direction', 'stable')
        change = trend.get('change', 0)
        output_lines.append(f"Price Trend: {direction.upper()} ({change:+.1f}%)")
        output_lines.append("")

    # Prediction
    if 'prediction' in analysis:
        prediction = analysis['prediction']
        output_lines.append("Price Prediction:")
        output_lines.append(f"  Best time to book: {prediction.get('bestTimeToBook', 'N/A')}")
        output_lines.append(f"  Expected price: {prediction.get('expectedPrice', 'N/A')}")
        output_lines.append("")

    return "\n".join(output_lines)


def format_flight_price(results: dict) -> str:
    """
    Format flight price details for human-readable output

    Args:
        results: Raw flight price results from MCP

    Returns:
        Formatted string output
    """
    if not results:
        return "No pricing details available"

    output_lines = []

    # Extract data
    data = results.get('data', {})
    if not data:
        return "No pricing details available"

    output_lines.append("Flight Price Details:")
    output_lines.append("")

    # Base price
    price = data.get('price', {})
    output_lines.append(f"Base Fare: {price.get('base', 'N/A')} {price.get('currency', 'USD')}")

    # Fees breakdown
    fees = price.get('fees', [])
    if fees:
        output_lines.append("Fees:")
        for fee in fees:
            output_lines.append(f"  {fee.get('type', 'N/A')}: {fee.get('amount', 'N/A')}")

    # Taxes
    taxes = price.get('taxes', [])
    if taxes:
        output_lines.append("Taxes:")
        for tax in taxes:
            output_lines.append(f"  {tax.get('code', 'N/A')}: {tax.get('amount', 'N/A')}")

    # Total
    total = price.get('total', 'N/A')
    currency = price.get('currency', 'USD')
    output_lines.append("")
    output_lines.append(f"Total Price: {total} {currency}")

    return "\n".join(output_lines)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "price_analysis":
            # Parse arguments
            if len(sys.argv) < 5:
                print("Usage: pricing.py price_analysis <origin> <destination> <departure_date>")
                sys.exit(1)

            origin = sys.argv[2]
            destination = sys.argv[3]
            departure_date = sys.argv[4]

            # Get price analysis
            results = price_analysis(
                origin=origin,
                destination=destination,
                departure_date=departure_date
            )

            # Output results
            print(json.dumps(results, indent=2))

        elif command == "get_price":
            if len(sys.argv) < 3:
                print("Usage: pricing.py get_price <flight_offer_id>")
                sys.exit(1)

            flight_offer_id = sys.argv[2]

            # Get flight price
            results = get_flight_price(flight_offer_id)

            # Output results
            print(json.dumps(results, indent=2))

        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
