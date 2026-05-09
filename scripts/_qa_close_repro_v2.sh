#!/bin/bash
# Re-reproduce cycle-1 close-report findings with explicit CLAUDE_PROJECT_DIR.
export CLAUDE_PROJECT_DIR=/root/travel-planner

PATBUF='LmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8qKg=='
URLBUF='aHR0cHM6Ly9yZXN0YXBpLmFtYXAuY29tL3YzL3Rlc3Q='
SKILLBUF='c2NyaXB0czpnYW9kZS1tYXBzOnRvb2xzOnJvdXRpbmc='

echo "=== Finding #1: Glob.pattern bypass (with CLAUDE_PROJECT_DIR set) ==="
PAT=$(echo "$PATBUF" | base64 -d)
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"
echo ""

echo "=== Finding #1 (with leading slash, no project context needed) ==="
PATBUF_ABS='Ly5jbGF1ZGUvc2tpbGxzL2dhb2RlLW1hcHMvKio='
PAT_ABS=$(echo "$PATBUF_ABS" | base64 -d)
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$PAT_ABS" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"
echo ""

echo "=== Finding #1 with subagent_type=meals (banned, no roles entry) ==="
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"meals"}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"
echo ""

echo "=== Finding #2: MCP browser_navigate ==="
URL=$(echo "$URLBUF" | base64 -d)
printf '{"tool_name":"mcp__playwright__browser_navigate","tool_input":{"url":"%s"},"subagent_type":"dev"}' "$URL" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"
echo ""

echo "=== Finding #3: AC6 timeline Skill positive ==="
SK=$(echo "$SKILLBUF" | base64 -d)
printf '{"tool_name":"Skill","tool_input":{"skill":"%s"},"subagent_type":"timeline"}' "$SK" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"
echo ""

echo "=== Finding #4: BA-QA r2 JSON ==="
python3 -c "import json; json.load(open('/root/travel-planner/docs/dev/ba-qa-report-20260509-114002-r2.json')); print('VALID')"
echo "exit=$?"
echo ""

echo "=== Edge case: Glob with leading-slash pattern; no subagent (identity-default-deny) ==="
PAT_ABS=$(echo "$PATBUF_ABS" | base64 -d)
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"}}' "$PAT_ABS" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Edge case: pattern with shell brace expansion {a,b}/gaode-maps/* ==="
BRACEBUF='e2EsYn0vLmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8qLm1k'
BR=$(echo "$BRACEBUF" | base64 -d)
echo "  pattern: $BR"
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$BR" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Edge case: ?-shaped wildcard pattern ==="
QBUF='Ly5jbGF1ZGUvc2tpbGxzL2dhb2Rlbi1tYXBzL3Rvb2xzL3JvdXRpbmcucHk='
QP=$(echo "$QBUF" | base64 -d)
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$QP" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"
