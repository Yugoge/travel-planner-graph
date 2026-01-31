# Gaode Maps - Utility Tools

Supporting tools for distance calculation and weather information.

## MCP Tools

### Tool 1: distance_measure

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__distance_measure`

**Purpose**: Calculate straight-line or driving distance between multiple locations.

**Parameters**:
- `origins` (required): Starting point(s) as "lng,lat" or "lng,lat|lng,lat|..."
  - Single origin or multiple origins
  - Maximum 10 origins per request
- `destination` (required): Destination point as "lng,lat"
  - Single destination only
- `type` (optional): Distance calculation method
  - `0` - Straight-line distance (default, fastest)
  - `1` - Driving distance (considers roads, slower)
  - `3` - Walking distance (considers pedestrian paths)

**Returns**:
- `results` array, each containing:
  - `origin_id` - Index of origin (1, 2, 3...)
  - `dest_id` - Always "1" (single destination)
  - `distance` - Distance in meters
  - `duration` - Estimated travel time in seconds (if type=1 or 3)
  - `info` - Status message

**Example (Single Distance)**:
```javascript
mcp__plugin_amap-maps_amap-maps__distance_measure({
  origins: "116.397428,39.90923",  // Tiananmen
  destination: "116.407526,39.90403",  // Forbidden City
  type: 0
})
```

**Response Structure**:
```json
{
  "status": "1",
  "count": "1",
  "results": [{"distance": "850", "duration": "0"}]
}
```

**Example (Multiple Origins)**:
```javascript
mcp__plugin_amap-maps_amap-maps__distance_measure({
  origins: "116.397428,39.90923|116.480881,39.996567|116.310003,39.991957",
  destination: "116.407526,39.90403",
  type: 1  // Driving distance
})
```

**Response Structure**:
```json
{
  "status": "1",
  "count": "3",
  "results": [
    {"origin_id": "1", "distance": "1250", "duration": "420"},
    {"origin_id": "2", "distance": "15300", "duration": "1860"},
    {"origin_id": "3", "distance": "12800", "duration": "1620"}
  ]
}
```

**Use Cases**:
- Compare distances from multiple hotels to attraction
- Calculate "as the crow flies" distance between cities
- Estimate driving time for route planning
- Find closest hotel to destination
- Validate feasibility of daily itinerary

**Type Selection Guide**:
- **Type 0 (Straight-line)**: Quick feasibility check, city-to-city distance
- **Type 1 (Driving)**: Car/taxi route planning, accurate duration
- **Type 3 (Walking)**: Pedestrian accessibility check, walkability

---

### Tool 2: weather_info

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__weather_info`

**Purpose**: Get current weather and forecast for Chinese cities.

**Parameters**:
- `city` (required): City name or adcode
  - Name: "北京", "上海", "成都"
  - Adcode: "110000" (Beijing), "310000" (Shanghai)
- `extensions` (optional): Forecast type
  - `base` - Current weather only (default)
  - `all` - Current + 4-day forecast

**Returns (extensions=base)**:
- `lives` array with current conditions:
  - `province` - Province name
  - `city` - City name
  - `adcode` - Administrative code
  - `weather` - Weather description (Chinese)
  - `temperature` - Current temperature (°C)
  - `winddirection` - Wind direction (Chinese)
  - `windpower` - Wind power level (1-12)
  - `humidity` - Relative humidity (%)
  - `reporttime` - Data timestamp (YYYY-MM-DD HH:MM:SS)

**Returns (extensions=all)**:
- `forecasts` array with forecast data:
  - `province`, `city`, `adcode` - Location info
  - `reporttime` - Forecast issue time
  - `casts` - Array of daily forecasts (4 days):
    - `date` - Date (YYYY-MM-DD)
    - `week` - Day of week (1-7)
    - `dayweather` - Daytime weather
    - `nightweather` - Nighttime weather
    - `daytemp` - Daytime high (°C)
    - `nighttemp` - Nighttime low (°C)
    - `daywind` - Daytime wind direction
    - `nightwind` - Nighttime wind direction
    - `daypower` - Daytime wind power
    - `nightpower` - Nighttime wind power

**Example (Current Weather)**:
```javascript
mcp__plugin_amap-maps_amap-maps__weather_info({
  city: "北京",
  extensions: "base"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "lives": [{
    "city": "北京市",
    "weather": "晴",
    "temperature": "15",
    "humidity": "45"
  }]
}
```

**Example (4-day Forecast)**:
```javascript
mcp__plugin_amap-maps_amap-maps__weather_info({
  city: "成都",
  extensions: "all"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "forecasts": [{
    "city": "成都市",
    "casts": [
      {"date": "2026-01-30", "dayweather": "多云", "daytemp": "18", "nighttemp": "10"},
      {"date": "2026-01-31", "dayweather": "小雨", "daytemp": "16", "nighttemp": "11"}
      // ... (4 total days)
    ]
  }]
}
```

**Use Cases**:
- Check weather before trip departure
- Plan outdoor activities around forecast
- Pack appropriate clothing
- Reschedule rain-sensitive attractions
- Provide weather context in itinerary

**Weather Descriptions (Chinese)**:
| Chinese | English | Icon |
|---------|---------|------|
| 晴 | Sunny | ☀️ |
| 多云 | Partly Cloudy | ⛅ |
| 阴 | Overcast | ☁️ |
| 小雨 | Light Rain | 🌧️ |
| 中雨 | Moderate Rain | 🌧️ |
| 大雨 | Heavy Rain | ⛈️ |
| 雪 | Snow | ❄️ |
| 雾 | Fog | 🌫️ |
| 霾 | Haze | 😷 |

---

## Best Practices

### 1. Distance Calculation Strategy

**Choosing Type**:
```markdown
Quick estimation:
- Use type=0 (straight-line)
- Convert to rough driving: distance * 1.3
- Good for feasibility checks

Accurate planning:
- Use type=1 (driving) for cars
- Use type=3 (walking) for pedestrians
- Cache results to avoid repeated calls
```

**Multiple Hotels Comparison**:
```markdown
1. Geocode all hotel addresses
2. Geocode main attraction/destination
3. Use distance_measure with multiple origins
4. Sort by distance or duration
5. Recommend closest hotel
```

**Performance**:
```python
# Batch compare 5 hotels to 1 destination
hotels = ["116.397,39.909|116.408,39.904|116.420,39.890|..."]
destination = "116.407526,39.90403"
result = distance_measure(origins=hotels, destination=destination, type=1)
# Returns 5 distances in one call
```

### 2. Weather Integration Strategy

**Trip Planning Phase**:
```markdown
1. Get 4-day forecast for destination
2. Identify rain days
3. Schedule indoor activities on rain days
4. Schedule outdoor activities on clear days
5. Add weather warnings to itinerary
```

**Daily Recommendations**:
```markdown
1. Check current weather
2. If rainy: Suggest indoor alternatives
3. If hot (>30°C): Suggest early morning/evening activities
4. If cold (<5°C): Warn about indoor heating in transport
5. If foggy/hazy: Warn about visibility
```

**Packing Suggestions**:
```python
def suggest_packing(forecast):
    temps = [day["daytemp"] for day in forecast["casts"]]
    max_temp = max(temps)
    min_temp = min(temps)

    if max_temp > 30:
        return "Pack light clothing, sunscreen, hat"
    elif min_temp < 10:
        return "Pack warm layers, jacket, gloves"
    elif "雨" in any(day["dayweather"] for day in forecast["casts"]):
        return "Pack umbrella or raincoat"
    else:
        return "Pack comfortable walking clothes"
```

### 3. Error Handling

**Distance Measure Errors**:
```python
for result in results:
    if result["info"] != "OK":
        # Origin unreachable or invalid coordinates
        continue
    distance_km = float(result["distance"]) / 1000
    duration_min = float(result["duration"]) / 60
```

**Weather Errors**:
- "INVALID_USER_SCODE" - City name incorrect, try adcode
- "NO_DATA" - City not in database, try nearby major city
- Rate limited - Cache weather data, refresh hourly max

### 4. Data Interpretation

**Distance Context**:
- < 1 km - Walking distance (10-15 min walk)
- 1-5 km - Short taxi ride (10-20 min)
- 5-20 km - Cross-city travel (30-60 min)
- 20-100 km - Suburban/nearby city (1-2 hours)
- > 100 km - Inter-city, consider train/flight

**Temperature Context** (China climate):
- > 35°C - Very hot, avoid midday outdoors
- 25-35°C - Warm, comfortable for sightseeing
- 15-25°C - Pleasant, ideal for outdoor activities
- 5-15°C - Cool, bring layers
- < 5°C - Cold, heavy winter clothing needed

**Wind Power Levels**:
- ≤3 - Light breeze, no impact
- 4-5 - Moderate wind, affects umbrellas
- 6-7 - Strong wind, difficult outdoor activities
- ≥8 - Very strong, avoid outdoor activities

## Integration Patterns

### Pattern 1: Hotel Selection by Distance
```markdown
1. Load `/gaode-maps utilities`
2. Geocode all candidate hotels
3. Geocode main destination/attraction
4. Use distance_measure with type=1 (driving)
5. Sort by duration
6. Recommend top 3 by distance + rating
```

### Pattern 2: Daily Feasibility Check
```markdown
1. Calculate distances between day's activities
2. Sum total walking distance
3. If > 10 km: Warn about tiring day
4. If > 5 km between consecutive: Suggest taxi
5. Adjust schedule or add buffer time
```

### Pattern 3: Weather-adjusted Itinerary
```markdown
1. Load `/gaode-maps utilities`
2. Get 4-day forecast for destination
3. For each day:
   - If rain: Move indoor activities to this day
   - If clear: Schedule outdoor/scenic activities
   - If extreme temp: Add warning notes
4. Output weather-optimized itinerary
```

### Pattern 4: Multi-city Distance Matrix
```markdown
1. Collect all cities in itinerary
2. Geocode each city center
3. For each pair:
   - Calculate straight-line distance
   - If < 300 km: Consider train/bus
   - If > 300 km: Consider flight
4. Recommend transportation modes
```

## Performance Tips

- **Cache weather**: Update hourly, not per-request
- **Batch distances**: Calculate multiple origins in one call (max 10)
- **Use straight-line**: For quick checks, refine with driving later
- **Geocode once**: Store coordinates, reuse for multiple distance calls
- **Forecast once per trip**: 4-day forecast covers most trips

## Limitations

**Distance Measure**:
- Maximum 10 origins per request
- Single destination only (not N×M matrix)
- Type 1/3 may be slower than type 0
- Real-time traffic not included (use routing tools for that)

**Weather Info**:
- 4-day forecast only (not extended)
- City-level only (not district-specific)
- Updates every 1-3 hours (not real-time)
- No severe weather alerts (use dedicated weather APIs)

## Data Sources

- **Distance**: Gaode Maps road network database
- **Weather**: China Meteorological Administration data
- **Update Frequency**:
  - Distance: Real-time road network (updated daily)
  - Weather: Updated every 1-3 hours

---

**Token Count**: ~1800 tokens (loaded on demand only)
