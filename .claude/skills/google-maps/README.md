# Google Maps MCP Script Integration

Python script-based integration for Google Maps Grounding Lite MCP server.

## Overview

This skill provides executable Python scripts that communicate directly with the Google Maps MCP server via JSON-RPC 2.0 over stdio. Scripts are invoked by agents via Bash tool, eliminating the need for MCP tools in Claude's context.

## Architecture

```
Agent → Bash Tool → Python Script → npx → MCP Server → Google Maps API
                                      ↓
                              JSON-RPC 2.0 over stdio
```

**Key Features**:
- No context pollution (MCP tools not loaded into Claude's tool list)
- Progressive disclosure (scripts in subdirectory, loaded on demand)
- Direct MCP communication (no WebSearch fallback)
- Portable (works without Claude Code MCP configuration)

## Directory Structure

```
.claude/skills/google-maps/
├── SKILL.md                    # Main skill documentation with usage
├── scripts/
│   ├── mcp_client.py          # Base MCP client (JSON-RPC 2.0)
│   ├── places.py              # Place search functionality
│   ├── routing.py             # Route computation
│   └── weather.py             # Weather lookups
├── examples/
│   ├── places-search-example.md
│   ├── routing-example.md
│   └── weather-lookup-example.md
└── tools/
    ├── places.md              # Tool documentation (reference)
    ├── routing.md
    └── weather.md
```

## Quick Start

### Prerequisites

1. **Google Maps API Key**: Obtain from https://console.cloud.google.com/google/maps-apis/
2. **Enable APIs**: Places API, Routes API, Geocoding API
3. **Set environment variable**:
   ```bash
   export GOOGLE_MAPS_API_KEY="your-api-key-here"
   ```

### Usage Examples

#### Search Places

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
  "restaurants in San Francisco" 10
```

#### Compute Routes

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York, NY" "Boston, MA" TRANSIT
```

#### Lookup Weather

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py \
  "Tokyo, Japan"
```

## Script Details

### 1. mcp_client.py (Base Client)

**Purpose**: Base MCP client for JSON-RPC 2.0 communication

**Features**:
- Launch MCP server via npx
- JSON-RPC protocol implementation
- Tool listing and invocation
- Retry logic with exponential backoff
- Response parsing and error handling

**Usage**:
```bash
python3 mcp_client.py @modelcontextprotocol/server-google-maps \
  GOOGLE_MAPS_API_KEY=your-key
```

### 2. places.py (Place Search)

**Purpose**: Search for places, businesses, and POIs

**Parameters**:
- `query`: Search query (required)
- `max_results`: Maximum number of results (default: 5)
- `location_bias`: Coordinates for regional bias (optional)

**Returns**:
- Place names, addresses, ratings, types, coordinates

**Usage**:
```bash
python3 places.py "coffee shops in Paris" 10 "48.8566,2.3522"
```

### 3. routing.py (Route Computation)

**Purpose**: Compute travel routes between locations

**Parameters**:
- `origin`: Starting location (required)
- `destination`: Ending location (required)
- `travel_mode`: DRIVE, WALK, BICYCLE, TRANSIT (default: DRIVE)
- `waypoints`: Comma-separated intermediate stops (optional)

**Returns**:
- Distance, duration, route steps, polyline data

**Usage**:
```bash
python3 routing.py "Paris" "Berlin" DRIVE "Brussels,Amsterdam"
```

### 4. weather.py (Weather Lookup)

**Purpose**: Get current weather information

**Parameters**:
- `location`: Location name or address (required)

**Returns**:
- Temperature, conditions, humidity, wind, pressure, visibility

**Usage**:
```bash
python3 weather.py "London, UK"
```

## Output Format

All scripts provide dual output:

**Stdout**: Human-readable formatted text
```
Search: restaurants in San Francisco

1. Gary Danko
   Address: 800 North Point St, San Francisco, CA 94109
   Rating: 4.7
   ...
```

**Stderr**: JSON for programmatic use
```json
{
  "query": "restaurants in San Francisco",
  "results": [...],
  "source": "google_maps"
}
```

## Error Handling

### Transient Errors (Auto-Retry)
- Network timeouts
- Rate limits (429)
- Server errors (5xx)

### Permanent Errors (No Retry)
- Invalid API key (401)
- Missing API key
- Invalid parameters (400)
- Not found (404)

## Agent Integration

Agents execute scripts via Bash tool and parse results:

```markdown
User: "Find restaurants in Paris"

Agent executes:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
  "restaurants in Paris" 5
```

Agent parses JSON output and formats response for user.
```

## Security

**CRITICAL**: Never hardcode API keys

- ✅ Use environment variables: `GOOGLE_MAPS_API_KEY`
- ✅ Configure in shell profile or .env files
- ❌ Never commit API keys to git
- ❌ Never hardcode in scripts or config files

## Performance

- Script startup: ~2 seconds (MCP server launch)
- API call: 1-3 seconds (varies by complexity)
- Total: 3-5 seconds per execution
- Caching recommended for repeated queries

## Rate Limits

- Free tier: Varies by API (check Google Cloud Console)
- Monitor usage: https://console.cloud.google.com/google/maps-apis/
- Scripts implement retry logic for rate limits

## Testing

### Test MCP Connection

```bash
export GOOGLE_MAPS_API_KEY="your-key"
python3 scripts/mcp_client.py @modelcontextprotocol/server-google-maps
```

### Test Place Search

```bash
python3 scripts/places.py "restaurants in San Francisco" 3
```

### Test Routing

```bash
python3 scripts/routing.py "New York" "Boston" TRANSIT
```

### Test Weather

```bash
python3 scripts/weather.py "Paris, France"
```

## Troubleshooting

### Error: GOOGLE_MAPS_API_KEY environment variable not set

**Solution**: Set the environment variable:
```bash
export GOOGLE_MAPS_API_KEY="your-api-key-here"
```

### Error: No response from MCP server

**Possible causes**:
1. npx not installed (install Node.js)
2. MCP package unavailable (check package name)
3. Network connectivity issues

### Error: MCP error: Invalid API key

**Solution**: Verify API key and enabled APIs at Google Cloud Console

## Best Practices

1. **Cache results**: Save JSON output for repeated queries
2. **Limit results**: Use max_results to avoid excessive API usage
3. **Specific queries**: "Italian restaurants in Manhattan" vs "food"
4. **Appropriate modes**: DRIVE for long distances, WALK for nearby
5. **Parse JSON**: Use stderr output for programmatic integration

## Next Steps

- Test scripts with international locations
- Update agent prompts to use script execution
- Remove WebSearch fallback from agent configurations
- Monitor API usage and quotas
- Implement caching for frequently-accessed data

## Documentation

- **SKILL.md**: Main skill documentation with usage examples
- **examples/**: Detailed workflow examples with agent integration
- **tools/**: MCP tool documentation (reference only)

## Support

For issues or questions:
1. Check examples/ directory for workflow patterns
2. Verify API key and enabled APIs
3. Test MCP connection with mcp_client.py
4. Review error messages for specific solutions
