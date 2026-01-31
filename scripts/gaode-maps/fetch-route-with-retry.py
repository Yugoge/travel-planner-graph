#!/usr/bin/env python3
"""Fetch route with retry logic and exponential backoff.

Handles transient network errors with configurable retry strategy.
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RouteAPIError(Exception):
    """Custom exception for route API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def should_retry(error: Exception, status_code: Optional[int] = None) -> bool:
    """Determine if error is retryable.

    Args:
        error: Exception that occurred
        status_code: HTTP status code if available

    Returns:
        True if should retry, False otherwise
    """
    # Retry on rate limiting or server errors
    if status_code and (status_code == 429 or status_code >= 500):
        return True

    # Don't retry on client errors (400-499 except 429)
    if status_code and 400 <= status_code < 500:
        return False

    # Retry on network errors
    error_msg = str(error).lower()
    retryable_errors = [
        'timeout',
        'connection',
        'network',
        'temporary failure'
    ]

    return any(err in error_msg for err in retryable_errors)


def fetch_route_with_retry(
    origin: str,
    destination: str,
    route_type: str = 'transit',
    cityd: Optional[str] = None,
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> Dict[str, Any]:
    """Fetch route with exponential backoff retry logic.

    Args:
        origin: Starting location
        destination: Ending location
        route_type: Route type ('transit' or 'driving')
        cityd: City for transit routing
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)

    Returns:
        Route data from API

    Raises:
        RouteAPIError: If max retries exceeded or non-retryable error
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Fetching {route_type} route from {origin} to {destination}")

            # NOTE: This is a placeholder for actual API call
            # In production, this would call the Gaode Maps MCP tool
            # For now, we simulate the API call pattern
            logger.debug(f"Would call: {route_type}_route(origin={origin}, destination={destination}, cityd={cityd})")

            # Simulate API response structure for testing
            # In real usage, replace with actual MCP tool call
            raise RouteAPIError("Simulated API call - replace with actual MCP tool", 200)

        except RouteAPIError as e:
            status_code = e.status_code

            # Check if should retry
            if not should_retry(e, status_code):
                logger.error(f"Non-retryable error: {e.message}")
                raise

            # Calculate backoff delay
            delay = initial_delay * (2 ** attempt)

            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s due to: {e.message}")
                time.sleep(delay)
            else:
                logger.error(f"Max retries ({max_retries}) exceeded")
                raise RouteAPIError(f"Max retries exceeded: {e.message}", status_code)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise RouteAPIError(f"Unexpected error: {str(e)}")

    raise RouteAPIError("Max retries exceeded")


def main():
    """Fetch route with retry from command line arguments."""
    parser = argparse.ArgumentParser(
        description='Fetch route with retry and exponential backoff'
    )
    parser.add_argument(
        'origin',
        type=str,
        help='Starting location'
    )
    parser.add_argument(
        'destination',
        type=str,
        help='Ending location'
    )
    parser.add_argument(
        '-t', '--type',
        type=str,
        choices=['transit', 'driving'],
        default='transit',
        help='Route type (default: transit)'
    )
    parser.add_argument(
        '-c', '--cityd',
        type=str,
        help='City for transit routing'
    )
    parser.add_argument(
        '-r', '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts (default: 3)'
    )
    parser.add_argument(
        '-d', '--initial-delay',
        type=float,
        default=1.0,
        help='Initial retry delay in seconds (default: 1.0)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Fetch route with retry
        route_data = fetch_route_with_retry(
            origin=args.origin,
            destination=args.destination,
            route_type=args.type,
            cityd=args.cityd or args.destination,
            max_retries=args.max_retries,
            initial_delay=args.initial_delay
        )

        # Write output
        output_json = json.dumps(route_data, indent=2, ensure_ascii=False)

        if args.output:
            logger.debug(f"Writing to file: {args.output}")
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Route data saved to {args.output}")
        else:
            print(output_json)

        return 0

    except RouteAPIError as e:
        logger.error(f"Route fetch failed: {e.message}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 2


if __name__ == '__main__':
    sys.exit(main())
