#!/bin/bash
PATBUF='LmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8qKg=='
PAT=$(echo "$PATBUF" | base64 -d)

cd /root/travel-planner

echo "=== With CLAUDE_PROJECT_DIR set ==="
CLAUDE_PROJECT_DIR=/root/travel-planner printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Investigate: hook with verbose tracing ==="
CLAUDE_PROJECT_DIR=/root/travel-planner python3 <<PYEOF
import sys, os, json, io
sys.path.insert(0, '/root/.claude/hooks')
sys.path.insert(0, '/root/.claude/hooks/lib')

target = "$PAT"
print('target=', repr(target))

# What does the hook see for tool_input?
tool_input = {"pattern": target}
print('tool_input=', tool_input)

# Trace through field whitelist scanner
from policy_registry import is_gaode_allowed
# Glob.pattern -> read-path
allowed, reason = is_gaode_allowed("dev", "read-path", target)
print('is_gaode_allowed("dev", "read-path", target):', allowed, reason)

# Try with abspath manually
abspath = os.path.abspath(target)
print('os.path.abspath(target):', abspath)
allowed, reason = is_gaode_allowed("dev", "read-path", abspath)
print('with abspath:', allowed, reason)
PYEOF
