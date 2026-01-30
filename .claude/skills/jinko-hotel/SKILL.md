---
name: jinko-hotel
description: |
  Jinko Hotel Booking skill provides access to 2M+ hotels worldwide with real-time pricing, availability, and facility filtering.
  Use when user needs hotel search, pricing comparison, or booking links for accommodations.
  Automatically invoke when planning trips, researching hotels, or finding lodging options.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Jinko Hotel Booking Skill

Access to 2M+ hotels worldwide with real-time pricing, availability, and comprehensive facility filtering via Jinko Hotel Booking MCP server.

## Prerequisites

**MCP Server Required**: Jinko Hotel Booking MCP must be configured in Claude Desktop.

See **MCP Server Setup** section below for configuration instructions.

## Tool Categories

This skill uses **progressive disclosure** to optimize token usage. Load only the tools you need:

### 1. **search** - Hotel Search and Filtering
- `search_hotels` - Search by location, dates, price range, rating
- `filter_by_facilities` - Filter by WiFi, parking, breakfast, pool, gym, etc.
- `search_nearby` - Find hotels near specific POI (landmarks, attractions)

**When to use**: Primary workflow for finding hotels matching user requirements.

### 2. **details** - Hotel Information and Reviews
- `get_hotel_details` - Comprehensive information (amenities, policies, photos)
- `get_room_types` - Room options, pricing, occupancy, bed configuration
- `get_reviews` - Guest reviews with ratings and insights

**When to use**: Deep dive into shortlisted hotels for detailed comparison.

### 3. **booking** - Availability and Booking Links
- `generate_booking_link` - Generate booking URL with pricing preserved
- `check_availability` - Real-time availability and restrictions
- `compare_prices` - Cross-platform price comparison (Booking.com, Expedia, etc.)

**When to use**: Final step to validate availability and generate booking links.

## Loading Tools

Load categories on demand to reduce token usage:

```
/jinko-hotel search   # Load search and filtering tools
/jinko-hotel details  # Load hotel details and reviews
/jinko-hotel booking  # Load booking and availability tools
/jinko-hotel help     # Show all categories
```

**Pattern**: Read `.claude/skills/jinko-hotel/tools/{category}.md` when category is requested.

## MCP Tool Naming

All MCP tools follow this naming convention:
```
mcp__context7_jinko-hotel__<tool-name>
```

Examples:
- `mcp__context7_jinko-hotel__search_hotels`
- `mcp__context7_jinko-hotel__filter_by_facilities`
- `mcp__context7_jinko-hotel__get_hotel_details`

## Typical Workflow

1. **Load search tools**: `/jinko-hotel search`
2. **Search hotels**: Call `search_hotels` with location, dates, price range
3. **Filter results**: Call `filter_by_facilities` for required amenities
4. **Load details**: `/jinko-hotel details` (if needed for shortlist)
5. **Get details**: Call `get_hotel_details` for top 2-3 hotels
6. **Load booking**: `/jinko-hotel booking` (for final step)
7. **Check availability**: Call `check_availability` to verify
8. **Generate link**: Call `generate_booking_link` for user

## MCP Server Setup

### Option 1: Streamable HTTP (Recommended)

Add to Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "jinko-hotel": {
      "url": "https://mcp.jinko.so/hotel?key=YOUR_JINKO_API_KEY"
    }
  }
}
```

### Option 2: Node.js I/O

```json
{
  "mcpServers": {
    "jinko-hotel": {
      "command": "npx",
      "args": ["-y", "@jinko/hotel-mcp"],
      "env": {
        "JINKO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**API Key**: Obtain from Jinko Hotel Booking service.

## Security

**CRITICAL**: Never hardcode API keys in skill files.

- API keys managed by MCP server via environment variables
- Store in Claude Desktop config or `.env` files
- Never commit credentials to version control
- Use MCP server environment configuration

## Error Handling

### Transient Errors (Retry with Backoff)
- **429 (Rate Limit)**: Exponential backoff (1s → 2s → 4s)
- **5xx (Server Error)**: Linear backoff (2s → 4s → 6s)

### Permanent Errors (No Retry)
- **400 (Invalid Parameters)**: Fix parameters and report error
- **401 (Unauthorized)**: Check API key configuration
- **403 (Forbidden)**: Verify permissions
- **404 (Not Found)**: Hotel unavailable or invalid ID

### Graceful Degradation
- **MCP Unavailable**: Fall back to WebSearch
- **API Quota Exceeded**: Use cached results or manual search
- **Booking Link Failure**: Provide manual search URL

## Integration

### Configured For Agents
- **accommodation** - Primary agent for hotel search

### Usage in Agents

**Accommodation Agent**:
```markdown
1. Read requirements: location, dates, budget, amenities
2. Invoke /jinko-hotel search
3. Call search_hotels with parameters
4. Call filter_by_facilities for required amenities
5. Select best hotel by rating and price
6. Parse results to accommodation.json format
7. Return complete
```

**Fallback**: If MCP unavailable, use WebSearch for hotel recommendations.

## Performance Optimization

### Parallel API Calls
When searching multiple locations, use parallel calls:

```javascript
// Good (parallel)
const [beijing, chengdu, shanghai] = await Promise.all([
  search_hotels({ location: "Beijing", ... }),
  search_hotels({ location: "Chengdu", ... }),
  search_hotels({ location: "Shanghai", ... })
]);

// Bad (sequential)
const beijing = await search_hotels({ location: "Beijing", ... });
const chengdu = await search_hotels({ location: "Chengdu", ... });
const shanghai = await search_hotels({ location: "Shanghai", ... });
```

### Selective Details Loading
Get details only for top candidates (2-3 hotels), not all results.

## Examples

See `/root/travel-planner/.claude/skills/jinko-hotel/examples/hotel-search.md` for complete multi-city workflow example.

---

**Quick Start**: Invoke `/jinko-hotel search` to begin hotel search workflow.
