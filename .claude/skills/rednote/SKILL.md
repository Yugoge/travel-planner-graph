---
name: rednote
description: |
  RedNote (小红书/Xiaohongshu) integration for searching Chinese UGC travel content.
  Use for discovering authentic reviews, recommendations, and guides for Chinese destinations.
  Provides keyword search and content access for notes about attractions, restaurants, shopping, and activities.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# RedNote Skill

RedNote (小红书/Xiaohongshu) is China's premier lifestyle and social commerce platform with rich user-generated travel content including reviews, recommendations, photo guides, and authentic experiences from Chinese travelers.

**MCP Server**: `rednote-mcp` (npm based)
**API Coverage**: 3/3 tools (100%)
**Authentication**: Cookie-based (manual login via `rednote-mcp init`)
**Content Language**: Primarily Chinese with some English
**Coverage**: Focused on Chinese destinations and Chinese travelers' global experiences

## When to Use This Skill

**Use RedNote for:**
- Chinese domestic travel (authentic local perspectives)
- Restaurant and food recommendations in China
- Hidden gems and insider tips from Chinese travelers
- Shopping and product recommendations
- Visual travel guides and photo inspiration
- Cultural insights and local customs
- Budget travel tips from locals

**Complementary to:**
- Google Maps (for international locations and navigation)
- Gaode Maps (for Chinese mapping and POI details)
- Duffel Flights (for flight booking)
- Airbnb (for accommodation booking)

## Available MCP Tools

RedNote MCP provides 4 tools for searching and accessing content:

1. **mcp__rednote__search_notes** - Search notes by keyword
2. **mcp__rednote__get_note_content** - Get note content via URL
3. **mcp__rednote__get_note_comments** - Get comments from note URL
4. **mcp__rednote__login** - Manual authentication (prefer CLI `rednote-mcp init`)

All tools are invoked directly as MCP tools (no Python scripts needed).

## Tool Details

### 1. Search Notes by Keyword

**Tool**: `mcp__rednote__search_notes`

Search RedNote content by keyword for travel-related information.

**Parameters**:
- `keywords` (required): 搜索关键词 (Search keyword, Chinese recommended)
- `limit` (optional): 返回结果数量限制 (Result limit, default: 10)

**Returns**:
- List of notes with:
  - Note ID and URL
  - Title and description
  - Author information
  - Like count, comment count, share count
  - Cover image URL
  - Note type (video/image/text)

**Example usage**:
```javascript
// Search for Beijing attractions (top 20 results)
mcp__rednote__search_notes({
  keywords: "北京必去景点",
  limit: 20
})

// Search for Shanghai restaurants (default 10 results)
mcp__rednote__search_notes({
  keywords: "上海美食推荐"
})

// Search for Hangzhou travel guide (top 5 results)
mcp__rednote__search_notes({
  keywords: "杭州旅游攻略",
  limit: 5
})
```

**Best practices**:
- Use Chinese keywords for better results (e.g., "北京" not "Beijing")
- Add modifiers like "推荐" (recommend), "攻略" (guide), "必去" (must-visit)
- Set `limit` to 20-50 for comprehensive coverage
- Start with limit=10 for quick exploration
- Use multiple keyword variations for thorough research

### 2. Get Note Content by URL

**Tool**: `mcp__rednote__get_note_content`

Retrieve detailed content from a specific RedNote post.

**Parameters**:
- `url` (required): 笔记 URL (RedNote note URL - xhslink.com or xiaohongshu.com)

**Returns**:
- Complete note details:
  - Full text content
  - All images and videos
  - Author profile
  - Engagement metrics
  - Tags and categories
  - Location information

**Example usage**:
```javascript
// IMPORTANT: Use the full URL from search_notes results (includes xsec_token)
// Get from search_notes result:
const notes = mcp__rednote__search_notes({ keywords: "成都美食", limit: 10 })
const fullUrl = notes[0].url  // Contains xsec_token parameter

// Then use the complete URL:
mcp__rednote__get_note_content({
  url: fullUrl  // e.g., "https://www.xiaohongshu.com/explore/65a1b2c3?xsec_token=..."
})

// Also supports short links (will auto-redirect):
mcp__rednote__get_note_content({
  url: "https://xhslink.com/abc123"
})
```

**Important Notes**:
- ⚠️ **Always use the complete URL from search_notes results** (includes xsec_token for authentication)
- URLs without xsec_token may timeout or return 404 errors
- The MCP server handles URL redirection automatically
- Typical timeout: 30 seconds (may fail for very slow network)

**Use cases**:
- Extract detailed recommendations from popular posts
- Get full photo galleries for visual reference
- Read complete travel guides and itineraries
- Verify restaurant/attraction details from multiple sources

### 3. Get Comments by URL

**Tool**: `mcp__rednote__get_note_comments`

Retrieve comments from a RedNote post.

**Parameters**:
- `url` (required): 笔记 URL (RedNote note URL)

**Returns**:
- List of comments with:
  - Author name
  - Comment content
  - Like count
  - Timestamp

**Example usage**:
```javascript
// Get comments from popular post
mcp__rednote__get_note_comments({
  url: "https://www.xiaohongshu.com/explore/65a1b2c3d4e5f6789"
})
```

**Use cases**:
- Read user feedback and Q&A
- Verify restaurant/attraction quality from comments
- Find additional tips from community
- Check recent visitor experiences

### 4. Login (Manual Authentication)

**Tool**: `mcp__rednote__login`

Programmatic authentication with RedNote account.

**Parameters**: None

**Returns**: Login success status

**Example usage**:
```javascript
// Trigger interactive login (browser will open)
mcp__rednote__login()
```

**Important**:
- **Prefer CLI**: Use `rednote-mcp init` command for initial setup
- This tool is for programmatic re-authentication scenarios
- Opens browser for interactive login
- Cookies saved to `~/.mcp/rednote/cookies.json`

## MCP Server Setup

### Prerequisites

- **Node.js**: Version 16 or higher
- **npm**: Version 7 or higher
- **Playwright**: Auto-installed with rednote-mcp

### Installation

**1. Install globally via npm**:
```bash
npm install -g rednote-mcp
```

**2. Initialize authentication** (manual login required):
```bash
rednote-mcp init
```

This launches a browser for you to:
1. Log in to RedNote with your account
2. Complete any verification (phone/SMS)
3. Cookies are saved to `~/.mcp/rednote/cookies.json`

**3. Configure MCP server** in Claude Desktop:

Edit `~/.config/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "rednote": {
      "command": "rednote-mcp",
      "args": []
    }
  }
}
```

**4. Restart Claude Desktop** to activate the MCP server.

### Authentication Notes

- **Cookie-based authentication**: RedNote uses browser cookies for API access
- **Manual login required**: Cannot be automated due to security measures
- **Cookie expiration**: Cookies may expire periodically, requiring re-authentication
- **Cookie location**: `~/.mcp/rednote/cookies.json` (outside git repository)
- **No hardcoded credentials**: All authentication handled by MCP server

### Troubleshooting

**Issue**: "Authentication failed" or "Invalid cookies"
- **Solution**: Run `rednote-mcp init` again to refresh cookies

**Issue**: "MCP server not responding"
- **Check**: Node.js version (must be ≥16)
- **Check**: MCP server configuration in Claude Desktop config
- **Restart**: Claude Desktop application

**Issue**: "No search results"
- **Try**: Different keywords (use Chinese characters)
- **Try**: Different sort types
- **Check**: Account has access (new accounts may have restrictions)

## How to Use

### Workflow Pattern

**Step 1: Search for relevant content**
```javascript
mcp__rednote__search_notes({
  keyword: "西安旅游三天",
  sort_type: "popularity_descending"
})
```

**Step 2: Parse search results**
- Review titles and descriptions
- Check engagement metrics (likes, comments)
- Identify most relevant posts
- Extract note URLs

**Step 3: Get detailed content**
```javascript
mcp__rednote__get_note_by_url({
  note_url: "https://www.xiaohongshu.com/explore/..."
})
```

**Step 4: Extract actionable information**
- Restaurant names and locations
- Attraction recommendations
- Budget estimates
- Practical tips and warnings

**Step 5: Verify and cross-reference**
- Compare multiple posts for consistency
- Cross-check with Gaode Maps for locations
- Verify current operating status

### Integration with Agents

**Configured for agents**:
- attractions (landmark and sightseeing recommendations)
- meals (restaurant and food discovery)
- shopping (market and product recommendations)
- entertainment (nightlife and activity suggestions)

**Usage in agents**:
```markdown
# In attractions agent
# Search RedNote for hidden gems
mcp__rednote__search_notes({
  keyword: "北京小众景点",
  sort_type: "popularity_descending"
})

# In meals agent
# Find authentic local restaurants
mcp__rednote__search_notes({
  keyword: "成都本地人推荐美食"
})

# In shopping agent
# Discover local markets
mcp__rednote__search_notes({
  keyword: "上海购物必去"
})

# In entertainment agent
# Find nightlife recommendations
mcp__rednote__search_notes({
  keyword: "深圳酒吧推荐"
})
```

## Effective Search Keywords

### Attraction Keywords
- "城市名 + 必去景点" (must-visit attractions)
- "城市名 + 小众景点" (hidden gems)
- "城市名 + 拍照圣地" (photo spots)
- "城市名 + 一日游" (day trip)
- "城市名 + 旅游攻略" (travel guide)

### Restaurant Keywords
- "城市名 + 美食推荐" (food recommendations)
- "城市名 + 本地人推荐" (local recommendations)
- "城市名 + 网红餐厅" (popular restaurants)
- "城市名 + 特色小吃" (local snacks)
- "菜系名 + 城市名" (cuisine + city)

### Shopping Keywords
- "城市名 + 购物" (shopping)
- "城市名 + 特产" (local specialties)
- "城市名 + 市场" (markets)
- "城市名 + 商场推荐" (mall recommendations)

### Entertainment Keywords
- "城市名 + 酒吧" (bars)
- "城市名 + 夜生活" (nightlife)
- "城市名 + 演出" (performances)
- "城市名 + KTV推荐" (karaoke)

## Data Quality Considerations

### Strengths
- **Authentic perspectives**: Real user experiences from Chinese travelers
- **Visual content**: Rich photo and video guides
- **Current information**: Recent posts reflect latest conditions
- **Local insights**: Chinese locals share insider tips
- **Budget options**: Many posts focus on affordable travel

### Limitations
- **Language barrier**: Primarily Chinese content (translation may be needed)
- **Subjectivity**: User-generated content varies in quality
- **No official data**: Not a source for business hours or official pricing
- **Trends over facts**: Popular content may prioritize aesthetics over practicality
- **Verification needed**: Always cross-reference with official sources

### Best Practices
1. **Use multiple sources**: Compare 3-5 posts for consensus
2. **Check post dates**: Prefer content from last 6 months
3. **Verify with maps**: Confirm locations using Gaode Maps or Google Maps
4. **Cross-reference**: Match with official website or contact info
5. **Consider engagement**: Higher likes/comments often indicate reliability
6. **Look for details**: Posts with specific prices, hours, and addresses are more reliable

## Security

**CRITICAL - Authentication Security**:
- Cookies stored in `~/.mcp/rednote/cookies.json` (user's home directory)
- Cookie file is outside git repository
- Never commit cookie files to version control
- Use environment variables for CI/CD (not applicable for personal use)
- Re-authenticate if cookies are compromised

## Examples

**Example workflows** available in `examples/` directory:
- `search-attractions.md` - Finding attraction recommendations
- `search-restaurants.md` - Discovering local restaurants
- `content-extraction.md` - Extracting detailed information from notes

## Quick Reference

**Common workflows**:

1. **Find hidden attractions in Chinese city**:
   - Use: `search_notes` with keyword "城市名小众景点"
   - Sort: "popularity_descending"
   - Parse: Top 5-10 results for consensus

2. **Discover authentic restaurants**:
   - Use: `search_notes` with keyword "城市名本地人推荐美食"
   - Filter: Posts with photos and detailed descriptions
   - Verify: Cross-check location with Gaode Maps

3. **Get detailed travel guide**:
   - Search: "城市名旅游攻略"
   - Identify: Most popular comprehensive guide
   - Use: `get_note_by_url` to extract full content
   - Parse: Itinerary, budgets, tips

4. **Find shopping recommendations**:
   - Search: "城市名购物" or "城市名特产"
   - Focus: Posts with specific store names and locations
   - Verify: Operating status via maps or web search

## Rate Limits and Usage

- **No official rate limits documented**: Use responsibly
- **Recommended**: Limit to 10-20 searches per planning session
- **Pagination**: Don't request more than 5 pages per keyword
- **Concurrent requests**: Avoid rapid-fire requests (may trigger blocks)
- **Cache results**: Save search results to avoid repeated queries

## Support

- Official site: https://www.xiaohongshu.com/
- MCP repository: https://github.com/iFurySt/RedNote-MCP
- npm package: https://www.npmjs.com/package/rednote-mcp

---

**Progressive Disclosure**: This overview is ~600 tokens. Tool details provided inline for immediate access.
