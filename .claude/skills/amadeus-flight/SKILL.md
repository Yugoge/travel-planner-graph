---
name: amadeus-flight
description: |
  Search and analyze flights using Amadeus GDS data.
  Use when user needs international flight search, multi-city itineraries,
  real-time pricing, airline details, or price trend analysis.
  Supports IATA airport codes and provides GDS-level flight data.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Amadeus Flight Search

Search and analyze flights using Amadeus Global Distribution System (GDS) data. Provides real-time pricing, multi-city itinerary support, and comprehensive airline details.

## Prerequisites

MCP server `amadeus-flight` must be configured with API credentials. See Setup section.

## Functionality

Scripts provide the following capabilities:

1. **Flight Search** (search.py)
   - Search one-way and round-trip flights
   - Multi-city itinerary search
   - Filter by nonstop, number of passengers

2. **Pricing** (pricing.py)
   - Price analysis and trends
   - Detailed pricing breakdown with fees and taxes
   - Price predictions and optimal booking windows

3. **Flight Details** (details.py)
   - Detailed flight information (schedule, aircraft)
   - Seat and cabin availability
   - Airline information

## Script Categories

Scripts are organized by functionality:

1. **search.py** - Flight search and multi-city searches
2. **pricing.py** - Price analysis and detailed pricing
3. **details.py** - Flight details, seat availability, airline info

Execute scripts directly without loading tool documentation.

## When to Use

**Use Amadeus Flight when:**
- Searching international routes (crossing borders)
- Long-distance routes (>1000km or >10 hours by train)
- Need real-time flight pricing with GDS data
- Multi-city itineraries with flight segments
- Price trend analysis for booking optimization
- Detailed airline and aircraft information required

**Do NOT use when:**
- Domestic China routes (use gaode-maps skill instead)
- Ground transportation preferred
- API credentials not configured

## Workflow

1. Execute Python scripts directly via Bash tool
2. Scripts communicate with MCP server via npx and JSON-RPC 2.0
3. Parse JSON response from script output
4. Structure data for agent use
5. Handle errors with automatic retry logic (3 attempts with exponential backoff)

## MCP Server Setup

**Environment Variables:**

Scripts automatically launch MCP server via npx. Set these environment variables:

```bash
export AMADEUS_API_KEY="your_api_key_here"
export AMADEUS_API_SECRET="your_api_secret_here"
```

Or add to `.env` file in project root:
```
AMADEUS_API_KEY=your_api_key_here
AMADEUS_API_SECRET=your_api_secret_here
```

**Get API Credentials:**
1. Register at https://developers.amadeus.com/
2. Create application in Self-Service portal
3. Copy API Key and API Secret
4. Store in environment variables (never hardcode)

## Security

- Never hardcode API keys in any files
- Use environment variables for credentials
- Configure credentials in MCP server config only
- API keys should never appear in skill files or agent files

## Error Handling

**Retry Logic:**
- 3 attempts with exponential backoff (1s, 2s, 4s)
- Log each attempt and error message
- Return structured error if all attempts fail

**Fallback Strategy:**
- On permanent failure: Report error to user with actionable message
- Check API credentials are properly configured
- Verify MCP server package is accessible via npx

**Common Errors:**
- Invalid IATA code: Validate airport codes before search
- Rate limit: Implement backoff, respect API limits
- No results: Try broader date range or nearby airports
- Authentication: Check API credentials configuration

## Integration

**Configured for agents:**
- transportation

**Script Execution:**
Execute scripts directly via Bash tool. See "Script Execution" section for complete examples.

## Best Practices

1. **Airport Codes**: Always use IATA codes (PEK, CDG, LHR)
2. **Date Format**: Use ISO 8601 format (YYYY-MM-DD)
3. **Multi-City**: Specify each leg with origin, destination, date
4. **Price Analysis**: Use to recommend optimal booking window
5. **Total Journey**: Include airport transfer time (2-3 hours)

## Script Execution

Execute Python scripts directly via Bash tool to call Amadeus MCP server:

### Search Flights

```bash
# One-way flight (Beijing to Paris, March 15, 1 adult, allow connections)
python3 /root/travel-planner/.claude/skills/amadeus-flight/scripts/search.py \
  search_flights PEK CDG 2026-03-15 null 1 false

# Round-trip flight (Beijing to Paris, March 15-25, 2 adults, nonstop only)
python3 /root/travel-planner/.claude/skills/amadeus-flight/scripts/search.py \
  search_flights PEK CDG 2026-03-15 2026-03-25 2 true

# Multi-city (Beijing -> Paris -> London)
python3 /root/travel-planner/.claude/skills/amadeus-flight/scripts/search.py \
  multi_city PEK CDG 2026-03-15 CDG LHR 2026-03-20
```

### Price Analysis

```bash
# Get price analysis for route
python3 /root/travel-planner/.claude/skills/amadeus-flight/scripts/pricing.py \
  price_analysis PEK CDG 2026-03-15

# Get detailed pricing for specific offer
python3 /root/travel-planner/.claude/skills/amadeus-flight/scripts/pricing.py \
  get_price ABC123XYZ
```

### Flight Details

```bash
# Get flight details
python3 /root/travel-planner/.claude/skills/amadeus-flight/scripts/details.py \
  flight_details AF123 2026-03-15

# Check seat availability
python3 /root/travel-planner/.claude/skills/amadeus-flight/scripts/details.py \
  seat_availability ABC123XYZ

# Get airline information
python3 /root/travel-planner/.claude/skills/amadeus-flight/scripts/details.py \
  airline_info AF
```

### Output Format

Scripts return JSON output to stdout. Parse the JSON to extract flight data:

```json
{
  "data": [
    {
      "id": "flight-offer-123",
      "price": {
        "total": "850.00",
        "currency": "USD"
      },
      "itineraries": [
        {
          "duration": "PT11H30M",
          "segments": [
            {
              "departure": {
                "iataCode": "PEK",
                "at": "2026-03-15T10:00:00"
              },
              "arrival": {
                "iataCode": "CDG",
                "at": "2026-03-15T15:30:00"
              },
              "carrierCode": "AF",
              "number": "123"
            }
          ]
        }
      ]
    }
  ]
}
```

## Examples

See `examples/` directory for detailed usage examples:
- `flight-search.md` - Complete flight search workflow
- `multi-city.md` - Multi-city itinerary example
- `price-optimization.md` - Price analysis example
