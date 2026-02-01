# Skill Test Report: Beijing Restaurant Search

**Test Date**: 2026-02-01
**Test Objective**: Verify functionality of rednote and google-maps skills for restaurant search in Beijing

---

## Test Results Summary

| Skill | Status | Success Rate | Notes |
|-------|--------|--------------|-------|
| **google-maps** | ✅ WORKING | 100% | Returned 20 high-quality restaurant results |
| **rednote** | ❌ NOT AVAILABLE | 0% | MCP server not connected to CLI environment |

---

## 1. Google Maps Skill

### Status: ✅ WORKING

### Test Command
```bash
cd /root/travel-planner/.claude/skills/google-maps
source /root/.claude/venv/bin/activate
python3 scripts/places.py "restaurants in Beijing" 5
```

### Results
- **Total Results**: 20 restaurants returned
- **Data Quality**: High
- **Response Time**: Fast (~2 seconds)
- **Data Source**: google_maps API

### Sample Results (Top 5)

1. **TRB Hutong**
   - Address: 23 Shatan North Street, Dongcheng, Beijing
   - Rating: 4.6/5.0
   - Location: 39.925275, 116.403539
   - Place ID: ChIJX7PV49hS8DURuT2QxQbm7KU

2. **Jing**
   - Address: 8 Jinyu Hutong, Wangfujing Peninsula Hotel, Dongcheng
   - Rating: 4.5/5.0
   - Location: 39.9150604, 116.4163908
   - Place ID: ChIJF_tJftJS8DURghmTAVtSU_E

3. **Xinrongji**
   - Address: 8 Xinyuan S Rd, Floor 1 Park Hyatt Beijing, Chaoyang
   - Rating: 4.5/5.0
   - Location: 39.94737, 116.45643
   - Place ID: ChIJpUivl4Ss8TURC3ygTskJKgI

4. **Fuchunju**
   - Address: 1 Wangfujing Ave, Floor 3, Raffles Hotel, Dongcheng
   - Rating: 4.6/5.0
   - Location: 39.92385, 116.41008
   - Place ID: ChIJSfS3rtdS8DURubHVcmf9d_g

5. **Maison FLO**
   - Address: 18 Xiaoyun Rd, Chaoyang, Beijing
   - Rating: 5.0/5.0
   - Location: 39.959081, 116.468365
   - Place ID: ChIJMe8ei4qr8TURPrKpVuwidas

### JSON Output Format
```json
{
  "query": "restaurants in Beijing",
  "results": {
    "places": [
      {
        "name": "TRB Hutong",
        "formatted_address": "China, Beijing# 23 Shatan North Street 邮政编码: 100009",
        "location": {"lat": 39.925275, "lng": 116.403539},
        "place_id": "ChIJX7PV49hS8DURuT2QxQbm7KU",
        "rating": 4.6,
        "types": ["restaurant", "food", "point_of_interest", "establishment"]
      }
    ]
  },
  "source": "google_maps"
}
```

### Strengths
- ✅ Comprehensive coverage of Beijing restaurants
- ✅ Accurate coordinates and addresses
- ✅ High-quality establishments (ratings 4.3-5.0)
- ✅ Mix of Chinese and international cuisine
- ✅ Includes both hutong restaurants and hotel dining
- ✅ Fast and reliable API responses
- ✅ Structured JSON output for programmatic use

### Limitations
- ⚠️ Limited to Google Maps indexed establishments
- ⚠️ May miss small local eateries without Google presence
- ⚠️ Does not provide Chinese-language reviews or local insights
- ⚠️ No information about specific dishes or specialties

---

## 2. RedNote Skill

### Status: ❌ NOT AVAILABLE

### Test Command
```bash
/rednote 北京美食
```

### Error
```
Error: No such tool available: mcp__rednote__search_notes
```

### Environment Check

**Installation Status**:
- ✅ rednote-mcp binary installed at `/usr/bin/rednote-mcp`
- ✅ Node.js v20.19.5 (meets requirement ≥16)
- ✅ npm v11.6.2 (meets requirement ≥7)
- ✅ Authentication cookies exist at `~/.mcp/rednote/cookies.json`
- ✅ Cookies updated: Jan 31 19:02 (recent)

**Issue Analysis**:
- ❌ MCP server not connected to Claude CLI environment
- ❌ MCP tools (mcp__rednote__*) not available in tool registry
- ℹ️ RedNote MCP server requires connection to Claude Desktop (not CLI)

### Root Cause
The RedNote MCP server is designed for **Claude Desktop** application, not the **Claude CLI** environment. MCP servers communicate through stdio or HTTP transport configured in `~/.config/Claude/claude_desktop_config.json`, which is only loaded by the desktop application.

### Alternative Solutions

**Option 1: Use Claude Desktop**
- Open Claude Desktop application
- MCP server will auto-connect if configured
- Use natural language to invoke RedNote tools

**Option 2: Create Python Script Wrapper**
- Develop a Python script that directly interfaces with RedNote API
- Use Playwright/Selenium to scrape search results
- Parse HTML/JSON responses programmatically
- Store in `.claude/skills/rednote/scripts/search.py`

**Option 3: Use Web Search Fallback**
- Search RedNote via WebSearch tool: "北京美食 site:xiaohongshu.com"
- Extract note URLs and parse content manually
- Less reliable but doesn't require MCP connection

### Recommendation
For CLI-based agents, recommend implementing **Option 2** (Python script wrapper) to enable programmatic access to RedNote content without MCP dependency.

---

## Comparison: Google Maps vs RedNote (Expected)

| Feature | Google Maps | RedNote |
|---------|-------------|---------|
| **Coverage** | Global, comprehensive | China-focused, UGC |
| **Data Type** | Official listings | User reviews + photos |
| **Language** | English + Chinese | Primarily Chinese |
| **Reliability** | Very high | Moderate (subjective) |
| **Authenticity** | Business info | Real traveler experiences |
| **CLI Access** | ✅ Working | ❌ Desktop only |
| **Best For** | POI search, coordinates | Hidden gems, local insights |

---

## Recommendations for Agents

### For Meals Agent (Beijing)

**Primary Data Source**: Google Maps
- Use for: Restaurant locations, ratings, contact info
- Script: `scripts/places.py "restaurants in [area]" [limit]`
- Reliability: High
- Available in CLI: Yes

**Secondary Data Source**: RedNote (when Desktop available)
- Use for: Local recommendations, hidden gems, specialty dishes
- Tool: `mcp__rednote__search_notes` with keywords "北京美食"
- Reliability: Moderate (needs cross-verification)
- Available in CLI: No (Desktop only)

**Fallback Strategy**:
1. Use Google Maps for initial restaurant list
2. If RedNote unavailable, use WebSearch for "北京 [dish/cuisine] 小红书推荐"
3. Cross-reference results with Gaode Maps for Chinese addresses
4. Verify operating status and hours via phone or official websites

### Integration Pattern

```python
# Recommended workflow for meals agent
def find_restaurants(city, cuisine, limit=10):
    # Step 1: Google Maps for official listings
    google_results = google_maps.search_places(
        query=f"{cuisine} restaurants in {city}",
        limit=limit
    )

    # Step 2: Filter by rating and reviews
    filtered = [r for r in google_results if r['rating'] >= 4.0]

    # Step 3: If RedNote available, enrich with local insights
    if rednote_available():
        rednote_results = rednote.search_notes(
            keywords=f"{city}{cuisine}推荐",
            limit=5
        )
        # Merge recommendations

    # Step 4: Return structured data
    return format_meal_data(filtered)
```

---

## Conclusion

**Google Maps Skill**: Fully functional and recommended for primary use in CLI-based agents. Provides reliable, structured data for restaurant search with global coverage.

**RedNote Skill**: Currently unavailable in CLI environment due to MCP Desktop dependency. Recommended for Desktop-based workflows or implement Python wrapper for CLI access.

**Action Items**:
1. ✅ Use Google Maps as primary data source for meals agent
2. ⚠️ Consider implementing RedNote Python wrapper for CLI compatibility
3. ℹ️ Document MCP limitation in agent documentation
4. 💡 Explore WebSearch as fallback for RedNote-style UGC content

---

**Test Conducted By**: Claude Code (Sonnet 4.5)
**Environment**: Claude CLI on Linux 6.8.0-88-generic
**Working Directory**: /root/travel-planner
