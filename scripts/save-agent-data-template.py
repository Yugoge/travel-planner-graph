#!/usr/bin/env python3
"""Template demonstrating correct usage of scripts/lib/json_io.py for saving agent data.

Root Cause Context: This template addresses the anti-pattern of embedding Python code
directly in agent documentation files (discovered 2026-02-12). Agent .md files should
reference executable scripts, not contain inline code examples.

This script serves as a reusable template that any agent can adapt for their specific
data structure and validation needs.

Usage:
    # Basic usage with validation
    python3 scripts/save-agent-data-template.py \\
        --agent-name meals \\
        --data-file data/chongqing-4day/meals.json \\
        --trip-dir data/chongqing-4day

    # Skip validation (not recommended)
    python3 scripts/save-agent-data-template.py \\
        --agent-name timeline \\
        --data-file data/chongqing-4day/timeline.json \\
        --trip-dir data/chongqing-4day \\
        --no-validate

    # Allow HIGH severity issues (emergency override)
    python3 scripts/save-agent-data-template.py \\
        --agent-name attractions \\
        --data-file data/chongqing-4day/attractions.json \\
        --trip-dir data/chongqing-4day \\
        --allow-high-severity

Exit Codes:
    0: Success - data saved and validated
    1: Validation failed with HIGH severity issues
    2: File I/O error or invalid arguments
"""

import sys
import argparse
from pathlib import Path

# Add scripts/lib to path for json_io import
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR / "lib"))

from json_io import save_agent_json, ValidationError, AtomicWriteError


def build_example_data(agent_name: str) -> dict:
    """Build example data structure based on agent type.

    IMPORTANT: In production usage, replace this function with your actual
    data generation logic. This is only for demonstration purposes.

    Args:
        agent_name: Agent name (meals, timeline, attractions, etc.)

    Returns:
        Agent-specific data dictionary (without envelope)
    """
    # Example data structures for different agents
    examples = {
        "meals": {
            "days": [
                {
                    "day": 1,
                    "date": "2026-02-15",
                    "breakfast": {
                        "name_base": "Example Restaurant",
                        "name_local": "示例餐厅",
                        "location_base": "123 Example Street",
                        "location_local": "示例街123号",
                        "cost": 50,
                        "cuisine_base": "Local",
                        "cuisine_local": "本地菜"
                    }
                }
            ]
        },
        "timeline": {
            "days": [
                {
                    "day": 1,
                    "date": "2026-02-15",
                    "timeline": {
                        "Example Restaurant": {
                            "start": "08:00",
                            "duration_minutes": 60,
                            "type": "breakfast"
                        }
                    },
                    "travel_segments": [
                        {
                            "name_base": "Walk to Next Location",
                            "type_base": "walk",
                            "duration_minutes": 10
                        }
                    ]
                }
            ]
        },
        "attractions": {
            "days": [
                {
                    "day": 1,
                    "date": "2026-02-15",
                    "activities": [
                        {
                            "name_base": "Example Temple",
                            "name_local": "示例寺庙",
                            "location_base": "456 Temple Road",
                            "location_local": "寺庙路456号",
                            "cost": 30
                        }
                    ]
                }
            ]
        },
        "entertainment": {
            "days": [
                {
                    "day": 1,
                    "date": "2026-02-15",
                    "activities": [
                        {
                            "name_base": "Example Show",
                            "name_local": "示例演出",
                            "location_base": "789 Theater Street",
                            "location_local": "剧院街789号",
                            "cost": 200
                        }
                    ]
                }
            ]
        },
        "transportation": {
            "days": [
                {
                    "day": 1,
                    "date": "2026-02-15",
                    "segments": [
                        {
                            "name_base": "Airport to Hotel",
                            "type_base": "taxi",
                            "duration_minutes": 45,
                            "cost": 80
                        }
                    ]
                }
            ]
        },
        "accommodation": {
            "hotel": {
                "name_base": "Example Hotel",
                "name_local": "示例酒店",
                "location_base": "321 Hotel Avenue",
                "location_local": "酒店大道321号",
                "cost_per_night": 500,
                "nights": 3
            }
        },
        "shopping": {
            "days": [
                {
                    "day": 1,
                    "date": "2026-02-15",
                    "items": [
                        {
                            "name_base": "Local Souvenirs",
                            "name_local": "当地纪念品",
                            "location_base": "Gift Shop",
                            "location_local": "礼品店",
                            "cost": 100
                        }
                    ]
                }
            ]
        },
        "budget": {
            "total": 5000,
            "breakdown": {
                "accommodation": 1500,
                "meals": 1000,
                "transportation": 800,
                "attractions": 600,
                "entertainment": 400,
                "shopping": 500,
                "contingency": 200
            }
        }
    }

    return examples.get(agent_name, {"placeholder": "Add your data structure here"})


def main():
    """Main execution function demonstrating json_io.py usage."""
    parser = argparse.ArgumentParser(
        description="Template for saving agent data using centralized JSON I/O library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--agent-name",
        required=True,
        help="Agent name (meals, timeline, attractions, etc.)"
    )
    parser.add_argument(
        "--data-file",
        required=True,
        type=Path,
        help="Output file path (e.g., data/chongqing-4day/meals.json)"
    )
    parser.add_argument(
        "--trip-dir",
        required=True,
        type=Path,
        help="Trip directory for cross-agent validation (e.g., data/chongqing-4day)"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation (NOT recommended)"
    )
    parser.add_argument(
        "--allow-high-severity",
        action="store_true",
        help="Allow HIGH severity validation issues (emergency override)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating .bak backup file"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.trip_dir.exists():
        print(f"ERROR: Trip directory does not exist: {args.trip_dir}", file=sys.stderr)
        sys.exit(2)

    # IMPORTANT: In production usage, replace this with your actual data generation logic
    # This example just builds placeholder data for demonstration
    agent_data = build_example_data(args.agent_name)

    # Save with validation and atomic write
    try:
        save_agent_json(
            file_path=args.data_file,
            agent_name=args.agent_name,
            data=agent_data,
            validate=not args.no_validate,
            create_backup=not args.no_backup,
            allow_high_severity=args.allow_high_severity
        )

        print(f"SUCCESS: Saved {args.agent_name} data to {args.data_file}")

        if args.no_validate:
            print("WARNING: Validation was skipped", file=sys.stderr)

        sys.exit(0)

    except ValidationError as e:
        print(f"ERROR: Validation failed with {len(e.high_issues)} HIGH severity issues:", file=sys.stderr)
        for issue in e.high_issues:
            print(f"  - Day {issue.day}, {issue.field}: {issue.message}", file=sys.stderr)
        print("\nTo force save despite errors, use --allow-high-severity (NOT recommended)", file=sys.stderr)
        sys.exit(1)

    except AtomicWriteError as e:
        print(f"ERROR: Failed to write file: {e}", file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
