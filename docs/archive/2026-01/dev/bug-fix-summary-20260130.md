# Gaode Maps MCP Scripts Bug Fix Summary

**Date**: 2026-01-30
**Status**: ✅ COMPLETED
**Priority**: CRITICAL

---

## Executive Summary

Fixed two critical bugs preventing gaode-maps skill scripts from executing. Both issues were protocol/naming mismatches between wrapper scripts and actual MCP server implementation.

**Result**: Scripts now work end-to-end, successfully querying Beijing→Shanghai transit routes (1,468km, 5.75 hours).

---

## Bugs Fixed

### BUG-001: Protocol Error in mcp_client.py
**File**: `.claude/skills/gaode-maps/scripts/mcp_client.py`
**Location**: Line 138
**Issue**: Sent `notifications/initialized` after initialization response
**Error**: `Method not found: notifications/initialized`

**Fix**: Removed the unsupported notification call
```python
# Before (line 138):
self._send_request("notifications/initialized", {})

# After:
# notifications/initialized not required by MCP protocol - removed
```

**Impact**: All script executions were failing immediately after initialization.

---

### BUG-002: Tool Name Mismatches in routing.py
**File**: `.claude/skills/gaode-maps/scripts/routing.py`
**Locations**: Lines 48, 91, 124, 157
**Issue**: Scripts used assumed tool names that don't exist in actual MCP server

**Fixes**:
| Function | Old Name (Wrong) | New Name (Correct) | Line |
|----------|------------------|-------------------|------|
| Transit | `transit_route` | `maps_direction_transit_integrated` | 91 |
| Driving | `driving_route` | `maps_direction_driving` | 48 |
| Walking | `walking_route` | `maps_direction_walking` | 124 |
| Cycling | `cycling_route` | `maps_bicycling` | 157 |

**Impact**: All routing functions were calling non-existent tools.

---

## Validation

### Test Case: Beijing → Shanghai Transit Route
```bash
cd /root/travel-planner/.claude/skills/gaode-maps
python3 scripts/routing.py transit \
  "116.407387,39.904179" \
  "121.473701,31.230416" \
  "北京市" 0
```

**Results**:
- ✅ Script executes without errors
- ✅ Returns valid JSON response
- ✅ Distance: 1,468,020 meters (1,468 km)
- ✅ Duration: 20,700 seconds (5.75 hours)
- ✅ Route: Bus → High-speed Rail (G33) → Subway
- ✅ No "Method not found" errors

### Verification Commands
```bash
# Verify BUG-001 fix (should only find comment)
grep -n 'notifications/initialized' scripts/mcp_client.py

# Verify BUG-002 fix (should find no old names)
grep 'transit_route\|driving_route\|walking_route\|cycling_route' scripts/routing.py | grep call_tool

# Verify new tool names present
grep 'maps_direction_' scripts/routing.py
```

---

## Root Cause Analysis

**Why These Bugs Occurred**:
1. Scripts written with assumed tool names without verifying actual MCP server implementation
2. Assumed `notifications/initialized` was required by MCP protocol (it's not)
3. No automated testing against actual MCP server during development

**How Fixes Address Root Cause**:
- Verified actual tool names through direct JSON-RPC testing
- Removed unnecessary protocol assumptions
- Aligned scripts with actual server behavior

---

## Files Modified

1. `.claude/skills/gaode-maps/scripts/mcp_client.py` - 1 line (protocol fix)
2. `.claude/skills/gaode-maps/scripts/routing.py` - 4 lines (tool name corrections)

**Total Changes**: 5 lines across 2 files

---

## Recommendations

1. **Testing**: Add automated tests that verify tool names against actual MCP server
2. **Documentation**: Document actual MCP server tool names in SKILL.md or reference doc
3. **Validation**: Test other gaode-maps scripts (poi_search.py, geocoding.py) for similar issues

---

## Success Criteria Met

- ✅ mcp_client.py no longer sends notifications/initialized
- ✅ routing.py uses correct tool names matching actual MCP server
- ✅ Beijing to Shanghai transit route query succeeds via routing.py script
- ✅ Script returns valid JSON with distance and duration
- ✅ No 'Method not found' errors during execution

---

## Related Documents

- Context: `docs/dev/skill-bug-fix-context-20260130.json`
- Implementation Report: `docs/dev/bug-fix-implementation-report-20260130.json`
- Test Report: `docs/dev/skill-test-report-20260130.md`
- Architecture: `docs/dev/skill-cleanup-completion-20260130.md`

---

**Fixed by**: Development Agent
**Request ID**: dev-skill-bug-fix-20260130
**QA Status**: Ready for verification
