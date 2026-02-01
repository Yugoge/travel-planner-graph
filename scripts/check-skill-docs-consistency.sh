#!/usr/bin/env bash
# Check all MCP-based skills for documentation vs implementation mismatch
# Usage: check-skill-docs-consistency.sh [skills_dir]
# Exit codes: 0=all consistent, 1=inconsistencies found, 2=error

set -euo pipefail

SKILLS_DIR="${1:-.claude/skills}"

if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "Error: Skills directory not found: $SKILLS_DIR" >&2
  exit 2
fi

echo "Checking skill documentation consistency in: $SKILLS_DIR"
echo

INCONSISTENCIES=0

for skill_path in "$SKILLS_DIR"/*; do
  if [[ ! -d "$skill_path" ]]; then
    continue
  fi

  skill_name=$(basename "$skill_path")
  skill_md="$skill_path/SKILL.md"
  scripts_dir="$skill_path/scripts"

  # Skip if no SKILL.md
  if [[ ! -f "$skill_md" ]]; then
    continue
  fi

  # Check if scripts directory exists
  has_scripts=false
  if [[ -d "$scripts_dir" ]] && [[ -n "$(ls -A "$scripts_dir" 2>/dev/null)" ]]; then
    has_scripts=true
  fi

  # Check SKILL.md content
  doc_claims_no_scripts=false
  if grep -qi "no python scripts" "$skill_md" 2>/dev/null; then
    doc_claims_no_scripts=true
  elif grep -qi "directly as MCP" "$skill_md" 2>/dev/null; then
    doc_claims_no_scripts=true
  elif grep -qi "pure MCP integration" "$skill_md" 2>/dev/null; then
    doc_claims_no_scripts=true
  fi

  # Detect inconsistency
  if $has_scripts && $doc_claims_no_scripts; then
    echo "✗ INCONSISTENCY: $skill_name"
    echo "  Documentation claims: No scripts / Direct MCP"
    echo "  Reality: scripts/ directory exists with files"
    echo "  Location: $scripts_dir"
    echo "  Files:"
    ls -1 "$scripts_dir" | sed 's/^/    - /'
    echo
    ((INCONSISTENCIES++))
  elif ! $has_scripts && ! $doc_claims_no_scripts; then
    # This might be okay - skill could have scripts mentioned but not yet implemented
    # We only flag the opposite case (claims no scripts but has them)
    :
  fi
done

if [[ $INCONSISTENCIES -eq 0 ]]; then
  echo "✓ All skill documentation is consistent with implementation"
  exit 0
else
  echo "✗ Found $INCONSISTENCIES skill(s) with documentation inconsistencies" >&2
  echo
  echo "Action required: Update SKILL.md files to accurately reflect implementation" >&2
  exit 1
fi
