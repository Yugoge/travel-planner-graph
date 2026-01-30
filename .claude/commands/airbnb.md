---
description: "Airbnb integration for vacation rentals, apartments, and alternative accommodation search"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# Airbnb Skill

Access Airbnb listings via MCP server for vacation rental search, apartment rentals, and alternative accommodation options.

## Quick Start

**Prerequisites**: Airbnb MCP server must be configured (see Setup section below).

**Usage**:
```
/airbnb [category]    # Load specific tool category
/airbnb help          # Show available categories
```

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **search** - Rental search and filtering
   - Search listings by location
   - Filter by amenities and facilities
   - Get detailed listing information
   - Review host ratings and reviews

## Loading Tool Categories

Load categories on demand to optimize token usage:

```markdown
To search rentals, load: /root/travel-planner/.claude/commands/airbnb/tools/search.md
```

## Use Cases

**Vacation Rentals**:
- Family accommodations with kitchen facilities
- Longer stays (weekly/monthly rentals)
- Unique properties (villas, cottages, apartments)

**Business Travel**:
- Apartment-style accommodations
- Work-friendly spaces with WiFi
- Extended stay options

**Group Travel**:
- Multi-bedroom properties
- Shared spaces for groups
- Cost-effective for 4+ travelers

**Local Experience**:
- Neighborhoods outside tourist areas
- Residential areas with local amenities
- Properties with local hosts

## When to Use Airbnb vs Hotels

**Prefer Airbnb when**:
- Stay duration >3 nights
- Group size >3 people
- Kitchen/laundry facilities needed
- Family travel with children
- Prefer local neighborhood experience
- Budget-conscious for groups

**Prefer Hotels when**:
- Short stays (1-2 nights)
- Business travel requiring services
- Need daily housekeeping
- Prefer standardized amenities
- Loyalty program benefits

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
If MCP server unavailable, fall back to WebSearch for rental information.

## Data Quality

**Important**: Airbnb listings are dynamic:
- Availability changes frequently
- Prices vary by season and demand
- Always verify current availability
- Check recent reviews (within 6 months)
- Confirm house rules and policies

## MCP Server Setup

**Required**: User must configure Airbnb MCP server before using this skill.

### Step 1: Install MCP Server

```bash
npm install -g @openbnb/mcp-server-airbnb
```

### Step 2: Configure MCP Server

**Recommended Method: Node.js I/O**

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb"],
      "env": {
        "AIRBNB_API_KEY": "YOUR_AIRBNB_API_KEY"
      }
    }
  }
}
```

**Note**: Airbnb API access may require partnership agreement. For development/testing, the MCP server may use public data or require alternative authentication methods. Check the MCP server documentation for current authentication requirements.

### Step 3: Restart Claude Desktop

Required for MCP server configuration to take effect.

### Verification

This skill assumes MCP tools are available:
- `search_listings` - Search vacation rentals
- `get_listing_details` - Get detailed listing information
- `filter_by_amenities` - Filter by amenities and facilities
- `get_host_reviews` - Get host and property reviews

If tools unavailable, skill will report error and suggest fallback to WebSearch.

## Rate Limits

Rate limits depend on Airbnb API tier and MCP server implementation:
- Monitor usage to avoid rate limiting
- Implement exponential backoff for retries
- Cache results when appropriate

## Security

**Never hardcode API keys**. Always use:
- MCP server configuration (environment variables)
- Claude Desktop config file
- Project-specific `.env` files (if applicable)

## Search Best Practices

### 1. Location Specification

Be specific with locations:
- Use city name and neighborhood when possible
- Include country for international destinations
- Add landmarks for context (e.g., "near Times Square")

### 2. Date Flexibility

- Prices vary significantly by date
- Weekend vs weekday rates differ
- Holiday periods have premium pricing
- Longer stays often have discounts

### 3. Amenity Filtering

Common amenities to consider:
- Kitchen (full kitchen vs kitchenette)
- WiFi (essential for remote work)
- Washer/dryer (important for long stays)
- Parking (critical in some cities)
- Air conditioning/heating
- Family-friendly (crib, high chair)

### 4. Review Analysis

Check reviews for:
- Cleanliness ratings
- Accuracy of listing description
- Communication with host
- Location safety and convenience
- Recent reviews (within 3-6 months)

## Examples

See: `/root/travel-planner/.claude/commands/airbnb/examples/`

## For Accommodation Agent

This skill is configured for the accommodation agent. Usage pattern:

1. Invoke `/airbnb search` to load rental search tools
2. Use `search_listings` for vacation rentals and apartments
3. Compare with hotel options from jinko-hotel
4. Parse response for price, amenities, ratings
5. Fall back to WebSearch if MCP unavailable

See `.claude/agents/accommodation.md` for integration details.
