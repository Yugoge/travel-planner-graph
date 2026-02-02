#!/usr/bin/env bash
# End-to-end test for plan workflow
# Tests both itinerary and bucket list scenarios
# Usage: test-plan-workflow.sh
# Exit codes: 0=all tests pass, 1=tests failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=================================================="
echo "🧪 Plan Workflow E2E Tests"
echo "=================================================="

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
test_start() {
  TESTS_RUN=$((TESTS_RUN + 1))
  echo ""
  echo "Test ${TESTS_RUN}: $1"
  echo "---"
}

test_pass() {
  TESTS_PASSED=$((TESTS_PASSED + 1))
  echo "✓ PASS: $1"
}

test_fail() {
  TESTS_FAILED=$((TESTS_FAILED + 1))
  echo "✗ FAIL: $1"
}

# Cleanup function
cleanup_test_data() {
  local slug=$1
  rm -rf "${PROJECT_ROOT}/data/${slug}" 2>/dev/null || true
  rm -f "${PROJECT_ROOT}/travel-plan-${slug}"*.html 2>/dev/null || true
}

# Test 1: Validate script existence
test_start "Verify all critical scripts exist"

REQUIRED_SCRIPTS=(
  "scripts/generate-and-deploy.sh"
  "scripts/deploy-travel-plans.sh"
  "scripts/validate-plan-workflow.sh"
  "scripts/lib/html_generator.py"
)

ALL_EXIST=true
for script in "${REQUIRED_SCRIPTS[@]}"; do
  if [[ -f "${PROJECT_ROOT}/${script}" ]]; then
    echo "  ✓ ${script}"
  else
    echo "  ✗ ${script} missing"
    ALL_EXIST=false
  fi
done

if [[ "$ALL_EXIST" == "true" ]]; then
  test_pass "All critical scripts exist"
else
  test_fail "Some scripts missing"
fi

# Test 2: Validate script permissions
test_start "Verify script execute permissions"

ALL_EXECUTABLE=true
for script in "${REQUIRED_SCRIPTS[@]}"; do
  if [[ -x "${PROJECT_ROOT}/${script}" ]]; then
    echo "  ✓ ${script} is executable"
  else
    echo "  ✗ ${script} not executable"
    ALL_EXECUTABLE=false
  fi
done

if [[ "$ALL_EXECUTABLE" == "true" ]]; then
  test_pass "All scripts have execute permissions"
else
  test_fail "Some scripts not executable"
fi

# Test 3: Python module import test
test_start "Test Python HTML generator module import"

# Activate venv
if [[ -f "${PROJECT_ROOT}/venv/bin/activate" ]]; then
  source "${PROJECT_ROOT}/venv/bin/activate"
elif [[ -f /root/.claude/venv/bin/activate ]]; then
  source /root/.claude/venv/bin/activate
fi

IMPORT_TEST=$(python - <<'PYTHON_TEST'
import sys
sys.path.insert(0, '/root/travel-planner/scripts')

try:
    from lib.html_generator import TravelPlanHTMLGenerator
    print("SUCCESS")
except ImportError as e:
    print(f"FAIL: {e}")
PYTHON_TEST
)

if [[ "$IMPORT_TEST" == "SUCCESS" ]]; then
  test_pass "Python module imports successfully"
else
  test_fail "Python module import failed: ${IMPORT_TEST}"
fi

# Test 4: Mock itinerary workflow
test_start "Mock itinerary workflow (file structure only)"

TEST_SLUG="test-itinerary-20260202-120000"
TEST_DATA_DIR="${PROJECT_ROOT}/data/${TEST_SLUG}"

mkdir -p "${TEST_DATA_DIR}"

# Create minimal requirements skeleton
cat > "${TEST_DATA_DIR}/requirements-skeleton.json" <<'JSON'
{
  "trip_summary": {
    "dates": "2026-02-15 to 2026-02-15",
    "duration_days": 1
  }
}
JSON

# Create minimal plan skeleton for itinerary
cat > "${TEST_DATA_DIR}/plan-skeleton.json" <<'JSON'
{
  "days": [
    {
      "day": 1,
      "date": "2026-02-15",
      "location": "TestCity"
    }
  ]
}
JSON

# Create minimal agent outputs
for agent in meals accommodation attractions entertainment shopping transportation timeline budget; do
  cat > "${TEST_DATA_DIR}/${agent}.json" <<JSON
{
  "agent": "${agent}",
  "status": "complete",
  "data": {
    "days": [
      {
        "day": 1
      }
    ]
  }
}
JSON
done

# Run validation script
if bash "${PROJECT_ROOT}/scripts/validate-plan-workflow.sh" "${TEST_SLUG}" >/dev/null 2>&1; then
  test_pass "Mock itinerary workflow validation passes"
else
  test_fail "Mock itinerary workflow validation failed"
fi

cleanup_test_data "${TEST_SLUG}"

# Test 5: Mock bucket list workflow
test_start "Mock bucket list workflow (file structure only)"

TEST_SLUG="test-bucket-list-20260202-120000"
TEST_DATA_DIR="${PROJECT_ROOT}/data/${TEST_SLUG}"

mkdir -p "${TEST_DATA_DIR}"

# Create minimal plan skeleton for bucket list
cat > "${TEST_DATA_DIR}/plan-skeleton.json" <<'JSON'
{
  "title": "Test Bucket List",
  "cities": [
    {
      "city": "TestCity",
      "province": "TestProvince"
    }
  ]
}
JSON

# Create minimal agent outputs for bucket list
for agent in meals accommodation attractions entertainment shopping transportation timeline budget; do
  cat > "${TEST_DATA_DIR}/${agent}.json" <<JSON
{
  "agent": "${agent}",
  "status": "complete",
  "cities": [
    {
      "city": "TestCity"
    }
  ]
}
JSON
done

# Run validation script
if bash "${PROJECT_ROOT}/scripts/validate-plan-workflow.sh" "${TEST_SLUG}" >/dev/null 2>&1; then
  test_pass "Mock bucket list workflow validation passes"
else
  test_fail "Mock bucket list workflow validation failed"
fi

cleanup_test_data "${TEST_SLUG}"

# Test 6: Validation script detects missing files
test_start "Validation script detects incomplete workflow"

TEST_SLUG="test-incomplete-20260202-120000"
TEST_DATA_DIR="${PROJECT_ROOT}/data/${TEST_SLUG}"

mkdir -p "${TEST_DATA_DIR}"

# Create only plan skeleton, no agent outputs
cat > "${TEST_DATA_DIR}/plan-skeleton.json" <<'JSON'
{
  "days": [
    {
      "day": 1,
      "date": "2026-02-15",
      "location": "TestCity"
    }
  ]
}
JSON

# Run validation script (should fail)
if bash "${PROJECT_ROOT}/scripts/validate-plan-workflow.sh" "${TEST_SLUG}" >/dev/null 2>&1; then
  test_fail "Validation should have failed for incomplete workflow"
else
  test_pass "Validation correctly detects incomplete workflow"
fi

cleanup_test_data "${TEST_SLUG}"

# Test 7: Validate deployment script naming flexibility
test_start "Deploy script accepts multiple naming formats"

# This is a syntax/logic test only (no actual deployment)
# We just verify the script can parse different filename formats

TEST_FORMATS=(
  "travel-plan-paris-2026-03-15.html"
  "travel-plan-china-20260202-120000.html"
  "travel-plan-bucket-list.html"
  "travel-plan-paris-2026-03-15-v2.html"
)

PARSING_OK=true
for format in "${TEST_FORMATS[@]}"; do
  # Create dummy file
  touch "${PROJECT_ROOT}/${format}"

  # Test if script can parse (will fail at auth check, but parsing should work)
  # We check if script gets past filename validation
  if bash "${PROJECT_ROOT}/scripts/deploy-travel-plans.sh" "${PROJECT_ROOT}/${format}" 2>&1 | grep -q "Error: Invalid filename format"; then
    echo "  ✗ Failed to parse: ${format}"
    PARSING_OK=false
  else
    echo "  ✓ Parsed: ${format}"
  fi

  # Cleanup
  rm -f "${PROJECT_ROOT}/${format}"
done

if [[ "$PARSING_OK" == "true" ]]; then
  test_pass "Deploy script accepts all naming formats"
else
  test_fail "Deploy script rejected some valid formats"
fi

# Test 8: Budget agent JSON validation check
test_start "Budget agent has JSON validation instructions"

if grep -q "JSON Validation" "${PROJECT_ROOT}/.claude/agents/budget.md" && \
   grep -q "jq empty" "${PROJECT_ROOT}/.claude/agents/budget.md"; then
  test_pass "Budget agent includes JSON validation instructions"
else
  test_fail "Budget agent missing JSON validation instructions"
fi

# Final summary
echo ""
echo "=================================================="
echo "📊 Test Summary"
echo "=================================================="
echo "Tests run:    ${TESTS_RUN}"
echo "Tests passed: ${TESTS_PASSED}"
echo "Tests failed: ${TESTS_FAILED}"
echo ""

if [[ ${TESTS_FAILED} -eq 0 ]]; then
  echo "✅ All tests passed!"
  exit 0
else
  echo "❌ ${TESTS_FAILED} test(s) failed"
  exit 1
fi
