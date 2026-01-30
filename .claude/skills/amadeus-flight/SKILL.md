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

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **search** - Flight search and pricing
   - search_flights - Search flights by origin/destination
   - multi_city_search - Search multi-city itineraries
   - price_analysis - Get price trends and predictions

2. **details** - Flight and airline information
   - flight_details - Get detailed flight information
   - seat_availability - Check seat and cabin availability

## Loading Tools

Load categories on demand:

```
/amadeus-flight search   # Loads tools/search.md
/amadeus-flight details  # Loads tools/details.md
```

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
- MCP server unavailable (fall back to WebSearch)

## Workflow

1. Execute Python scripts directly via Bash tool
2. Scripts communicate with MCP server via npx and JSON-RPC 2.0
3. Parse JSON response from script output
4. Structure data for agent use
5. Handle errors with automatic retry logic (3 attempts with exponential backoff)

## MCP Server Setup

Configure in MCP settings file:

```json
{
  "mcpServers": {
    "amadeus-flight": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-amadeus"],
      "env": {
        "AMADEUS_API_KEY": "${AMADEUS_API_KEY}",
        "AMADEUS_API_SECRET": "${AMADEUS_API_SECRET}"
      }
    }
  }
}
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
- On permanent failure: switch to WebSearch
- Document data source in output (amadeus vs web_search)
- Maintain data structure consistency

**Common Errors:**
- Invalid IATA code: Validate airport codes before search
- Rate limit: Implement backoff, respect API limits
- No results: Try broader date range or nearby airports
- Authentication: Check API credentials configuration

## Integration

**Configured for agents:**
- transportation

**Usage:**
```
/amadeus-flight search
/amadeus-flight details
```

## Best Practices

1. **Airport Codes**: Always use IATA codes (PEK, CDG, LHR)
2. **Date Format**: Use ISO 8601 format (YYYY-MM-DD)
3. **Multi-City**: Specify each leg with origin, destination, date
4. **Price Analysis**: Use to recommend optimal booking window
5. **Total Journey**: Include airport transfer time (2-3 hours)
6. **Data Source**: Always document whether data from Amadeus or fallback

## Examples

See `examples/` directory for detailed usage examples:
- `flight-search.md` - Complete flight search workflow
- `multi-city.md` - Multi-city itinerary example
- `price-optimization.md` - Price analysis example
