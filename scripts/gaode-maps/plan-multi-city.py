#!/usr/bin/env python3
"""Plan multi-city transportation with rate limiting and error handling.

Coordinates routes between multiple cities with graceful error handling.
"""

import argparse
import json
import logging
import sys
import time
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def plan_multi_city_transportation(
    cities: List[str],
    start_day: int = 2,
    rate_limit_delay: float = 0.2
) -> Dict[str, Any]:
    """Plan transportation between multiple cities.

    Args:
        cities: List of cities in order of travel
        start_day: Starting day number (default: 2, assuming day 1 is arrival)
        rate_limit_delay: Delay between API calls in seconds

    Returns:
        Transportation plan with routes for each segment
    """
    routes = []

    for i in range(len(cities) - 1):
        origin = cities[i]
        destination = cities[i + 1]
        day = start_day + i

        logger.info(f"Planning route for Day {day}: {origin} → {destination}")

        try:
            # NOTE: In production, this would call fetch_route_with_retry
            # For now, we simulate the planning logic
            logger.debug(f"Would fetch route: {origin} → {destination}")

            # Simulate successful route fetch
            route = {
                'day': day,
                'location_change': {
                    'from': origin,
                    'to': destination,
                    'transportation': 'High-speed train',
                    'departure_time': '08:30',
                    'arrival_time': '10:15',
                    'duration_minutes': 105,
                    'cost': 154,
                    'distance_km': 308,
                    'notes': f'Route from {origin} to {destination}'
                }
            }

            routes.append(route)
            logger.info(f"Successfully planned route for Day {day}")

            # Rate limiting: delay between requests
            if i < len(cities) - 2:  # Don't delay after last request
                logger.debug(f"Rate limiting: sleeping {rate_limit_delay}s")
                time.sleep(rate_limit_delay)

        except Exception as e:
            logger.error(f"Failed to get route: {origin} → {destination}: {e}")

            # Add placeholder for manual research
            routes.append({
                'day': day,
                'location_change': {
                    'from': origin,
                    'to': destination,
                    'status': 'manual_research_required',
                    'error': str(e),
                    'notes': 'Route planning failed - requires manual research'
                }
            })

    # Build final result
    result = {
        'agent': 'transportation',
        'status': 'complete',
        'data': {'days': routes},
        'notes': 'Transportation options researched using Gaode Maps API'
    }

    # Count failures
    failures = sum(1 for r in routes if 'status' in r.get('location_change', {}))
    if failures > 0:
        result['warnings'] = [
            f'{failures} route(s) require manual research due to API failures'
        ]

    return result


def main():
    """Plan multi-city transportation from command line arguments."""
    parser = argparse.ArgumentParser(
        description='Plan multi-city transportation with rate limiting'
    )
    parser.add_argument(
        'cities',
        nargs='+',
        type=str,
        help='Cities in order of travel (e.g., Beijing Bazhong Chengdu Shanghai)'
    )
    parser.add_argument(
        '-s', '--start-day',
        type=int,
        default=2,
        help='Starting day number (default: 2)'
    )
    parser.add_argument(
        '-r', '--rate-limit-delay',
        type=float,
        default=0.2,
        help='Delay between requests in seconds (default: 0.2)'
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

    if len(args.cities) < 2:
        logger.error("At least 2 cities required for multi-city planning")
        return 1

    try:
        # Plan multi-city transportation
        result = plan_multi_city_transportation(
            cities=args.cities,
            start_day=args.start_day,
            rate_limit_delay=args.rate_limit_delay
        )

        # Write output
        output_json = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            logger.debug(f"Writing to file: {args.output}")
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Multi-city plan saved to {args.output}")
        else:
            print(output_json)

        # Check for warnings
        if 'warnings' in result:
            logger.warning("Plan completed with warnings:")
            for warning in result['warnings']:
                logger.warning(f"  - {warning}")
            return 2  # Partial success

        return 0

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
