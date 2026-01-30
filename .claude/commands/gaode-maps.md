---
description: "Gaode Maps integration for route planning, POI search, and geocoding in China"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# Gaode Maps Skill

Access Gaode Maps (高德地图) API via MCP server for accurate route planning, POI search, and location services in China.

## Quick Start

**No MCP server configuration required**. This skill uses Python scripts that communicate with Gaode Maps MCP server via npx.

**Usage**:
```bash
# Geocoding
python3 .claude/commands/gaode-maps/scripts/geocoding.py geocode "北京市朝阳区" "北京"
python3 .claude/commands/gaode-maps/scripts/geocoding.py regeocode "116.481488,39.990464"

# Routing
python3 .claude/commands/gaode-maps/scripts/routing.py driving "北京市" "上海市"
python3 .claude/commands/gaode-maps/scripts/routing.py transit "重庆市" "成都市" "重庆" "成都"

# POI Search
python3 .claude/commands/gaode-maps/scripts/poi_search.py keyword "火锅" "重庆"
python3 .claude/commands/gaode-maps/scripts/poi_search.py nearby "104.065735,30.659462" "餐厅" "" 500

# Utilities
python3 .claude/commands/gaode-maps/scripts/utilities.py weather "成都" "all"
python3 .claude/commands/gaode-maps/scripts/utilities.py distance "116.481488,39.990464" "121.473701,31.230416" 1
```

## Script Categories

This skill provides Python scripts for direct execution:

1. **geocoding.py** - Location conversion
   - `geocode` - Address to coordinates
   - `regeocode` - Coordinates to address
   - `ip_location` - IP-based location

2. **routing.py** - Inter-city and intra-city routes
   - `driving` - Driving routes with traffic
   - `transit` - Public transit routes
   - `walking` - Walking routes
   - `cycling` - Cycling routes

3. **poi_search.py** - Find points of interest
   - `keyword` - Keyword search
   - `nearby` - Nearby search
   - `detail` - POI details

4. **utilities.py** - Additional services
   - `weather` - Weather information
   - `distance` - Distance measurement

## Script Execution

All scripts are located in `.claude/commands/gaode-maps/scripts/` and can be executed directly:

```bash
# Full path execution
python3 /root/travel-planner/.claude/commands/gaode-maps/scripts/geocoding.py geocode "北京市"

# Relative path execution (from project root)
python3 .claude/commands/gaode-maps/scripts/routing.py driving "北京" "上海"
```

## Coordinate System

**Important**: Gaode Maps uses GCJ-02 coordinate system (China-specific offset from WGS-84).
- Input: Addresses or Chinese location names
- Output: GCJ-02 coordinates (for China) or WGS-84 (international)
- Don't manually convert coordinates

## Error Handling

Scripts implement automatic retry logic with exponential backoff.

**Transient errors** (automatically retried up to 3 times):
- Network timeouts
- Rate limits (429)
- Server errors (5xx)

**Permanent errors** (fail immediately, no retry):
- Invalid credentials (401)
- Forbidden (403)
- Invalid parameters (400)
- Not found (404)

**Exit codes**:
- `0` - Success
- `1` - Error (check stderr for details)

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
