---
name: eventbrite
description: Event discovery and ticketing via Eventbrite API
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Eventbrite Skill

Discover events, concerts, conferences, and activities worldwide.

**MCP Server**: `@mseep/eventbrite-mcp` (v1.0.1)
**API Coverage**: 4/4 tools (100%)
**API Key**: Requires `EVENTBRITE_API_KEY` environment variable

## Available Tools

1. **search_events** - Search for events by query, location, category, date
2. **get_event** - Get detailed information about a specific event
3. **get_categories** - Get list of all Eventbrite event categories
4. **get_venue** - Get venue details and information

## How to Use

Execute scripts from skill directory:
```bash
cd /root/travel-planner/.claude/skills/eventbrite
python3 scripts/<script_name>.py <arguments>
```

**Requires**: `EVENTBRITE_API_KEY` environment variable

## Scripts

### 1. Search Events (search.py)

Search for events with filters.

```bash
# Basic search
python3 scripts/search.py "concerts in New York"

# With location and date filters
python3 scripts/search.py "tech conferences" --location "San Francisco" --start-date 2026-03-01

# Filter by category
python3 scripts/search.py "music events" --category 103 --location "London"
```

### 2. Event Details (details.py)

Get comprehensive event information.

```bash
python3 scripts/details.py 123456789
```

**Returns**: Name, description, start/end time, venue, organizer, pricing, capacity

### 3. Get Categories (categories.py)

List all available event categories.

```bash
python3 scripts/categories.py
```

**Returns**: Category IDs and names for filtering searches

### 4. Venue Details (venue.py)

Get venue information.

```bash
python3 scripts/venue.py 987654321
```

**Returns**: Address, capacity, amenities, accessibility information

## Output Format

All scripts output JSON to stdout, errors to stderr.

## Tool Name Verification

Tool names verified against actual MCP server source code (v1.0.1):
- All 4 tools match source code definitions
- Parameter names match API expectations
- No assumed tool names
