# Google Maps - Weather Lookup

Lookup current weather data for locations using geocoding integration.

## MCP Tools

### Tool 1: lookup_weather

**MCP Tool Name**: `mcp__plugin_google-maps_google-maps__lookup_weather`

**Description**: Get current weather information for a location. Useful for basic weather checks when planning activities.

**Parameters**:
- `location` (required, object): Location to lookup weather
  - `latitude` (number): Location latitude
  - `longitude` (number): Location longitude
  - OR `address` (string): Location address (will be geocoded)

**Returns**:
- `weather` (object): Current weather data
  - `temperature` (number): Current temperature in Celsius
  - `temperature_fahrenheit` (number): Current temperature in Fahrenheit
  - `condition` (string): Weather condition (e.g., "Clear", "Rain", "Cloudy")
  - `humidity` (number): Relative humidity percentage
  - `wind_speed` (number): Wind speed in km/h
  - `wind_direction` (string): Wind direction (e.g., "NE", "SW")
  - `pressure` (number): Atmospheric pressure in hPa
  - `visibility` (number): Visibility in kilometers
  - `uv_index` (number): UV index (0-11+)
  - `timestamp` (string): Data timestamp
- `location` (object): Resolved location
  - `name` (string): Location name
  - `coordinates` (object): Lat/lng

**Example**:
```javascript
// Lookup weather by coordinates
lookup_weather({
  location: {
    latitude: 40.7580,
    longitude: -73.9855
  }
})
```

**Example with Address**:
```javascript
// Lookup weather by address
lookup_weather({
  location: {
    address: "Paris, France"
  }
})
```

**Use Cases**:
- Quick weather check for current conditions
- Temperature verification for clothing recommendations
- Basic weather context for activity planning
- Real-time weather updates during trip

---

## Best Practices

1. **Coordinates vs Address**:
   - Use coordinates when available (faster, more accurate)
   - Use address for user-friendly queries
   - Cache geocoding results to avoid repeated lookups

2. **Temperature Handling**:
   - Store both Celsius and Fahrenheit
   - Convert based on user preference
   - Formula: F = (C × 9/5) + 32

3. **Condition Interpretation**:
   - "Clear" / "Sunny": Good for outdoor activities
   - "Partly Cloudy": Generally safe for outdoor activities
   - "Cloudy": Consider indoor alternatives
   - "Rain" / "Drizzle": Indoor activities or rain gear
   - "Thunderstorm": Indoor activities only
   - "Snow": Cold weather gear, indoor activities

4. **UV Index Guidance**:
   - 0-2: Low (safe)
   - 3-5: Moderate (sunscreen recommended)
   - 6-7: High (sunscreen + hat)
   - 8-10: Very High (minimize sun exposure)
   - 11+: Extreme (avoid sun)

5. **Wind Speed**:
   - <10 km/h: Calm
   - 10-20 km/h: Breezy
   - 20-30 km/h: Windy
   - 30+ km/h: Very windy (may affect outdoor activities)

6. **Data Freshness**:
   - Check `timestamp` field
   - Current weather is point-in-time
   - For forecasts, use dedicated weather API (weather skill)

## Limitations

**What This Tool Does NOT Provide**:
- Multi-day forecasts (use `/weather forecast`)
- Hourly forecasts (use `/weather forecast`)
- Weather alerts (use `/weather alerts`)
- Air quality data (use `/weather air-quality`)
- Historical weather data

**When to Use Weather Skill Instead**:
- Need 5-day forecast
- Need hourly forecast
- Need severe weather alerts
- Need air quality index
- Need detailed meteorological data

## Error Handling

**Common Errors**:
- Invalid coordinates: Validate lat/lng ranges
- Address not found: Use more specific address or coordinates
- Service unavailable: Fall back to weather skill
- No data available: Location may be too remote

**Retry Pattern**:
```
Attempt 1: Direct MCP call
Attempt 2: Retry with coordinates if address failed
Attempt 3: Use weather skill as alternative
Fallback: Use WebSearch for basic weather info
```

## Integration Examples

**Quick Weather Check**:
```javascript
// Before finalizing day plan
const weather = lookup_weather({
  location: { latitude: city_lat, longitude: city_lng }
});

if (weather.condition === "Rain") {
  // Prioritize indoor attractions
} else if (weather.temperature > 30) {
  // Schedule outdoor activities in morning
} else {
  // Normal schedule
}
```

**Transportation Agent - Weather Impact**:
```javascript
// Check weather for travel day
const weather = lookup_weather({
  location: { address: destination_city }
});

if (weather.condition.includes("Storm")) {
  // Prefer train over flight
  preferred_mode = "train";
} else if (weather.wind_speed > 40) {
  // High winds may affect flights
  add_buffer_time = 60; // minutes
}
```

**Attractions Agent - Activity Selection**:
```javascript
// Select weather-appropriate attractions
const weather = lookup_weather({
  location: { latitude: city_lat, longitude: city_lng }
});

if (weather.temperature > 35 || weather.uv_index > 8) {
  // Hot weather: Indoor attractions or water activities
  recommended_types = ["museum", "aquarium", "shopping_mall"];
} else if (weather.condition === "Clear" && weather.temperature < 25) {
  // Perfect weather: Outdoor sightseeing
  recommended_types = ["park", "viewpoint", "monument"];
}
```

**Meals Agent - Dining Venue Selection**:
```javascript
// Select indoor or outdoor dining
const weather = lookup_weather({
  location: { latitude: restaurant_area_lat, longitude: restaurant_area_lng }
});

if (weather.condition === "Clear" && weather.temperature >= 18 && weather.temperature <= 28) {
  // Perfect for outdoor dining
  search_types.push("outdoor_seating", "terrace", "rooftop");
} else {
  // Indoor dining recommended
  search_types.push("indoor_seating");
}
```

**Shopping Agent - Weather Gear Recommendations**:
```javascript
// Recommend weather-appropriate items
const weather = lookup_weather({
  location: { address: destination_city }
});

const weather_items = [];

if (weather.condition.includes("Rain")) {
  weather_items.push("Umbrella", "Rain jacket", "Waterproof shoes");
}

if (weather.temperature < 10) {
  weather_items.push("Warm jacket", "Gloves", "Scarf");
}

if (weather.uv_index > 6) {
  weather_items.push("Sunscreen", "Sunglasses", "Sun hat");
}
```

## Response Format

**Structure weather data for output**:
```json
{
  "weather": {
    "temperature_c": 22,
    "temperature_f": 72,
    "condition": "Partly Cloudy",
    "humidity": 65,
    "wind_speed_kmh": 15,
    "wind_direction": "NE",
    "uv_index": 6,
    "recommendation": "Pleasant weather. Sunscreen recommended for outdoor activities."
  }
}
```

## Comparison with Weather Skill

| Feature | Google Maps Weather | Weather Skill |
|---------|-------------------|---------------------|
| Current weather | ✅ Yes | ✅ Yes |
| 5-day forecast | ❌ No | ✅ Yes |
| Hourly forecast | ❌ No | ✅ Yes |
| Weather alerts | ❌ No | ✅ Yes |
| Air quality | ❌ No | ✅ Yes |
| Historical data | ❌ No | ✅ Yes |

**Recommendation**: Use Google Maps weather for quick current checks. Use weather skill for comprehensive weather planning.
