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

**Environment Variable Required**:
- `OPENWEATHER_API_KEY` - Get free API key from https://openweathermap.org/api
- Register at: https://home.openweathermap.org/users/sign_up
- Copy API key to environment

**Note**: No MCP server configuration needed. Scripts communicate directly with MCP via npx.

## Script-Based Implementation

This skill uses Python scripts that communicate with OpenWeatherMap MCP server via JSON-RPC 2.0 over stdio.
Scripts are executed on-demand, no MCP tools exposed to Claude.

### Available Scripts

**1. Current Weather** - `scripts/current.py`
   - Get current weather conditions
   - Temperature, humidity, conditions, wind
   - UV index and visibility

**2. Forecast** - `scripts/forecast.py`
   - 5-day forecast (3-hour intervals)
   - Configurable days (1-5)
   - Detailed hourly breakdown

**3. Alerts** - `scripts/alerts.py`
   - Severe weather alerts
   - Government warnings
   - Storm tracking and notifications

## Script Execution

### Current Weather

**Basic usage**:
```bash
python3 .claude/skills/openweathermap/scripts/current.py "New York, US"
```

**With units**:
```bash
python3 .claude/skills/openweathermap/scripts/current.py "London, GB" --units metric
python3 .claude/skills/openweathermap/scripts/current.py "Tokyo, JP" --units imperial
```

**JSON output**:
```bash
python3 .claude/skills/openweathermap/scripts/current.py "Paris, FR" --json
```

### Forecast

**5-day forecast**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "New York, US"
```

**Specific days**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "London, GB" --days 3
python3 .claude/skills/openweathermap/scripts/forecast.py "Tokyo, JP" --days 1
```

**With units**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "Berlin, DE" --units metric --days 5
```

### Weather Alerts

**Check alerts**:
```bash
python3 .claude/skills/openweathermap/scripts/alerts.py "Miami, US"
```

**Summary only**:
```bash
python3 .claude/skills/openweathermap/scripts/alerts.py "New Orleans, US" --summary
```

**JSON output**:
```bash
python3 .claude/skills/openweathermap/scripts/alerts.py "Houston, US" --json
```

## Environment Setup

Set API key before running scripts:

```bash
export OPENWEATHER_API_KEY="your-api-key-here"
```

Or add to `.env` file in project root:
```
OPENWEATHER_API_KEY=your-api-key-here
```

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
