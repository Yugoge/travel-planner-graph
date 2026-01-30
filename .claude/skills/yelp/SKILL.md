---
name: yelp
description: |
  Search restaurants and dining options using Yelp Fusion AI MCP.
  Use when researching breakfast, lunch, dinner options with ratings, reviews, pricing, and booking information.
  Provides verified user ratings, review counts, price levels, cuisine categories, opening hours, and location data.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Yelp Restaurant Search

Search and discover restaurants using Yelp Fusion AI data. Provides comprehensive dining information with verified ratings, reviews, pricing, and booking details.

## When to Use

Invoke this skill when:
- Researching breakfast, lunch, or dinner options
- Finding restaurants by cuisine type or dietary needs
- Getting verified user ratings and review counts
- Checking restaurant pricing, hours, and location
- Filtering by budget, rating, or distance
- Planning meals around activities or accommodation

## Prerequisites

Yelp Fusion AI MCP server must be configured with valid API key.

**Security**: API key configured in MCP server config (never hardcoded in files).

## Script Execution

This skill provides Python scripts that communicate with Yelp MCP server via JSON-RPC 2.0 over stdio.

### Available Scripts

1. **search.py** - Restaurant search and discovery
   - Search restaurants by natural language query
   - Filter by location, category, price, rating
   - Get business details by ID
   - Search by cuisine category

2. **details.py** - Get complete business information
   - Operating hours schedule
   - Photos and contact details
   - Transaction options (delivery, pickup, reservation)

### Script Location

All scripts are in `/root/travel-planner/.claude/skills/yelp/scripts/`

### Prerequisites

**API Key Setup**:
1. Register at https://www.yelp.com/developers
2. Create app in Yelp Fusion portal
3. Copy API Key
4. Set environment variable: `export YELP_API_KEY=your_api_key`

**Requirements**:
- Python 3.7+
- npx (Node.js package runner)
- Internet connection

**Rate Limits**: Free tier provides 5,000 API calls/day

## Integration

**Configured for agents**:
- meals

**Invocation**:
- Manual: `/yelp search`
- Automatic: Meals agent invokes when researching restaurants

## Usage Examples

### Search Restaurants

**Natural language search**:
```bash
cd /root/travel-planner/.claude/skills/yelp/scripts
python3 search.py search "best italian restaurants" "San Francisco, CA" --price=2,3 --limit=10
```

**Geographic search with coordinates**:
```bash
python3 search.py search "breakfast cafes" --lat=37.7749 --lon=-122.4194 --radius=1000 --open-now
```

**Search by category**:
```bash
python3 search.py category vegetarian "New York, NY" --price=1,2 --limit=10
```

### Get Business Details

**Full business information**:
```bash
python3 details.py gary-danko-san-francisco
```

### Common Search Patterns

**Breakfast near accommodation**:
```bash
python3 search.py search "breakfast" --lat=37.7749 --lon=-122.4194 --radius=500 --categories=breakfast_brunch,cafes --price=1,2
```

**Lunch near attraction**:
```bash
python3 search.py search "lunch restaurants" --lat=37.7749 --lon=-122.4194 --radius=1000 --price=2,3
```

**Dinner by cuisine**:
```bash
python3 search.py category italian "San Francisco, CA" --price=2,3,4 --limit=15
```

## Error Handling

**Retry Logic**: Scripts implement 3 attempts with exponential backoff (1s, 2s, 4s)

**Error Types**:
- 401 Unauthorized: Check YELP_API_KEY environment variable
- 429 Rate limit: Wait and retry with backoff
- 400 Bad request: Validate search parameters
- 404 Not found: Business ID invalid or removed
- 5xx Server error: Automatic retry with backoff

## Response Structure

Yelp tools return structured JSON with:
- `name`: Restaurant name
- `location`: Full address
- `rating`: User rating (1-5 scale)
- `review_count`: Number of reviews
- `price`: Price level ($, $$, $$$, $$$$)
- `categories`: Cuisine types and tags
- `hours`: Operating hours
- `url`: Yelp page URL
- `coordinates`: Latitude and longitude
- `phone`: Contact number
- `transactions`: Delivery, pickup, reservation options

## Data Quality

**Yelp advantages**:
- Verified user ratings and review counts
- Real-time operating hours
- Accurate pricing indicators
- Cuisine categories and dietary tags
- Location coordinates for distance calculations
- Booking and reservation information
- Worldwide coverage

**Data coverage**:
- Worldwide restaurant coverage
- Real-time operating hours and status
- Verified ratings from millions of reviews
- Updated daily with new listings and changes

## Best Practices

1. **Search Strategy**:
   - Use natural language for broad search
   - Filter by minimum rating (≥3.5 recommended)
   - Filter by minimum review count (≥20 recommended)
   - Consider price level relative to budget
   - Check distance from accommodation or activities

2. **Quality Standards**:
   - Minimum rating: 3.5 stars
   - Minimum reviews: 20 reviews
   - Location convenience: <2km from activity or accommodation
   - Operating hours match meal time
   - Price aligns with budget constraints

3. **Dietary Restrictions**:
   - Search by category for dietary needs
   - Vegetarian: "vegetarian", "vegan"
   - Halal: "halal"
   - Kosher: "kosher"
   - Gluten-free: filter reviews or use WebSearch for details

4. **Budget Optimization**:
   - $ = under $10 per person
   - $$ = $11-30 per person
   - $$$ = $31-60 per person
   - $$$$ = over $61 per person
   - Allocate: 15% breakfast, 30% lunch, 40% dinner of daily meal budget

5. **Variety and Balance**:
   - Track used restaurants across days
   - Avoid repeating cuisine types on consecutive days
   - Mix price levels throughout trip
   - Balance local and international options

## Examples

See usage examples in `examples/` directory:
- `restaurant-search.md` - Complete meal planning workflow

## Security

- Never hardcode API keys in any files
- API key stored in MCP server environment variables
- Credentials managed at MCP server level, not in skill code
- No sensitive data in logs or output files

## Support

**Documentation**: https://github.com/Yelp/yelp-mcp
**Yelp Fusion API**: https://www.yelp.com/developers/documentation/v3
**MCP Protocol**: https://modelcontextprotocol.io/
