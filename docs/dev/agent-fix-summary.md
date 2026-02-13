# Agent Documentation Fix - Save.py Syntax Correction

**Date**: 2026-02-13 16:00:00
**Task**: Fix incorrect save.py syntax in all 8 agent documentation files

---

## Problem

All 8 agent files (.claude/agents/*.md) contained **incorrect Python function call syntax** in bash code blocks:

```bash
save.py(
  file_path="data/{destination-slug}/timeline.json",
  content=<complete_json_string>
)
```

This syntax confused agents into thinking they should call a `save.py()` Python function, which doesn't exist. Instead, agents would either:
- Fall back to using the Write tool (causing data overwrites)
- Fail with errors
- Generate malformed commands

---

## Root Cause

**Commit**: b057f26 - checkpoint: Auto-save at 2026-02-12 18:58:20

Someone changed from `Write()` to `save.py()` but kept the Write tool's **function call syntax** instead of using proper **bash CLI syntax**.

---

## Solution

Replaced all 8 occurrences with proper bash CLI syntax showing TWO options:

**Option 1: Save from temp file**
```bash
cat > /tmp/{agent}_update.json << 'EOF'
{
  "agent": "{agent}",
  "status": "complete",
  "data": {...}
}
