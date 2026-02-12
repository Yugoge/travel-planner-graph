# QA Feature Comparison Report
## scripts/save-agent-data-template.py vs scripts/load.py + scripts/save.py

**Date:** 2026-02-12
**Request ID:** qa-20260212-191450
**QA Status:** FAIL
**Recommendation:** DO NOT REPLACE template script

---

## Executive Summary

The new scripts `load.py` and `save.py` **DO NOT** fully replace `save-agent-data-template.py` functionality. Critical issues identified:

1. **CRITICAL:** save.py has function signature mismatch with json_io.validate_agent_data()
2. **CRITICAL:** save.py missing example data generation for 8 agent types
3. **MAJOR:** Breaking CLI interface changes (24 references across 8 agent files)
4. **MAJOR:** load.py serves DIFFERENT purpose (reading vs writing) - not a replacement

### Verification Status by Success Criteria

| Criterion | Status | Details |
|-----------|--------|---------|
| All functionality covered | ❌ FAIL | Missing example data, broken validation, incompatible CLI |
| Equivalent error handling | ❌ FAIL | Will fail with TypeError before error handlers reached |
| Support all 8 agents | ⚠️ WARN | load.py explicit support, save.py generic, template has examples |
| json_io integration | ❌ FAIL | save.py function signature mismatch |
| Clear documentation | ✅ PASS | Good docstrings in both scripts |
| Gaps documented | ✅ PASS | All gaps documented in this report |

---

## Feature Comparison Matrix

### Template Script Features

| Feature | Implementation | Status |
|---------|---------------|--------|
| Save agent data with validation | Lines 249-256: save_agent_json() | ✅ Working |
| Example data for 8 agents | Lines 62-193: build_example_data() | ✅ Working |
| Validation toggles | --no-validate, --allow-high-severity | ✅ Working |
| Backup creation | --no-backup flag | ✅ Working |
| json_io integration | Correct usage of save_agent_json() | ✅ Working |
| Error handling | ValidationError, AtomicWriteError, Exception | ✅ Working |
| Educational purpose | Template with extensive docs | ✅ Working |
| CLI interface | --agent-name, --data-file, --trip-dir | ✅ Working |
| Exit codes | 0=success, 1=validation, 2=error | ✅ Documented |

### load.py Features (NEW functionality)

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| Hierarchical access (Level 1) | Lines 92-104: filter_level_1() | Day metadata only |
| Hierarchical access (Level 2) | Lines 107-154: filter_level_2() | POI titles/keys |
| Hierarchical access (Level 3) | Lines 157-197: filter_level_3() | Full data access |
| Batch loading | --agents flag | Multiple agents at once |
| Granular filtering | --day, --poi, --poi-index | Precise data selection |
| Output control | --output, --pretty | File or stdout |
| Agent POI mapping | Lines 55-64: AGENT_POI_KEYS | Explicit 8-agent support |

**Note:** load.py is READ functionality, template is WRITE functionality. Not comparable.

### save.py Features (Attempts to replace template)

| Feature | Implementation | Status |
|---------|---------------|--------|
| Save with validation | Lines 97-148 | ❌ BROKEN (function signature bug) |
| Batch saving | Lines 150-253: save_batch() | ⚠️ Untested (validation broken) |
| Stdin support | Lines 329-331 | ✅ New capability |
| Validation toggles | --no-validate, --allow-high | ✅ Similar to template |
| Backup creation | --no-backup flag | ✅ Similar to template |
| json_io integration | Lines 47-52: imports | ❌ BROKEN (wrong usage) |
| Error handling | Lines 81-95, 142-147 | ❌ Unreachable (TypeError first) |
| Example data | N/A | ❌ MISSING |
| CLI interface | --trip, --agent, --input | ❌ BREAKING CHANGE |
| Exit codes | sys.exit(0|1) | ⚠️ Not documented |

---

## Critical Issues Blocking Replacement

### Issue 1: Function Signature Mismatch (CRITICAL)

**Location:** scripts/save.py:73-78

**Problem:**
```python
# save.py calls with keyword args:
validate_agent_data(
    trip_slug=trip_slug,      # WRONG: function expects 'agent_name' first
    agent_name=agent,         # WRONG: this is second param 'json_data'
    data=data,                # WRONG: this is third param 'trip_dir'
    allow_high_severity=allow_high  # WRONG: param doesn't exist
)
```

**Expected (json_io.py:236-240):**
```python
def validate_agent_data(
    agent_name: str,        # First positional arg
    json_data: dict,        # Second positional arg
    trip_dir: Path          # Third positional arg
) -> Tuple[List[Issue], Dict[str, Any]]:
```

**Impact:** Will raise `TypeError` at runtime when validation is invoked.

**Fix Required:**
```python
envelope = {"agent": agent, "status": "complete", "data": data}
trip_dir = DATA_DIR / trip_slug
validate_agent_data(agent, envelope, trip_dir)
```

### Issue 2: Missing Example Data (CRITICAL)

**Location:** Template lines 49-193 vs save.py (none)

**Problem:** Template provides `build_example_data()` demonstrating data structures for all 8 agents:
- meals
- timeline
- attractions
- entertainment
- transportation
- accommodation
- shopping
- budget

**Impact:** Agents lose reference implementation. Educational value of template is lost.

**Recommendation:** Either add equivalent to save.py or keep template for educational purposes.

### Issue 3: Breaking CLI Changes (MAJOR)

**Location:** All 8 agent documentation files

**Impact Analysis:**
- Files affected: 8 (.claude/agents/*.md)
- References per file: 3
- Total references to update: 24

**CLI Mapping:**

| Template Parameter | save.py Parameter | Breaking? |
|-------------------|-------------------|-----------|
| --agent-name | --agent | ✅ Yes |
| --data-file | --input | ✅ Yes |
| --trip-dir | --trip | ✅ Yes |
| --allow-high-severity | --allow-high | ✅ Yes |
| --no-validate | --no-validate | ❌ No |
| --no-backup | --no-backup | ❌ No |

**Migration Effort:** High - all examples in agent docs need updating.

### Issue 4: Data Envelope Inconsistency (CRITICAL)

**Location:** scripts/save.py:127

**Problem:** Inconsistent handling of data envelope:
- Line 73: Validation expects raw data (no envelope)
- Line 127: save_agent_json() receives data with conditional unwrapping
```python
data=data.get("data") if "data" in data else data,
```

**Impact:** Unclear data contract - will validation receive envelope or raw data?

**Fix Required:** Standardize on one format throughout the script.

---

## Functional Gap Analysis

### Gaps (Features in Template NOT in save.py)

| Gap | Severity | Impact |
|-----|----------|--------|
| Example data generation (build_example_data) | CRITICAL | Agents lose reference implementations |
| Working validation integration | CRITICAL | Core functionality broken |
| Backward-compatible CLI | MAJOR | 24 documentation updates needed |
| Exit code documentation | MEDIUM | Unclear failure modes |
| Educational inline docs | MEDIUM | Reduced learning value |

### Improvements (Features in save.py NOT in template)

| Improvement | Value | Notes |
|-------------|-------|-------|
| Batch save with rollback | HIGH | Atomic multi-agent updates |
| Stdin support | MEDIUM | Better scriptability |
| 4-phase commit process | MEDIUM | Better reliability (when fixed) |
| Emoji status indicators | LOW | Better UX |

### load.py Assessment

**Conclusion:** load.py is **NOT** a replacement for template. It serves a DIFFERENT purpose:
- **Template:** Write/save agent data with validation
- **load.py:** Read agent data with hierarchical access control

**Recommendation:** Keep load.py as complementary NEW functionality.

---

## Backward Compatibility Analysis

### Agent Documentation Impact

**Files requiring updates if template is replaced:**

1. .claude/agents/meals.md (lines 236, 242, 247)
2. .claude/agents/timeline.md (lines 236, 242, 247)
3. .claude/agents/attractions.md (lines 265, 271, 276)
4. .claude/agents/entertainment.md (lines 244, 250, 255)
5. .claude/agents/accommodation.md (lines 281, 287, 292)
6. .claude/agents/shopping.md (lines 243, 249, 254)
7. .claude/agents/transportation.md (lines 241, 247, 252)
8. .claude/agents/budget.md (lines 190, 196, 201)

**Total updates required:** 24 reference updates across 8 files

### Migration Requirements

If template is to be replaced, the following must be completed:

1. ✅ Fix critical bugs in save.py (validation signature, envelope handling)
2. ✅ Add example data generation to save.py OR keep template for education
3. ✅ Update all 24 references in 8 agent documentation files
4. ✅ Document exit codes in save.py --help
5. ✅ Add venv activation to usage examples
6. ✅ Test batch save functionality
7. ✅ Verify stdin pipe workflows
8. ✅ Create migration guide for agents

---

## Test Results

### CLI Help Test

| Script | Test | Result |
|--------|------|--------|
| load.py --help | Syntax | ✅ Pass |
| save.py --help | Syntax | ✅ Pass |
| template --help | Syntax | ✅ Pass |
| load.py --help | Examples clear | ✅ Pass |
| save.py --help | Examples clear | ✅ Pass |
| template --help | Exit codes documented | ✅ Pass |

### Functional Test

| Script | Test | Result | Details |
|--------|------|--------|---------|
| load.py | Level 3 load | ✅ Pass | Successfully loaded meals.json |
| save.py | Validation call | ❌ Fail | Would raise TypeError |
| template | json_io integration | ✅ Pass | Correct function usage |

### Integration Test

| Test | Result | Evidence |
|------|--------|----------|
| json_io library usage | ❌ Fail | save.py line 73-78 wrong signature |
| All 8 agents supported | ⚠️ Partial | load.py yes, save.py generic, template examples |
| Error handling | ❌ Fail | TypeError before handlers reached |
| Validation enforcement | ❌ Fail | Broken validation call |

---

## Code Quality Findings

### Critical Issues (Blocks Release)

1. **Function signature mismatch** (save.py:73-78)
   - Severity: CRITICAL
   - Category: api-compatibility
   - Fix: Match json_io.validate_agent_data() signature

2. **Data envelope inconsistency** (save.py:127)
   - Severity: CRITICAL
   - Category: data-transformation
   - Fix: Standardize envelope handling

3. **Missing example data** (save.py overall)
   - Severity: CRITICAL
   - Category: functionality-gap
   - Fix: Add build_example_data() or keep template

### Major Issues (Should Fix)

1. **Breaking CLI changes** (save.py:278-283)
   - Severity: MAJOR
   - Category: backward-compatibility
   - Fix: Maintain compatibility or provide migration

2. **No exit code docs** (save.py:1-35)
   - Severity: MEDIUM
   - Category: documentation
   - Fix: Document in module docstring

### Minor Issues (Can Fix Later)

1. **No venv in examples** (all scripts)
   - Severity: MINOR
   - Category: venv-usage
   - Fix: Add 'source venv/bin/activate && ' prefix

---

## Recommendations

### Primary Recommendation: DO NOT REPLACE

**Reasons:**
1. save.py has critical bugs preventing functionality
2. Template serves educational purpose (example data for 8 agents)
3. Breaking changes require high migration effort (24 updates)
4. load.py is complementary, not replacement

### Suggested Path Forward

**Option 1: Keep All Three (RECOMMENDED)**
- **Template:** Educational reference with example data structures
- **load.py:** Production tool for hierarchical data reading
- **save.py:** Production tool for batch saves (after fixing bugs)

**Benefits:**
- Clear purpose separation
- Minimal migration effort
- Agents have reference implementations

**Option 2: Replace Template (NOT RECOMMENDED)**
- Fix all critical bugs in save.py
- Add build_example_data() to save.py
- Update 24 references across 8 files
- Provide migration guide

**Benefits:**
- Single save interface
- Reduced script count

**Drawbacks:**
- High migration effort
- Risk of breaking agent workflows
- Loss of educational clarity

### Immediate Actions Required

If proceeding with replacement:

1. **MUST FIX:** Validation function signature (save.py:73-78)
2. **MUST FIX:** Data envelope handling (save.py:127)
3. **MUST ADD:** Example data generation or keep template
4. **MUST UPDATE:** 24 references in 8 agent files
5. **SHOULD ADD:** Exit code documentation
6. **SHOULD ADD:** venv activation in examples

---

## Conclusion

The verification shows that scripts/save-agent-data-template.py **CANNOT** be replaced by load.py + save.py in their current state due to:

- **3 critical bugs** blocking functionality
- **2 major issues** requiring significant migration
- **1 minor issue** affecting documentation

**Final Assessment:**
- **Functional equivalence:** ❌ NO
- **Quality equivalence:** ❌ NO
- **Ready for replacement:** ❌ NO
- **Iteration needed:** ✅ YES

**QA Status:** FAIL
**Release Recommendation:** REJECT replacement

---

## Appendix: Detailed Code References

### Template Script Quality Assessment
- **Lines 1-36:** Excellent documentation with usage examples and exit codes
- **Lines 49-193:** Comprehensive example data for all 8 agent types
- **Lines 249-256:** Correct usage of save_agent_json()
- **Lines 265-278:** Robust error handling with clear remediation advice
- **Overall:** High-quality reference implementation

### save.py Quality Assessment
- **Lines 1-35:** Good documentation but missing exit codes
- **Lines 47-52:** Correct imports from json_io
- **Lines 73-78:** ❌ CRITICAL BUG - wrong function signature
- **Lines 127:** ❌ CRITICAL BUG - inconsistent envelope handling
- **Lines 150-253:** Good batch save design (untested due to validation bug)
- **Overall:** Good design, critical implementation bugs

### load.py Quality Assessment
- **Lines 1-43:** Excellent documentation of 3-level access model
- **Lines 55-64:** Explicit agent support via AGENT_POI_KEYS
- **Lines 79-89:** Direct JSON loading (appropriate for read-only)
- **Lines 92-197:** Well-structured filtering logic for 3 levels
- **Overall:** High-quality implementation of NEW functionality

---

**Report Generated:** 2026-02-12T19:28:00Z
**QA Agent:** claude-sonnet-4-5
**Verification Duration:** ~45 minutes
**Confidence Level:** Very High
