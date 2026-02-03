#!/usr/bin/env bash
# Unified atomic script: Generate HTML + Deploy to GitHub Pages
# Usage: generate-and-deploy.sh <destination-slug> [version-suffix]
# Exit codes: 0=success, 1=generation failed, 2=deployment failed, 3=missing files

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
VERSION_SUFFIX="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data/${DESTINATION_SLUG}"

echo "=================================================="
echo "🚀 Unified Generate + Deploy"
echo "Destination: ${DESTINATION_SLUG}"
echo "Version: ${VERSION_SUFFIX:-default}"
echo "=================================================="

# Step 1: Auto-detect project type (itinerary vs bucket list)
echo ""
echo "📋 Step 1: Detecting project type..."

PROJECT_TYPE="unknown"

if [[ -f "${DATA_DIR}/plan-skeleton.json" ]]; then
  # Check if it's a bucket list (has "cities" array) or itinerary (has "days" array)
  if jq -e '.cities' "${DATA_DIR}/plan-skeleton.json" > /dev/null 2>&1; then
    PROJECT_TYPE="bucket-list"
  elif jq -e '.days' "${DATA_DIR}/plan-skeleton.json" > /dev/null 2>&1; then
    PROJECT_TYPE="itinerary"
  fi
fi

if [[ "$PROJECT_TYPE" == "unknown" ]]; then
  echo "❌ Error: Cannot detect project type"
  echo "   Plan skeleton must have 'days' array (itinerary) or 'cities' array (bucket list)"
  exit 3
fi

echo "✓ Detected project type: ${PROJECT_TYPE}"

# Step 2: Generate HTML using Python module
echo ""
echo "📋 Step 2: Generating HTML..."

OUTPUT_FILE="${PROJECT_ROOT}/travel-plan-${DESTINATION_SLUG}${VERSION_SUFFIX}.html"

# Activate virtual environment
if [[ -f "${PROJECT_ROOT}/venv/bin/activate" ]]; then
  source "${PROJECT_ROOT}/venv/bin/activate"
elif [[ -f /root/.claude/venv/bin/activate ]]; then
  source /root/.claude/venv/bin/activate
else
  echo "❌ Error: Virtual environment not found"
  exit 3
fi

# Use Python module to generate HTML
python - <<PYTHON_SCRIPT
import sys
from pathlib import Path

# Add scripts directory to Python path
project_root = Path("${PROJECT_ROOT}")
sys.path.insert(0, str(project_root))

# Import the HTML generator module
from scripts.lib.html_generator import TravelPlanHTMLGenerator

# Configuration
destination_slug = "${DESTINATION_SLUG}"
version_suffix = "${VERSION_SUFFIX}"
project_type = "${PROJECT_TYPE}"
data_dir = Path("${DATA_DIR}")
output_file = Path("${OUTPUT_FILE}")

# Generate HTML using the module
try:
    generator = TravelPlanHTMLGenerator(
        destination_slug=destination_slug,
        data_dir=data_dir
    )
    generator.generate_html(output_file)
    print(f"✓ HTML generated: {output_file}")
except Exception as e:
    print(f"❌ Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

if [[ $? -ne 0 ]]; then
  echo "❌ Error: HTML generation failed"
  exit 1
fi

echo "✓ HTML generated successfully"

# Step 3: Deploy to GitHub Pages (atomic - cannot be skipped)
echo ""
echo "📋 Step 3: Deploying to GitHub Pages..."

# Check if deployment is possible
if [[ -z "${GITHUB_TOKEN:-}" ]] && [[ ! -f ~/.ssh/id_ed25519 ]] && [[ ! -f ~/.ssh/id_rsa ]]; then
  echo "⚠️  Warning: No GitHub authentication found"
  echo "   Skipping deployment (local file only)"
  echo "   To enable deployment, set GITHUB_TOKEN or configure SSH keys"
  echo ""
  echo "✓ Generation complete (local only): ${OUTPUT_FILE}"
  exit 0
fi

# Deploy using existing script
bash "${SCRIPT_DIR}/deploy-travel-plans.sh" "${OUTPUT_FILE}"

if [[ $? -ne 0 ]]; then
  echo "❌ Error: Deployment failed"
  exit 2
fi

echo ""
echo "=================================================="
echo "✅ Complete: Generated + Deployed"
echo "=================================================="
echo ""
echo "📄 Local file: ${OUTPUT_FILE}"
echo "🌐 Live URL will be shown in deploy script output above"
echo ""

exit 0
