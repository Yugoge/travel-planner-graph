---
name: amadeus-flight
description: International flight search using Amadeus GDS
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Amadeus Flight Skill

Search flights worldwide using Amadeus GDS data.

**MCP Server**: `amadeus-mcp-server` (v1.0.0)
**API Coverage**: 4/4 tools (100%)
**API Key**: Requires `AMADEUS_API_KEY` and `AMADEUS_API_SECRET` environment variables

## Available Tools

1. **get_flights** - Search flight offers with comprehensive filters
2. **get_city** - Get city information by IATA code
3. **get_tours_activities** - Search tours and activities at destinations
4. **get_hotels** - Search hotel offers

## How to Use

```bash
cd /root/travel-planner/.claude/skills/amadeus-flight
python3 scripts/search.py search_flights ORIGIN DEST DEPART_DATE RETURN_DATE ADULTS NONSTOP
python3 scripts/pricing.py price_analysis ORIGIN DEST DATE
python3 scripts/details.py flight_details FLIGHT_NUMBER DATE
```

## Examples

**Search Flights**:
```bash
python3 scripts/search.py get_flights PEK CDG 2026-03-15 null 1 false
```

**Price Analysis**:
```bash
python3 scripts/pricing.py price_analysis PEK CDG 2026-03-15
```

Returns JSON with pricing, airlines, duration, stops.
