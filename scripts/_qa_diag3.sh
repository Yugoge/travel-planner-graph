#!/bin/bash
# Test the EXACT cycle-1 finding-1 reproduction.
PATBUF='LmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8qKg=='
PAT=$(echo "$PATBUF" | base64 -d)

cd /root/travel-planner
echo "cwd: $(pwd)"
echo "pattern: $PAT"

echo ""
echo "=== Direct python from /root/travel-planner ==="
CLAUDE_PROJECT_DIR=/root/travel-planner python3 <<PYEOF
import sys, os
sys.path.insert(0, '/root/.claude/hooks/lib')
target = "$PAT"
print('target:', target)
print('abspath:', os.path.abspath(target))
from policy_registry import _candidate_targets, is_gaode_allowed
print('candidates:', _candidate_targets(target))
allowed, reason = is_gaode_allowed("dev", "read-path", target)
print('allowed=', allowed, 'reason=', reason)
PYEOF

echo ""
echo "=== Hook end-to-end with subagent_type=dev ==="
CLAUDE_PROJECT_DIR=/root/travel-planner printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Hook end-to-end without subagent_type (should hit identity-default-deny) ==="
CLAUDE_PROJECT_DIR=/root/travel-planner printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"}}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"
