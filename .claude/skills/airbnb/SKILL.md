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

## Script Execution

This skill uses Python scripts to communicate with the Airbnb MCP server via JSON-RPC 2.0.

### Search Listings

```bash
# Basic search
python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py "San Francisco, CA"

# Search with dates and guests
python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py "Austin, TX" \
  --checkin 2026-06-15 --checkout 2026-06-22 \
  --adults 2 --children 2

# Search with price filtering
python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py "Portland, OR" \
  --min-price 100 --max-price 250

# Pagination (get next page)
python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py "Seattle, WA" \
  --cursor "pagination_token_here"

# Raw JSON output
python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py "Miami, FL" --raw
```

### Get Listing Details

```bash
# Basic details
python3 /root/travel-planner/.claude/skills/airbnb/scripts/details.py 12345678

# Details with dates for pricing
python3 /root/travel-planner/.claude/skills/airbnb/scripts/details.py 12345678 \
  --checkin 2026-06-15 --checkout 2026-06-22

# Details with guest count
python3 /root/travel-planner/.claude/skills/airbnb/scripts/details.py 12345678 \
  --adults 2 --children 2

# Raw JSON output
python3 /root/travel-planner/.claude/skills/airbnb/scripts/details.py 12345678 --raw
```

### Script Parameters

**search.py**:
- `location` (required): Location to search (e.g., "San Francisco, CA")
- `--place-id`: Google Maps Place ID (overrides location)
- `--checkin`: Check-in date (YYYY-MM-DD)
- `--checkout`: Check-out date (YYYY-MM-DD)
- `--adults`: Number of adults (default: 1)
- `--children`: Number of children
- `--infants`: Number of infants
- `--pets`: Number of pets
- `--min-price`: Minimum price per night (USD)
- `--max-price`: Maximum price per night (USD)
- `--cursor`: Pagination cursor for next page
- `--raw`: Output raw JSON

**details.py**:
- `listing_id` (required): Airbnb listing ID (from search results)
- `--checkin`: Check-in date (YYYY-MM-DD)
- `--checkout`: Check-out date (YYYY-MM-DD)
- `--adults`: Number of adults (default: 1)
- `--children`: Number of children
- `--infants`: Number of infants
- `--pets`: Number of pets
- `--raw`: Output raw JSON

## MCP Server Setup

**Prerequisites**:
- Node.js 18+
- npx installed
- No API keys needed (uses public Airbnb data)

**MCP Package**: `@openbnb/mcp-server-airbnb`

Scripts launch the MCP server automatically via npx.

## Integration

**Configured for agents**: accommodation

**Usage**: Execute Python scripts via Bash tool

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

## Error Handling

If script execution fails:
1. Verify Node.js and npx are installed
2. Check network connectivity
3. Retry with increased timeout
4. Verify listing IDs are correct (for details.py)

**No WebSearch fallback** - Scripts communicate directly with Airbnb MCP server.

## Security

- No API keys stored in skill files
- No credentials required for MCP server
- Server handles rate limiting automatically
- Use `--ignore-robots` flag only when necessary

---

## For Accommodation Agent

Execute scripts via Bash tool for vacation rental search:

1. **Search listings**: Run search.py with location, dates, and filters
2. **Filter results**: Select top candidates (rating 4.5+, Superhost preferred)
3. **Get details**: Run details.py for top 3-5 listings
4. **Calculate costs**: Extract total cost including all fees
5. **Format output**: Generate JSON for accommodation plan

**Example workflow**:
```bash
# Step 1: Search
python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py "Austin, TX" \
  --checkin 2026-06-15 --checkout 2026-06-22 \
  --adults 2 --children 2 --min-price 100 --max-price 250 --raw

# Step 2: Get details for top listing
python3 /root/travel-planner/.claude/skills/airbnb/scripts/details.py 12345678 \
  --checkin 2026-06-15 --checkout 2026-06-22 \
  --adults 2 --children 2 --raw
```

**Ready to use**: Execute Python scripts via Bash tool.
