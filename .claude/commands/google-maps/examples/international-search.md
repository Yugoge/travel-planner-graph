# Example: International Travel Planning with Google Maps

Complete workflow for planning international travel using Google Maps Grounding Lite MCP integration.

## Scenario

Planning a 3-city European trip: Paris → Barcelona → Rome

**User Requirements**:
- 7 days total
- Mid-range budget
- Interested in culture, food, history
- Prefers walking and public transit
- Vegetarian-friendly restaurants

---

## Step 1: Transportation Agent - Inter-City Routes

**Task**: Plan transportation between cities.

```javascript
// Day 3: Paris to Barcelona
// Load routing tools
// /google-maps routing

// Compute driving route
const drivingRoute = await compute_routes({
  origin: "Paris, France",
  destination: "Barcelona, Spain",
  travelMode: "DRIVE",
  routingPreference: "TRAFFIC_AWARE",
  departureTime: "2026-02-15T08:00:00Z"
});

// Compute transit route (train)
const transitRoute = await compute_routes({
  origin: "Paris Gare de Lyon",
  destination: "Barcelona Sants Station",
  travelMode: "TRANSIT",
  departureTime: "2026-02-15T08:00:00Z"
});

// Parse results
const options = [
  {
    mode: "High-speed train",
    duration_hours: transitRoute.routes[0].duration / 3600,  // ~6.5 hours
    distance_km: transitRoute.routes[0].distanceMeters / 1000,  // ~830 km
    cost_usd: 150,  // Extract from fare or estimate
    notes: "Direct TGV, comfortable, scenic"
  },
  {
    mode: "Driving",
    duration_hours: drivingRoute.routes[0].duration / 3600,  // ~10 hours
    distance_km: drivingRoute.routes[0].distanceMeters / 1000,  // ~1030 km
    cost_usd: estimateDrivingCost(1030, 1.6, 12).total,  // ~180 USD
    notes: "Flexible schedule, requires car rental"
  },
  {
    mode: "Flight",
    duration_hours: 3.5,  // From WebSearch fallback
    distance_km: 830,
    cost_usd: 120,  // From flight search
    notes: "Fastest, but add airport time"
  }
];

// Select best option (train based on comfort + budget)
const selected = options[0];

// Save to transportation.json
{
  "day": 3,
  "location_change": {
    "from": "Paris, France",
    "to": "Barcelona, Spain",
    "transportation": "High-speed train (TGV)",
    "departure_time": "08:30",
    "arrival_time": "15:00",
    "duration_minutes": 390,
    "cost": 150,
    "notes": "Book 2-4 weeks in advance, luggage included",
    "data_source": "google_maps"
  }
}
```

---

## Step 2: Accommodation Agent - Hotel Search

**Task**: Find hotels in each city.

```javascript
// Paris hotel (Days 1-2)
// Load places tools
// /google-maps places

const parisHotels = await search_places({
  textQuery: "mid-range hotels in Marais district Paris",
  includedType: "hotel",
  locationBias: {
    circle: {
      center: { latitude: 48.8566, longitude: 2.3522 },
      radius: 2000
    }
  },
  minRating: 4.0,
  priceLevels: ["MODERATE"],
  maxResultCount: 10
});

// Filter and format
const parisHotel = {
  name: parisHotels[0].displayName.text,
  location: parisHotels[0].formattedAddress,
  cost: 120,  // per night, estimate from priceLevel
  type: "Hotel",
  amenities: ["WiFi", "Breakfast included", "Central location"],
  rating: parisHotels[0].rating,
  notes: `${parisHotels[0].userRatingCount} reviews, near metro`,
  data_source: "google_maps"
};

// Barcelona hotel (Days 3-5)
const barcelonaHotels = await search_places({
  textQuery: "hotels near Gothic Quarter Barcelona",
  includedType: "hotel",
  locationBias: {
    circle: {
      center: { latitude: 41.3874, longitude: 2.1686 },
      radius: 2000
    }
  },
  minRating: 4.0,
  priceLevels: ["MODERATE"],
  maxResultCount: 10
});

const barcelonaHotel = formatHotelData(barcelonaHotels[0]);

// Rome hotel (Days 6-7)
const romeHotels = await search_places({
  textQuery: "hotels near Colosseum Rome",
  includedType: "hotel",
  minRating: 4.0,
  priceLevels: ["MODERATE"],
  maxResultCount: 10
});

const romeHotel = formatHotelData(romeHotels[0]);

// Save to accommodation.json
```

---

## Step 3: Attractions Agent - Sightseeing

**Task**: Find tourist attractions based on user interests (culture, history).

```javascript
// Paris attractions (Day 1-2)
const parisAttractions = await search_places({
  textQuery: "top museums and historical sites in Paris",
  includedType: "tourist_attraction",
  locationBias: {
    circle: {
      center: { latitude: 48.8566, longitude: 2.3522 },
      radius: 5000
    }
  },
  minRating: 4.5,
  maxResultCount: 20
});

// Also search museums specifically
const parisMuseums = await search_places({
  textQuery: "museums in Paris",
  includedType: "museum",
  minRating: 4.5,
  maxResultCount: 15
});

// Combine and select top attractions
const parisSelected = [
  {
    name: "Louvre Museum",
    location: "Rue de Rivoli, 75001 Paris",
    cost: 17,  // EUR converted to USD
    duration_minutes: 240,
    type: "Museum",
    notes: "Book timed entry online, arrive early",
    data_source: "google_maps"
  },
  {
    name: "Eiffel Tower",
    location: "Champ de Mars, Paris",
    cost: 28,
    duration_minutes: 120,
    type: "Landmark",
    notes: "Book summit tickets in advance",
    data_source: "google_maps"
  },
  {
    name: "Notre-Dame Cathedral (exterior)",
    location: "Île de la Cité, Paris",
    cost: 0,
    duration_minutes: 60,
    type: "Historical site",
    notes: "Exterior viewing during restoration",
    data_source: "google_maps"
  }
];

// Barcelona attractions (Day 3-5)
const barcelonaAttractions = await search_places({
  textQuery: "Gaudi architecture and Gothic Quarter Barcelona",
  includedType: "tourist_attraction",
  minRating: 4.5,
  maxResultCount: 20
});

const barcelonaSelected = selectTopAttractions(barcelonaAttractions, 5);

// Rome attractions (Day 6-7)
const romeAttractions = await search_places({
  textQuery: "ancient Rome historical sites Colosseum Forum",
  includedType: "tourist_attraction",
  minRating: 4.5,
  maxResultCount: 20
});

const romeSelected = selectTopAttractions(romeAttractions, 5);

// Save to attractions.json
```

---

## Step 4: Meals Agent - Restaurant Search

**Task**: Find vegetarian-friendly restaurants near accommodations.

```javascript
// Paris dinner (Day 1)
const parisDinner = await search_places({
  textQuery: "vegetarian friendly restaurants in Marais Paris",
  includedType: "restaurant",
  locationBias: {
    circle: {
      center: parisHotel.location,  // Hotel coordinates
      radius: 1000  // 1km walking distance
    }
  },
  minRating: 4.0,
  priceLevels: ["MODERATE"],
  openNow: false,  // Planning ahead
  maxResultCount: 10
});

const parisRestaurant = {
  name: parisDinner[0].displayName.text,
  location: parisDinner[0].formattedAddress,
  cost: 35,  // per person estimate
  cuisine: "French",
  notes: `Vegetarian options available, ${parisDinner[0].rating} stars`,
  data_source: "google_maps"
};

// Barcelona lunch (Day 4) - near Sagrada Familia
const barcelonaLunch = await search_places({
  textQuery: "vegetarian tapas restaurants near Sagrada Familia",
  includedType: "restaurant",
  locationBias: {
    circle: {
      center: { latitude: 41.4036, longitude: 2.1744 },  // Sagrada Familia
      radius: 500
    }
  },
  minRating: 4.0,
  priceLevels: ["INEXPENSIVE", "MODERATE"],
  maxResultCount: 10
});

const barcelonaRestaurant = formatRestaurantData(barcelonaLunch[0]);

// Rome dinner (Day 6)
const romeDinner = await search_places({
  textQuery: "vegetarian Italian restaurants near Colosseum Rome",
  includedType: "restaurant",
  locationBias: {
    circle: {
      center: { latitude: 41.8902, longitude: 12.4922 },  // Colosseum
      radius: 800
    }
  },
  minRating: 4.0,
  priceLevels: ["MODERATE"],
  maxResultCount: 10
});

const romeRestaurant = formatRestaurantData(romeDinner[0]);

// Save to meals.json
```

---

## Step 5: Shopping Agent - Local Markets

**Task**: Find shopping destinations for souvenirs.

```javascript
// Paris shopping (Day 2 afternoon)
const parisShopping = await search_places({
  textQuery: "local markets and souvenir shops in Latin Quarter Paris",
  locationBias: {
    circle: {
      center: { latitude: 48.8534, longitude: 2.3488 },
      radius: 1000
    }
  },
  maxResultCount: 10
});

const parisMarket = {
  name: "Marché Maubert",
  location: "Place Maubert, Paris",
  cost: 50,  // Budget allocation
  type: "Local Market",
  notes: "Open Tuesday, Thursday, Saturday mornings",
  data_source: "google_maps"
};

// Barcelona shopping (Day 5)
const barcelonaShopping = await search_places({
  textQuery: "La Boqueria market and Gothic Quarter shops Barcelona",
  includedType: "shopping_mall",
  minRating: 4.0,
  maxResultCount: 10
});

const barcelonaMarket = formatShoppingData(barcelonaShopping[0]);

// Save to shopping.json
```

---

## Step 6: Entertainment Agent - Evening Activities

**Task**: Find evening entertainment options.

```javascript
// Barcelona evening (Day 4) - Flamenco show
const barcelonaShows = await search_places({
  textQuery: "flamenco show Barcelona Gothic Quarter",
  includedType: "performing_arts_theater",
  locationBias: {
    circle: {
      center: { latitude: 41.3874, longitude: 2.1686 },
      radius: 2000
    }
  },
  minRating: 4.5,
  maxResultCount: 10
});

const barcelonaShow = {
  name: barcelonaShows[0].displayName.text,
  location: barcelonaShows[0].formattedAddress,
  cost: 45,
  time: "21:00",
  type: "Flamenco Performance",
  notes: "Book tickets online, show duration 90 minutes",
  data_source: "google_maps"
};

// Save to entertainment.json
```

---

## Step 7: Weather Context

**Task**: Get weather overview for all cities.

```javascript
// Load weather tools
// /google-maps weather

const parisWeather = await lookup_weather({
  location: "Paris, France"
});

const barcelonaWeather = await lookup_weather({
  location: "Barcelona, Spain"
});

const romeWeather = await lookup_weather({
  location: "Rome, Italy"
});

// Weather overview
const weatherSummary = [
  {
    city: "Paris",
    temperature: formatTemperature(parisWeather.temperature),
    condition: parisWeather.condition,
    recommendation: recommendActivityType(parisWeather).recommendation
  },
  {
    city: "Barcelona",
    temperature: formatTemperature(barcelonaWeather.temperature),
    condition: barcelonaWeather.condition,
    recommendation: recommendActivityType(barcelonaWeather).recommendation
  },
  {
    city: "Rome",
    temperature: formatTemperature(romeWeather.temperature),
    condition: romeWeather.condition,
    recommendation: recommendActivityType(romeWeather).recommendation
  }
];

// Use weather to adjust daily plans
// Include packing recommendations in final output
```

---

## Step 8: Walking Routes Between Attractions

**Task**: Calculate walking times for daily itineraries.

```javascript
// Paris Day 1: Hotel → Louvre → Eiffel Tower
const parisRoute1 = await compute_routes({
  origin: parisHotel.location,
  destination: "Louvre Museum, Paris",
  travelMode: "WALK"
});

const parisRoute2 = await compute_routes({
  origin: "Louvre Museum, Paris",
  destination: "Eiffel Tower, Paris",
  travelMode: "WALK"
});

// Calculate total walking time
const totalWalkingTime =
  parisRoute1.routes[0].duration / 60 +  // Convert to minutes
  parisRoute2.routes[0].duration / 60;

// If too long (>40 minutes), suggest transit
if (totalWalkingTime > 40) {
  const transitOption = await compute_routes({
    origin: "Louvre Museum, Paris",
    destination: "Eiffel Tower, Paris",
    travelMode: "TRANSIT"
  });

  // Use transit instead
  console.log(`Transit recommended: ${transitOption.routes[0].duration / 60} minutes`);
}
```

---

## Complete Output Structure

```json
{
  "destination": "Paris-Barcelona-Rome",
  "duration_days": 7,
  "data_sources": ["google_maps", "web_search"],
  "transportation": {
    "day_3": {
      "from": "Paris",
      "to": "Barcelona",
      "mode": "High-speed train",
      "cost": 150,
      "source": "google_maps"
    },
    "day_6": {
      "from": "Barcelona",
      "to": "Rome",
      "mode": "Flight",
      "cost": 130,
      "source": "web_search"
    }
  },
  "accommodation": {
    "paris": {...},
    "barcelona": {...},
    "rome": {...}
  },
  "attractions": {
    "paris": [...],
    "barcelona": [...],
    "rome": [...]
  },
  "meals": {
    "day_1": {"breakfast": ..., "lunch": ..., "dinner": ...},
    ...
  },
  "shopping": {...},
  "entertainment": {...},
  "weather_overview": [...]
}
```

---

## Key Takeaways

1. **Progressive Loading**: Load only needed tool categories (`places`, `routing`, `weather`)
2. **Location Bias**: Use `locationBias` to find nearby POIs (restaurants, hotels near attractions)
3. **Filtering**: Apply `minRating`, `priceLevels`, `includedType` to refine results
4. **Multi-Modal**: Compare driving, transit, walking for route planning
5. **Fallback**: Always implement WebSearch fallback if MCP unavailable
6. **Data Source**: Document whether data came from `google_maps` or `web_search`
7. **User Preferences**: Filter results based on dietary restrictions, budget, interests
8. **Weather Context**: Use weather to optimize indoor/outdoor activity scheduling

---

## Error Handling in Practice

```javascript
async function safeGoogleMapsSearch(params, fallbackQuery) {
  try {
    // Try Google Maps first
    const results = await search_places(params);
    return { source: 'google_maps', data: results };
  } catch (error) {
    console.warn('Google Maps unavailable:', error.message);

    // Fall back to WebSearch
    const webResults = await webSearchPlaces(fallbackQuery);
    return { source: 'web_search', data: webResults };
  }
}

// Usage
const restaurants = await safeGoogleMapsSearch(
  {
    textQuery: "vegetarian restaurants in Paris Marais",
    includedType: "restaurant",
    minRating: 4.0
  },
  "best vegetarian restaurants Paris Marais district"
);
```

---

This example demonstrates the complete integration of Google Maps Grounding Lite into the travel planning workflow, showing how each agent uses the skill to gather accurate, real-time data for international destinations.
