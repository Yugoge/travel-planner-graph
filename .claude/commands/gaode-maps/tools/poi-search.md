# Gaode Maps - POI Search Tools

Point of Interest (POI) search tools for finding restaurants, hotels, attractions, and services in China.

## Available Tools

### 1. poi_search_keyword

Search for POIs using keywords and filters.

**MCP Tool**: `poi_search_keyword`

**Parameters**:
- `keywords` (required): Search keywords (e.g., "火锅", "hotel", "景点")
- `city` (optional): City name or city code (e.g., "成都" or "028")
- `citylimit` (optional): Limit results to specified city (true/false)
- `types` (optional): POI category codes (see category reference below)
- `page_size` (optional): Results per page (default 20, max 50)
- `page_num` (optional): Page number (default 1)

**Returns**:
- POI name (Chinese)
- Address
- Coordinates (GCJ-02)
- POI type/category
- District
- Phone number (if available)
- Average rating (if available)
- Distance from search center (if location specified)

**Example**:
```javascript
// Search for hotpot restaurants in Chongqing
poi_search_keyword({
  keywords: "火锅",
  city: "重庆",
  citylimit: true,
  types: "050100",  // Restaurant category
  page_size: 10
})
```

**Use Cases**:
- Restaurant recommendations
- Hotel search
- Attraction discovery
- Shopping mall location
- Service finder (ATM, hospital, pharmacy)

---

### 2. poi_search_nearby

Search for POIs near a specific location.

**MCP Tool**: `poi_search_nearby`

**Parameters**:
- `location` (required): Center point coordinates (e.g., "116.481488,39.990464")
- `keywords` (optional): Filter by keywords
- `types` (optional): POI category codes
- `radius` (optional): Search radius in meters (default 1000, max 50000)
- `page_size` (optional): Results per page (default 20, max 50)
- `page_num` (optional): Page number (default 1)

**Returns**:
- Same as poi_search_keyword, plus:
- Distance from center point (meters)
- Direction from center point

**Example**:
```javascript
// Find restaurants within 500m of hotel
poi_search_nearby({
  location: "104.065735,30.659462",  // Chengdu coordinates
  keywords: "餐厅",
  radius: 500,
  page_size: 10
})
```

**Use Cases**:
- "Near me" searches
- Walking-distance recommendations
- Area exploration
- Convenience planning

---

### 3. poi_detail

Get detailed information about a specific POI.

**MCP Tool**: `poi_detail`

**Parameters**:
- `id` (required): POI ID (from search results)

**Returns**:
- Full name and alias
- Complete address
- Coordinates (GCJ-02)
- Phone numbers
- Website URL
- Business hours
- Photos (if available)
- Rating and reviews summary
- Parking information
- Transit access

**Example**:
```javascript
// Get details for a specific restaurant
poi_detail({
  id: "B000A7BD6C"  // POI ID from search
})
```

**Use Cases**:
- Detailed venue information
- Contact details for reservations
- Business hours verification
- Photo gallery for user preview

---

## POI Category Codes Reference

Common categories for travel planning:

### Accommodation
- `100000`: Hotels
- `100100`: Star hotels
- `100200`: Express hotels
- `100300`: Hostels

### Dining
- `050000`: Food & Beverages
- `050100`: Chinese restaurants
- `050200`: Foreign restaurants
- `050300`: Fast food
- `050400`: Cafés & tea houses

### Attractions
- `110000`: Tourist attractions
- `110100`: Parks & squares
- `110200`: Museums
- `110300`: Religious sites
- `110400`: Historical sites

### Shopping
- `060000`: Shopping
- `060100`: Shopping malls
- `060200`: Supermarkets
- `060300`: Markets
- `060400`: Specialty stores

### Entertainment
- `090000`: Entertainment
- `090100`: Theaters & cinemas
- `090200`: KTV
- `090300`: Bars & clubs
- `090400`: Recreation centers

### Services
- `070000`: Life services
- `070100`: ATMs & banks
- `070200`: Hospitals
- `070300`: Pharmacies
- `070400`: Post offices

### Transportation
- `150000`: Transportation facilities
- `150100`: Gas stations
- `150200`: Parking lots
- `150300`: Train stations
- `150400`: Bus stations
- `150500`: Airports
- `150600`: Subway stations

---

## Best Practices

### 1. Search Strategy

**Broad search first**:
```javascript
// Start with general keywords
poi_search_keyword({
  keywords: "餐厅",
  city: "重庆",
  page_size: 20
})

// Then filter by category
poi_search_keyword({
  keywords: "火锅",
  city: "重庆",
  types: "050100",
  page_size: 10
})
```

**Nearby search for convenience**:
```javascript
// First geocode the accommodation
const hotelCoords = await geocode({ address: "重庆市渝中区解放碑" });

// Then search nearby
poi_search_nearby({
  location: hotelCoords,
  keywords: "餐厅",
  radius: 1000  // 1km walking distance
})
```

### 2. Multi-Language Input

Accept both English and Chinese:
```javascript
function normalizeKeywords(input) {
  const translations = {
    'restaurant': '餐厅',
    'hotel': '酒店',
    'attraction': '景点',
    'shopping': '购物',
    'hospital': '医院'
  };

  return translations[input.toLowerCase()] || input;
}

// Usage
poi_search_keyword({
  keywords: normalizeKeywords(userInput),
  city: city
})
```

### 3. Result Filtering

**Filter by rating**:
```javascript
function filterByRating(results, minRating = 4.0) {
  return results.filter(poi => {
    const rating = parseFloat(poi.rating || 0);
    return rating >= minRating;
  });
}
```

**Filter by distance**:
```javascript
function filterByDistance(results, maxDistance = 1000) {
  return results.filter(poi => {
    const distance = parseInt(poi.distance || 0);
    return distance <= maxDistance;
  });
}
```

**Sort by relevance**:
```javascript
function sortByRelevance(results, preferences) {
  return results.sort((a, b) => {
    // Prioritize higher ratings
    const ratingDiff = (b.rating || 0) - (a.rating || 0);
    if (Math.abs(ratingDiff) > 0.5) return ratingDiff;

    // Then by distance
    return (a.distance || 0) - (b.distance || 0);
  });
}
```

### 4. Pagination

Handle large result sets:
```javascript
async function getAllResults(searchParams, maxPages = 3) {
  const allResults = [];

  for (let page = 1; page <= maxPages; page++) {
    const results = await poi_search_keyword({
      ...searchParams,
      page_num: page,
      page_size: 50
    });

    allResults.push(...results.pois);

    if (results.pois.length < 50) break;  // Last page
  }

  return allResults;
}
```

### 5. Error Handling

**Handle empty results**:
```javascript
async function searchWithFallback(keywords, city) {
  let results = await poi_search_keyword({ keywords, city, citylimit: true });

  if (results.count === 0) {
    // Expand search to broader area
    results = await poi_search_keyword({ keywords, city, citylimit: false });
  }

  if (results.count === 0) {
    // Fall back to web search
    console.warn('No POI results, using WebSearch');
    return await webSearchPOI(keywords, city);
  }

  return results;
}
```

**Handle invalid coordinates**:
```javascript
async function safeNearbySearch(location, keywords) {
  try {
    return await poi_search_nearby({ location, keywords });
  } catch (error) {
    if (error.message.includes('invalid location')) {
      // Geocode the location first
      const coords = await geocode({ address: location });
      return await poi_search_nearby({
        location: `${coords.lng},${coords.lat}`,
        keywords
      });
    }
    throw error;
  }
}
```

### 6. Data Enrichment

Combine with detail lookup:
```javascript
async function enrichPOIResults(searchResults, limit = 5) {
  const topResults = searchResults.pois.slice(0, limit);

  const enriched = await Promise.all(
    topResults.map(async (poi) => {
      try {
        const details = await poi_detail({ id: poi.id });
        return { ...poi, ...details };
      } catch (error) {
        console.warn(`Failed to get details for ${poi.id}`);
        return poi;
      }
    })
  );

  return enriched;
}
```

---

## Integration with Specialist Agents

### Meals Agent
```javascript
// 1. Search restaurants near accommodation
const restaurants = await poi_search_nearby({
  location: accommodationCoords,
  keywords: cuisineType,  // e.g., "火锅", "川菜"
  types: "050100",
  radius: 1000
});

// 2. Filter by rating and budget
const filtered = filterByRatingAndPrice(restaurants, minRating, maxPrice);

// 3. Get details for top 3
const detailed = await enrichPOIResults(filtered, 3);

// 4. Save to meals.json
```

### Accommodation Agent
```javascript
// 1. Search hotels in city/district
const hotels = await poi_search_keyword({
  keywords: "酒店",
  city: cityName,
  types: "100000",
  page_size: 20
});

// 2. Filter by user preferences (budget, location)
const suitable = filterByPreferences(hotels, userPrefs);

// 3. Get details including photos and reviews
const detailed = await enrichPOIResults(suitable, 5);

// 4. Save to accommodation.json
```

### Attractions Agent
```javascript
// 1. Search attractions by user interests
const attractions = await poi_search_keyword({
  keywords: userInterest,  // e.g., "博物馆", "古镇"
  city: cityName,
  types: "110000",
  page_size: 20
});

// 2. Get details and business hours
const detailed = await enrichPOIResults(attractions, 10);

// 3. Check if open on travel dates
const available = filterByBusinessHours(detailed, travelDates);

// 4. Save to attractions.json
```

### Shopping Agent
```javascript
// 1. Search shopping areas
const shopping = await poi_search_keyword({
  keywords: "购物中心",
  city: cityName,
  types: "060100",
  page_size: 10
});

// 2. Find specialty markets if user interested
if (userWantsLocalMarkets) {
  const markets = await poi_search_keyword({
    keywords: "市场",
    city: cityName,
    types: "060300"
  });
}

// 3. Save to shopping.json
```

---

## Example: Complete Restaurant Search

```javascript
async function findRestaurants(city, accommodationAddress, cuisine, budget) {
  // 1. Geocode accommodation
  const coords = await geocode({ address: accommodationAddress });

  // 2. Search nearby restaurants
  const results = await poi_search_nearby({
    location: `${coords.lng},${coords.lat}`,
    keywords: cuisine,
    types: "050100",
    radius: 1000,
    page_size: 20
  });

  // 3. Filter by rating
  const highRated = filterByRating(results.pois, 4.0);

  // 4. Get details for top 5
  const detailed = await enrichPOIResults({ pois: highRated }, 5);

  // 5. Estimate prices and filter by budget
  const affordable = detailed.filter(poi => estimatePrice(poi) <= budget);

  return affordable;
}
```
