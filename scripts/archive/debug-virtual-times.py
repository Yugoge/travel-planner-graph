#!/usr/bin/env python3
"""
Debug virtual time generation logic
Simulates the fallback time calculation from generate-html-interactive.py
"""

import json
import sys
from pathlib import Path


def simulate_day_timeline(plan_id: str, day_num: int) -> dict:
    """Simulate timeline generation for a specific day"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / plan_id

    # Load data
    def load_json(filename):
        path = data_dir / filename
        if not path.exists():
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'data' in data:
                return data['data']
            return data

    meals = load_json("meals.json")
    attractions = load_json("attractions.json")
    entertainment = load_json("entertainment.json")

    result = {
        "day": day_num,
        "timeline": [],
        "conflicts": []
    }

    # Meal default times (from line 261-265)
    meal_default_times = {
        "breakfast": {"start": "08:00", "end": "09:00"},
        "lunch": {"start": "12:00", "end": "13:30"},
        "dinner": {"start": "18:30", "end": "20:00"}
    }

    # Add meals
    if meals and "days" in meals:
        day_meals = next((d for d in meals["days"] if d.get("day") == day_num), {})
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if meal_type in day_meals:
                meal = day_meals[meal_type]
                meal_time = meal_default_times[meal_type]
                result["timeline"].append({
                    "name": meal.get("name", ""),
                    "type": "meal",
                    "meal_type": meal_type,
                    "start": meal_time["start"],
                    "end": meal_time["end"]
                })

    # Add attractions with virtual time calculation (line 308-351)
    if attractions and "days" in attractions:
        day_attrs = next((d for d in attractions["days"] if d.get("day") == day_num), {})
        if "attractions" in day_attrs:
            current_time_hour = 10  # Start attractions at 10:00
            current_time_minute = 0
            for attr in day_attrs["attractions"]:
                # Calculate virtual time based on duration
                duration_minutes = attr.get("duration_minutes", 120)  # default 2h
                duration_hours = duration_minutes / 60

                start_time = f"{current_time_hour:02d}:{current_time_minute:02d}"
                end_hour = current_time_hour + int(duration_hours)
                end_minute = current_time_minute + int((duration_hours % 1) * 60)
                if end_minute >= 60:
                    end_hour += 1
                    end_minute -= 60
                end_time = f"{end_hour:02d}:{end_minute:02d}"

                result["timeline"].append({
                    "name": attr.get("name", ""),
                    "type": "attraction",
                    "start": start_time,
                    "end": end_time,
                    "duration_minutes": duration_minutes
                })

                # Update current time for next attraction (add 30min buffer)
                current_time_hour = end_hour
                current_time_minute = end_minute + 30
                if current_time_minute >= 60:
                    current_time_hour += 1
                    current_time_minute -= 60

    # Add entertainment with virtual time calculation (line 386-427)
    if entertainment and "days" in entertainment:
        day_ent = next((d for d in entertainment["days"] if d.get("day") == day_num), {})
        if "entertainment" in day_ent:
            current_time_hour = 19  # Start entertainment at 19:00
            current_time_minute = 0
            for ent in day_ent["entertainment"]:
                duration_str = ent.get("duration", "2h")
                duration_hours = 2.0
                if "h" in duration_str:
                    try:
                        duration_hours = float(duration_str.replace("h", "").strip())
                    except:
                        duration_hours = 2.0

                start_time = f"{current_time_hour:02d}:{current_time_minute:02d}"
                end_hour = current_time_hour + int(duration_hours)
                end_minute = current_time_minute + int((duration_hours % 1) * 60)
                if end_minute >= 60:
                    end_hour += 1
                    end_minute -= 60
                end_time = f"{end_hour:02d}:{end_minute:02d}"

                result["timeline"].append({
                    "name": ent.get("name", ""),
                    "type": "entertainment",
                    "start": start_time,
                    "end": end_time,
                    "duration": duration_str
                })

                # Update current time for next entertainment
                current_time_hour = end_hour
                current_time_minute = end_minute

    # Sort by start time
    result["timeline"].sort(key=lambda x: x["start"])

    # Check for conflicts
    for i, entry1 in enumerate(result["timeline"]):
        for entry2 in result["timeline"][i+1:]:
            # Parse times
            h1s, m1s = map(int, entry1["start"].split(':'))
            h1e, m1e = map(int, entry1["end"].split(':'))
            h2s, m2s = map(int, entry2["start"].split(':'))
            h2e, m2e = map(int, entry2["end"].split(':'))

            start1 = h1s * 60 + m1s
            end1 = h1e * 60 + m1e
            start2 = h2s * 60 + m2s
            end2 = h2e * 60 + m2e

            # Check overlap
            if start1 < end2 and start2 < end1:
                result["conflicts"].append({
                    "entry1": f"{entry1['name']} ({entry1['start']}-{entry1['end']})",
                    "entry2": f"{entry2['name']} ({entry2['start']}-{entry2['end']})",
                    "overlap_minutes": min(end1, end2) - max(start1, start2)
                })

    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: debug-virtual-times.py <plan-id> <day-num>")
        sys.exit(1)

    plan_id = sys.argv[1]
    day_num = int(sys.argv[2])

    result = simulate_day_timeline(plan_id, day_num)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["conflicts"]:
        print(f"\nFound {len(result['conflicts'])} conflicts!", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\nNo conflicts detected.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
