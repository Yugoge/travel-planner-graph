# MCP Package Errors - Detailed Report

**Date**: 2026-01-30
**Issue**: 3 out of 6 MCP packages return 404 errors from npm registry

---

## Error Summary

All 3 packages return identical error:
```
npm error code E404
npm error 404 Not Found - GET https://registry.npmjs.org/<package> - Not found
npm error 404 The requested resource could not be found or you do not have permission to access it.
```

---

## 1. TripAdvisor MCP Server

### Attempted Package
```
@tripadvisor/tripadvisor-mcp-server
```

### NPM Error
```bash
npm view @tripadvisor/tripadvisor-mcp-server
# npm error code E404
# npm error 404 Not Found - GET https://registry.npmjs.org/@tripadvisor%2ftripadvisor-mcp-server
```

### Current Usage in Codebase
**File**: `.claude/skills/tripadvisor/scripts/attractions.py`
```python
with MCPClient("@tripadvisor/tripadvisor-mcp-server", env_vars) as client:
```

**Files**:
- `scripts/attractions.py` (2 calls)
- `scripts/tours.py` (likely 2 calls)
- `scripts/mcp_client.py` (client definition)

### Search for Alternatives
```bash
npm search tripadvisor mcp
# Result: No results (empty)
```

**Conclusion**: No TripAdvisor MCP package exists on npm

---

## 2. Yelp MCP Server

### Attempted Package
```
@yelp/yelp-mcp-server
```

### NPM Error
```bash
npm view @yelp/yelp-mcp-server
# npm error code E404
# npm error 404 Not Found - GET https://registry.npmjs.org/@yelp%2fyelp-mcp-server
```

### Current Usage in Codebase
**File**: `.claude/skills/yelp/scripts/search.py`
```python
with MCPClient('@yelp/yelp-mcp-server', {'YELP_API_KEY': api_key}) as client:
```

**Files**:
- `scripts/search.py` (3 calls)
- `scripts/details.py` (likely 1 call)
- `scripts/mcp_client.py` (client definition)

### Search for Alternatives
```bash
npm search yelp mcp
# Result: No results (empty)
```

**Conclusion**: No Yelp MCP package exists on npm

---

## 3. Jinko Hotel Booking MCP Server

### Attempted Package
```
@jinko/hotel-booking-mcp-server
```

### NPM Error
```bash
npm view @jinko/hotel-booking-mcp-server
# npm error code E404
# npm error 404 Not Found - GET https://registry.npmjs.org/@jinko%2fhotel-booking-mcp-server
```

### Current Usage in Codebase
**File**: `.claude/skills/jinko-hotel/scripts/search.py`
```python
with MCPClient(
    package='@jinko/hotel-booking-mcp-server',
    env_vars={'JINKO_API_KEY': api_key}
) as client:
```

**Files**:
- `scripts/search.py` (2 calls)
- `scripts/details.py` (likely 1 call)
- `scripts/booking.py` (likely 1 call)
- `scripts/mcp_client.py` (client definition)

### Search for Alternatives
```bash
npm search hotel mcp
# Result: No results (empty)
```

**Note**: Dev subagent found `hotel-mcp@1.3.1` but it's completely different:
- Different provider (not Jinko)
- Uses Supabase backend
- Read-only hotel information
- Not a booking service

**Conclusion**: No Jinko/hotel booking MCP package exists on npm

---

## Root Cause Analysis

### Why These Packages Don't Exist

**Hypothesis 1**: Packages were never published
- Skills may have been created based on planned/future MCPs
- MCP servers never completed development
- Publishers abandoned projects

**Hypothesis 2**: Package names were assumed
- Similar to Google Maps BUG (search_places vs maps_search_places)
- Package names were guessed without verification
- No source verification was done during skill creation

**Hypothesis 3**: Private packages
- Might be private npm packages requiring authentication
- However, npm returns 404 (not 403), so unlikely

**Most Likely**: Skills were created with **assumed** package names that never existed.

---

## Impact Analysis

### Files Affected

**TripAdvisor** (4 files):
- `.claude/skills/tripadvisor/SKILL.md`
- `.claude/skills/tripadvisor/scripts/attractions.py`
- `.claude/skills/tripadvisor/scripts/tours.py`
- `.claude/skills/tripadvisor/scripts/mcp_client.py`

**Yelp** (4 files):
- `.claude/skills/yelp/SKILL.md`
- `.claude/skills/yelp/scripts/search.py`
- `.claude/skills/yelp/scripts/details.py`
- `.claude/skills/yelp/scripts/mcp_client.py`

**Jinko Hotel** (5 files):
- `.claude/skills/jinko-hotel/SKILL.md`
- `.claude/skills/jinko-hotel/scripts/search.py`
- `.claude/skills/jinko-hotel/scripts/details.py`
- `.claude/skills/jinko-hotel/scripts/booking.py`
- `.claude/skills/jinko-hotel/scripts/mcp_client.py`

**Total**: 13 files cannot function (all `npx` calls will fail)

---

## Options for Resolution

### Option 1: DELETE Skills (Recommended)
**Action**: Remove all 3 skills completely
**Pros**:
- Clean codebase
- No broken functionality
- Immediate resolution
**Cons**:
- Lose 3 features
- May need alternatives

**Commands**:
```bash
rm -rf .claude/skills/tripadvisor
rm -rf .claude/skills/yelp
rm -rf .claude/skills/jinko-hotel
```

---

### Option 2: Search for Alternative MCP Packages
**Action**: Deep search for similar MCPs on npm
**Pros**:
- Might find working alternatives
- Preserve functionality
**Cons**:
- Time consuming
- Alternatives may not exist
- May have different APIs

**Research needed**:
```bash
# Broader searches
npm search "mcp server" | grep -i trip
npm search "mcp server" | grep -i yelp
npm search "mcp server" | grep -i hotel

# Check GitHub for MCP servers
# Search: "tripadvisor mcp server" site:github.com
# Search: "yelp mcp server" site:github.com
# Search: "hotel booking mcp server" site:github.com
```

---

### Option 3: Build Custom MCP Wrappers
**Action**: Create MCP servers from scratch for these APIs
**Pros**:
- Full control
- Exact features needed
**Cons**:
- ~6 hours per MCP (18 hours total)
- Maintenance burden
- Need API documentation

**APIs to wrap**:
- TripAdvisor Content API
- Yelp Fusion API
- Hotel booking API (e.g., Booking.com, Expedia)

---

### Option 4: Use APIs Directly (No MCP)
**Action**: Replace MCP client with direct API calls
**Pros**:
- No MCP dependency
- Direct control
**Cons**:
- Breaks MCP architecture pattern
- More code in skills
- No MCP benefits (caching, standardization)

**Example** (Yelp):
```python
import requests

def search_yelp(query, location):
    headers = {'Authorization': f'Bearer {YELP_API_KEY}'}
    params = {'term': query, 'location': location}
    response = requests.get('https://api.yelp.com/v3/businesses/search',
                           headers=headers, params=params)
    return response.json()
```

---

## Recommendation

Based on dev subagent analysis:

1. **DELETE** TripAdvisor and Yelp skills
   - No MCP alternatives found
   - Low value for travel planning (can use Google Maps reviews instead)

2. **INVESTIGATE** hotel alternatives:
   - Try `hotel-mcp@1.3.1` (requires Supabase setup)
   - OR search for Booking.com/Expedia MCPs
   - OR delete if no viable alternative

3. **KEEP** working MCPs:
   - ✅ Airbnb (`@openbnb/mcp-server-airbnb`)
   - ✅ Eventbrite (`@mseep/eventbrite-mcp`)
   - ✅ Amadeus Flight (`amadeus-mcp-server` - fixed)

---

## Next Steps for You

Please decide:

1. **TripAdvisor**: DELETE / SEARCH / BUILD / DIRECT ?
2. **Yelp**: DELETE / SEARCH / BUILD / DIRECT ?
3. **Hotel**: DELETE / hotel-mcp / SEARCH / BUILD / DIRECT ?

Once you decide, I will:
- Execute chosen actions
- Update remaining skills
- Generate final verification report
- Hand off to QA for testing

---

**Status**: ⏸️ BLOCKED - Awaiting your decision

---

*Generated with [Claude Code](https://claude.ai/code) via [Happy](https://happy.engineering)*

*Co-Authored-By: Claude <noreply@anthropic.com>*
*Co-Authored-By: Happy <yesreply@happy.engineering>*
