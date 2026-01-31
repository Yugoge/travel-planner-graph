# Gaode Maps - Routing Tools

Route planning and navigation for all transportation modes in China.

## MCP Tools

### Tool 1: driving_route

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__driving_route`

**Purpose**: Calculate driving routes with real-time traffic data, alternative routes, and estimated costs.

**Parameters**:
- `origin` (required): Starting point as "longitude,latitude" or address
- `destination` (required): Ending point as "longitude,latitude" or address
- `strategy` (optional): Route strategy
  - `0` - Fast (default, considers traffic)
  - `1` - Avoid toll roads
  - `2` - Distance priority (shortest)
  - `3` - Avoid highways
  - `4` - Balance distance and time
  - `5` - Consider multiple factors
- `waypoints` (optional): Intermediate waypoints as "lng,lat;lng,lat"
- `avoidpolygons` (optional): Areas to avoid as polygon coordinates
- `avoidroad` (optional): Specific road names to avoid

**Returns**:
- `route` object:
  - `distance` - Total distance in meters
  - `duration` - Estimated time in seconds (with traffic)
  - `tolls` - Toll fee in CNY
  - `traffic_lights` - Number of traffic lights
  - `steps` - Turn-by-turn navigation instructions
  - `polyline` - Encoded route path
- `taxi_cost` - Estimated taxi fare (day/night)
- `alternative_routes` - Up to 3 alternative routes

**Example**:
```javascript
mcp__plugin_amap-maps_amap-maps__driving_route({
  origin: "Beijing",
  destination: "Shanghai",
  strategy: 0
})
```

**Response Structure**:
```json
{
  "status": "1",
  "route": {
    "distance": "1213450",
    "duration": "43200",
    "tolls": "385",
    "paths": [{
      "steps": [{"instruction": "沿北京东路向东行驶", "distance": "1500"}]
      // ... (multiple turn-by-turn steps)
    }]
  }
}
```

**Use Cases**:
- Inter-city road trip planning
- Private car/taxi cost estimation
- Route comparison (fast vs scenic)
- Multi-stop itinerary routing

---

### Tool 2: walking_route

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__walking_route`

**Purpose**: Calculate pedestrian routes using sidewalks and crosswalks.

**Parameters**:
- `origin` (required): Starting point as "longitude,latitude" or address
- `destination` (required): Ending point as "longitude,latitude" or address

**Returns**:
- `route` object:
  - `distance` - Total walking distance in meters
  - `duration` - Estimated walking time in seconds (avg 1.2 m/s)
  - `steps` - Turn-by-turn walking directions
  - `polyline` - Walking path

**Example**:
```javascript
mcp__plugin_amap-maps_amap-maps__walking_route({
  origin: "天安门",
  destination: "故宫"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "route": {
    "distance": "850",
    "duration": "708",
    "steps": [{"instruction": "向北步行", "distance": "200"}]
  }
}
```

**Use Cases**:
- Walking between nearby attractions
- Hotel to restaurant walking distance
- Exploring city on foot
- Accessibility planning

---

### Tool 3: cycling_route

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__cycling_route`

**Purpose**: Calculate bicycle routes using bike lanes and bike-friendly roads.

**Parameters**:
- `origin` (required): Starting point as "longitude,latitude" or address
- `destination` (required): Ending point as "longitude,latitude" or address

**Returns**:
- `route` object:
  - `distance` - Total cycling distance in meters
  - `duration` - Estimated cycling time in seconds (avg 5 m/s)
  - `steps` - Turn-by-turn cycling directions
  - `polyline` - Cycling path

**Example**:
```javascript
mcp__plugin_amap-maps_amap-maps__cycling_route({
  origin: "西湖音乐喷泉",
  destination: "雷峰塔"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "route": {
    "distance": "3200",
    "duration": "640",
    "steps": [{"instruction": "沿湖滨路骑行", "distance": "500"}]
  }
}
```

**Use Cases**:
- Bike rental route planning
- City exploration by bicycle
- Eco-friendly transportation
- Scenic bike routes

---

### Tool 4: transit_route

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__transit_route`

**Purpose**: Calculate public transportation routes (bus, subway, train) with schedules and transfers.

**Parameters**:
- `origin` (required): Starting point as "longitude,latitude" or city/address
- `destination` (required): Ending point as "longitude,latitude" or city/address
- `city` (optional): City name (required for intra-city transit)
- `cityd` (optional): Destination city name (for inter-city transit)
- `strategy` (optional): Transit strategy
  - `0` - Fast (default, minimize time)
  - `1` - Minimize transfers
  - `2` - Minimize walking
  - `3` - No subway
  - `5` - Minimize cost
- `nightflag` (optional): Include night buses (0=no, 1=yes)
- `date` (optional): Departure date (YYYY-MM-DD) for scheduled transit
- `time` (optional): Departure time (HH:MM)

**Returns**:
- `route` object:
  - `distance` - Total distance including walking in meters
  - `duration` - Total travel time in seconds
  - `cost` - Total fare in CNY
  - `walking_distance` - Total walking distance in meters
  - `transits` - Array of route options with segments:
    - `bus` - Bus/subway line information
    - `railway` - Train information (inter-city)
    - `walking` - Walking segments
    - `cost` - Fare for this segment
    - `duration` - Time for this segment

**Example (Inter-city)**:
```javascript
mcp__plugin_amap-maps_amap-maps__transit_route({
  origin: "北京",
  destination: "上海",
  cityd: "上海",
  date: "2026-02-15",
  time: "08:00"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "route": {
    "transits": [{
      "cost": "553",
      "duration": "16200",
      "segments": [{
        "railway": {
          "name": "G3",
          "departure_stop": "北京南站",
          "arrival_stop": "上海虹桥站",
          "departure_time": "08:00",
          "arrival_time": "12:30"
        }
      }]
    }]
  }
}
```

**Example (Intra-city)**:
```javascript
mcp__plugin_amap-maps_amap-maps__transit_route({
  origin: "天安门",
  destination: "鸟巢",
  city: "北京",
  strategy: 0
})
```

**Use Cases**:
- Inter-city train/bus planning
- Subway route within cities
- Bus route finding
- Public transit cost estimation
- Multi-modal transportation planning

---

## Best Practices

### 1. Input Format
- **Coordinates**: Use "longitude,latitude" format (GCJ-02)
- **Addresses**: Use Chinese characters for best results
- **City names**: Use official Chinese names (北京 not Beijing)

### 2. Strategy Selection
- **Driving**: Use strategy 0 (fast) for time-sensitive trips
- **Transit**: Use strategy 0 (fast) for commuting, strategy 1 (fewer transfers) for luggage
- **Inter-city**: Always provide date/time for accurate schedules

### 3. Response Parsing
- Convert distance meters to km: `distance / 1000`
- Convert duration seconds to minutes: `duration / 60`
- Convert duration seconds to hours: `duration / 3600`
- Toll and cost are in CNY

### 4. Error Handling
- Status "1" = Success, "0" = Failure
- Check `info` field for error messages
- Common errors:
  - "INVALID_PARAMS" - Check coordinate format
  - "NO_RESULT" - Try alternative addresses
  - "DAILY_QUERY_OVER_LIMIT" - Rate limit exceeded

### 5. Multi-city Routes
- For inter-city: Use city names, not coordinates
- Always specify `cityd` for destination city
- Provide date/time for train schedules
- Results include high-speed rail, regular trains, buses

## Integration Patterns

### Pattern 1: Compare Transportation Modes
```markdown
1. Load `/gaode-maps routing`
2. Call `transit_route` for public option
3. Call `driving_route` for private option
4. Compare: duration, cost, convenience
5. Recommend based on user preferences
```

### Pattern 2: Multi-stop Itinerary
```markdown
1. Load `/gaode-maps routing`
2. Call `driving_route` with waypoints parameter
3. Get total distance and duration
4. Calculate fuel cost (distance * 0.7 CNY/km)
5. Add toll fees from response
```

### Pattern 3: Accessibility Check
```markdown
1. Load `/gaode-maps routing`
2. Call `transit_route` with strategy 2 (minimize walking)
3. Check `walking_distance` in response
4. If > 500m, suggest alternative or taxi
```

## Error Handling

**Retry Logic**:
```python
max_retries = 3
for attempt in range(max_retries):
    response = call_mcp_tool(params)
    if response.status == "1":
        return response
    if "OVER_LIMIT" in response.info:
        sleep(60)  # Wait 1 minute
    else:
        break  # Don't retry other errors
```

**Fallback Strategy**:
```markdown
1. Try Gaode Maps MCP tool
2. If error or no MCP: Use Google Maps skill
3. If no Google Maps: Use WebSearch
4. Parse web results and structure data
```

## Performance Tips

- Cache frequently used routes
- Batch multiple route requests when possible
- Use coordinates instead of addresses (faster)
- Pre-geocode addresses for repeat queries
- Monitor API quota usage daily

---

**Token Count**: ~2000 tokens (loaded on demand only)
