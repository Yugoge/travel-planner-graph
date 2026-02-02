#!/usr/bin/env bash
# Validate plan workflow execution completeness
# Usage: validate-plan-workflow.sh <destination-slug>
# Exit codes: 0=complete, 1=incomplete, 2=missing critical files

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
DATA_DIR="data/${DESTINATION_SLUG}"

echo "=================================================="
echo "🔍 Validating Plan Workflow"
echo "Destination: ${DESTINATION_SLUG}"
echo "=================================================="

# Track validation results
MISSING_FILES=()
INCOMPLETE_STEPS=()
WARNINGS=()

# Step 1: Check critical files exist
echo ""
echo "📋 Step 1: Checking required files..."

REQUIRED_FILES=(
  "requirements-skeleton.json"
  "plan-skeleton.json"
  "meals.json"
  "accommodation.json"
  "attractions.json"
  "entertainment.json"
  "shopping.json"
  "timeline.json"
  "budget.json"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "${DATA_DIR}/${file}" ]]; then
    MISSING_FILES+=("${file}")
    echo "  ❌ Missing: ${file}"
  else
    echo "  ✓ Found: ${file}"
  fi
done

# Check transportation.json (optional if no location changes)
if [[ -f "${DATA_DIR}/transportation.json" ]]; then
  echo "  ✓ Found: transportation.json"
else
  WARNINGS+=("transportation.json not found (OK if no location changes)")
  echo "  ⚠️  Optional: transportation.json"
fi

# Step 2: Validate JSON syntax
echo ""
echo "📋 Step 2: Validating JSON syntax..."

for file in "${REQUIRED_FILES[@]}"; do
  if [[ -f "${DATA_DIR}/${file}" ]]; then
    if jq empty "${DATA_DIR}/${file}" 2>/dev/null; then
      echo "  ✓ Valid JSON: ${file}"
    else
      INCOMPLETE_STEPS+=("${file} has invalid JSON syntax")
      echo "  ❌ Invalid JSON: ${file}"
    fi
  fi
done

# Step 3: Check agent completion status
echo ""
echo "📋 Step 3: Checking agent completion status..."

check_agent_status() {
  local file=$1
  local agent_name=$2

  if [[ ! -f "${DATA_DIR}/${file}" ]]; then
    return 1
  fi

  local status=$(jq -r '.status // "unknown"' "${DATA_DIR}/${file}" 2>/dev/null)

  if [[ "$status" == "complete" ]]; then
    echo "  ✓ ${agent_name}: complete"
    return 0
  else
    echo "  ❌ ${agent_name}: ${status}"
    INCOMPLETE_STEPS+=("${agent_name} status is '${status}', expected 'complete'")
    return 1
  fi
}

check_agent_status "meals.json" "meals-agent"
check_agent_status "accommodation.json" "accommodation-agent"
check_agent_status "attractions.json" "attractions-agent"
check_agent_status "entertainment.json" "entertainment-agent"
check_agent_status "shopping.json" "shopping-agent"
check_agent_status "timeline.json" "timeline-agent"
check_agent_status "budget.json" "budget-agent"

# Step 4: Verify HTML generation
echo ""
echo "📋 Step 4: Checking HTML generation..."

HTML_PATTERN="travel-plan-${DESTINATION_SLUG}*.html"
HTML_FILES=($(ls ${HTML_PATTERN} 2>/dev/null || echo ""))

if [[ ${#HTML_FILES[@]} -gt 0 ]]; then
  echo "  ✓ Found ${#HTML_FILES[@]} HTML file(s):"
  for html_file in "${HTML_FILES[@]}"; do
    echo "    - ${html_file}"
  done
else
  WARNINGS+=("No HTML files generated yet (expected travel-plan-${DESTINATION_SLUG}.html)")
  echo "  ⚠️  No HTML files found (not critical for data validation)"
fi

# Step 5: Check deployment (optional but recommended)
echo ""
echo "📋 Step 5: Checking deployment status..."

# Note: This is informational only, not a failure condition
if [[ -n "${GITHUB_TOKEN:-}" ]] || [[ -f ~/.ssh/id_ed25519 ]] || [[ -f ~/.ssh/id_rsa ]]; then
  echo "  ℹ️  GitHub authentication available (deployment possible)"
else
  WARNINGS+=("No GitHub authentication found (deployment skipped)")
  echo "  ⚠️  No GitHub authentication (deployment not possible)"
fi

# Summary
echo ""
echo "=================================================="
echo "📊 Validation Summary"
echo "=================================================="

if [[ ${#MISSING_FILES[@]} -eq 0 ]] && [[ ${#INCOMPLETE_STEPS[@]} -eq 0 ]]; then
  echo "✅ Workflow COMPLETE"
  echo ""
  echo "All required files present and valid."
  echo "All agents completed successfully."

  if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo ""
    echo "Warnings (non-critical):"
    for warning in "${WARNINGS[@]}"; do
      echo "  ⚠️  ${warning}"
    done
  fi

  exit 0
else
  echo "❌ Workflow INCOMPLETE"
  echo ""

  if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo "Missing files (${#MISSING_FILES[@]}):"
    for file in "${MISSING_FILES[@]}"; do
      echo "  - ${file}"
    done
    echo ""
  fi

  if [[ ${#INCOMPLETE_STEPS[@]} -gt 0 ]]; then
    echo "Incomplete steps (${#INCOMPLETE_STEPS[@]}):"
    for step in "${INCOMPLETE_STEPS[@]}"; do
      echo "  - ${step}"
    done
    echo ""
  fi

  if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo "Critical files missing. Cannot proceed."
    exit 2
  else
    echo "Some steps incomplete. Review and retry."
    exit 1
  fi
fi
