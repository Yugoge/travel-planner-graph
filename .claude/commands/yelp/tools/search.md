# Yelp - Restaurant Search Tools

Restaurant discovery and details tools for finding dining options worldwide.

## Available Tools

### 1. search_businesses

Natural language or structured restaurant search.

**MCP Tool**: `search_businesses`

**Parameters**:
- `query` (required): Natural language search query or specific terms
  - Examples: "best tacos in Austin", "vegetarian restaurants", "romantic dinner spots"
- `location` (required): City, neighborhood, or address
  - Examples: "New York, NY", "Tokyo, Japan", "123 Main St, San Francisco"
- `latitude` (optional): Latitude for precise location-based search
- `longitude` (optional): Longitude for precise location-based search
- `radius` (optional): Search radius in meters (max 40000)
- `categories` (optional): Yelp category filter (e.g., "italian", "seafood", "vegan")
- `price` (optional): Price level filter (1=$, 2=$$, 3=$$$, 4=$$$$)
- `open_now` (optional): Filter to only open businesses (boolean)
- `limit` (optional): Number of results (default 20, max 50)

**Returns**:
- Business name and ID
- Rating (0-5 stars)
- Review count
- Price level ($, $$, $$$, $$$$)
- Categories (cuisine types)
- Address and location coordinates
- Phone number
- Business URL (for reservations/booking)
- Distance from search location
- Photos
- Review highlights

**Example**:
```javascript
// Natural language search
search_businesses({
  query: "authentic Japanese ramen",
  location: "San Francisco, CA",
  open_now: true,
  limit: 10
})

// Structured search with filters
search_businesses({
  query: "restaurants",
  location: "New York, NY",
  categories: "italian",
  price: 2,  // $$
  radius: 5000,  // 5km
  limit: 15
})
```

**Use Cases**:
- Find restaurants near attractions
- Search by cuisine type
- Filter by budget (price level)
- Discover highly-rated options
- Find open restaurants now

---

### 2. get_business_details

Get detailed information about a specific restaurant.

**MCP Tool**: `get_business_details`

**Parameters**:
- `business_id` (required): Yelp business ID from search results

**Returns**:
- Complete business information
- Full address and coordinates
- All photos
- Opening hours (by day)
- Special hours (holidays)
- Detailed review highlights
- Popular dishes or items
- Amenities (parking, wifi, etc)
- Transaction types (delivery, pickup, reservation)
- Rating breakdown

**Example**:
```javascript
// Get details for specific restaurant
get_business_details({
  business_id: "yelp-business-id-12345"
})
```

**Use Cases**:
- Verify opening hours before recommendation
- Get complete address for directions
- Check amenities (wheelchair accessible, outdoor seating)
- Find booking/reservation URL
- Get detailed review information

---

### 3. search_by_category

Search restaurants by Yelp category or cuisine type.

**MCP Tool**: `search_by_category`

**Parameters**:
- `category` (required): Yelp category alias
  - Common categories: "italian", "chinese", "mexican", "japanese", "seafood", "vegan", "bbq", "cafes", "bakeries", "steakhouses"
- `location` (required): City or address
- `latitude` (optional): Latitude for location
- `longitude` (optional): Longitude for location
- `radius` (optional): Search radius in meters
- `price` (optional): Price filter (1-4)
- `open_now` (optional): Filter to open businesses
- `limit` (optional): Number of results (max 50)

**Returns**:
Same structure as `search_businesses`:
- Business details
- Ratings and reviews
- Location and contact info
- Price level
- Photos

**Example**:
```javascript
// Find Italian restaurants
search_by_category({
  category: "italian",
  location: "Chicago, IL",
  price: 2,
  limit: 10
})

// Find vegetarian options
search_by_category({
  category: "vegan",
  location: "Los Angeles, CA",
  open_now: true,
  radius: 3000
})
```

**Use Cases**:
- Browse by cuisine type
- Find specific dietary options (vegan, halal, kosher)
- Discover category-specific recommendations
- Filter by food type for themed meals

---

## Common Yelp Categories

**Cuisine Types**:
- `italian`, `chinese`, `japanese`, `mexican`, `indian`, `thai`, `french`, `korean`, `vietnamese`

**Dietary Preferences**:
- `vegan`, `vegetarian`, `gluten_free`, `halal`, `kosher`

**Meal Types**:
- `breakfast_brunch`, `cafes`, `bakeries`, `desserts`

**Restaurant Types**:
- `seafood`, `steakhouses`, `pizza`, `burgers`, `sandwiches`, `salad`, `soup`

**Dining Style**:
- `fine_dining`, `casual_dining`, `fast_food`, `food_trucks`, `buffets`

For complete list: https://www.yelp.com/developers/documentation/v3/all_category_list

---

## Best Practices

### 1. Search Strategy

**For breakfast recommendations**:
```javascript
search_businesses({
  query: "breakfast",
  location: destinationCity,
  categories: "breakfast_brunch,cafes",
  open_now: true,
  limit: 10
})
```

**For lunch near attraction**:
```javascript
search_businesses({
  query: "lunch restaurants",
  latitude: attractionLat,
  longitude: attractionLon,
  radius: 1000,  // 1km radius
  price: 2,  // $$
  limit: 10
})
```

**For special dinner**:
```javascript
search_businesses({
  query: "romantic dinner",
  location: destinationCity,
  categories: "italian,french,fine_dining",
  price: 3,  // $$$
  limit: 15
})
```

### 2. Error Handling

**Retry logic**:
```javascript
async function searchWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_businesses(params);
    } catch (error) {
      if (error.status === 429) {
        // Rate limit - wait and retry
        await sleep(2000 * (i + 1));
        continue;
      }
      if (error.status >= 500) {
        // Server error - retry
        await sleep(1000 * (i + 1));
        continue;
      }
      // Permanent error - don't retry
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Fallback to WebSearch**:
```javascript
try {
  const results = await search_businesses({
    query: "Italian restaurants",
    location: city
  });
  return formatYelpResults(results);
} catch (error) {
  console.warn('Yelp unavailable, falling back to WebSearch');
  return await webSearchRestaurants(city, "Italian");
}
```

### 3. Response Parsing

**Extract key information**:
```javascript
function parseYelpBusiness(business) {
  return {
    name: business.name,
    location: business.location.display_address.join(', '),
    cost: business.price ? business.price.length * 10 : 20,  // Estimate: $ = $10, $$ = $20, etc
    cuisine: business.categories.map(c => c.title).join(', '),
    rating: business.rating,
    review_count: business.review_count,
    phone: business.phone,
    booking_url: business.url,
    notes: generateNotes(business)
  };
}

function generateNotes(business) {
  const notes = [];

  if (business.rating >= 4.5) {
    notes.push('Highly rated');
  }

  if (business.review_count > 500) {
    notes.push('Very popular');
  }

  if (business.transactions?.includes('restaurant_reservation')) {
    notes.push('Reservations recommended');
  }

  if (business.is_closed) {
    notes.push('Currently closed - verify hours');
  }

  return notes.join(', ');
}
```

**Price conversion**:
```javascript
function estimateCostPerPerson(priceLevel) {
  const priceMap = {
    '$': 15,      // Budget
    '$$': 30,     // Moderate
    '$$$': 60,    // Upscale
    '$$$$': 100   // Fine dining
  };

  return priceMap[priceLevel] || 25;  // Default estimate
}
```

**Filter by rating**:
```javascript
function filterHighQuality(businesses) {
  return businesses.filter(b => {
    // Minimum 3.5 stars with at least 20 reviews
    return b.rating >= 3.5 && b.review_count >= 20;
  });
}
```

### 4. Location Convenience

**Calculate distance from accommodation**:
```javascript
function sortByProximity(businesses, hotelLat, hotelLon) {
  return businesses.sort((a, b) => {
    const distA = calculateDistance(
      hotelLat, hotelLon,
      a.coordinates.latitude, a.coordinates.longitude
    );
    const distB = calculateDistance(
      hotelLat, hotelLon,
      b.coordinates.latitude, b.coordinates.longitude
    );
    return distA - distB;
  });
}

function calculateDistance(lat1, lon1, lat2, lon2) {
  // Haversine formula for distance in km
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

function toRad(degrees) {
  return degrees * Math.PI / 180;
}
```

### 5. Dietary Restrictions

**Filter by dietary needs**:
```javascript
async function findDietaryOptions(location, restrictions) {
  const categoryMap = {
    'vegetarian': 'vegetarian,vegan',
    'vegan': 'vegan',
    'gluten-free': 'gluten_free',
    'halal': 'halal',
    'kosher': 'kosher'
  };

  const categories = restrictions
    .map(r => categoryMap[r.toLowerCase()])
    .filter(Boolean)
    .join(',');

  if (!categories) {
    // No specific categories, search with query
    return search_businesses({
      query: `${restrictions.join(' ')} restaurants`,
      location: location,
      limit: 15
    });
  }

  return search_by_category({
    category: categories.split(',')[0],  // Use first category
    location: location,
    limit: 15
  });
}
```

### 6. Budget Optimization

**Recommend within budget**:
```javascript
function filterByBudget(businesses, dailyBudget, mealType) {
  const mealBudgetPercent = {
    'breakfast': 0.15,  // 15% of daily budget
    'lunch': 0.30,      // 30% of daily budget
    'dinner': 0.40      // 40% of daily budget
  };

  const maxCost = dailyBudget * mealBudgetPercent[mealType];

  return businesses.filter(b => {
    const estimatedCost = estimateCostPerPerson(b.price);
    return estimatedCost <= maxCost;
  });
}
```

---

## Integration with Meals Agent

The meals agent should:

1. **Load this file** when researching dining options
2. **Use search_businesses** for general restaurant discovery
3. **Use search_by_category** for specific cuisine types
4. **Use get_business_details** to verify hours and amenities
5. **Parse response** for name, location, cost, rating, notes
6. **Filter results** by rating, reviews, dietary needs, budget
7. **Save structured data** to `meals.json`
8. **Fall back to WebSearch** if MCP unavailable

Example workflow:
```
1. Read requirements: dietary restrictions, budget, preferences
2. For each day's lunch near attraction:
   a. Invoke /yelp search (loads this file)
   b. Call search_businesses with attraction coordinates
   c. Filter by rating (>3.5), price (within budget)
   d. Select top option
   e. Parse and structure data
3. Save to meals.json
4. Return complete
```

---

## Response Structure Example

```json
{
  "businesses": [
    {
      "id": "yelp-business-id",
      "name": "Mario's Italian Restaurant",
      "rating": 4.5,
      "review_count": 342,
      "price": "$$",
      "categories": [
        {"alias": "italian", "title": "Italian"},
        {"alias": "pizza", "title": "Pizza"}
      ],
      "location": {
        "address1": "123 Main St",
        "city": "San Francisco",
        "zip_code": "94102",
        "country": "US",
        "display_address": ["123 Main St", "San Francisco, CA 94102"]
      },
      "coordinates": {
        "latitude": 37.7749,
        "longitude": -122.4194
      },
      "phone": "+14155551234",
      "url": "https://www.yelp.com/biz/marios-italian-restaurant",
      "image_url": "https://s3-media.yelp.com/photo.jpg",
      "distance": 1234.56,  // meters from search location
      "transactions": ["delivery", "pickup", "restaurant_reservation"],
      "is_closed": false
    }
  ],
  "total": 245
}
```
