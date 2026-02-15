#!/usr/bin/env python3
"""
Unified Data Saving Script - Batch Validation and Atomic Writes
================================================================
Single script for all agent data saving with mandatory validation.

This script replaces all individual save scripts and enforces:
  - Automatic validation (plan-validate.py)
  - Atomic writes (.tmp → rename)
  - Automatic backups (.bak)
  - Batch operations with rollback
  - HIGH severity issues block saves

Usage:
  # Save single agent data (full-file replacement)
  python3 scripts/save.py --trip TRIP_SLUG --agent meals --input data.json

  # Merge single-day update into multi-day file (preserves other days)
  python3 scripts/save.py --trip TRIP_SLUG --agent timeline --input day5_update.json --merge-days

  # Save from stdin (pipe)
  cat modified_data.json | python3 scripts/save.py --trip TRIP_SLUG --agent meals

  # Batch save multiple agents
  python3 scripts/save.py --trip TRIP_SLUG --batch agents_data.json

  # Skip validation (DANGEROUS - not recommended)
  python3 scripts/save.py --trip TRIP_SLUG --agent meals --input data.json --no-validate

  # Allow HIGH severity issues (DANGEROUS)
  python3 scripts/save.py --trip TRIP_SLUG --agent meals --input data.json --allow-high

Design Goals:
  - Mandatory validation: prevent data corruption
  - Atomic operations: prevent partial writes
  - Rollback support: batch operations all-or-nothing
  - Error reporting: detailed issue reporting
"""

import json
import sys
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from lib
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.json_io import (
    save_agent_json,
    load_agent_json,
    merge_agent_days,
    ValidationError,
    AtomicWriteError,
    validate_agent_data
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLAN_VALIDATE = PROJECT_ROOT / "scripts" / "plan-validate.py"


def validate_data(trip_slug: str, agent: str, data: Dict[str, Any],
                  skip_validation: bool = False,
                  allow_high: bool = False) -> tuple:
    """Run plan-validate.py validation.

    Returns:
        (success: bool, issues: list, metrics: dict)
    """
    if skip_validation:
        print("⚠️  WARNING: Validation skipped (--no-validate)", file=sys.stderr)
        return True, [], {}

    # Use json_io validation which calls plan-validate.py
    try:
        trip_dir = DATA_DIR / trip_slug
        issues, metrics = validate_agent_data(agent, data, trip_dir)

        # Check for HIGH severity issues
        high_issues = [
            i for i in issues
            if (i.severity.value if hasattr(i.severity, 'value') else i.severity) == "HIGH"
        ]
        if high_issues and not allow_high:
            raise ValidationError(issues, metrics)

        return True, [], {}

    except ValidationError as e:
        if allow_high:
            print(f"⚠️  WARNING: HIGH severity issues present but --allow-high specified",
                  file=sys.stderr)
            return True, e.issues, e.metrics
        else:
            print(f"❌ Validation failed with {len(e.high_issues)} HIGH severity issues:",
                  file=sys.stderr)
            for issue in e.high_issues[:10]:
                print(f"  - {issue.label}: {issue.field} — {issue.message}", file=sys.stderr)
            if len(e.high_issues) > 10:
                print(f"  ... and {len(e.high_issues) - 10} more HIGH severity issues",
                      file=sys.stderr)
            return False, e.issues, e.metrics


def save_single_agent(trip_slug: str, agent: str, data: Dict[str, Any],
                      skip_validation: bool = False,
                      allow_high: bool = False,
                      create_backup: bool = True,
                      merge_days: bool = False) -> bool:
    """Save single agent data with validation.

    Root Cause Reference (b057f26, 579f972, 921f855, 894b008):
    save.py was documented as merging but only performed full-file replacement,
    causing timeline data loss (21 days → 1 day during Day 5 review).

    Args:
        merge_days: If True, merge single-day updates into existing multi-day file
                    instead of replacing entire file. Preserves days not in update.

    Returns:
        True if successful, False otherwise
    """
    trip_dir = DATA_DIR / trip_slug
    if not trip_dir.exists():
        print(f"❌ Error: Trip directory not found: {trip_dir}", file=sys.stderr)
        return False

    agent_file = trip_dir / f"{agent}.json"

    # Unwrap envelope if present
    agent_data = data.get("data") if "data" in data else data

    # Merge mode: read existing file and merge days
    if merge_days and agent_file.exists():
        try:
            existing_data = load_agent_json(agent_file, validate=False)
            merged_data = merge_agent_days(existing_data, agent_data, agent)
            agent_data = merged_data
            print(f"🔀 Merge mode: Merged {len(data.get('data', {}).get('days', []))} day(s) into existing file", file=sys.stderr)
        except Exception as e:
            print(f"❌ Merge failed: {e}", file=sys.stderr)
            return False

    # Wrap in envelope for validation
    envelope_data = {"agent": agent, "status": "complete", "data": agent_data}

    # Validate merged data
    success, issues, metrics = validate_data(trip_slug, agent, envelope_data, skip_validation, allow_high)

    if not success:
        print(f"\n❌ Save aborted due to validation errors", file=sys.stderr)
        print(f"   Fix HIGH severity issues and try again", file=sys.stderr)
        print(f"   Or use --allow-high to force save (NOT RECOMMENDED)", file=sys.stderr)
        return False

    # Save using json_io
    try:
        save_agent_json(
            file_path=agent_file,
            agent_name=agent,
            data=agent_data,
            validate=False,  # Already validated above
            create_backup=create_backup
        )

        print(f"✅ Saved: {agent_file}", file=sys.stderr)

        if issues:
            med_count = len([i for i in issues if i.severity.value == "MEDIUM"])
            low_count = len([i for i in issues if i.severity.value == "LOW"])
            if med_count or low_count:
                print(f"   ⚠️  Warnings: {med_count} MEDIUM, {low_count} LOW", file=sys.stderr)

        return True

    except AtomicWriteError as e:
        print(f"❌ Write error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return False


def save_batch(trip_slug: str, batch_data: Dict[str, Any],
               skip_validation: bool = False,
               allow_high: bool = False) -> bool:
    """Save multiple agents with rollback on failure.

    batch_data format:
    {
      "meals": {...},
      "attractions": {...},
      ...
    }

    Returns:
        True if all saves successful, False otherwise
    """
    trip_dir = DATA_DIR / trip_slug
    if not trip_dir.exists():
        print(f"❌ Error: Trip directory not found: {trip_dir}", file=sys.stderr)
        return False

    print(f"📦 Batch save: {len(batch_data)} agents", file=sys.stderr)

    # Phase 1: Validate all
    print(f"\n1️⃣  Phase 1: Validating {len(batch_data)} agents...", file=sys.stderr)
    validation_results = {}

    for agent, data in batch_data.items():
        print(f"   Validating {agent}...", end=" ", file=sys.stderr)
        success, issues, metrics = validate_data(trip_slug, agent, data, skip_validation, allow_high)
        validation_results[agent] = (success, issues, metrics)

        if success:
            print("✅", file=sys.stderr)
        else:
            print("❌", file=sys.stderr)

    # Check if any failed
    failed_agents = [agent for agent, (success, _, _) in validation_results.items() if not success]

    if failed_agents:
        print(f"\n❌ Validation failed for {len(failed_agents)} agents: {', '.join(failed_agents)}",
              file=sys.stderr)
        print(f"   Batch save aborted (no files modified)", file=sys.stderr)
        return False

    # Phase 2: Create backups
    print(f"\n2️⃣  Phase 2: Creating backups...", file=sys.stderr)
    backup_paths = {}

    for agent in batch_data.keys():
        agent_file = trip_dir / f"{agent}.json"
        if agent_file.exists():
            backup_path = agent_file.with_suffix(".json.bak")
            shutil.copy2(agent_file, backup_path)
            backup_paths[agent] = backup_path
            print(f"   {agent}: {backup_path.name}", file=sys.stderr)

    # Phase 3: Save all
    print(f"\n3️⃣  Phase 3: Saving {len(batch_data)} agents...", file=sys.stderr)
    save_errors = []

    for agent, data in batch_data.items():
        agent_file = trip_dir / f"{agent}.json"

        try:
            # Use json_io save
            save_agent_json(
                file_path=agent_file,
                agent_name=agent,
                data=data.get("data") if "data" in data else data,
                validate=False,  # Already validated
                create_backup=False  # Already created backups
            )
            print(f"   {agent}: ✅", file=sys.stderr)

        except Exception as e:
            print(f"   {agent}: ❌ {e}", file=sys.stderr)
            save_errors.append((agent, str(e)))

    # Phase 4: Rollback if any errors
    if save_errors:
        print(f"\n4️⃣  Phase 4: Rolling back {len(save_errors)} failed saves...", file=sys.stderr)

        for agent, backup_path in backup_paths.items():
            agent_file = trip_dir / f"{agent}.json"
            shutil.copy2(backup_path, agent_file)
            print(f"   {agent}: restored from backup", file=sys.stderr)

        print(f"\n❌ Batch save failed, all changes rolled back", file=sys.stderr)
        return False

    # Success
    print(f"\n✅ Batch save successful: {len(batch_data)} agents", file=sys.stderr)

    # Report warnings
    total_warnings = sum(
        len([i for i in issues if i.severity.value in ("MEDIUM", "LOW")])
        for _, issues, _ in validation_results.values()
    )
    if total_warnings:
        print(f"   ⚠️  Total warnings: {total_warnings}", file=sys.stderr)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Unified data saving script with mandatory validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Save single agent from file
  python3 scripts/save.py --trip china-feb-2026 --agent meals --input modified_meals.json

  # Merge single-day update into multi-day file (preserves other days)
  python3 scripts/save.py --trip china-feb-2026 --agent timeline --input day5_update.json --merge-days

  # Save single agent from stdin
  cat modified_meals.json | python3 scripts/save.py --trip china-feb-2026 --agent meals

  # Batch save multiple agents
  python3 scripts/save.py --trip china-feb-2026 --batch batch_data.json

  # Skip validation (NOT RECOMMENDED)
  python3 scripts/save.py --trip china-feb-2026 --agent meals --input data.json --no-validate

  # Allow HIGH severity issues (NOT RECOMMENDED)
  python3 scripts/save.py --trip china-feb-2026 --agent meals --input data.json --allow-high
        """
    )

    parser.add_argument("--trip", required=True, help="Trip slug (directory name in data/)")
    parser.add_argument("--agent", help="Agent name (meals, attractions, etc.)")
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--batch", help="Batch input JSON file (multiple agents)")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation (DANGEROUS)")
    parser.add_argument("--allow-high", action="store_true", help="Allow HIGH severity issues (DANGEROUS)")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--merge-days", action="store_true",
                        help="Merge single-day updates into existing multi-day file (preserves other days)")

    args = parser.parse_args()

    # Validate arguments
    if args.batch and args.agent:
        print("Error: Cannot specify both --batch and --agent", file=sys.stderr)
        sys.exit(1)

    if not args.batch and not args.agent:
        print("Error: Must specify either --batch or --agent", file=sys.stderr)
        sys.exit(1)

    if args.batch and args.input:
        print("Error: --batch and --input are mutually exclusive", file=sys.stderr)
        sys.exit(1)

    # Load input data
    if args.batch:
        # Batch mode
        batch_path = Path(args.batch)
        if not batch_path.exists():
            print(f"Error: Batch file not found: {batch_path}", file=sys.stderr)
            sys.exit(1)

        with open(batch_path, encoding="utf-8") as f:
            batch_data = json.load(f)

        success = save_batch(
            trip_slug=args.trip,
            batch_data=batch_data,
            skip_validation=args.no_validate,
            allow_high=args.allow_high
        )

    else:
        # Single agent mode
        if args.input:
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Error: Input file not found: {input_path}", file=sys.stderr)
                sys.exit(1)

            with open(input_path, encoding="utf-8") as f:
                data = json.load(f)
        else:
            # Read from stdin
            data = json.load(sys.stdin)

        success = save_single_agent(
            trip_slug=args.trip,
            agent=args.agent,
            data=data,
            skip_validation=args.no_validate,
            allow_high=args.allow_high,
            create_backup=not args.no_backup,
            merge_days=args.merge_days
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
