---
name: tripadvisor
description: |
  Access TripAdvisor data for attractions, tours, activities, and user reviews.
  Use when researching tourist attractions, booking tours, finding activities, or getting traveler reviews.
  Provides verified ratings, pricing, hours, and booking information worldwide.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# TripAdvisor Skill

Access comprehensive TripAdvisor data for attractions, tours, activities, and user reviews worldwide.

## When to Use

Invoke this skill when:
- Researching tourist attractions and landmarks
- Finding tours, activities, and experiences
- Getting verified user reviews and ratings
- Checking attraction hours, prices, and booking requirements
- Comparing activity options by rating and price
- Planning day trips and guided tours

## Prerequisites

Set `TRIPADVISOR_API_KEY` environment variable with valid API credentials.

**Security**: API keys stored in environment variables (never hardcoded in files).

## Script Execution

This skill communicates with TripAdvisor MCP server via Python scripts using JSON-RPC 2.0 over stdio.

### Attractions

**Search attractions by location**:
```bash
python3 .claude/skills/tripadvisor/scripts/attractions.py search "Paris, France" \
  --category museums --min-rating 4.0 --max-results 10
```

**Get attraction details**:
```bash
python3 .claude/skills/tripadvisor/scripts/attractions.py details 12345
```

**Search nearby attractions**:
```bash
python3 .claude/skills/tripadvisor/scripts/attractions.py nearby 48.8584 2.2945 \
  --radius 2 --min-rating 4.0
```

### Tours and Activities

**Search tours by location**:
```bash
python3 .claude/skills/tripadvisor/scripts/tours.py search "Paris, France" \
  --category food-tours --time evening --min-rating 4.5
```

**Get tour details with availability**:
```bash
python3 .claude/skills/tripadvisor/scripts/tours.py details 67890 --date 2026-02-20
```

**Get user reviews**:
```bash
python3 .claude/skills/tripadvisor/scripts/tours.py reviews 67890 --max-reviews 10
```

**Check booking availability**:
```bash
python3 .claude/skills/tripadvisor/scripts/tours.py booking 67890 2026-02-20 --party-size 4
```

## Tool Categories

This skill uses progressive disclosure. Load documentation only when needed:

1. **attractions** - Search and discover attractions
   - Documentation: `.claude/skills/tripadvisor/tools/attractions.md`
   - Script: `scripts/attractions.py`

2. **tours** - Find tours, activities, and experiences
   - Documentation: `.claude/skills/tripadvisor/tools/tours.md`
   - Script: `scripts/tours.py`

## Integration

**Configured for agents**:
- attractions
- entertainment

**Invocation**:
- Manual: `/tripadvisor attractions` or `/tripadvisor tours`
- Automatic: Agents invoke when researching attractions or entertainment

## Error Handling

**Retry Logic**: 3 attempts with exponential backoff (1s, 2s, 4s)

**Error Types**:
- API key invalid: Verify TRIPADVISOR_API_KEY environment variable is set
- Rate limit exceeded: Wait and retry with backoff
- Location not found: Broaden search or use alternate location name
- No results: Adjust search filters (lower min-rating, increase max-results)

## Response Structure

All TripAdvisor tools return structured JSON with:
- `name`: Attraction or tour name
- `location`: Address or area
- `rating`: User rating (1-5 scale)
- `reviews_count`: Number of reviews
- `price`: Cost in USD (if applicable)
- `hours`: Operating hours
- `booking_url`: Link to book or learn more
- `traveler_tips`: Verified user recommendations

## Data Quality

**TripAdvisor advantages**:
- Verified user reviews and ratings
- Real-time pricing and availability
- Accurate operating hours
- Booking information and links
- Traveler tips and recommendations
- Worldwide coverage (200+ countries)

**Data freshness**:
- Reviews and ratings updated daily
- Pricing and availability checked in real-time
- Operating hours verified by venue owners
- Seasonal closures reflected in availability

## Best Practices

1. **Search Strategy**:
   - Start with broad location search
   - Filter by user ratings (minimum 4.0 recommended)
   - Consider number of reviews (higher = more reliable)
   - Check seasonal availability

2. **Data Validation**:
   - Verify hours for current season
   - Check if advance booking required
   - Confirm pricing is per person or per group
   - Note any age restrictions or requirements

3. **Geographic Clustering**:
   - Group attractions by proximity
   - Minimize travel time between activities
   - Consider transportation options

4. **User Experience**:
   - Include traveler tips in recommendations
   - Note accessibility information if available
   - Highlight unique or must-see features
   - Warn about common issues (crowds, long queues)

## Examples

See usage examples in `examples/` directory:
- `attraction-search.md` - Complete attraction search workflow
- `tour-booking.md` - Tour search and booking flow
- `review-analysis.md` - Analyzing user reviews

## Security

- Never hardcode API keys in any files
- API key stored in MCP server environment variables
- Credentials managed at MCP server level, not in skill code
- No sensitive data in logs or output files

## Support

**Documentation**: https://apify.com/mcp/tripadvisor-mcp-server
**MCP Protocol**: https://modelcontextprotocol.io/
**Issues**: Report MCP server issues to Apify support
