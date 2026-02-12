#!/usr/bin/env python3
"""
Fix duration_minutes field by detecting and correcting unit conversion errors

Purpose: Systematically correct routes where Gaode Maps API duration (in seconds)
         was incorrectly used directly as minutes without dividing by 60.

Root Cause: Commit d453036 introduced code that parsed Gaode Maps API responses
           but failed to convert duration field from seconds to minutes, causing
           duration values to be 60x too large.

Detection Logic: For each route, calculate expected_duration based on distance
                and mode speed. If actual_duration ≈ expected_duration * 60,
                it's highly likely the value is in seconds, so divide by 60.

Usage: source ~/.claude/venv/bin/activate && python3 scripts/fix-duration-units.py <transportation_json_path> [options]

Exit codes:
  0 - Success (routes fixed or no fixes needed)
  1 - Errors during execution
  2 - Invalid arguments
"""

import json
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Import mode speeds from validation script logic
DEFAULT_MODE_SPEEDS = {
    'walking': 1.2,      # ~4.3 km/h (Gaode Maps standard)
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
        description='Fix duration unit conversion errors in transportation.json'
    )
    parser.add_argument(
        'transportation_json',
        help='Path to transportation.json file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying file'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        default=True,
        help='Create backup before modifying (default: True)'
    )
    parser.add_argument(
        '--no-backup',
        dest='backup',
        action='store_false',
        help='Skip backup creation'
    )
    parser.add_argument(
        '--mode-speeds',
        type=str,
        help='JSON dict of mode→speed(m/s) mappings to override defaults'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.15,
        help='Match threshold for unit error detection (default: 0.15 = 15%% tolerance)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output path for fixed JSON (default: overwrite input file)'
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

    for mode_key, speed in mode_speeds.items():
        if mode_key in mode_lower:
            return speed

    return None


def calculate_expected_duration(distance_meters: float, speed_ms: float) -> float:
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


def detect_and_fix_route(
    route_id: str,
    route: Dict,
    mode_speeds: Dict[str, float],
    threshold: float
) -> Tuple[bool, Dict, float]:
    """
    Detect if route has unit error and return corrected duration

    Args:
        route_id: Route identifier
        route: Route data dict
        mode_speeds: Mode→speed mappings
        threshold: Match threshold for detecting unit error

    Returns:
        (needs_fix, fix_report, corrected_duration)
    """
    distance_m = route.get('distance_meters', 0)
    duration_min = route.get('duration_minutes', 0)
    transport = route.get('recommended_transport', '')

    # Skip routes without distance/duration
    if distance_m == 0 or duration_min == 0:
        return False, {'route_id': route_id, 'action': 'skipped', 'reason': 'No distance/duration'}, duration_min

    # Get speed for this mode
    speed_ms = get_mode_speed(transport, mode_speeds)
    if speed_ms is None:
        return False, {'route_id': route_id, 'action': 'skipped', 'reason': f'Unknown mode: {transport}'}, duration_min

    # Calculate expected duration
    expected_min = calculate_expected_duration(distance_m, speed_ms)
    if expected_min == 0:
        return False, {'route_id': route_id, 'action': 'skipped', 'reason': 'Invalid calculation'}, duration_min

    # Check if actual duration matches expected * 60 (seconds interpretation)
    # Formula: if |actual - (expected * 60)| / (expected * 60) < threshold, it's likely seconds
    expected_if_seconds = expected_min * 60
    deviation_if_seconds = abs(duration_min - expected_if_seconds) / expected_if_seconds

    needs_fix = deviation_if_seconds < threshold
    corrected_duration = round(duration_min / 60, 1) if needs_fix else duration_min

    fix_report = {
        'route_id': route_id,
        'from': route.get('from', 'N/A'),
        'to': route.get('to', 'N/A'),
        'transport': transport,
        'distance_meters': distance_m,
        'duration_original': duration_min,
        'duration_expected_min': round(expected_min, 1),
        'duration_corrected': corrected_duration,
        'action': 'fixed' if needs_fix else 'no_change',
        'detection_confidence': round((1 - deviation_if_seconds) * 100, 1) if needs_fix else 0
    }

    return needs_fix, fix_report, corrected_duration


def fix_transportation_json(
    json_path: Path,
    mode_speeds: Dict[str, float],
    threshold: float,
    dry_run: bool
) -> Dict:
    """
    Fix all routes with unit conversion errors

    Args:
        json_path: Path to transportation.json
        mode_speeds: Mode→speed mappings
        threshold: Match threshold for unit error detection
        dry_run: If True, don't modify file

    Returns:
        Fix report dict
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    report = {
        'file': str(json_path),
        'dry_run': dry_run,
        'threshold': threshold,
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_routes': 0,
            'routes_fixed': 0,
            'routes_unchanged': 0,
            'routes_skipped': 0
        },
        'fixes': []
    }

    # Process each day
    for day_data in data.get('data', {}).get('days', []):
        for route_id, route in day_data.get('intra_city_routes', {}).items():
            report['summary']['total_routes'] += 1

            needs_fix, fix_info, corrected_duration = detect_and_fix_route(
                route_id, route, mode_speeds, threshold
            )

            if fix_info['action'] == 'fixed':
                report['summary']['routes_fixed'] += 1
                report['fixes'].append(fix_info)
                # Apply fix if not dry run
                if not dry_run:
                    route['duration_minutes'] = corrected_duration
            elif fix_info['action'] == 'no_change':
                report['summary']['routes_unchanged'] += 1
            elif fix_info['action'] == 'skipped':
                report['summary']['routes_skipped'] += 1

    # Write fixed data if not dry run
    if not dry_run and report['summary']['routes_fixed'] > 0:
        report['output_file'] = str(json_path)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

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

    # Create backup if requested and not dry run
    if args.backup and not args.dry_run:
        backup_path = json_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        shutil.copy2(json_path, backup_path)
        print(f"Backup created: {backup_path}", file=sys.stderr)

    # Run fix
    report = fix_transportation_json(json_path, mode_speeds, args.threshold, args.dry_run)

    # Output report
    report_json = json.dumps(report, indent=2, ensure_ascii=False)
    print(report_json)

    # Print summary
    print(f"\nFix Summary:", file=sys.stderr)
    print(f"  Total routes: {report['summary']['total_routes']}", file=sys.stderr)
    print(f"  Fixed: {report['summary']['routes_fixed']}", file=sys.stderr)
    print(f"  Unchanged: {report['summary']['routes_unchanged']}", file=sys.stderr)
    print(f"  Skipped: {report['summary']['routes_skipped']}", file=sys.stderr)

    if args.dry_run:
        print(f"\n(Dry run - no changes made)", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
