#!/usr/bin/env python3
"""
Validate timeline.json has no time overlaps
Detects overlapping time ranges that would cause visual conflicts in TimelineView
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta


def parse_time(time_str: str) -> datetime:
    """Parse HH:MM time string to datetime object"""
    try:
        h, m = map(int, time_str.split(':'))
        return datetime(2026, 1, 1, h, m)
    except:
        raise ValueError(f"Invalid time format: {time_str}")


def check_overlap(entry1: dict, entry2: dict) -> bool:
    """Check if two timeline entries overlap"""
    start1 = parse_time(entry1['start_time'])
    end1 = parse_time(entry1['end_time'])
    start2 = parse_time(entry2['start_time'])
    end2 = parse_time(entry2['end_time'])

    # Overlap if: (start1 < end2) and (start2 < end1)
    return start1 < end2 and start2 < end1


def validate_timeline(plan_id: str) -> dict:
    """Validate timeline.json has no overlapping time ranges"""
    base_dir = Path(__file__).parent.parent
    timeline_path = base_dir / "data" / plan_id / "timeline.json"

    if not timeline_path.exists():
        return {
            "status": "error",
            "message": f"timeline.json not found at {timeline_path}"
        }

    with open(timeline_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract 'data' field if it's an agent output
    if isinstance(data, dict) and 'data' in data:
        data = data['data']

    if not data or 'days' not in data:
        return {
            "status": "error",
            "message": "timeline.json missing 'days' array"
        }

    results = {
        "status": "valid",
        "total_days": len(data['days']),
        "conflicts": [],
        "empty_timelines": []
    }

    for day in data['days']:
        day_num = day.get('day', 0)
        timeline = day.get('timeline', {})

        if not timeline:
            results['empty_timelines'].append(day_num)
            continue

        # Convert timeline dict to list of entries with names
        entries = []
        for name, time_range in timeline.items():
            if isinstance(time_range, str) and '-' in time_range:
                start, end = time_range.split('-')
                entries.append({
                    'name': name,
                    'start_time': start.strip(),
                    'end_time': end.strip()
                })
            elif isinstance(time_range, dict):
                entries.append({
                    'name': name,
                    'start_time': time_range.get('start', ''),
                    'end_time': time_range.get('end', '')
                })

        # Check for overlaps
        for i, entry1 in enumerate(entries):
            for entry2 in entries[i+1:]:
                if check_overlap(entry1, entry2):
                    results['conflicts'].append({
                        'day': day_num,
                        'entry1': f"{entry1['name']} ({entry1['start_time']}-{entry1['end_time']})",
                        'entry2': f"{entry2['name']} ({entry2['start_time']}-{entry2['end_time']})"
                    })

    if results['conflicts']:
        results['status'] = 'conflicts_found'
    elif results['empty_timelines']:
        results['status'] = 'empty_timelines'

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-timeline-conflicts.py <plan-id>")
        sys.exit(1)

    plan_id = sys.argv[1]
    results = validate_timeline(plan_id)

    print(json.dumps(results, indent=2, ensure_ascii=False))

    if results['status'] == 'conflicts_found':
        sys.exit(1)
    elif results['status'] == 'empty_timelines':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
