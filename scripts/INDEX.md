# scripts

*Last updated: 2026-05-06T11:27:09Z*
**Total entries**: 73
**Convention**: kebab

## Tree
```
scripts/
├── gaode-maps/
│   ├── `parse-transit-routes.py` - Extracts main segment information and formats into structured data
│   ├── `plan-multi-city.py` - Coordinates routes between multiple cities with graceful error handling
│   ├── `recommend-transportation.py` - Compares transit and driving options considering time, cost, and user preferences
│   └── `transportation-workflow.py` - Orchestrates full transportation planning from requirements to final JSON output
├── hooks/
│   ├── `hook-checklist-userprompt.py` - UserPromptSubmit Hook: Checklist Injection for Slash Commands
│   ├── `hook-enforce-step-sequence.py` - PostToolUse Hook: Enforce one-step-at-a-time progression in workflow checklists
│   ├── `hook-enforce-todo-count.py` - PostToolUse Hook: Enforce canonical todo count immediately after TodoWrite
│   ├── `hook-enforce-workflow.py` - Stop Hook: Enforce workflow structural integrity before allowing Claude to stop
│   ├── `hook-precheck-workflow.py` - PreToolUse Hook: Require TodoWrite/TodoRead acknowledgment before other tools
│   ├── `hook-session-start.py` - SessionStart Hook: Display count of due reviews on session startup
│   └── `hook-todo-state-tracker.py` - PostToolUse Hook: Output checklist progress after every TodoWrite call
├── lib/
│   ├── `html_generator.py` - Reusable HTML generator module for travel plans
│   ├── `image_fetcher.py` - Image Fetcher Module
│   ├── `json_io.py` - Root Cause Fix: Prevents schema violations like meals in travel_segments
│   ├── `mcp_client.py` - Base MCP client for communicating with MCP servers via JSON-RPC 2.0 over stdio
│   └── `save_translate.py` - User-facing terms ('primary', 'Plan A', '主行程' etc.) map onto the
├── tests/
│   ├── `test_json_io_ownership.py` - Iter 2 (spec-20260505-221501 / W2): verifies the persistence-layer
│   └── `test_merge_agent_slots.py` - Root Cause Fix reference (L4): the former merge_agent_days() performed full
├── todo/
│   ├── `plan.py` - Root cause reference: Commit 77dca06 introduced nested loop pattern for Step 14-15
│   └── `review.py` - Preloaded TodoList for /review command workflow.
├── utils/
│   ├── `fetch-exchange-rate.sh` - Description: Fetch real-time exchange rate between two currencies with cache fallback
│   └── `load_env.py` - Load environment variables from .env file in project root
├── `audit-data-loss.py` - Root Cause: Before merge_agent_slots() (added 2026-04-16), POI agents that
├── `calculate-route-distances.py` - Reads GPS coordinates from agent outputs, calculates haversine distances,
├── `check-budget-overage.py` - Check if budget overage exceeds thresholds requiring day-by-day review
├── `check-day-completion.sh` - Validate that all days in requirements-skeleton.json have user_plans populated
├── `check-location-continuity.sh` - Validate that all location changes have corresponding location_change objects
├── `check_plan_integrity.py` - Cross-file referential-integrity linter (spec-20260506-092951 §5.7).
├── `clean-redundant-fields.py` - Clean Redundant Fields from Agent Data
├── `deploy-travel-plans.sh` - Deploy travel plan HTML to GitHub Pages
├── `detect-location-changes.py` - Reads day-by-day plan and identifies when travelers move between cities
├── `fetch-images-batch.py` - Batch image fetcher using skill scripts directly
├── `fix-day2-hotel-checkin.py` - Fix Day 2 Hotel Check-in Script
├── `fix-duration-units.py` - Fix duration_minutes field by detecting and correcting unit conversion errors
├── `generate-and-deploy.sh` - Generate interactive React HTML and deploy to GitHub Pages
├── `generate-booking-checklist.py` - Extract booking items from timeline/budget warnings and generate actionable checklist
├── `generate-html-interactive.py` - Interactive React Travel Plan Generator
├── `generate-html.sh` - Generate travel HTML using Python html_generator.py
├── `generate-plan-slug.py` - Addresses root cause from commit 77dca06 where {destination-slug} was used
├── `generate-skeletons.py` - Addresses root cause from dev-20260204-141257: Orchestrator architectural constraint
├── `index.md` - scripts Index
├── `init-plan-skeleton.sh` - Convert requirements-skeleton.json to plan-skeleton.json
├── `init-requirements-skeleton.sh` - Generate requirements-skeleton.json from user interview data
├── `load.py` - Unified Data Loading Script - 3-Level Hierarchical Access
├── `log-modification.py` - Modification Logging Helper - Append structured log entry to modification-log.json
├── `merge-timeline-day1.py` - Timeline Day 1 Merge Script
├── `migrate_spec_20260506.py` - Run under DEV_MIGRATION_BYPASS=spec-20260506-092951 so the new write-time
├── `parse-agent-json.py` - Parse agent JSON response and display summary, warnings, errors
├── `plan-validate.py` - Plan Data Validation — pre-HTML-generation gate
├── `push-to-main-repo.sh` - Push source code to main travel-planner repository (private)
├── `regen-command-index.py` - Regenerate .claude/commands/INDEX.md from frontmatter of command .md files.
├── `save.py` - Unified Data Saving Script — Batch Validation and Atomic Writes.
├── `save.py.backup` - backup file
├── `strip-image-url-fields.py` - Description: Recursively strip "image_url" keys from JSON files (PATH B image migration).
├── `sync-agent-data.py` - Agent Data Synchronization Script
├── `test-load-py.sh` - Description: Comprehensive test suite for scripts/load.py
├── `test-unified-workflow.sh` - Test Unified Scripts Architecture
├── `update-agent-docs.sh` - Update all agent documentation to use unified load.py/save.py scripts
├── `update-agent-prompts.py` - Agent Prompt Hardening Script
├── `update-skeleton.py` - Performs atomic mutations on existing skeleton files without regenerating from
├── `validate-agent-outputs.py` - JSON Schema-based validation of all agent outputs
├── `validate-plan-workflow.sh` - Validate plan workflow execution completeness
├── `validate-route-durations.py` - Validate duration/distance consistency across all routes in transportation.json
├── `validate-timeline-consistency.sh` - Validate timeline dictionary: keys match activity names, no time conflicts
├── `validate-timeline-data.py` - Validate timeline.json data completeness, structure, and time overlaps
├── `verify-plan-integrity.py` - Codex-signed deploy-blocking integrity verifier for travel-plan trips
└── `verify-tool-restrictions.py` - Tool Restrictions Verification Script
```

---
*Auto-generated by doc-sync hook.*