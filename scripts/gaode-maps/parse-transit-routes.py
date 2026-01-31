#!/usr/bin/env python3
"""Parse transit route response from Gaode Maps API.

Extracts main segment information and formats into structured data.
"""

import argparse
import json
import logging
import sys
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_transit_route(result: Dict[str, Any]) -> Dict[str, Any]:
    """Parse transit route response from Gaode Maps.

    Args:
        result: Raw API response from transit_route call

    Returns:
        Structured route information with transportation details

    Raises:
        KeyError: If required fields missing from response
        ValueError: If no valid transit segments found
    """
    try:
        transits = result.get('route', {}).get('transits', [])
        if not transits:
            raise ValueError("No transit options found in response")

        # Get first transit option (usually fastest/best)
        first_transit = transits[0]
        segments = first_transit.get('segments', [])

        # Find main transportation segment (railway or bus)
        main_segment = None
        for segment in segments:
            transit_type = segment.get('transit_type', '')
            if transit_type in ['railway', 'bus']:
                main_segment = segment
                break

        if not main_segment:
            raise ValueError("No railway or bus segment found in transit route")

        # Extract segment details
        departure = main_segment.get('departure', {})
        arrival = main_segment.get('arrival', {})
        duration = main_segment.get('duration', 0)
        cost = main_segment.get('cost', 0)
        distance = main_segment.get('distance', 0)

        # Determine transportation type
        transportation = (
            'High-speed train' if main_segment.get('transit_type') == 'railway'
            else 'Bus'
        )

        # Build parsed result
        parsed = {
            'from': departure.get('name', 'Unknown'),
            'to': arrival.get('name', 'Unknown'),
            'transportation': transportation,
            'departure_time': departure.get('time', ''),
            'arrival_time': arrival.get('time', ''),
            'duration_minutes': round(duration / 60),
            'cost': cost,
            'distance_km': round(distance / 1000),
            'notes': f"Depart from {departure.get('name', 'Unknown')}, arrive at {arrival.get('name', 'Unknown')}"
        }

        return parsed

    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse transit route: missing field {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing transit route: {e}")
        raise


def main():
    """Parse transit route from stdin or file."""
    parser = argparse.ArgumentParser(
        description='Parse Gaode Maps transit route response'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        type=str,
        help='Input JSON file (default: stdin)'
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
        # Read input
        if args.input_file:
            logger.debug(f"Reading from file: {args.input_file}")
            with open(args.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            logger.debug("Reading from stdin")
            data = json.load(sys.stdin)

        # Parse route
        parsed = parse_transit_route(data)

        # Write output
        output_json = json.dumps(parsed, indent=2, ensure_ascii=False)

        if args.output:
            logger.debug(f"Writing to file: {args.output}")
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Parsed route saved to {args.output}")
        else:
            print(output_json)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 2


if __name__ == '__main__':
    sys.exit(main())
