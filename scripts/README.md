# scripts/

Helper scripts for travel plan validation, generation, and deployment.

---

## Purpose

This folder contains reusable shell scripts that validate, generate, and deploy travel plans. Scripts are parameterized (no hardcoded paths) and designed to be called by planning workflows or manually.

**Key principle**: Scripts operate on data/ JSON files and enforce quality standards.

## Allowed File Types

- `.sh` files: Shell scripts (Bash)
- `.py` files: Python scripts (for complex logic or TodoWrite integration)
- NO `.pyc` files in git (bytecode should be .gitignored)

## Naming Convention

- **Shell scripts**: kebab-case with verb-noun pattern
  - Validation: `check-*.sh`, `validate-*.sh`
  - Generation: `generate-*.sh`
  - Deployment: `deploy-*.sh`
- **Python scripts**: snake_case (PEP 8)
- **Subdirectories**: kebab-case or descriptive names

## Python Modules

**lib/ directory**: Reusable Python modules for complex logic

- `lib/html_generator.py` - **[NEW]** Class-based HTML generator module
  - Class: `TravelPlanHTMLGenerator`
  - Methods: `detect_project_type()`, `merge_itinerary_data()`, `merge_bucket_list_data()`, `generate_html()`
  - Supports: Both itinerary and bucket list project types
  - Unit testable, no hardcoded values
  - Used by: `generate-and-deploy.sh` script
  - CLI usage: `python lib/html_generator.py <destination-slug> --data-dir <path> --output <path>`

## Organization Rules

### Script Categories

**1. Validation Scripts**

Purpose: Verify data quality and consistency

- `check-day-completion.sh` - Verify all trip days have plans
  - Input: Trip directory path
  - Output: Missing day warnings
  - Exit code: 0 if complete, 1 if missing days

- `check-location-continuity.sh` - Validate location transitions
  - Input: Timeline JSON file
  - Output: Location discontinuity errors
  - Exit code: 0 if continuous, 1 if gaps

- `validate-timeline-consistency.sh` - Validate timeline structure
  - Input: Timeline JSON file
  - Output: Schema validation errors
  - Exit code: 0 if valid, 1 if invalid

- `validate-plan-workflow.sh` - **[NEW]** Validate complete plan workflow execution
  - Input: `<destination-slug>`
  - Output: Comprehensive workflow status report
  - Checks: Required files, JSON syntax, agent completion, HTML generation
  - Exit codes: 0=complete, 1=incomplete, 2=missing critical files
  - Use to verify all workflow steps executed correctly

**2. Generation Scripts**

Purpose: Convert JSON data to output formats

- `generate-and-deploy.sh` - **[NEW]** Unified atomic script for generate + deploy
  - Input: `<destination-slug>` [version-suffix]
  - Output: HTML file + live GitHub Pages URL
  - Auto-detects project type (itinerary vs bucket list)
  - Atomic operation: Generation ALWAYS followed by deployment
  - Exit codes: 0=success, 1=generation failed, 2=deployment failed, 3=missing files
  - Replaces: Separate generate + deploy workflow
  - Root cause reference: Fixes script separation that caused workflow interruption

- `generate-travel-html.sh` - **[DEPRECATED]** Legacy HTML generator for itinerary only
  - Use `generate-and-deploy.sh` instead
  - Kept for backward compatibility only
  - Input: Trip directory path
  - Output: HTML file with embedded map/timeline
  - Dependencies: Timeline, accommodation, attractions JSON files

**3. Deployment Scripts**

Purpose: Deploy plans to execution

- `deploy-travel-plans.sh` - Deploy HTML to GitHub Pages
  - Input: HTML file path (supports multiple naming formats)
  - Output: Deployed plan URL or status
  - Now accepts: itinerary format, timestamp format, bucket list format, version suffixes
  - Auto-detects GitHub username and authentication method
  - Creates repository if needed, enables GitHub Pages
  - Note: Large script (18KB) - handles authentication, repo creation, index generation

**4. Workflow Scripts**

Purpose: TodoWrite integration and planning workflows

- `todo/plan.py` - Travel planning workflow checklist
  - Purpose: Define todo tasks for planning workflow
  - Used by: Planning agents via TodoWrite tool
  - Format: Python script returning todo list structure

**5. Gaode Maps Utilities**

Purpose: Process Gaode Maps API responses for transportation planning

- `gaode-maps/parse-transit-routes.py` - Parse transit route responses
  - Input: Gaode Maps API JSON response
  - Output: Structured route data with parsed fields
  - Exit code: 0 if success, 1 if parse error

- `gaode-maps/recommend-transportation.py` - Recommend best transportation
  - Input: Transit and driving options, user preferences
  - Output: Recommended option with scoring
  - Exit code: 0 if success, 1 if file error

- `gaode-maps/fetch-route-with-retry.py` - Fetch routes with retry logic
  - Input: Origin, destination, route type
  - Output: API response with exponential backoff retry
  - Exit code: 0 if success, 1 if failed

- `gaode-maps/plan-multi-city.py` - Plan multi-city transportation
  - Input: List of cities in travel order
  - Output: Complete transportation plan JSON
  - Exit code: 0 if success, 2 if partial failure

- `gaode-maps/transportation-workflow.py` - Complete workflow
  - Input: Destination slug (reads from data/)
  - Output: transportation.json in data directory
  - Exit code: 0 if success, 1 if failed

- `gaode-maps/README.md` - Documentation for utilities

**6. Location Detection**

Purpose: Detect location changes in travel plans

- `detect-location-changes.py` - Detect location changes
  - Input: plan-skeleton.json file path
  - Output: Updated plan with location_change objects
  - Exit code: 0 if success, 1 if file error

**7. Hook Scripts**

Purpose: Pre/post-tool hooks for workflow enforcement in Claude Code

- `hooks/hook-enforce-step-sequence.py` - Enforce canonical todo step ordering
  - Input: TodoWrite tool call context
  - Output: Block/allow decision based on step sequence rules
  - Exit code: 0 if valid, non-zero if sequence violation

- `hooks/hook-enforce-todo-count.py` - Enforce required todo count per workflow
  - Input: TodoWrite tool call with todo list
  - Output: Block if count mismatches canonical step count
  - Exit code: 0 if count matches, non-zero if mismatch

- `hooks/hook-enforce-workflow.py` - General workflow enforcement
  - Input: Tool call context
  - Output: Block unauthorized tool calls during workflows

- `hooks/hook-precheck-workflow.py` - Pre-check workflow state
  - Input: Session context
  - Output: Workflow readiness status

- `hooks/hook-checklist-userprompt.py` - Checklist validation on user prompt
  - Input: User prompt context
  - Output: Checklist compliance status

- `hooks/hook-session-start.py` - Session initialization hook
  - Input: Session start event
  - Output: Session state initialization

- `hooks/hook-todo-state-tracker.py` - Track todo state transitions
  - Input: TodoWrite changes
  - Output: State transition log

**8. Data I/O Scripts**

Purpose: Load and save travel plan data with validation

- `load.py` - Load travel plan data from JSON files
  - Input: Trip slug, optional agent filter
  - Output: Parsed plan data dictionary

- `save.py` - Save travel plan data with validation
  - Input: Trip slug, agent data, validation options
  - Output: Validated and saved JSON files
  - Features: Hotel timeline validation, token filtering, adaptive thresholds

**9. Utility Scripts**

Purpose: Miscellaneous utilities for plan management

- `parse-agent-json.py` - Parse agent JSON output
- `log-modification.py` - Log file modifications for audit trail
- `fix-day2-hotel-checkin.py` - Fix Day 2 hotel check-in timing
- `merge-timeline-day1.py` - Merge timeline data for Day 1
- `update-agent-prompts.py` - Update agent prompt templates
- `verify-tool-restrictions.py` - Verify MCP tool restrictions
- `clean-redundant-fields.py` - Remove redundant JSON fields
- `sync-agent-data.py` - Sync agent data across trip directories
- `update-skeleton.py` - Update plan skeleton files
- `generate-skeletons.py` - Generate skeleton files from requirements
- `generate-plan-slug.py` - Generate URL-safe slugs for plans
- `generate-booking-checklist.py` - Generate booking checklist
- `fetch-images-batch.py` - Batch fetch POI images
- `calculate-route-distances.py` - Calculate distances between route stops
- `check-budget-overage.py` - Check budget overages
- `fix-duration-units.py` - Fix duration unit inconsistencies
- `validate-agent-outputs.py` - Validate agent output completeness
- `validate-route-durations.py` - Validate route duration estimates
- `validate-timeline-data.py` - Validate timeline data quality

## File Creation Patterns

Based on Git history:

**Created by**: Manual user additions and automated hook generation
**Timeframe**: Jan 29, 2026 - Mar 14, 2026 (ongoing)
**Automation**: ~30% automated (hooks), ~70% manual

**Pattern**:
- Initial batch created Jan 29, 2026 (validation, generation, deployment)
- Data I/O scripts added Feb 2026 (load.py, save.py)
- Hook scripts added Mar 2026 (workflow enforcement)
- Ongoing modifications for validation improvements

## Standards

### Shell Scripts (.sh)

1. **Executable**: All .sh files must have execute permissions (`chmod +x`)
2. **Shebang**: Start with `#!/usr/bin/env bash` or `#!/bin/bash`
3. **Parameters**: Accept file/directory paths as arguments (no hardcoded paths)
4. **Error handling**: Check arguments, validate inputs, return proper exit codes
5. **Output**: Human-readable messages to stdout, errors to stderr

**Example usage**:
```bash
./scripts/validate-timeline-consistency.sh data/trip-name/timeline.json
./scripts/check-day-completion.sh data/trip-name/
```

### Python Scripts (.py)

1. **Shebang**: `#!/usr/bin/env python3` for standalone scripts
2. **Style**: Follow PEP 8 (4-space indentation, snake_case)
3. **Type hints**: Use type annotations
4. **Docstrings**: Document functions and modules
5. **Dependencies**: Minimal external dependencies (use stdlib when possible)

### Exit Codes

Scripts must return proper exit codes:

- `0`: Success (validation passed, generation completed)
- `1`: Failure (validation failed, errors occurred)
- `2`: Invalid arguments (missing required parameters)

**Rationale**: Allows workflow scripts to chain commands and detect failures.

### Documentation

Each script should include:

1. **Header comment**: Description, usage, parameters, exit codes
2. **Examples**: Sample invocations in comments
3. **Error messages**: Clear, actionable error messages

**Example header**:
```bash
#!/usr/bin/env bash
#
# Check day completion in travel timeline
#
# Usage: ./check-day-completion.sh <trip-directory>
#
# Exit codes:
#   0 - All days have plans
#   1 - Missing days detected
#   2 - Invalid arguments
```

## Script Dependencies

**Input sources**:
- `data/` directory: JSON files (requirements, timeline, categories)

**Output targets**:
- Stdout: Validation results, generation status
- Stderr: Error messages
- Files: Generated HTML (generate-travel-html.sh)
- Web/deployment: Remote endpoints (deploy-travel-plans.sh)

**Workflow integration**:
```
User → Planning agent → todo/plan.py (TodoWrite) → Validation scripts → Generation scripts → Deployment scripts
```

## Usage Examples

### Validate Timeline

```bash
# Check timeline structure
./scripts/validate-timeline-consistency.sh data/china-multi-city-feb15-mar7-2026/timeline.json

# Verify all days have plans
./scripts/check-day-completion.sh data/china-multi-city-feb15-mar7-2026/

# Check location continuity
./scripts/check-location-continuity.sh data/china-multi-city-feb15-mar7-2026/timeline.json
```

### Generate HTML

```bash
# Generate interactive HTML view
./scripts/generate-travel-html.sh data/china-multi-city-feb15-mar7-2026/
```

### Deploy Plan

```bash
# Deploy to execution environment
./scripts/deploy-travel-plans.sh data/china-multi-city-feb15-mar7-2026/
```

## Integration with Planning Workflow

Planning agents use scripts in this sequence:

1. **Planning phase**: User creates requirements-skeleton.json
2. **Generation phase**: Agent generates plan-skeleton.json, timeline.json
3. **Validation phase**: Scripts verify quality
   - `validate-timeline-consistency.sh` - Check structure
   - `check-day-completion.sh` - Check completeness
   - `check-location-continuity.sh` - Check logic
4. **Generation phase**: Create deliverables
   - `generate-travel-html.sh` - Create HTML view
5. **Deployment phase**: Deploy plan
   - `deploy-travel-plans.sh` - Deploy to target

**Quality gate**: Validation scripts must pass (exit code 0) before generation/deployment.

## Todo Workflow Integration

**todo/plan.py**:
- Defines todo checklist for planning workflow
- Used by planning agents via TodoWrite tool
- Returns structured todo list (pending, in_progress, completed)

**Usage in agents**:
```python
# Import todo definition
from scripts.todo.plan import get_planning_todos

# Generate todo list
todos = get_planning_todos(trip_requirements)

# Write to TodoWrite tool
TodoWrite(todos=todos)
```

## Git Analysis

<!-- AUTO-GENERATED by rule-inspector - DO NOT EDIT -->
First created: 2026-01-29
Last significant update: 2026-03-14
Total files: 124 (24 .py root-level, 20 .sh, 7 subdirectories)
Subdirectories: archive/ (62 files), gaode-maps/ (5), hooks/ (7), lib/ (4), todo/ (3), utils/ (3)
Total commits (scripts folder): 30+ commits
Recent activity (Mar 2026): Hook enforcement scripts (step-sequence, todo-count, workflow), save.py validation fixes, auto-commits
New scripts since last update: hooks/hook-enforce-step-sequence.py, hooks/hook-enforce-todo-count.py, hooks/hook-precheck-workflow.py, hooks/hook-checklist-userprompt.py, hooks/hook-enforce-workflow.py, hooks/hook-session-start.py, hooks/hook-todo-state-tracker.py
Stability: Active (hook development, validation improvements)
<!-- END AUTO-GENERATED -->

---

*This README documents the organization rules for scripts/. Generated by rule-inspector from git history analysis.*
