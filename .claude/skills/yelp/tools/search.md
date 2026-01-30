# Yelp - Restaurant Search Tools

Comprehensive restaurant search and discovery using Yelp Fusion AI MCP.

## MCP Tools

### Tool 1: search_businesses

**MCP Tool Name**: `mcp__plugin_yelp_yelp__search_businesses`

Natural language or structured search for restaurants and businesses.

**Parameters**:
- `query` (required): Natural language search query OR structured filters
  - Natural: "best vegetarian restaurants near Union Square"
  - Structured: JSON with `term`, `location`, `categories`, `price`, `radius`
- `location` (optional): City, address, or coordinates
- `latitude` (optional): Latitude for geographic search
- `longitude` (optional): Longitude for geographic search
- `radius` (optional): Search radius in meters (max 40000)
- `categories` (optional): Comma-separated category aliases
- `price` (optional): Price levels (1, 2, 3, 4 for $, $$, $$$, $$$$)
- `open_now` (optional): Filter to currently open businesses
- `limit` (optional): Number of results (default 20, max 50)

**Returns**:
```json
{
  "businesses": [
    {
      "id": "business-id",
      "name": "Restaurant Name",
      "rating": 4.5,
      "review_count": 234,
      "price": "$$",
      "categories": [
        {"alias": "italian", "title": "Italian"}
      ],
      "location": {
        "address1": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94102"
      },
      "coordinates": {
        "latitude": 37.7749,
        "longitude": -122.4194
      },
      "url": "https://www.yelp.com/biz/restaurant-name",
      "phone": "+14155551234",
      "hours": [
        {
          "is_open_now": true,
          "hours_type": "REGULAR"
        }
      ],
      "transactions": ["delivery", "pickup", "restaurant_reservation"]
    }
  ],
  "total": 150
}
```

**Example**:
```javascript
// Natural language search
search_businesses({
  query: "best breakfast cafes near downtown with outdoor seating"
})

// Structured search with filters
search_businesses({
  query: JSON.stringify({
    term: "italian restaurant",
    location: "San Francisco, CA",
    categories: "italian,pizza",
    price: "2,3",
    radius: 2000,
    open_now: true,
    limit: 10
  })
})
```

**Use Cases**:
- Search breakfast near accommodation
- Find lunch options near attractions
- Discover dinner restaurants by cuisine
- Filter by dietary restrictions and budget
- Get restaurants within walking distance

---

### Tool 2: get_business_details

**MCP Tool Name**: `mcp__plugin_yelp_yelp__get_business_details`

Get detailed information about a specific business by ID.

**Parameters**:
- `business_id` (required): Yelp business ID from search results

**Returns**:
```json
{
  "id": "business-id",
  "name": "Restaurant Name",
  "rating": 4.5,
  "review_count": 234,
  "price": "$$",
  "categories": [...],
  "location": {...},
  "coordinates": {...},
  "photos": ["url1", "url2", "url3"],
  "hours": [
    {
      "open": [
        {
          "day": 0,
          "start": "0800",
          "end": "2200"
        }
      ],
      "hours_type": "REGULAR",
      "is_open_now": true
    }
  ],
  "transactions": [...],
  "messaging": {
    "url": "...",
    "use_case_text": "..."
  },
  "special_hours": [...]
}
```

**Example**:
```javascript
get_business_details({
  business_id: "gary-danko-san-francisco"
})
```

**Use Cases**:
- Verify restaurant details before adding to itinerary
- Get complete operating hours schedule
- Check photos and ambiance
- Confirm transaction options (delivery, pickup, reservation)

---

### Tool 3: search_by_category

**MCP Tool Name**: `mcp__plugin_yelp_yelp__search_by_category`

Search restaurants by cuisine category or type.

**Parameters**:
- `category` (required): Category alias (see Common Categories below)
- `location` (required): City, address, or coordinates
- `latitude` (optional): Latitude for geographic search
- `longitude` (optional): Longitude for geographic search
- `radius` (optional): Search radius in meters
- `price` (optional): Price levels (1, 2, 3, 4)
- `open_now` (optional): Filter to currently open
- `limit` (optional): Number of results

**Returns**:
Same structure as `search_businesses`

**Example**:
```javascript
search_by_category({
  category: "vegetarian",
  location: "San Francisco, CA",
  price: "1,2",
  radius: 1500,
  limit: 10
})
```

**Use Cases**:
- Search by dietary restriction (vegetarian, vegan, halal, kosher)
- Find specific cuisine type (italian, chinese, mexican)
- Discover breakfast cafes or brunch spots
- Filter by meal type and budget

---

## Common Yelp Categories

### Dietary Restrictions
- `vegetarian` - Vegetarian
- `vegan` - Vegan
- `halal` - Halal
- `kosher` - Kosher
- `gluten_free` - Gluten-Free (limited support)

### Cuisine Types
- `italian` - Italian
- `chinese` - Chinese
- `mexican` - Mexican
- `japanese` - Japanese
- `thai` - Thai
- `indian` - Indian
- `french` - French
- `mediterranean` - Mediterranean
- `american` - American (Traditional)
- `newamerican` - American (New)

### Meal Types
- `breakfast_brunch` - Breakfast & Brunch
- `cafes` - Cafes
- `coffee` - Coffee & Tea
- `sandwiches` - Sandwiches
- `pizza` - Pizza
- `burgers` - Burgers
- `seafood` - Seafood
- `steakhouses` - Steakhouses

### Restaurant Types
- `restaurants` - Restaurants (general)
- `food` - Food (general)
- `bars` - Bars
- `gastropubs` - Gastropubs
- `diners` - Diners
- `buffets` - Buffets

---

## Search Strategy

### Breakfast Search
```javascript
// Near accommodation
search_businesses({
  query: JSON.stringify({
    term: "breakfast cafe",
    latitude: hotel_lat,
    longitude: hotel_lon,
    categories: "breakfast_brunch,cafes,coffee",
    price: "1,2",
    radius: 500,
    open_now: true,
    limit: 10
  })
})
```

### Lunch Search
```javascript
// Near attraction
search_businesses({
  query: JSON.stringify({
    term: "lunch restaurant",
    latitude: attraction_lat,
    longitude: attraction_lon,
    categories: "restaurants,sandwiches,cafes",
    price: "2,3",
    radius: 1000,
    limit: 10
  })
})
```

### Dinner Search
```javascript
// By cuisine preference
search_by_category({
  category: "italian",
  location: "San Francisco, CA",
  price: "2,3,4",
  radius: 3000,
  limit: 15
})
```

---

## Error Handling

### Retry Logic

```javascript
async function searchWithRetry(params, maxAttempts = 3) {
  let lastError;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const result = await search_businesses(params);
      return { success: true, data: result };
    } catch (error) {
      lastError = error;

      // Don't retry permanent errors
      if (error.status === 401 || error.status === 403 || error.status === 400) {
        break;
      }

      // Exponential backoff for transient errors
      if (error.status === 429 || error.status >= 500) {
        const delay = Math.pow(2, attempt - 1) * 1000;
        await sleep(delay);
        continue;
      }

      break;
    }
  }

  return {
    success: false,
    error: lastError,
    fallback_to_websearch: true
  };
}
```

### Fallback to WebSearch

```javascript
// Try Yelp first
const yelpResult = await searchWithRetry(params);

if (!yelpResult.success || yelpResult.data.businesses.length === 0) {
  // Fall back to WebSearch
  const webResult = await WebSearch({
    query: `best restaurants ${location} ${cuisine} ${dietary_restriction}`
  });

  // Parse WebSearch results and structure similarly
  return {
    source: "websearch",
    data: parseWebSearchResults(webResult)
  };
}
```

---

## Response Parsing Helpers

### Filter by Quality

```javascript
function filterByQuality(businesses) {
  return businesses.filter(b =>
    b.rating >= 3.5 &&
    b.review_count >= 20
  );
}
```

### Filter by Budget

```javascript
function filterByBudget(businesses, maxPrice) {
  const priceMap = { '$': 1, '$$': 2, '$$$': 3, '$$$$': 4 };
  return businesses.filter(b =>
    priceMap[b.price] <= maxPrice
  );
}
```

### Calculate Distance

```javascript
function haversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c; // Distance in km
}

function filterByDistance(businesses, targetLat, targetLon, maxDistanceKm) {
  return businesses
    .map(b => ({
      ...b,
      distance: haversineDistance(
        targetLat, targetLon,
        b.coordinates.latitude, b.coordinates.longitude
      )
    }))
    .filter(b => b.distance <= maxDistanceKm)
    .sort((a, b) => a.distance - b.distance);
}
```

### Filter by Dietary Restrictions

```javascript
function filterByDiet(businesses, dietaryNeeds) {
  if (!dietaryNeeds || dietaryNeeds.length === 0) return businesses;

  return businesses.filter(b =>
    b.categories.some(cat =>
      dietaryNeeds.some(diet =>
        cat.alias.includes(diet.toLowerCase())
      )
    )
  );
}
```

### Estimate Cost

```javascript
function estimateCost(priceLevel, mealType) {
  const priceMap = {
    '$': { breakfast: 8, lunch: 12, dinner: 15 },
    '$$': { breakfast: 15, lunch: 20, dinner: 30 },
    '$$$': { breakfast: 25, lunch: 35, dinner: 50 },
    '$$$$': { breakfast: 40, lunch: 60, dinner: 80 }
  };

  return priceMap[priceLevel]?.[mealType] || 20;
}
```

---

## Best Practices

1. **Use Natural Language**: Yelp's AI handles complex queries well
   - "vegetarian brunch with outdoor seating near downtown"
   - "romantic italian dinner under $50 per person"

2. **Filter Results**: Always apply quality filters
   - Minimum rating: 3.5 stars
   - Minimum reviews: 20 reviews
   - Maximum distance: 2km from target location

3. **Check Operating Hours**: Verify restaurant is open
   - Use `open_now: true` filter
   - Verify hours match meal time (breakfast 7-11am, lunch 11am-3pm, dinner 5-10pm)

4. **Track Variety**: Avoid repeating restaurants or cuisines
   - Keep list of used restaurant IDs
   - Track cuisine types per day
   - Mix price levels throughout trip

5. **Consider Location**: Optimize travel time
   - Breakfast: <500m from accommodation
   - Lunch: <1km from attraction
   - Dinner: <3km, may travel further for special meal

6. **Budget Allocation**: Distribute daily meal budget
   - Breakfast: 15% of daily meal budget
   - Lunch: 30% of daily meal budget
   - Dinner: 40% of daily meal budget
   - Buffer: 15% for snacks/drinks

7. **Handle Errors Gracefully**:
   - Retry transient errors (429, 5xx)
   - Fall back to WebSearch on failure
   - Document data source in output

8. **Optimize API Usage**:
   - Use radius filters to limit results
   - Request only needed fields
   - Cache results when repeating queries
   - Stay within rate limits (5,000 calls/day)

---

## Common Error Messages

- **401 Unauthorized**: API key missing or invalid
  - Solution: Check MCP server configuration

- **429 Too Many Requests**: Rate limit exceeded
  - Solution: Implement exponential backoff, reduce query frequency

- **400 Bad Request**: Invalid parameters
  - Solution: Validate location, categories, and search term

- **404 Not Found**: Business ID doesn't exist
  - Solution: Re-search or skip this business

- **5xx Server Error**: Yelp service issue
  - Solution: Retry with backoff, then fall back to WebSearch
