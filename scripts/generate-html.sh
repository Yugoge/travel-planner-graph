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

# Step 1: Fetch images from Google Maps and Gaode Maps APIs
echo "Step 1: Fetching images from APIs..."
if python "${SCRIPT_DIR}/lib/image_fetcher.py" "${DESTINATION_SLUG}"; then
  echo "✓ Images fetched successfully"
else
  echo "⚠ Image fetching failed or incomplete, will use Unsplash fallbacks"
fi

# Step 2: Generate HTML using interactive generator
echo "Step 2: Generating interactive HTML..."
python "${SCRIPT_DIR}/generate-html-interactive.py" "${DESTINATION_SLUG}"

exit 0
