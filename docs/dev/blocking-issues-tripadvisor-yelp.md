# Blocking Issues: TripAdvisor and Yelp MCP Verification

**Date**: 2026-01-30
**Reporter**: Dev Subagent
**Severity**: HIGH - Skills Non-Functional

---

## Executive Summary

After downloading and inspecting actual npm packages, **2 out of 6** claimed MCP packages **DO NOT EXIST** on npm:

1. `@tripadvisor/tripadvisor-mcp-server` - **404 Not Found**
2. `@yelp/yelp-mcp-server` - **404 Not Found**

This means the existing `tripadvisor` and `yelp` skill directories contain scripts that reference non-existent packages.

---

## Issue Details

### 1. TripAdvisor MCP (@tripadvisor/tripadvisor-mcp-server)

**Status**: Package does not exist on npm

**Evidence**:
```bash
$ npm pack @tripadvisor/tripadvisor-mcp-server
npm error 404 Not Found - GET https://registry.npmjs.org/@tripadvisor%2ftripadvisor-mcp-server
npm error 404 The requested resource '@tripadvisor/tripadvisor-mcp-server@*' could not be found
```

**Impact**:
- Skill directory: `.claude/skills/tripadvisor/`
- Scripts affected:
  - `scripts/attractions.py`
  - `scripts/tours.py`
  - `scripts/mcp_client.py`
- All scripts are **non-functional** (will fail when executed)

**Current State**:
- Skill exists but is based on hypothetical/placeholder package name
- No actual MCP server to connect to
- Tools claimed: `search_attractions`, `search_tours` (UNVERIFIED - no source code to inspect)

---

### 2. Yelp MCP (@yelp/yelp-mcp-server)

**Status**: Package does not exist on npm

**Evidence**:
```bash
$ npm pack @yelp/yelp-mcp-server
npm error 404 Not Found - GET https://registry.npmjs.org/@yelp%2fyelp-mcp-server
npm error 404 The requested resource '@yelp/yelp-mcp-server@*' could not be found
```

**Alternative Found**:
- `yelp-fusion` package exists BUT is a regular API client, not an MCP server
- Would require custom MCP wrapper development

**Impact**:
- Skill directory: `.claude/skills/yelp/`
- Scripts affected: (directory appears empty or minimal)
- Skill is **non-functional**

**Current State**:
- Skill exists but has no valid MCP server
- Tools claimed: `search`, `business_details` (UNVERIFIED)

---

## Resolution Options

### Option 1: Delete Non-Functional Skills (RECOMMENDED for immediate cleanup)

**Action**:
```bash
rm -rf .claude/skills/tripadvisor
rm -rf .claude/skills/yelp
```

**Pros**:
- Clean up misleading/broken skills
- Clear signal to user that these don't work
- Prevent accidental usage of non-functional code

**Cons**:
- Lose placeholder code (if it has any value)

---

### Option 2: Search for Alternative MCP Packages

**Action**:
- Search npm for actual TripAdvisor/Yelp MCP servers
- Check GitHub for community-built MCP implementations
- Investigate if official MCPs are in development

**Search Commands**:
```bash
npm search tripadvisor mcp
npm search yelp mcp
npm search travel mcp
npm search tourism mcp
```

**Pros**:
- Might find working alternatives
- Community solutions may exist

**Cons**:
- Time-consuming
- May not find suitable alternatives
- Alternative packages may have different APIs

---

### Option 3: Build Custom MCP Wrappers

**Action**:
- Use TripAdvisor Content API directly (https://tripadvisor-content-api.readme.io/)
- Use Yelp Fusion API directly (https://www.yelp.com/developers/documentation/v3)
- Create custom MCP server wrappers

**Pros**:
- Full control over functionality
- Use official APIs
- Can tailor to exact needs

**Cons**:
- Significant development effort
- Need to maintain custom code
- Requires API keys/authentication setup

**Implementation Estimate**:
- TripAdvisor wrapper: ~4-6 hours
- Yelp wrapper: ~4-6 hours
- Testing and integration: ~2-4 hours
- **Total**: ~10-16 hours development time

---

### Option 4: Use API Clients Directly (No MCP)

**Action**:
- Remove skills from MCP framework
- Create standalone API client scripts
- Use native API endpoints

**Example for Yelp**:
```python
import requests

YELP_API_KEY = os.environ["YELP_API_KEY"]

def search_yelp(term, location):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": term, "location": location}
    response = requests.get(url, headers=headers, params=params)
    return response.json()
```

**Pros**:
- Simple, direct integration
- No MCP complexity
- Works immediately with API keys

**Cons**:
- Lose MCP standardization
- Different pattern from other skills
- Less integration with Claude Desktop

---

## User Decision Required

**Question**: How would you like to proceed?

1. **Delete** tripadvisor and yelp skills (clean slate)
2. **Search** for alternative MCP packages (research phase)
3. **Build** custom MCP wrappers (development phase)
4. **Use** direct API clients without MCP (pragmatic approach)
5. **Wait** for official MCPs to be published (may never happen)

---

## Recommended Immediate Action

**For Immediate Progress**:
1. DELETE non-functional skills to prevent confusion
2. DOCUMENT which services are unavailable
3. PROCEED with verification of working MCPs:
   - ✅ Airbnb (@openbnb/mcp-server-airbnb) - VERIFIED
   - ✅ Eventbrite (@mseep/eventbrite-mcp) - VERIFIED
   - ✅ Amadeus (amadeus-mcp-server) - VERIFIED + FIXED
   - ⚠️ Hotel (hotel-mcp vs jinko-hotel) - NEEDS CLARIFICATION
4. TEST working skills when API keys provided

**After User Decision**:
- Implement chosen approach for TripAdvisor/Yelp
- Complete full skill verification
- Proceed to QA phase

---

## Related Issues

### Hotel MCP Name Mismatch

**Claimed**: `@jinko/hotel-booking-mcp-server`
**Actual**: `hotel-mcp` (completely different provider)

**Issue**:
- hotel-mcp is a read-only info server using Supabase backend
- Requires SUPABASE_URL, SUPABASE_ANON_KEY, DEFAULT_SITE_ID
- NOT a booking service
- 29 tools available (mostly multimedia/translation tools)

**Action Required**: User must clarify if they want:
- A) hotel-mcp (read-only info with 29 tools)
- B) Search for actual jinko hotel package
- C) Different hotel booking MCP

---

## Lesson Learned

**Root Cause**: Context document contained hypothetical/assumed package names without verification.

**Prevention**:
- ALWAYS verify npm package existence before creating skills
- Download and inspect source code FIRST
- Never assume package names match expected patterns (@company/service-mcp-server)
- Check npm registry before skill development

**Process Improvement**:
- Add "verify package exists" step to skill creation checklist
- Require source code inspection before claiming tool coverage
- Document actual vs assumed package names in all contexts

---

## Contact

For questions or decisions, please respond with your choice (1-5 above) or provide alternative direction.

**Next Steps Blocked Until**:
- User decision on TripAdvisor approach
- User decision on Yelp approach
- User clarification on Hotel provider (hotel-mcp vs jinko)
