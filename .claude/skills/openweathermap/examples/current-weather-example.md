# Current Weather Example

Get current weather conditions for travel planning.

## Use Case

Check current weather at destination before departure to adjust packing and activities.

## Script Execution

### Example 1: New York

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/current.py "New York, US"
```

**Expected Output**:
```
Location: New York, US
Conditions: Clear Sky
Temperature: 18°C
Feels Like: 17°C
Range: 16°C - 20°C
Humidity: 65%
Pressure: 1013 hPa
Wind: 3.5 m/s at 240°
Visibility: 10.0 km
Cloud Cover: 5%
Sunrise: 06:45
Sunset: 19:32
```

### Example 2: London with Imperial Units

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/current.py "London, GB" --units imperial
```

**Expected Output**:
```
Location: London, GB
Conditions: Light Rain
Temperature: 55°F
Feels Like: 52°F
Range: 52°F - 58°F
Humidity: 78%
Pressure: 1008 hPa
Wind: 8.2 mph at 180°
Visibility: 6.5 km
Cloud Cover: 85%
Sunrise: 07:15
Sunset: 18:45
```

### Example 3: JSON Output for Parsing

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/current.py "Tokyo, JP" --json
```

**Expected Output** (abbreviated):
```json
{
  "coord": {"lon": 139.6917, "lat": 35.6895},
  "weather": [
    {
      "id": 800,
      "main": "Clear",
      "description": "clear sky",
      "icon": "01d"
    }
  ],
  "main": {
    "temp": 22.5,
    "feels_like": 21.8,
    "temp_min": 20.0,
    "temp_max": 24.5,
    "pressure": 1015,
    "humidity": 55
  },
  "wind": {
    "speed": 2.5,
    "deg": 120
  },
  "clouds": {"all": 10},
  "visibility": 10000,
  "sys": {
    "country": "JP",
    "sunrise": 1706659200,
    "sunset": 1706697600
  },
  "name": "Tokyo"
}
```

## Agent Integration

**For transportation agent**:
```markdown
When planning route, check weather at origin and destination:

1. Execute: python3 .claude/skills/openweathermap/scripts/current.py "<origin-city>"
2. Execute: python3 .claude/skills/openweathermap/scripts/current.py "<destination-city>"
3. Parse conditions, temperature, wind
4. Adjust route recommendations (e.g., avoid storm areas)
5. Suggest travel time adjustments if needed
```

**For attractions agent**:
```markdown
Before recommending outdoor activities:

1. Execute: python3 .claude/skills/openweathermap/scripts/current.py "<city-name>"
2. Check conditions and temperature
3. If rain: Suggest indoor attractions
4. If extreme heat/cold: Adjust activity timing
5. Provide weather-appropriate recommendations
```

## Error Handling

**If location not found**:
```bash
$ python3 .claude/skills/openweathermap/scripts/current.py "InvalidCity, XX"
Error: Failed after 3 attempts: MCP error: City not found
```

**Solution**: Use correct city name and country code format (e.g., "London, GB" not "London, UK")

**If API key missing**:
```bash
$ python3 .claude/skills/openweathermap/scripts/current.py "Paris, FR"
Error: OPENWEATHER_API_KEY environment variable not set
```

**Solution**: Set environment variable:
```bash
export OPENWEATHER_API_KEY="your-api-key-here"
```

## Notes

- Free tier allows 60 calls/minute
- Coordinates returned in latitude/longitude (WGS-84)
- Times displayed in local timezone
- Temperature in Celsius by default
