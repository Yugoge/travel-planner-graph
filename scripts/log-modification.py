#!/usr/bin/env python3
"""
Modification Logging Helper - Append structured log entry to modification-log.json
==================================================================================
Root cause commits: ef0ed28, f9634dc - timeline data loss without tracking

This script appends structured modification log entries to track all agent changes.

Usage:
  # Log a modification with required fields
  python log-modification.py \\
    --trip TRIP_SLUG \\
    --agent AGENT_NAME \\
    --file FILE_NAME \\
    --action ACTION \\
    --description "What changed and why" \\
    --fields "field1,field2,field3"

  # Example: Timeline agent modifying timeline.json
  python log-modification.py \\
    --trip china-feb-15-mar-7-2026-20260202-195429 \\
    --agent timeline \\
    --file timeline.json \\
    --action update \\
    --description "Updated Day 3 timeline to fix overlapping activities" \\
    --fields "days[2].timeline,days[2].warnings"

Exit codes:
  0 = success (log entry appended)
  1 = validation error (missing required parameters)
  2 = file I/O error
  3 = invalid trip directory

Design Goals:
  - Parameterized (no hardcoded values)
  - Machine-readable JSON output
  - Atomic writes with rollback
  - Validation of required fields
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def validate_trip_directory(trip_slug: str) -> Path:
    """Validate trip directory exists.

    Returns:
        Path to trip directory

    Raises:
        SystemExit(3) if directory not found
    """
    trip_dir = DATA_DIR / trip_slug
    if not trip_dir.exists():
        print(f"❌ Error: Trip directory not found: {trip_dir}", file=sys.stderr)
        print(f"   Available trips:", file=sys.stderr)
        for d in DATA_DIR.iterdir():
            if d.is_dir():
                print(f"   - {d.name}", file=sys.stderr)
        sys.exit(3)

    return trip_dir


def append_log_entry(
    trip_dir: Path,
    agent: str,
    file: str,
    action: str,
    description: str,
    changed_fields: List[str]
) -> bool:
    """Append log entry to modification-log.json.

    Args:
        trip_dir: Path to trip directory
        agent: Agent name (timeline, meals, etc.)
        file: File name being modified (timeline.json, etc.)
        action: Action type (create, update, delete)
        description: Human-readable description of what changed
        changed_fields: List of JSON paths that were modified

    Returns:
        True if successful

    Raises:
        SystemExit(2) on file I/O errors
    """
    log_file = trip_dir / "modification-log.json"

    # Create log structure if file doesn't exist
    if not log_file.exists():
        log_data = {
            "trip_slug": trip_dir.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "modifications": []
        }
    else:
        # Read existing log
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {log_file}: {e}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"❌ Error reading {log_file}: {e}", file=sys.stderr)
            sys.exit(2)

    # Create new log entry
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "file": file,
        "action": action,
        "description": description,
        "changed_fields": changed_fields
    }

    # Append entry
    log_data["modifications"].append(log_entry)

    # Atomic write with backup
    temp_file = log_file.with_suffix(".json.tmp")
    backup_file = log_file.with_suffix(".json.bak")

    try:
        # Write to temp file
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        # Create backup if original exists
        if log_file.exists():
            log_file.replace(backup_file)

        # Rename temp to final
        temp_file.replace(log_file)

        print(f"✅ Log entry appended: {log_file}", file=sys.stderr)
        print(f"   Agent: {agent}", file=sys.stderr)
        print(f"   File: {file}", file=sys.stderr)
        print(f"   Action: {action}", file=sys.stderr)
        print(f"   Fields: {', '.join(changed_fields)}", file=sys.stderr)

        return True

    except Exception as e:
        print(f"❌ Error writing {log_file}: {e}", file=sys.stderr)

        # Rollback: restore from backup if it exists
        if backup_file.exists() and not log_file.exists():
            backup_file.replace(log_file)
            print(f"   Rolled back to backup", file=sys.stderr)

        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()

        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(
        description="Append structured modification log entry (Root cause: ef0ed28, f9634dc - untracked changes)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Timeline agent modifying timeline.json
  python log-modification.py \\
    --trip china-feb-15-mar-7-2026-20260202-195429 \\
    --agent timeline \\
    --file timeline.json \\
    --action update \\
    --description "Updated Day 3 timeline to fix overlapping activities" \\
    --fields "days[2].timeline,days[2].warnings"

  # Meals agent creating meals.json
  python log-modification.py \\
    --trip china-feb-15-mar-7-2026-20260202-195429 \\
    --agent meals \\
    --file meals.json \\
    --action create \\
    --description "Initial meal plan with local restaurants" \\
    --fields "days"

  # Budget agent updating budget.json
  python log-modification.py \\
    --trip china-feb-15-mar-7-2026-20260202-195429 \\
    --agent budget \\
    --file budget.json \\
    --action update \\
    --description "Adjusted accommodation budget after hotel price changes" \\
    --fields "categories.accommodation.estimated"
        """
    )

    parser.add_argument(
        "--trip",
        required=True,
        help="Trip slug (directory name in data/)"
    )
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent name (timeline, meals, attractions, etc.)"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="File name being modified (timeline.json, meals.json, etc.)"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["create", "update", "delete"],
        help="Action type: create (new file), update (modify existing), delete (remove entries)"
    )
    parser.add_argument(
        "--description",
        required=True,
        help="Human-readable description of what changed and why"
    )
    parser.add_argument(
        "--fields",
        required=True,
        help="Comma-separated list of JSON paths that were modified (e.g., 'days[2].timeline,days[2].warnings')"
    )

    args = parser.parse_args()

    # Validate required fields
    if not args.description.strip():
        print("❌ Error: --description cannot be empty", file=sys.stderr)
        sys.exit(1)

    if not args.fields.strip():
        print("❌ Error: --fields cannot be empty", file=sys.stderr)
        sys.exit(1)

    # Parse fields
    changed_fields = [f.strip() for f in args.fields.split(",") if f.strip()]

    if not changed_fields:
        print("❌ Error: --fields must contain at least one field", file=sys.stderr)
        sys.exit(1)

    # Validate trip directory
    trip_dir = validate_trip_directory(args.trip)

    # Append log entry
    append_log_entry(
        trip_dir=trip_dir,
        agent=args.agent,
        file=args.file,
        action=args.action,
        description=args.description,
        changed_fields=changed_fields
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
