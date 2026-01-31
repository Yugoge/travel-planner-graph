#!/bin/bash
# Test script to verify if agents enforce skill-only usage
# Usage: bash scripts/test-agent-skill-enforcement.sh

set -e

DESTINATION="test-skill-enforcement"
DATA_DIR="data/${DESTINATION}"

echo "🧪 Testing Agent Skill Enforcement"
echo "=================================="
echo ""

# Create minimal test data
mkdir -p "${DATA_DIR}"

cat > "${DATA_DIR}/requirements-skeleton.json" << 'EOF'
{
  "trip_summary": {
    "dates": "2026-02-01 to 2026-02-02",
    "duration_days": 2,
    "travelers": "2 adults",
    "budget": "€100"
  },
  "days": [
    {
      "day": 1,
      "date": "2026-02-01",
      "location": "Beijing",
      "user_plans": ["Visit Forbidden City"]
    }
  ]
}
EOF

cat > "${DATA_DIR}/plan-skeleton.json" << 'EOF'
{
  "days": [
    {
      "day": 1,
      "date": "2026-02-01",
      "location": "Beijing",
      "user_requirements": ["Visit Forbidden City"],
      "breakfast": {"name": "", "cost": 0},
      "lunch": {"name": "", "cost": 0},
      "dinner": {"name": "", "cost": 0},
      "accommodation": {"name": "", "cost": 0},
      "attractions": []
    }
  ]
}
EOF

echo "✅ Test data created in ${DATA_DIR}"
echo ""
echo "📝 Test requirements:"
echo "   - Agent should use gaode-maps or google-maps for POI search"
echo "   - Agent should NOT use WebSearch"
echo "   - Output JSON should have data_sources WITHOUT 'web_search'"
echo ""
echo "⚠️  Manual test required:"
echo "   1. Invoke attractions agent with Task tool"
echo "   2. Check ${DATA_DIR}/attractions.json"
echo "   3. Verify data_sources field"
echo ""
echo "Expected: data_sources: ['gaode_maps'] or ['google_maps']"
echo "Failure: data_sources: ['web_search']"
