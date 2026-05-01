# RedNote - Search Tool

Search RedNote (小红书/Xiaohongshu) for Chinese UGC travel content.

## MCP Tools

### Tool 1: rednote_search_notes

**MCP Tool Name**: `mcp__rednote__search_notes`

**Purpose**: Search for RedNote notes (posts) by keyword to discover authentic Chinese travel recommendations, reviews, and guides.

**Parameters**:
- `keywords` (required): Search keywords (Chinese recommended)
  - Examples: "北京旅游", "上海美食", "成都景点"
  - Can use English but results will be limited
- `limit` (optional): Number of results to return (default: 10, max: 50)
  - Recommended: 10-20 for most searches
  - Use 30-50 for comprehensive research

**Returns**:
- Array of notes, each containing:
  - `title` (标题) - Note title
  - `author` (作者) - Author name
  - `content` (内容) - Full note content with details
  - `likes` (点赞) - Like count
  - `comments` (评论) - Comment count  
  - `link` (链接) - URL to original note
  - Rich content including:
    - Restaurant/attraction recommendations with addresses
    - Personal experiences and tips
    - Photos and visual guides
    - Budget estimates and pricing info
    - Local insights from Chinese travelers

**Example Usage**:

Find Beijing food recommendations:
```python
result = call_tool("mcp__rednote__search_notes", {
    "keywords": "北京美食",
    "limit": 10
})
```

Find Shanghai hidden attractions:
```python
result = call_tool("mcp__rednote__search_notes", {
    "keywords": "上海小众景点",
    "limit": 20
})
```

**Best Practices**:
- Use Chinese keywords for best results
- Add modifiers: "推荐" (recommendations), "攻略" (guide), "必去" (must-visit)
- Combine location + category: "成都火锅", "杭州西湖"
- Check multiple notes (5-10) for consensus
- Verify locations with Gaode Maps or Google Maps

**Content Types**:
- Restaurant reviews with specific dishes
- 3-day itinerary guides
- Shopping district recommendations
- Hidden gems and local favorites
- Budget breakdowns and cost estimates
- Seasonal travel tips

**Data Quality**:
- ✅ Authentic user-generated content
- ✅ Current information (recent posts)
- ✅ Visual content (photos, videos)
- ✅ Local Chinese perspectives
- ⚠️ Subjective opinions (verify with multiple sources)
- ⚠️ May include sponsored content

**Requirements**:
- RedNote MCP server must be initialized: `rednote-mcp init`
- Cookies stored at `~/.mcp/rednote/cookies.json`
- xvfb required for headless browser in CLI environments
- Playwright chromium-1208 browser installed

**Use Cases**:
- Finding authentic local restaurants
- Discovering hidden attractions
- Getting real budget estimates
- Understanding Chinese travel culture
- Cross-referencing with official POI data

**Complements**:
- Google Maps - Structured POI data, international
- Gaode Maps - Official POI data, China domestic
- Duffel Flights - Flight bookings
- Airbnb - Accommodation options
