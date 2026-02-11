# schemas

JSON schema definitions for travel plan data validation.

---

## Purpose

This folder contains JSON schema files that define the structure and validation rules for travel plan data. Schemas ensure data consistency across agents, scripts, and HTML generation.

**Key use case**: Validate JSON files in `data/` directory against standardized schemas.

## Allowed File Types

- `.json` files: JSON schema definitions
- `.md` files: Schema documentation
- NO other formats

## Naming Convention

- **Schema files**: `{category}.schema.json`
  - Example: `accommodation.schema.json`, `timeline.schema.json`
  - Pattern: Domain name + `.schema.json` suffix
- **Documentation**: `{topic}-{format}.md`
  - Example: `POI-data-schema.md`, `naming-convention.md`

## Organization Rules

### Schema Files

**Domain-specific schemas**:
- `accommodation.schema.json` - Hotel/lodging data structure
- `attractions.schema.json` - Tourist attractions POI format
- `entertainment.schema.json` - Events/shows data structure
- `meals.schema.json` - Restaurant/dining POI format
- `shopping.schema.json` - Shopping locations format
- `budget.schema.json` - Cost tracking structure
- `timeline.schema.json` - Daily itinerary format
- `transportation.schema.json` - Inter-city travel format

**Common schemas**:
- `poi-common.schema.json` - Shared POI fields (used by all POI schemas)
- Reusable components for location, contact info, opening hours

### Documentation Files

- `POI-data-schema.md` - Comprehensive POI schema guide
- `naming-convention.md` - Field naming standards

## File Responsibilities

**Schema files**:
- Define required vs optional fields
- Specify data types (string, number, array, object)
- Set validation rules (min/max, patterns, enums)
- Document field purposes and constraints

**Usage**:
- Scripts validate data JSONs against schemas
- Agents reference schemas when generating data
- Error messages reference schema violations

## File Creation Patterns

Based on Git history:

**Created by**: Manual schema design + script generation
**Timeframe**: Feb 8-11, 2026
**Automation**: 50% manual design, 50% script updates

**Pattern**:
1. Schema designed manually (domain modeling)
2. Scripts validate against schema (enforcement)
3. Schema updated when new fields needed (iterative refinement)
4. Migration scripts update old data to new schema

**Recent commits**:
- 2026-02-11 01:12: "checkpoint: Auto-save" (schema updates)
- 2026-02-10 22:39: "feat: tighten schemas + normalize all 21-day data"
- 2026-02-08 13:25+: Schema creation and refinement

## Standards

### JSON Schema Format

1. **JSON Schema Draft 7**: Standard specification
2. **2-space indentation**: Consistent formatting
3. **Descriptive titles**: Each schema has title and description
4. **Field documentation**: Each property includes description
5. **Validation rules**: Min/max, patterns, required fields

### Schema Structure

**Common POI fields** (from `poi-common.schema.json`):
- `name` (string, required): POI name in Chinese and English
- `name_en` (string, required): English name
- `name_zh` (string, required): Chinese name
- `coordinates` (object, optional): {latitude, longitude}
- `address` (string, optional): Street address
- `opening_hours` (string, optional): Hours of operation
- `phone` (string, optional): Contact phone
- `cost` (number, optional): Price in CNY
- `cost_usd` (number, optional): Price in USD
- `images` (array, optional): Image URLs

**Domain-specific extensions**:
- Each domain adds specialized fields
- Example: `accommodation` adds check-in/out dates, room type
- Example: `attractions` adds ticket price, duration, best_time_to_visit

### Validation

**Schema validation scripts**:
- `scripts/qa-schema-audit.py` - Validate all schemas
- `scripts/validate-agent-outputs.py` - Check agent outputs
- `scripts/plan-validate.py` - Comprehensive plan validation

**Validation workflow**:
1. Agent generates data JSON
2. Script validates against schema
3. Errors reported to user
4. Agent fixes violations
5. Re-validate until clean

## Schema Evolution

**Version control**:
- Schemas evolve with project requirements
- Breaking changes require data migration
- Non-breaking additions backward compatible

**Change process**:
1. Identify need (new field, validation rule)
2. Update schema file
3. Add field to existing data (migration script)
4. Update agents to use new field
5. Validate all data files

**Recent changes**:
- Added `optional` field support (Feb 11, 2026)
- Tightened validation rules (Feb 10, 2026)
- Standardized POI common fields (Feb 8, 2026)

## Integration with Workflow

**Agent usage**:
```python
# Agent reads schema
schema = json.load(open('schemas/attractions.schema.json'))

# Agent generates data matching schema
attractions = generate_attractions(requirements, schema)

# Script validates
validate_schema(attractions, schema)
```

**Script validation**:
```bash
# Validate all agent outputs
./scripts/validate-agent-outputs.py data/china-*/attractions.json schemas/attractions.schema.json

# Schema audit
./scripts/qa-schema-audit.py
```

## Dependencies

**Input to**: Agents, validation scripts, HTML generator

**Read by**:
- `scripts/validate-agent-outputs.py`
- `scripts/plan-validate.py`
- `scripts/qa-schema-audit.py`
- `scripts/migrate-data-to-schema.py`

**Output from**: Manual design (schema engineers)

## Git Analysis

<!-- AUTO-GENERATED by rule-inspector - DO NOT EDIT -->
First created: 2026-02-08
Primary creator: Manual schema design + validation scripts
Last significant update: 2026-02-11
Total schemas: 9 (8 domain + 1 common)
Documentation: 2 MD files
Recent activity: Schema tightening, normalization, optional field support
Total commits (schemas folder): 5+ commits
Stability: Medium (active refinement phase)
<!-- END AUTO-GENERATED -->

---

*This README documents the organization rules for schemas/. Generated by rule-inspector from git history analysis.*
