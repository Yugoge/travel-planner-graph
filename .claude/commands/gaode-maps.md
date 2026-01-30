---
description: "Gaode Maps integration for route planning, POI search, and geocoding in China"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# Gaode Maps Skill

Access Gaode Maps (高德地图) API via MCP server for accurate route planning, POI search, and location services in China.

## Quick Start

**Prerequisites**: Gaode Maps MCP server must be configured (see Setup section below).

**Usage**:
```
/gaode-maps [category]    # Load specific tool category
/gaode-maps help          # Show available categories
```

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **routing** - Inter-city and intra-city routes
   - Driving routes with traffic
   - Walking routes
   - Cycling routes
   - Public transit routes

2. **poi-search** - Find points of interest
   - Keyword search
   - Nearby search
   - POI details

3. **geocoding** - Location conversion
   - Address to coordinates
   - Coordinates to address
   - IP-based location

4. **utilities** - Additional services
   - Weather information
   - Distance measurement

## Loading Tool Categories

Load categories on demand to optimize token usage:

```markdown
To plan a driving route, load: /root/travel-planner/.claude/commands/gaode-maps/tools/routing.md
To search for hotels, load: /root/travel-planner/.claude/commands/gaode-maps/tools/poi-search.md
To convert addresses, load: /root/travel-planner/.claude/commands/gaode-maps/tools/geocoding.md
To check weather, load: /root/travel-planner/.claude/commands/gaode-maps/tools/utilities.md
```

## Coordinate System

**Important**: Gaode Maps uses GCJ-02 coordinate system (China-specific offset from WGS-84).
- Input: Addresses or Chinese location names
- Output: GCJ-02 coordinates (for China) or WGS-84 (international)
- Don't manually convert coordinates

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
If MCP server unavailable, fall back to WebSearch for route information.

## Language Support

- Input: English or Chinese
- Output: Primarily Chinese (native API responses)
- Distance/time: Numeric values (universal)

## MCP Server Setup

**Required**: User must configure Gaode Maps MCP server before using this skill.

### Step 1: Get API Key

Register at: https://console.amap.com/dev/key/app

### Step 2: Configure MCP Server

**Recommended Method: Streamable HTTP**

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "amap-maps": {
      "url": "https://mcp.amap.com/mcp?key=YOUR_AMAP_API_KEY"
    }
  }
}
```

**Alternative Method: Node.js I/O**

```json
{
  "mcpServers": {
    "amap-maps": {
      "command": "npx",
      "args": ["-y", "@amap/amap-maps-mcp-server"],
      "env": {
        "AMAP_MAPS_API_KEY": "YOUR_AMAP_API_KEY"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

Required for MCP server configuration to take effect.

### Verification

This skill assumes MCP tools are available:
- `driving_route`
- `walking_route`
- `cycling_route`
- `transit_route`
- `poi_search_keyword`
- `poi_search_nearby`
- `poi_detail`
- `geocode`
- `reverse_geocode`
- `ip_location`
- `weather_info`
- `distance_measure`

If tools unavailable, skill will report error and suggest fallback to WebSearch.

## Rate Limits

- Free tier: 2,000-3,000 calls/day
- Basic tier: 300,000 calls/day
- Monitor usage at: https://console.amap.com/

## Security

**Never hardcode API keys**. Always use:
- MCP server configuration (environment variables)
- Claude Desktop config file
- Project-specific `.env` files (if applicable)

## Examples

See: `/root/travel-planner/.claude/commands/gaode-maps/examples/`

## For Transportation Agent

This skill is configured for the transportation agent. Usage pattern:

1. Invoke `/gaode-maps routing` to load route planning tools
2. Use `driving_route` or `transit_route` for inter-city transportation
3. Parse response for distance, duration, cost estimates
4. Fall back to WebSearch if MCP unavailable

See `.claude/agents/transportation.md` for integration details.
