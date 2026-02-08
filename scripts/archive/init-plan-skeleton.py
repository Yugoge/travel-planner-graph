#!/usr/bin/env python3
"""Initialize plan skeleton from requirements skeleton with location change detection."""

import json
import sys
from pathlib import Path


def init_plan_skeleton(requirements_path: str, output_path: str):
    """Initialize plan skeleton with all required fields."""

    # Read requirements
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = json.load(f)

    days = []
    prev_location = None

    for day_req in requirements['days']:
        day_num = day_req['day']
        date = day_req['date']
        location = day_req['location']

        # Detect location change
        if '→' in location:
            # Multi-location day (travel day)
            parts = location.split('→')
            from_loc = parts[0].strip()
            to_loc = parts[1].strip()
            location_change = {
                "from": from_loc,
                "to": to_loc,
                "method": "TBD",
                "departure_time": "",
                "arrival_time": "",
                "cost": 0,
                "booking_required": True
            }
            current_location = to_loc
        elif prev_location and prev_location != location:
            # Location changed from previous day
            location_change = {
                "from": prev_location,
                "to": location,
                "method": "TBD",
                "departure_time": "",
                "arrival_time": "",
                "cost": 0,
                "booking_required": True
            }
            current_location = location
        else:
            location_change = None
            current_location = location

        day_obj = {
            "day": day_num,
            "date": date,
            "location": current_location,
            "location_change": location_change,
            "user_requirements": day_req.get('user_plans', []),
            "breakfast": {"name": "", "location": "", "cost": 0, "notes": ""},
            "lunch": {"name": "", "location": "", "cost": 0, "notes": ""},
            "dinner": {"name": "", "location": "", "cost": 0, "notes": ""},
            "accommodation": {"name": "", "location": "", "cost": 0, "check_in": "", "check_out": "", "booking_required": True},
            "attractions": [],
            "entertainment": [],
            "shopping": [],
            "free_time": [],
            "timeline": {},
            "budget": {
                "meals": 0,
                "accommodation": 0,
                "activities": 0,
                "shopping": 0,
                "transportation": 0,
                "total": 0
            }
        }

        days.append(day_obj)
        prev_location = current_location

    plan_skeleton = {
        "trip_summary": requirements['trip_summary'],
        "days": days,
        "emergency_info": {
            "hospitals": [],
            "police_stations": [],
            "embassy": None
        }
    }

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(plan_skeleton, f, indent=2, ensure_ascii=False)

    print(f"✓ Plan skeleton initialized with {len(days)} days")
    print(f"✓ Detected {sum(1 for d in days if d['location_change'])} location changes")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: init-plan-skeleton.py <requirements-skeleton.json> <plan-skeleton.json>")
        sys.exit(1)

    init_plan_skeleton(sys.argv[1], sys.argv[2])
