# OpenWeatherMap - Weather Forecasts

Get weather predictions for trip planning.

## MCP Tools

### Tool 1: forecast_5day

**MCP Tool Name**: `mcp__plugin_openweathermap_openweathermap__forecast_5day`

**Parameters**:
- `location` (required): City name, coordinates, or location string
  - Format: "City, Country Code" (e.g., "Tokyo, JP")
  - Format: "lat,lon" (e.g., "35.6762,139.6503")
- `units` (optional): Temperature units (metric/imperial/standard)

**Returns**:
- `city`: City information
  - `name`: City name
  - `coord`: Coordinates
  - `country`: Country code
  - `timezone`: Timezone offset
  - `sunrise`: Sunrise time
  - `sunset`: Sunset time
- `list`: Array of forecast entries (40 entries, 3-hour intervals)
  - `dt`: Forecast timestamp (UTC)
  - `main`: Temperature and pressure data
    - `temp`: Temperature
    - `feels_like`: Perceived temperature
    - `temp_min`: Minimum temperature
    - `temp_max`: Maximum temperature
    - `pressure`: Atmospheric pressure
    - `humidity`: Humidity percentage
  - `weather`: Weather conditions array
    - `main`: Condition (Clear, Clouds, Rain, Snow, etc.)
    - `description`: Detailed description
    - `icon`: Weather icon code
  - `clouds`: Cloudiness percentage
  - `wind`: Wind data
    - `speed`: Wind speed
    - `deg`: Wind direction
  - `visibility`: Visibility in meters
  - `pop`: Probability of precipitation (0.0 to 1.0)
  - `rain`: Rain volume (mm, if present)
    - `3h`: Rain volume for last 3 hours
  - `snow`: Snow volume (mm, if present)
    - `3h`: Snow volume for last 3 hours
  - `dt_txt`: Forecast time as readable string

**Example**:
```javascript
// Get 5-day forecast for Barcelona
mcp__plugin_openweathermap_openweathermap__forecast_5day({
  location: "Barcelona, ES",
  units: "metric"
})

// Response example (excerpt):
{
  "city": {
    "name": "Barcelona",
    "coord": {"lat": 41.3888, "lon": 2.159},
    "country": "ES",
    "timezone": 3600,
    "sunrise": 1706598000,
    "sunset": 1706633400
  },
  "list": [
    {
      "dt": 1706626800,
      "main": {
        "temp": 16.5,
        "feels_like": 15.8,
        "temp_min": 15.2,
        "temp_max": 16.5,
        "pressure": 1015,
        "humidity": 72
      },
      "weather": [{"main": "Clouds", "description": "broken clouds", "icon": "04d"}],
      "clouds": {"all": 65},
      "wind": {"speed": 4.2, "deg": 240},
      "visibility": 10000,
      "pop": 0.15,
      "dt_txt": "2024-01-30 15:00:00"
    }
    // ... 39 more entries
  ]
}
```

**Use Cases**:
- Plan multi-day itinerary based on weather
- Identify best days for outdoor activities
- Schedule indoor activities on rainy days
- Optimize travel days vs activity days
- Plan sunrise/sunset photography sessions

---

### Tool 2: hourly_forecast

**MCP Tool Name**: `mcp__plugin_openweathermap_openweathermap__hourly_forecast`

**Parameters**:
- `location` (required): City name or coordinates
- `units` (optional): Temperature units (metric/imperial/standard)
- `hours` (optional): Number of hours to forecast (default: 48, max: 48)

**Returns**:
Similar structure to 5-day forecast but with hourly granularity:
- `list`: Array of hourly forecast entries (up to 48 entries)
  - Each entry has same structure as 5-day forecast
  - Time intervals are 1 hour instead of 3 hours

**Example**:
```javascript
// Get 24-hour forecast for Rome
mcp__plugin_openweathermap_openweathermap__hourly_forecast({
  location: "Rome, IT",
  units: "metric",
  hours: 24
})
```

**Use Cases**:
- Plan specific activity times during the day
- Check hourly temperature variation
- Find optimal time for outdoor dining
- Schedule beach visits during warmest hours
- Plan around expected rain showers

## Best Practices

### 1. Data Interpretation

**Probability of Precipitation (pop)**:
- 0.0-0.2: Very unlikely (safe for outdoor plans)
- 0.2-0.5: Possible (have backup plan)
- 0.5-0.8: Likely (prefer indoor activities)
- 0.8-1.0: Very likely (plan indoor alternatives)

**Temperature Planning**:
- Use `temp_min` and `temp_max` for daily range
- Check `feels_like` for actual comfort level
- Morning temps: entries at 06:00-09:00
- Afternoon temps: entries at 12:00-15:00
- Evening temps: entries at 18:00-21:00

**Weather Conditions**:
- "Clear" → Excellent for outdoor activities
- "Clouds" → Good for most activities
- "Rain" → Indoor activities or rain gear needed
- "Thunderstorm" → Avoid outdoor activities
- "Snow" → Special equipment/clothing needed

### 2. Activity Scheduling

**Outdoor Activities**:
```markdown
Filter forecast entries:
- pop < 0.3 (low rain chance)
- weather.main != "Rain" or "Thunderstorm"
- wind.speed < 10 m/s
- visibility > 5000m
→ Good for: hiking, sightseeing, beach, outdoor dining
```

**Indoor Flexibility**:
```markdown
If forecast shows:
- pop > 0.5 on Day 3
- weather.main = "Rain"
→ Schedule museums, shopping, indoor attractions on Day 3
```

**Temperature-Based Planning**:
```markdown
Daily temp analysis:
- temp_max > 30°C → Schedule indoor activities 12:00-16:00
- temp_min < 10°C → Pack warm layers
- temp range > 15°C → Pack versatile clothing
```

### 3. Multi-Day Trip Optimization

**Step 1**: Load 5-day forecast
**Step 2**: Analyze each day:
- Best day: Lowest pop, clearest conditions → outdoor highlights
- Moderate days: Partial clouds → flexible activities
- Worst day: High pop, rain → museums, shopping

**Step 3**: Reschedule itinerary to match weather
**Step 4**: Provide packing recommendations based on forecast

### 4. Sunrise/Sunset Planning

Use `city.sunrise` and `city.sunset` for:
- Photography golden hour planning
- Outdoor dining timing
- Beach sunset experiences
- Early morning hikes

### 5. Data Freshness

- Forecast accuracy decreases after 3 days
- Always mention forecast date in recommendations
- Re-check forecast closer to travel date
- Provide contingency plans for uncertain weather

## Error Handling

**Invalid Location**:
```markdown
1. Try with country code
2. Try nearby major city
3. Use coordinates if available
4. Fall back to WebSearch
```

**API Limits**:
```markdown
- Free tier: 60 calls/minute, 1M calls/month
- If exceeded: Use cached data or WebSearch fallback
```

**Missing Data**:
```markdown
- If rain/snow missing: Assume 0mm
- If visibility missing: Assume 10km
- If pop missing: Use weather.main to estimate
```

## Integration Examples

**Transportation Planning**:
```markdown
Check forecast for travel day:
- If pop > 0.6 → Allow extra travel time
- If snow forecast → Consider train over car
- If fog (visibility < 1000m) → Early departure not advised
```

**Activity Recommendations**:
```markdown
For each planned day:
1. Get forecast entry for activity time
2. If pop < 0.3 AND weather != "Rain" → Outdoor activity OK
3. If temp > 30°C → Recommend indoor during afternoon
4. If wind > 15 m/s → Avoid boat tours, cable cars
```

**Packing Suggestions**:
```markdown
Analyze 5-day forecast:
- If any day has rain → Pack umbrella/rain jacket
- If temp_min < 15°C → Pack warm layers
- If temp_max > 28°C → Pack light clothing
- If high humidity forecast → Breathable fabrics
```
