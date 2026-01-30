---
name: openweathermap
description: |
  Get weather information for travel planning decisions.
  Use when planning activities, transportation, or checking conditions at destinations.
  Provides current weather, 5-day forecasts, hourly forecasts, air quality, and weather alerts.
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# OpenWeatherMap Weather Service

Access real-time weather data for informed travel planning decisions.

## Prerequisites

MCP server must be configured with OPENWEATHER_API_KEY environment variable.

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **current** - Current weather conditions
   - Get current weather by location
   - Temperature, humidity, conditions, wind
   - UV index and visibility

2. **forecast** - Weather forecasts
   - 5-day forecast (3-hour intervals)
   - Hourly forecast (48 hours)
   - Extended predictions

3. **air-quality** - Air quality data
   - Air Quality Index (AQI)
   - Pollutant levels (PM2.5, PM10, O3, etc.)
   - Health recommendations

4. **alerts** - Weather alerts and warnings
   - Severe weather alerts
   - Government warnings
   - Storm tracking

## Loading Tools

Load categories on demand:

```
/openweathermap current   # Loads tools/current.md
/openweathermap forecast  # Loads tools/forecast.md
/openweathermap air-quality  # Loads tools/air-quality.md
/openweathermap alerts    # Loads tools/alerts.md
```

## MCP Server Setup

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "openweathermap": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-openweathermap"],
      "env": {
        "OPENWEATHER_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Get API key from: https://openweathermap.org/api

## Security

- Never hardcode API keys in files
- Use environment variables for credentials
- Configure API key in MCP server configuration only
- Keep credentials out of version control

## Integration

Configured for agents:
- transportation (weather-based route planning)
- meals (outdoor dining conditions)
- accommodation (weather at destination)
- attractions (outdoor activity planning)
- shopping (market/street shopping weather)
- entertainment (outdoor event conditions)
- timeline (activity scheduling based on weather)
- budget (weather-related expense adjustments)

## Usage Pattern

```markdown
1. Load relevant tool category: `/openweathermap forecast`
2. Invoke MCP tool with location parameters
3. Parse weather data from response
4. Apply to planning decisions
5. Provide weather-aware recommendations
```

## Error Handling

- If MCP unavailable: Fall back to WebSearch for weather information
- If API key invalid: Return error message with setup instructions
- If location not found: Try alternative location formats or geocoding

## Examples

See `examples/` directory for detailed usage scenarios:
- Basic weather check for destination
- Multi-day forecast analysis
- Activity recommendations based on conditions
- Transportation planning with weather considerations
