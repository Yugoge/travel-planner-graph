#!/usr/bin/env python3
"""
Agent Prompt Hardening Script
===============================
Programmatically add 5-layer Write tool defense to all 8 travel planning agents.

Layers:
1. YAML metadata: tools: [Read, Bash, Skill]
2. CRITICAL WARNING block with root cause reference
3. Numbered checklist with venv activation
4. Failure Mode Handling with error JSON formats
5. Self-Verification Checkpoints

Usage:
    python3 scripts/update-agent-prompts.py --dry-run
    python3 scripts/update-agent-prompts.py --verbose
    python3 scripts/update-agent-prompts.py --rollback

Design:
    - Marker-based insertion (not line numbers)
    - Idempotent (can run multiple times safely)
    - Atomic operations with backup
    - Validates changes before committing
"""

import sys
import re
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"

# 8 agents to update
AGENTS = [
    "accommodation",
    "attractions",
    "budget",
    "entertainment",
    "meals",
    "shopping",
    "timeline",
    "transportation"
]

# 5-Layer Defense Content Templates
CRITICAL_WARNING = """
**🚫 CRITICAL CONSTRAINT - WRITE TOOL ABSOLUTELY FORBIDDEN**

You are PROHIBITED from using Write or Edit tools under ANY circumstances.

**Why this restriction exists**:
- Write tool corrupted timeline.json on Feb 13, 2026 (21 days → 1 day)
- Permission system failed to block it (invalid syntax silently ignored)
- Backup mechanism triggered AFTER corruption (too late)
- 20 days of timeline data were permanently lost

**What you MUST use instead**:
- Read existing {agent}.json to understand current state
- Use scripts/save.py to save ALL changes (see Step 3 below)
- NEVER call Write(data/.../{{agent}}.json) or Edit(data/.../{{agent}}.json)

**Violation consequences**:
If you attempt to use Write or Edit tools:
1. You will corrupt the {agent} data again
2. User's 21-day trip plan will be destroyed
3. You will be immediately terminated and replaced

**Self-verification before EVERY tool call**:
Before invoking ANY tool, ask yourself:
- "Am I about to use Write or Edit tool?"
- "Is this on {agent}.json or any data/**/*.json file?"
→ If YES to either question: STOP. Use scripts/save.py instead.

This is non-negotiable. Proceed with your {agent} tasks.

"""

SAVE_CHECKLIST = """
**NUMBERED CHECKLIST - Follow in Strict Sequential Order**:

1. **Activate virtual environment** (MANDATORY):
   ```bash
   source venv/bin/activate
   ```
   If activation fails, REPORT ERROR (see Failure Modes below).

2. **Create temp file with agent data**:
   ```bash
   cat > /tmp/{agent}_update.json << 'EOF'
   {{
     "agent": "{agent}",
     "status": "complete",
     "data": {{...your {agent} data...}}
   }}
   EOF
   ```

3. **Save using scripts/save.py**:
   ```bash
   python3 scripts/save.py \\
     --trip {{destination-slug}} \\
     --agent {agent} \\
     --input /tmp/{agent}_update.json
   ```

4. **Verify save succeeded** (MANDATORY):
   Check exit code:
   - Exit code 0 = success → proceed
   - Exit code 1 = validation failed → REPORT ERROR (see Failure Modes)
   - Exit code 2 = write failed → REPORT ERROR

   If exit code is NOT 0, you MUST stop and report error to user.

5. **Return completion status**:
   Only after exit code 0, return:
   ```json
   {{
     "agent": "{agent}",
     "status": "complete",
     "saved_to": "data/{{destination-slug}}/{agent}.json"
   }}
   ```

**CRITICAL**: If ANY step fails, DO NOT proceed to next step. Report error immediately.
"""

FAILURE_MODES = """
## Failure Mode Handling

**If you cannot complete Step 3 (save.py) for ANY reason, you MUST return this exact error format**:

### Error Format 1: Virtual Environment Activation Failed
```json
{{
  "agent": "{agent}",
  "status": "error",
  "error_type": "venv_activation_failed",
  "message": "Cannot activate virtual environment at venv/bin/activate",
  "attempted_command": "source venv/bin/activate",
  "user_action_required": "Verify virtual environment exists: ls -la venv/bin/activate"
}}
```

### Error Format 2: save.py Validation Failed
```json
{{
  "agent": "{agent}",
  "status": "error",
  "error_type": "validation_failed",
  "message": "scripts/save.py rejected data due to HIGH severity validation issues",
  "exit_code": 1,
  "validation_summary": "Extract from stderr: '❌ Validation failed with N HIGH severity issues'",
  "user_action_required": "Fix validation issues reported by save.py, then re-run agent"
}}
```

### Error Format 3: save.py Write Failed
```json
{{
  "agent": "{agent}",
  "status": "error",
  "error_type": "write_failed",
  "message": "scripts/save.py atomic write operation failed",
  "exit_code": 2,
  "stderr_output": "Captured stderr from save.py",
  "user_action_required": "Check file permissions on data/{{destination-slug}}/{agent}.json"
}}
```

### Error Format 4: save.py Script Not Found
```json
{{
  "agent": "{agent}",
  "status": "error",
  "error_type": "script_not_found",
  "message": "scripts/save.py does not exist",
  "attempted_path": "scripts/save.py",
  "user_action_required": "Verify save.py exists: ls -la scripts/save.py"
}}
```

### Error Format 5: Unknown save.py Error
```json
{{
  "agent": "{agent}",
  "status": "error",
  "error_type": "unknown_save_error",
  "message": "scripts/save.py failed with unexpected error",
  "exit_code": "{{actual_exit_code}}",
  "stderr_output": "Full stderr from save.py",
  "user_action_required": "Report this error to user with full stderr output"
}}
```

**ABSOLUTE REQUIREMENT**: If save.py fails for ANY reason, you MUST:
1. Return one of the 5 error JSON formats above (NOT attempt Write tool as fallback)
2. Include complete stderr output from save.py in your error message
3. STOP processing immediately (do not continue to other days or tasks)

**DO NOT**:
- Attempt to use Write tool as fallback ❌
- Guess at what went wrong without checking exit codes ❌
- Continue processing if save failed ❌
- Return "status": "complete" if save.py had exit code ≠ 0 ❌
"""

VERIFICATION_CHECKPOINTS = """
## Self-Verification Checkpoints

**Before invoking ANY tool, run this mental checklist**:

```
□ Am I about to call Write tool?
  → If YES: STOP. This violates CRITICAL CONSTRAINT above.

□ Am I about to call Edit tool?
  → If YES: STOP. This violates CRITICAL CONSTRAINT above.

□ Am I creating a temp file with > or >>?
  → If YES and it's for save.py input: PROCEED (this is correct).
  → If YES and it's direct to data/*.json: STOP (use save.py instead).

□ Have I activated venv before calling save.py?
  → If NO: STOP. Run "source venv/bin/activate" first.

□ Did save.py exit with code 0?
  → If NO: STOP. Report error using Failure Mode formats above.
  → If UNKNOWN: CHECK exit code with $? before proceeding.

□ Am I returning status: "complete"?
  → If YES: Verify save.py actually succeeded (exit code 0).
  → If save failed: Return error JSON instead.
```

**After completing each day/task, verify**:
- Temp file was created successfully
- save.py command included correct --trip and --agent flags
- Exit code was checked before continuing
- Only returned "complete" after successful save

**On encountering errors**:
- Read full stderr output from save.py
- Match error to one of 5 Failure Modes above
- Return appropriate error JSON format
- DO NOT continue processing
"""


def parse_frontmatter(content: str) -> Tuple[Optional[dict], str, int]:
    """Parse YAML frontmatter from markdown.

    Returns:
        (metadata_dict, body_content, frontmatter_end_line)
    """
    lines = content.split('\n')

    if not lines or not lines[0].strip() == '---':
        return None, content, 0

    # Find closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break

    if end_idx is None:
        return None, content, 0

    frontmatter = '\n'.join(lines[1:end_idx])
    body = '\n'.join(lines[end_idx + 1:])

    try:
        metadata = yaml.safe_load(frontmatter)
        return metadata, body, end_idx
    except yaml.YAMLError as e:
        print(f"❌ YAML parse error: {e}", file=sys.stderr)
        return None, content, 0


def add_tools_restriction(metadata: dict) -> bool:
    """Add tools: [Read, Bash, Skill] to metadata.

    Returns:
        True if modified, False if already present
    """
    if 'tools' in metadata:
        current = metadata['tools']
        expected = ['Read', 'Bash', 'Skill']
        if current == expected:
            return False
        # Update if different
        metadata['tools'] = expected
        return True
    else:
        metadata['tools'] = ['Read', 'Bash', 'Skill']
        return True


def find_insertion_point(body: str, marker_pattern: str) -> Optional[int]:
    """Find line number for content insertion based on marker.

    Returns:
        Line index (0-based) or None if not found
    """
    lines = body.split('\n')
    for i, line in enumerate(lines):
        if re.search(marker_pattern, line):
            return i
    return None


def insert_after_line(body: str, line_idx: int, content: str) -> str:
    """Insert content after specified line."""
    lines = body.split('\n')
    lines.insert(line_idx + 1, content)
    return '\n'.join(lines)


def insert_before_line(body: str, line_idx: int, content: str) -> str:
    """Insert content before specified line."""
    lines = body.split('\n')
    lines.insert(line_idx, content)
    return '\n'.join(lines)


def is_already_hardened(body: str) -> bool:
    """Check if agent already has 5-layer defense."""
    markers = [
        r'🚫 CRITICAL CONSTRAINT - WRITE TOOL ABSOLUTELY FORBIDDEN',
        r'NUMBERED CHECKLIST - Follow in Strict Sequential Order',
        r'Failure Mode Handling',
        r'Self-Verification Checkpoints'
    ]

    matches = sum(1 for marker in markers if re.search(marker, body))
    return matches >= 3  # At least 3 of 4 markers present


def update_agent_file(agent: str, dry_run: bool = False, verbose: bool = False) -> bool:
    """Update single agent file with 5-layer defense.

    Returns:
        True if successful, False otherwise
    """
    agent_file = AGENTS_DIR / f"{agent}.md"

    if not agent_file.exists():
        print(f"⚠️  {agent}.md not found, skipping", file=sys.stderr)
        return False

    # Read current content
    content = agent_file.read_text(encoding='utf-8')

    # Parse frontmatter
    metadata, body, fm_end_line = parse_frontmatter(content)

    if metadata is None:
        print(f"❌ {agent}.md: Failed to parse YAML frontmatter", file=sys.stderr)
        return False

    # Check if already hardened
    if is_already_hardened(body):
        if verbose:
            print(f"✓ {agent}.md: Already hardened, skipping", file=sys.stderr)
        return True

    # Layer 1: Add tools restriction to metadata
    modified_metadata = add_tools_restriction(metadata)

    # Layer 2: Add CRITICAL WARNING after frontmatter
    warning = CRITICAL_WARNING.format(agent=agent)

    # Find first ## section (insertion point)
    first_section_idx = find_insertion_point(body, r'^## ')

    if first_section_idx is None:
        print(f"❌ {agent}.md: Cannot find first ## section", file=sys.stderr)
        return False

    # Insert warning before first section
    body = insert_before_line(body, first_section_idx, warning)

    # Layer 3: Enhance Step 3 with numbered checklist
    step3_idx = find_insertion_point(body, r'### Step 3:.*Save')

    if step3_idx is not None:
        checklist = SAVE_CHECKLIST.format(agent=agent)
        # Replace Step 3 section content
        # Find next ### or ## (end of section)
        lines = body.split('\n')
        end_idx = None
        for i in range(step3_idx + 1, len(lines)):
            if re.search(r'^###? ', lines[i]):
                end_idx = i
                break

        if end_idx:
            # Replace content between step3_idx and end_idx
            new_lines = lines[:step3_idx + 1] + [checklist] + lines[end_idx:]
            body = '\n'.join(new_lines)
        else:
            # Just append after Step 3
            body = insert_after_line(body, step3_idx, checklist)
    else:
        if verbose:
            print(f"⚠️  {agent}.md: Step 3 section not found, skipping checklist insertion", file=sys.stderr)

    # Layer 4: Add Failure Mode Handling before ## Validation
    validation_idx = find_insertion_point(body, r'^## Validation')

    if validation_idx is not None:
        failure_modes = FAILURE_MODES.format(agent=agent)
        body = insert_before_line(body, validation_idx, failure_modes)
    else:
        # Add at end if Validation section not found
        if verbose:
            print(f"⚠️  {agent}.md: Validation section not found, adding Failure Modes at end", file=sys.stderr)
        body += "\n" + FAILURE_MODES.format(agent=agent)

    # Layer 5: Add Self-Verification Checkpoints at end
    body += "\n" + VERIFICATION_CHECKPOINTS

    # Reconstruct file
    new_frontmatter = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
    new_content = f"---\n{new_frontmatter}---\n{body}"

    if dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN: {agent}.md")
        print(f"{'='*60}")
        print(f"Would add tools: {metadata.get('tools', 'N/A')}")
        print(f"Would insert CRITICAL WARNING before first ## section")
        print(f"Would enhance Step 3 with numbered checklist")
        print(f"Would add Failure Mode Handling before ## Validation")
        print(f"Would add Self-Verification Checkpoints at end")
        print()
        return True

    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = agent_file.with_suffix(f".md.bak-{timestamp}")
    shutil.copy2(agent_file, backup_path)

    if verbose:
        print(f"📦 {agent}.md: Backup created at {backup_path.name}", file=sys.stderr)

    # Write new content
    agent_file.write_text(new_content, encoding='utf-8')

    if verbose:
        print(f"✅ {agent}.md: Updated with 5-layer defense", file=sys.stderr)

    return True


def rollback_agent(agent: str) -> bool:
    """Rollback agent to most recent backup."""
    agent_file = AGENTS_DIR / f"{agent}.md"

    # Find most recent backup
    backups = list(AGENTS_DIR.glob(f"{agent}.md.bak-*"))

    if not backups:
        print(f"❌ {agent}.md: No backups found", file=sys.stderr)
        return False

    latest_backup = max(backups, key=lambda p: p.stat().st_mtime)

    shutil.copy2(latest_backup, agent_file)
    print(f"✅ {agent}.md: Rolled back from {latest_backup.name}", file=sys.stderr)

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Add 5-layer Write tool defense to all 8 travel planning agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without modifying files
  python3 scripts/update-agent-prompts.py --dry-run

  # Execute updates with detailed output
  python3 scripts/update-agent-prompts.py --verbose

  # Rollback to previous version
  python3 scripts/update-agent-prompts.py --rollback
        """
    )

    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--rollback", action="store_true", help="Rollback all agents to most recent backup")
    parser.add_argument("--agent", help="Update single agent (default: all 8 agents)")

    args = parser.parse_args()

    agents_to_update = [args.agent] if args.agent else AGENTS

    if args.rollback:
        print(f"🔄 Rolling back {len(agents_to_update)} agents...", file=sys.stderr)
        success_count = sum(rollback_agent(agent) for agent in agents_to_update)
        print(f"\n✅ Rolled back {success_count}/{len(agents_to_update)} agents", file=sys.stderr)
        sys.exit(0 if success_count == len(agents_to_update) else 1)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n", file=sys.stderr)

    print(f"🔧 Updating {len(agents_to_update)} agents with 5-layer defense...", file=sys.stderr)

    success_count = 0
    for agent in agents_to_update:
        if update_agent_file(agent, dry_run=args.dry_run, verbose=args.verbose):
            success_count += 1

    print(f"\n✅ Updated {success_count}/{len(agents_to_update)} agents", file=sys.stderr)

    if not args.dry_run and success_count > 0:
        print(f"\n📋 Next steps:", file=sys.stderr)
        print(f"  1. Review changes: git diff .claude/agents/", file=sys.stderr)
        print(f"  2. Run verification: python3 scripts/verify-tool-restrictions.py", file=sys.stderr)
        print(f"  3. Commit changes if satisfied", file=sys.stderr)

    sys.exit(0 if success_count == len(agents_to_update) else 1)


if __name__ == "__main__":
    main()
