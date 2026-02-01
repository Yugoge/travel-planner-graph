#!/usr/bin/env python3
"""
Timeline Agent - Creates detailed daily timelines and detects scheduling conflicts.
This agent runs AFTER all other agents complete their tasks.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class TimelineAgent:
    """Generates timelines from trip planning data and validates schedules."""

    def __init__(self, destination_slug: str):
        """Initialize the timeline agent with a destination."""
        self.destination_slug = destination_slug
        self.data_dir = Path(f"/root/travel-planner/data/{destination_slug}")
        self.warnings = []
        self.timeline_data = None

    def load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load and parse JSON file from data directory."""
        file_path = self.data_dir / filename
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found in {self.data_dir}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: {filename} contains invalid JSON")
            return {}

    def time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM format to minutes since midnight."""
        try:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes
        except ValueError:
            return 0

    def minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to HH:MM format."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    def calculate_end_time(self, start_time: str, duration_minutes: int) -> str:
        """Calculate end time given start time and duration."""
        start_mins = self.time_to_minutes(start_time)
        end_mins = start_mins + duration_minutes
        return self.minutes_to_time(end_mins)

    def detect_conflicts(self, timeline: Dict[str, Dict]) -> List[str]:
        """Detect overlapping activities in timeline."""
        conflicts = []
        activities = list(timeline.items())

        for i, (name1, activity1) in enumerate(activities):
            start1 = self.time_to_minutes(activity1["start_time"])
            end1 = self.time_to_minutes(activity1["end_time"])

            for name2, activity2 in activities[i + 1 :]:
                start2 = self.time_to_minutes(activity2["start_time"])
                end2 = self.time_to_minutes(activity2["end_time"])

                # Check for overlap
                if start1 < end2 and end1 > start2:
                    conflicts.append(
                        f"Overlap: {name1} ({activity1['start_time']}-"
                        f"{activity1['end_time']}) conflicts with "
                        f"{name2} ({activity2['start_time']}-{activity2['end_time']})"
                    )

        return conflicts

    def validate_meal_times(self, day: int, timeline: Dict[str, Dict]) -> None:
        """Validate that meal times fall within reasonable windows."""
        meal_windows = {
            "breakfast": (420, 600),  # 7:00 AM - 10:00 AM (minutes)
            "lunch": (720, 900),  # 12:00 PM - 3:00 PM
            "dinner": (1080, 1320),  # 6:00 PM - 10:00 PM
        }

        for activity_name, activity in timeline.items():
            for meal_type, (start_min, end_min) in meal_windows.items():
                if meal_type.lower() in activity_name.lower():
                    meal_start = self.time_to_minutes(activity["start_time"])
                    if not (start_min <= meal_start <= end_min):
                        time_str = activity["start_time"]
                        self.warnings.append(
                            f"Day {day}: {activity_name} at {time_str} "
                            f"falls outside typical {meal_type} window"
                        )

    def validate_day_schedule(self, day: int, timeline: Dict[str, Dict]) -> None:
        """Check if day schedule is reasonable."""
        if not timeline:
            return

        times = []
        for activity in timeline.values():
            times.append(self.time_to_minutes(activity["start_time"]))
            times.append(self.time_to_minutes(activity["end_time"]))

        if not times:
            return

        earliest = min(times)
        latest = max(times)

        # Check wake-up time
        if earliest < 360:  # Before 6:00 AM
            wake_time = self.minutes_to_time(earliest)
            self.warnings.append(
                f"Day {day}: Very early wake-up at {wake_time} - verify feasibility"
            )

        # Check bedtime
        if latest > 1380:  # After 11:00 PM
            bed_time = self.minutes_to_time(latest)
            self.warnings.append(
                f"Day {day}: Late bedtime at {bed_time} - verify feasibility"
            )

        # Check total duration
        total_minutes = latest - earliest
        if total_minutes > 900:  # More than 15 hours
            hours = total_minutes / 60
            self.warnings.append(
                f"Day {day}: Very long day ({hours:.1f} hours) - consider if schedule is sustainable"
            )

    def build_timeline_for_day(self, day: int) -> Dict[str, Dict]:
        """Build timeline dictionary for a single day."""
        timeline = {}

        # Load all data files
        skeleton = self.load_json_file("plan-skeleton.json")
        accommodation = self.load_json_file("accommodation.json")
        meals = self.load_json_file("meals.json")
        attractions = self.load_json_file("attractions.json")
        transportation = self.load_json_file("transportation.json")
        entertainment = self.load_json_file("entertainment.json")
        shopping = self.load_json_file("shopping.json")

        # Add accommodation check-out
        for hotel in accommodation.get("data", {}).get("hotels", []):
            if hotel.get("day") == day:
                timeline["Hotel check-out"] = {
                    "start_time": hotel.get("check_out_time", "11:00"),
                    "end_time": self.calculate_end_time(
                        hotel.get("check_out_time", "11:00"), 15
                    ),
                    "duration_minutes": 15,
                }

        # Add meals
        for meal in meals.get("data", {}).get("meals", []):
            if meal.get("day") == day:
                meal_name = meal.get("name", f"{meal.get('type', 'Meal')}")
                timeline[meal_name] = {
                    "start_time": meal.get("time"),
                    "end_time": self.calculate_end_time(
                        meal.get("time"), meal.get("duration_minutes", 60)
                    ),
                    "duration_minutes": meal.get("duration_minutes", 60),
                }

        # Add attractions
        for attraction in attractions.get("data", {}).get("attractions", []):
            if attraction.get("day") == day:
                attr_name = attraction.get("name", "Attraction")
                recommended_time = attraction.get("recommended_time", "10:00")
                timeline[attr_name] = {
                    "start_time": recommended_time,
                    "end_time": self.calculate_end_time(
                        recommended_time, attraction.get("duration_minutes", 120)
                    ),
                    "duration_minutes": attraction.get("duration_minutes", 120),
                }

        # Add entertainment shows
        for show in entertainment.get("data", {}).get("shows", []):
            if show.get("day") == day:
                show_name = show.get("name", "Show")
                timeline[show_name] = {
                    "start_time": show.get("start_time"),
                    "end_time": self.calculate_end_time(
                        show.get("start_time"), show.get("duration_minutes", 120)
                    ),
                    "duration_minutes": show.get("duration_minutes", 120),
                }

        # Add shopping locations
        for shop in shopping.get("data", {}).get("locations", []):
            if shop.get("day") == day:
                shop_name = shop.get("name", "Shopping")
                timeline[shop_name] = {
                    "start_time": shop.get("start_time", "10:00"),
                    "end_time": self.calculate_end_time(
                        shop.get("start_time", "10:00"),
                        shop.get("duration_minutes", 120),
                    ),
                    "duration_minutes": shop.get("duration_minutes", 120),
                }

        # Validate and detect issues
        conflicts = self.detect_conflicts(timeline)
        if conflicts:
            self.warnings.extend([f"Day {day}: {c}" for c in conflicts])

        self.validate_meal_times(day, timeline)
        self.validate_day_schedule(day, timeline)

        return timeline

    def run(self) -> Dict[str, Any]:
        """Execute the timeline agent and generate output."""
        print(f"Timeline Agent: Processing {self.destination_slug}...")

        # Load plan skeleton
        skeleton = self.load_json_file("plan-skeleton.json")
        days = skeleton.get("days", []) or skeleton.get("data", {}).get("days", [])

        if not days:
            print("Error: No days found in plan-skeleton.json")
            return {"agent": "timeline", "status": "error"}

        # Build timelines for each day
        output = {
            "agent": "timeline",
            "status": "complete",
            "data": {"days": []},
            "warnings": [],
            "notes": "Timeline validation completed",
        }

        for day_info in days:
            day_num = day_info.get("day", 1)
            timeline = self.build_timeline_for_day(day_num)

            output["data"]["days"].append(
                {
                    "day": day_num,
                    "date": day_info.get("date", ""),
                    "timeline": timeline,
                }
            )

        output["warnings"] = self.warnings

        return output

    def save_output(self, output: Dict[str, Any]) -> bool:
        """Save timeline output to JSON file."""
        output_path = self.data_dir / "timeline.json"
        try:
            with open(output_path, "w") as f:
                json.dump(output, f, indent=2)
            print(f"Success: Timeline saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving timeline: {e}")
            return False


def main():
    """Main entry point for timeline agent."""
    if len(sys.argv) < 2:
        print("Usage: timeline_agent.py <destination_slug>")
        sys.exit(1)

    destination_slug = sys.argv[1]
    agent = TimelineAgent(destination_slug)
    output = agent.run()
    success = agent.save_output(output)

    if success:
        print("Timeline agent completed successfully")
        print(f"Warnings generated: {len(output.get('warnings', []))}")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
