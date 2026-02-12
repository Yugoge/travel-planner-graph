#!/usr/bin/env python3
"""
Validate duration/distance consistency across all routes in transportation.json

Purpose: Detect routes where duration_minutes doesn't match expected duration
         based on distance and transportation mode speed.

Root Cause: Gaode Maps API returns duration in SECONDS, but commit d453036
           introduced code that used this value directly as MINUTES without
           conversion (duration=600s stored as duration_minutes=600 instead of 10).

Usage: source ~/.claude/venv/bin/activate && python3 scripts/validate-route-durations.py <transportation_json_path> [options]

Exit codes:
  0 - All routes valid
  1 - Validation errors found
  2 - Invalid arguments or file not found
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Default mode speeds in meters per second (m/s)
# Based on Gaode Maps standards (routing.md line 84: walking ~1.2 m/s)
DEFAULT_MODE_SPEEDS = {
    'walking': 1.2,      # ~4.3 km/h
    'cycling': 4.2,      # ~15 km/h
    'driving': 11.1,     # ~40 km/h (urban average)
    'transit': 8.3,      # ~30 km/h (including stops)
    'taxi': 11.1,        # Same as driving
    'didi': 11.1,        # Same as driving
    'bus': 8.3,          # Same as transit
    'subway': 13.9,      # ~50 km/h (including stops)
    'metro': 13.9        # Same as subway
}


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Validate route duration/distance consistency'
    )
    parser.add_argument(
        'transportation_json',
        help='Path to transportation.json file'
    )
    parser.add_argument(
        '--mode-speeds',
        type=str,
        help='JSON dict of mode→speed(m/s) mappings to override defaults'
    )
    parser.add_argument(
        '--tolerance',
        type=float,
        default=0.5,
        help='Acceptable deviation ratio (default: 0.5 = 50%% tolerance)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON report path (default: stdout)'
    )

    return parser.parse_args()


def get_mode_speed(transport_mode: str, mode_speeds: Dict[str, float]) -> float:
    """
    Extract speed for transportation mode

    Args:
        transport_mode: String like "Walking", "Taxi/Didi", "Bus 181路"
        mode_speeds: Dict mapping mode keywords to speeds (m/s)

    Returns:
        Speed in m/s, or None if mode not recognized
    """
    mode_lower = transport_mode.lower()

    # Check each known mode keyword
    for mode_key, speed in mode_speeds.items():
        if mode_key in mode_lower:
            return speed

    return None


def calculate_expected_duration(
    distance_meters: float,
    speed_ms: float
) -> float:
    """
    Calculate expected duration in minutes

    Args:
        distance_meters: Distance in meters
        speed_ms: Speed in meters per second

    Returns:
        Expected duration in minutes
    """
    if speed_ms <= 0:
        return 0

    duration_seconds = distance_meters / speed_ms
    return duration_seconds / 60


def validate_route(
    route_id: str,
    route: Dict,
    mode_speeds: Dict[str, float],
    tolerance: float
) -> Tuple[bool, Dict]:
    """
    Validate a single route

    Args:
        route_id: Route identifier
        route: Route data dict
        mode_speeds: Mode→speed mappings
        tolerance: Acceptable deviation ratio

    Returns:
        (is_valid, validation_result_dict)
    """
    distance_m = route.get('distance_meters', 0)
    duration_min = route.get('duration_minutes', 0)
    transport = route.get('recommended_transport', '')

    # Skip routes without distance/duration
    if distance_m == 0 or duration_min == 0:
        return True, {
            'route_id': route_id,
            'status': 'skipped',
            'reason': 'Missing distance or duration'
        }

    # Get speed for this mode
    speed_ms = get_mode_speed(transport, mode_speeds)
    if speed_ms is None:
        return True, {
            'route_id': route_id,
            'status': 'skipped',
            'reason': f'Unknown transport mode: {transport}'
        }

    # Calculate expected duration
    expected_min = calculate_expected_duration(distance_m, speed_ms)

    # Calculate deviation
    deviation_ratio = abs(duration_min - expected_min) / expected_min if expected_min > 0 else 0

    # Check if duration appears to be in wrong units (seconds instead of minutes)
    # If actual duration is ~60x expected, it's likely seconds misinterpreted as minutes
    seconds_as_minutes_ratio = abs(duration_min - expected_min * 60) / (expected_min * 60) if expected_min > 0 else 1

    is_valid = deviation_ratio <= tolerance

    result = {
        'route_id': route_id,
        'from': route.get('from', 'N/A'),
        'to': route.get('to', 'N/A'),
        'transport': transport,
        'distance_meters': distance_m,
        'distance_km': round(distance_m / 1000, 2),
        'duration_minutes_actual': duration_min,
        'duration_minutes_expected': round(expected_min, 1),
        'deviation_ratio': round(deviation_ratio, 3),
        'speed_assumed_ms': speed_ms,
        'speed_assumed_kmh': round(speed_ms * 3.6, 1),
        'status': 'valid' if is_valid else 'invalid',
        'likely_unit_error': seconds_as_minutes_ratio < 0.2  # Strong match to seconds interpretation
    }

    if not is_valid:
        result['issue'] = f"Duration {duration_min}min deviates {deviation_ratio*100:.0f}% from expected {expected_min:.1f}min"

    return is_valid, result


def validate_transportation_json(
    json_path: Path,
    mode_speeds: Dict[str, float],
    tolerance: float
) -> Dict:
    """
    Validate all routes in transportation.json

    Args:
        json_path: Path to transportation.json
        mode_speeds: Mode→speed mappings
        tolerance: Acceptable deviation ratio

    Returns:
        Validation report dict
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    report = {
        'file': str(json_path),
        'tolerance': tolerance,
        'mode_speeds_ms': mode_speeds,
        'mode_speeds_kmh': {k: round(v * 3.6, 1) for k, v in mode_speeds.items()},
        'summary': {
            'total_routes': 0,
            'valid_routes': 0,
            'invalid_routes': 0,
            'skipped_routes': 0,
            'likely_unit_errors': 0
        },
        'days': []
    }

    for day_data in data.get('data', {}).get('days', []):
        day_report = {
            'day': day_data.get('day'),
            'date': day_data.get('date'),
            'location': day_data.get('location'),
            'routes': []
        }

        for route_id, route in day_data.get('intra_city_routes', {}).items():
            report['summary']['total_routes'] += 1

            is_valid, route_result = validate_route(
                route_id, route, mode_speeds, tolerance
            )

            day_report['routes'].append(route_result)

            if route_result['status'] == 'valid':
                report['summary']['valid_routes'] += 1
            elif route_result['status'] == 'invalid':
                report['summary']['invalid_routes'] += 1
            elif route_result['status'] == 'skipped':
                report['summary']['skipped_routes'] += 1

            if route_result.get('likely_unit_error', False):
                report['summary']['likely_unit_errors'] += 1

        day_report['invalid_count'] = len([r for r in day_report['routes'] if r['status'] == 'invalid'])
        report['days'].append(day_report)

    return report


def main():
    """Main execution"""
    args = parse_arguments()

    # Check input file
    json_path = Path(args.transportation_json)
    if not json_path.exists():
        print(f"Error: File not found: {json_path}", file=sys.stderr)
        return 2

    # Parse mode speeds
    mode_speeds = DEFAULT_MODE_SPEEDS.copy()
    if args.mode_speeds:
        try:
            custom_speeds = json.loads(args.mode_speeds)
            mode_speeds.update(custom_speeds)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --mode-speeds: {e}", file=sys.stderr)
            return 2

    # Run validation
    report = validate_transportation_json(json_path, mode_speeds, args.tolerance)

    # Output report
    report_json = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report_json)
        print(f"Validation report written to: {args.output}")
    else:
        print(report_json)

    # Print summary
    print(f"\nValidation Summary:", file=sys.stderr)
    print(f"  Total routes: {report['summary']['total_routes']}", file=sys.stderr)
    print(f"  Valid: {report['summary']['valid_routes']}", file=sys.stderr)
    print(f"  Invalid: {report['summary']['invalid_routes']}", file=sys.stderr)
    print(f"  Skipped: {report['summary']['skipped_routes']}", file=sys.stderr)
    print(f"  Likely unit errors: {report['summary']['likely_unit_errors']}", file=sys.stderr)

    # Exit code
    if report['summary']['invalid_routes'] > 0:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
