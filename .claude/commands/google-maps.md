---
description: Google Maps integration for places, routing, geocoding, distance matrix,
  and elevation
allowed-tools: Task, Read, Bash
argument-hint: '[category|help]'
model: inherit
disable-model-invocation: true
uses_scripts:
- .claude/commands/scripts/google-maps/scripts/places.py
- .claude/commands/scripts/google-maps/scripts/routing.py
- .claude/commands/scripts/google-maps/scripts/geocoding.py
dispatches: []
mutates_files: []
---

# Google Maps Skill

International mapping and location services using Google Maps API via MCP server.

## Quick Start

**Usage**:
```bash
# Place search
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/commands/scripts/google-maps/scripts/places.py "restaurants in Paris" 5

# Directions (driving)
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/commands/scripts/google-maps/scripts/routing.py "New York, NY" "Boston, MA"

# Transit directions
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/commands/scripts/google-maps/scripts/routing.py "San Francisco" "Los Angeles" transit

# Geocoding
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/commands/scripts/google-maps/scripts/geocoding.py geocode "Eiffel Tower, Paris"

# Reverse geocoding
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/commands/scripts/google-maps/scripts/geocoding.py reverse 48.8584 2.2945
```

## Available Scripts

All scripts are in `/root/travel-planner/.claude/commands/scripts/google-maps/scripts/` and require `GOOGLE_MAPS_API_KEY` environment variable.

1. **places.py** - Search for places
   - `places.py "<query>" [limit] [location_bias]`
   - Example: `places.py "coffee shops" 10 "48.8566,2.3522"`

2. **routing.py** - Get directions between points
   - `routing.py "<origin>" "<destination>" [mode]`
   - Modes: `driving` (default), `walking`, `bicycling`, `transit`

3. **geocoding.py** - Address/coordinate conversion
   - `geocoding.py geocode "<address>"` - Address to coordinates
   - `geocoding.py reverse <lat> <lng>` - Coordinates to address

4. **place_details.py** - Detailed place information
   - `place_details.py <place_id>`
   - Returns: name, address, phone, website, rating, reviews, hours

5. **distance_matrix.py** - Multi-origin/destination distances
   - `distance_matrix.py "<origins>" "<destinations>" [mode]`
   - Multiple: `distance_matrix.py "SF,LA" "Seattle,Portland" transit`

6. **elevation.py** - Elevation data for coordinates
   - `elevation.py <lat,lng> [<lat,lng> ...]`

## Output Format

- **stdout**: Human-readable formatted text
- **stderr**: Raw JSON for programmatic use

## MCP Tools

1. **maps_search_places** - Search for places
2. **maps_directions** - Get directions between points
3. **maps_geocode** - Convert address to coordinates
4. **maps_reverse_geocode** - Convert coordinates to address
5. **maps_place_details** - Get detailed place information
6. **maps_distance_matrix** - Calculate distances between multiple points
7. **maps_elevation** - Get elevation data

## Error Handling

All scripts check for `GOOGLE_MAPS_API_KEY` and return structured JSON errors with solution hints.

## API Key

Requires `GOOGLE_MAPS_API_KEY` environment variable. Get a key at: https://console.cloud.google.com/
