# Google Maps - Route Computation

Compute travel routes and directions between locations with multiple travel modes.

## MCP Tools

### Tool 1: compute_routes

**MCP Tool Name**: `mcp__plugin_google-maps_google-maps__compute_routes`

**Description**: Calculate optimal routes between origin and destination with support for multiple travel modes. Returns detailed route information including distance, duration, and turn-by-turn directions.

**Parameters**:
- `origin` (required, object): Starting point
  - `latitude` (number): Origin latitude
  - `longitude` (number): Origin longitude
  - OR `address` (string): Origin address (will be geocoded)
- `destination` (required, object): End point
  - `latitude` (number): Destination latitude
  - `longitude` (number): Destination longitude
  - OR `address` (string): Destination address (will be geocoded)
- `travel_mode` (optional, string): Mode of transportation
  - `DRIVE` (default): Driving directions
  - `TRANSIT`: Public transportation
  - `WALK`: Walking directions
  - `BICYCLE`: Bicycling directions
- `waypoints` (optional, array): Intermediate stops
  - Each waypoint: `{ latitude, longitude }` or `{ address }`
- `departure_time` (optional, string): ISO 8601 timestamp for traffic-aware routing
- `arrival_time` (optional, string): ISO 8601 timestamp (only for TRANSIT mode)
- `avoid` (optional, array): Route restrictions
  - `tolls`: Avoid toll roads
  - `highways`: Avoid highways
  - `ferries`: Avoid ferries

**Returns**:
- `routes` (array): List of alternative routes
  - `summary` (string): Route description
  - `legs` (array): Route segments
    - `distance` (object): Distance information
      - `value` (number): Distance in meters
      - `text` (string): Human-readable distance
    - `duration` (object): Time information
      - `value` (number): Duration in seconds
      - `text` (string): Human-readable duration
    - `start_address` (string): Origin address
    - `end_address` (string): Destination address
    - `start_location` (object): Origin coordinates
    - `end_location` (object): Destination coordinates
    - `steps` (array): Turn-by-turn directions
      - `instruction` (string): Navigation instruction
      - `distance` (object): Step distance
      - `duration` (object): Step duration
      - `travel_mode` (string): Mode for this step
  - `warnings` (array): Route warnings
  - `waypoint_order` (array): Optimized waypoint sequence

**Example**:
```javascript
// Compute driving route
compute_routes({
  origin: {
    latitude: 40.7580,
    longitude: -73.9855
  },
  destination: {
    latitude: 40.7614,
    longitude: -73.9776
  },
  travel_mode: "DRIVE",
  departure_time: "2026-02-01T09:00:00Z"
})
```

**Example with Address**:
```javascript
// Compute transit route using addresses
compute_routes({
  origin: { address: "Times Square, New York, NY" },
  destination: { address: "Central Park, New York, NY" },
  travel_mode: "TRANSIT",
  arrival_time: "2026-02-01T14:00:00Z"
})
```

**Use Cases**:
- Inter-city transportation planning
- Local transportation between attractions
- Walking routes between nearby locations
- Public transit directions
- Multi-stop itineraries with waypoints

---

## Best Practices

1. **Travel Mode Selection**:
   - `DRIVE`: Inter-city trips, rural areas, car rentals
   - `TRANSIT`: Urban areas, cities with good public transport
   - `WALK`: Short distances (<2km), sightseeing routes
   - `BICYCLE`: Cities with bike infrastructure, recreational routes

2. **Departure Time**:
   - Always provide for DRIVE mode to get traffic-aware estimates
   - Use ISO 8601 format: `2026-02-01T09:00:00Z`
   - Consider local timezone (convert to UTC)

3. **Multiple Routes**:
   - API returns multiple alternatives (usually 1-3)
   - Compare by duration, distance, and route features
   - Consider user preferences (avoid tolls, highways)

4. **Distance Conversion**:
   - API returns meters and seconds
   - Convert: meters to km (÷1000), seconds to minutes (÷60)
   - Store both metric and converted values

5. **Transit Mode**:
   - Use `arrival_time` for time-critical arrivals
   - Use `departure_time` for flexible departures
   - Parse transit steps for vehicle types (bus, train, subway)
   - Check if route requires transfers

6. **Waypoints**:
   - Use for multi-stop itineraries
   - API optimizes waypoint order (check `waypoint_order`)
   - Maximum 25 waypoints per request

## Error Handling

**Common Errors**:
- Invalid coordinates: Validate lat/lng ranges
- No route found: Check if locations are accessible by chosen travel mode
- ZERO_RESULTS: Locations too far apart or no transit available
- Address geocoding failed: Use coordinates instead
- Quota exceeded: Implement caching and rate limiting

**Retry Pattern**:
```
Attempt 1: Direct MCP call
Attempt 2: Retry with different travel mode if applicable
Attempt 3: Retry with coordinates instead of addresses
Fallback: Use WebSearch for route information
```

## Integration Examples

**Transportation Agent - Inter-city Route**:
```javascript
// Calculate high-speed train equivalent (driving route for distance)
compute_routes({
  origin: { address: "Beijing, China" },
  destination: { address: "Shanghai, China" },
  travel_mode: "DRIVE"
})
// Use distance to estimate train duration and cost
// Distance: ~1200km → Train: ~5 hours, ~¥500
```

**Transportation Agent - Airport to Hotel**:
```javascript
// Transit route from airport
compute_routes({
  origin: { address: "JFK Airport, New York" },
  destination: {
    latitude: hotel_lat,
    longitude: hotel_lng
  },
  travel_mode: "TRANSIT",
  arrival_time: checkin_time
})
// Parse steps for subway/bus instructions
```

**Attractions Agent - Walking Tour**:
```javascript
// Walking route between attractions
compute_routes({
  origin: { latitude: museum_lat, longitude: museum_lng },
  destination: { latitude: park_lat, longitude: park_lng },
  travel_mode: "WALK"
})
// Check if walking time is reasonable (<30 min)
```

**Transportation Agent - Multi-stop Journey**:
```javascript
// Route with waypoints
compute_routes({
  origin: { address: "Hotel A" },
  destination: { address: "Hotel B" },
  waypoints: [
    { address: "Attraction 1" },
    { address: "Attraction 2" },
    { address: "Restaurant" }
  ],
  travel_mode: "DRIVE"
})
// Use optimized waypoint order for efficient route
```

## Response Parsing

**Extract Key Information**:
```javascript
// From API response
const route = routes[0]; // Best route
const leg = route.legs[0]; // First/only segment

// Distance and duration
const distance_km = leg.distance.value / 1000;
const duration_min = leg.duration.value / 60;

// Start and end
const from = leg.start_address;
const to = leg.end_address;

// Transit steps (if TRANSIT mode)
const transit_steps = leg.steps.filter(step =>
  step.travel_mode === "TRANSIT"
);

// Calculate cost estimate (example)
const cost_usd = travel_mode === "DRIVE"
  ? distance_km * 0.5  // $0.50 per km
  : 10;  // Flat transit fare
```

## Traffic and Real-time Data

**Considerations**:
- `departure_time` enables traffic-aware routing for DRIVE mode
- `duration_in_traffic` field shows real-time duration estimate
- Always add buffer time for reliability (10-20% of duration)
- Check `warnings` array for road closures or construction

**Example**:
```javascript
const route = routes[0].legs[0];
const normal_duration = route.duration.value / 60; // minutes
const traffic_duration = route.duration_in_traffic?.value / 60;
const buffer_time = Math.ceil(traffic_duration * 0.15); // 15% buffer

const recommended_departure = arrival_time - traffic_duration - buffer_time;
```
