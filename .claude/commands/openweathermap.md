---
description: "OpenWeatherMap integration for weather forecasts, air quality, and weather alerts"
allowed-tools: Task, Read, Bash
argument-hint: "[category|help]"
model: inherit
---

# OpenWeatherMap Skill

Access OpenWeatherMap API via MCP server for accurate weather forecasts, current conditions, air quality, and weather alerts worldwide.

## Quick Start

**Prerequisites**: OpenWeatherMap MCP server must be configured (see Setup section below).

**Usage**:
```
/openweathermap [category]    # Load specific tool category
/openweathermap help          # Show available categories
```

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **current** - Current weather conditions
   - Real-time temperature and conditions
   - Humidity, pressure, wind speed
   - Visibility and cloud cover
   - Sunrise/sunset times

2. **forecast** - Weather forecasts
   - 5-day forecast (3-hour intervals)
   - Hourly forecast (48 hours)
   - Daily summaries
   - Temperature trends

3. **air-quality** - Air quality index
   - AQI values and categories
   - Pollutant concentrations
   - Health recommendations

4. **alerts** - Weather warnings
   - Severe weather alerts
   - Storm warnings
   - Temperature extremes
   - Precipitation alerts

## Loading Tool Categories

Load categories on demand to optimize token usage:

```markdown
To check current weather, load: /root/travel-planner/.claude/commands/openweathermap/tools/current.md
To get weather forecast, load: /root/travel-planner/.claude/commands/openweathermap/tools/forecast.md
To check air quality, load: /root/travel-planner/.claude/commands/openweathermap/tools/air-quality.md
To get weather alerts, load: /root/travel-planner/.claude/commands/openweathermap/tools/alerts.md
```

## Coordinate System

**Standard**: OpenWeatherMap uses WGS-84 coordinate system (standard GPS coordinates).
- Input: City names, coordinates (lat, lon), or location IDs
- Output: WGS-84 coordinates (latitude, longitude)
- Global coverage (all countries)

## Error Handling

**Transient errors** (retry with backoff):
- Network timeouts
- Rate limits (429)
- Server errors (5xx)

**Permanent errors** (don't retry):
- Invalid credentials (401)
- Forbidden (403)
- Invalid parameters (400)
- Not found (404)

**Graceful degradation**:
If MCP server unavailable, fall back to WebSearch for weather information.

## Language Support

- Input: City names in English or local language
- Output: Weather data with English descriptions
- Units: Metric (Celsius, meters/sec) or Imperial (Fahrenheit, mph)
- Default: Metric for international destinations

## MCP Server Setup

**Required**: User must configure OpenWeatherMap MCP server before using this skill.

### Step 1: Get API Key

Register at: https://openweathermap.org/api

**Recommended Plan**:
- Free tier: 60 calls/minute, 1,000,000 calls/month
- One Call API 3.0: Current + forecast + historical

### Step 2: Configure MCP Server

**Recommended Method: Environment Variable**

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openweathermap": {
      "command": "npx",
      "args": ["-y", "@openweathermap/mcp-server"],
      "env": {
        "OPENWEATHER_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

**Alternative: Set Environment Variable**

```bash
export OPENWEATHER_API_KEY="your_api_key_here"
```

### Step 3: Restart Claude Desktop

Required for MCP server configuration to take effect.

### Verification

This skill assumes MCP tools are available:
- `current_weather`
- `forecast_5day`
- `hourly_forecast`
- `air_quality`
- `weather_alerts`

If tools unavailable, skill will report error and suggest fallback to WebSearch.

## Rate Limits

- Free tier: 60 calls/minute, 1,000,000 calls/month
- Startup tier: 100 calls/minute, 3,000,000 calls/month
- Monitor usage at: https://home.openweathermap.org/api_keys

## Security

**Never hardcode API keys**. Always use:
- MCP server configuration (environment variables)
- Claude Desktop config file
- Project-specific `.env` files (if applicable)

## Examples

See: `/root/travel-planner/.claude/commands/openweathermap/examples/`

## For Travel Planning Agents

This skill is configured as an auxiliary service for all travel planning agents. Usage pattern:

1. Invoke `/openweathermap forecast` to load forecast tools
2. Use `forecast_5day` to check weather for destination
3. Parse response for temperature, precipitation, conditions
4. Adjust recommendations based on weather:
   - **Transportation**: Suggest train over flight in bad weather
   - **Attractions**: Indoor vs outdoor activities based on forecast
   - **Meals**: Outdoor dining feasible in good weather
   - **Shopping**: Include umbrella/raincoat in bad weather
   - **Entertainment**: Suggest indoor venues during rain
   - **Timeline**: Adjust activity timing to avoid rain/heat
   - **Budget**: Account for weather-related costs

**Integration Examples**:
- Attractions agent: Check forecast before recommending outdoor parks
- Meals agent: Suggest covered restaurants during rain
- Shopping agent: Add weather-appropriate clothing to recommendations
- Timeline agent: Schedule outdoor activities during best weather windows

See agent-specific configuration in `.claude/agents/*.md` for integration details.

## Weather-Based Decision Making

**Temperature Ranges**:
- Cold (<10°C): Warm clothing, indoor activities prioritized
- Mild (10-20°C): Layered clothing, flexible activities
- Warm (20-30°C): Light clothing, hydration important
- Hot (>30°C): Minimal outdoor time, air-conditioned venues

**Precipitation**:
- Rain: Indoor activities, covered venues, waterproof gear
- Snow: Winter sports, warm clothing, indoor alternatives
- Clear: Full range of outdoor activities

**Air Quality**:
- Good (AQI 0-50): All outdoor activities safe
- Moderate (AQI 51-100): Reduce prolonged outdoor exertion
- Unhealthy (AQI 101+): Indoor activities prioritized, masks recommended
