#!/usr/bin/env bash
# Pre-Save Validation Hook - Verify modification log entry exists
# Root cause commits: ef0ed28, f9634dc - timeline data loss without tracking
#
# This hook runs BEFORE scripts/save.py to verify that agents have created
# a log entry in modification-log.json before attempting to save data.
#
# Usage: Called automatically by agent workflow before save.py execution
#
# Exit codes:
#   0 = validation passed (log entry exists or warning issued)
#   1 = validation failed (critical error, abort save)

set -euo pipefail

# Parameters
TRIP_SLUG="${1:?Missing trip slug}"
AGENT="${2:?Missing agent name}"
FILE="${3:?Missing file name}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODIFICATION_LOG="${PROJECT_ROOT}/data/${TRIP_SLUG}/modification-log.json"

# Check if modification log exists
if [[ ! -f "$MODIFICATION_LOG" ]]; then
  echo "⚠️  WARNING: modification-log.json not found" >&2
  echo "   Expected: ${MODIFICATION_LOG}" >&2
  echo "   This save will NOT be tracked in the modification log" >&2
  echo "   Please create log entry using: python log-modification.py" >&2
  echo "" >&2
  echo "   Proceeding with save (tracking recommended but not mandatory)..." >&2
  exit 0
fi

# Read modification log
if ! LOG_DATA=$(cat "$MODIFICATION_LOG" 2>/dev/null); then
  echo "⚠️  WARNING: Cannot read modification-log.json" >&2
  echo "   Proceeding with save (tracking recommended but not mandatory)..." >&2
  exit 0
fi

# Check if recent log entry exists (within last 5 minutes) for this agent+file
CURRENT_TIME=$(date -u +%s)
FIVE_MINUTES_AGO=$((CURRENT_TIME - 300))

# Extract last modification entry for this agent+file
# Note: This is a simple check, not foolproof. Agents should still create log entries.
# Activate venv if available, fallback to python3
source "${PROJECT_ROOT}/venv/bin/activate" 2>/dev/null || true
RECENT_ENTRY_COUNT=$(echo "$LOG_DATA" | python -c "
import json
import sys
from datetime import datetime, timezone

try:
    data = json.load(sys.stdin)
    modifications = data.get('modifications', [])

    # Count recent entries for this agent+file
    recent_count = 0
    for mod in modifications:
        if mod.get('agent') == '${AGENT}' and mod.get('file') == '${FILE}':
            # Parse timestamp
            ts_str = mod.get('timestamp', '')
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    ts_unix = int(ts.timestamp())
                    if ts_unix >= ${FIVE_MINUTES_AGO}:
                        recent_count += 1
                except:
                    pass

    print(recent_count)
except:
    print('0')
" 2>/dev/null || echo "0")

if [[ "$RECENT_ENTRY_COUNT" -eq 0 ]]; then
  echo "⚠️  WARNING: No recent log entry found for ${AGENT}/${FILE}" >&2
  echo "   Please create log entry BEFORE saving:" >&2
  echo "" >&2
  echo "   python log-modification.py \\" >&2
  echo "     --trip ${TRIP_SLUG} \\" >&2
  echo "     --agent ${AGENT} \\" >&2
  echo "     --file ${FILE} \\" >&2
  echo "     --action update \\" >&2
  echo "     --description 'What changed and why' \\" >&2
  echo "     --fields 'field1,field2'" >&2
  echo "" >&2
  echo "   Proceeding with save (tracking STRONGLY RECOMMENDED)..." >&2
fi

exit 0
