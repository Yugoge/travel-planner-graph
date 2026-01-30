---
name: tripadvisor
description: |
  Access TripAdvisor data for attractions, tours, activities, and user reviews.
  Use when researching tourist attractions, booking tours, finding activities, or getting traveler reviews.
  Provides verified ratings, pricing, hours, and booking information worldwide.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# TripAdvisor Skill

Access comprehensive TripAdvisor data for attractions, tours, activities, and user reviews worldwide.

## When to Use

Invoke this skill when:
- Researching tourist attractions and landmarks
- Finding tours, activities, and experiences
- Getting verified user reviews and ratings
- Checking attraction hours, prices, and booking requirements
- Comparing activity options by rating and price
- Planning day trips and guided tours

## Prerequisites

TripAdvisor MCP server must be configured with valid API credentials.

**Security**: API keys configured in MCP server config (never hardcoded in files).

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **attractions** - Search and discover attractions
   - Search attractions by location and category
   - Get detailed attraction information
   - Filter by rating, price, and type
   - Access user reviews and photos

2. **tours** - Find tours, activities, and experiences
   - Search tours and activities
   - Get tour details and schedules
   - Check availability and pricing
   - Access booking information

## Loading Tools

Load categories on demand using Read tool:

```
# Load attraction search tools
Read .claude/skills/tripadvisor/tools/attractions.md

# Load tour and activity tools
Read .claude/skills/tripadvisor/tools/tours.md
```

**Pattern**: After loading, invoke MCP tools following the tool definitions.

## MCP Server Setup

Configure in `~/.config/claude/mcp_config.json`:

```json
{
  "mcpServers": {
    "tripadvisor": {
      "command": "npx",
      "args": ["-y", "@apify/tripadvisor-mcp-server"],
      "env": {
        "TRIPADVISOR_API_KEY": "${TRIPADVISOR_API_KEY}"
      }
    }
  }
}
```

**Environment variable**: Set `TRIPADVISOR_API_KEY` in your shell profile.

## Integration

**Configured for agents**:
- attractions
- entertainment

**Invocation**:
- Manual: `/tripadvisor attractions` or `/tripadvisor tours`
- Automatic: Agents invoke when researching attractions or entertainment

## Error Handling

**Retry Logic**: 3 attempts with exponential backoff (1s, 2s, 4s)

**Fallback Strategy**: If TripAdvisor unavailable, use WebSearch

**Error Types**:
- API key invalid: Check MCP server configuration
- Rate limit exceeded: Wait and retry with backoff
- Location not found: Broaden search or use alternate location name
- No results: Adjust search filters or use WebSearch

## Response Structure

All TripAdvisor tools return structured JSON with:
- `name`: Attraction or tour name
- `location`: Address or area
- `rating`: User rating (1-5 scale)
- `reviews_count`: Number of reviews
- `price`: Cost in USD (if applicable)
- `hours`: Operating hours
- `booking_url`: Link to book or learn more
- `traveler_tips`: Verified user recommendations

## Data Quality

**TripAdvisor advantages**:
- Verified user reviews and ratings
- Real-time pricing and availability
- Accurate operating hours
- Booking information and links
- Traveler tips and recommendations
- Worldwide coverage (200+ countries)

**When to use WebSearch instead**:
- TripAdvisor unavailable or returning errors
- Need very recent information (within 24 hours)
- Searching for niche or very new attractions
- Need local government or official source data

## Best Practices

1. **Search Strategy**:
   - Start with broad location search
   - Filter by user ratings (minimum 4.0 recommended)
   - Consider number of reviews (higher = more reliable)
   - Check seasonal availability

2. **Data Validation**:
   - Verify hours for current season
   - Check if advance booking required
   - Confirm pricing is per person or per group
   - Note any age restrictions or requirements

3. **Geographic Clustering**:
   - Group attractions by proximity
   - Minimize travel time between activities
   - Consider transportation options

4. **User Experience**:
   - Include traveler tips in recommendations
   - Note accessibility information if available
   - Highlight unique or must-see features
   - Warn about common issues (crowds, long queues)

## Examples

See usage examples in `examples/` directory:
- `attraction-search.md` - Complete attraction search workflow
- `tour-booking.md` - Tour search and booking flow
- `review-analysis.md` - Analyzing user reviews

## Security

- Never hardcode API keys in any files
- API key stored in MCP server environment variables
- Credentials managed at MCP server level, not in skill code
- No sensitive data in logs or output files

## Support

**Documentation**: https://apify.com/mcp/tripadvisor-mcp-server
**MCP Protocol**: https://modelcontextprotocol.io/
**Issues**: Report MCP server issues to Apify support
