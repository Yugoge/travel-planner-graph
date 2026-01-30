---
description: "Google Maps integration for route planning, POI search, and location services worldwide"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# Google Maps Skill

Access Google Maps Grounding Lite API via MCP server for accurate route planning, POI search, and location services for international destinations.

## Quick Start

**Prerequisites**: Google Maps Grounding Lite MCP server must be configured (see Setup section below).

**Usage**:
```
/google-maps [category]    # Load specific tool category
/google-maps help          # Show available categories
```

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **places** - Search points of interest worldwide
   - Place search by text
   - Nearby place search
   - Place details and reviews
   - Photo retrieval

2. **routing** - Calculate routes between locations
   - Driving routes with traffic
   - Walking routes
   - Transit routes
   - Bicycling routes

3. **weather** - Weather information lookup
   - Current weather conditions
   - Location-based weather

## Loading Tool Categories

Load categories on demand to optimize token usage:

```markdown
To search for hotels, load: /root/travel-planner/.claude/commands/google-maps/tools/places.md
To plan a driving route, load: /root/travel-planner/.claude/commands/google-maps/tools/routing.md
To check weather, load: /root/travel-planner/.claude/commands/google-maps/tools/weather.md
```

## Coordinate System

**Important**: Google Maps uses WGS-84 coordinate system (standard GPS coordinates).
- Input: Addresses or location names in any language
- Output: WGS-84 coordinates (latitude, longitude)
- Compatible with international GPS devices and services

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
If MCP server unavailable, fall back to WebSearch for location information.

## Language Support

- Input: Any language (English, Chinese, Spanish, French, etc.)
- Output: Localized based on request or English default
- Distance/time: Numeric values with units (universal)

## MCP Server Setup

**Required**: User must configure Google Maps Grounding Lite MCP server before using this skill.

### Step 1: Get API Key

Register at: https://console.cloud.google.com/
Enable Google Maps Platform APIs

### Step 2: Configure MCP Server

**Recommended Method: Streamable HTTP**

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-maps": {
      "url": "https://mapstools.googleapis.com/mcp",
      "headers": {
        "X-Goog-Api-Key": "YOUR_GOOGLE_MAPS_API_KEY"
      }
    }
  }
}
```

**Alternative Method: Environment Variable**

Set environment variable and configure MCP client:

```bash
export GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"
```

### Step 3: Restart Claude Desktop

Required for MCP server configuration to take effect.

### Verification

This skill assumes MCP tools are available:
- `search_places`
- `compute_routes`
- `lookup_weather`

If tools unavailable, skill will report error and suggest fallback to WebSearch.

## Rate Limits

- Free tier: Varies by API
- Paid tier: Based on Google Cloud pricing
- Monitor usage at: https://console.cloud.google.com/

## Security

**Never hardcode API keys**. Always use:
- MCP server configuration (headers)
- Environment variables
- Google Cloud Secret Manager (for production)

## Examples

See: `/root/travel-planner/.claude/commands/google-maps/examples/`

## For Agent Integration

This skill is configured for multiple agents:

**Transportation Agent**:
1. Invoke `/google-maps routing` to load route planning tools
2. Use `compute_routes` for inter-city transportation
3. Parse response for distance, duration, cost estimates
4. Fall back to WebSearch if MCP unavailable

**Meals Agent**:
1. Invoke `/google-maps places` to load POI search tools
2. Use `search_places` to find restaurants
3. Filter by rating, price, distance
4. Get details and reviews

**Accommodation Agent**:
1. Invoke `/google-maps places` to load POI search tools
2. Use `search_places` to find hotels and lodging
3. Filter by amenities, price range, location
4. Get photos and reviews

**Attractions Agent**:
1. Invoke `/google-maps places` to load POI search tools
2. Use `search_places` to find tourist attractions
3. Filter by type, rating, opening hours
4. Get place details and photos

**Shopping Agent**:
1. Invoke `/google-maps places` to load POI search tools
2. Use `search_places` to find shopping centers and markets
3. Filter by type, location, opening hours
4. Get reviews and photos

**Entertainment Agent**:
1. Invoke `/google-maps places` to load POI search tools
2. Use `search_places` to find venues and entertainment
3. Filter by type, time, location
4. Get event information and reviews

See respective agent files (`.claude/agents/*.md`) for integration details.
