#!/bin/bash
# PreToolUse hook: Block Write/Edit to production paths from dev environment.
# Extended (W6, 2026-05-05): per-agent ownership enforcement (owned_files regex
# from .claude/agents/<agent>.md frontmatter) + universal image_url deny on
# data/**/*.json. ONE hook (architect concern_6 binding: do NOT split into a
# stack of bespoke hooks).
#
# Behavior:
#   1. Production-path block (legacy): /root/happy/, /root/.happy/,
#      /root/.happy-jade/, /usr/lib/node_modules/happy*, /usr/bin/happy*.
#   2. Agent-ownership block: when invoked under a subagent (env var
#      CLAUDE_AGENT_TYPE present and != 'orchestrator'), the target file_path
#      MUST match an anchored regex listed in
#      .claude/agents/<CLAUDE_AGENT_TYPE>.md frontmatter `owned_files`.
#   3. Universal image_url deny: any Write/Edit payload that introduces an
#      `image_url` key inside a data/**/*.json file is rejected, regardless of
#      caller. Codex Top-5 control 4: "no agent (any type) may directly write
#      image_url".
#   4. Orchestrator (no CLAUDE_AGENT_TYPE, or CLAUDE_AGENT_TYPE=orchestrator)
#      is exempt from check 2. Check 3 still applies.
#
# Created: 2026-04-04. Extended: 2026-05-05 (W6 / spec-20260505-221501 / M9).

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)

# Only act on Write and Edit tools
case "$TOOL_NAME" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# ---- Check 1: legacy production-path block ----
case "$FILE_PATH" in
  /root/happy/*)
    echo "BLOCKED: Write/Edit to production source /root/happy/ is FORBIDDEN from dev environment" >&2
    echo "Path: $FILE_PATH" >&2
    echo "Use git to bring changes into production." >&2
    exit 2 ;;
esac

case "$FILE_PATH" in
  /root/.happy/*)
    echo "BLOCKED: Write/Edit to production daemon home /root/.happy/ is FORBIDDEN" >&2
    echo "Path: $FILE_PATH" >&2
    exit 2 ;;
esac

case "$FILE_PATH" in
  /root/.happy-jade/*)
    echo "BLOCKED: Write/Edit to jade daemon home /root/.happy-jade/ is FORBIDDEN" >&2
    echo "Path: $FILE_PATH" >&2
    exit 2 ;;
esac

case "$FILE_PATH" in
  /usr/lib/node_modules/happy*)
    echo "BLOCKED: Write/Edit to global happy modules is FORBIDDEN" >&2
    echo "Path: $FILE_PATH" >&2
    exit 2 ;;
esac

case "$FILE_PATH" in
  /usr/bin/happy*)
    echo "BLOCKED: Write/Edit to global happy binary is FORBIDDEN" >&2
    echo "Path: $FILE_PATH" >&2
    exit 2 ;;
esac

# ---- Check 2 + Check 3: agent ownership + universal image_url deny ----
# Pass full payload via env var (HOOK_PAYLOAD) so the embedded Python can
# read it from the environment, freeing sys.stdin for the heredoc-as-script.
HOOK_PAYLOAD="$INPUT" python3 - "$FILE_PATH" "$TOOL_NAME" << 'PYHOOK_EOF'
import json
import os
import re
import sys

INPUT_JSON = os.environ.get('HOOK_PAYLOAD', '')
FILE_PATH = sys.argv[1]
TOOL_NAME = sys.argv[2]

try:
    payload = json.loads(INPUT_JSON)
except Exception:
    sys.exit(0)

tool_input = payload.get('tool_input', {}) or {}

def text_contains_image_url(text):
    if not text:
        return False
    return re.search(r'"image_url"\s*:', text) is not None

def json_payload_has_image_url(text):
    if not text:
        return False
    try:
        obj = json.loads(text)
    except Exception:
        return False
    stack = [obj]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if 'image_url' in node:
                return True
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return False

PROJECT_ROOT = os.environ.get('CLAUDE_PROJECT_DIR', '/root/travel-planner')
try:
    rel_path = os.path.relpath(FILE_PATH, PROJECT_ROOT)
except Exception:
    rel_path = FILE_PATH

is_data_json = bool(re.match(r'^data/[^/]+/[^/]+\.json$', rel_path))

# Check 3 first: universal image_url deny on data/**/*.json.
if is_data_json:
    candidate_text = ''
    if TOOL_NAME == 'Write':
        candidate_text = tool_input.get('content', '') or ''
    elif TOOL_NAME == 'Edit':
        candidate_text = tool_input.get('new_string', '') or ''

    if candidate_text:
        offending = (json_payload_has_image_url(candidate_text)
                     or text_contains_image_url(candidate_text))
        if offending:
            sys.stderr.write(
                "BLOCKED: universal image_url deny - payload writes 'image_url' "
                f"key into {rel_path}.\n"
                "Codex Top-5 control 4: no agent (or script) may directly "
                "write image_url. Images live in data/<trip>/images.json only "
                "and are populated exclusively by scripts/fetch-images-batch.py.\n"
            )
            sys.exit(2)

# Check 2: agent ownership.
agent_type = os.environ.get('CLAUDE_AGENT_TYPE', '').strip()
DATA_AGENT_TYPES = {
    'meals', 'accommodation', 'transportation', 'attractions',
    'entertainment', 'shopping', 'cafe', 'timeline', 'budget',
}
if agent_type and agent_type in DATA_AGENT_TYPES:
    agent_md = os.path.join(PROJECT_ROOT, '.claude', 'agents', f'{agent_type}.md')
    owned_regexes = []
    if os.path.isfile(agent_md):
        try:
            with open(agent_md, 'r') as f:
                src = f.read()
            m = re.search(r'(?ms)^---\n(.*?)\n---\n', src)
            if m:
                fm = m.group(1)
                in_block = False
                for line in fm.splitlines():
                    if re.match(r'^owned_files:\s*$', line):
                        in_block = True
                        continue
                    if in_block:
                        sm = re.match(r'^-\s+(.+?)\s*$', line)
                        if sm:
                            owned_regexes.append(sm.group(1))
                        else:
                            if re.match(r'^\S', line):
                                in_block = False
        except Exception:
            owned_regexes = []

    if owned_regexes:
        matched = False
        for pat in owned_regexes:
            try:
                if re.match(pat, rel_path):
                    matched = True
                    break
            except re.error:
                continue
        if not matched:
            sys.stderr.write(
                f"BLOCKED: agent '{agent_type}' attempted to write {rel_path}, "
                f"which is not in its owned_files allowlist.\n"
                f"Allowed patterns: {owned_regexes}\n"
                f"See .claude/agents/{agent_type}.md frontmatter.\n"
            )
            sys.exit(2)

sys.exit(0)
PYHOOK_EOF
