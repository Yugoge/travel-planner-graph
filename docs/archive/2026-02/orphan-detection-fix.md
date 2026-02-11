# Orphan Detection Logic Fix

**Date**: 2026-02-11
**Request**: User feedback from clean-20260211-152201

## Issue

The Cleanliness Inspector's orphan script detection had a design flaw:
- It only checked direct references in `.claude/agents/` and `.claude/commands/`
- It did NOT check `scripts/INDEX.md`, `docs/`, or git history
- However, per project requirements, scripts with ONLY INDEX/docs history references SHOULD be marked as orphans
- They need to be directly invoked by commands/agents/scripts to be considered "functional"

## Fix Applied

Modified `/root/.claude/scripts/detect-orphan-scripts.sh`:

### Change 1: Added explicit comment (line ~148)
```bash
# DO NOT check INDEX.md or docs/ references
# Scripts with only INDEX/docs references are still orphans
# They need to be directly invoked by commands/agents/scripts
```

### Change 2: Modified `has_report()` function (line ~168)
```bash
# Function to check for corresponding report
# NOTE: Has_report does NOT affect orphan status
# Scripts with only docs/reports references are STILL orphans
has_report() {
    # Always return false - docs/reports don't count as functional references
    echo "false"
}
```

## Result

After fix:
- **Before**: 0 orphan scripts detected
- **After**: 54 orphan scripts detected

These include scripts that were previously hidden due to INDEX.md or docs/reports references:
- `scripts/fix-attractions-data.py`
- `scripts/optimize-route.py`
- `scripts/add-notes-local.py`
- And 51 others

## Definition

**Orphan Script** = A script that is NOT directly invoked by:
- Commands in `.claude/commands/`
- Agents in `.claude/agents/`
- Other scripts (via import, subprocess, or shell invocation)

Having references in `scripts/INDEX.md`, `docs/`, or git commit history does NOT make a script non-orphan.

---

**Impact**: This fix applies globally to all projects using `/clean` workflow.
