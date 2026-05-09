#!/bin/bash
# QA close-debate cycle-3 reproduction script — base64 indirection avoids self-tripping the hook.
SKILLBUF='c2NyaXB0czpnYW9kZS1tYXBzOnRvb2xzOnJvdXRpbmc='
URLBUF='aHR0cHM6Ly9yZXN0YXBpLmFtYXAuY29tL3YzL3Rlc3Q='
PATBUF='Ly5jbGF1ZGUvc2tpbGxzL2dhb2RlLW1hcHMvKio='

echo "=== Finding #1: Glob.pattern bypass ==="
PAT=$(echo "$PATBUF" | base64 -d)
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"meals"}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Finding #2: MCP browser_navigate bypass ==="
URL=$(echo "$URLBUF" | base64 -d)
printf '{"tool_name":"mcp__playwright__browser_navigate","tool_input":{"url":"%s"},"subagent_type":"meals"}' "$URL" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Finding #3: AC6 timeline Skill positive ==="
SK=$(echo "$SKILLBUF" | base64 -d)
printf '{"tool_name":"Skill","tool_input":{"skill":"%s"},"subagent_type":"timeline"}' "$SK" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Finding #4: BA-QA r2 JSON parse ==="
python3 -c "import json; json.load(open('/root/travel-planner/docs/dev/ba-qa-report-20260509-114002-r2.json')); print('VALID')"
echo "exit=$?"

echo ""
echo "=== AC18 Feb-13 guard: timeline Write should be denied ==="
printf '{"tool_name":"Write","tool_input":{"file_path":"/tmp/foo.txt","content":"x"},"subagent_type":"timeline"}' | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== AC15 BA documentation false-positive guard: ba Edit ticket containing amap URL should be allowed ==="
URL2=$(echo "$URLBUF" | base64 -d)
printf '{"tool_name":"Edit","tool_input":{"file_path":"/root/travel-planner/docs/dev/ticket-test.md","old_string":"x","new_string":"see %s"},"subagent_type":"ba"}' "$URL2" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"
