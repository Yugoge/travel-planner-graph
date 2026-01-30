# Jinko Hotel - Search and Filtering Tools

Hotel search, facility filtering, and location-based search tools for finding accommodations.

## MCP Tools

### Tool 1: search_hotels

**MCP Tool Name**: `mcp__context7_jinko-hotel__search_hotels`

Search hotels by location, dates, price range, and rating criteria.

**Parameters**:
- `location` (required, string): City, region, or address (e.g., "Beijing, China", "Paris, France")
- `check_in` (required, string): Check-in date in YYYY-MM-DD format
- `check_out` (required, string): Check-out date in YYYY-MM-DD format
- `guests` (optional, number): Number of guests (default: 2)
- `rooms` (optional, number): Number of rooms (default: 1)
- `min_price` (optional, number): Minimum price per night in USD
- `max_price` (optional, number): Maximum price per night in USD
- `rating_min` (optional, number): Minimum star rating (1-5)
- `sort_by` (optional, string): Sort order - "price_low", "price_high", "rating", "distance"

**Returns**:
- `search_id` (string): Search session ID for filtering
- `hotels` (array): List of matching hotels
  - `id` (string): Hotel unique identifier
  - `name` (string): Hotel name
  - `address` (string): Full address
  - `location` (object): Coordinates {lat, lng}
  - `rating` (number): Star rating (1-5)
  - `price` (number): Price per night in USD
  - `currency` (string): Currency code
  - `image_url` (string): Primary hotel image
  - `facilities` (array): Available facilities
- `total_results` (number): Total matching hotels
- `page` (number): Current page number

**Example**:
```javascript
// Search hotels in Beijing for March 1-4, 2026
const results = await mcp__context7_jinko_hotel__search_hotels({
  location: "Beijing, China",
  check_in: "2026-03-01",
  check_out: "2026-03-04",
  guests: 2,
  rooms: 1,
  min_price: 100,
  max_price: 150,
  rating_min: 4,
  sort_by: "rating"
});

// Parse results
results.hotels.forEach(hotel => {
  console.log(`${hotel.name} - $${hotel.price}/night - ${hotel.rating} stars`);
});
```

**Use Cases**:
- Find hotels matching budget and location
- Search for specific date ranges
- Filter by minimum star rating
- Compare prices across multiple hotels

**Error Handling**:
```javascript
try {
  const results = await search_hotels({...});
  if (results.total_results === 0) {
    // No hotels found - expand search criteria
    // Option 1: Increase price range
    // Option 2: Lower rating requirement
    // Option 3: Use broader location (city instead of district)
  }
} catch (error) {
  if (error.code === 'RATE_LIMIT') {
    // Wait and retry with exponential backoff
    await sleep(2000);
    return retry(search_hotels, params);
  }
  // Fall back to WebSearch
  return searchHotelsViaWeb(location, dates);
}
```

---

### Tool 2: filter_by_facilities

**MCP Tool Name**: `mcp__context7_jinko-hotel__filter_by_facilities`

Filter search results by required facilities and amenities.

**Parameters**:
- `search_id` (required, string): Search session ID from search_hotels response
- `facilities` (required, array): List of required facilities
  - Available options: "wifi", "parking", "breakfast", "pool", "gym", "spa", "restaurant", "bar", "airport_shuttle", "pet_friendly", "accessible", "laundry", "business_center", "air_conditioning"

**Returns**:
- `hotels` (array): Filtered list of hotels with all required facilities
- `filtered_count` (number): Number of hotels matching criteria
- `original_count` (number): Original number before filtering

**Example**:
```javascript
// First search
const searchResults = await search_hotels({
  location: "Tokyo, Japan",
  check_in: "2026-04-15",
  check_out: "2026-04-18"
});

// Then filter for WiFi and breakfast
const filtered = await mcp__context7_jinko_hotel__filter_by_facilities({
  search_id: searchResults.search_id,
  facilities: ["wifi", "breakfast"]
});

console.log(`Found ${filtered.filtered_count} of ${filtered.original_count} hotels with WiFi and breakfast`);
```

**Use Cases**:
- Narrow down search results by amenities
- Find hotels with specific required facilities
- Progressive filtering (start broad, refine step by step)
- Match user requirements for amenities

**Best Practices**:

1. **Progressive Filtering**:
```javascript
// Start with essential facilities
const step1 = await filter_by_facilities({
  search_id: id,
  facilities: ["wifi"]
});

// Add nice-to-have if enough results
if (step1.filtered_count >= 5) {
  const step2 = await filter_by_facilities({
    search_id: id,
    facilities: ["wifi", "breakfast", "pool"]
  });
}
```

2. **Fallback Strategy**:
```javascript
// Try with all requirements
let results = await filter_by_facilities({
  search_id: id,
  facilities: ["wifi", "breakfast", "pool", "gym"]
});

// If too few results, reduce requirements
if (results.filtered_count < 3) {
  results = await filter_by_facilities({
    search_id: id,
    facilities: ["wifi", "breakfast"]  // Keep essentials only
  });
}
```

---

### Tool 3: search_nearby

**MCP Tool Name**: `mcp__context7_jinko-hotel__search_nearby`

Find hotels near specific point of interest (landmark, attraction, station).

**Parameters**:
- `poi` (required, string): Point of interest name (e.g., "Eiffel Tower", "Tokyo Station")
- `location` (required, string): City or region context
- `check_in` (required, string): Check-in date (YYYY-MM-DD)
- `check_out` (required, string): Check-out date (YYYY-MM-DD)
- `radius_km` (optional, number): Search radius in kilometers (default: 2)
- `max_results` (optional, number): Maximum number of results (default: 20)

**Returns**:
- `hotels` (array): Hotels sorted by distance from POI
  - All standard hotel fields (id, name, price, rating)
  - `distance_km` (number): Distance from POI in kilometers
  - `distance_minutes` (number): Estimated walking time in minutes
- `poi_location` (object): Coordinates of POI {lat, lng}
- `poi_name` (string): Resolved POI name

**Example**:
```javascript
// Find hotels near Forbidden City
const nearby = await mcp__context7_jinko_hotel__search_nearby({
  poi: "Forbidden City",
  location: "Beijing, China",
  check_in: "2026-05-10",
  check_out: "2026-05-13",
  radius_km: 1.5,
  max_results: 10
});

// Hotels are sorted by distance
nearby.hotels.forEach(hotel => {
  console.log(`${hotel.name} - ${hotel.distance_km}km (${hotel.distance_minutes}min walk) - $${hotel.price}/night`);
});
```

**Use Cases**:
- Find hotels near specific attractions
- Stay close to conference venues or business locations
- Find hotels near transportation hubs
- Optimize location for daily activities

**Best Practices**:

1. **Adjust Radius Based on Results**:
```javascript
// Start with tight radius
let results = await search_nearby({
  poi: "Louvre Museum",
  location: "Paris",
  check_in: "2026-06-01",
  check_out: "2026-06-03",
  radius_km: 1
});

// Expand if too few results
if (results.hotels.length < 5) {
  results = await search_nearby({
    poi: "Louvre Museum",
    location: "Paris",
    check_in: "2026-06-01",
    check_out: "2026-06-03",
    radius_km: 3  // Expand radius
  });
}
```

2. **Multiple POI Strategy**:
```javascript
// If trip involves multiple POIs, find central location
const [louvre, eiffelTower, arcDeTriomphe] = await Promise.all([
  search_nearby({ poi: "Louvre Museum", ... }),
  search_nearby({ poi: "Eiffel Tower", ... }),
  search_nearby({ poi: "Arc de Triomphe", ... })
]);

// Find hotels appearing in all three searches
const centralHotels = findIntersection([louvre.hotels, eiffelTower.hotels, arcDeTriomphe.hotels]);
```

---

## Best Practices

### 1. Search Strategy

**Broad → Narrow Approach**:
1. Start with `search_hotels` (broad location, flexible price)
2. Apply `filter_by_facilities` (essential amenities only)
3. Use `search_nearby` if specific POI is critical
4. Refine criteria only if too many results (>20)

**Example**:
```javascript
// Step 1: Broad search
const all = await search_hotels({
  location: "Rome, Italy",
  check_in: "2026-07-01",
  check_out: "2026-07-05",
  rating_min: 3  // Start permissive
});

// Step 2: Filter essentials
const filtered = await filter_by_facilities({
  search_id: all.search_id,
  facilities: ["wifi"]  // Only absolute requirements
});

// Step 3: If still too many, increase rating or tighten price
if (filtered.filtered_count > 20) {
  const refined = await search_hotels({
    location: "Rome, Italy",
    check_in: "2026-07-01",
    check_out: "2026-07-05",
    rating_min: 4,  // Increase quality
    max_price: 200  // Add price cap
  });
}
```

### 2. Performance Optimization

**Parallel Searches for Multiple Cities**:
```javascript
// Good: Parallel execution
const [city1, city2, city3] = await Promise.all([
  search_hotels({ location: "Beijing", ... }),
  search_hotels({ location: "Shanghai", ... }),
  search_hotels({ location: "Guangzhou", ... })
]);

// Bad: Sequential execution (3x slower)
const city1 = await search_hotels({ location: "Beijing", ... });
const city2 = await search_hotels({ location: "Shanghai", ... });
const city3 = await search_hotels({ location: "Guangzhou", ... });
```

**Cache Search IDs**:
```javascript
// Save search_id to reuse for multiple filter operations
const searchResults = await search_hotels({...});
const searchId = searchResults.search_id;

// Reuse same search_id for different filter combinations
const withWifi = await filter_by_facilities({ search_id: searchId, facilities: ["wifi"] });
const withBreakfast = await filter_by_facilities({ search_id: searchId, facilities: ["breakfast"] });
const withBoth = await filter_by_facilities({ search_id: searchId, facilities: ["wifi", "breakfast"] });
```

### 3. Error Handling Patterns

**Retry Logic**:
```javascript
async function searchHotelsWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_hotels(params);
    } catch (error) {
      if (error.code === 'RATE_LIMIT' && i < maxRetries - 1) {
        await sleep(Math.pow(2, i) * 1000);  // Exponential backoff
        continue;
      }
      throw error;
    }
  }
}
```

**Graceful Degradation**:
```javascript
async function searchHotels(params) {
  try {
    return await mcp__context7_jinko_hotel__search_hotels(params);
  } catch (error) {
    console.warn('Jinko Hotel MCP unavailable, falling back to WebSearch');
    return await searchHotelsViaWeb(params.location, params.check_in, params.check_out);
  }
}
```

---

## Common Patterns

### Pattern 1: Budget-Conscious Search
```javascript
// Find best value hotels
const results = await search_hotels({
  location: "Barcelona, Spain",
  check_in: "2026-08-10",
  check_out: "2026-08-15",
  max_price: 100,
  rating_min: 4,
  sort_by: "price_low"  // Lowest price first
});

// Filter for essentials only
const filtered = await filter_by_facilities({
  search_id: results.search_id,
  facilities: ["wifi"]
});

// Select top 3 by rating
const topHotels = filtered.hotels
  .sort((a, b) => b.rating - a.rating)
  .slice(0, 3);
```

### Pattern 2: Luxury Search
```javascript
// Find premium hotels
const luxury = await search_hotels({
  location: "Dubai, UAE",
  check_in: "2026-12-20",
  check_out: "2026-12-25",
  rating_min: 5,
  sort_by: "rating"
});

// Filter for luxury amenities
const refined = await filter_by_facilities({
  search_id: luxury.search_id,
  facilities: ["spa", "pool", "gym", "restaurant", "bar"]
});
```

### Pattern 3: Location-Optimized Search
```javascript
// Find hotels central to multiple POIs
const near_attraction1 = await search_nearby({
  poi: "British Museum",
  location: "London, UK",
  check_in: "2026-09-01",
  check_out: "2026-09-03",
  radius_km: 2
});

const near_attraction2 = await search_nearby({
  poi: "Tower of London",
  location: "London, UK",
  check_in: "2026-09-01",
  check_out: "2026-09-03",
  radius_km: 2
});

// Find hotels that appear in both searches
const centralHotels = near_attraction1.hotels.filter(h1 =>
  near_attraction2.hotels.some(h2 => h2.id === h1.id)
);
```

---

**Next**: Use `/jinko-hotel details` to load hotel information and review tools.
