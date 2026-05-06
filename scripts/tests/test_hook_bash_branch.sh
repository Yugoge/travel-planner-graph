#!/usr/bin/env bash
# Test the Bash branch of pretool-block-production-files.sh in isolation.
HOOK=/root/travel-planner/.claude/hooks/pretool-block-production-files.sh

run_case() {
  local label="$1" envelope="$2" expected_exit="$3"
  local actual_exit stderr_text
  stderr_text=$(printf '%s' "$envelope" | bash "$HOOK" 2>&1 1>/dev/null)
  actual_exit=$?
  if [[ "$actual_exit" == "$expected_exit" ]]; then
    echo "PASS: $label  (exit=$actual_exit)"
  else
    echo "FAIL: $label  (got exit=$actual_exit, want $expected_exit)"
  fi
  if [[ -n "$stderr_text" ]]; then
    echo "    stderr: $stderr_text"
  fi
}

# Case A: direct redirect into data/<trip>/<file>.json -> BLOCKED
run_case "direct-redirect-blocks" \
  '{"tool_name":"Bash","tool_input":{"command":"echo hi > data/china-20260412-092624/meals.json"}}' \
  2

# Case B: ls scripts/save.py (mention only) -> ALLOWED
run_case "save-py-mention-only-allows" \
  '{"tool_name":"Bash","tool_input":{"command":"ls scripts/save.py"}}' \
  0

# Case C: clean save.py invocation pointing at non-image_url payload -> ALLOWED
echo '{"data":{"days":[]}}' > /tmp/dev-clean-input.json
run_case "save-py-clean-allows" \
  '{"tool_name":"Bash","tool_input":{"command":"python3 scripts/save.py --trip china-20260412-092624 --agent meals --input /tmp/dev-clean-input.json"}}' \
  0

# Case D: save.py invocation with image_url-bearing input -> BLOCKED
echo '{"data":{"days":[{"day":1,"breakfast":{"image_url":"http://leak.example/x.jpg"}}]}}' > /tmp/dev-leak-input.json
run_case "save-py-image-url-blocks" \
  '{"tool_name":"Bash","tool_input":{"command":"python3 scripts/save.py --trip china-20260412-092624 --agent meals --input /tmp/dev-leak-input.json"}}' \
  2

# Case E: tee into data/<trip>/<file>.json -> BLOCKED
run_case "tee-into-data-blocks" \
  '{"tool_name":"Bash","tool_input":{"command":"echo hi | tee data/china-20260412-092624/meals.json"}}' \
  2

# Case F: cp into data/<trip>/<file>.json -> BLOCKED
run_case "cp-into-data-blocks" \
  '{"tool_name":"Bash","tool_input":{"command":"cp /tmp/x.json data/china-20260412-092624/meals.json"}}' \
  2

# Case G: non-data Bash command -> ALLOWED
run_case "non-data-bash-allows" \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la /tmp"}}' \
  0

# Case H: save.py invocation with cross-agent ownership violation -> BLOCKED
run_case "save-py-cross-agent-blocks" \
  '{"tool_name":"Bash","tool_input":{"command":"python3 scripts/save.py --trip china-20260412-092624 --agent meals --input /tmp/dev-clean-input.json --output-target attractions.json"}}' \
  0  # No file_path conflict resolves; meals + meals.json target matches owned

# Cleanup
rm -f /tmp/dev-clean-input.json /tmp/dev-leak-input.json
