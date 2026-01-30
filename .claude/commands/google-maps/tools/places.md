# Google Maps - Places Search Tools

Point of Interest (POI) search tools for finding restaurants, hotels, attractions, and services worldwide using Google Maps Grounding Lite.

## Available Tools

### 1. search_places

Search for places using text query with comprehensive filtering options.

**MCP Tool**: `search_places`

**Parameters**:
- `textQuery` (required): Search query text (e.g., "restaurants in Paris", "hotels near Eiffel Tower")
- `includedType` (optional): Place type filter (e.g., "restaurant", "hotel", "tourist_attraction")
- `locationBias` (optional): Geographic bias for results
  - `circle`: Center point with radius (lat, lng, radius_meters)
  - `rectangle`: Bounding box (low lat/lng, high lat/lng)
- `maxResultCount` (optional): Maximum results to return (default 20, max varies by API)
- `minRating` (optional): Minimum star rating (0.0-5.0)
- `priceLevels` (optional): Price level filter (INEXPENSIVE, MODERATE, EXPENSIVE, VERY_EXPENSIVE)
- `openNow` (optional): Filter to currently open places (boolean)

**Returns**:
- Place ID (unique identifier)
- Display name (localized)
- Formatted address
- Location (latitude, longitude)
- Rating (1.0-5.0)
- User ratings total
- Price level
- Business status (OPERATIONAL, CLOSED_TEMPORARILY, CLOSED_PERMANENTLY)
- Opening hours
- Place types
- Photos (references)
- Website URL
- Phone number

**Example**:
```javascript
// Search for restaurants in Paris
search_places({
  textQuery: "best French restaurants in Paris",
  includedType: "restaurant",
  locationBias: {
    circle: {
      center: { latitude: 48.8566, longitude: 2.3522 },
      radius: 5000
    }
  },
  minRating: 4.0,
  maxResultCount: 10,
  priceLevels: ["MODERATE", "EXPENSIVE"]
})
```

**Use Cases**:
- Restaurant recommendations
- Hotel search with filters
- Tourist attraction discovery
- Shopping mall location
- Service finder (ATM, hospital, pharmacy)
- Event venue search

---

### 2. Place Type Reference

Common place types for travel planning:

**Accommodation**:
- `lodging` - General accommodation
- `hotel` - Hotels
- `hostel` - Hostels
- `resort_hotel` - Resort hotels
- `bed_and_breakfast` - B&Bs
- `guest_house` - Guest houses

**Dining**:
- `restaurant` - All restaurants
- `cafe` - Cafés
- `bar` - Bars
- `fast_food_restaurant` - Fast food
- `bakery` - Bakeries
- `meal_delivery` - Delivery services
- `meal_takeaway` - Takeout

**Attractions**:
- `tourist_attraction` - Tourist sites
- `museum` - Museums
- `art_gallery` - Art galleries
- `park` - Parks
- `zoo` - Zoos
- `aquarium` - Aquariums
- `amusement_park` - Theme parks
- `historical_landmark` - Historical sites
- `religious_site` - Temples, churches

**Shopping**:
- `shopping_mall` - Shopping centers
- `department_store` - Department stores
- `supermarket` - Supermarkets
- `clothing_store` - Clothing shops
- `jewelry_store` - Jewelry shops
- `book_store` - Bookstores

**Entertainment**:
- `night_club` - Nightclubs
- `movie_theater` - Cinemas
- `performing_arts_theater` - Theaters
- `casino` - Casinos
- `bowling_alley` - Bowling
- `stadium` - Stadiums

**Services**:
- `atm` - ATMs
- `bank` - Banks
- `hospital` - Hospitals
- `pharmacy` - Pharmacies
- `police` - Police stations
- `post_office` - Post offices

**Transportation**:
- `airport` - Airports
- `train_station` - Train stations
- `bus_station` - Bus stations
- `subway_station` - Subway/metro
- `taxi_stand` - Taxi stands
- `parking` - Parking facilities

---

## Best Practices

### 1. Search Strategy

**Broad search first**:
```javascript
// Start with general query
search_places({
  textQuery: "restaurants in Barcelona",
  maxResultCount: 20
})

// Then refine with filters
search_places({
  textQuery: "seafood restaurants Barcelona",
  includedType: "restaurant",
  minRating: 4.0,
  priceLevels: ["MODERATE"],
  maxResultCount: 10
})
```

**Location-biased search**:
```javascript
// Search near specific location (e.g., hotel)
search_places({
  textQuery: "breakfast cafe",
  locationBias: {
    circle: {
      center: { latitude: 41.3874, longitude: 2.1686 },
      radius: 1000  // 1km radius
    }
  },
  openNow: true,
  maxResultCount: 10
})
```

### 2. Multi-Language Support

Google Maps automatically handles multiple languages:
```javascript
// Query in any language
search_places({
  textQuery: "东京的寿司店",  // Sushi restaurants in Tokyo (Chinese)
  includedType: "restaurant",
  locationBias: {
    circle: {
      center: { latitude: 35.6762, longitude: 139.6503 },
      radius: 5000
    }
  }
})

// Or English
search_places({
  textQuery: "sushi restaurants in Tokyo",
  includedType: "restaurant"
})
```

### 3. Result Filtering

**Filter by rating**:
```javascript
function filterByRating(places, minRating = 4.0) {
  return places.filter(place =>
    place.rating && place.rating >= minRating
  );
}
```

**Filter by price**:
```javascript
function filterByPrice(places, maxPrice = "MODERATE") {
  const priceOrder = {
    "INEXPENSIVE": 1,
    "MODERATE": 2,
    "EXPENSIVE": 3,
    "VERY_EXPENSIVE": 4
  };

  return places.filter(place =>
    !place.priceLevel || priceOrder[place.priceLevel] <= priceOrder[maxPrice]
  );
}
```

**Filter by distance**:
```javascript
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c; // Distance in km
}

function filterByDistance(places, centerLat, centerLon, maxDistanceKm = 1) {
  return places.filter(place => {
    const distance = calculateDistance(
      centerLat, centerLon,
      place.location.latitude, place.location.longitude
    );
    return distance <= maxDistanceKm;
  });
}
```

### 4. Error Handling

**Retry logic**:
```javascript
async function searchPlacesWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_places(params);
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
async function searchPlacesWithFallback(textQuery, filters) {
  try {
    const places = await search_places({
      textQuery,
      ...filters
    });
    return { source: 'google_maps', data: places };
  } catch (error) {
    console.warn('Google Maps unavailable, falling back to WebSearch');
    const results = await webSearchPlaces(textQuery, filters);
    return { source: 'web_search', data: results };
  }
}
```

### 5. Response Parsing

**Extract essential information**:
```javascript
function formatPlaceForAgent(place) {
  return {
    name: place.displayName?.text || 'Unknown',
    address: place.formattedAddress || '',
    location: {
      lat: place.location?.latitude,
      lng: place.location?.longitude
    },
    rating: place.rating || 0,
    reviews: place.userRatingCount || 0,
    priceLevel: place.priceLevel || 'PRICE_LEVEL_UNSPECIFIED',
    openNow: place.currentOpeningHours?.openNow,
    website: place.websiteUri,
    phone: place.internationalPhoneNumber,
    types: place.types || []
  };
}
```

**Price level to USD estimate**:
```javascript
function estimatePriceUSD(priceLevel, placeType = 'restaurant') {
  const ranges = {
    restaurant: {
      'INEXPENSIVE': { min: 5, max: 15 },
      'MODERATE': { min: 15, max: 35 },
      'EXPENSIVE': { min: 35, max: 70 },
      'VERY_EXPENSIVE': { min: 70, max: 150 }
    },
    hotel: {
      'INEXPENSIVE': { min: 30, max: 70 },
      'MODERATE': { min: 70, max: 150 },
      'EXPENSIVE': { min: 150, max: 300 },
      'VERY_EXPENSIVE': { min: 300, max: 800 }
    }
  };

  const typeRanges = ranges[placeType] || ranges.restaurant;
  const range = typeRanges[priceLevel] || typeRanges['MODERATE'];
  return (range.min + range.max) / 2;
}
```

---

## Integration with Specialist Agents

### Meals Agent
```javascript
// 1. Search restaurants near accommodation
const restaurants = await search_places({
  textQuery: `${cuisineType} restaurants near ${accommodationAddress}`,
  includedType: "restaurant",
  locationBias: {
    circle: {
      center: { latitude: hotelLat, longitude: hotelLng },
      radius: 1000
    }
  },
  minRating: 4.0,
  priceLevels: ["MODERATE"],
  maxResultCount: 10
});

// 2. Filter and format results
const suitable = filterByPreferences(restaurants, userPreferences);

// 3. Save to meals.json
```

### Accommodation Agent
```javascript
// 1. Search hotels in destination
const hotels = await search_places({
  textQuery: `hotels in ${cityName}`,
  includedType: "hotel",
  locationBias: {
    circle: {
      center: { latitude: cityLat, longitude: cityLng },
      radius: 5000
    }
  },
  minRating: 4.0,
  priceLevels: budgetLevels,
  maxResultCount: 20
});

// 2. Filter by amenities (WiFi, breakfast)
const suitable = filterByAmenities(hotels, requiredAmenities);

// 3. Save to accommodation.json
```

### Attractions Agent
```javascript
// 1. Search tourist attractions
const attractions = await search_places({
  textQuery: `top tourist attractions in ${cityName}`,
  includedType: "tourist_attraction",
  locationBias: {
    circle: {
      center: { latitude: cityLat, longitude: cityLng },
      radius: 10000
    }
  },
  minRating: 4.5,
  maxResultCount: 20
});

// 2. Also search museums, parks
const museums = await search_places({
  textQuery: `museums in ${cityName}`,
  includedType: "museum",
  minRating: 4.0
});

// 3. Combine and filter
const combined = [...attractions, ...museums];
const filtered = filterByUserInterests(combined, userInterests);

// 4. Save to attractions.json
```

### Shopping Agent
```javascript
// 1. Search shopping malls
const malls = await search_places({
  textQuery: `shopping malls in ${cityName}`,
  includedType: "shopping_mall",
  minRating: 4.0,
  maxResultCount: 10
});

// 2. Search local markets if interested
const markets = await search_places({
  textQuery: `local markets in ${cityName}`,
  textQuery: `${cityName} market`,
  maxResultCount: 10
});

// 3. Save to shopping.json
```

### Entertainment Agent
```javascript
// 1. Search entertainment venues
const venues = await search_places({
  textQuery: `${entertainmentType} in ${cityName}`,
  includedType: entertainmentTypeMapped,  // "night_club", "theater", etc.
  locationBias: {
    circle: {
      center: { latitude: cityLat, longitude: cityLng },
      radius: 5000
    }
  },
  minRating: 4.0,
  maxResultCount: 15
});

// 2. Filter by opening hours
const openTonight = venues.filter(v => v.currentOpeningHours?.openNow);

// 3. Save to entertainment.json
```

---

## Example: Complete Restaurant Search

```javascript
async function findRestaurants(cityName, hotelLat, hotelLng, cuisine, budget, dietary) {
  // 1. Build query with dietary restrictions
  let query = `${cuisine} restaurants in ${cityName}`;
  if (dietary) {
    query += ` ${dietary} friendly`;  // e.g., "vegetarian friendly"
  }

  // 2. Map budget to price levels
  const priceLevels = budget === 'budget'
    ? ["INEXPENSIVE"]
    : budget === 'luxury'
    ? ["EXPENSIVE", "VERY_EXPENSIVE"]
    : ["MODERATE"];

  // 3. Search with location bias
  const results = await search_places({
    textQuery: query,
    includedType: "restaurant",
    locationBias: {
      circle: {
        center: { latitude: hotelLat, longitude: hotelLng },
        radius: 1500
      }
    },
    minRating: 4.0,
    priceLevels: priceLevels,
    maxResultCount: 15
  });

  // 4. Filter by distance (within 1km walking)
  const nearby = filterByDistance(results, hotelLat, hotelLng, 1.0);

  // 5. Format for meals agent
  return nearby.map(formatPlaceForAgent);
}
```

## Notes

- Always check `businessStatus` before recommending (avoid CLOSED_PERMANENTLY)
- Use `currentOpeningHours.openNow` for real-time availability
- Respect rate limits and implement exponential backoff
- Fall back to WebSearch if MCP unavailable
- Document data source in agent output
