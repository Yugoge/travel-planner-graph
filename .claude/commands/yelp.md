---
description: "Yelp Fusion AI integration for restaurant search with ratings, reviews, and pricing"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# Yelp Skill

Access Yelp Fusion AI API via MCP server for comprehensive restaurant search with ratings, reviews, pricing, and booking information worldwide.

## Quick Start

**Prerequisites**: Yelp Fusion AI MCP server must be configured (see Setup section below).

**Usage**:
```
/yelp [category]    # Load specific tool category
/yelp help          # Show available categories
```

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **search** - Restaurant discovery and details
   - Natural language search
   - Category-based search
   - Business details with ratings
   - Review highlights

## Loading Tool Categories

Load categories on demand to optimize token usage:

```markdown
To search restaurants, load: /root/travel-planner/.claude/commands/yelp/tools/search.md
```

## Search Capabilities

**Natural language queries**:
- "Best pizza in New York"
- "Romantic Italian restaurant near Times Square"
- "Vegetarian-friendly cafes in San Francisco"
- "Cheap eats in Tokyo"

**Structured data returned**:
- Business name and address
- Rating (out of 5 stars)
- Price level ($, $$, $$$, $$$$)
- Review count and highlights
- Categories and cuisine types
- Phone number and booking URL
- Opening hours
- Distance from location

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
If MCP server unavailable, fall back to WebSearch for restaurant information.

## Language Support

- Input: English (primary), supports international locations
- Output: English with localized business information
- Pricing: Local currency converted to $ symbols

## MCP Server Setup

**Required**: User must configure Yelp Fusion AI MCP server before using this skill.

### Step 1: Get API Key

Register at: https://fusion.yelp.com/
Create an app and copy your API key.

### Step 2: Configure MCP Server

**Recommended Method: Node.js I/O**

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yelp": {
      "command": "npx",
      "args": ["-y", "@yelp/yelp-mcp-server"],
      "env": {
        "YELP_API_KEY": "YOUR_YELP_API_KEY"
      }
    }
  }
}
```

**Alternative Method: Streamable HTTP** (if available)

```json
{
  "mcpServers": {
    "yelp": {
      "url": "https://mcp.yelp.com/mcp?key=YOUR_YELP_API_KEY"
    }
  }
}
```

### Step 3: Restart Claude Desktop

Required for MCP server configuration to take effect.

### Verification

This skill assumes MCP tools are available:
- `search_businesses`
- `get_business_details`
- `search_by_category`

If tools unavailable, skill will report error and suggest fallback to WebSearch.

## Rate Limits

- Free tier: 5,000 API calls/day
- Monitor usage at: https://www.yelp.com/developers/v3/manage_app
- Rate limit headers returned with each response

## Security

**Never hardcode API keys**. Always use:
- MCP server configuration (environment variables)
- Claude Desktop config file
- Project-specific `.env` files (if applicable)

## Examples

See: `/root/travel-planner/.claude/commands/yelp/examples/`

## For Meals Agent

This skill is configured for the meals agent. Usage pattern:

1. Invoke `/yelp search` to load restaurant search tools
2. Use `search_businesses` with natural language or structured parameters
3. Parse response for name, location, rating, price, reviews
4. Fall back to WebSearch if MCP unavailable

See `.claude/agents/meals.md` for integration details.
