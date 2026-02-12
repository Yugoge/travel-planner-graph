# Travel Plans

This repository contains auto-generated travel plans from the travel-planner.

**Live Site:** [https://Yugoge.github.io/travel-planner-graph/](https://Yugoge.github.io/travel-planner-graph/)

## Travel Plans

- [China Feb 15 Mar 7 2026 - 2026-02-10](https://Yugoge.github.io/travel-planner-graph/china-feb-15-mar-7-2026/2026-02-10/)
- [China Feb 15 Mar 7 2026 - 2026-02-02](https://Yugoge.github.io/travel-planner-graph/china-feb-15-mar-7-2026/2026-02-02/)
- [Beijing Exchange Bucket List - 2026-02-10](https://Yugoge.github.io/travel-planner-graph/beijing-exchange-bucket-list/2026-02-10/)
- [Beijing Exchange Bucket List - 2026-02-02](https://Yugoge.github.io/travel-planner-graph/beijing-exchange-bucket-list/2026-02-02/)

## Data Validation

This project uses schema-driven validation to ensure data quality.

### Running Validation

```bash
# Validate all trips
python scripts/plan-validate.py

# Validate specific trip
python scripts/plan-validate.py china-feb-15-mar-7-2026-20260202-195429

# Filter by severity
python scripts/plan-validate.py --min-severity MEDIUM

# Validate specific agent
python scripts/plan-validate.py --agent meals

# Export JSON report
python scripts/plan-validate.py --json-file report.json
```

### Configuration

Validation behavior can be customized via `config/validation.json`:

- **english_placeholders**: Words indicating untranslated content (e.g., "TBD", "Optional")
- **currency_region_map**: City-to-currency mapping for validation (disabled by default)
- **intentional_overlap_keywords**: Keywords indicating expected timeline overlaps
- **enforce_title_case**: Whether to enforce Title Case formatting

See `config/validation.json` for full documentation and default values.

### Running Tests

```bash
# Run unit tests for schema-driven inference
python tests/test_plan_validate_schema_inference.py
```

---

Last updated: 
