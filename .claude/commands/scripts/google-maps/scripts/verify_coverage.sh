#!/bin/bash
# Google Maps MCP Coverage Verification Script
# Verifies that all official MCP tools are implemented
# Exit code: 0 = verified, 1 = mismatch

set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Google Maps MCP Coverage Verification ==="
echo ""

# Official MCP tools from https://developers.google.com/maps/ai/grounding-lite/reference/mcp
echo "1. Official MCP Tools:"
cat <<EOF > /tmp/google_maps_official.txt
compute_routes
lookup_weather
search_places
EOF
sort /tmp/google_maps_official.txt
echo "Total: $(wc -l < /tmp/google_maps_official.txt)"
echo ""

# Extract implemented tools from Python scripts
echo "2. Implemented Tools:"
grep -rh 'call_tool(' scripts/*.py | \
  grep -v 'def call_tool' | \
  sed 's/.*call_tool("\([^"]*\)".*/\1/' | \
  sort | uniq > /tmp/google_maps_implemented.txt
cat /tmp/google_maps_implemented.txt
echo "Total: $(wc -l < /tmp/google_maps_implemented.txt)"
echo ""

# Compare
echo "3. Coverage Analysis:"
if diff /tmp/google_maps_official.txt /tmp/google_maps_implemented.txt > /dev/null; then
    OFFICIAL_COUNT=$(wc -l < /tmp/google_maps_official.txt)
    IMPLEMENTED_COUNT=$(wc -l < /tmp/google_maps_implemented.txt)
    echo "✅ VERIFIED: 100% Coverage"
    echo "Coverage: ${IMPLEMENTED_COUNT}/${OFFICIAL_COUNT} (100%)"
    echo ""
    echo "Tool Details:"
    for tool in $(cat /tmp/google_maps_official.txt); do
        LOCATION=$(grep -rn "call_tool(\"$tool\"" scripts/*.py | head -1)
        echo "  ✅ $tool - $LOCATION"
    done
    exit 0
else
    echo "❌ MISMATCH DETECTED"
    echo ""
    MISSING=$(comm -23 /tmp/google_maps_official.txt /tmp/google_maps_implemented.txt)
    EXTRA=$(comm -13 /tmp/google_maps_official.txt /tmp/google_maps_implemented.txt)

    if [ -n "$MISSING" ]; then
        echo "Missing tools (in official MCP but not implemented):"
        echo "$MISSING" | sed 's/^/  ❌ /'
    fi

    if [ -n "$EXTRA" ]; then
        echo "Extra tools (implemented but not in official MCP):"
        echo "$EXTRA" | sed 's/^/  ⚠️ /'
    fi

    exit 1
fi
