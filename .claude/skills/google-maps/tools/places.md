# Google Maps - Places Search

Search for locations, businesses, and points of interest using Google Places API.

## MCP Tools

### Tool 1: search_places

**MCP Tool Name**: `mcp__plugin_google-maps_google-maps__search_places`

**Description**: Search for places by name, category, type, or location. Returns detailed information about matching locations.

**Parameters**:
- `query` (required, string): Search query (e.g., "restaurants near Times Square", "coffee shops", "Eiffel Tower")
- `location` (optional, object): Latitude/longitude bias for search results
  - `latitude` (number): Latitude coordinate
  - `longitude` (number): Longitude coordinate
- `radius` (optional, number): Search radius in meters (default: 5000, max: 50000)
- `type` (optional, string): Place type filter (e.g., "restaurant", "cafe", "museum", "hotel")

**Returns**:
- `places` (array): List of matching places
  - `name` (string): Place name
  - `formatted_address` (string): Full address
  - `location` (object): Coordinates (lat, lng)
  - `place_id` (string): Google Place ID
  - `rating` (number): User rating (1-5 scale)
  - `user_ratings_total` (number): Number of reviews
  - `types` (array): Place categories
  - `price_level` (number): Price range (0-4, 0=free, 4=expensive)
  - `opening_hours` (object): Operating hours information
  - `business_status` (string): "OPERATIONAL" or "CLOSED_TEMPORARILY"

**Example**:
```javascript
// Search for restaurants near a location
search_places({
  query: "italian restaurants",
  location: {
    latitude: 40.7580,
    longitude: -73.9855
  },
  radius: 2000,
  type: "restaurant"
})
```

**Use Cases**:
- Find restaurants for meal planning
- Search hotels for accommodation
- Locate tourist attractions
- Find shopping venues
- Discover entertainment venues
- Search transportation hubs (airports, train stations)

---

## Best Practices

1. **Specific Queries**: Use detailed search terms for better results
   - Good: "vegan restaurants in Manhattan"
   - Poor: "food"

2. **Location Bias**: Provide location coordinates when searching in specific areas
   - Improves relevance of results
   - Required for radius-based searches

3. **Type Filtering**: Use type parameter to narrow results
   - Common types: restaurant, cafe, bar, lodging, museum, park, store
   - See [Google Place Types](https://developers.google.com/maps/documentation/places/web-service/supported_types)

4. **Rating Filtering**: Filter results in post-processing
   - Minimum rating: 3.5-4.0 for quality recommendations
   - Minimum reviews: 20+ for reliability

5. **Result Validation**:
   - Check `business_status` is "OPERATIONAL"
   - Verify `opening_hours` match travel schedule
   - Consider `price_level` against budget

6. **Token Optimization**:
   - Request only needed place details
   - Limit search radius to relevant area
   - Filter results before presenting to user

## Error Handling

**Common Errors**:
- Invalid API key: Check `GOOGLE_MAPS_API_KEY` environment variable
- Quota exceeded: Implement rate limiting or caching
- No results: Broaden search query or increase radius
- Invalid coordinates: Validate latitude (-90 to 90) and longitude (-180 to 180)

**Retry Pattern**:
```
Attempt 1: Direct MCP call
Attempt 2: Retry after 2s delay
Attempt 3: Retry after 5s delay
Fallback: Use WebSearch with same query
```

## Integration Examples

**Meals Agent**:
```javascript
// Search for breakfast cafes
search_places({
  query: "breakfast cafe",
  location: { latitude: hotel_lat, longitude: hotel_lng },
  radius: 1500,
  type: "cafe"
})
// Filter: rating >= 4.0, user_ratings_total >= 20, price_level <= 2
```

**Accommodation Agent**:
```javascript
// Search for hotels
search_places({
  query: "hotels in downtown",
  location: { latitude: city_lat, longitude: city_lng },
  radius: 3000,
  type: "lodging"
})
// Filter: rating >= 4.0, business_status == "OPERATIONAL"
```

**Attractions Agent**:
```javascript
// Search for museums
search_places({
  query: "art museums",
  location: { latitude: city_lat, longitude: city_lng },
  radius: 5000,
  type: "museum"
})
// Filter: rating >= 4.0, check opening_hours
```

**Shopping Agent**:
```javascript
// Search for markets
search_places({
  query: "local markets",
  location: { latitude: city_lat, longitude: city_lng },
  radius: 3000,
  type: "store"
})
```

**Entertainment Agent**:
```javascript
// Search for nightlife
search_places({
  query: "live music venues",
  location: { latitude: city_lat, longitude: city_lng },
  radius: 4000,
  type: "night_club"
})
```
