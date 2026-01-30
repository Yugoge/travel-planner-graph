---
name: jinko-hotel
description: |
  Jinko Hotel Booking skill provides access to 2M+ hotels worldwide with real-time pricing, availability, and facility filtering.
  Use when user needs hotel search, pricing comparison, or booking links for accommodations.
  Automatically invoke when planning trips, researching hotels, or finding lodging options.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Jinko Hotel Booking Skill

Access to 2M+ hotels worldwide with real-time pricing, availability, and comprehensive facility filtering via Jinko Hotel Booking MCP server.

## Prerequisites

- Python 3.7+ installed
- npx available (Node.js)
- JINKO_API_KEY environment variable set

Scripts will automatically launch MCP server via npx when needed.

## Tool Categories

This skill uses **progressive disclosure** to optimize token usage. Load only the tools you need:

### 1. **search** - Hotel Search and Filtering
- `search_hotels` - Search by location, dates, price range, rating
- `filter_by_facilities` - Filter by WiFi, parking, breakfast, pool, gym, etc.
- `search_nearby` - Find hotels near specific POI (landmarks, attractions)

**When to use**: Primary workflow for finding hotels matching user requirements.

### 2. **details** - Hotel Information and Reviews
- `get_hotel_details` - Comprehensive information (amenities, policies, photos)
- `get_room_types` - Room options, pricing, occupancy, bed configuration
- `get_reviews` - Guest reviews with ratings and insights

**When to use**: Deep dive into shortlisted hotels for detailed comparison.

### 3. **booking** - Availability and Booking Links
- `generate_booking_link` - Generate booking URL with pricing preserved
- `check_availability` - Real-time availability and restrictions
- `compare_prices` - Cross-platform price comparison (Booking.com, Expedia, etc.)

**When to use**: Final step to validate availability and generate booking links.

## Script Execution

This skill uses Python scripts to communicate with Jinko Hotel Booking MCP server via JSON-RPC 2.0.

**Prerequisites**:
- JINKO_API_KEY environment variable must be set
- Python 3.7+ installed
- npx available (Node.js)

### Search Hotels

Search for hotels by location, dates, and filters:

```bash
# Basic search
cd /root/travel-planner/.claude/skills/jinko-hotel/scripts
python3 search.py search 'Beijing' '2026-02-15' '2026-02-17'

# With filters
python3 search.py search 'Shanghai' '2026-03-10' '2026-03-12' 2 1 200 500 4.0
# Arguments: location checkin checkout guests rooms min_price max_price min_rating
```

### Search Near POI

Find hotels near specific landmarks:

```bash
python3 search.py nearby 'Beijing' 'Tiananmen Square' 3.0 '2026-02-15' '2026-02-17'
# Arguments: location poi radius_km checkin checkout
```

### Get Hotel Details

Retrieve comprehensive hotel information:

```bash
python3 details.py details 'hotel_12345'
```

### Get Room Types

View available rooms and pricing:

```bash
# Basic room info
python3 details.py rooms 'hotel_12345'

# With pricing for specific dates
python3 details.py rooms 'hotel_12345' '2026-02-15' '2026-02-17'
```

### Get Reviews

Read guest reviews:

```bash
python3 details.py reviews 'hotel_12345' 20 'recent'
# Arguments: hotel_id limit sort_by (recent|rating_high|rating_low)
```

### Check Availability

Verify real-time availability:

```bash
python3 booking.py availability 'hotel_12345' '2026-02-15' '2026-02-17' 2 1
# Arguments: hotel_id checkin checkout guests rooms
```

### Generate Booking Link

Create booking URL with pricing:

```bash
python3 booking.py link 'hotel_12345' 'room_67890' '2026-02-15' '2026-02-17' 2 1
# Arguments: hotel_id room_type_id checkin checkout guests rooms
```

### Compare Prices

Compare across platforms:

```bash
python3 booking.py compare 'hotel_12345' '2026-02-15' '2026-02-17' 2 1 'booking.com,expedia'
# Arguments: hotel_id checkin checkout guests rooms platforms_csv
```

## Typical Workflow

1. **Search hotels**: Execute `search.py search` with location, dates, price range
2. **Filter results**: Parse JSON output, optionally filter by facilities
3. **Get details**: Execute `details.py details` for top 2-3 hotels
4. **Check availability**: Execute `booking.py availability` to verify
5. **Generate link**: Execute `booking.py link` for user

## Configuration

Set the JINKO_API_KEY environment variable:

```bash
export JINKO_API_KEY="your-api-key-here"
```

**API Key**: Obtain from Jinko Hotel Booking service.

Scripts will automatically launch the MCP server via npx when needed.

## Security

**CRITICAL**: Never hardcode API keys in skill files.

- API keys managed by MCP server via environment variables
- Store in Claude Desktop config or `.env` files
- Never commit credentials to version control
- Use MCP server environment configuration

## Error Handling

### Transient Errors (Retry with Backoff)
- **429 (Rate Limit)**: Exponential backoff (1s → 2s → 4s)
- **5xx (Server Error)**: Linear backoff (2s → 4s → 6s)

### Permanent Errors (No Retry)
- **400 (Invalid Parameters)**: Fix parameters and report error
- **401 (Unauthorized)**: Check API key configuration
- **403 (Forbidden)**: Verify permissions
- **404 (Not Found)**: Hotel unavailable or invalid ID

### Handling Failures
- **Script Errors**: Check JINKO_API_KEY is set
- **API Quota Exceeded**: Report to user, retry later
- **Booking Link Failure**: Report error to user

## Integration

### Configured For Agents
- **accommodation** - Primary agent for hotel search

### Usage in Agents

**Accommodation Agent**:
```markdown
1. Read requirements: location, dates, budget, amenities
2. Invoke /jinko-hotel search
3. Call search_hotels with parameters
4. Call filter_by_facilities for required amenities
5. Select best hotel by rating and price
6. Parse results to accommodation.json format
7. Return complete
```

**Note**: Scripts must be executed via Bash tool with proper environment variables.

## Performance Optimization

### Parallel API Calls
When searching multiple locations, use parallel calls:

```javascript
// Good (parallel)
const [beijing, chengdu, shanghai] = await Promise.all([
  search_hotels({ location: "Beijing", ... }),
  search_hotels({ location: "Chengdu", ... }),
  search_hotels({ location: "Shanghai", ... })
]);

// Bad (sequential)
const beijing = await search_hotels({ location: "Beijing", ... });
const chengdu = await search_hotels({ location: "Chengdu", ... });
const shanghai = await search_hotels({ location: "Shanghai", ... });
```

### Selective Details Loading
Get details only for top candidates (2-3 hotels), not all results.

## Examples

See `/root/travel-planner/.claude/skills/jinko-hotel/examples/hotel-search.md` for complete multi-city workflow example.

---

**Quick Start**: Invoke `/jinko-hotel search` to begin hotel search workflow.
