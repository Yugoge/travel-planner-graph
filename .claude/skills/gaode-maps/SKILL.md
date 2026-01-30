---
name: gaode-maps
description: |
  Gaode Maps (高德地图/AMap) integration for routing, POI search, and geocoding in China.
  Use when planning travel in mainland China for accurate local data with Chinese addresses.
  Supports transit routes, driving directions, POI search, and coordinate conversion (GCJ-02).
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Gaode Maps Skill

Gaode Maps (高德地图/AMap) provides comprehensive mapping and location services for mainland China, including route planning, POI search, geocoding, and utilities.

## When to Use This Skill

**Use Gaode Maps for:**
- Travel planning within mainland China (more accurate than Google Maps)
- Inter-city transportation research (trains, buses, driving)
- POI search with Chinese addresses (restaurants, hotels, attractions)
- Distance and travel time calculations in China
- Geocoding Chinese addresses to coordinates

**Use Google Maps for:**
- International travel outside China
- Locations in Hong Kong, Macau, Taiwan
- Global routing spanning multiple countries

## Prerequisites

**MCP Server Configuration Required**:
- Package: `@amap/amap-maps-mcp-server`
- API Key: Register at https://console.amap.com/dev/key/app
- Configuration: Add to `~/.config/Claude/claude_desktop_config.json`

See Setup section below for details.

## Tool Categories

This skill uses progressive disclosure to optimize token usage. Load only the categories you need:

### 1. **routing** - Route planning and navigation
   - `driving_route` - Car/taxi routes with traffic data
   - `walking_route` - Pedestrian routes and sidewalks
   - `cycling_route` - Bike routes and bike lanes
   - `transit_route` - Public transportation (bus, subway, train)

### 2. **poi-search** - Point of interest search
   - `poi_search_keyword` - Search by name or category
   - `poi_search_nearby` - Find nearby POIs by coordinates
   - `poi_detail` - Get detailed information about a POI

### 3. **geocoding** - Address and coordinate conversion
   - `geocode` - Convert address to coordinates
   - `reverse_geocode` - Convert coordinates to address
   - `ip_location` - Get location from IP address

### 4. **utilities** - Supporting tools
   - `distance_measure` - Calculate distance between points
   - `weather_info` - Current weather for a location

## Loading Tool Categories

**On-demand loading pattern**:
```markdown
/gaode-maps routing      # Loads tools/routing.md
/gaode-maps poi-search   # Loads tools/poi-search.md
/gaode-maps geocoding    # Loads tools/geocoding.md
/gaode-maps utilities    # Loads tools/utilities.md
```

After loading a category, you can directly invoke the MCP tools using their full names.

## MCP Tool Naming Convention

All Gaode Maps MCP tools follow this pattern:
```
mcp__plugin_amap-maps_amap-maps__<tool-name>
```

Examples:
- `mcp__plugin_amap-maps_amap-maps__driving_route`
- `mcp__plugin_amap-maps_amap-maps__poi_search_keyword`
- `mcp__plugin_amap-maps_amap-maps__geocode`

## MCP Server Setup

### Method 1: Streamable HTTP (Recommended)

**Configuration** (`~/.config/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "amap-maps": {
      "url": "https://mcp.amap.com/mcp?key=YOUR_AMAP_API_KEY"
    }
  }
}
```

**Advantages**:
- Fastest connection
- No Node.js required
- Most reliable

### Method 2: Node.js I/O

**Configuration** (`~/.config/Claude/claude_desktop_config.json`):
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

**Requirements**:
- Node.js runtime installed
- NPM package auto-downloaded on first use

### Getting API Key

1. Register at: https://console.amap.com/dev/key/app
2. Create new application
3. Enable required services (routing, search, geocoding)
4. Copy API key to configuration
5. Restart Claude Desktop

### Rate Limits

| Tier | Daily Calls |
|------|-------------|
| Free | 2,000-3,000 |
| Basic | 300,000 |

Monitor usage: https://console.amap.com/

## Important Considerations

### Coordinate System

Gaode Maps uses **GCJ-02** (China's required coordinate system):
- Different from WGS-84 (GPS standard)
- Different from BD-09 (Baidu Maps)
- Coordinates are offset for national security reasons
- Use Gaode's geocoding tools for conversion

### Language Support

- Accepts both English and Chinese inputs
- API responses are in Chinese (native data)
- POI names and addresses in Chinese characters
- Category codes support English keywords

### Coverage

- **Excellent**: Mainland China cities and rural areas
- **Limited**: Hong Kong, Macau, Taiwan
- **Not supported**: International locations outside Greater China

## Security

**CRITICAL - Never commit credentials**:
- Store API keys in MCP server configuration (user's home directory)
- Never hardcode keys in skill files or scripts
- Configuration file is outside git repository
- Use environment variables for CI/CD

## Integration with Agents

**Configured for agents**:
- transportation (inter-city routes)
- meals (restaurant POI search)
- accommodation (hotel POI search)
- attractions (landmark POI search)
- shopping (market/mall POI search)
- entertainment (venue POI search)

**Usage in agents**:
```markdown
# In transportation agent
/gaode-maps routing
# Then use transit_route or driving_route tools
```

## Error Handling

**Retry Logic**:
- Transient errors: Retry up to 3 times with exponential backoff
- Rate limit errors: Wait and retry after specified delay
- Authentication errors: Check API key configuration
- Invalid parameters: Validate inputs before calling

**Fallback Strategy**:
- If Gaode Maps MCP unavailable: Fall back to WebSearch
- If API returns no results: Try alternative search terms
- If coordinates invalid: Try geocoding address first

## Examples

**Example workflows** available in `examples/` directory:
- `inter-city-route.md` - Planning transportation between cities

## Quick Reference

**Common workflows**:

1. **Search restaurant in Chinese city**:
   - Load: `/gaode-maps poi-search`
   - Use: `poi_search_keyword` with location and keyword
   - Parse: Name, address, rating, phone

2. **Plan inter-city route**:
   - Load: `/gaode-maps routing`
   - Use: `transit_route` with origin and destination
   - Parse: Transit options, duration, cost

3. **Get coordinates for Chinese address**:
   - Load: `/gaode-maps geocoding`
   - Use: `geocode` with address string
   - Parse: Latitude, longitude, formatted address

4. **Calculate distance between cities**:
   - Load: `/gaode-maps utilities`
   - Use: `distance_measure` with two coordinate pairs
   - Parse: Distance in meters, estimated time

## Support

- Official docs: https://lbs.amap.com/api/webservice/summary
- API console: https://console.amap.com/
- MCP package: https://github.com/amap-mcp (if available)

---

**Progressive Disclosure**: This overview is ~800 tokens. Tool details are loaded on demand to save context.
