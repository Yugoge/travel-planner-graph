#!/bin/bash
# Verify Glob.pattern bypass closure with a known-good role (dev, in roles dict).
PATBUF='Ly5jbGF1ZGUvc2tpbGxzL2dhb2RlLW1hcHMvKio='
PATBUF2='Ly5jbGF1ZGUvY29tbWFuZHMvc2NyaXB0cy9nYW9kZS1tYXBzLyoq'

echo "=== Glob.pattern as dev role — should fire gaode-policy read-path matcher ==="
PAT=$(echo "$PATBUF" | base64 -d)
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$PAT" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Grep.glob as dev role — should fire gaode-policy read-path matcher ==="
PAT2=$(echo "$PATBUF2" | base64 -d)
printf '{"tool_name":"Grep","tool_input":{"pattern":"key","glob":"%s"},"subagent_type":"dev"}' "$PAT2" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Composed-path bypass: Glob path=/.../skills + pattern=gaode-maps/** ==="
PATH_BUF='L3Jvb3QvLmNsYXVkZS9za2lsbHMv'
PAT_BUF='Z2FvZGUtbWFwcy8qKg=='
PSEG=$(echo "$PATH_BUF" | base64 -d)
PSEG2=$(echo "$PAT_BUF" | base64 -d)
printf '{"tool_name":"Glob","tool_input":{"path":"%s","pattern":"%s"},"subagent_type":"dev"}' "$PSEG" "$PSEG2" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== Heredoc body bypass: bash with python3 inside heredoc body ==="
HEREBUF='YmFzaCA8PEVPRgpweXRob24zIC9yb290Ly5jbGF1ZGUvY29tbWFuZHMvc2NyaXB0cy9nYW9kZS1tYXBzL3NjcmlwdHMvcG9pX3NlYXJjaC5weQpFT0Y='
CMD=$(echo "$HEREBUF" | base64 -d)
printf '{"tool_name":"Bash","tool_input":{"command":%s},"subagent_type":"dev"}' "$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$CMD")" | python3 /root/.claude/hooks/pretool-tool-policy.py
echo "exit=$?"

echo ""
echo "=== T1 verifier ==="
T1='/root/travel-planner/scripts/verify-gaode-ban.sh'
bash "$T1" 2>&1 | tail -5
echo ""
echo "=== T2 integration verifier ==="
T2='/root/travel-planner/scripts/verify-gaode-ban-integration.sh'
bash "$T2" 2>&1 | tail -5
echo ""
echo "=== T3 contract verifier ==="
T3='/root/travel-planner/scripts/verify-gaode-ban-contract.sh'
bash "$T3" 2>&1 | tail -5
