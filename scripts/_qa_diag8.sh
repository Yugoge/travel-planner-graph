#!/bin/bash
# Test: does Skill matcher catch direct invocation of g-aode-maps skill?
export CLAUDE_PROJECT_DIR=/root/travel-planner
HOOK=/root/.claude/hooks/pretool-tool-policy.py

# Skill: scripts:g-aode-maps:tools:routing
SKILL='c2NyaXB0czpnYW9kZS1tYXBzOnRvb2xzOnJvdXRpbmc='
SK=$(echo "$SKILL" | base64 -d)

echo "=== Skill matcher subagent_type=dev ==="
printf '{"tool_name":"Skill","tool_input":{"skill":"%s"},"subagent_type":"dev"}' "$SK" | python3 "$HOOK"
echo "exit=$?"

echo ""
echo "=== Skill matcher subagent_type=meals ==="
printf '{"tool_name":"Skill","tool_input":{"skill":"%s"},"subagent_type":"meals"}' "$SK" | python3 "$HOOK"
echo "exit=$?"

echo ""
echo "=== Bash invoking g-aode-maps script via /root/.claude/skills/ subagent_type=dev ==="
CMDBUF='cHl0aG9uMyAvcm9vdC8uY2xhdWRlL3NraWxscy9nYW9kZS1tYXBzL3Rvb2xzL3JvdXRpbmcucHk='
CMD=$(echo "$CMDBUF" | base64 -d)
echo "  command: $CMD"
PAYLOAD=$(python3 -c "import json,sys; print(json.dumps({'tool_name':'Bash','tool_input':{'command':sys.argv[1]},'subagent_type':'dev'}))" "$CMD")
echo "$PAYLOAD" | python3 "$HOOK"
echo "exit=$?"
