# Google Maps - Routing Tools

Route planning and navigation tools for various transportation modes worldwide using Google Maps Grounding Lite.

## Available Tools

### 1. compute_routes

Calculate routes between locations with multiple transportation modes and optimization options.

**MCP Tool**: `compute_routes`

**Parameters**:
- `origin` (required): Starting location
  - Address string: "1600 Amphitheatre Parkway, Mountain View, CA"
  - Place ID: "ChIJ2eUgeAK6j4ARbn5u_wAGqWA"
  - Coordinates: { latitude: 37.4224, longitude: -122.0842 }
- `destination` (required): Ending location (same format as origin)
- `travelMode` (optional): Transportation mode
  - `DRIVE` (default): Driving route
  - `WALK`: Walking route
  - `BICYCLE`: Bicycling route
  - `TRANSIT`: Public transportation route
  - `TWO_WHEELER`: Motorcycle/scooter route
- `routingPreference` (optional): Route optimization strategy
  - `TRAFFIC_AWARE`: Consider current traffic (default for DRIVE)
  - `TRAFFIC_AWARE_OPTIMAL`: Best route with traffic
  - `SHORTEST`: Shortest distance
- `departureTime` (optional): Planned departure time (ISO 8601 format)
- `arrivalTime` (optional): Desired arrival time (ISO 8601 format, transit only)
- `waypoints` (optional): Intermediate stops (array of location objects)
- `avoid` (optional): Features to avoid (array)
  - `TOLLS`: Avoid toll roads
  - `HIGHWAYS`: Avoid highways
  - `FERRIES`: Avoid ferries
- `units` (optional): Distance units
  - `METRIC`: Kilometers (default)
  - `IMPERIAL`: Miles

**Returns**:
- Routes array (multiple route options)
- Distance (meters/kilometers)
- Duration (seconds and formatted time)
- Duration in traffic (for driving routes)
- Polyline (encoded route path)
- Legs (route segments)
  - Start/end locations
  - Steps with instructions
  - Distance and duration per leg
- Warnings (tolls, restrictions)
- Fare information (for transit)

**Example - Driving Route**:
```javascript
// Paris to Barcelona driving route
compute_routes({
  origin: { latitude: 48.8566, longitude: 2.3522 },
  destination: { latitude: 41.3874, longitude: 2.1686 },
  travelMode: "DRIVE",
  routingPreference: "TRAFFIC_AWARE",
  avoid: ["TOLLS"],
  departureTime: "2026-02-15T08:00:00Z"
})
```

**Example - Walking Route**:
```javascript
// Walk from hotel to restaurant
compute_routes({
  origin: "Eiffel Tower, Paris",
  destination: "Louvre Museum, Paris",
  travelMode: "WALK"
})
```

**Example - Transit Route**:
```javascript
// Public transportation with arrival time
compute_routes({
  origin: "London Heathrow Airport",
  destination: "Tower of London",
  travelMode: "TRANSIT",
  arrivalTime: "2026-02-15T14:00:00Z"
})
```

**Example - Multi-Stop Route**:
```javascript
// Route with waypoints
compute_routes({
  origin: "Rome, Italy",
  destination: "Venice, Italy",
  waypoints: [
    { latitude: 43.7696, longitude: 11.2558 },  // Florence
    { latitude: 44.4949, longitude: 11.3426 }   // Bologna
  ],
  travelMode: "DRIVE"
})
```

**Use Cases**:
- Inter-city driving routes
- Walking tours between attractions
- Public transit navigation
- Multi-city road trips
- Bike route planning
- Traffic-aware commute planning

---

## Travel Mode Details

### DRIVE (Driving Routes)
- Returns multiple route options
- Includes traffic information
- Provides turn-by-turn directions
- Shows toll roads and costs (if available)
- Best for: Car rentals, taxis, inter-city travel

### WALK (Walking Routes)
- Pedestrian-friendly paths
- Includes stairs and footpaths
- Excludes highways and motorways
- Best for: City exploration, attraction-to-attraction

### BICYCLE (Bicycling Routes)
- Bike lanes and paths when available
- Considers elevation changes
- Avoids highways
- Best for: Bike rentals, cycling tours

### TRANSIT (Public Transportation)
- Combines bus, subway, train, tram
- Provides schedules and fares
- Shows transfer points
- Requires departure or arrival time for accuracy
- Best for: City navigation, budget travel

### TWO_WHEELER (Motorcycle/Scooter)
- Similar to driving but optimized for smaller vehicles
- May use different lanes and shortcuts
- Best for: Scooter rentals, motorcycle tours

---

## Best Practices

### 1. Input Flexibility

Accept multiple location formats:
```javascript
function normalizeLocation(location) {
  // String address
  if (typeof location === 'string') {
    return location;
  }

  // Coordinates object
  if (location.latitude && location.longitude) {
    return {
      latitude: parseFloat(location.latitude),
      longitude: parseFloat(location.longitude)
    };
  }

  // Place ID
  if (location.placeId) {
    return location.placeId;
  }

  throw new Error('Invalid location format');
}
```

### 2. Travel Mode Selection

Choose appropriate mode based on context:
```javascript
function selectTravelMode(distance, userPreference, budget) {
  // Short distances: walk
  if (distance < 2) return 'WALK';

  // Budget conscious: transit
  if (budget === 'budget') return 'TRANSIT';

  // Long distances: drive
  if (distance > 50) return 'DRIVE';

  // User preference
  return userPreference || 'DRIVE';
}
```

### 3. Departure Time Optimization

For accurate traffic and transit data:
```javascript
function getDepartureTime(dayOfTrip, activityStartTime) {
  // Subtract buffer time (e.g., 30 minutes before activity)
  const activityTime = new Date(activityStartTime);
  activityTime.setMinutes(activityTime.getMinutes() - 30);

  // Format as ISO 8601
  return activityTime.toISOString();
}
```

### 4. Response Parsing

**Extract essential route information**:
```javascript
function formatRouteForAgent(route) {
  const leg = route.legs[0];  // First leg for direct routes

  return {
    distance_km: route.distanceMeters / 1000,
    distance_meters: route.distanceMeters,
    duration_seconds: route.duration,
    duration_formatted: formatDuration(route.duration),
    duration_in_traffic: route.staticDuration || route.duration,
    start_address: leg.startLocation.address,
    end_address: leg.endLocation.address,
    polyline: route.polyline.encodedPolyline,
    warnings: route.warnings || [],
    has_tolls: route.warnings?.some(w => w.includes('toll')),
    fare: route.travelAdvisory?.transitFare
  };
}

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
}
```

**Extract step-by-step directions**:
```javascript
function extractDirections(route) {
  const steps = [];

  route.legs.forEach(leg => {
    leg.steps.forEach(step => {
      steps.push({
        instruction: step.navigationInstruction?.instructions,
        distance: step.distanceMeters,
        duration: step.staticDuration,
        travel_mode: step.travelMode
      });
    });
  });

  return steps;
}
```

**Extract transit details**:
```javascript
function extractTransitInfo(route) {
  if (route.travelMode !== 'TRANSIT') return null;

  const transitSteps = [];

  route.legs.forEach(leg => {
    leg.steps.forEach(step => {
      if (step.transitDetails) {
        transitSteps.push({
          line: step.transitDetails.transitLine?.name,
          vehicle: step.transitDetails.transitLine?.vehicle?.type,
          departure_stop: step.transitDetails.stopDetails?.departureStop?.name,
          arrival_stop: step.transitDetails.stopDetails?.arrivalStop?.name,
          departure_time: step.transitDetails.stopDetails?.departureTime,
          arrival_time: step.transitDetails.stopDetails?.arrivalTime,
          num_stops: step.transitDetails.stopCount,
          headsign: step.transitDetails.headsign
        });
      }
    });
  });

  return transitSteps;
}
```

### 5. Error Handling

**Retry logic**:
```javascript
async function computeRoutesWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await compute_routes(params);
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
async function computeRoutesWithFallback(origin, destination, mode) {
  try {
    const routes = await compute_routes({
      origin,
      destination,
      travelMode: mode
    });
    return { source: 'google_maps', data: routes };
  } catch (error) {
    console.warn('Google Maps unavailable, falling back to WebSearch');
    const results = await webSearchRoute(origin, destination, mode);
    return { source: 'web_search', data: results };
  }
}
```

**Handle no routes found**:
```javascript
async function findBestRoute(origin, destination, preferences) {
  // Try preferred mode first
  let routes = await compute_routes({
    origin,
    destination,
    travelMode: preferences.mode,
    avoid: preferences.avoid
  });

  // If no routes, try without restrictions
  if (!routes || routes.length === 0) {
    console.warn('No routes with restrictions, trying without');
    routes = await compute_routes({
      origin,
      destination,
      travelMode: preferences.mode
    });
  }

  // If still no routes, try different mode
  if (!routes || routes.length === 0) {
    console.warn('No routes found, trying alternative mode');
    routes = await compute_routes({
      origin,
      destination,
      travelMode: 'DRIVE'  // Fallback to driving
    });
  }

  return routes;
}
```

### 6. Cost Estimation

**Estimate driving costs**:
```javascript
function estimateDrivingCost(distanceKm, fuelPricePerLiter = 1.5, fuelEfficiency = 10) {
  // fuelEfficiency in km per liter
  const litersNeeded = distanceKm / fuelEfficiency;
  const fuelCost = litersNeeded * fuelPricePerLiter;

  // Add tolls if route has them (estimate)
  const tollCost = 0;  // Extract from route warnings if available

  return {
    fuel: fuelCost,
    tolls: tollCost,
    total: fuelCost + tollCost
  };
}
```

**Extract transit fare**:
```javascript
function extractTransitCost(route) {
  if (route.travelAdvisory?.transitFare) {
    const fare = route.travelAdvisory.transitFare;
    return {
      amount: fare.units || 0,
      currency: fare.currencyCode || 'USD'
    };
  }
  return null;
}
```

---

## Integration with Transportation Agent

The transportation agent should:

1. **Load this file** when processing location changes
2. **Use compute_routes** for inter-city transportation
3. **Compare multiple modes** (drive, transit, walk) when appropriate
4. **Parse response** for distance, duration, cost
5. **Save structured data** to `transportation.json`
6. **Fall back to WebSearch** if MCP unavailable

Example workflow:
```javascript
// 1. Detect location change: Paris → Barcelona
const dayData = planSkeleton.days[2];  // Day 3 has location change

// 2. Load routing tools (this file)
// /google-maps routing

// 3. Compute route with multiple options
const drivingRoute = await compute_routes({
  origin: "Paris, France",
  destination: "Barcelona, Spain",
  travelMode: "DRIVE",
  departureTime: "2026-02-15T08:00:00Z"
});

const transitRoute = await compute_routes({
  origin: "Paris, France",
  destination: "Barcelona, Spain",
  travelMode: "TRANSIT",
  departureTime: "2026-02-15T08:00:00Z"
});

// 4. Compare options
const drivingOption = {
  mode: "Driving",
  distance: drivingRoute.routes[0].distanceMeters / 1000,
  duration: drivingRoute.routes[0].duration / 3600,
  cost: estimateDrivingCost(drivingRoute.routes[0].distanceMeters / 1000)
};

const transitOption = {
  mode: "High-speed train",
  distance: transitRoute.routes[0].distanceMeters / 1000,
  duration: transitRoute.routes[0].duration / 3600,
  cost: extractTransitCost(transitRoute.routes[0])?.amount || 150
};

// 5. Select best based on user preferences
const selected = selectBestOption([drivingOption, transitOption], userPreferences);

// 6. Save to transportation.json
const transportationData = {
  day: 3,
  location_change: {
    from: "Paris, France",
    to: "Barcelona, Spain",
    transportation: selected.mode,
    departure_time: "08:30",
    arrival_time: calculateArrivalTime("08:30", selected.duration),
    duration_minutes: selected.duration * 60,
    cost: selected.cost.total || selected.cost,
    notes: generateNotes(selected),
    data_source: "google_maps"
  }
};
```

## Example: Multi-City Route Planning

```javascript
async function planMultiCityRoute(cities, travelMode = "DRIVE") {
  const routes = [];

  for (let i = 0; i < cities.length - 1; i++) {
    const route = await compute_routes({
      origin: cities[i],
      destination: cities[i + 1],
      travelMode: travelMode,
      routingPreference: "TRAFFIC_AWARE"
    });

    routes.push({
      from: cities[i],
      to: cities[i + 1],
      distance_km: route.routes[0].distanceMeters / 1000,
      duration_hours: route.routes[0].duration / 3600,
      formatted: formatRouteForAgent(route.routes[0])
    });
  }

  return routes;
}

// Usage
const cities = ["Paris, France", "Lyon, France", "Barcelona, Spain", "Madrid, Spain"];
const routePlan = await planMultiCityRoute(cities, "DRIVE");
```

## Notes

- Always use ISO 8601 format for departure/arrival times
- Consider time zones for international routes
- Transit routes require departure or arrival time for accuracy
- Check `route.warnings` for important alerts (tolls, closures)
- Respect rate limits and implement exponential backoff
- Fall back to WebSearch if MCP unavailable
- Document data source in agent output
- For very long routes (>500km), consider flight options via web search
