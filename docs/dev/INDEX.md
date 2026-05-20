# dev

*Last updated: 2026-05-20T20:32:42Z*
**Total entries**: 422
**Convention**: kebab

## Tree
```
dev/
├── overnight/
│   └── c6ec78c9-d0c0-4f25-a13b-34a83ae12d49/
├── playwright-judge5-output/
│   └── screenshots/
├── playwright-screenshots/
├── scratch-20260509-114002/
│   ├── `architect-redev-findings.md` - Architect findings — /redev cycle for spec-20260508-221237 M1
│   └── `specialist-findings.md` - Specialist Consultation Findings — spec-20260508-221237
├── screenshots/
│   └── dev-20260505-123425/
├── specs/
│   ├── spec-20260505-221501/
│   │   ├── views/
│   │   └── `ba-report-init.json` - json config
│   ├── spec-20260506-092951/
│   │   └── views/
│   ├── spec-20260508-221237/
│   │   ├── views/
│   │   └── `M2-contract.md` - M2 Contract — spec-20260508-221237
│   ├── spec-20260513-085358/
│   │   └── views/
│   ├── `spec-20260412-141227.md` - Spec: Xiaohongshu (小红书) Cloudflare Worker Reverse Proxy
│   ├── `spec-20260416-172720.md` - Spec: Fix silent data loss bug in POI agents — merge_agent_days replaces entire day object instead of merging at slot level
│   ├── `spec-20260416-192200.md` - Spec: Unify all agent save behavior — slot-level merge as default, delete --merge-days
│   ├── `spec-20260505-221501.md` - Spec: Travel-planner harness 升级 — Codex 共识版后验方案
│   ├── `spec-20260506-092951.md` - Spec: Travel-planner harness root-cause hardening — block schema/semantic violations at write-time, fix accumulated data bugs, kill HEAD pollution
│   ├── `spec-20260508-221237-redev1.md` - Redev Spec — spec-20260508-221237 Cycle 5 Close Blockers
│   ├── `spec-20260508-221237.md` - Spec: gaode-maps harness ban (non-geo agents) + options-first day planning flow
│   └── `spec-20260513-085358.md` - Spec: M2 prerequisite — systematic bugs surfaced during 2026-05-13 china-20260412-092624 review
├── `architect-rednote-mcp-archprop-2-3-closeout-20260505-124619.json` - json config
├── `architect-rednote-mcp-source-of-truth-20260505-061800.json` - json config
├── `architect-report-init.json` - json config
├── `ba-qa-report-20260415-210000.json` - json config
├── `ba-qa-report-20260416-172720.json` - json config
├── `ba-qa-report-20260417-001800.json` - json config
├── `ba-qa-report-20260418-153011.json` - json config
├── `ba-qa-report-20260505-060527.json` - json config
├── `ba-qa-report-20260505-061047.json` - json config
├── `ba-qa-report-20260505-123425.json` - json config
├── `ba-qa-report-20260505-124619.json` - json config
├── `ba-qa-report-20260505-174743.json` - json config
├── `ba-qa-report-20260505-175102.json` - json config
├── `ba-qa-report-20260505-231740-iter2.json` - json config
├── `ba-qa-report-20260505-231740.json` - json config
├── `ba-qa-report-20260506-081545-iter2.json` - json config
├── `ba-qa-report-20260506-081545.json` - json config
├── `ba-qa-report-20260506-104100.json` - json config
├── `ba-qa-report-20260506-141814.json` - json config
├── `ba-qa-report-20260509-114002-cycle3-r2.json` - json config
├── `ba-qa-report-20260509-114002-cycle3-r3.json` - json config
├── `ba-qa-report-20260509-114002-cycle3.json` - json config
├── `ba-qa-report-20260509-114002-r2.json` - json config
├── `ba-qa-report-20260509-114002.json` - json config
├── `ba-qa-report-20260513-090000-round2.json` - json config
├── `ba-qa-report-20260513-090000.json` - json config
├── `ba-qa-report-20260514-103616.json` - json config
├── `ba-qa-report-20260515-102340.json` - json config
├── `ba-qa-report-20260517-071910.json` - json config
├── `ba-qa-report-20260517-101502.json` - json config
├── `ba-qa-report-20260517-153318.json` - json config
├── `ba-spec-20260405-201500.md` - BA Specification: Fix 3 Critical Bugs in Travel Plan HTML Generator
├── `ba-spec-20260406-010001.md` - BA Specification: Fix check-budget-overage.py Multi-Currency Support
├── `ba-spec-20260406-010002.md` - BA Specification: Fix NameError 'days' in check_semantics
├── `ba-spec-20260406-010003.md` - BA Specification: Fix Gaode API Key Environment Variable Name in fetch-images-batch.py
├── `ba-spec-20260406-010004.md` - BA Specification: Fix City Cover Image Partial Matching
├── `ba-spec-20260406-010005.md` - BA Specification: Image Fetch Failure Visibility in generate-and-deploy Pipeline
├── `ba-spec-20260406-010006.md` - BA Specification: Fix check-budget-overage.py for Multi-Currency Support (Bug8 + Bug26 Combined)
├── `ba-spec-20260406-010007.md` - BA Specification: Fix deploy-travel-plans.sh Branch Detection
├── `ba-spec-20260406-020001.md` - BA Specification: Restructure Meal Alternatives to Nested Format
├── `ba-spec-20260406-020002.md` - BA Specification: Structured Brand Array in Shopping JSON
├── `ba-spec-20260406-020003.md` - BA Specification: Include Schema File Paths in Step 8 Agent Prompts
├── `ba-spec-20260406-020004.md` - BA Specification: Semantic Time Constraints for Timeline Agent
├── `ba-spec-20260406-020005.md` - BA Specification: Harden TimelineView Degenerate Entry Filtering and Optional Item Deduplication
├── `ba-spec-20260412-213000.md` - BA Specification: Fix City Covers, Meals Layout, and Shopping Images
├── `ba-spec-20260413-063000.md` - BA Specification: Fix Shopping Brand-Splitting Duplicate Image Bug
├── `ba-spec-20260413-064500.md` - BA Specification: Fix Duplicate POIs Across Categories and Broken Day 1 Timeline
├── `ba-spec-20260413-181500.md` - BA Specification: Horizontal Scroll Layout for Category Cards
├── `ba-spec-20260413-190000.md` - BA Specification: Fix sync-agent-data.py meal_types Detection Bug
├── `ba-spec-20260413-200500.md` - BA Specification: Hard-Blocking Time Conflict Gate in save.py
├── `ba-spec-20260415-010000.md` - BA Specification: Enforce timeline.json as Single Source of Truth for Scheduling
├── `ba-spec-20260415-210000.md` - BA Specification: Independent Cafe POI Type
├── `ba-spec-20260416-172720.md` - BA Specification: Fix silent data loss bug in POI agents — slot-level merge
├── `ba-spec-20260417-001800.md` - BA Specification: Unify all agent save behavior — slot-level merge as default, delete --merge-days
├── `ba-spec-20260418-153011.md` - BA Specification: Currency System Architecture Redesign
├── `ba-spec-codex-prompt-cycle3-revision.txt` - txt file
├── `ba-spec-codex-prompt-cycle3-revision3.txt` - txt file
├── `ba-spec-codex-prompt-dev-cycle3.txt` - txt file
├── `ba-spec-codex-response-cycle3-revision.txt` - txt file
├── `ba-spec-codex-response-cycle3-revision3.txt` - txt file
├── `cleanliness-inspector-report-20260505-061047.json` - json config
├── `cleanliness-inspector-report-20260505-123425.json` - json config
├── `cleanliness-inspector-report-20260505-124619.json` - json config
├── `cleanliness-inspector-report-20260505-175102.json` - json config
├── `cleanliness-inspector-report-20260505-231740.json` - json config
├── `cleanliness-inspector-report-20260506-081545.json` - json config
├── `cleanliness-inspector-report-20260506-141814.json` - json config
├── `cleanliness-inspector-report-20260509-114002.json` - json config
├── `cleanliness-inspector-report-20260513-090000.json` - json config
├── `cleanliness-inspector-report-20260514-103616.json` - json config
├── `cleanliness-inspector-report-20260514-200000.json` - json config
├── `cleanliness-inspector-report-20260514-200530.json` - json config
├── `cleanliness-inspector-report-20260515-102340.json` - json config
├── `cleanliness-inspector-report-20260517-071910.json` - json config
├── `cleanliness-inspector-report-20260517-101502.json` - json config
├── `cleanliness-inspector-report-20260517-211850.json` - json config
├── `cleanliness-inspector-report-20260518-101127.json` - json config
├── `cleanliness-inspector-report-20260519-161933.json` - json config
├── `close-report-20260505-061047.md` - Close Debate Report — 20260505-061047
├── `close-report-20260505-123425.md` - Close Report — 20260505-123425
├── `close-report-20260505-124619.md` - Close Report — 20260505-124619
├── `close-report-20260505-175102.md` - Close Report — 20260505-175102
├── `close-report-20260505-231740.md` - Close Report — Cycle 20260505-231740
├── `close-report-20260506-081545.md` - Close Report — Cycle 20260506-081545 (/redev iteration 2)
├── `close-report-20260506-141814.md` - Close Debate Report — task-id 20260506-141814
├── `close-report-20260509-114002.md` - Close Debate Report — 20260509-114002
├── `close-report-20260513-090000.md` - Close Debate Report
├── `close-report-20260514-103616.md` - Close Report — Task 20260514-103616
├── `close-report-20260514-200000.md` - Close Report — Task 20260514-200000
├── `close-report-20260514-200530.md` - Close Debate Report
├── `close-report-20260515-102340.md` - Close Report: task-id 20260515-102340
├── `close-report-20260517-071910.md` - Close Debate Report
├── `close-report-20260517-101502.md` - Close-Debate Report: 20260517-101502
├── `close-report-20260517-211850.md` - Close Debate Report — 20260517-211850
├── `close-report-20260518-101127.md` - Close Debate Report
├── `close-report-20260519-161933.md` - Close Debate Report
├── `commit-cycle-report-20260509-114002.json` - json config
├── `commit-manifest-20260509-114002-cycle4.json` - json config
├── `commit-manifest-20260509-114002.json` - json config
├── `completion-20260415-210000.md` - Development Completion Report — Cafe POI Type
├── `completion-20260416-172720.md` - Development Completion Report
├── `completion-20260417-001800.md` - Development Completion Report
├── `completion-20260505-060527.md` - Development Completion Report — 20260505-060527
├── `completion-20260505-061047.md` - Development Completion Report — 20260505-061047
├── `completion-20260505-123425.md` - Schema-Restoration Completion Report — 20260505-123425
├── `completion-20260505-124619.md` - Development Completion Report — 20260505-124619
├── `completion-20260505-174743.md` - 彻底清理 Completion — 20260505-174743
├── `completion-20260505-175102.md` - Development Completion Report — 20260505-175102
├── `completion-20260505-231740.md` - Development Completion Report — 20260505-231740
├── `completion-20260506-081545.md` - Development Completion Report — 20260506-081545 (/redev)
├── `completion-20260506-104100.md` - Development Completion Report — 20260506-104100
├── `completion-20260506-141814.md` - Development Completion Report — 20260506-141814 (/redev follow-on)
├── `completion-20260509-114002.md` - Development Completion Report — 20260509-114002
├── `completion-20260513-090000.md` - Development Completion Report — 20260513-090000
├── `completion-20260517-071910.md` - Completion Report: 20260517-071910
├── `completion-20260517-101502.md` - Completion Report: 20260517-101502
├── `completion-20260517-153318.md` - Completion Report — 20260517-153318
├── `completion-20260517-172103.md` - Completion Report: Photo Rendering in Trip Editor
├── `completion-20260517-211850.md` - Completion Report — 20260517-211850
├── `completion-20260518-101127.md` - Completion Report — 20260518-101127
├── `completion-20260519-161933.md` - Completion Report — task_id 20260519-161933
├── `context-20260320-213000.json` - json config
├── `context-20260321-155000.json` - json config
├── `context-20260405-201500.json` - json config
├── `context-20260406-010001.json` - json config
├── `context-20260406-010002.json` - json config
├── `context-20260406-010003.json` - json config
├── `context-20260406-010004.json` - json config
├── `context-20260406-010005.json` - json config
├── `context-20260406-010006.json` - json config
├── `context-20260406-010007.json` - json config
├── `context-20260406-020001.json` - json config
├── `context-20260406-020002.json` - json config
├── `context-20260406-020003.json` - json config
├── `context-20260406-020004.json` - json config
├── `context-20260406-020005.json` - json config
├── `context-20260413-063000.json` - json config
├── `context-20260413-064500.json` - json config
├── `context-20260413-181500.json` - json config
├── `context-20260413-190000.json` - json config
├── `context-20260413-200500.json` - json config
├── `context-20260415-010000.json` - json config
├── `context-20260415-210000.json` - json config
├── `context-20260416-172720.json` - json config
├── `context-20260417-001800.json` - json config
├── `context-20260418-153011.json` - json config
├── `context-20260505-060527.json` - json config
├── `context-20260505-061047.json` - json config
├── `context-20260505-123425.json` - json config
├── `context-20260505-124619.json` - json config
├── `context-20260505-174743.json` - json config
├── `context-20260505-175102.json` - json config
├── `context-20260505-231740.json` - json config
├── `context-20260506-081545.json` - json config
├── `context-20260506-104100.json` - json config
├── `context-20260506-141814.json` - json config
├── `context-20260509-114002.json` - json config
├── `context-20260513-090000.json` - json config
├── `context-20260514-103616.json` - json config
├── `context-20260514-200000.json` - json config
├── `context-20260514-200530.json` - json config
├── `context-20260515-102340.json` - json config
├── `context-20260517-071910.json` - json config
├── `context-20260517-101502.json` - json config
├── `context-20260517-153318.json` - json config
├── `context-20260517-172103.json` - json config
├── `context-20260517-195000.json` - json config
├── `context-20260517-211506.json` - json config
├── `context-20260517-211850.json` - json config
├── `context-20260518-101127.json` - json config
├── `context-20260519-161933.json` - json config
├── `context-20260520-200804.json` - json config
├── `context-xhs-login-fix.md` - Context Document: XHS/RedNote Login Fix
├── `cycle-20260505-231740.md` - Cycle Artifact: 20260505-231740
├── `dev-report-20260320-213000.json` - json config
├── `dev-report-20260321-001000.json` - json config
├── `dev-report-20260321-155000.json` - json config
├── `dev-report-20260405-201500.json` - json config
├── `dev-report-20260406-010001.json` - json config
├── `dev-report-20260406-010002.json` - json config
├── `dev-report-20260406-010003.json` - json config
├── `dev-report-20260406-010004.json` - json config
├── `dev-report-20260406-010005.json` - json config
├── `dev-report-20260406-010007.json` - json config
├── `dev-report-20260406-020001.json` - json config
├── `dev-report-20260406-020002.json` - json config
├── `dev-report-20260406-020003.json` - json config
├── `dev-report-20260406-020004.json` - json config
├── `dev-report-20260406-020005.json` - json config
├── `dev-report-20260412-213000.json` - json config
├── `dev-report-20260413-063000.json` - json config
├── `dev-report-20260413-064500.json` - json config
├── `dev-report-20260413-070000.json` - json config
├── `dev-report-20260413-181500.json` - json config
├── `dev-report-20260413-cleanup.json` - json config
├── `dev-report-20260415-010000-iter2.json` - json config
├── `dev-report-20260415-010000.json` - json config
├── `dev-report-20260415-210000.json` - json config
├── `dev-report-20260416-172720.json` - json config
├── `dev-report-20260417-001800.json` - json config
├── `dev-report-20260418-153011.json` - json config
├── `dev-report-20260504-234535-rc-defensive-fixes.json` - json config
├── `dev-report-20260505-060527.json` - json config
├── `dev-report-20260505-061047.json` - json config
├── `dev-report-20260505-123425.json` - json config
├── `dev-report-20260505-124619.json` - json config
├── `dev-report-20260505-174743-iter2.json` - json config
├── `dev-report-20260505-174743.json` - json config
├── `dev-report-20260505-175102.json` - json config
├── `dev-report-20260505-231740-W1.json` - json config
├── `dev-report-20260505-231740-W2.json` - json config
├── `dev-report-20260505-231740-W3.json` - json config
├── `dev-report-20260505-231740-W4.json` - json config
├── `dev-report-20260505-231740-W5.json` - json config
├── `dev-report-20260505-231740-W6.json` - json config
├── `dev-report-20260505-231740-W7.json` - json config
├── `dev-report-20260505-231740.json` - json config
├── `dev-report-20260506-081545-W1.json` - json config
├── `dev-report-20260506-081545-W2.json` - json config
├── `dev-report-20260506-081545-W3.json` - json config
├── `dev-report-20260506-081545.json` - json config
├── `dev-report-20260506-104100-iter2.json` - json config
├── `dev-report-20260506-104100-iter3.json` - json config
├── `dev-report-20260506-104100.json` - json config
├── `dev-report-20260506-141814.json` - json config
├── `dev-report-20260509-114002-cycle4.json` - json config
├── `dev-report-20260509-114002.json` - json config
├── `dev-report-20260513-090000-W-refactor.json` - json config
├── `dev-report-20260513-090000-W1-patch.json` - json config
├── `dev-report-20260513-090000-W1.json` - json config
├── `dev-report-20260513-090000-W2.json` - json config
├── `dev-report-20260513-090000-W3.json` - json config
├── `dev-report-20260513-090000-W4.json` - json config
├── `dev-report-20260513-090000-W5.json` - json config
├── `dev-report-20260513-090000-W6.json` - json config
├── `dev-report-20260513-090000-W8.json` - json config
├── `dev-report-20260513-090000.json` - json config
├── `dev-report-20260514-103616-m2.json` - json config
├── `dev-report-20260514-103616-m3.json` - json config
├── `dev-report-20260514-103616-m4a.json` - json config
├── `dev-report-20260514-103616-m4b.json` - json config
├── `dev-report-20260514-103616-m5.json` - json config
├── `dev-report-20260514-103616-m6.json` - json config
├── `dev-report-20260514-103616-m7.json` - json config
├── `dev-report-20260514-103616.json` - json config
├── `dev-report-20260514-200000.json` - json config
├── `dev-report-20260514-200530.json` - json config
├── `dev-report-20260515-102340.json` - json config
├── `dev-report-20260517-071910.json` - json config
├── `dev-report-20260517-101502.json` - json config
├── `dev-report-20260517-153318.json` - json config
├── `dev-report-20260517-172103.json` - json config
├── `dev-report-20260517-211850.json` - json config
├── `dev-report-20260518-101127.json` - json config
├── `dev-report-20260519-161933.json` - json config
├── `dev-report-20260520-200804.json` - json config
├── `prompt-inspector-report-20260505-061047.json` - json config
├── `prompt-inspector-report-20260505-123425.json` - json config
├── `prompt-inspector-report-20260505-124619.json` - json config
├── `prompt-inspector-report-20260505-175102.json` - json config
├── `prompt-inspector-report-20260505-231740.json` - json config
├── `prompt-inspector-report-20260506-081545.json` - json config
├── `prompt-inspector-report-20260506-141814.json` - json config
├── `prompt-inspector-report-20260509-114002.json` - json config
├── `prompt-inspector-report-20260513-090000.json` - json config
├── `prompt-inspector-report-20260514-103616.json` - json config
├── `prompt-inspector-report-20260514-200000.json` - json config
├── `prompt-inspector-report-20260514-200530.json` - json config
├── `prompt-inspector-report-20260515-102340.json` - json config
├── `prompt-inspector-report-20260517-071910.json` - json config
├── `prompt-inspector-report-20260517-101502.json` - json config
├── `prompt-inspector-report-20260517-211850.json` - json config
├── `prompt-inspector-report-20260518-101127.json` - json config
├── `prompt-inspector-report-20260519-161933.json` - json config
├── `qa-codex-consensus-20260506-081545.txt` - txt file
├── `qa-codex-consensus-round2-20260506-081545.txt` - txt file
├── `qa-full-audit-20260413.json` - json config
├── `qa-input-codex-prompt-20260506-081545.txt` - txt file
├── `qa-input-codex-round2-20260506-081545.txt` - txt file
├── `qa-output-ac10-envvar-stderr.txt` - txt file
├── `qa-output-ac10-envvar-stdout.txt` - txt file
├── `qa-output-ac10-noenv-stderr.txt` - txt file
├── `qa-output-ac10-noenv-stdout.txt` - txt file
├── `qa-output-codex-cycle3-r2-response.txt` - txt file
├── `qa-output-codex-cycle3-response.txt` - txt file
├── `qa-output-codex-prompt-cycle3-close.txt` - txt file
├── `qa-output-codex-prompt-cycle3-r2.txt` - txt file
├── `qa-output-codex-prompt-cycle3.txt` - txt file
├── `qa-output-codex-prompt-cycle4-close.txt` - txt file
├── `qa-output-codex-prompt-redev-postdev.txt` - txt file
├── `qa-output-tamper-bak-20260505-124619.js` - js file
├── `qa-report-20260320-213000.json` - json config
├── `qa-report-20260321-155000.json` - json config
├── `qa-report-20260405-201500.json` - json config
├── `qa-report-20260406-010001.json` - json config
├── `qa-report-20260406-010002.json` - json config
├── `qa-report-20260406-010003.json` - json config
├── `qa-report-20260406-010004.json` - json config
├── `qa-report-20260406-010005.json` - json config
├── `qa-report-20260406-010007.json` - json config
├── `qa-report-20260406-020001.json` - json config
├── `qa-report-20260406-020002.json` - json config
├── `qa-report-20260406-020003.json` - json config
├── `qa-report-20260406-020004.json` - json config
├── `qa-report-20260406-020005.json` - json config
├── `qa-report-20260412-213000.json` - json config
├── `qa-report-20260413-063000.json` - json config
├── `qa-report-20260413-064500.json` - json config
├── `qa-report-20260413-070000.json` - json config
├── `qa-report-20260413-181500.json` - json config
├── `qa-report-20260415-010000-iter2.json` - json config
├── `qa-report-20260415-010000.json` - json config
├── `qa-report-20260415-210000.json` - json config
├── `qa-report-20260416-172720.json` - json config
├── `qa-report-20260417-001800.json` - json config
├── `qa-report-20260418-153011.json` - json config
├── `qa-report-20260505-060527.json` - json config
├── `qa-report-20260505-061047.json` - json config
├── `qa-report-20260505-123425.json` - json config
├── `qa-report-20260505-124619.json` - json config
├── `qa-report-20260505-174743.json` - json config
├── `qa-report-20260505-175102.json` - json config
├── `qa-report-20260505-231740.json` - json config
├── `qa-report-20260506-081545.json` - json config
├── `qa-report-20260506-104100-iter2.json` - json config
├── `qa-report-20260506-104100-iter3.json` - json config
├── `qa-report-20260506-104100.json` - json config
├── `qa-report-20260506-141814.json` - json config
├── `qa-report-20260509-114002.json` - json config
├── `qa-report-20260513-090000.json` - json config
├── `qa-report-20260515-102340.json` - json config
├── `qa-report-20260517-071910.json` - json config
├── `qa-report-20260517-101502.json` - json config
├── `qa-report-20260517-153318.json` - json config
├── `qa-report-20260517-172103.json` - json config
├── `qa-report-20260517-195000.json` - json config
├── `qa-report-20260517-211603.json` - json config
├── `qa-report-20260517-211850.json` - json config
├── `qa-report-20260518-101127.json` - json config
├── `qa-report-20260519-161933-ba-validation-v2.json` - json config
├── `qa-report-20260519-161933-ba-validation-v3.json` - json config
├── `qa-report-20260519-161933-ba-validation.json` - json config
├── `qa-report-20260519-161933.json` - json config
├── `qa-report-20260520-200804-ba-validation.json` - json config
├── `qa-report-20260520-200804.json` - json config
├── `qa-validation-20260321.json` - json config
├── `qa-verification-iter2-summary.md` - QA Verification Iteration 2 Summary
├── `style-inspector-report-20260505-061047.json` - json config
├── `style-inspector-report-20260505-123425.json` - json config
├── `style-inspector-report-20260505-124619.json` - json config
├── `style-inspector-report-20260505-175102.json` - json config
├── `style-inspector-report-20260505-231740.json` - json config
├── `style-inspector-report-20260506-081545.json` - json config
├── `style-inspector-report-20260506-141814.json` - json config
├── `style-inspector-report-20260509-114002.json` - json config
├── `style-inspector-report-20260513-090000.json` - json config
├── `style-inspector-report-20260514-103616.json` - json config
├── `style-inspector-report-20260514-200000.json` - json config
├── `style-inspector-report-20260514-200530.json` - json config
├── `style-inspector-report-20260515-102340.json` - json config
├── `style-inspector-report-20260517-071910.json` - json config
├── `style-inspector-report-20260517-101502.json` - json config
├── `style-inspector-report-20260517-211850.json` - json config
├── `style-inspector-report-20260518-101127.json` - json config
├── `style-inspector-report-20260519-161933.json` - json config
├── `ticket-20260505-060527.md` - BA Specification: Travel Planner Render Bugs (7-bug cluster)
├── `ticket-20260505-061047.md` - BA Specification: Reconcile rednote-mcp source-of-truth after wrong-target patches
├── `ticket-20260505-123425.md` - BA Specification: Restore China-20260412 Trip Plan to Schema Compliance
├── `ticket-20260505-124619.md` - BA Specification: Complete search_notes_light deployment for production use (practical-value + defense-in-depth + known-bug bundle)
├── `ticket-20260505-174743.md` - BA Specification: 彻底清理 dev-cycle internal narrative leaked into trip data
├── `ticket-20260505-175102.md` - BA Specification: Forward-fix two CLOSE: NO defects from prior cycle 20260505-124619
├── `ticket-20260505-231740.md` - BA Specification: Codex-signed harness upgrade — full 10-step plan
├── `ticket-20260506-081545.md` - BA Specification: /redev fix 3 close blockers from cycle 20260505-231740 — ITERATION 2
├── `ticket-20260506-104100.md` - BA Specification: Travel-planner harness root-cause hardening — block schema/semantic violations at write-time, fix accumulated data bugs, kill HEAD pollution
├── `ticket-20260506-141814.md` - BA Specification: Close residual gaps from spec-20260506-092951 (2-item follow-on)
├── `ticket-20260509-114002.md` - BA Specification: M1 — gaode-maps harness ban (six matcher surfaces) + per-agent DO-NOT prompt block
├── `ticket-20260513-090000.md` - BA Specification: M2-prerequisite 13-bug fix-all-at-once cycle (round-2 remediation)
├── `ticket-20260514-103616.md` - BA Master Ticket: Complete spec-20260508-221237 §5.2-§5.13 (post-M1)
├── `ticket-20260514-200000.md` - BA Specification: spec-20260508-221237-redev1 Close Blockers (6 fixes)
├── `ticket-20260514-200530.md` - BA Specification: Travel-Planner Memory Content-Source Policy Restructure
├── `ticket-20260515-102340.md` - BA Specification: v2 Server Bug Fixes (4 bugs + 2 missing dependencies)
├── `ticket-20260517-071910.md` - BA Specification: Notion-style UI Redesign + 3 Bug Fixes
├── `ticket-20260517-101502.md` - BA Specification: UI Layout Redesign — 3-Column Notion Paradigm
├── `ticket-20260517-153318.md` - BA Specification: Notion-Style Visual Alignment — Web Editor (Except Candidates Sidebar)
├── `ticket-20260517-172103.md` - BA Specification: Add Photo Rendering to Trip Editor Cards and Cover
├── `ticket-20260517-195000.md` - BA Specification: Photo Card Layout Fixes — Timeline Thumbnail + Cover Resolution
├── `ticket-20260517-211506.md` - BA Specification: Fix .slot-selected Photo Layout + #trip-cover Visual Defect
├── `ticket-20260517-211850.md` - BA Specification: Trip Editor — React-Based Architecture (Visual Parity + Interactive Layer)
├── `ticket-20260518-101127.md` - BA Specification: Unified Viewer/Editor Page — EDITOR_MODE Removal + 12 Editor Features
├── `ticket-20260519-161933.md` - BA Specification: Fix Drag-Drop Visual Layer — Replace card content on selection
├── `ticket-20260520-200804.md` - BA Specification: Fix 2 /close blockers from cycle 20260519-161933
├── `user-requirement-dev-20260520-200659.md` - No description
└── `user-requirement-dev-20260520-200804.md` - No description
```

---
*Auto-generated by doc-sync hook.*