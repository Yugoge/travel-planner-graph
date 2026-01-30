---
name: google-maps
description: |
  Search places, compute routes, and lookup weather using Google Maps Grounding Lite MCP.
  Use when user needs to find locations, calculate travel routes, or check weather data.
  Provides real-time place search, route planning, and weather lookups.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Google Maps Skill

Provides access to Google Maps Grounding Lite MCP server with three core capabilities: place search, route computation, and weather lookups.

## Prerequisites

MCP server must be configured. This skill wraps the `google-maps` MCP server tools.

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **places** - Search for locations, businesses, and points of interest
   - search_places: Find places by name, category, or location

2. **routing** - Compute travel routes and directions
   - compute_routes: Calculate routes with multiple travel modes

3. **weather** - Lookup current weather data
   - lookup_weather: Get weather information for locations

## Loading Tools

Load categories on demand:

```
/google-maps places   # Loads tools/places.md
/google-maps routing  # Loads tools/routing.md
/google-maps weather  # Loads tools/weather.md
```

## MCP Server Setup

The Google Maps Grounding Lite MCP server must be configured in your MCP settings.

**Configuration** (in MCP config file):
```json
{
  "mcpServers": {
    "google-maps": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-google-maps"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "${GOOGLE_MAPS_API_KEY}"
      }
    }
  }
}
```

**Environment Variables**:
- `GOOGLE_MAPS_API_KEY`: Required. Your Google Maps API key with Places API, Routes API, and Geocoding API enabled.

## Security

- Never hardcode API keys in files
- Use environment variables for credentials
- Configure API key in MCP server config with `${GOOGLE_MAPS_API_KEY}` substitution
- Restrict API key to necessary APIs only (Places, Routes, Geocoding)

## Integration

Configured for agents:
- transportation
- meals
- accommodation
- attractions
- shopping
- entertainment

Usage: `/google-maps [category]`

## Error Handling

- MCP tools may fail if API key is invalid or missing
- Implement retry logic (3 attempts with exponential backoff)
- Fall back to WebSearch if MCP unavailable
- Always document data source (google_maps or web_search)

## Best Practices

1. Load only required tool category to minimize token usage
2. Use specific search queries for better results
3. Verify API quotas and rate limits
4. Cache results when practical
5. Provide fallback to WebSearch for reliability
