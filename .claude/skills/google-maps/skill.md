---
name: google-maps
description: Google Maps integration for places, routing, geocoding, distance matrix, elevation, and place details
allowed-tools: [Bash, Read]
model: inherit
user-invocable: true
---

# Google Maps Skill

International mapping and location services using Google Maps API via MCP server.

**MCP Server**: `@modelcontextprotocol/server-google-maps` (v0.6.2)
**API Coverage**: 7/7 tools (100%)

## Available Tools

1. **maps_search_places** - Search for places
2. **maps_directions** - Get directions between points
3. **maps_geocode** - Convert address to coordinates
4. **maps_reverse_geocode** - Convert coordinates to address
5. **maps_place_details** - Get detailed place information
6. **maps_distance_matrix** - Calculate distances between multiple origins/destinations
7. **maps_elevation** - Get elevation data for locations

## How to Use

Execute scripts from skill directory:
```bash
cd /root/travel-planner/.claude/skills/google-maps
source /root/.claude/venv/bin/activate && python3 scripts/<script_name>.py <arguments>
```

**Requires**: `GOOGLE_MAPS_API_KEY` environment variable

## Scripts

### 1. Place Search (places.py)

Search for places using text queries.

```bash
# Basic search
source /root/.claude/venv/bin/activate && python3 scripts/places.py "restaurants in Paris" 5

# With location bias
source /root/.claude/venv/bin/activate && python3 scripts/places.py "coffee shops" 10 "48.8566,2.3522"
```

### 2. Directions (routing.py)

Get directions between two points.

```bash
# Driving (default)
source /root/.claude/venv/bin/activate && python3 scripts/routing.py "New York, NY" "Boston, MA"

# Transit
source /root/.claude/venv/bin/activate && python3 scripts/routing.py "San Francisco" "Los Angeles" transit

# Walking
source /root/.claude/venv/bin/activate && python3 scripts/routing.py "Times Square" "Central Park" walking
```

**Modes**: `driving` (default), `walking`, `bicycling`, `transit`

### 3. Geocoding (geocoding.py)

Convert addresses to coordinates or vice versa.

```bash
# Address to coordinates
source /root/.claude/venv/bin/activate && python3 scripts/geocoding.py geocode "Eiffel Tower, Paris"

# Coordinates to address
source /root/.claude/venv/bin/activate && python3 scripts/geocoding.py reverse 48.8584 2.2945
```

### 4. Place Details (place_details.py)

Get detailed information about a place using place_id.

```bash
source /root/.claude/venv/bin/activate && python3 scripts/place_details.py ChIJN1t_tDeuEmsRUsoyG83frY4
```

Returns: name, address, phone, website, rating, reviews, opening hours

### 5. Distance Matrix (distance_matrix.py)

Calculate travel distances/times between multiple origins and destinations.

```bash
# Single origin/destination
source /root/.claude/venv/bin/activate && python3 scripts/distance_matrix.py "San Francisco" "Seattle"

# Multiple origins and destinations
source /root/.claude/venv/bin/activate && python3 scripts/distance_matrix.py "SF,LA" "Seattle,Portland" transit
```

### 6. Elevation (elevation.py)

Get elevation data for coordinates.

```bash
# Single location
source /root/.claude/venv/bin/activate && python3 scripts/elevation.py 39.7391536,-104.9847034

# Multiple locations
source /root/.claude/venv/bin/activate && python3 scripts/elevation.py 39.7391536,-104.9847034 36.1699,-115.1398
```

## Output Format

All scripts output:
- **stdout**: Human-readable formatted text
- **stderr**: Raw JSON for programmatic use

## Error Handling

All scripts check for `GOOGLE_MAPS_API_KEY` and return structured errors:
```json
{
  "error": "GOOGLE_MAPS_API_KEY environment variable not set",
  "solution": "Set GOOGLE_MAPS_API_KEY environment variable with your API key"
}
```

## Tool Name Verification

Tool names verified against actual MCP server source code (v0.6.2):
- ✅ All 7 tools match source code definitions
- ✅ Parameter names match API expectations
- ✅ No assumed tool names (like gaode-maps BUG-002)
