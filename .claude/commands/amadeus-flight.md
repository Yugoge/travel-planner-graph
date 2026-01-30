---
description: "Amadeus Flight Search integration for international flight booking with real-time pricing and multi-city itineraries"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# Amadeus Flight Skill

Access Amadeus Flight Search API via MCP server for comprehensive flight search with GDS-level data, real-time pricing, and multi-city routing capabilities.

## Quick Start

**Prerequisites**: Amadeus Flight Search MCP server must be configured (see Setup section below).

**Usage**:
```
/amadeus-flight [category]    # Load specific tool category
/amadeus-flight help          # Show available categories
```

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **search** - Flight search and booking
   - Search flights by route
   - Multi-city itineraries
   - Price analysis and trends
   - Seat availability

2. **details** - Flight information
   - Detailed flight information
   - Airline details
   - Aircraft specifications
   - Terminal information

## Loading Tool Categories

Load categories on demand to optimize token usage:

```markdown
To search for flights, load: /root/travel-planner/.claude/commands/amadeus-flight/tools/search.md
To get flight details, load: /root/travel-planner/.claude/commands/amadeus-flight/tools/details.md
```

## Error Handling

**Transient errors** (retry with backoff):
- Network timeouts
- Rate limits (429)
- Server errors (5xx)

**Permanent errors** (don't retry):
- Invalid credentials (401)
- Forbidden (403)
- Invalid parameters (400)
- Not found (404)

**Graceful degradation**:
If MCP server unavailable, fall back to WebSearch for flight information.

## Data Format

**Airport Codes**: IATA 3-letter codes (e.g., LAX, JFK, LHR)
**Dates**: ISO 8601 format (YYYY-MM-DD)
**Currency**: ISO 4217 codes (USD, EUR, CNY, etc.)
**Time**: 24-hour format with timezone

## MCP Server Setup

**Required**: User must configure Amadeus Flight Search MCP server before using this skill.

### Step 1: Get API Credentials

Register at: https://developers.amadeus.com/register

Create an application to obtain:
- API Key (Client ID)
- API Secret (Client Secret)

### Step 2: Configure MCP Server

**Recommended Method: Streamable HTTP**

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "amadeus-flight": {
      "url": "https://mcp.amadeus.com/flight-search",
      "headers": {
        "X-API-Key": "YOUR_AMADEUS_API_KEY",
        "X-API-Secret": "YOUR_AMADEUS_API_SECRET"
      }
    }
  }
}
```

**Alternative Method: Node.js I/O**

```json
{
  "mcpServers": {
    "amadeus-flight": {
      "command": "npx",
      "args": ["-y", "@amadeus/flight-search-mcp-server"],
      "env": {
        "AMADEUS_API_KEY": "YOUR_AMADEUS_API_KEY",
        "AMADEUS_API_SECRET": "YOUR_AMADEUS_API_SECRET"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

Required for MCP server configuration to take effect.

### Verification

This skill assumes MCP tools are available:
- `search_flights`
- `multi_city_search`
- `price_analysis`
- `flight_details`
- `seat_availability`

If tools unavailable, skill will report error and suggest fallback to WebSearch.

## Rate Limits

**Test Environment**:
- Free tier: 100 calls/month
- Rate: 10 calls/second

**Production Environment**:
- Requires paid account
- Higher limits based on contract
- Monitor usage at: https://developers.amadeus.com/

## Security

**Never hardcode API credentials**. Always use:
- MCP server configuration (environment variables)
- Claude Desktop config file
- Project-specific `.env` files (if applicable)

**API Key Protection**:
- Never commit credentials to version control
- Use `.gitignore` for `.env` files
- Rotate keys regularly
- Use test credentials for development

## Examples

See: `/root/travel-planner/.claude/commands/amadeus-flight/examples/`

## For Transportation Agent

This skill is configured for the transportation agent. Usage pattern:

1. Invoke `/amadeus-flight search` to load flight search tools
2. Use `search_flights` for point-to-point international routes
3. Use `multi_city_search` for complex multi-destination trips
4. Parse response for price, duration, airline, schedule
5. Fall back to WebSearch if MCP unavailable

See `.claude/agents/transportation.md` for integration details.

## Best Practices

### 1. Search Strategy

**One-way vs Round-trip**:
- Use one-way for multi-city trips
- Use round-trip for simple there-and-back journeys
- Compare prices between both options

**Flexible Dates**:
- Search multiple date ranges for best prices
- Consider +/- 3 days for flexibility
- Weekday flights often cheaper than weekends

### 2. Multi-City Itineraries

**Routing**:
- Maximum 6 segments per search
- Each segment requires origin, destination, date
- Ensure logical connection times (2-4 hours minimum)

**Example**:
```
Beijing → Paris (Day 1)
Paris → London (Day 5)
London → Beijing (Day 10)
```

### 3. Price Analysis

**Trends**:
- Historical price data (past 12 months)
- Price predictions (next 30 days)
- Optimal booking window recommendations

**Factors**:
- Seasonality (peak vs off-peak)
- Day of week (Tuesday/Wednesday cheapest)
- Time of day (red-eye flights cheaper)
- Advance booking (3-8 weeks optimal)

### 4. Response Parsing

**Extract key information**:
- Total price (including taxes and fees)
- Duration (total travel time including layovers)
- Number of stops (non-stop preferred)
- Airline and flight numbers
- Departure/arrival times (with timezone)
- Baggage allowance
- Seat availability by cabin class

### 5. Error Recovery

**Retry logic**:
```
1. Initial request fails
2. Wait 2 seconds
3. Retry with exponential backoff (2s, 4s, 8s)
4. After 3 attempts, fall back to WebSearch
5. Log error for debugging
```

**Fallback strategy**:
```
1. Try Amadeus API
2. If unavailable, use WebSearch with query:
   "flights from {origin} to {destination} {date}"
3. Parse search results manually
4. Include warning: "Data from web search, not real-time"
```

## Integration Notes

**For Transportation Agent**:
- Use for international routes (>1000km or crossing borders)
- Compare with Gaode Maps for domestic China flights
- Prioritize non-stop flights when time-sensitive
- Consider total cost including baggage fees
- Note visa/passport requirements in recommendations
- Include airport transfer time in total journey duration

**For Multi-Agent Workflows**:
- Transportation agent calls this skill
- Results saved to `data/{destination-slug}/transportation.json`
- Budget agent reads pricing data
- Itinerary agent schedules around flight times
