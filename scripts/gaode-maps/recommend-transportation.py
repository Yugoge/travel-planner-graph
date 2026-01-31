#!/usr/bin/env python3
"""Recommend best transportation option based on multiple factors.

Compares transit and driving options considering time, cost, and user preferences.
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


def recommend_transportation(
    transit_option: Dict[str, Any],
    driving_option: Dict[str, Any],
    user_preferences: Dict[str, Any]
) -> Dict[str, Any]:
    """Recommend best transportation based on time, cost, and preferences.

    Args:
        transit_option: Parsed transit route data
        driving_option: Parsed driving route data
        user_preferences: User preferences (luggage, travelers, budget, etc.)

    Returns:
        Recommended option with reasoning
    """
    considerations = []

    # Time comparison
    transit_time = transit_option.get('duration_minutes', 0)
    driving_time = driving_option.get('duration_minutes', 0)

    if transit_time < driving_time:
        time_diff = driving_time - transit_time
        considerations.append({
            'factor': 'time',
            'winner': 'transit',
            'detail': f'Train is {time_diff} minutes faster'
        })
    elif driving_time < transit_time:
        time_diff = transit_time - driving_time
        considerations.append({
            'factor': 'time',
            'winner': 'driving',
            'detail': f'Driving is {time_diff} minutes faster'
        })

    # Cost comparison (add fuel estimate for driving)
    transit_cost = transit_option.get('cost', 0)
    driving_tolls = driving_option.get('cost', 0)
    fuel_estimate = user_preferences.get('fuel_estimate_per_km', 0.6)
    distance_km = driving_option.get('distance_km', 0)
    driving_total_cost = driving_tolls + (distance_km * fuel_estimate)

    if transit_cost < driving_total_cost:
        cost_diff = round(driving_total_cost - transit_cost)
        considerations.append({
            'factor': 'cost',
            'winner': 'transit',
            'detail': f'Train is ¥{cost_diff} cheaper'
        })
    elif driving_total_cost < transit_cost:
        cost_diff = round(transit_cost - driving_total_cost)
        considerations.append({
            'factor': 'cost',
            'winner': 'driving',
            'detail': f'Driving is ¥{cost_diff} cheaper'
        })

    # Convenience factors
    luggage = user_preferences.get('luggage', 'light')
    travelers = user_preferences.get('travelers', 1)

    if luggage == 'heavy' or travelers > 3:
        considerations.append({
            'factor': 'convenience',
            'winner': 'driving',
            'detail': 'Private car better for heavy luggage or large groups'
        })
    else:
        considerations.append({
            'factor': 'convenience',
            'winner': 'transit',
            'detail': 'Public transit convenient for light luggage and small groups'
        })

    # Calculate scores
    transit_score = sum(1 for c in considerations if c['winner'] == 'transit')
    driving_score = sum(1 for c in considerations if c['winner'] == 'driving')

    # Make recommendation
    if transit_score >= driving_score:
        recommendation = transit_option.copy()
        recommendation['recommendation_reason'] = considerations
        recommendation['score'] = {
            'transit': transit_score,
            'driving': driving_score
        }
    else:
        recommendation = driving_option.copy()
        recommendation['recommendation_reason'] = considerations
        recommendation['score'] = {
            'transit': transit_score,
            'driving': driving_score
        }

    return recommendation


def main():
    """Recommend transportation from JSON input files."""
    parser = argparse.ArgumentParser(
        description='Recommend best transportation option'
    )
    parser.add_argument(
        'transit_file',
        type=str,
        help='Transit option JSON file'
    )
    parser.add_argument(
        'driving_file',
        type=str,
        help='Driving option JSON file'
    )
    parser.add_argument(
        '-p', '--preferences',
        type=str,
        help='User preferences JSON file (default: use defaults)'
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
        # Read transit option
        logger.debug(f"Reading transit option: {args.transit_file}")
        with open(args.transit_file, 'r', encoding='utf-8') as f:
            transit_option = json.load(f)

        # Read driving option
        logger.debug(f"Reading driving option: {args.driving_file}")
        with open(args.driving_file, 'r', encoding='utf-8') as f:
            driving_option = json.load(f)

        # Read preferences (or use defaults)
        if args.preferences:
            logger.debug(f"Reading preferences: {args.preferences}")
            with open(args.preferences, 'r', encoding='utf-8') as f:
                user_preferences = json.load(f)
        else:
            user_preferences = {
                'luggage': 'light',
                'travelers': 2,
                'fuel_estimate_per_km': 0.6
            }
            logger.debug("Using default preferences")

        # Make recommendation
        recommendation = recommend_transportation(
            transit_option,
            driving_option,
            user_preferences
        )

        # Write output
        output_json = json.dumps(recommendation, indent=2, ensure_ascii=False)

        if args.output:
            logger.debug(f"Writing to file: {args.output}")
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Recommendation saved to {args.output}")
        else:
            print(output_json)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 2


if __name__ == '__main__':
    sys.exit(main())
