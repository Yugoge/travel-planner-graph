#!/usr/bin/env bash
# Validate that all location changes have corresponding location_change objects
# Usage: check-location-continuity.sh <destination-slug>
# Exit codes: 0=all location changes have objects, 1=missing location_change, 2=file not found

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
PLAN_FILE="data/${DESTINATION_SLUG}/plan-skeleton.json"

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "Error: Plan skeleton file not found: $PLAN_FILE" >&2
  exit 2
fi

# Check for location changes without location_change object
VIOLATIONS=$(jq -r '
  .days as $days |
  [range(1; ($days | length)) |
    select($days[.].location != $days[. - 1].location and ($days[.].location_change == null or $days[.].location_change == {})) |
    {
      day: $days[.].day,
      from: $days[. - 1].location,
      to: $days[.].location
    }
  ] |
  if length > 0 then
    map("Day \(.day): \(.from) → \(.to)") | join("\n")
  else
    "none"
  end
' "$PLAN_FILE")

if [[ "$VIOLATIONS" == "none" ]]; then
  echo "✓ All location changes have location_change objects"
  exit 0
else
  echo "✗ Location changes missing location_change objects:" >&2
  echo "$VIOLATIONS" >&2
  exit 1
fi
