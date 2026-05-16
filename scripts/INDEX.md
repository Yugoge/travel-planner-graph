# scripts

*Last updated: 2026-05-16T20:46:47Z*
**Total entries**: 122
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
│   ├── exporters/
│   │   ├── `common.py` - Trip-loading wraps `trip_contract.load_trip`. Slot iteration unifies the 6
│   │   ├── `ical_renderer.py` - Produces a VCALENDAR with one VEVENT per selected slot + per inter-city
│   │   └── `pdf_renderer.py` - A4 portrait, one day per page, CJK font embedded (WenQuanYi Zen Hei primary,
│   ├── server/
│   │   ├── `budget.py` - Aggregates costs from day.json, transportation.json, route_cache.json. No
│   │   ├── `common.py` - Provides:
│   │   ├── `export.py` - Invokes scripts/export-pdf.py or scripts/export-ical.py (M6 worker output)
│   │   ├── `route.py` - Spec: spec-20260508-221237 §5.9 + §5.13 D #7
│   │   ├── `save.py` - Receives a batch of mutations for a single day. Applies them to day-NN.json
│   │   └── `trip.py` - Calls trip_contract.load_trip to assemble meta + days + transportation +
│   ├── trip_contract/
│   │   ├── `api_contract.py` - Consumed by:
│   │   ├── `constants.py` - Canonical constants for the M2 v2 trip contract.
│   │   ├── `day_type.py` - Computes which slots a day is EXPECTED to skip given its day_type and
│   │   ├── `errors.py` - Validation error types.
│   │   ├── `json_schema.py` - Loads schemas/v2/*.schema.json and runs the appropriate one against a payload
│   │   ├── `legacy.py` - Walks any JSON-shaped object and returns paths where the legacy
│   │   ├── `loaders.py` - data/<trip>/{meta.json, days/day-NN.json, transportation.json, route_cache.json,
│   │   ├── `state_machine.py` - Per codex Q2: gating uses min(day.stage), NOT max. A trip may only advance to a
│   │   ├── `transport.py` - §5.13 B red-eye ownership rule (cp-07): owning_day == depart_day, always.
│   │   └── `validators.py` - Public:
│   ├── `html_generator.py` - Reusable HTML generator module for travel plans
│   ├── `image_fetcher.py` - Image Fetcher Module
│   ├── `json_io.py` - Root Cause Fix: Prevents schema violations like meals in travel_segments
│   ├── `mcp-tool-catalog.json` - json config
│   ├── `mcp_client.py` - Base MCP client for communicating with MCP servers via JSON-RPC 2.0 over stdio
│   ├── `react_template.tpl` - tpl file
│   ├── `render_day_data.py` - Each helper is <=30 lines per the project quality gate. The renderer
│   ├── `render_html_builders.py` - W7 refactor (spec-20260513-085358): module-level functions take the
│   ├── `save_translate.py` - User-facing terms ('primary', 'Plan A', '主行程' etc.) map onto the
│   └── `semantic_lint.py` - Cross-domain duplicate detection (AC8), meal_slot demoted-primary audit
├── tests/
│   ├── `test_json_io_ownership.py` - Iter 2 (spec-20260505-221501 / W2): verifies the persistence-layer
│   └── `test_merge_agent_slots.py` - Root Cause Fix reference (L4): the former merge_agent_days() performed full
├── todo/
│   ├── `plan.py` - Root cause reference: Commit 77dca06 introduced nested loop pattern for Step 14-15
│   └── `review.py` - Preloaded TodoList for /review command workflow.
├── utils/
│   ├── `fetch-exchange-rate.sh` - Description: Fetch real-time exchange rate between two currencies with cache fallback
│   └── `load_env.py` - Load environment variables from .env file in project root
├── `_qa_close_repro.sh` - QA close-debate cycle-3 reproduction script — base64 indirection avoids self-tripping the hook.
├── `_qa_close_repro2.sh` - Verify Glob.pattern bypass closure with a known-good role (dev, in roles dict).
├── `_qa_close_repro_v2.sh` - Re-reproduce cycle-1 close-report findings with explicit CLAUDE_PROJECT_DIR.
├── `_qa_codex_verify.sh` - Verify the 4 critical Codex bypass claims independently.
├── `_qa_diag.sh` - Diagnose why Glob.pattern alone (no path) didn't fire gaode read-path matcher.
├── `_qa_diag2.sh` - Diagnose what abspath gives for the bare pattern.
├── `_qa_diag3.sh` - Test the EXACT cycle-1 finding-1 reproduction.
├── `_qa_diag4.sh` - Shell script
├── `_qa_diag5.py` - Python script
├── `_qa_diag6.py` - Spawn the hook subprocess with the JSON on stdin
├── `_qa_diag7.py` - What does the policy actually have for read-path prefixes?
├── `_qa_diag8.sh` - Test: does Skill matcher catch direct invocation of g-aode-maps skill?
├── `audit-data-loss.py` - Root Cause: Before merge_agent_slots() (added 2026-04-16), POI agents that
├── `calculate-route-distances.py` - Reads GPS coordinates from agent outputs, calculates haversine distances,
├── `check-budget-overage.py` - Check if budget overage exceeds thresholds requiring day-by-day review
├── `check-day-completion.sh` - Validate that all days in requirements-skeleton.json have user_plans populated
├── `check-location-continuity.sh` - Validate that all location changes have corresponding location_change objects
├── `check_plan_integrity.py` - Cross-file referential-integrity linter (spec-20260506-092951 §5.7).
├── `clean-redundant-fields.py` - Clean Redundant Fields from Agent Data
├── `day13_chengdu_match.py` - so the renderer surfaces them with dashed-border + Optional badge, matching Chengdu Day 5/6
├── `day13_dinner_g26.py` - Sit-down 本帮菜 (HOMES) impossible. Change primary to G26 on-train meal order,
├── `deploy-travel-plans.sh` - Deploy travel plan HTML to GitHub Pages
├── `detect-location-changes.py` - Reads day-by-day plan and identifies when travelers move between cities
├── `export-ical.py` - Usage: python3 scripts/export-ical.py --trip <trip_id>
├── `export-pdf.py` - Usage: python3 scripts/export-pdf.py --trip <trip_id>
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
├── `migrate_yunnan_v1_to_v2.py` - migrate_yunnan_v1_to_v2.py
├── `parse-agent-json.py` - Parse agent JSON response and display summary, warnings, errors
├── `plan-validate.py` - Plan Data Validation — pre-HTML-generation gate
├── `push-to-main-repo.sh` - Push source code to main travel-planner repository (private)
├── `regen-command-index.py` - Regenerate .claude/commands/INDEX.md from frontmatter of command .md files.
├── `save.py` - Unified Data Saving Script — Batch Validation and Atomic Writes.
├── `save.py.backup` - backup file
├── `serve-trip.py` - Spec: spec-20260508-221237 §5.13 D + M2-contract.md §9
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
├── `validate-trip-contract.py` - Validates the new options-first per-day file shape under data/<trip>/days/day-NN.json,
├── `verify-gaode-ban-contract.sh` - Description: T3 contract verifier — validates every MCP tool in the catalog
├── `verify-gaode-ban-integration.sh` - Description: T2 integration verifier — spawns pretool-tool-policy.py as subprocess,
├── `verify-gaode-ban.sh` - Description: Verify gaode-maps harness ban (spec-20260508-221237 M1 + M5).
├── `verify-plan-integrity.py` - Codex-signed deploy-blocking integrity verifier for travel-plan trips
└── `verify-tool-restrictions.py` - Tool Restrictions Verification Script
```

---
*Auto-generated by doc-sync hook.*