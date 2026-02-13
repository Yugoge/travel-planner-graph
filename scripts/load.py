#!/usr/bin/env python3
"""
Unified Data Loading Script - 3-Level Hierarchical Access
==========================================================
Single script for all agent data loading with progressive disclosure.

This script replaces all individual load scripts and provides controlled access
to agent data through three levels:

Level 1 (--level 1): Day-level metadata only
  - day, date, location
  - No POI details exposed

Level 2 (--level 2): POI titles/keys only
  - All Level 1 data
  - POI names (name_base, name_local)
  - POI types (type_base)
  - No detailed content (cost, time, coordinates, notes, etc.)

Level 3 (--level 3): Full POI data
  - All Level 1 + Level 2 data
  - Complete POI details (cost, time, coordinates, notes, etc.)
  - Full read/write access

Usage:
  # Load Level 1 (day metadata)
  python3 scripts/load.py --trip TRIP_SLUG --agent meals --level 1

  # Load Level 2 (POI titles)
  python3 scripts/load.py --trip TRIP_SLUG --agent meals --level 2 --day 3

  # Load Level 3 (full data)
  python3 scripts/load.py --trip TRIP_SLUG --agent meals --level 3 --day 3 --poi lunch

  # Batch load multiple agents
  python3 scripts/load.py --trip TRIP_SLUG --agents meals,attractions --level 2

Design Goals:
  - Progressive disclosure: agents only see what they need
  - Reduce context size: avoid loading full JSON unnecessarily
  - Enforce access control: prevent accidental modifications
  - Unified interface: single script for all agents
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Agent-specific POI key mappings
AGENT_POI_KEYS = {
    "meals": ["breakfast", "lunch", "dinner"],
    "attractions": ["attractions"],  # array
    "entertainment": ["entertainment"],  # array
    "accommodation": ["accommodation"],  # singular
    "shopping": ["shopping"],  # array
    "transportation": ["location_change"],  # singular, optional
    "budget": ["budget"],  # singular
    "timeline": ["timeline", "travel_segments"],  # special: object map + array
}

# Fields exposed at each level
LEVEL_1_FIELDS = {"day", "date", "location", "location_base", "location_local"}

LEVEL_2_FIELDS = LEVEL_1_FIELDS | {
    "name_base", "name_local",
    "type_base", "type_local",
    "cuisine_base", "cuisine_local",
    "from_base", "from_local", "to_base", "to_local",
}

# Level 3: all fields (no restriction)


def load_agent_file(trip_slug: str, agent: str) -> Dict[str, Any]:
    """Load complete agent JSON file."""
    trip_dir = DATA_DIR / trip_slug
    agent_file = trip_dir / f"{agent}.json"

    if not agent_file.exists():
        print(f"Error: {agent_file} not found", file=sys.stderr)
        sys.exit(1)

    try:
        with open(agent_file, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Malformed JSON in {agent_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to load {agent_file}: {e}", file=sys.stderr)
        sys.exit(1)


def filter_level_1(data: Dict[str, Any]) -> Dict[str, Any]:
    """Level 1: Day metadata only (no POI details)."""
    filtered_days = []

    for day in data.get("data", {}).get("days", []):
        filtered_day = {k: v for k, v in day.items() if k in LEVEL_1_FIELDS}
        filtered_days.append(filtered_day)

    return {
        "agent": data.get("agent"),
        "status": data.get("status"),
        "data": {"days": filtered_days}
    }


def filter_level_2(data: Dict[str, Any], agent: str, day_num: Optional[int] = None, date_str: Optional[str] = None) -> Dict[str, Any]:
    """Level 2: POI titles/keys only (no detailed content)."""
    filtered_days = []
    poi_keys = AGENT_POI_KEYS.get(agent, [])

    for day in data.get("data", {}).get("days", []):
        if day_num is not None and day.get("day") != day_num:
            continue
        if date_str is not None and day.get("date") != date_str:
            continue

        # Start with Level 1 fields
        filtered_day = {k: v for k, v in day.items() if k in LEVEL_1_FIELDS}

        # Add POI titles/keys
        for poi_key in poi_keys:
            if poi_key not in day:
                continue

            poi_data = day[poi_key]

            if isinstance(poi_data, dict):
                # Singular POI (accommodation, transportation, budget)
                if poi_key == "timeline":
                    # Timeline: object map - just show keys
                    filtered_day[poi_key] = {k: "..." for k in poi_data.keys()}
                elif poi_key == "budget":
                    # Budget: show structure only
                    filtered_day[poi_key] = {k: "..." for k in poi_data.keys()}
                else:
                    # Regular singular POI (accommodation, location_change)
                    filtered_poi = {k: v for k, v in poi_data.items() if k in LEVEL_2_FIELDS}
                    filtered_day[poi_key] = filtered_poi

            elif isinstance(poi_data, list):
                # Array of POIs (attractions, entertainment, shopping, travel_segments)
                filtered_pois = []
                for poi in poi_data:
                    if isinstance(poi, dict):
                        filtered_poi = {k: v for k, v in poi.items() if k in LEVEL_2_FIELDS}
                        filtered_pois.append(filtered_poi)
                filtered_day[poi_key] = filtered_pois

        filtered_days.append(filtered_day)

    return {
        "agent": data.get("agent"),
        "status": data.get("status"),
        "data": {"days": filtered_days}
    }


def filter_level_3(data: Dict[str, Any], agent: str, day_num: Optional[int] = None,
                   poi_key: Optional[str] = None, poi_index: Optional[int] = None,
                   date_str: Optional[str] = None) -> Dict[str, Any]:
    """Level 3: Full POI data (complete read/write access)."""
    if day_num is None and date_str is None:
        # Return full data for all days
        return data

    # Filter to specific day
    filtered_days = []
    for day in data.get("data", {}).get("days", []):
        if day_num is not None and day.get("day") != day_num:
            continue
        if date_str is not None and day.get("date") != date_str:
            continue

        if poi_key is None:
            # Return full day data
            filtered_days.append(day)
        else:
            # Return specific POI only
            filtered_day = {k: v for k, v in day.items() if k in LEVEL_1_FIELDS}

            if poi_key in day:
                poi_data = day[poi_key]

                if isinstance(poi_data, list) and poi_index is not None:
                    # Array POI with index
                    if 0 <= poi_index < len(poi_data):
                        filtered_day[poi_key] = [poi_data[poi_index]]
                    else:
                        print(f"Error: POI index {poi_index} out of range (0-{len(poi_data)-1})", file=sys.stderr)
                        sys.exit(1)
                else:
                    # Singular POI or full array
                    filtered_day[poi_key] = poi_data

            filtered_days.append(filtered_day)

    return {
        "agent": data.get("agent"),
        "status": data.get("status"),
        "data": {"days": filtered_days}
    }


def main():
    parser = argparse.ArgumentParser(
        description="Unified data loading script with 3-level hierarchical access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Level 1: Load day metadata for meals
  python3 scripts/load.py --trip china-feb-2026 --agent meals --level 1

  # Level 2: Load POI titles for Day 3 meals
  python3 scripts/load.py --trip china-feb-2026 --agent meals --level 2 --day 3

  # Level 3: Load full lunch data for Day 3
  python3 scripts/load.py --trip china-feb-2026 --agent meals --level 3 --day 3 --poi lunch

  # Level 3: Load full attraction #2 for Day 5
  python3 scripts/load.py --trip china-feb-2026 --agent attractions --level 3 --day 5 --poi attractions --poi-index 2

  # Batch load: Multiple agents Level 2
  python3 scripts/load.py --trip china-feb-2026 --agents meals,attractions,entertainment --level 2
        """
    )

    parser.add_argument("--trip", required=True, help="Trip slug (directory name in data/)")
    parser.add_argument("--agent", help="Agent name (meals, attractions, etc.)")
    parser.add_argument("--agents", help="Comma-separated agent names for batch loading")
    parser.add_argument("--level", type=int, choices=[1, 2, 3], required=True,
                        help="Access level (1=day metadata, 2=POI titles, 3=full data)")
    parser.add_argument("--day", type=int, help="Filter to specific day number (Level 2/3)")
    parser.add_argument("--date", help="Filter to specific date YYYY-MM-DD (Level 2/3)")
    parser.add_argument("--poi", help="POI key (breakfast/lunch/dinner/attractions/etc.) (Level 3)")
    parser.add_argument("--poi-index", type=int, help="POI array index (Level 3, for arrays)")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    args = parser.parse_args()

    # Validate arguments
    if args.agent and args.agents:
        print("Error: Cannot specify both --agent and --agents", file=sys.stderr)
        sys.exit(1)

    if not args.agent and not args.agents:
        print("Error: Must specify either --agent or --agents", file=sys.stderr)
        sys.exit(1)

    if args.poi and args.level != 3:
        print("Error: --poi requires --level 3", file=sys.stderr)
        sys.exit(1)

    if args.poi_index is not None and not args.poi:
        print("Error: --poi-index requires --poi", file=sys.stderr)
        sys.exit(1)

    if args.day and args.date:
        print("Error: Cannot specify both --day and --date", file=sys.stderr)
        sys.exit(1)

    # Determine agents to load
    agents = args.agents.split(",") if args.agents else [args.agent]

    # Load and filter data
    results = {}

    for agent in agents:
        agent = agent.strip()

        # Load full data
        data = load_agent_file(args.trip, agent)

        # Apply level filter
        if args.level == 1:
            filtered = filter_level_1(data)
        elif args.level == 2:
            filtered = filter_level_2(data, agent, args.day, args.date)
        else:  # level 3
            filtered = filter_level_3(data, agent, args.day, args.poi, args.poi_index, args.date)

        results[agent] = filtered

    # Output
    if len(results) == 1:
        output_data = list(results.values())[0]
    else:
        output_data = results

    json_str = json.dumps(output_data, indent=2 if args.pretty else None, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json_str, encoding="utf-8")
        print(f"✅ Data written to: {output_path}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
