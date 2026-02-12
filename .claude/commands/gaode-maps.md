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
source /root/.claude/venv/bin/activate && python .claude/skills/gaode-maps/scripts/geocoding.py geocode "北京市朝阳区" "北京"
source /root/.claude/venv/bin/activate && python .claude/skills/gaode-maps/scripts/geocoding.py regeocode "116.481488,39.990464"

# Routing
source /root/.claude/venv/bin/activate && python .claude/skills/gaode-maps/scripts/routing.py driving "北京市" "上海市"
source /root/.claude/venv/bin/activate && python .claude/skills/gaode-maps/scripts/routing.py transit "重庆市" "成都市" "重庆" "成都"

# POI Search
source /root/.claude/venv/bin/activate && python .claude/skills/gaode-maps/scripts/poi_search.py keyword "火锅" "重庆"
source /root/.claude/venv/bin/activate && python .claude/skills/gaode-maps/scripts/poi_search.py nearby "104.065735,30.659462" "餐厅" "" 500

# Utilities
source /root/.claude/venv/bin/activate && python .claude/skills/gaode-maps/scripts/utilities.py weather "成都" "all"
source /root/.claude/venv/bin/activate && python .claude/skills/gaode-maps/scripts/utilities.py distance "116.481488,39.990464" "121.473701,31.230416" 1
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

All scripts are located in `.claude/skills/gaode-maps/scripts/` and can be executed directly:

```bash
# Full path execution
source venv/bin/activate || source .venv/bin/activate && python .claude/skills/gaode-maps/scripts/geocoding.py geocode "北京市"

# Relative path execution (from project root)
source venv/bin/activate || source .venv/bin/activate && python .claude/skills/gaode-maps/scripts/routing.py driving "北京" "上海"
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

## API Key Configuration

Scripts use environment variable `AMAP_MAPS_API_KEY` (defaults to project key if not set).

**Current project key**: `your_api_key_here` (set via `AMAP_MAPS_API_KEY` environment variable)

**To use your own key**:
```bash
export AMAP_MAPS_API_KEY="your_key_here"
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/geocoding.py geocode "北京市"
```

**Get your own API key**: https://console.amap.com/dev/key/app

## Technical Details

**Communication Protocol**: JSON-RPC 2.0 over stdio
**MCP Server**: `@amap/amap-maps-mcp-server` (launched via npx)
**Transport**: Scripts launch MCP server on-demand, communicate via stdin/stdout, and terminate after completion.

**Available MCP tools**:
- `driving_route`, `walking_route`, `cycling_route`, `transit_route`
- `poi_search_keyword`, `poi_search_nearby`, `poi_detail`
- `geocode`, `reverse_geocode`, `ip_location`
- `weather_info`, `distance_measure`

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

1. Execute routing script directly via Bash tool:
   ```bash
   python3 .claude/commands/gaode-maps/scripts/routing.py transit "重庆市" "成都市" "重庆" "成都"
   ```

2. Parse JSON response for distance, duration, cost estimates

3. Save structured data to `transportation.json`

See `.claude/agents/transportation.md` for integration details.

## For Other Agents

**Meals Agent**: Use `poi_search.py` to find restaurants
```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/poi_search.py keyword "火锅" "重庆" "050100" 10
```

**Accommodation Agent**: Use `poi_search.py` for hotel search, `geocoding.py` for address validation
```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/poi_search.py keyword "酒店" "成都" "100000" 20
```

**Attractions Agent**: Use `poi_search.py` to discover attractions, `utilities.py` for distances
```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/poi_search.py keyword "景点" "成都" "110000" 15
```
