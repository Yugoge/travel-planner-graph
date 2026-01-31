#!/usr/bin/env python3
"""Detect location changes between consecutive days in travel plan.

Reads day-by-day plan and identifies when travelers move between cities.
"""

import argparse
import json
import logging
import sys
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_location_changes(days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect location changes between consecutive days.

    Args:
        days: List of day objects with location field

    Returns:
        Updated days list with location_change objects added
    """
    if len(days) < 2:
        logger.info("Single day trip - no location changes")
        return days

    updated_days = []
    location_changes_found = 0

    for i, day in enumerate(days):
        # Copy day data
        updated_day = day.copy()

        # Check if location differs from previous day
        if i > 0:
            current_location = day.get('location', '')
            previous_location = days[i - 1].get('location', '')

            if current_location and previous_location and current_location != previous_location:
                logger.info(f"Day {day.get('day')}: Location change detected: {previous_location} → {current_location}")

                # Add location_change object
                updated_day['location_change'] = {
                    'from': previous_location,
                    'to': current_location,
                    'transportation': None,
                    'departure_time': None,
                    'arrival_time': None,
                    'cost': None
                }

                location_changes_found += 1
            else:
                # Same location or missing data - no change
                updated_day['location_change'] = None
        else:
            # First day - no previous location to compare
            updated_day['location_change'] = None

        updated_days.append(updated_day)

    logger.info(f"Total location changes detected: {location_changes_found}")
    return updated_days


def process_plan_skeleton(
    input_file: str,
    output_file: str = None
) -> Dict[str, Any]:
    """Process plan skeleton to detect and add location changes.

    Args:
        input_file: Path to input JSON file
        output_file: Path to output file (optional, defaults to overwriting input)

    Returns:
        Updated plan skeleton
    """
    logger.info(f"Processing plan skeleton: {input_file}")

    # Read input
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            plan_skeleton = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        raise

    # Detect location changes
    days = plan_skeleton.get('days', [])
    if not days:
        logger.warning("No days found in plan skeleton")
        return plan_skeleton

    updated_days = detect_location_changes(days)

    # Update plan skeleton
    plan_skeleton['days'] = updated_days

    # Write output
    output_path = output_file or input_file
    logger.debug(f"Writing updated plan to: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(plan_skeleton, f, indent=2, ensure_ascii=False)

    logger.info(f"Updated plan skeleton saved to: {output_path}")
    return plan_skeleton


def main():
    """Detect location changes from command line."""
    parser = argparse.ArgumentParser(
        description='Detect location changes in travel plan'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Input plan skeleton JSON file'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file (default: overwrite input file)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print changes without writing to file'
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
        if args.dry_run:
            # Read and detect without writing
            with open(args.input_file, 'r', encoding='utf-8') as f:
                plan_skeleton = json.load(f)

            days = plan_skeleton.get('days', [])
            updated_days = detect_location_changes(days)

            # Print result to stdout
            result = plan_skeleton.copy()
            result['days'] = updated_days
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            # Process and write
            process_plan_skeleton(args.input_file, args.output)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 2


if __name__ == '__main__':
    sys.exit(main())
