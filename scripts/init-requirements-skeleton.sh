#!/usr/bin/env bash
# Generate requirements-skeleton.json from user interview data
# Usage: init-requirements-skeleton.sh <destination-slug> <start-date> <end-date> <travelers> <budget> <preferences>
# Exit codes: 0=success, 1=invalid parameters, 2=file creation failed

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
START_DATE="${2:?Missing required start-date (YYYY-MM-DD)}"
END_DATE="${3:?Missing required end-date (YYYY-MM-DD)}"
TRAVELERS="${4:?Missing required travelers count}"
BUDGET="${5:?Missing required budget (e.g., €1000)}"
PREFERENCES="${6:-Mix of hotels and home stays, moderate pace}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data/${DESTINATION_SLUG}"
OUTPUT_FILE="${DATA_DIR}/requirements-skeleton.json"

echo "=================================================="
echo "Generate Requirements Skeleton"
echo "Destination: ${DESTINATION_SLUG}"
echo "Dates: ${START_DATE} to ${END_DATE}"
echo "Travelers: ${TRAVELERS}"
echo "Budget: ${BUDGET}"
echo "=================================================="

# Create data directory if needed
if [[ ! -d "${DATA_DIR}" ]]; then
  echo "Creating data directory: ${DATA_DIR}"
  mkdir -p "${DATA_DIR}"
fi

# Activate virtual environment
if [[ -f "${PROJECT_ROOT}/venv/bin/activate" ]]; then
  source "${PROJECT_ROOT}/venv/bin/activate"
elif [[ -f /root/.claude/venv/bin/activate ]]; then
  source /root/.claude/venv/bin/activate
else
  echo "Error: Virtual environment not found" >&2
  exit 1
fi

# Calculate duration
DURATION=$(python -c "
from datetime import datetime
start = datetime.strptime('${START_DATE}', '%Y-%m-%d')
end = datetime.strptime('${END_DATE}', '%Y-%m-%d')
print((end - start).days + 1)
")

echo ""
echo "Step 1: Generating day-by-day structure for ${DURATION} days..."

# Generate requirements skeleton JSON
python - <<PYTHON_SCRIPT
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Parameters
destination_slug = "${DESTINATION_SLUG}"
start_date_str = "${START_DATE}"
end_date_str = "${END_DATE}"
travelers = ${TRAVELERS}
budget = "${BUDGET}"
preferences = "${PREFERENCES}"
output_file = Path("${OUTPUT_FILE}")

# Parse dates
try:
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
except ValueError as e:
    print(f"Error: Invalid date format: {e}", file=sys.stderr)
    sys.exit(1)

duration = (end_date - start_date).days + 1

if duration <= 0:
    print("Error: End date must be after start date", file=sys.stderr)
    sys.exit(1)

# Generate day-by-day structure
days = []
for day_num in range(1, duration + 1):
    current_date = start_date + timedelta(days=day_num - 1)

    day_obj = {
        "day": day_num,
        "date": current_date.strftime('%Y-%m-%d'),
        "location": "",
        "user_plans": []
    }

    days.append(day_obj)

# Create requirements skeleton
requirements = {
    "trip_summary": {
        "dates": f"{start_date_str} to {end_date_str}",
        "duration_days": duration,
        "travelers": f"{travelers} (couple)" if travelers == 2 else str(travelers),
        "budget": budget,
        "preferences": {
            "accommodation": "Mix of hotels and home stays",
            "dietary": "No restrictions",
            "pace": "Moderate to relaxed",
            "interests": preferences,
            "language_level": "A1",
            "special_notes": ""
        }
    },
    "days": days,
    "confirmed_bookings": {
        "flights": [],
        "accommodation": [],
        "trains": []
    },
    "must_do_activities": [],
    "wishlist": [],
    "constraints": []
}

# Write output
try:
    output_file.write_text(json.dumps(requirements, indent=2, ensure_ascii=False))
    print(f"✓ Requirements skeleton generated: {output_file}")
except Exception as e:
    print(f"Error writing file: {e}", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
PYTHON_SCRIPT

if [[ $? -ne 0 ]]; then
  echo "Error: Failed to generate requirements skeleton" >&2
  exit 2
fi

echo ""
echo "=================================================="
echo "✓ Requirements skeleton created successfully"
echo "=================================================="
echo ""
echo "File: ${OUTPUT_FILE}"
echo ""
echo "Next steps:"
echo "1. Edit ${OUTPUT_FILE} and fill in user interview data"
echo "2. Add locations to each day"
echo "3. Add user_plans for each day"
echo "4. Add confirmed bookings, must-do activities, wishlist"
echo "5. Run init-plan-skeleton.sh to generate plan skeleton"
echo ""

exit 0
