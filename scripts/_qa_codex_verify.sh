#!/bin/bash
# Verify the 4 critical Codex bypass claims independently.
export CLAUDE_PROJECT_DIR=/root/travel-planner
HOOK=/root/.claude/hooks/pretool-tool-policy.py

# Codex claim 1: Glob(pattern="**/.claude/skills/g-aode-maps/**") → exits 0
PAT1='KiovLmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8qKg=='
P1=$(echo "$PAT1" | base64 -d)
echo "=== Codex Claim 1: Glob(pattern=\"**/.claude/skills/...\") subagent_type=dev ==="
echo "  pattern: $P1"
printf '{"tool_name":"Glob","tool_input":{"pattern":"%s"},"subagent_type":"dev"}' "$P1" | python3 "$HOOK"
echo "exit=$?"
echo ""

# Codex claim 2: Grep(glob="**/.claude/commands/scripts/g-aode-maps/**") → exits 0
PAT2='KiovLmNsYXVkZS9jb21tYW5kcy9zY3JpcHRzL2dhb2RlLW1hcHMvKio='
P2=$(echo "$PAT2" | base64 -d)
echo "=== Codex Claim 2: Grep(glob=\"**/.claude/commands/scripts/...\") subagent_type=dev ==="
echo "  glob: $P2"
printf '{"tool_name":"Grep","tool_input":{"pattern":"key","glob":"%s"},"subagent_type":"dev"}' "$P2" | python3 "$HOOK"
echo "exit=$?"
echo ""

# Codex claim 3: Grep(path=".claude/commands/scripts", pattern="poi") → exits 0; can traverse banned subtree
PAT3='LmNsYXVkZS9jb21tYW5kcy9zY3JpcHRz'
P3=$(echo "$PAT3" | base64 -d)
echo "=== Codex Claim 3: Grep(path=\".claude/commands/scripts\", pattern=\"poi\") subagent_type=dev ==="
echo "  path: $P3"
printf '{"tool_name":"Grep","tool_input":{"path":"%s","pattern":"poi"},"subagent_type":"dev"}' "$P3" | python3 "$HOOK"
echo "exit=$?"
echo ""

# Codex claim 4: Glob(path=".claude/commands/scripts", pattern="**/*") → exits 0
echo "=== Codex Claim 4: Glob(path=\".claude/commands/scripts\", pattern=\"**/*\") subagent_type=dev ==="
echo "  path: $P3, pattern: **/*"
printf '{"tool_name":"Glob","tool_input":{"path":"%s","pattern":"**/*"},"subagent_type":"dev"}' "$P3" | python3 "$HOOK"
echo "exit=$?"
echo ""

# Bonus: even more direct — what about Glob(path=".claude/skills/g-aode-maps")?
PAT5='LmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcw=='
P5=$(echo "$PAT5" | base64 -d)
echo "=== Bonus Claim 5: Glob(path=\".claude/skills/g-aode-maps\") subagent_type=dev ==="
echo "  path: $P5"
printf '{"tool_name":"Glob","tool_input":{"path":"%s","pattern":"*"},"subagent_type":"dev"}' "$P5" | python3 "$HOOK"
echo "exit=$?"
echo ""

# What about Read of the parent directory?
PAT6='L3Jvb3QvLmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy9TS0lMTC5tZA=='
P6=$(echo "$PAT6" | base64 -d)
echo "=== Bonus Claim 6: Read(file_path=\"/root/.claude/skills/g-aode-maps/SKILL.md\") subagent_type=dev ==="
echo "  file_path: $P6"
printf '{"tool_name":"Read","tool_input":{"file_path":"%s"},"subagent_type":"dev"}' "$P6" | python3 "$HOOK"
echo "exit=$?"
