# hooks

*Last updated: 2026-05-06T11:28:51Z*
**Total entries**: 54
**Convention**: kebab

## Tree
```
hooks/
├── lib/
│   └── `todo_canonical.py` - Shared canonical todo validation utilities
├── `audit-slashcommand.sh` - audit-slashcommand.sh
├── `auto-commit.sh` - ============================================================================
├── `checkpoint.sh` - checkpoint.sh - Manual checkpoint command
├── `ensure-git-repo.sh` - ============================================================================
├── `fswatch-manager.sh` - fswatch-manager.sh - Manage git-fswatch instances
├── `git-fswatch.sh` - git-fswatch.sh - Comprehensive Git file watcher using fswatch
├── `hook-todo-injection.py` - Global PreToolUse Hook: Todo Injection for Slash Commands
├── `install-auto-sync.sh` - install-auto-sync.sh - Quick installer for auto-sync features
├── `install-git-hooks.sh` - install-git-hooks.sh - Install pre-commit hooks into git repositories
├── `install-protection-all.sh` - install-protection-all.sh - Automatically install protection for all git repos
├── `install.sh` - ============================================================================
├── `post-commit-warn.sh` - post-commit-warn.sh - Warn about untracked files after commit
├── `post_tool_use.sh` - PostToolUse Hook - Code quality hints after file modifications
├── `posttool-command-frontmatter-validate.py` - PostToolUse Hook: Validate .claude/commands/*.md frontmatter structure
├── `posttool-doc-sync.py` - PostToolUse Hook: Auto-sync INDEX.md and CLAUDE.md when structural files change
├── `posttool-git-checkpoint.sh` - posttool-git-checkpoint.sh — refs/checkpoints/<branch> auto-checkpoint.
├── `posttool-git-warn.sh` - post-commit-warn.sh - Warn about untracked files after commit
├── `posttool-overnight-file-check.py` - PostToolUse:Agent Hook: Verify overnight subagent output files exist
├── `posttool-overnight-loop.py` - PostToolUse:TodoWrite Hook: Overnight Loop Detection
├── `posttool-subagent-track.py` - PostToolUse:Agent Hook: Track subagent invocations in workflow bookmark
├── `posttool-todo-count.py` - PostToolUse Hook: Enforce canonical todo count immediately after TodoWrite
├── `posttool-todo-sequence.py` - PostToolUse Hook: Enforce one-step-at-a-time progression in workflow checklists
├── `posttool-todo-tracker.py` - PostToolUse Hook: Output checklist progress after every TodoWrite call
├── `pre-commit-check.sh` - pre-commit-check.sh - Detect untracked files before commit
├── `pre-save-validation.sh` - Pre-Save Validation Hook - Verify modification log entry exists
├── `pre_slashcommand_validate.sh` - pre_slashcommand_validate.sh
├── `pre_tool_use_safety.sh` - PreToolUse Safety Hook - Warn before dangerous operations
├── `pretool-bash-safety.sh` - PreToolUse Safety Hook - Warn or block before dangerous operations
├── `pretool-block-enterworktree.sh` - PreToolUse hook: Block EnterWorktree tool
├── `pretool-block-production-files.sh` - PreToolUse hook: Block Write/Edit to production paths from dev environment.
├── `pretool-block-production.sh` - PreToolUse hook: Block Playwright navigation to production URLs
├── `pretool-docker-build-guard.sh` - Hook: PreToolUse:Bash
├── `pretool-overnight-hook-guard.py` - PreToolUse Hook: Overnight session file modification guard
├── `pretool-quality-gate.py` - PreToolUse Hook: Quality gate for Write/Edit operations
├── `pretool-subagent-enforce.py` - PreToolUse Hook: Enforce subagent invocation at designated workflow steps
├── `pretool-todo-validate.py` - PreToolUse Hook: Validate TodoWrite input BEFORE execution
├── `pretool-validate-data-write.py` - Implements spec-20260506-092951 §5.1, §5.3, §5.7. Reads JSON hook payload
├── `pretool-workflow-gate.py` - PreToolUse Hook: Require TodoWrite/TodoRead acknowledgment before other tools
├── `pretool-worktree-guard.sh` - PreToolUse hook: Detect stale agent worktrees before ANY tool call
├── `prompt-workflow.py` - UserPromptSubmit Hook: Checklist Injection for Slash Commands
├── `protection-status.sh` - protection-status.sh - Display protection status for all git repositories
├── `pull.sh` - pull.sh - Executable version of /pull command
├── `push.sh` - push.sh - Executable version of /push command
├── `session-git-init.sh` - ============================================================================
├── `session-info.sh` - s-info.sh — SessionStart: display environment info + tool quick reference
├── `session_start.sh` - SessionStart Hook - Display working environment info
├── `smart-checkpoint.sh` - smart-checkpoint.sh - Intelligent auto-checkpoint system
├── `start-fswatch-all.sh` - start-fswatch-all.sh - Start fswatch monitoring for all important repositories
├── `stop-git-commit.sh` - stop-git-commit.sh — Stop-hook: snapshot to refs/checkpoints/<branch> only.
├── `stop-overnight-timelock.py` - Stop Hook: Block conversation termination until overnight end-time
├── `stop-workflow-enforce.py` - Stop Hook: Enforce workflow structural integrity before allowing Claude to stop
└── `userprompt-doc-sync-check.py` - UserPromptSubmit Hook: Periodic file deletion detection for doc-sync
```

---
*Auto-generated by doc-sync hook.*