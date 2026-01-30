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

Access Google Maps Grounding Lite MCP server via Python scripts for place search, route computation, and weather lookups. Supports international locations worldwide.

## Quick Start

**Prerequisites**: GOOGLE_MAPS_API_KEY environment variable must be set.

**Usage**:
```bash
# Search for places
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "restaurants in San Francisco"

# Compute routes
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py "New York" "Boston" TRANSIT

# Lookup weather
python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "Tokyo, Japan"
```

## Script Execution

This skill provides executable Python scripts that communicate with Google Maps MCP server via JSON-RPC 2.0 over stdio.

### 1. Places Search (`scripts/places.py`)

Search for locations, businesses, and points of interest.

**Usage**:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py <query> [max_results] [location_bias]
```

**Examples**:
```bash
# Basic search
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "coffee shops in Paris"

# Limit results
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "hotels in London" 10

# With location bias (lat,lng)
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "restaurants" 5 "37.7749,-122.4194"
```

**Returns**: Place names, addresses, ratings, types, and coordinates.

### 2. Route Computation (`scripts/routing.py`)

Compute travel routes between locations with multiple travel modes.

**Usage**:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py <origin> <destination> [travel_mode] [waypoints]
```

**Travel Modes**: DRIVE (default), WALK, BICYCLE, TRANSIT

**Examples**:
```bash
# Driving route
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py "San Francisco, CA" "Los Angeles, CA"

# Transit route
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py "Paris" "Lyon" TRANSIT

# Walking route
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py "Times Square" "Central Park" WALK

# Route with waypoints
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py "Berlin" "Munich" DRIVE "Frankfurt,Stuttgart"
```

**Returns**: Distance, duration, route steps, and polyline data.

### 3. Weather Lookup (`scripts/weather.py`)

Get current weather information for any location.

**Usage**:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py <location>
```

**Examples**:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "San Francisco, CA"
python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "Paris, France"
python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "Tokyo, Japan"
```

**Returns**: Temperature, conditions, humidity, wind, pressure, and visibility.

## Environment Setup

**Required**: Google Maps API key with Places API, Routes API, and Geocoding API enabled.

**Set environment variable**:
```bash
export GOOGLE_MAPS_API_KEY="your-api-key-here"
```

**Get API Key**: https://console.cloud.google.com/google/maps-apis/

## Script Architecture

All scripts use the base `mcp_client.py` module which handles:
- MCP server launch via npx
- JSON-RPC 2.0 protocol communication
- Error handling with retry logic (3 attempts)
- Response parsing and formatting

**No WebSearch fallback**: Scripts connect directly to Google Maps MCP server. If API key is missing or invalid, scripts return clear error messages.

## Error Handling

**Transient errors** (automatic retry with exponential backoff):
- Network timeouts
- Rate limits
- Server errors (5xx)

**Permanent errors** (no retry):
- Invalid API key (401)
- Missing API key
- Invalid parameters (400)
- Not found (404)

**Error messages include**:
- Clear description of the issue
- Solution or next steps
- Original request parameters

## Security

**IMPORTANT**: Never hardcode API keys in files.

- Use environment variables for credentials
- Set `GOOGLE_MAPS_API_KEY` before running scripts
- Restrict API key to necessary APIs only (Places, Routes, Geocoding)
- Add API key restrictions (HTTP referrers, IP addresses)

## Integration

Configured for agents:
- transportation (routing, weather)
- meals (places)
- accommodation (places)
- attractions (places, routing)
- shopping (places)
- entertainment (places, routing)

**Agent Usage Pattern**:
1. Agent receives user request
2. Agent executes appropriate script via Bash tool
3. Script launches MCP server and makes JSON-RPC call
4. Script returns parsed result
5. Agent uses result to answer user query

## Rate Limits

- Google Maps API free tier: varies by API
- Monitor usage at: https://console.cloud.google.com/google/maps-apis/
- Scripts implement automatic retry with backoff for rate limits

## Output Format

**Stdout**: Human-readable formatted output
**Stderr**: Raw JSON output for programmatic use

Example:
```bash
# Human-readable output to stdout
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "restaurants in Paris"

# Capture JSON output for parsing
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "restaurants in Paris" 2>/tmp/result.json
```

## Best Practices

1. Always set GOOGLE_MAPS_API_KEY environment variable before running scripts
2. Use specific search queries for better results
3. Limit max_results to avoid excessive API usage
4. Cache results when practical
5. Use appropriate travel mode for route computation
6. Parse JSON output (stderr) for programmatic integration
