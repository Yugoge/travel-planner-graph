# Weather Forecast Example

Get weather forecasts for multi-day travel planning.

## Use Case

Plan activities for upcoming trip based on expected weather conditions over next 5 days.

## Script Execution

### Example 1: 5-Day Forecast

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "New York, US"
```

**Expected Output**:
```
Forecast for: New York, US

=== Monday, January 30, 2026 ===
  Temperature: 15.2°C - 22.5°C
  Conditions: Clear Sky
  Hourly breakdown:
    00:00: 18.5°C, Clear Sky, Humidity 62%, Wind 2.5 m/s
    03:00: 16.2°C, Clear Sky, Humidity 68%, Wind 2.1 m/s
    06:00: 15.2°C, Few Clouds, Humidity 72%, Wind 1.8 m/s
    09:00: 18.8°C, Scattered Clouds, Humidity 58%, Wind 2.8 m/s
    12:00: 21.5°C, Scattered Clouds, Humidity 48%, Wind 3.2 m/s
    15:00: 22.5°C, Few Clouds, Humidity 45%, Wind 3.5 m/s
    18:00: 20.2°C, Clear Sky, Humidity 52%, Wind 3.0 m/s
    21:00: 18.0°C, Clear Sky, Humidity 60%, Wind 2.6 m/s

=== Tuesday, January 31, 2026 ===
  Temperature: 14.8°C - 21.2°C
  Conditions: Broken Clouds
  Hourly breakdown:
    00:00: 17.2°C, Few Clouds, Humidity 65%, Wind 2.3 m/s
    03:00: 15.8°C, Scattered Clouds, Humidity 70%, Wind 2.0 m/s
    ...

[Additional days truncated for brevity]
```

### Example 2: 3-Day Forecast

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "London, GB" --days 3
```

**Expected Output**:
```
Forecast for: London, GB

=== Thursday, February 1, 2026 ===
  Temperature: 8.5°C - 12.8°C
  Conditions: Light Rain
  Hourly breakdown:
    00:00: 10.2°C, Light Rain, Humidity 82%, Wind 4.5 m/s
    03:00: 9.5°C, Light Rain, Humidity 85%, Wind 4.2 m/s
    06:00: 8.5°C, Moderate Rain, Humidity 88%, Wind 5.0 m/s
    ...

[Next 2 days shown]
```

### Example 3: Imperial Units

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "Miami, US" --units imperial --days 2
```

**Expected Output**:
```
Forecast for: Miami, US

=== Friday, February 2, 2026 ===
  Temperature: 72.0°F - 85.5°F
  Conditions: Clear Sky
  Hourly breakdown:
    00:00: 75.2°F, Clear Sky, Humidity 68%, Wind 6.5 m/s
    ...
```

### Example 4: JSON Output

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "Tokyo, JP" --json --days 1
```

**Expected Output** (abbreviated):
```json
{
  "city": {
    "id": 1850144,
    "name": "Tokyo",
    "coord": {"lat": 35.6895, "lon": 139.6917},
    "country": "JP",
    "timezone": 32400
  },
  "list": [
    {
      "dt": 1706659200,
      "main": {
        "temp": 22.5,
        "feels_like": 21.8,
        "temp_min": 20.0,
        "temp_max": 24.5,
        "pressure": 1015,
        "humidity": 55
      },
      "weather": [
        {
          "id": 800,
          "main": "Clear",
          "description": "clear sky"
        }
      ],
      "wind": {"speed": 2.5, "deg": 120},
      "dt_txt": "2026-01-30 00:00:00"
    }
    // More forecast items...
  ]
}
```

## Agent Integration

**For timeline agent**:
```markdown
When creating multi-day itinerary:

1. Execute: python3 .claude/skills/openweathermap/scripts/forecast.py "<destination>" --days 5
2. Parse daily conditions and temperatures
3. Schedule outdoor activities on clear days
4. Schedule indoor activities on rainy days
5. Adjust timing for extreme temperatures
6. Provide weather-aware daily schedule
```

**For attractions agent**:
```markdown
When recommending activities:

1. Execute: python3 .claude/skills/openweathermap/scripts/forecast.py "<city>" --days 3
2. Identify best weather days
3. Recommend outdoor attractions on clear days (hiking, parks, beaches)
4. Recommend indoor attractions on poor weather days (museums, galleries)
5. Provide contingency plans for weather changes
```

## Parsing Tips

**Extract specific data from JSON**:
```bash
# Get temperatures for next 24 hours
python3 .claude/skills/openweathermap/scripts/forecast.py "Paris, FR" --json | \
  jq '.list[:8] | .[] | {time: .dt_txt, temp: .main.temp}'

# Get all rainy periods
python3 .claude/skills/openweathermap/scripts/forecast.py "London, GB" --json | \
  jq '.list[] | select(.weather[0].main == "Rain") | {time: .dt_txt, desc: .weather[0].description}'
```

## Error Handling

**If days out of range**:
```bash
$ python3 .claude/skills/openweathermap/scripts/forecast.py "Paris, FR" --days 10
usage: forecast.py [-h] [--days {1,2,3,4,5}] [--units {metric,imperial}] [--json] location
forecast.py: error: argument --days: invalid choice: 10 (choose from 1, 2, 3, 4, 5)
```

## Notes

- Forecast provided in 3-hour intervals
- Maximum 5-day forecast (API limitation)
- Includes temperature, conditions, wind, humidity
- Times in UTC, convert to local timezone as needed
