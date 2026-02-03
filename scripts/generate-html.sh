#!/usr/bin/env bash
# Generate travel HTML using Python html_generator.py
# Usage: generate-html.sh <destination-slug> [version-suffix]
# Exit codes: 0=success, 1=generation failed, 2=missing parameters

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
VERSION_SUFFIX="${2:-}"

# Determine paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data/${DESTINATION_SLUG}"
OUTPUT_FILE="${PROJECT_ROOT}/travel-plan-${DESTINATION_SLUG}${VERSION_SUFFIX}.html"

# Verify data directory exists
if [[ ! -d "$DATA_DIR" ]]; then
  echo "Error: Data directory not found: $DATA_DIR" >&2
  exit 2
fi

# Activate virtual environment (try project venv first, then global)
if [[ -f "${PROJECT_ROOT}/.claude/venv/bin/activate" ]]; then
  source "${PROJECT_ROOT}/.claude/venv/bin/activate"
elif [[ -f "/root/.claude/venv/bin/activate" ]]; then
  source "/root/.claude/venv/bin/activate"
else
  echo "Warning: Virtual environment not found, using system Python" >&2
fi

# Call Python HTML generator
python "${SCRIPT_DIR}/lib/html_generator.py" \
  "${DESTINATION_SLUG}" \
  --data-dir "${DATA_DIR}" \
  --output "${OUTPUT_FILE}"

exit 0
