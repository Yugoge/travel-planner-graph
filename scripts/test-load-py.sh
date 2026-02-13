#!/usr/bin/env bash
# Description: Comprehensive test suite for scripts/load.py
# Usage: test-load-py.sh <trip-slug>
# Exit codes: 0=all pass, 1=some failures

set -euo pipefail

TRIP_SLUG="${1:-china-feb-15-mar-7-2026-20260202-195429}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOAD_SCRIPT="$PROJECT_ROOT/scripts/load.py"
TEST_OUTPUT_DIR="/tmp/load-py-test-$$"
REPORT_FILE="$PROJECT_ROOT/docs/dev/loadpy-test-report-$(date +%Y%m%d-%H%M%S).json"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test results
TEST_RESULTS_FILE="$TEST_OUTPUT_DIR/results.jsonl"

# Cleanup on exit
cleanup() {
  rm -rf "$TEST_OUTPUT_DIR"
}
trap cleanup EXIT

mkdir -p "$TEST_OUTPUT_DIR"

# Activate venv
source "$PROJECT_ROOT/venv/bin/activate"

# Test function
run_test() {
  local test_name="$1"
  local command="$2"
  local expected_exit_code="${3:-0}"
  local validation="${4:-}"

  echo "[TEST $((TOTAL_TESTS + 1))] $test_name"

  local output_file="$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json"
  local stderr_file="$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.stderr"

  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  local exit_code=0

  # Run command
  eval "$command" > "$output_file" 2> "$stderr_file" || exit_code=$?

  # Check exit code
  if [ "$exit_code" -ne "$expected_exit_code" ]; then
    echo "✗ FAIL - Expected exit code $expected_exit_code, got $exit_code"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    local stderr_preview=$(cat "$stderr_file" 2>/dev/null | head -c 200 | tr '\n' ' ' | sed 's/"/\\"/g' || echo '')
    echo "{\"test_name\":\"$test_name\",\"command\":\"$command\",\"status\":\"fail\",\"exit_code\":$exit_code,\"expected_exit_code\":$expected_exit_code,\"validation\":\"Exit code mismatch\",\"stderr\":\"$stderr_preview\"}" >> "$TEST_RESULTS_FILE"
    return 1
  fi

  # Additional validation
  if [ -n "$validation" ]; then
    if ! eval "$validation" 2>/dev/null; then
      echo "✗ FAIL - Validation failed: $validation"
      FAILED_TESTS=$((FAILED_TESTS + 1))
      echo "{\"test_name\":\"$test_name\",\"command\":\"$command\",\"status\":\"fail\",\"exit_code\":$exit_code,\"validation\":\"Validation failed: $validation\"}" >> "$TEST_RESULTS_FILE"
      return 1
    fi
  fi

  echo "✓ PASS"
  PASSED_TESTS=$((PASSED_TESTS + 1))
  local output_preview=$(cat "$output_file" 2>/dev/null | head -c 200 | tr '\n' ' ' | sed 's/"/\\"/g' || echo '')
  echo "{\"test_name\":\"$test_name\",\"command\":\"$command\",\"status\":\"pass\",\"exit_code\":$exit_code,\"validation\":\"${validation:-OK}\",\"output_preview\":\"$output_preview\"}" >> "$TEST_RESULTS_FILE"
  return 0
}

# Validate JSON output
validate_json() {
  local file="$1"
  jq empty "$file" 2>/dev/null
}

echo "========================================="
echo "load.py Comprehensive Test Suite"
echo "========================================="
echo "Trip: $TRIP_SLUG"
echo "Script: $LOAD_SCRIPT"
echo ""

# ==========================================
# SECTION 1: Basic Parameter Combinations
# ==========================================
echo "=== SECTION 1: Basic Parameter Combinations ==="
echo ""

run_test "Level 1 - timeline metadata only" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agents timeline --level 1" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

run_test "Level 2 - timeline keys, day 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agents timeline --level 2 --day 1" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

run_test "Level 3 - timeline full data, day 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agents timeline --level 3 --day 1" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

run_test "Multiple agents - timeline,meals,budget level 3 day 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agents timeline,meals,budget --level 3 --day 1" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

run_test "Pretty output - timeline level 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agents timeline --level 1 --pretty" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json' && test \$(wc -l < '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json') -gt 10"

run_test "File output - timeline level 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agents timeline --level 1 --output '$TEST_OUTPUT_DIR/file-output.json'" \
  0 \
  "test -f '$TEST_OUTPUT_DIR/file-output.json' && validate_json '$TEST_OUTPUT_DIR/file-output.json'"

# ==========================================
# SECTION 2: All Agents
# ==========================================
echo ""
echo "=== SECTION 2: All Agents ==="
echo ""

for agent in timeline meals attractions entertainment shopping accommodation transportation budget; do
  run_test "Agent: $agent - level 1" \
    "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent '$agent' --level 1" \
    0 \
    "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

  run_test "Agent: $agent - level 2 day 1" \
    "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent '$agent' --level 2 --day 1" \
    0 \
    "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

  run_test "Agent: $agent - level 3 day 1" \
    "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent '$agent' --level 3 --day 1" \
    0 \
    "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"
done

# ==========================================
# SECTION 3: Day Filtering
# ==========================================
echo ""
echo "=== SECTION 3: Day Filtering ==="
echo ""

for day in 1 5 10 15 21; do
  run_test "Day $day - meals level 3" \
    "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent meals --level 3 --day $day" \
    0 \
    "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"
done

# ==========================================
# SECTION 4: POI Extraction
# ==========================================
echo ""
echo "=== SECTION 4: POI Extraction ==="
echo ""

for poi in breakfast lunch dinner; do
  run_test "POI: $poi - meals level 3 day 1" \
    "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent meals --level 3 --day 1 --poi '$poi'" \
    0 \
    "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"
done

run_test "POI: attractions - level 3 day 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent attractions --level 3 --day 1 --poi attractions" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

run_test "POI: attractions[0] - level 3 day 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent attractions --level 3 --day 1 --poi attractions --poi-index 0" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

# ==========================================
# SECTION 5: Edge Cases - Error Handling
# ==========================================
echo ""
echo "=== SECTION 5: Edge Cases - Error Handling ==="
echo ""

run_test "Invalid trip slug" \
  "python3 '$LOAD_SCRIPT' --trip 'nonexistent-trip-123' --agent timeline --level 1" \
  1 \
  ""

run_test "Non-existent agent name" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent 'nonexistent' --level 1" \
  1 \
  ""

run_test "Day 0 (out of range)" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent meals --level 3 --day 0" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json' && test \$(jq '.data.days | length' '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json') -eq 0"

run_test "Day 999 (out of range)" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent meals --level 3 --day 999" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json' && test \$(jq '.data.days | length' '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json') -eq 0"

run_test "POI without level 3" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent meals --level 2 --day 1 --poi lunch" \
  1 \
  ""

run_test "Both --agent and --agents specified" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent meals --agents timeline --level 1" \
  1 \
  ""

run_test "Neither --agent nor --agents specified" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --level 1" \
  1 \
  ""

run_test "POI index without POI" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent attractions --level 3 --day 1 --poi-index 0" \
  1 \
  ""

run_test "POI index out of range" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent attractions --level 3 --day 1 --poi attractions --poi-index 999" \
  1 \
  ""

# ==========================================
# SECTION 6: Stress Tests
# ==========================================
echo ""
echo "=== SECTION 6: Stress Tests ==="
echo ""

run_test "All 8 agents - level 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agents timeline,meals,attractions,entertainment,shopping,accommodation,transportation,budget --level 1" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

run_test "All 8 agents - level 3 day 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agents timeline,meals,attractions,entertainment,shopping,accommodation,transportation,budget --level 3 --day 1" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

run_test "All 21 days - level 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent timeline --level 1" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json' && test \$(jq '.data.days | length' '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json') -eq 21"

# ==========================================
# SECTION 7: Unicode/Chinese Character Handling
# ==========================================
echo ""
echo "=== SECTION 7: Unicode/Chinese Character Handling ==="
echo ""

run_test "Unicode handling - attractions level 3 day 1" \
  "python3 '$LOAD_SCRIPT' --trip '$TRIP_SLUG' --agent attractions --level 3 --day 1 --pretty" \
  0 \
  "validate_json '$TEST_OUTPUT_DIR/test-$TOTAL_TESTS.json'"

# ==========================================
# Generate Report
# ==========================================
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Total: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
  echo "✓ All tests passed!"
  exit_status=0
else
  echo "✗ Some tests failed"
  exit_status=1
fi

# Generate JSON report
mkdir -p "$(dirname "$REPORT_FILE")"

# Convert JSONL to JSON array
TEST_RESULTS_JSON="[]"
if [ -f "$TEST_RESULTS_FILE" ]; then
  TEST_RESULTS_JSON=$(jq -s '.' "$TEST_RESULTS_FILE")
fi

cat > "$REPORT_FILE" <<EOF
{
  "request_id": "dev-loadpy-test-$(date +%Y%m%d-%H%M%S)",
  "timestamp": "$(date -Iseconds)",
  "status": "completed",
  "test_summary": {
    "total_tests": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS,
    "skipped": 0
  },
  "test_results": $TEST_RESULTS_JSON,
  "bugs_found": [],
  "inspection_findings": [],
  "coverage_matrix": {
    "levels": "All 3 levels tested (1: metadata, 2: keys, 3: full data)",
    "agents": "All 8 agents tested (timeline, meals, attractions, entertainment, shopping, accommodation, transportation, budget)",
    "days": "Days 1, 5, 10, 15, 21 tested; out-of-range days tested (0, 999)",
    "poi_extraction": "Single POI, array POI, POI with index tested",
    "error_handling": "Invalid trip, invalid agent, invalid parameters tested",
    "stress_tests": "All agents simultaneously, all days, unicode characters tested"
  }
}
EOF

echo ""
echo "Report written to: $REPORT_FILE"

exit $exit_status
