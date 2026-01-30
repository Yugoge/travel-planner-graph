---
description: "TripAdvisor integration for attraction search, reviews, tours, and activity recommendations"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# TripAdvisor Skill

Access TripAdvisor data via MCP server for attraction discovery, user reviews, ratings, and tour information.

## Quick Start

**Prerequisites**: TripAdvisor MCP server must be configured (see Setup section below).

**Usage**:
```
/tripadvisor [category]    # Load specific tool category
/tripadvisor help          # Show available categories
```

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **attractions** - Search and discover attractions
   - Search attractions by location
   - Get detailed attraction information
   - Filter by rating and type
   - Get business hours and ticket prices

2. **tours** - Find tours and experiences
   - Search tours and activities
   - Get tour details and pricing
   - Filter by duration and category
   - Check availability

## Loading Tool Categories

Load categories on demand to optimize token usage:

```markdown
To search attractions, load: /root/travel-planner/.claude/commands/tripadvisor/tools/attractions.md
To find tours, load: /root/travel-planner/.claude/commands/tripadvisor/tools/tours.md
```

## Data Quality

**TripAdvisor provides**:
- User reviews and ratings (1-5 scale)
- Photos and descriptions
- Price ranges and ticket costs
- Opening hours and best visiting times
- Traveler tips and recommendations
- Tour availability and booking info

**Advantages over generic web search**:
- Verified user reviews
- Accurate pricing information
- Real-time availability
- Community ratings and rankings
- Detailed category filtering

## Error Handling

**Transient errors** (retry with backoff):
- Network timeouts
- Rate limits (429)
- Server errors (5xx)

**Permanent errors** (don't retry):
- Invalid credentials (401)
- Forbidden (403)
- Invalid parameters (400)
- Not found (404)

**Graceful degradation**:
If MCP server unavailable, fall back to WebSearch for attraction information.

## Language Support

- Input: English (primary), location names in local language accepted
- Output: English descriptions and reviews
- Price: Local currency with USD equivalent
- Ratings: Universal 1-5 scale

## MCP Server Setup

**Required**: User must configure TripAdvisor MCP server before using this skill.

### Step 1: Install Apify TripAdvisor Scraper

Register at: https://apify.com/apify/tripadvisor-scraper

### Step 2: Configure MCP Server

**Recommended Method: Apify MCP Server**

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tripadvisor": {
      "command": "npx",
      "args": ["-y", "@apify/tripadvisor-mcp-server"],
      "env": {
        "APIFY_API_TOKEN": "YOUR_APIFY_API_TOKEN"
      }
    }
  }
}
```

**Alternative Method: Direct Apify API**

```json
{
  "mcpServers": {
    "tripadvisor": {
      "url": "https://api.apify.com/v2/acts/apify~tripadvisor-scraper/mcp?token=YOUR_APIFY_API_TOKEN"
    }
  }
}
```

### Step 3: Restart Claude Desktop

Required for MCP server configuration to take effect.

### Verification

This skill assumes MCP tools are available:
- `search_attractions`
- `get_attraction_details`
- `search_tours`
- `get_reviews`

If tools unavailable, skill will report error and suggest fallback to WebSearch.

## Rate Limits

- Free tier: 1,000 API calls/month
- Paid tier: Based on Apify plan
- Monitor usage at: https://console.apify.com/

## Security

**Never hardcode API keys**. Always use:
- MCP server configuration (environment variables)
- Claude Desktop config file
- Project-specific `.env` files (if applicable)

## Examples

See: `/root/travel-planner/.claude/commands/tripadvisor/examples/`

## For Attractions Agent

This skill is configured for the attractions agent. Usage pattern:

1. Invoke `/tripadvisor attractions` to load attraction search tools
2. Use `search_attractions` to find attractions by location
3. Use `get_attraction_details` for detailed information
4. Parse response for ratings, prices, hours, reviews
5. Fall back to WebSearch if MCP unavailable

See `.claude/agents/attractions.md` for integration details.

## For Entertainment Agent

This skill is configured for the entertainment agent. Usage pattern:

1. Invoke `/tripadvisor tours` to load tour search tools
2. Use `search_tours` to find evening entertainment and shows
3. Filter by type (theater, concerts, nightlife tours)
4. Parse response for schedules, pricing, availability
5. Fall back to WebSearch if MCP unavailable

See `.claude/agents/entertainment.md` for integration details.
