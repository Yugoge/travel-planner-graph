#!/usr/bin/env python3
"""Fix cross-agent location mismatches for the same day.

Different agent JSON files (meals, shopping, entertainment, etc.) sometimes use
different location strings for the same day. This script standardizes them by:
1. Building a consensus location from transportation.json (authoritative for travel days)
2. Using "FromCity / ToCity" format for travel days
3. Using single city name for non-travel days
4. Applying the consensus location to all agent files

Usage:
    fix-cross-agent-locations.py <trip_directory> [--dry-run]
"""

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple


# Agent files that have day-level location fields
AGENT_FILES = [
    "accommodation.json",
    "attractions.json",
    "budget.json",
    "entertainment.json",
    "meals.json",
    "shopping.json",
    "timeline.json",
]


def load_agent_data(trip_dir: str) -> Dict[str, Any]:
    """Load all agent JSON files from a trip directory.

    Returns dict mapping filename -> parsed JSON data.
    """
    agents = {}
    for filename in AGENT_FILES:
        filepath = os.path.join(trip_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                agents[filename] = json.load(f)
    return agents


def get_days_from_agent(agent_data: Dict[str, Any]) -> Optional[List[Dict]]:
    """Extract the days array from an agent's data structure."""
    if "data" in agent_data:
        data = agent_data["data"]
        if isinstance(data, dict) and "days" in data:
            return data["days"]
        if isinstance(data, list):
            return data
    return None


def get_transportation_travel_days(trip_dir: str) -> Dict[int, Tuple[str, str]]:
    """Parse transportation.json to find days with location changes.

    Returns dict mapping day_number -> (from_city, to_city).
    """
    transport_path = os.path.join(trip_dir, "transportation.json")
    if not os.path.exists(transport_path):
        return {}

    with open(transport_path, "r", encoding="utf-8") as f:
        transport_data = json.load(f)

    travel_days = {}
    days = get_days_from_agent(transport_data)
    if not days:
        return {}

    for day_entry in days:
        day_num = day_entry.get("day")
        if day_num is None:
            continue

        loc_change = day_entry.get("location_change")
        if loc_change and isinstance(loc_change, dict):
            from_city = loc_change.get("from", "")
            to_city = loc_change.get("to", "")
            if from_city and to_city:
                travel_days[day_num] = (from_city, to_city)

    return travel_days


def collect_all_locations(
    agents: Dict[str, Any],
) -> Dict[int, Dict[str, str]]:
    """Collect location strings from all agents for each day.

    Returns dict mapping day_number -> {filename: location_string}.
    """
    all_locations: Dict[int, Dict[str, str]] = {}

    for filename, agent_data in agents.items():
        days = get_days_from_agent(agent_data)
        if not days:
            continue

        for day_entry in days:
            day_num = day_entry.get("day")
            if day_num is None:
                continue

            location = day_entry.get("location")
            if location:
                if day_num not in all_locations:
                    all_locations[day_num] = {}
                all_locations[day_num][filename] = location

    return all_locations


def has_mismatch(agent_locations: Dict[str, str]) -> bool:
    """Check if agents disagree on location for a day."""
    unique_locations = set(agent_locations.values())
    return len(unique_locations) > 1


def determine_consensus_location(
    day_num: int,
    agent_locations: Dict[str, str],
    travel_days: Dict[int, Tuple[str, str]],
) -> Optional[str]:
    """Determine the correct standardized location for a given day.

    Only returns a value when agents disagree (mismatch exists).
    For travel days (location_change in transportation.json), use "FromCity / ToCity".
    For non-travel days with mismatch, use the most common location among agents.
    Returns None if all agents already agree (no fix needed).
    """
    if not has_mismatch(agent_locations):
        return None  # All agents agree, no fix needed

    # Agents disagree -- determine the correct location
    if day_num in travel_days:
        from_city, to_city = travel_days[day_num]
        return f"{from_city} / {to_city}"

    # Non-travel day with mismatch: pick the most common location string
    location_counts = Counter(agent_locations.values())
    most_common = location_counts.most_common(1)
    if most_common:
        return most_common[0][0]

    # Fallback: return first available
    return next(iter(agent_locations.values()))


def apply_consensus_locations(
    agents: Dict[str, Any],
    consensus: Dict[int, str],
) -> Dict[str, List[Dict[str, str]]]:
    """Apply consensus locations to all agent day entries.

    Returns a changelog: {filename: [{day, old, new}, ...]}.
    """
    changelog: Dict[str, List[Dict[str, str]]] = {}

    for filename, agent_data in agents.items():
        days = get_days_from_agent(agent_data)
        if not days:
            continue

        file_changes = []
        for day_entry in days:
            day_num = day_entry.get("day")
            if day_num is None or day_num not in consensus:
                continue

            old_location = day_entry.get("location", "")
            new_location = consensus[day_num]

            if old_location != new_location and old_location:
                file_changes.append({
                    "day": day_num,
                    "old": old_location,
                    "new": new_location,
                })
                day_entry["location"] = new_location

        if file_changes:
            changelog[filename] = file_changes

    return changelog


def save_agents(trip_dir: str, agents: Dict[str, Any]) -> None:
    """Save modified agent data back to JSON files."""
    for filename, agent_data in agents.items():
        filepath = os.path.join(trip_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(agent_data, f, indent=2, ensure_ascii=False)
            f.write("\n")


def print_changelog(trip_dir: str, changelog: Dict[str, List[Dict]]) -> None:
    """Print a human-readable diff of all location changes."""
    if not changelog:
        print(f"  No location mismatches found in {os.path.basename(trip_dir)}")
        return

    total_changes = sum(len(changes) for changes in changelog.values())
    print(f"\n  Trip: {os.path.basename(trip_dir)}")
    print(f"  Total changes: {total_changes}")
    print(f"  {'─' * 60}")

    for filename, changes in sorted(changelog.items()):
        for change in sorted(changes, key=lambda c: c["day"]):
            print(
                f"  {filename:25s} Day {change['day']:2d}: "
                f'"{change["old"]}" -> "{change["new"]}"'
            )


def process_trip(trip_dir: str, dry_run: bool = False) -> Dict[str, List[Dict]]:
    """Process a single trip directory to fix location mismatches.

    Returns the changelog of applied changes.
    """
    if not os.path.isdir(trip_dir):
        print(f"Error: Directory not found: {trip_dir}", file=sys.stderr)
        return {}

    # Step 1: Load all agent files
    agents = load_agent_data(trip_dir)
    if not agents:
        print(f"  No agent files found in {trip_dir}", file=sys.stderr)
        return {}

    # Step 2: Get travel days from transportation.json
    travel_days = get_transportation_travel_days(trip_dir)

    # Step 3: Collect all locations across agents
    all_locations = collect_all_locations(agents)

    # Step 4: Build consensus only for days with mismatches
    consensus: Dict[int, str] = {}
    for day_num in sorted(all_locations.keys()):
        agent_locs = all_locations[day_num]
        resolved = determine_consensus_location(
            day_num, agent_locs, travel_days
        )
        if resolved is not None:
            consensus[day_num] = resolved

    # Step 5: Apply consensus and collect changelog
    changelog = apply_consensus_locations(agents, consensus)

    # Step 6: Save or report
    print_changelog(trip_dir, changelog)

    if not dry_run and changelog:
        save_agents(trip_dir, agents)
        print(f"  Files saved.")
    elif dry_run and changelog:
        print(f"  (dry-run mode, no files modified)")

    return changelog


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fix cross-agent location mismatches in travel plan data"
    )
    parser.add_argument(
        "trip_dirs",
        nargs="+",
        help="One or more trip directory paths to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files",
    )
    args = parser.parse_args()

    print("Cross-Agent Location Mismatch Fixer")
    print("=" * 60)

    total_changes = 0
    for trip_dir in args.trip_dirs:
        changelog = process_trip(trip_dir, dry_run=args.dry_run)
        total_changes += sum(len(c) for c in changelog.values())

    print(f"\n{'=' * 60}")
    print(f"Total location changes across all trips: {total_changes}")

    return 0 if total_changes >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
