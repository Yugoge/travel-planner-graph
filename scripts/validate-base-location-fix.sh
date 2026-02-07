#!/usr/bin/env bash
# Description: Validate base_location conditional rendering fix
# Usage: validate-base-location-fix.sh <plan-id>
# Exit codes: 0=success, 1=failure

set -euo pipefail

PLAN_ID="${1:?Missing required plan-id parameter}"
VENV_PATH="${2:-venv}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Activate virtual environment
if [[ ! -d "$VENV_PATH" ]]; then
  echo "Error: Virtual environment not found: $VENV_PATH" >&2
  exit 1
fi

source "$VENV_PATH/bin/activate"

# Generate HTML
echo "Generating HTML for plan: $PLAN_ID"
OUTPUT_FILE=$(python scripts/generate-html-interactive.py "$PLAN_ID" 2>&1 | grep "Output:" | awk '{print $3}')

if [[ ! -f "$OUTPUT_FILE" ]]; then
  echo "Error: HTML generation failed, output file not found" >&2
  exit 1
fi

echo "Generated: $OUTPUT_FILE"

# Extract PLAN_DATA from HTML
PLAN_DATA=$(grep -A100 "const PLAN_DATA = {" "$OUTPUT_FILE" | sed -n '/const PLAN_DATA = {/,/^    }/p')

# Extract base_location value
BASE_LOCATION=$(echo "$PLAN_DATA" | grep '"base_location":' | sed 's/.*"base_location": "\(.*\)".*/\1/')

echo "base_location value: '$BASE_LOCATION'"

# Check conditional rendering in JSX
if grep -q '{tripSummary.base_location && <PropertyRow label="Base Location">' "$OUTPUT_FILE"; then
  echo "✅ Conditional rendering present in JSX"
else
  echo "❌ Conditional rendering NOT found in JSX" >&2
  exit 1
fi

# Validate behavior
if [[ -z "$BASE_LOCATION" ]]; then
  echo "✅ Empty base_location detected - PropertyRow will be hidden"
else
  echo "✅ Non-empty base_location detected: '$BASE_LOCATION' - PropertyRow will be shown"
fi

echo ""
echo "✅ Validation successful!"
echo "   - Conditional rendering: IMPLEMENTED"
echo "   - base_location value: '$BASE_LOCATION'"
echo "   - Expected behavior: PropertyRow will $([ -z "$BASE_LOCATION" ] && echo "NOT display" || echo "display")"

exit 0
