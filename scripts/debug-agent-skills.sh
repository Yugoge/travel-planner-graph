#!/bin/bash
# Deep analysis of agent vs direct execution environment differences

echo "=================================="
echo "ENVIRONMENT COMPARISON ANALYSIS"
echo "=================================="
echo

echo "1. PYTHON ENVIRONMENT"
echo "-------------------"
echo "Current shell Python:"
which python3
python3 --version
echo

echo "Current shell pip list | grep openmeteo:"
pip list 2>/dev/null | grep openmeteo || echo "  Not found"
echo

echo "Venv Python (if exists):"
if [ -f ~/.claude/venv/bin/python3 ]; then
    ~/.claude/venv/bin/python3 --version
    ~/.claude/venv/bin/pip list 2>/dev/null | grep openmeteo || echo "  Not found in venv"
else
    echo "  Venv not found"
fi
echo

echo "2. ENVIRONMENT VARIABLES"
echo "----------------------"
echo "AMAP_MAPS_API_KEY: ${AMAP_MAPS_API_KEY:0:20}... (${#AMAP_MAPS_API_KEY} chars)"
echo "GOOGLE_MAPS_API_KEY: ${GOOGLE_MAPS_API_KEY:0:20}... (${#GOOGLE_MAPS_API_KEY} chars)"
echo "DUFFEL_API_KEY: ${DUFFEL_API_KEY:0:20}... (${#DUFFEL_API_KEY} chars)"
echo

echo ".env file exists: $([ -f /root/travel-planner/.env ] && echo 'YES' || echo 'NO')"
if [ -f /root/travel-planner/.env ]; then
    echo ".env file keys:"
    grep -E "^[A-Z_]+=.*" /root/travel-planner/.env | cut -d'=' -f1
fi
echo

echo "3. MCP SERVERS"
echo "-------------"
echo "rednote-mcp installed:"
which rednote-mcp && rednote-mcp --version 2>&1 | head -1
echo

echo "rednote-mcp initialized (cookie file):"
if [ -f ~/.rednote-mcp/cookie.txt ]; then
    echo "  YES - $(wc -c < ~/.rednote-mcp/cookie.txt) bytes"
else
    echo "  NO - needs 'rednote-mcp init'"
fi
echo

echo "4. NETWORK CONFIGURATION"
echo "----------------------"
echo "HTTP_PROXY: ${HTTP_PROXY:-not set}"
echo "HTTPS_PROXY: ${HTTPS_PROXY:-not set}"
echo "http_proxy: ${http_proxy:-not set}"
echo "https_proxy: ${https_proxy:-not set}"
echo "NO_PROXY: ${NO_PROXY:-not set}"
echo

echo "5. GAODE MAPS API TEST"
echo "--------------------"
echo "Direct curl test (5s timeout):"
timeout 5 curl -s "https://restapi.amap.com/v5/place/text?key=${AMAP_MAPS_API_KEY}&keywords=test&region=北京" \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Status: {data.get(\"status\", \"unknown\")}'); print(f'Info: {data.get(\"info\", \"unknown\")}')" \
  2>&1 || echo "  FAILED: Connection timeout or error"
echo

echo "6. PYTHON MODULE AVAILABILITY"
echo "---------------------------"
echo "Testing openmeteo_requests import:"
python3 -c "import openmeteo_requests; print('  SUCCESS')" 2>&1 || echo "  FAILED: Module not found"
echo

echo "Testing in venv:"
if [ -f ~/.claude/venv/bin/python3 ]; then
    ~/.claude/venv/bin/python3 -c "import openmeteo_requests; print('  SUCCESS in venv')" 2>&1 || echo "  FAILED in venv"
else
    echo "  Venv not found"
fi
echo

echo "7. AGENT EXECUTION CONTEXT (simulated)"
echo "-------------------------------------"
echo "Testing skill execution without .env loaded:"
(unset AMAP_MAPS_API_KEY GOOGLE_MAPS_API_KEY DUFFEL_API_KEY; \
 cd /root/travel-planner/.claude/skills/gaode-maps/scripts && \
 timeout 5 python3 -c "
import os
print(f'AMAP_MAPS_API_KEY in env: {\"AMAP_MAPS_API_KEY\" in os.environ}')
print(f'AMAP_MAPS_API_KEY value: {os.environ.get(\"AMAP_MAPS_API_KEY\", \"NOT SET\")[:20]}...')
" 2>&1)
echo

echo "8. load_env.py FUNCTIONALITY TEST"
echo "--------------------------------"
cd /root/travel-planner/.claude/skills/gaode-maps/scripts
python3 << 'PYEOF'
import sys
import os

print("Before load_env:")
print(f"  AMAP_MAPS_API_KEY: {os.environ.get('AMAP_MAPS_API_KEY', 'NOT SET')[:20]}...")

sys.path.insert(0, os.path.dirname(__file__))
import load_env

print("After load_env:")
print(f"  AMAP_MAPS_API_KEY: {os.environ.get('AMAP_MAPS_API_KEY', 'NOT SET')[:20]}...")
print(f"  Load successful: {os.environ.get('AMAP_MAPS_API_KEY') is not None}")
PYEOF

echo
echo "=================================="
echo "ANALYSIS COMPLETE"
echo "=================================="
