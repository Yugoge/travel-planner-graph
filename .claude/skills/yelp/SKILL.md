---
name: yelp
description: |
  Search restaurants and dining options using Yelp Fusion AI MCP.
  Use when researching breakfast, lunch, dinner options with ratings, reviews, pricing, and booking information.
  Provides verified user ratings, review counts, price levels, cuisine categories, opening hours, and location data.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Yelp Restaurant Search

Search and discover restaurants using Yelp Fusion AI data. Provides comprehensive dining information with verified ratings, reviews, pricing, and booking details.

## When to Use

Invoke this skill when:
- Researching breakfast, lunch, or dinner options
- Finding restaurants by cuisine type or dietary needs
- Getting verified user ratings and review counts
- Checking restaurant pricing, hours, and location
- Filtering by budget, rating, or distance
- Planning meals around activities or accommodation

## Prerequisites

Yelp Fusion AI MCP server must be configured with valid API key.

**Security**: API key configured in MCP server config (never hardcoded in files).

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **search** - Restaurant search and discovery
   - Search restaurants by natural language or filters
   - Get detailed business information
   - Search by cuisine category
   - Filter by rating, price, dietary needs, location

## Loading Tools

Load search tools on demand using Read tool:

```
# Load restaurant search tools
Read /root/travel-planner/.claude/skills/yelp/tools/search.md
```

**Pattern**: After loading, invoke MCP tools following the tool definitions.

## MCP Server Setup

Configure in MCP settings file:

```json
{
  "mcpServers": {
    "yelp": {
      "command": "npx",
      "args": ["-y", "@yelp/yelp-mcp-server"],
      "env": {
        "YELP_API_KEY": "${YELP_API_KEY}"
      }
    }
  }
}
```

**Get API Key**:
1. Register at https://www.yelp.com/developers
2. Create app in Yelp Fusion portal
3. Copy API Key
4. Store in environment variable (never hardcode)

**Rate Limits**: Free tier provides 5,000 API calls/day

## Integration

**Configured for agents**:
- meals

**Invocation**:
- Manual: `/yelp search`
- Automatic: Meals agent invokes when researching restaurants

## Error Handling

**Retry Logic**: 3 attempts with exponential backoff (1s, 2s, 4s)

**Fallback Strategy**: If Yelp unavailable, use WebSearch

**Error Types**:
- 401 Unauthorized: Check API key configuration
- 429 Rate limit: Wait and retry with backoff
- 400 Bad request: Validate search parameters
- 404 Not found: Business ID invalid or removed
- 5xx Server error: Retry with backoff

## Response Structure

Yelp tools return structured JSON with:
- `name`: Restaurant name
- `location`: Full address
- `rating`: User rating (1-5 scale)
- `review_count`: Number of reviews
- `price`: Price level ($, $$, $$$, $$$$)
- `categories`: Cuisine types and tags
- `hours`: Operating hours
- `url`: Yelp page URL
- `coordinates`: Latitude and longitude
- `phone`: Contact number
- `transactions`: Delivery, pickup, reservation options

## Data Quality

**Yelp advantages**:
- Verified user ratings and review counts
- Real-time operating hours
- Accurate pricing indicators
- Cuisine categories and dietary tags
- Location coordinates for distance calculations
- Booking and reservation information
- Worldwide coverage

**When to use WebSearch instead**:
- Yelp MCP unavailable or returning errors
- Need very recent information (within 24 hours)
- Searching for very new restaurants (opened <1 week)
- Need official restaurant website or menu details

## Best Practices

1. **Search Strategy**:
   - Use natural language for broad search
   - Filter by minimum rating (≥3.5 recommended)
   - Filter by minimum review count (≥20 recommended)
   - Consider price level relative to budget
   - Check distance from accommodation or activities

2. **Quality Standards**:
   - Minimum rating: 3.5 stars
   - Minimum reviews: 20 reviews
   - Location convenience: <2km from activity or accommodation
   - Operating hours match meal time
   - Price aligns with budget constraints

3. **Dietary Restrictions**:
   - Search by category for dietary needs
   - Vegetarian: "vegetarian", "vegan"
   - Halal: "halal"
   - Kosher: "kosher"
   - Gluten-free: filter reviews or use WebSearch for details

4. **Budget Optimization**:
   - $ = under $10 per person
   - $$ = $11-30 per person
   - $$$ = $31-60 per person
   - $$$$ = over $61 per person
   - Allocate: 15% breakfast, 30% lunch, 40% dinner of daily meal budget

5. **Variety and Balance**:
   - Track used restaurants across days
   - Avoid repeating cuisine types on consecutive days
   - Mix price levels throughout trip
   - Balance local and international options

## Examples

See usage examples in `examples/` directory:
- `restaurant-search.md` - Complete meal planning workflow

## Security

- Never hardcode API keys in any files
- API key stored in MCP server environment variables
- Credentials managed at MCP server level, not in skill code
- No sensitive data in logs or output files

## Support

**Documentation**: https://github.com/Yelp/yelp-mcp
**Yelp Fusion API**: https://www.yelp.com/developers/documentation/v3
**MCP Protocol**: https://modelcontextprotocol.io/
