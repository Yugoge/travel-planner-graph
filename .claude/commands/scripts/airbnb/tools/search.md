# Airbnb - Search Tool

Search for vacation rentals and accommodations on Airbnb.

## MCP Tools

### Tool 1: airbnb_search

**MCP Tool Name**: `mcp__airbnb__search`

**Purpose**: Search for Airbnb listings by location and dates.

**Parameters**:
- `location` (required): City, address, or landmark
  - Examples: "Beijing", "Paris, France", "Tokyo Station"
- `checkin` (required): Check-in date in YYYY-MM-DD format
  - Example: "2026-02-10"
- `checkout` (required): Check-out date in YYYY-MM-DD format
  - Example: "2026-02-12"
- `adults` (optional): Number of adult guests (default: 1)
- `children` (optional): Number of children (default: 0)
- `infants` (optional): Number of infants (default: 0)
- `pets` (optional): Number of pets (default: 0)
- `price_min` (optional): Minimum price per night in USD
- `price_max` (optional): Maximum price per night in USD

**Returns**:
- `searchUrl` - Airbnb search URL
- `searchResults` array, each containing:
  - `id` - Listing ID
  - `url` - Listing URL
  - `name` - Property name/title
  - `location` - Coordinates (latitude, longitude)
  - `badges` - Special badges (e.g., "Guest favorite")
  - `primaryLine` - Room type (e.g., "1 bedroom, 1 queen bed")
  - `secondaryLine` - Host type
  - `avgRatingA11yLabel` - Rating (e.g., "4.93 out of 5, 146 reviews")
  - `structuredDisplayPrice` - Pricing info
    - `primaryLine.accessibilityLabel` - Total price
    - `explanationData.priceDetails` - Nightly rate breakdown

**Example Usage**:

Find accommodations in Beijing:
```python
result = call_tool("mcp__airbnb__search", {
    "location": "Beijing, China",
    "checkin": "2026-02-10",
    "checkout": "2026-02-12",
    "adults": 2,
    "price_min": 50,
    "price_max": 200
})
```

**Notes**:
- Requires `--ignore-robots-txt` flag to bypass robots.txt restrictions
- Results may vary based on availability and pricing
- Use for vacation rentals, apartments, and unique stays
- Coordinate data uses WGS-84 (standard GPS)

**Legal Notice**: Web scraping Airbnb may violate their Terms of Service. Use only for personal research and testing purposes.
