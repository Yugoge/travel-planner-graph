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

**2. Generation Scripts**

Purpose: Convert JSON data to output formats

- `generate-travel-html.sh` - Generate interactive HTML views
  - Input: Trip directory path
  - Output: HTML file with embedded map/timeline
  - Dependencies: Timeline, accommodation, attractions JSON files

**3. Deployment Scripts**

Purpose: Deploy plans to execution

- `deploy-travel-plans.sh` - Deploy plans to web or app
  - Input: Trip directory path
  - Output: Deployed plan URL or status
  - Note: Large script (18KB) - likely handles multiple deployment targets

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

## File Creation Patterns

Based on Git history:

**Created by**: Manual user additions
**Timeframe**: Jan 29, 2026
**Automation**: 0% (all manually created)

**Pattern**:
- All scripts created in single batch (Jan 29, 2026)
- No subsequent modifications (stable)
- Designed during initial project setup

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
All scripts created: 2026-01-29 15:25 UTC
Last modification: 2026-01-29 15:25 UTC (no changes since creation)
Total commits (scripts folder): 1 commit (initial creation)
Stability: High (no changes in 2 days)
<!-- END AUTO-GENERATED -->

---

*This README documents the organization rules for scripts/. Generated by rule-inspector from git history analysis.*
