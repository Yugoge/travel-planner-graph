#!/usr/bin/env bash
# Validate that all days in requirements-skeleton.json have user_plans populated
# Usage: check-day-completion.sh <destination-slug>
# Exit codes: 0=all days complete, 1=missing user_plans, 2=file not found

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
REQUIREMENTS_FILE="data/${DESTINATION_SLUG}/requirements-skeleton.json"

if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
  echo "Error: Requirements file not found: $REQUIREMENTS_FILE" >&2
  exit 2
fi

TOTAL_DAYS=$(jq -r '.days | length' "$REQUIREMENTS_FILE")
INCOMPLETE_DAYS=$(jq -r '[.days[] | select(.user_plans == null or (.user_plans | length) == 0) | .day] | length' "$REQUIREMENTS_FILE")

if [[ "$INCOMPLETE_DAYS" -eq 0 ]]; then
  echo "✓ All $TOTAL_DAYS days have user_plans populated"
  exit 0
else
  INCOMPLETE_DAY_NUMBERS=$(jq -r '[.days[] | select(.user_plans == null or (.user_plans | length) == 0) | .day] | join(", ")' "$REQUIREMENTS_FILE")
  echo "✗ $INCOMPLETE_DAYS day(s) missing user_plans: Day $INCOMPLETE_DAY_NUMBERS" >&2
  exit 1
fi
