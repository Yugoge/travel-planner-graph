# Gaode Maps - Routing Tools

Route planning tools for various transportation modes in China.

## Available Tools

### 1. driving_route

Plan driving routes with real-time traffic information.

**MCP Tool**: `driving_route`

**Parameters**:
- `origin` (required): Starting point address or coordinates (e.g., "北京市朝阳区" or "116.481488,39.990464")
- `destination` (required): Destination address or coordinates
- `strategy` (optional): Route strategy
  - `0`: Fastest route (default)
  - `1`: Avoid highways
  - `2`: Avoid tolls
  - `3`: Shortest distance
  - `4`: Avoid congestion
- `waypoints` (optional): Waypoints separated by semicolons (max 16)

**Returns**:
- Distance (meters and kilometers)
- Duration (seconds and formatted time)
- Tolls (CNY)
- Traffic lights count
- Step-by-step directions
- Route polyline (GCJ-02 coordinates)

**Example**:
```javascript
// Beijing to Shanghai driving route
driving_route({
  origin: "北京市",
  destination: "上海市",
  strategy: 0
})
```

**Use Cases**:
- Inter-city driving routes
- Road trip planning
- Delivery route optimization
- Traffic-aware navigation

---

### 2. transit_route

Plan public transportation routes (bus, subway, intercity trains).

**MCP Tool**: `transit_route`

**Parameters**:
- `origin` (required): Starting point address or coordinates
- `destination` (required): Destination address or coordinates
- `city` (optional): City name or city code (auto-detected if omitted)
- `cityd` (optional): Destination city (for inter-city transit)
- `strategy` (optional): Route strategy
  - `0`: Fastest route
  - `1`: Fewest transfers
  - `2`: Shortest walking distance
  - `3`: Most comfortable (default)
  - `5`: Avoid subway

**Returns**:
- Transit segments (bus, subway, walk, railway)
- Duration per segment
- Cost per segment
- Total duration and cost
- Transfer points
- Departure/arrival times
- Walking instructions

**Example**:
```javascript
// Beijing to Chengdu transit route
transit_route({
  origin: "北京市",
  destination: "成都市",
  cityd: "成都",
  strategy: 0
})
```

**Use Cases**:
- Inter-city train/bus planning
- Urban subway routing
- Multi-modal transportation
- Budget travel planning

---

### 3. walking_route

Plan pedestrian walking routes.

**MCP Tool**: `walking_route`

**Parameters**:
- `origin` (required): Starting point address or coordinates
- `destination` (required): Destination address or coordinates

**Returns**:
- Distance (meters)
- Duration (seconds)
- Step-by-step walking directions
- Route polyline

**Example**:
```javascript
// Walk from hotel to attraction
walking_route({
  origin: "重庆市渝中区解放碑",
  destination: "重庆市渝中区洪崖洞"
})
```

**Use Cases**:
- Intra-city sightseeing routes
- Hotel to attraction distances
- Walking tour planning
- Accessibility assessment

---

### 4. cycling_route

Plan cycling routes.

**MCP Tool**: `cycling_route`

**Parameters**:
- `origin` (required): Starting point address or coordinates
- `destination` (required): Destination address or coordinates

**Returns**:
- Distance (meters)
- Duration (seconds)
- Step-by-step cycling directions
- Route polyline

**Example**:
```javascript
// Bike sharing route in city
cycling_route({
  origin: "杭州市西湖区西湖",
  destination: "杭州市西湖区灵隐寺"
})
```

**Use Cases**:
- Bike-sharing routes
- Cycling tour planning
- Alternative transportation
- Exercise route planning

---

## Best Practices

### 1. Input Flexibility

Accept both formats:
- Chinese addresses: "北京市朝阳区国贸"
- Coordinates: "116.459585,39.910176"

For ambiguous locations, use coordinates from geocoding tools.

### 2. Strategy Selection

**Driving**:
- Use strategy `0` (fastest) for time-sensitive travel
- Use strategy `2` (avoid tolls) for budget-conscious travelers
- Use strategy `4` (avoid congestion) during peak hours

**Transit**:
- Use strategy `0` (fastest) for tight schedules
- Use strategy `1` (fewest transfers) for elderly/children
- Use strategy `2` (shortest walk) for travelers with luggage

### 3. Error Handling

**Retry logic**:
```javascript
async function getRouteWithRetry(origin, destination, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await driving_route({ origin, destination });
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
  const route = await transit_route({ origin, destination });
  return formatRouteData(route);
} catch (error) {
  console.warn('Gaode Maps unavailable, falling back to WebSearch');
  return await webSearchRoute(origin, destination);
}
```

### 4. Response Parsing

**Duration formatting**:
```javascript
function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
}
```

**Distance formatting**:
```javascript
function formatDistance(meters) {
  return meters >= 1000
    ? `${(meters / 1000).toFixed(1)} km`
    : `${meters} m`;
}
```

**Cost extraction**:
```javascript
function extractCost(routeResponse) {
  // Tolls for driving routes
  const tolls = routeResponse.route?.tolls || 0;

  // Fares for transit routes
  const transitCost = routeResponse.route?.transits?.[0]?.cost || 0;

  return tolls || transitCost || 0;
}
```

### 5. Multi-City Routes

For multi-city trips, chain routes:
```javascript
const cities = ['Beijing', 'Bazhong', 'Chengdu', 'Shanghai'];
const routes = [];

for (let i = 0; i < cities.length - 1; i++) {
  const route = await transit_route({
    origin: cities[i],
    destination: cities[i + 1],
    cityd: cities[i + 1]
  });
  routes.push(route);
}
```

## Integration with Transportation Agent

The transportation agent should:

1. **Load this file** when processing location changes
2. **Use transit_route** for inter-city transportation (trains, buses)
3. **Use driving_route** if user prefers driving
4. **Use walking_route** for short distances (<5km)
5. **Parse response** for distance, duration, cost
6. **Save structured data** to `transportation.json`
7. **Fall back to WebSearch** if MCP unavailable

Example workflow:
```
1. Detect location change: Chongqing → Chengdu
2. Invoke /gaode-maps routing (loads this file)
3. Call transit_route({ origin: "重庆", destination: "成都", cityd: "成都" })
4. Parse response: duration=2h 15m, cost=154 CNY, type=high-speed train
5. Save to transportation.json
6. Return complete
```
