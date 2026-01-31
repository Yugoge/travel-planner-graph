# Prompt Verbosity Inspection Summary

**Inspection Date**: 2026-01-31
**Inspector**: prompt-inspector
**Request ID**: clean-20260131-191742

---

## Executive Summary

Inspected 51 markdown files across `.claude/commands/`, `.claude/skills/`, and `.claude/agents/` directories. Identified **14 files with verbosity violations** following the "rules not stories" principle.

**Key Findings**:
- 9 critical violations (>40% verbosity or >200 verbose lines)
- 4 major violations (30-40% verbosity or 100-200 verbose lines)
- 1 minor violation (duplicate content)
- **Total verbose lines**: 3,422 lines across violations
- **Average verbosity**: 50.2% in violating files
- **Reduction potential**: 2,800-3,000 lines (40-45%)

---

## Critical Violations

### 1. `.claude/commands/gaode-maps/tools/utilities.md` (585 lines)
- **Verbosity**: 58.1% (340 verbose lines)
- **Issues**: Extensive JavaScript implementation examples, integration patterns, advanced usage scenarios
- **Target**: Reduce to <150 lines total (~75% reduction)

### 2. `.claude/skills/gaode-maps/tools/geocoding.md` (475 lines)
- **Verbosity**: 54.7% (260 verbose lines)
- **Issues**: Duplicate of commands version with Best Practices, Common Workflows, Error Handling
- **Target**: Consolidate with commands version or reduce to ~215 lines

### 3. `.claude/skills/gaode-maps/tools/utilities.md` (445 lines)
- **Verbosity**: 53.9% (240 verbose lines)
- **Issues**: Duplicate verbose patterns from commands version
- **Target**: Consolidate with commands version or reduce to ~205 lines

### 4. `.claude/commands/gaode-maps/tools/poi-search.md` (476 lines)
- **Verbosity**: 52.5% (250 verbose lines)
- **Issues**: Exhaustive POI category codes (120 lines), verbose Best Practices
- **Target**: Move category codes to external reference, reduce to ~226 lines

### 5. `.claude/commands/gaode-maps/tools/geocoding.md` (589 lines)
- **Verbosity**: 49.1% (289 verbose lines)
- **Issues**: Best Practices code examples (150 lines), Common Workflows (89 lines)
- **Target**: Reduce to ~300 lines

### 6. `.claude/skills/gaode-maps/tools/poi-search.md` (433 lines)
- **Verbosity**: 48.5% (210 verbose lines)
- **Issues**: Duplicate of commands version
- **Target**: Consolidate or reduce to ~223 lines

### 7. `.claude/skills/rednote/examples/content-extraction.md` (508 lines)
- **Verbosity**: 78.7% (400 verbose lines)
- **Issues**: Extremely verbose mock API response (300 lines), redundant data reformatting
- **Target**: Reduce to ~108 lines

### 8. `.claude/commands/gaode-maps/examples/script-execution.md` (415 lines)
- **Verbosity**: 72.3% (300 verbose lines)
- **Issues**: Full verbose JSON output for each example
- **Target**: Reduce to ~165 lines

### 9. `.claude/commands/plan.md` (608 lines)
- **Verbosity**: 36.7% (223 verbose lines)
- **Issues**: Architecture Overview (32 lines), Quality Standards (71 lines), verbose step explanations (87 lines)
- **Target**: Reduce to ~428 lines

---

## Major Violations

### 10. `.claude/skills/gaode-maps/tools/routing.md` (371 lines)
- **Verbosity**: 40.4% (150 verbose lines)
- **Target**: Reduce to ~221 lines

### 11. `.claude/commands/gaode-maps/examples/inter-city-route.md` (426 lines)
- **Verbosity**: 35.2% (150 verbose lines)
- **Target**: Reduce to ~276 lines

### 12. `.claude/skills/airbnb/tools/details.md` (368 lines)
- **Verbosity**: 35.3% (130 verbose lines)
- **Target**: Reduce to ~238 lines

### 13. `.claude/skills/rednote/SKILL.md` (480 lines)
- **Verbosity**: 33.3% (160 verbose lines)
- **Target**: Reduce to ~320 lines

---

## Minor Violations

### 14. `.claude/skills/gaode-maps/examples/inter-city-route.md` (269 lines)
- **Verbosity**: 33.5% (90 lines)
- **Issue**: Duplicate of commands version
- **Recommendation**: Eliminate duplication entirely

---

## Common Verbosity Patterns

### 1. **Verbose Best Practices Sections**
Found in 8 files, averaging 100+ lines with JavaScript code examples and implementation patterns.

**Example**: `.claude/commands/gaode-maps/tools/utilities.md`
```markdown
## Best Practices

### 1. Weather Integration

**Daily weather in travel plan**:
```javascript
async function getDailyWeather(city, days) {
  // 30+ lines of implementation code
}
```
```

**Fix**: Move to developer guides, keep only essential parameter notes in tool reference.

---

### 2. **Exhaustive API Response Examples**
Found in 5 files, with 100-300 line mock responses.

**Example**: `.claude/skills/rednote/examples/content-extraction.md`
- 300 lines of sample RedNote API response
- Includes full travel itinerary data
- Then duplicates same data in "structured" format

**Fix**: Show only key fields (10-20 lines), link to full example if needed.

---

### 3. **Duplicate Content**
Commands vs Skills directories have identical content:
- `tools/geocoding.md` (589 vs 475 lines)
- `tools/poi-search.md` (476 vs 433 lines)
- `tools/utilities.md` (585 vs 445 lines)
- `examples/inter-city-route.md` (426 vs 269 lines)

**Fix**: Consolidate to single source of truth.

---

### 4. **Philosophy and Architecture Sections**
Found in `plan.md`:
- Architecture Overview (32 lines)
- Quality Standards (71 lines)
- Notes (10 lines)

**Fix**: Move to `/dev.md` or development documentation.

---

### 5. **Tutorial-Style Walkthroughs**
Found in 6 files with step-by-step explanations instead of reference format.

**Example**: Common Workflows, Integration Patterns sections

**Fix**: Convert to concise examples in `examples/` directory.

---

## Consolidation Opportunities

### 1. **Commands vs Skills Duplication**
**Issue**: Same tool documentation exists in both directories.

**Files affected**:
- `commands/gaode-maps/tools/*.md` (1,953 lines)
- `skills/gaode-maps/tools/*.md` (1,724 lines)
- Total duplication: ~1,700 lines

**Recommendation**:
- Keep single version in `skills/` (user-facing)
- Remove from `commands/` or create symlinks
- Save ~1,700 lines

---

### 2. **POI Category Codes**
**Issue**: 100-120 line exhaustive listings in 2 files.

**Files affected**:
- `commands/gaode-maps/tools/poi-search.md`
- `skills/gaode-maps/tools/poi-search.md`

**Recommendation**:
- Extract to `docs/references/gaode-poi-categories.md`
- Link from tool docs with 5-10 most common categories
- Save ~200 lines

---

## Reduction Roadmap

### Phase 1: Quick Wins (30 minutes, ~1,000 lines)
1. Remove duplicate files between commands/ and skills/ directories
2. Remove Architecture Overview and Quality Standards from plan.md
3. Extract POI category codes to external reference

### Phase 2: Content Compression (1-2 hours, ~1,500 lines)
1. Compress API response examples to key fields only
2. Reduce Best Practices sections to essential notes
3. Remove Common Workflows and Integration Patterns

### Phase 3: Consolidation (1 hour, ~500 lines)
1. Consolidate commands/skills tool documentation
2. Move verbose examples to dedicated example files
3. Remove redundant explanations in step-by-step guides

**Total Estimated Reduction**: 2,800-3,000 lines (40-45%)

---

## Target Metrics

| File Type | Current Avg Verbosity | Target Verbosity |
|-----------|----------------------|------------------|
| Critical files | 50-80% | 10-15% |
| Major files | 30-40% | 12-20% |
| Example files | 35-80% | 15-25% |

---

## Reference

**Successful Cleanup Example**: `convert.md` cleanup (commit 2d21631)
- Reduced 113 lines (-22%)
- Applied "rules not stories" principle
- Removed philosophical sections and verbose explanations

Apply same approach to files identified in this report.

---

## Next Steps

1. Review this report with project maintainer
2. Prioritize critical violations for immediate cleanup
3. Apply "rules not stories" principle consistently
4. Set up linting rules to prevent future verbosity creep
5. Document concise writing guidelines in `/dev.md`

---

**Full Report**: `/root/travel-planner/docs/clean/prompt-report-20260131-191742.json`
