#!/usr/bin/env bash
# Convert requirements-skeleton.json to plan-skeleton.json
# Usage: init-plan-skeleton.sh <requirements-json-path> [output-path]
# Exit codes: 0=success, 1=input not found, 2=conversion failed

set -euo pipefail

REQUIREMENTS_JSON="${1:?Missing required requirements-json-path}"
OUTPUT_PATH="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=================================================="
echo "Convert Requirements to Plan Skeleton"
echo "Input: ${REQUIREMENTS_JSON}"
echo "=================================================="

# Validate input file
if [[ ! -f "${REQUIREMENTS_JSON}" ]]; then
  echo "Error: Requirements file not found: ${REQUIREMENTS_JSON}" >&2
  exit 1
fi

# Determine output path
if [[ -z "${OUTPUT_PATH}" ]]; then
  # Default: same directory as input, named plan-skeleton.json
  INPUT_DIR="$(dirname "${REQUIREMENTS_JSON}")"
  OUTPUT_PATH="${INPUT_DIR}/plan-skeleton.json"
fi

echo "Output: ${OUTPUT_PATH}"

# Activate virtual environment
if [[ -f "${PROJECT_ROOT}/venv/bin/activate" ]]; then
  source "${PROJECT_ROOT}/venv/bin/activate"
elif [[ -f "$HOME/.claude/venv/bin/activate" ]]; then
  source "$HOME/.claude/venv/bin/activate"
else
  echo "Error: Virtual environment not found" >&2
  exit 1
fi

echo ""
echo "Step 1: Converting requirements to plan skeleton..."

# Convert requirements to plan skeleton
python - <<PYTHON_SCRIPT
import json
import sys
from pathlib import Path

requirements_path = Path("${REQUIREMENTS_JSON}")
output_path = Path("${OUTPUT_PATH}")

# Load requirements
try:
    with requirements_path.open('r', encoding='utf-8') as f:
        requirements = json.load(f)
except FileNotFoundError:
    print(f"Error: Requirements file not found: {requirements_path}", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in requirements: {e}", file=sys.stderr)
    sys.exit(2)

# Convert days from requirements to plan skeleton format
days = []
for day in requirements.get('days', []):
    plan_day = {
        "day": day.get("day"),
        "date": day.get("date"),
        "location": day.get("location", ""),
        "location_change": None,  # Will be populated by detect-location-changes.py
        "user_requirements": day.get("user_plans", []),
        "breakfast": {"name": "", "location": "", "cost": 0},
        "lunch": {"name": "", "location": "", "cost": 0},
        "dinner": {"name": "", "location": "", "cost": 0},
        "accommodation": {"name": "", "location": "", "cost": 0},
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

    days.append(plan_day)

# Create plan skeleton
plan_skeleton = {
    "days": days,
    "emergency_info": {
        "hospitals": [],
        "police_stations": [],
        "embassy": None
    }
}

# Write initial plan skeleton (without location_change detection)
try:
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(plan_skeleton, f, indent=2, ensure_ascii=False)
    print(f"✓ Plan skeleton structure created: {output_path}")
except Exception as e:
    print(f"Error writing plan skeleton: {e}", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
PYTHON_SCRIPT

if [[ $? -ne 0 ]]; then
  echo "Error: Failed to convert requirements to plan skeleton" >&2
  exit 2
fi

echo ""
echo "Step 2: Detecting location changes..."

# Use detect-location-changes.py to add location_change objects
python "${SCRIPT_DIR}/detect-location-changes.py" "${OUTPUT_PATH}"

if [[ $? -ne 0 ]]; then
  echo "Warning: Location change detection failed, but plan skeleton was created" >&2
fi

echo ""
echo "=================================================="
echo "✓ Plan skeleton created successfully"
echo "=================================================="
echo ""
echo "File: ${OUTPUT_PATH}"
echo ""
echo "Plan skeleton includes:"
echo "- Day-by-day structure with empty fields for agent outputs"
echo "- location_change objects for days with city transitions"
echo "- user_requirements copied from requirements-skeleton.json"
echo ""
echo "Next steps:"
echo "1. Run /plan command to populate plan skeleton with agent outputs"
echo ""

exit 0
