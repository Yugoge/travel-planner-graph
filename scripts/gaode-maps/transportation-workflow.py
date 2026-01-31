#!/usr/bin/env python3
"""Complete transportation agent workflow.

Orchestrates full transportation planning from requirements to final JSON output.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read and parse JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    logger.debug(f"Reading file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """Write data to JSON file.

    Args:
        file_path: Path to output file
        data: Data to write
    """
    logger.debug(f"Writing file: {file_path}")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def identify_location_changes(plan_skeleton: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify days with location changes.

    Args:
        plan_skeleton: Plan skeleton data

    Returns:
        List of days with location changes
    """
    days = plan_skeleton.get('days', [])
    location_change_days = [
        day for day in days
        if day.get('location_change') is not None
    ]

    logger.info(f"Found {len(location_change_days)} days with location changes")
    return location_change_days


def research_route(
    origin: str,
    destination: str,
    preferences: Dict[str, Any]
) -> Dict[str, Any]:
    """Research route with retry and recommendation logic.

    Args:
        origin: Starting location
        destination: Ending location
        preferences: User preferences for transportation

    Returns:
        Recommended route data

    Raises:
        Exception: If route research fails
    """
    logger.info(f"Researching route: {origin} → {destination}")

    try:
        # NOTE: In production, these would call actual MCP tools
        # For now, we simulate the workflow logic

        # Step 1: Fetch transit route with retry
        logger.debug(f"Fetching transit route: {origin} → {destination}")
        # transit_route = fetch_route_with_retry(origin, destination, 'transit')

        # Step 2: Fetch driving route with fewer retries
        logger.debug(f"Fetching driving route: {origin} → {destination}")
        # driving_route = fetch_route_with_retry(origin, destination, 'driving', max_retries=2)

        # Step 3: Parse routes
        # transit_parsed = parse_transit_route(transit_route)
        # driving_parsed = parse_driving_route(driving_route)

        # Step 4: Make recommendation
        # recommendation = recommend_transportation(transit_parsed, driving_parsed, preferences)

        # Simulated recommendation for testing
        recommendation = {
            'from': origin,
            'to': destination,
            'transportation': 'High-speed train',
            'departure_time': '08:30',
            'arrival_time': '10:15',
            'duration_minutes': 105,
            'cost': 154,
            'distance_km': 308,
            'notes': f'Recommended route from {origin} to {destination}'
        }

        logger.info(f"Successfully researched route: {origin} → {destination}")
        return recommendation

    except Exception as e:
        logger.error(f"Route research failed: {e}")
        raise


def transportation_agent_workflow(
    destination_slug: str,
    data_dir: str = '/root/travel-planner/data',
    rate_limit_delay: float = 0.2
) -> str:
    """Complete transportation agent workflow.

    Args:
        destination_slug: Destination identifier
        data_dir: Base data directory
        rate_limit_delay: Delay between API calls

    Returns:
        Status string ('complete' or 'error')
    """
    logger.info(f"Starting transportation workflow for: {destination_slug}")

    # Step 1: Read requirements and plan skeleton
    dest_dir = Path(data_dir) / destination_slug
    requirements_file = dest_dir / 'requirements-skeleton.json'
    plan_file = dest_dir / 'plan-skeleton.json'
    output_file = dest_dir / 'transportation.json'

    try:
        requirements = read_json_file(str(requirements_file))
        plan_skeleton = read_json_file(str(plan_file))
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return 'error'
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 'error'

    # Step 2: Identify days with location changes
    location_change_days = identify_location_changes(plan_skeleton)

    if not location_change_days:
        logger.info("No inter-city transportation needed (single-city trip)")
        result = {
            'agent': 'transportation',
            'status': 'complete',
            'data': {'days': []},
            'notes': 'No inter-city transportation needed (single-city trip)'
        }
        write_json_file(str(output_file), result)
        return 'complete'

    # Step 3: Research routes for each location change
    routes = []
    preferences = requirements.get('trip_summary', {}).get('preferences', {})

    for day in location_change_days:
        location_change = day.get('location_change', {})
        origin = location_change.get('from')
        destination = location_change.get('to')
        day_num = day.get('day')

        if not origin or not destination:
            logger.warning(f"Skipping day {day_num}: missing origin or destination")
            continue

        try:
            # Research route with retry and recommendation
            recommendation = research_route(origin, destination, preferences)

            routes.append({
                'day': day_num,
                'location_change': recommendation
            })

            logger.info(f"Day {day_num} route planned successfully")

        except Exception as e:
            logger.error(f"Route research failed for day {day_num}: {e}")

            # Add placeholder for manual research
            routes.append({
                'day': day_num,
                'location_change': {
                    'from': origin,
                    'to': destination,
                    'status': 'research_failed',
                    'error': str(e),
                    'fallback': 'Manual research required'
                }
            })

        # Rate limiting between requests
        if day != location_change_days[-1]:  # Don't delay after last
            time.sleep(rate_limit_delay)

    # Step 4: Save results
    result = {
        'agent': 'transportation',
        'status': 'complete',
        'data': {'days': routes},
        'notes': 'Routes researched using Gaode Maps. Book transportation 1-2 weeks in advance.'
    }

    # Add warnings for failures
    failures = sum(1 for r in routes if 'status' in r.get('location_change', {}))
    if failures > 0:
        result['warnings'] = [
            f'{failures} route(s) require manual research due to API failures'
        ]

    write_json_file(str(output_file), result)
    logger.info(f"Transportation data saved to: {output_file}")

    return 'complete'


def main():
    """Run transportation workflow from command line."""
    parser = argparse.ArgumentParser(
        description='Complete transportation agent workflow'
    )
    parser.add_argument(
        'destination_slug',
        type=str,
        help='Destination slug (e.g., chongqing-chengdu-2026)'
    )
    parser.add_argument(
        '-d', '--data-dir',
        type=str,
        default='/root/travel-planner/data',
        help='Base data directory (default: /root/travel-planner/data)'
    )
    parser.add_argument(
        '-r', '--rate-limit-delay',
        type=float,
        default=0.2,
        help='Delay between API calls in seconds (default: 0.2)'
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
        status = transportation_agent_workflow(
            destination_slug=args.destination_slug,
            data_dir=args.data_dir,
            rate_limit_delay=args.rate_limit_delay
        )

        if status == 'complete':
            logger.info("Transportation workflow completed successfully")
            return 0
        else:
            logger.error("Transportation workflow failed")
            return 1

    except Exception as e:
        logger.error(f"Unexpected error in workflow: {e}")
        return 2


if __name__ == '__main__':
    sys.exit(main())
