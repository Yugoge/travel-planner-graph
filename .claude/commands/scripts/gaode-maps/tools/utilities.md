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

## Quick Tips

Distance types: 0=straight-line (fast), 1=driving (accurate), 3=walking.
Batch compare: Up to 10 origins to 1 destination in single call.

Weather: Get 4-day forecast, schedule indoor activities on rain days.
Temperature: >30°C hot, 15-25°C pleasant, <5°C cold.

Limits: Max 10 origins per distance call, 4-day forecast only, city-level weather.

---

**Complete patterns and examples**: See commands/gaode-maps/tools/utilities.md
