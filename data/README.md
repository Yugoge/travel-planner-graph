# data/

Travel plan data storage in structured JSON format.

---

## Purpose

This folder stores trip planning data in machine-readable JSON format. Each trip has its own subdirectory containing requirements, generated plans, and detailed breakdowns by category.

**Key use case**: Scripts read/write JSON files here for trip planning workflows.

## Allowed File Types

- `.json` files ONLY
- NO other formats (.md, .txt, .yaml, etc.)
- Exception: This README.md and INDEX.md for documentation

## Naming Convention

- **Directories**: kebab-case with descriptive trip identifier
  - Format: `{destination}-{duration}-{dates}` (e.g., `china-multi-city-feb15-mar7-2026`)
  - Test directories: `test-*` prefix (e.g., `test-trip`)
- **JSON files**: kebab-case with semantic suffixes
  - Templates: `*-skeleton.json`
  - Test fixtures: `*-broken.json`, `*-incomplete.json`
  - Data categories: `{category}.json` (e.g., `timeline.json`, `budget.json`)

## Organization Rules

### Trip Directory Structure

Each active trip requires this standard structure:

```
trip-name/
├── requirements-skeleton.json    # REQUIRED: Trip requirements/constraints
├── plan-skeleton.json            # REQUIRED: Generated trip plan
├── timeline.json                 # REQUIRED: Day-by-day schedule
├── transportation.json           # Transport between cities
├── accommodation.json            # Hotels/lodging
├── attractions.json              # Tourist sites
├── meals.json                    # Dining plans
├── entertainment.json            # Events/shows
├── shopping.json                 # Shopping plans
└── budget.json                   # Cost tracking
```

**Required files**: `requirements-skeleton.json`, `plan-skeleton.json`, `timeline.json`

**Optional files**: Other category files depend on trip complexity

### File Purposes

**requirements-skeleton.json**:
- Input to trip planning workflow
- Contains: dates, destinations, preferences, constraints, budget
- Created: Manually or via planning scripts
- Format: User-facing requirements specification

**plan-skeleton.json**:
- Output from trip planning workflow
- Contains: Complete itinerary overview
- Generated: From requirements via planning scripts
- Format: Structured trip plan

**timeline.json**:
- Day-by-day schedule
- Contains: Daily activities with times and locations
- Generated: From plan-skeleton
- Used by: Validation scripts (check-day-completion.sh, validate-timeline-consistency.sh)

**Category files** (transportation, accommodation, etc.):
- Detailed breakdowns of plan sections
- Contains: Bookings, reservations, contact info
- Generated: From plan-skeleton or added manually
- Optional: Only create if needed for trip complexity

### Test Data

**test-trip/** directory:
- Template files for development
- Broken/incomplete files for validation testing
- NOT a real trip plan

**Usage**:
- Scripts use test-trip/ for development
- Validation scripts test against broken files
- Do NOT modify test fixtures without updating tests

## File Creation Patterns

Based on Git history:

**Created by**: Manual user input and planning scripts
**Timeframe**: Jan 29-30, 2026
**Automation**: ~50% manual, ~50% script-generated

**Pattern**:
1. User creates `requirements-skeleton.json` (manual)
2. Planning script generates `plan-skeleton.json` (automated)
3. User or scripts add category files (mixed)

## Standards

### JSON Format

1. **Valid JSON**: All files must parse without errors
2. **Pretty-printed**: Use 2-space indentation
3. **UTF-8 encoding**: Support international characters (Chinese, etc.)
4. **No comments**: JSON does not support comments (use separate docs)

### Schema Validation

1. **requirements-skeleton.json**: Must include dates, destinations
2. **timeline.json**: Must have continuous day coverage (no gaps)
3. **Location continuity**: End location of day N = start location of day N+1
4. **Date consistency**: All dates within trip date range

**Validation scripts**:
- `scripts/check-day-completion.sh` - Verify all days have plans
- `scripts/check-location-continuity.sh` - Check location transitions
- `scripts/validate-timeline-consistency.sh` - Validate timeline structure

### Naming Standards

**Trip directories**:
- Use destination-duration-dates pattern
- Lowercase with hyphens (kebab-case)
- Example: `japan-2weeks-apr2026`, `europe-1month-summer2026`

**JSON files**:
- Use semantic category names
- Lowercase with hyphens (kebab-case)
- Suffix templates with `-skeleton`
- Suffix test fixtures with `-broken` or `-incomplete`

## Directory Structure

**Active Trips**: Currently planning trips are stored in root-level directories.

**Archived Trips**: Completed and test trips are stored in `archive/YYYY-MM/`.

### Archive

**archive/2026-01/** (Jan 2026 trips):
- china-multi-city-feb15-mar7-2026/ (232 KB) - Completed multi-city trip
- test-trip/ (24 KB) - Template and test fixtures

**archive/2026-02/** (Feb 2026 tests):
- beijing-3day-budget/ (52 KB) - Budget agent test
- beijing-simple-test/ (44 KB) - Simple agent test
- beijing-timeline-test/ (40 KB) - Timeline agent test
- china-multi-city-feb-mar-2026/ (204 KB) - Multi-city trip planning
- shanghai-test/ (32 KB) - Shanghai test data
- skill-test/ (184 KB) - Skill integration tests

**Total archived**: 8 trips | 812 KB

## Active Trips

**Status**: No active trips (data/ directory ready for new planning)

## Integration with Scripts

Scripts in `scripts/` directory interact with this data:

**Planning scripts**:
- `deploy-travel-plans.sh` - Deploy plans to execution
- `generate-travel-html.sh` - Generate HTML views

**Validation scripts**:
- `check-day-completion.sh` - Verify timeline completeness
- `check-location-continuity.sh` - Check location logic
- `validate-timeline-consistency.sh` - Validate timeline format

**Usage**:
```bash
# Validate timeline
./scripts/validate-timeline-consistency.sh data/china-multi-city-feb15-mar7-2026/timeline.json

# Check day completion
./scripts/check-day-completion.sh data/china-multi-city-feb15-mar7-2026/
```

## Git Analysis

<!-- AUTO-GENERATED by rule-inspector - DO NOT EDIT -->
First created: 2026-01-29
Primary creator: Manual user input + planning scripts
Last significant update: 2026-02-01
Total commits (data folder): 15+ commits
Recent activity: Testing agent-skill integration, timeline validation, budget agent testing
<!-- END AUTO-GENERATED -->

---

*This README documents the organization rules for data/. Generated by rule-inspector from git history analysis.*
