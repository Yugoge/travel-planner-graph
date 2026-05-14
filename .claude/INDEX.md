# .claude

*Last updated: 2026-05-14T18:29:16Z*
**Total entries**: 354
**Convention**: kebab

## Tree
```
.claude/
├── agents/
│   ├── `accommodation.md` - Research hotels and lodging options for each location
│   ├── `attractions.md` - Research sightseeing and activities based on user requirements
│   ├── `budget.md` - Calculate daily budget breakdown and detect overages
│   ├── `cafe.md` - Research coffee shops, teahouses, and rest/relaxation spots for each day
│   ├── `entertainment.md` - Research shows, nightlife, and entertainment options
│   ├── `meals.md` - Research breakfast, lunch, and dinner options for each day
│   ├── `shopping.md` - Research shopping destinations and retail experiences
│   ├── `timeline.md` - Create timeline dictionary and detect scheduling conflicts
│   └── `transportation.md` - Research inter-city transportation options for days with location changes
├── commands/
│   ├── gaode-maps/
│   │   ├── examples/
│   │   ├── tools/
│   │   ├── `consolidation-report.md` - Gaode Maps Documentation Consolidation Report
│   │   └── `readme.md` - gaode-maps
│   ├── scripts/
│   │   ├── airbnb/
│   │   ├── duffel-flights/
│   │   ├── gaode-maps/
│   │   ├── google-maps/
│   │   ├── openmeteo-weather/
│   │   ├── rednote/
│   │   └── shared/
│   ├── `gaode-maps.md` - Gaode Maps integration for route planning, POI search, and geocoding
│   ├── `google-maps.md` - Google Maps integration for places, routing, geocoding, distance matrix,
│   ├── `plan.md` - Multi-agent travel planning with specialized subagents and interactive
│   ├── `poi-classification-rules.md` - Decision tree and rules for POI classification across domains
│   ├── `rednote.md` - RedNote (小红书/Xiaohongshu) integration for searching Chinese UGC travel
│   └── `review.md` - Multi-day iterative review command with incremental workflow
├── dev-registry/
│   ├── dev-20260505-060527/
│   │   ├── `architect.json` - json config
│   │   ├── `ba.json` - json config
│   │   ├── `cleaner.json` - json config
│   │   ├── `cleanliness-inspector.json` - json config
│   │   ├── `dev.json` - json config
│   │   ├── `git-edge-case-analyst.json` - json config
│   │   ├── `pm.json` - json config
│   │   ├── `product-owner.json` - json config
│   │   ├── `prompt-inspector.json` - json config
│   │   ├── `qa.json` - json config
│   │   ├── `rule-inspector.json` - json config
│   │   ├── `style-inspector.json` - json config
│   │   ├── `test-executor.json` - json config
│   │   ├── `test-validator.json` - json config
│   │   ├── `ui-specialist.json` - json config
│   │   └── `user.json` - json config
│   ├── dev-20260505-061047/
│   ├── dev-20260505-123425/
│   │   ├── `architect.json` - json config
│   │   ├── `ba.json` - json config
│   │   ├── `cleaner.json` - json config
│   │   ├── `cleanliness-inspector.json` - json config
│   │   ├── `dev.json` - json config
│   │   ├── `git-edge-case-analyst.json` - json config
│   │   ├── `pm.json` - json config
│   │   ├── `product-owner.json` - json config
│   │   ├── `prompt-inspector.json` - json config
│   │   ├── `qa.json` - json config
│   │   ├── `rule-inspector.json` - json config
│   │   ├── `style-inspector.json` - json config
│   │   ├── `test-executor.json` - json config
│   │   ├── `test-validator.json` - json config
│   │   ├── `ui-specialist.json` - json config
│   │   └── `user.json` - json config
│   ├── dev-20260505-124619/
│   ├── dev-20260505-174743/
│   │   ├── `architect.json` - json config
│   │   ├── `ba.json` - json config
│   │   ├── `cleaner.json` - json config
│   │   ├── `cleanliness-inspector.json` - json config
│   │   ├── `dev.json` - json config
│   │   ├── `git-edge-case-analyst.json` - json config
│   │   ├── `pm.json` - json config
│   │   ├── `product-owner.json` - json config
│   │   ├── `prompt-inspector.json` - json config
│   │   ├── `qa.json` - json config
│   │   ├── `rule-inspector.json` - json config
│   │   ├── `style-inspector.json` - json config
│   │   ├── `test-executor.json` - json config
│   │   ├── `test-validator.json` - json config
│   │   ├── `ui-specialist.json` - json config
│   │   └── `user.json` - json config
│   ├── dev-20260505-175102/
│   │   └── `dev.json` - json config
│   ├── dev-20260505-230534/
│   │   ├── `architect.json` - json config
│   │   ├── `ba.json` - json config
│   │   ├── `cleaner.json` - json config
│   │   ├── `cleanliness-inspector.json` - json config
│   │   ├── `dev.json` - json config
│   │   ├── `git-edge-case-analyst.json` - json config
│   │   ├── `pm.json` - json config
│   │   ├── `product-owner.json` - json config
│   │   ├── `prompt-inspector.json` - json config
│   │   ├── `qa.json` - json config
│   │   ├── `rule-inspector.json` - json config
│   │   ├── `style-inspector.json` - json config
│   │   ├── `test-executor.json` - json config
│   │   ├── `test-validator.json` - json config
│   │   ├── `ui-specialist.json` - json config
│   │   └── `user.json` - json config
│   ├── dev-20260506-104100/
│   │   ├── `architect.json` - json config
│   │   ├── `ba.json` - json config
│   │   ├── `cleaner.json` - json config
│   │   ├── `cleanliness-inspector.json` - json config
│   │   ├── `dev.json` - json config
│   │   ├── `git-edge-case-analyst.json` - json config
│   │   ├── `pm.json` - json config
│   │   ├── `product-owner.json` - json config
│   │   ├── `prompt-inspector.json` - json config
│   │   ├── `qa.json` - json config
│   │   ├── `rule-inspector.json` - json config
│   │   ├── `style-inspector.json` - json config
│   │   ├── `test-executor.json` - json config
│   │   ├── `test-validator.json` - json config
│   │   ├── `ui-specialist.json` - json config
│   │   └── `user.json` - json config
│   ├── dev-20260506-141814/
│   │   ├── `architect.json` - json config
│   │   ├── `ba.json` - json config
│   │   ├── `cleaner.json` - json config
│   │   ├── `cleanliness-inspector.json` - json config
│   │   ├── `dev.json` - json config
│   │   ├── `git-edge-case-analyst.json` - json config
│   │   ├── `pm.json` - json config
│   │   ├── `product-owner.json` - json config
│   │   ├── `prompt-inspector.json` - json config
│   │   ├── `qa.json` - json config
│   │   ├── `rule-inspector.json` - json config
│   │   ├── `style-inspector.json` - json config
│   │   ├── `test-executor.json` - json config
│   │   ├── `test-validator.json` - json config
│   │   ├── `ui-specialist.json` - json config
│   │   └── `user.json` - json config
│   ├── dev-20260513-090000/
│   │   ├── `architect.json` - json config
│   │   ├── `ba.json` - json config
│   │   ├── `bypass-quality-gate.flag` - flag file
│   │   ├── `cleaner.json` - json config
│   │   ├── `cleanliness-inspector.json` - json config
│   │   ├── `dev.json` - json config
│   │   ├── `git-edge-case-analyst.json` - json config
│   │   ├── `pm.json` - json config
│   │   ├── `product-owner.json` - json config
│   │   ├── `prompt-inspector.json` - json config
│   │   ├── `qa.json` - json config
│   │   ├── `rule-inspector.json` - json config
│   │   ├── `style-inspector.json` - json config
│   │   ├── `test-executor.json` - json config
│   │   ├── `test-validator.json` - json config
│   │   ├── `ui-specialist.json` - json config
│   │   └── `user.json` - json config
│   ├── dev-20260514-103616/
│   │   └── `user.json` - json config
│   ├── `agent-index.json` - json config
│   └── `agent-index.json.lock` - lock file
├── hooks/
│   ├── lib/
│   │   ├── `gaode_policy.py` - Self-contained copy of gaode-related functions from
│   │   ├── `heredoc_extract.py` - Self-contained copy of extract_heredoc_bodies (and supporting parsers)
│   │   └── `todo_canonical.py` - Shared canonical todo validation utilities
│   ├── `audit-slashcommand.sh` - audit-slashcommand.sh
│   ├── `auto-commit.sh` - ============================================================================
│   ├── `checkpoint.sh` - checkpoint.sh - Manual checkpoint command
│   ├── `ensure-git-repo.sh` - ============================================================================
│   ├── `fswatch-manager.sh` - fswatch-manager.sh - Manage git-fswatch instances
│   ├── `git-fswatch.sh` - git-fswatch.sh - Comprehensive Git file watcher using fswatch
│   ├── `hook-todo-injection.py` - Global PreToolUse Hook: Todo Injection for Slash Commands
│   ├── `install-auto-sync.sh` - install-auto-sync.sh - Quick installer for auto-sync features
│   ├── `install-git-hooks.sh` - install-git-hooks.sh - Install pre-commit hooks into git repositories
│   ├── `install-protection-all.sh` - install-protection-all.sh - Automatically install protection for all git repos
│   ├── `install.sh` - ============================================================================
│   ├── `post-commit-warn.sh` - post-commit-warn.sh - Warn about untracked files after commit
│   ├── `post_tool_use.sh` - PostToolUse Hook - Code quality hints after file modifications
│   ├── `posttool-command-frontmatter-validate.py` - PostToolUse Hook: Validate .claude/commands/*.md frontmatter structure
│   ├── `posttool-doc-sync.py` - PostToolUse Hook: Auto-sync INDEX.md and CLAUDE.md when structural files change
│   ├── `posttool-git-checkpoint.sh` - posttool-git-checkpoint.sh — refs/checkpoints/<branch> auto-checkpoint.
│   ├── `posttool-git-warn.sh` - post-commit-warn.sh - Warn about untracked files after commit
│   ├── `posttool-overnight-file-check.py` - PostToolUse:Agent Hook: Verify overnight subagent output files exist
│   ├── `posttool-overnight-loop.py` - PostToolUse:TodoWrite Hook: Overnight Loop Detection
│   ├── `posttool-subagent-track.py` - PostToolUse:Agent Hook: Track subagent invocations in workflow bookmark
│   ├── `posttool-todo-count.py` - PostToolUse Hook: Enforce canonical todo count immediately after TodoWrite
│   ├── `posttool-todo-sequence.py` - PostToolUse Hook: Enforce one-step-at-a-time progression in workflow checklists
│   ├── `posttool-todo-tracker.py` - PostToolUse Hook: Output checklist progress after every TodoWrite call
│   ├── `pre-commit-check.sh` - pre-commit-check.sh - Detect untracked files before commit
│   ├── `pre-save-validation.sh` - Pre-Save Validation Hook - Verify modification log entry exists
│   ├── `pre_slashcommand_validate.sh` - pre_slashcommand_validate.sh
│   ├── `pre_tool_use_safety.sh` - PreToolUse Safety Hook - Warn before dangerous operations
│   ├── `pretool-bash-safety.sh` - PreToolUse Safety Hook - Warn or block before dangerous operations
│   ├── `pretool-block-enterworktree.sh` - PreToolUse hook: Block EnterWorktree tool
│   ├── `pretool-block-production-files.sh` - PreToolUse hook: Block Write/Edit to production paths from dev environment.
│   ├── `pretool-block-production.sh` - PreToolUse hook: Block Playwright navigation to production URLs
│   ├── `pretool-docker-build-guard.sh` - Hook: PreToolUse:Bash
│   ├── `pretool-gaode-policy.py` - Standalone hook reading
│   ├── `pretool-overnight-hook-guard.py` - PreToolUse Hook: Overnight session file modification guard
│   ├── `pretool-quality-gate.py` - PreToolUse Hook: Quality gate for Write/Edit operations
│   ├── `pretool-subagent-enforce.py` - PreToolUse Hook: Enforce subagent invocation at designated workflow steps
│   ├── `pretool-todo-validate.py` - PreToolUse Hook: Validate TodoWrite input BEFORE execution
│   ├── `pretool-validate-data-write.py` - Implements spec-20260506-092951 §5.1, §5.3, §5.7. Reads JSON hook payload
│   ├── `pretool-workflow-gate.py` - PreToolUse Hook: Require TodoWrite/TodoRead acknowledgment before other tools
│   ├── `pretool-worktree-guard.sh` - PreToolUse hook: Detect stale agent worktrees before ANY tool call
│   ├── `prompt-workflow.py` - UserPromptSubmit Hook: Checklist Injection for Slash Commands
│   ├── `protection-status.sh` - protection-status.sh - Display protection status for all git repositories
│   ├── `pull.sh` - pull.sh - Executable version of /pull command
│   ├── `push.sh` - push.sh - Executable version of /push command
│   ├── `session-git-init.sh` - ============================================================================
│   ├── `session-info.sh` - s-info.sh — SessionStart: display environment info + tool quick reference
│   ├── `session_start.sh` - SessionStart Hook - Display working environment info
│   ├── `smart-checkpoint.sh` - smart-checkpoint.sh - Intelligent auto-checkpoint system
│   ├── `start-fswatch-all.sh` - start-fswatch-all.sh - Start fswatch monitoring for all important repositories
│   ├── `stop-git-commit.sh` - stop-git-commit.sh — Stop-hook: snapshot to refs/checkpoints/<branch> only.
│   ├── `stop-overnight-timelock.py` - Stop Hook: Block conversation termination until overnight end-time
│   ├── `stop-workflow-enforce.py` - Stop Hook: Enforce workflow structural integrity before allowing Claude to stop
│   └── `userprompt-doc-sync-check.py` - UserPromptSubmit Hook: Periodic file deletion detection for doc-sync
├── policies/
│   └── `gaode-policy.json` - json config
├── skills/
│   ├── gaode-maps/
│   │   ├── examples/
│   │   ├── scripts/
│   │   ├── tools/
│   │   ├── `skill.md` - |
│   │   └── `test-report-20260130.json` - json config
│   └── google-maps/
│       ├── examples/
│       ├── scripts/
│       ├── tools/
│       └── `skill.md` - Google Maps integration for places, routing, geocoding, distance matrix, elevation, and place details
├── specs/
│   ├── spec-20260505-221501/
│   │   ├── `cp-state-architect-2.json` - json config
│   │   ├── `cp-state-architect-2.json.lock` - lock file
│   │   ├── `cp-state-architect.json` - json config
│   │   ├── `cp-state-architect.json.lock` - lock file
│   │   ├── `cp-state-ba-2.json` - json config
│   │   ├── `cp-state-ba-2.json.lock` - lock file
│   │   ├── `cp-state-ba.json` - json config
│   │   ├── `cp-state-ba.json.lock` - lock file
│   │   ├── `cp-state-dev-2.json` - json config
│   │   ├── `cp-state-dev-2.json.lock` - lock file
│   │   ├── `cp-state-dev-3.json` - json config
│   │   ├── `cp-state-dev-3.json.lock` - lock file
│   │   ├── `cp-state-dev-4.json` - json config
│   │   ├── `cp-state-dev-4.json.lock` - lock file
│   │   ├── `cp-state-dev-5.json` - json config
│   │   ├── `cp-state-dev-5.json.lock` - lock file
│   │   ├── `cp-state-dev-6.json` - json config
│   │   ├── `cp-state-dev-6.json.lock` - lock file
│   │   ├── `cp-state-dev-7.json` - json config
│   │   ├── `cp-state-dev-7.json.lock` - lock file
│   │   ├── `cp-state-dev.json` - json config
│   │   ├── `cp-state-dev.json.lock` - lock file
│   │   ├── `cp-state-qa-2.json` - json config
│   │   ├── `cp-state-qa-2.json.lock` - lock file
│   │   ├── `cp-state-qa.json` - json config
│   │   └── `cp-state-qa.json.lock` - lock file
│   ├── spec-20260506-092951/
│   │   ├── `cp-state-ba-2.json` - json config
│   │   ├── `cp-state-ba-2.json.lock` - lock file
│   │   ├── `cp-state-ba.json` - json config
│   │   ├── `cp-state-ba.json.lock` - lock file
│   │   ├── `cp-state-dev-2.json` - json config
│   │   ├── `cp-state-dev-2.json.lock` - lock file
│   │   ├── `cp-state-dev.json` - json config
│   │   ├── `cp-state-dev.json.lock` - lock file
│   │   ├── `cp-state-qa-2.json` - json config
│   │   ├── `cp-state-qa-2.json.lock` - lock file
│   │   ├── `cp-state-qa.json` - json config
│   │   └── `cp-state-qa.json.lock` - lock file
│   ├── spec-20260508-221237/
│   │   ├── `cp-state-ba-2.json` - json config
│   │   ├── `cp-state-ba-2.json.lock` - lock file
│   │   ├── `cp-state-ba.json` - json config
│   │   ├── `cp-state-ba.json.lock` - lock file
│   │   ├── `cp-state-dev-2.json` - json config
│   │   ├── `cp-state-dev-2.json.lock` - lock file
│   │   ├── `cp-state-dev-3.json` - json config
│   │   ├── `cp-state-dev-3.json.lock` - lock file
│   │   ├── `cp-state-dev-4.json` - json config
│   │   ├── `cp-state-dev-4.json.lock` - lock file
│   │   ├── `cp-state-dev-5.json` - json config
│   │   ├── `cp-state-dev-5.json.lock` - lock file
│   │   ├── `cp-state-dev-6.json` - json config
│   │   ├── `cp-state-dev-6.json.lock` - lock file
│   │   ├── `cp-state-dev-7.json` - json config
│   │   ├── `cp-state-dev-7.json.lock` - lock file
│   │   ├── `cp-state-dev-8.json` - json config
│   │   ├── `cp-state-dev-8.json.lock` - lock file
│   │   ├── `cp-state-dev-9.json` - json config
│   │   ├── `cp-state-dev-9.json.lock` - lock file
│   │   ├── `cp-state-dev.json` - json config
│   │   ├── `cp-state-dev.json.lock` - lock file
│   │   ├── `cp-state-qa-2.json` - json config
│   │   ├── `cp-state-qa-2.json.lock` - lock file
│   │   ├── `cp-state-qa-3.json` - json config
│   │   ├── `cp-state-qa-3.json.lock` - lock file
│   │   ├── `cp-state-qa.json` - json config
│   │   ├── `cp-state-qa.json.lock` - lock file
│   │   ├── `cp-state-ui-specialist-2.json` - json config
│   │   ├── `cp-state-ui-specialist-2.json.lock` - lock file
│   │   ├── `cp-state-ui-specialist-3.json` - json config
│   │   ├── `cp-state-ui-specialist-3.json.lock` - lock file
│   │   ├── `cp-state-ui-specialist.json` - json config
│   │   └── `cp-state-ui-specialist.json.lock` - lock file
│   └── spec-20260513-085358/
│       ├── `cp-state-architect.json` - json config
│       ├── `cp-state-architect.json.lock` - lock file
│       ├── `cp-state-ba-2.json` - json config
│       ├── `cp-state-ba-2.json.lock` - lock file
│       ├── `cp-state-ba.json` - json config
│       ├── `cp-state-ba.json.lock` - lock file
│       ├── `cp-state-dev-2.json` - json config
│       ├── `cp-state-dev-2.json.lock` - lock file
│       ├── `cp-state-dev-3.json` - json config
│       ├── `cp-state-dev-3.json.lock` - lock file
│       ├── `cp-state-dev-4.json` - json config
│       ├── `cp-state-dev-4.json.lock` - lock file
│       ├── `cp-state-dev-5.json` - json config
│       ├── `cp-state-dev-5.json.lock` - lock file
│       ├── `cp-state-dev.json` - json config
│       ├── `cp-state-dev.json.lock` - lock file
│       ├── `cp-state-qa-2.json` - json config
│       ├── `cp-state-qa-2.json.lock` - lock file
│       ├── `cp-state-qa.json` - json config
│       └── `cp-state-qa.json.lock` - lock file
├── worktrees/
│   └── overnight-20260412-c6ec78c9/
│       ├── config/
│       ├── data/
│       ├── docs/
│       ├── infra/
│       ├── output/
│       ├── schemas/
│       ├── scripts/
│       ├── tests/
│       ├── `CLAUDE.md` - CLAUDE.md
│       ├── `index.html` - html file
│       ├── `package-lock.json` - json config
│       ├── `package.json` - json config
│       ├── `requirements.txt` - txt file
│       ├── `travel-life-ai-app.png` - png file
│       └── `xiaohongshu-search.png` - png file
├── `index.md` - .claude Index
├── `PROJECT-DOCS.md` - Travel Planner Project Documentation
├── `settings.json` - json config
├── `workflow-0a534494-870e-4c16-989e-e11e07d688c0.json` - json config
├── `workflow-0e35f08c-7f82-47ec-ba8a-1b00e087405a.json` - json config
├── `workflow-32d47198-5235-445b-97f7-a627757b50a8.json` - json config
├── `workflow-c59044cd-0bea-4cf9-9b55-61a7bb1d9f65.json` - json config
├── `workflow-d3bf2777-cd14-4492-b890-4e34af2bc49f.json` - json config
└── `workflow-dacbe96c-62e6-4a28-962c-626a6816a54b.json` - json config
```

---
*Auto-generated by doc-sync hook.*