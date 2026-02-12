#!/usr/bin/env python3
"""
Clean Redundant Fields from Agent Data
=======================================
Automatically remove redundant fields detected by plan-validate.py

This script:
1. Runs plan-validate.py to detect redundant fields
2. Removes fields reported as "Unexpected fields"
3. Saves cleaned data with validation
4. Creates backups before modification

Usage:
  # Clean specific agent
  python3 scripts/clean-redundant-fields.py --trip TRIP_SLUG --agent meals

  # Clean all agents in trip
  python3 scripts/clean-redundant-fields.py --trip TRIP_SLUG --all

  # Dry run (show what would be removed)
  python3 scripts/clean-redundant-fields.py --trip TRIP_SLUG --agent meals --dry-run
"""

import json
import sys
import argparse
import subprocess
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.json_io import load_agent_json, save_agent_json, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLAN_VALIDATE = PROJECT_ROOT / "scripts" / "plan-validate.py"

AGENT_LIST = ["meals", "attractions", "entertainment", "accommodation",
              "shopping", "transportation", "timeline", "budget"]


def run_plan_validate(trip_slug: str, agent: str = None) -> dict:
    """Run plan-validate.py and parse output to find redundant fields.

    Returns:
        Dict mapping agent -> day -> poi_key -> set(redundant_fields)
    """
    cmd = [sys.executable, str(PLAN_VALIDATE), trip_slug, "--json"]
    if agent:
        cmd.extend(["--agent", agent])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode not in (0, 1):  # 0=pass, 1=fail (expected with HIGH issues)
        print(f"❌ Error running plan-validate.py:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    try:
        validation_data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing plan-validate output: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse issues to find redundant fields
    redundant_map = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    for issue in validation_data.get("issues", []):
        if issue.get("field") == "additional_properties" and issue.get("severity") == "HIGH":
            # Parse message: "Unexpected fields: field1, field2, field3 (schema forbids extra fields)"
            message = issue.get("message", "")
            match = re.search(r"Unexpected fields: ([^(]+)", message)
            if match:
                fields_str = match.group(1).strip()
                redundant_fields = {f.strip() for f in fields_str.split(",")}

                agent_name = issue.get("agent")
                day_num = issue.get("day")
                label = issue.get("label", "")

                # Extract POI key from label
                # Format: "Day N (date) poi_key: name"
                poi_match = re.search(r"\) ([^:]+):", label)
                if poi_match:
                    poi_key = poi_match.group(1).strip()
                    redundant_map[agent_name][day_num][poi_key].update(redundant_fields)

    return redundant_map


def clean_agent_data(trip_slug: str, agent: str, redundant_map: dict, dry_run: bool = False) -> int:
    """Clean redundant fields from agent data.

    Returns:
        Number of fields removed
    """
    trip_dir = DATA_DIR / trip_slug
    agent_file = trip_dir / f"{agent}.json"

    if not agent_file.exists():
        print(f"⚠️  {agent}.json not found", file=sys.stderr)
        return 0

    # Load data
    try:
        data = load_agent_json(agent_file)
    except Exception as e:
        print(f"❌ Error loading {agent}.json: {e}", file=sys.stderr)
        return 0

    if agent not in redundant_map:
        print(f"✅ {agent}: No redundant fields detected", file=sys.stderr)
        return 0

    # Clean fields
    fields_removed = 0
    agent_redundant = redundant_map[agent]

    for day in data.get("days", []):
        day_num = day.get("day")
        if day_num not in agent_redundant:
            continue

        day_redundant = agent_redundant[day_num]

        # Get POI keys for this agent
        from load import AGENT_POI_KEYS
        poi_keys = AGENT_POI_KEYS.get(agent, [])

        for poi_key in poi_keys:
            if poi_key not in day:
                continue

            poi_data = day[poi_key]

            # Handle arrays
            if isinstance(poi_data, list):
                for idx, poi in enumerate(poi_data):
                    if isinstance(poi, dict) and poi_key in day_redundant:
                        redundant_fields = day_redundant[poi_key]
                        for field in redundant_fields:
                            if field in poi:
                                if dry_run:
                                    print(f"  [DRY RUN] Would remove: Day {day_num} {poi_key}[{idx}].{field}",
                                          file=sys.stderr)
                                else:
                                    del poi[field]
                                    fields_removed += 1

            # Handle singular POI
            elif isinstance(poi_data, dict) and poi_key in day_redundant:
                redundant_fields = day_redundant[poi_key]
                for field in redundant_fields:
                    if field in poi_data:
                        if dry_run:
                            print(f"  [DRY RUN] Would remove: Day {day_num} {poi_key}.{field}",
                                  file=sys.stderr)
                        else:
                            del poi_data[field]
                            fields_removed += 1

    if dry_run:
        print(f"✅ {agent}: {fields_removed} fields would be removed", file=sys.stderr)
        return fields_removed

    if fields_removed == 0:
        print(f"✅ {agent}: No fields removed", file=sys.stderr)
        return 0

    # Save cleaned data
    try:
        save_agent_json(
            file_path=agent_file,
            agent_name=agent,
            data=data,
            validate=True,
            create_backup=True
        )
        print(f"✅ {agent}: Removed {fields_removed} redundant fields", file=sys.stderr)
        return fields_removed

    except ValidationError as e:
        print(f"❌ {agent}: Validation failed after cleanup:", file=sys.stderr)
        for issue in e.high_issues[:5]:
            print(f"  - {issue.message}", file=sys.stderr)
        print(f"   Restored from backup", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"❌ {agent}: Save error: {e}", file=sys.stderr)
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Clean redundant fields from agent data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean specific agent
  python3 scripts/clean-redundant-fields.py --trip china-feb-2026 --agent meals

  # Clean all agents
  python3 scripts/clean-redundant-fields.py --trip china-feb-2026 --all

  # Dry run (show what would be removed)
  python3 scripts/clean-redundant-fields.py --trip china-feb-2026 --agent meals --dry-run
        """
    )

    parser.add_argument("--trip", required=True, help="Trip slug (directory name in data/)")
    parser.add_argument("--agent", help="Agent name (meals, attractions, etc.)")
    parser.add_argument("--all", action="store_true", help="Clean all agents")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without modifying files")

    args = parser.parse_args()

    if not args.agent and not args.all:
        print("Error: Must specify either --agent or --all", file=sys.stderr)
        sys.exit(1)

    if args.agent and args.all:
        print("Error: Cannot specify both --agent and --all", file=sys.stderr)
        sys.exit(1)

    # Determine agents to clean
    agents = AGENT_LIST if args.all else [args.agent]

    print(f"🔍 Step 1: Running plan-validate.py to detect redundant fields...", file=sys.stderr)
    print("", file=sys.stderr)

    # Run validation
    redundant_map = run_plan_validate(args.trip, None if args.all else args.agent)

    if not redundant_map:
        print("✅ No redundant fields detected", file=sys.stderr)
        sys.exit(0)

    # Report findings
    total_issues = sum(
        len(pois)
        for agent_data in redundant_map.values()
        for day_data in agent_data.values()
        for pois in day_data.values()
    )

    print(f"📊 Found redundant fields in {len(redundant_map)} agents ({total_issues} locations)",
          file=sys.stderr)
    print("", file=sys.stderr)

    if args.dry_run:
        print(f"🔍 Step 2: Dry run (showing what would be removed)...", file=sys.stderr)
    else:
        print(f"🧹 Step 2: Cleaning redundant fields...", file=sys.stderr)

    print("", file=sys.stderr)

    # Clean each agent
    total_removed = 0

    for agent in agents:
        removed = clean_agent_data(args.trip, agent, redundant_map, args.dry_run)
        total_removed += removed

    print("", file=sys.stderr)

    if args.dry_run:
        print(f"✅ Dry run complete: {total_removed} fields would be removed", file=sys.stderr)
    else:
        print(f"✅ Cleanup complete: {total_removed} redundant fields removed", file=sys.stderr)
        print(f"📦 Backups created with .bak extension", file=sys.stderr)


if __name__ == "__main__":
    main()
