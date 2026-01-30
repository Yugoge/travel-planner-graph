---
name: airbnb
description: |
  Search and retrieve detailed information about Airbnb vacation rentals.
  Use when user needs extended stay accommodations (5+ nights), family/group travel (4+ guests),
  properties with kitchens and laundry, or local neighborhood experiences.
  Automatically invoked by accommodation agent for vacation rental searches.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Airbnb Skill

Search Airbnb listings and retrieve detailed property information for vacation rental accommodation planning.

## When to Use

Invoke this skill when:
- Extended stays (5+ nights) where rentals are more cost-effective
- Family or group travel (4+ guests) needing multiple bedrooms
- Kitchen and laundry facilities required
- Prefer local neighborhood experience over hotel services
- Comparing accommodation options with hotel alternatives

## Prerequisites

**MCP Server**: `@openbnb/mcp-server-airbnb` must be configured.

No API keys required - server uses public Airbnb search.

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **search** - Search listings with filters
   - Search by location, dates, guests, price
   - Pagination support for browsing results
   - Returns property summaries with pricing

2. **details** - Get comprehensive property information
   - Full amenities list
   - House rules and policies
   - Host information
   - Location coordinates

## Loading Tools

Load categories on demand:

```
/airbnb search   # Loads tools/search.md
/airbnb details  # Loads tools/details.md
```

## MCP Server Setup

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": [
        "-y",
        "@openbnb/mcp-server-airbnb"
      ]
    }
  }
}
```

**Requirements**:
- Node.js 18+
- No API keys needed

## Integration

**Configured for agents**: accommodation

**Usage**:
```
/airbnb search   # Search vacation rentals
/airbnb details  # Get property details
```

## Best Practices

1. **Date ranges**: Always specify check-in/check-out for accurate pricing
2. **Guest counts**: Include all guests (adults, children, infants, pets) for availability
3. **Price filtering**: Use min/max price to narrow results to budget
4. **Pagination**: Use cursor for browsing beyond first page
5. **Verification**: Check ratings (4.5+ preferred), Superhost status, recent reviews
6. **Cost calculation**: Include all fees (cleaning, service) for total cost

## Quality Criteria

- Prefer Superhosts with 4.5+ rating
- Check reviews within past 6 months
- Verify property type matches needs (entire place vs. private room)
- Calculate average per-night cost including all fees
- Confirm amenities (WiFi, kitchen, washer/dryer)
- Check house rules (smoking, pets, events)

## Fallback Strategy

If MCP unavailable or results insufficient:
1. Use WebSearch for "airbnb [location] [dates]"
2. Document manual search results
3. Note MCP unavailability in agent output

## Security

- No API keys stored in skill files
- No credentials required for MCP server
- Server handles rate limiting automatically
- Use `ignoreRobotsText` parameter only when necessary

---

**Ready to use**: Invoke `/airbnb search` or `/airbnb details` to load tools.
