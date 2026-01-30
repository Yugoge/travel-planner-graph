# Airbnb - Search

Search Airbnb listings with comprehensive filtering options.

## MCP Tools

### Tool: airbnb_search

**MCP Tool Name**: `mcp__plugin_airbnb_airbnb__airbnb_search`

**Purpose**: Search for vacation rental listings with location, date, guest, and price filters.

**Parameters**:
- `location` (required): Location to search (e.g., "San Francisco, CA", "Paris, France")
- `placeId` (optional): Google Maps Place ID for precise targeting (overrides location)
- `checkin` (optional): Check-in date in YYYY-MM-DD format
- `checkout` (optional): Check-out date in YYYY-MM-DD format
- `adults` (optional): Number of adults (default: 1)
- `children` (optional): Number of children (default: 0)
- `infants` (optional): Number of infants (default: 0)
- `pets` (optional): Number of pets (default: 0)
- `minPrice` (optional): Minimum price per night (USD)
- `maxPrice` (optional): Maximum price per night (USD)
- `cursor` (optional): Pagination cursor for browsing additional results
- `ignoreRobotsText` (optional): Boolean to override robots.txt (use sparingly)

**Returns**:
- Array of property listings with:
  - `id`: Airbnb listing ID
  - `name`: Property name/title
  - `url`: Direct link to listing
  - `price`: Price per night (may not include all fees)
  - `rating`: Average rating
  - `reviewCount`: Number of reviews
  - `location`: City/neighborhood
  - `propertyType`: Entire place, private room, etc.
  - `bedrooms`: Number of bedrooms
  - `beds`: Number of beds
  - `bathrooms`: Number of bathrooms
  - `maxGuests`: Maximum guest capacity
  - `isSuperhost`: Boolean indicating Superhost status
- `searchUrl`: URL to view results on Airbnb
- `cursor`: Pagination cursor for next page (if more results available)

**Example**:
```javascript
// Search for family rental in Austin for 1 week
mcp__plugin_airbnb_airbnb__airbnb_search({
  location: "Austin, TX",
  checkin: "2026-06-15",
  checkout: "2026-06-22",
  adults: 2,
  children: 2,
  minPrice: 100,
  maxPrice: 250
})

// Response includes:
// - Array of matching properties
// - Direct links to listings
// - Pagination cursor for more results
```

**Use Cases**:
- Initial accommodation search for vacation rentals
- Compare options by location, price, size
- Filter by guest count to find suitable properties
- Browse multiple pages of results using cursor
- Get pricing estimates for date ranges

---

## Best Practices

### Date Filtering
**Always specify dates** when possible:
- Airbnb pricing varies significantly by date
- Availability changes with dates
- Without dates, you get base price (may not reflect actual cost)

```javascript
// GOOD: Specific dates for accurate pricing
airbnb_search({
  location: "Portland, OR",
  checkin: "2026-07-10",
  checkout: "2026-07-17"
})

// ACCEPTABLE: No dates for general availability check
airbnb_search({
  location: "Portland, OR"
})
```

### Guest Configuration
**Include all guests** for accurate availability:
- Properties have maximum guest limits
- Some charge extra for additional guests
- Infant/pet policies vary by property

```javascript
// GOOD: Complete guest breakdown
airbnb_search({
  location: "Miami, FL",
  adults: 2,
  children: 2,
  infants: 1,
  pets: 0
})
```

### Price Filtering
**Use price range** to match budget:
- Narrows results to relevant options
- Saves time browsing
- Consider price is per night (not including fees)

```javascript
// Filter to mid-range properties ($150-250/night)
airbnb_search({
  location: "Seattle, WA",
  minPrice: 150,
  maxPrice: 250
})
```

### Pagination
**Browse multiple pages** for best options:
- First page may not have best value
- Use cursor to load more results
- Stop when you have 5-10 good candidates

```javascript
// Get first page
const page1 = airbnb_search({ location: "Boston, MA" })

// Get second page using cursor
const page2 = airbnb_search({
  location: "Boston, MA",
  cursor: page1.cursor
})
```

### Location Precision
**Use Place IDs** for precise searches:
- Exact neighborhood targeting
- Eliminates ambiguity (e.g., "Cambridge" could be UK or MA)
- Get Place IDs from Google Maps skill

```javascript
// Precise search using Place ID
airbnb_search({
  placeId: "ChIJd8BlQ2BZwokRjMKdAYXD8Zo", // NYC Financial District
  checkin: "2026-08-01",
  checkout: "2026-08-05"
})
```

## Workflow Integration

### Accommodation Agent Workflow

1. **Analyze requirements** from skeleton files:
   - Trip duration (hotel vs. rental)
   - Guest count (room capacity needs)
   - Budget (price filtering)

2. **Execute search**:
   ```javascript
   const results = airbnb_search({
     location: destination,
     checkin: tripStart,
     checkout: tripEnd,
     adults: adultCount,
     children: childCount,
     minPrice: budgetMin,
     maxPrice: budgetMax
   })
   ```

3. **Filter results**:
   - Rating >= 4.5
   - Superhost preferred
   - Review count >= 10
   - Recent reviews (within 6 months)
   - Matches amenity requirements

4. **Load details** for top candidates:
   - Use `/airbnb details` skill
   - Verify amenities (kitchen, washer, WiFi)
   - Check house rules (smoking, pets, events)
   - Review cancellation policy

5. **Calculate total cost**:
   - Base price × nights
   - Add cleaning fee
   - Add service fee
   - Calculate average per night
   - Compare with hotel options

## Error Handling

### No Results Found
```javascript
// If empty results:
// 1. Broaden search (remove price filters)
// 2. Try nearby locations
// 3. Adjust dates if too restrictive
// 4. Fall back to WebSearch
```

### Rate Limiting
```javascript
// If rate limited:
// 1. Wait and retry
// 2. MCP server handles this automatically
// 3. Use fewer searches (filter locally)
```

### Invalid Parameters
```javascript
// If parameter errors:
// 1. Check date format (YYYY-MM-DD)
// 2. Verify guest counts are integers
// 3. Ensure location is valid string
// 4. Price should be numbers (not currency strings)
```

## Performance Tips

1. **Minimize searches**: Filter requirements first, then search once
2. **Cache results**: Store search results to avoid duplicate calls
3. **Batch filtering**: Get 20-30 results, filter locally by criteria
4. **Progressive refinement**: Start broad, narrow with price/dates

## Output Structure

For accommodation agent JSON output:

```json
{
  "name": "Cozy Downtown Loft",
  "location": "Downtown Austin, TX",
  "cost": 180,
  "total_cost": 1260,
  "type": "Vacation Rental (Airbnb)",
  "amenities": ["Full kitchen", "Washer/Dryer", "WiFi", "Workspace", "Parking"],
  "notes": "Average per night $180 | Total for 7 nights: $1,260 (includes $100 cleaning fee) | Superhost | 4.8 stars (143 reviews) | Check-in: flexible after 3pm | Recent review (Jan 2026): 'Perfect for families'"
}
```

**Key fields**:
- `cost`: Average per night (total ÷ nights)
- `total_cost`: Complete cost including all fees
- `type`: Always "Vacation Rental (Airbnb)"
- `notes`: Include Superhost status, rating, review count, total cost breakdown

---

**Next step**: Use `/airbnb details` to get comprehensive property information for top candidates.
