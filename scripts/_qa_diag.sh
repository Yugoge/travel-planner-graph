#!/bin/bash
# Diagnose why Glob.pattern alone (no path) didn't fire gaode read-path matcher.
PATBUF='Ly5jbGF1ZGUvc2tpbGxzL2dhb2RlLW1hcHMvKio='

echo "=== Glob with absolute pattern only ==="
PAT=$(echo "$PATBUF" | base64 -d)
echo "  pattern = $PAT"
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py 2>&1
echo "  exit=$?"

echo ""
echo "=== Glob with relative pattern (no leading slash) ==="
PATBUF2='LmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8qKg=='
PAT2=$(echo "$PATBUF2" | base64 -d)
echo "  pattern = $PAT2"
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$PAT2" | python3 /root/.claude/hooks/pretool-tool-policy.py 2>&1
echo "  exit=$?"

echo ""
echo "=== Grep with glob field only ==="
printf '{"tool_name":"Grep","tool_input":{"pattern":"k","glob":"%s"},"subagent_type":"dev"}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py 2>&1
echo "  exit=$?"

echo ""
echo "=== Glob with path only (denied prefix) ==="
PATHBUF='L3Jvb3QvLmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8='
PTH=$(echo "$PATHBUF" | base64 -d)
echo "  path = $PTH"
printf '{"tool_name":"Glob","tool_input":{"path":"%s","pattern":"*.md"},"subagent_type":"dev"}' "$PTH" | python3 /root/.claude/hooks/pretool-tool-policy.py 2>&1
echo "  exit=$?"
