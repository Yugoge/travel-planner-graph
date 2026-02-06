---
name: duffel-flights
description: Global flight search via Duffel API with real-time pricing and availability
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Duffel Flights Skill

Search for flights worldwide with real-time pricing, availability, and booking information via Duffel's comprehensive airline API.

**MCP Server**: `flights-mcp` (Python based)
**API Coverage**: 3/3 tools (100%)
**API Key**: Requires `DUFFEL_API_KEY` environment variable
**Coverage**: Global airlines and routes

## Available Tools

1. **search_flights** - Search for one-way or round-trip flights
2. **get_offer_details** - Get detailed information about a specific flight offer
3. **search_multi_city** - Search for multi-city itineraries

## How to Use

Execute scripts from skill directory:
```bash
cd /root/travel-planner/.claude/skills/duffel-flights
source /root/.claude/venv/bin/activate && python3 scripts/<script_name>.py <arguments>
```

**Requires**: `DUFFEL_API_KEY` environment variable must be set.

## Scripts

### 1. Search Flights (search_flights.py)

Search for one-way or round-trip flights.

```bash
# One-way flight
source /root/.claude/venv/bin/activate && python3 scripts/search_flights.py JFK LAX 2026-03-15

# Round-trip flight
source /root/.claude/venv/bin/activate && python3 scripts/search_flights.py JFK LAX 2026-03-15 \
  --type round_trip \
  --return-date 2026-03-22

# Business class for 2 passengers
source /root/.claude/venv/bin/activate && python3 scripts/search_flights.py LHR CDG 2026-04-01 \
  --cabin-class business \
  --adults 2 \
  --max-connections 0
```

**Parameters**:
- `origin`: Origin airport IATA code (e.g., JFK, LAX, LHR)
- `destination`: Destination airport IATA code
- `departure_date`: Departure date (YYYY-MM-DD)
- `--type`: Flight type (one_way, round_trip, multi_city) - default: one_way
- `--return-date`: Return date for round-trip (YYYY-MM-DD)
- `--adults`: Number of adult passengers (default: 1)
- `--cabin-class`: economy, premium_economy, business, first (default: economy)
- `--max-connections`: Maximum connections (default: 2, use 0 for direct only)

**Returns**:
- Request ID for tracking
- List of flight offers with:
  - Offer ID (for booking)
  - Price (amount and currency)
  - Flight details per slice (outbound/return)
  - Departure/arrival times
  - Duration
  - Carrier information
  - Number of stops
  - Connection details (if applicable)

### 2. Offer Details (get_offer_details.py)

Get comprehensive details about a specific flight offer.

```bash
source /root/.claude/venv/bin/activate && python3 scripts/get_offer_details.py off_12345abcdef
```

**Parameters**:
- `offer_id`: Flight offer ID from search results

**Returns**:
- Complete offer details including:
  - Full pricing breakdown
  - Baggage allowances
  - Fare conditions
  - Passenger details
  - Booking requirements
  - Cancellation policies

### 3. Multi-City Search (search_multi_city.py)

Search for complex multi-city itineraries.

```bash
# 3-city trip
source /root/.claude/venv/bin/activate && python3 scripts/search_multi_city.py \
  --segment JFK LAX 2026-03-01 \
  --segment LAX SFO 2026-03-05 \
  --segment SFO JFK 2026-03-10 \
  --adults 2 \
  --cabin-class economy

# Business trip with multiple stops
source /root/.claude/venv/bin/activate && python3 scripts/search_multi_city.py \
  --segment LHR CDG 2026-04-15 \
  --segment CDG FRA 2026-04-18 \
  --segment FRA AMS 2026-04-22 \
  --segment AMS LHR 2026-04-25 \
  --cabin-class business \
  --max-connections 1
```

**Parameters**:
- `--segment`: Flight segment (can be repeated): ORIGIN DEST DATE
- `--adults`: Number of adult passengers (default: 1)
- `--cabin-class`: economy, premium_economy, business, first (default: economy)
- `--max-connections`: Maximum connections per segment (default: 2)

**Returns**: Same format as search_flights with all segments included

## Cabin Classes

- **economy**: Standard economy class
- **premium_economy**: Enhanced economy with more legroom
- **business**: Business class
- **first**: First class (where available)

## IATA Airport Codes

Common examples:
- **JFK**: New York JFK
- **LAX**: Los Angeles
- **LHR**: London Heathrow
- **CDG**: Paris Charles de Gaulle
- **FRA**: Frankfurt
- **NRT**: Tokyo Narita
- **SYD**: Sydney
- **DXB**: Dubai

Use standard 3-letter IATA codes for all airports.

## Output Format

All scripts output:
- **stdout**: JSON formatted data
- **stderr**: Error messages

JSON structure includes:
```json
{
  "request_id": "req_abc123",
  "offers": [
    {
      "offer_id": "off_xyz789",
      "price": {
        "amount": "450.00",
        "currency": "USD"
      },
      "slices": [
        {
          "origin": "JFK",
          "destination": "LAX",
          "departure": "2026-03-15T08:00:00",
          "arrival": "2026-03-15T11:30:00",
          "duration": "PT5H30M",
          "carrier": "United Airlines",
          "stops": 0,
          "stops_description": "Non-stop"
        }
      ]
    }
  ]
}
```

## Error Handling

Common errors:
- **Missing API key**: Set `DUFFEL_API_KEY` environment variable
- **Invalid airport code**: Use valid IATA 3-letter codes
- **No availability**: Try different dates or routes
- **API timeout**: Reduce max_connections or try simpler search

Scripts return:
- **Exit 0**: Success
- **Exit 1**: API error, invalid parameters, or network failure

## API Key Setup

```bash
# Set environment variable
export DUFFEL_API_KEY="your_api_key_here"

# Or add to .env file
echo "DUFFEL_API_KEY=your_api_key_here" >> .env
```

Get API key from: https://duffel.com/

### Test API Key

**API Key**: Available from Duffel (https://duffel.com/) - add to `.env` file

**Test Status**: ❌ **MCP Server Installation Issues**

**Test Date**: 2026-01-30

**Issue**: The `flights-mcp` Python package installs successfully but fails to execute due to Python import errors:
```python
Traceback (most recent call last):
  File "/usr/local/bin/flights-mcp", line 5, in <module>
    from flights import main
  File "/usr/local/lib/python3.12/dist-packages/flights/__init__.py", line 3, in <module>
    from . import server
```

**Workaround Options**:
1. **Recommended**: Configure MCP directly in Claude Desktop (bypass Python wrapper)
   - Add to `~/.config/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "duffel-flights": {
         "command": "flights-mcp",
         "env": {
           "DUFFEL_API_KEY": "${DUFFEL_API_KEY}"
         }
       }
     }
   }
   ```
   Note: Set `DUFFEL_API_KEY` in your `.env` file (see `.env.example` for template)
2. **Alternative**: Use Google Maps + WebSearch for flight research instead
3. **Advanced**: Debug package dependencies with maintainer

**See Also**: `/root/travel-planner/API-KEY-MCP-TEST-RESULTS.md` for detailed test report

## Use Cases

### Compare Flight Options

```bash
# Search and compare prices
source /root/.claude/venv/bin/activate && python3 scripts/search_flights.py SFO NYC 2026-05-01 --type round_trip --return-date 2026-05-08
```

### Book Direct Flights Only

```bash
# No connections
source /root/.claude/venv/bin/activate && python3 scripts/search_flights.py LAX HNL 2026-06-15 --max-connections 0
```

### Plan Multi-City Tour

```bash
# European tour
source /root/.claude/venv/bin/activate && python3 scripts/search_multi_city.py \
  --segment LHR CDG 2026-07-01 \
  --segment CDG ROM 2026-07-05 \
  --segment ROM BCN 2026-07-10 \
  --segment BCN LHR 2026-07-15
```

### Get Booking Details

```bash
# After search, get full offer details for booking
source /root/.claude/venv/bin/activate && python3 scripts/get_offer_details.py off_12345
```

## Technical Notes

- **MCP Type**: Python based (direct command execution)
- **Server Command**: `flights-mcp`
- **Protocol**: JSON-RPC 2.0 over stdio
- **Data Source**: Duffel API (aggregated from multiple airlines)
- **Real-time**: Live pricing and availability
- **Rate Limiting**: Subject to Duffel API limits
- **Timeout**: 15s for standard searches, 30s for multi-city

## Tool Name Verification

Tool names verified against actual MCP server source code:
- All 3 tools match source code definitions
- Parameter names match API expectations
- No assumed tool names
