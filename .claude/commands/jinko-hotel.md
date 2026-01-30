---
description: "Jinko Hotel Booking integration for hotel search with real-time pricing and availability"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# Jinko Hotel Skill

Access Jinko Hotel Booking API via MCP server for comprehensive hotel search with 2M+ hotels worldwide, real-time pricing, availability, and booking links.

## Quick Start

**Prerequisites**: Jinko Hotel Booking MCP server must be configured (see Setup section below).

**Usage**:
```
/jinko-hotel [category]    # Load specific tool category
/jinko-hotel help          # Show available categories
```

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **search** - Hotel search and filtering
   - Location-based search
   - Facility filtering
   - Price range filtering
   - Rating filtering

2. **details** - Hotel information
   - Detailed hotel information
   - Room types and pricing
   - Amenities and services
   - Reviews and ratings

3. **booking** - Booking management
   - Generate booking links
   - Check availability
   - Price comparison

## Loading Tool Categories

Load categories on demand to optimize token usage:

```markdown
To search hotels, load: /root/travel-planner/.claude/commands/jinko-hotel/tools/search.md
To get hotel details, load: /root/travel-planner/.claude/commands/jinko-hotel/tools/details.md
To generate booking links, load: /root/travel-planner/.claude/commands/jinko-hotel/tools/booking.md
```

## Database Coverage

- **2M+ hotels** worldwide
- Real-time pricing and availability
- Multi-language support
- Currency conversion
- Local payment methods

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
If MCP server unavailable, fall back to WebSearch for hotel information.

## Language Support

- Input: English or local language
- Output: Multi-language support (English, Chinese, etc.)
- Currency: Multi-currency support with conversion

## MCP Server Setup

**Required**: User must configure Jinko Hotel Booking MCP server before using this skill.

### Step 1: Get API Key

Register at: https://www.jinko.so/

### Step 2: Configure MCP Server

**Recommended Method: Streamable HTTP**

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jinko-hotel": {
      "url": "https://mcp.jinko.so/hotel?key=YOUR_JINKO_API_KEY"
    }
  }
}
```

**Alternative Method: Node.js I/O**

```json
{
  "mcpServers": {
    "jinko-hotel": {
      "command": "npx",
      "args": ["-y", "@jinko/hotel-booking-mcp"],
      "env": {
        "JINKO_API_KEY": "YOUR_JINKO_API_KEY"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

Required for MCP server configuration to take effect.

### Verification

This skill assumes MCP tools are available:
- `search_hotels`
- `filter_by_facilities`
- `get_hotel_details`
- `generate_booking_link`
- `check_availability`
- `compare_prices`

If tools unavailable, skill will report error and suggest fallback to WebSearch.

## Rate Limits

- Free tier: 1,000 calls/day
- Basic tier: 100,000 calls/day
- Monitor usage at: https://www.jinko.so/dashboard

## Security

**Never hardcode API keys**. Always use:
- MCP server configuration (environment variables)
- Claude Desktop config file
- Project-specific `.env` files (if applicable)

## Examples

See: `/root/travel-planner/.claude/commands/jinko-hotel/examples/`

## For Accommodation Agent

This skill is configured for the accommodation agent. Usage pattern:

1. Invoke `/jinko-hotel search` to load hotel search tools
2. Use `search_hotels` with location, dates, and filters
3. Use `filter_by_facilities` to refine results (WiFi, pool, parking, etc.)
4. Use `get_hotel_details` for comprehensive information
5. Parse response for name, location, cost, amenities, ratings
6. Fall back to WebSearch if MCP unavailable

See `.claude/agents/accommodation.md` for integration details.
