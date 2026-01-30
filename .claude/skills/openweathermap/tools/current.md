# OpenWeatherMap - Current Weather

Get real-time weather conditions for any location.

## MCP Tools

### Tool 1: current_weather

**MCP Tool Name**: `mcp__plugin_openweathermap_openweathermap__current_weather`

**Parameters**:
- `location` (required): City name, coordinates, or location string
  - Format: "City, Country Code" (e.g., "London, UK")
  - Format: "lat,lon" (e.g., "51.5074,-0.1278")
  - Format: City name only (e.g., "Tokyo")
- `units` (optional): Temperature units
  - "metric" (Celsius, m/s wind) - default
  - "imperial" (Fahrenheit, mph wind)
  - "standard" (Kelvin)

**Returns**:
- `location`: Location name
- `coord`: Latitude and longitude
- `weather`: Array of weather conditions
  - `main`: Main condition (Clear, Clouds, Rain, etc.)
  - `description`: Detailed description
  - `icon`: Weather icon code
- `main`: Main weather data
  - `temp`: Current temperature
  - `feels_like`: Perceived temperature
  - `temp_min`: Minimum temperature
  - `temp_max`: Maximum temperature
  - `pressure`: Atmospheric pressure (hPa)
  - `humidity`: Humidity percentage
- `visibility`: Visibility in meters
- `wind`: Wind data
  - `speed`: Wind speed
  - `deg`: Wind direction (degrees)
  - `gust`: Wind gust speed
- `clouds`: Cloudiness percentage
- `dt`: Data calculation timestamp (UTC)
- `sys`: System data
  - `sunrise`: Sunrise time (UTC)
  - `sunset`: Sunset time (UTC)
  - `country`: Country code
- `timezone`: Timezone offset from UTC (seconds)

**Example**:
```javascript
// Get current weather for Paris
mcp__plugin_openweathermap_openweathermap__current_weather({
  location: "Paris, FR",
  units: "metric"
})

// Response example:
{
  "location": "Paris",
  "coord": {"lat": 48.8566, "lon": 2.3522},
  "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
  "main": {
    "temp": 18.5,
    "feels_like": 17.8,
    "temp_min": 16.2,
    "temp_max": 20.1,
    "pressure": 1013,
    "humidity": 65
  },
  "visibility": 10000,
  "wind": {"speed": 3.5, "deg": 220},
  "clouds": {"all": 0},
  "dt": 1706624400,
  "sys": {
    "sunrise": 1706598120,
    "sunset": 1706632680,
    "country": "FR"
  },
  "timezone": 3600
}
```

**Use Cases**:
- Check current conditions before outdoor activities
- Verify weather at destination before departure
- Compare weather across multiple cities
- Get real-time temperature for packing decisions
- Check visibility for photography or sightseeing
- Verify wind conditions for outdoor events

## Best Practices

1. **Location Format**:
   - Use "City, Country Code" for accuracy (e.g., "Beijing, CN")
   - For coordinates, use format "lat,lon" without spaces
   - Test location name first if unsure

2. **Units Selection**:
   - Use "metric" for most international travelers
   - Use "imperial" only when specifically requested
   - Specify units to avoid confusion

3. **Data Interpretation**:
   - `feels_like` is more useful than `temp` for outdoor planning
   - Check both `temp_min` and `temp_max` for day planning
   - Visibility <1000m may affect outdoor activities
   - Wind speed >10 m/s (36 km/h) affects outdoor comfort

4. **Timing**:
   - Data is updated every 10-15 minutes
   - Use `dt` timestamp to check data freshness
   - Convert `sunrise` and `sunset` times using timezone offset

## Error Handling

**Common Errors**:
- "city not found": Try alternative spelling or use coordinates
- "Invalid API key": Check MCP configuration
- "API limit exceeded": Wait or upgrade API plan

**Fallback Strategy**:
```markdown
1. Try with country code: "Paris, FR" instead of "Paris"
2. Try coordinates if city name fails
3. Fall back to WebSearch: "current weather [location]"
```

## Integration with Planning

**Transportation**:
- Check weather at departure and arrival cities
- Consider visibility for driving routes
- Check wind for flight delays

**Activities**:
- `temp` + `feels_like` for outdoor activity comfort
- `weather.main` = "Rain" → indoor alternatives
- `visibility` < 5000m → skip viewpoint visits

**Packing**:
- Use `temp_min` and `temp_max` range for clothing
- Check `humidity` for comfort planning
- Verify `wind.speed` for jacket requirements
