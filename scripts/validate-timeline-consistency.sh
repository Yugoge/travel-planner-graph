#!/usr/bin/env bash
# Validate timeline dictionary: keys match activity names, no time conflicts
# Usage: validate-timeline-consistency.sh <destination-slug>
# Exit codes: 0=consistent, 1=validation errors, 2=file not found

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
PLAN_FILE="data/${DESTINATION_SLUG}/plan-skeleton.json"

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "Error: Plan skeleton file not found: $PLAN_FILE" >&2
  exit 2
fi

# Validation logic: check timeline keys match activity names and detect time conflicts
VALIDATION_RESULT=$(jq -r '
  .days[] |
  . as $day |

  # Collect all activity names (exclude accommodation and transportation - not time-bound by design)
  (
    [
      (if .breakfast.name != "" then .breakfast.name else empty end),
      (if .lunch.name != "" then .lunch.name else empty end),
      (if .dinner.name != "" then .dinner.name else empty end),
      (.attractions[]?.name // empty),
      (.entertainment[]?.name // empty),
      (.shopping[]?.name // empty)
    ]
  ) as $activity_names |

  # Get timeline keys
  ($day.timeline | keys) as $timeline_keys |

  # Check for mismatches
  {
    day: .day,
    missing_in_timeline: ($activity_names - $timeline_keys),
    extra_in_timeline: ($timeline_keys - $activity_names),
    conflicts: (
      # Check for time conflicts (overlapping times)
      [
        $day.timeline | to_entries | sort_by(.value.start_time) |
        . as $sorted |
        range(0; length - 1) as $i |
        $sorted[$i] as $current |
        $sorted[$i + 1] as $next |
        select($current.value.end_time > $next.value.start_time) |
        "\($current.key) (\($current.value.start_time)-\($current.value.end_time)) overlaps with \($next.key) (\($next.value.start_time)-\($next.value.end_time))"
      ]
    )
  } |

  # Format output
  if (.missing_in_timeline | length) > 0 or (.extra_in_timeline | length) > 0 or (.conflicts | length) > 0 then
    [
      "Day \(.day):",
      (if (.missing_in_timeline | length) > 0 then "  Missing in timeline: \(.missing_in_timeline | join(", "))" else empty end),
      (if (.extra_in_timeline | length) > 0 then "  Extra in timeline: \(.extra_in_timeline | join(", "))" else empty end),
      (if (.conflicts | length) > 0 then "  Time conflicts: \(.conflicts | join("; "))" else empty end)
    ] | join("\n")
  else
    empty
  end
' "$PLAN_FILE")

if [[ -z "$VALIDATION_RESULT" ]]; then
  echo "✓ Timeline consistency validated: all activity names match, no time conflicts"
  exit 0
else
  echo "✗ Timeline validation errors:" >&2
  echo "$VALIDATION_RESULT" >&2
  exit 1
fi
