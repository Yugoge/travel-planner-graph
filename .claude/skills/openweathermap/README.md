# OpenWeatherMap Skill - Script-Based Implementation

Python script-based MCP integration for OpenWeatherMap weather data.

## Quick Start

### 1. Get API Key

Register at: https://openweathermap.org/api (free tier available)

### 2. Set Environment Variable

```bash
export OPENWEATHER_API_KEY="your-api-key-here"
```

Or add to project `.env` file:
```
OPENWEATHER_API_KEY=your-api-key-here
```

### 3. Run Scripts

**Current weather**:
```bash
python3 .claude/skills/openweathermap/scripts/current.py "New York, US"
```

**5-day forecast**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "London, GB" --days 3
```

**Weather alerts**:
```bash
python3 .claude/skills/openweathermap/scripts/alerts.py "Miami, US"
```

## File Structure

```
.claude/skills/openweathermap/
├── SKILL.md                          # Main skill documentation
├── README.md                         # This file
├── scripts/
│   ├── mcp_client.py                # Base MCP client (JSON-RPC 2.0)
│   ├── current.py                   # Current weather conditions
│   ├── forecast.py                  # Weather forecasts (1-5 days)
│   └── alerts.py                    # Weather alerts/warnings
├── examples/
│   ├── current-weather-example.md   # Current weather usage examples
│   ├── forecast-example.md          # Forecast usage examples
│   └── alerts-example.md            # Alerts usage examples
└── tools/
    ├── current.md                   # Tool documentation (reference)
    ├── forecast.md                  # Tool documentation (reference)
    ├── alerts.md                    # Tool documentation (reference)
    └── air-quality.md               # Tool documentation (reference)
```

## Scripts

### mcp_client.py

Base MCP client for JSON-RPC 2.0 communication with MCP server via stdio.

**Features**:
- Launches MCP server on-demand via npx
- JSON-RPC 2.0 protocol implementation
- Automatic retry with exponential backoff (3 attempts)
- Error handling and cleanup

**Usage** (import in other scripts):
```python
from mcp_client import MCPClient

client = MCPClient(
    package='@modelcontextprotocol/server-openweathermap',
    env_vars={'OPENWEATHER_API_KEY': api_key}
)
result = client.call_tool('get-current-weather', {'location': 'New York, US'})
```

### current.py

Get current weather conditions.

**Parameters**:
- `location` (required) - City name and country code (e.g., "New York, US")
- `--units` (optional) - metric (Celsius) or imperial (Fahrenheit), default: metric
- `--json` (optional) - Output raw JSON response

**Exit codes**:
- 0: Success
- 1: Error (API key missing, location invalid, network failure)

**Examples**:
```bash
python3 current.py "New York, US"
python3 current.py "London, GB" --units metric
python3 current.py "Tokyo, JP" --json
```

### forecast.py

Get weather forecast for 1-5 days.

**Parameters**:
- `location` (required) - City name and country code
- `--days` (optional) - Number of days (1-5), default: 5
- `--units` (optional) - metric or imperial, default: metric
- `--json` (optional) - Output raw JSON response

**Exit codes**:
- 0: Success
- 1: Error (API key missing, location invalid, network failure)

**Examples**:
```bash
python3 forecast.py "New York, US"
python3 forecast.py "London, GB" --days 3
python3 forecast.py "Tokyo, JP" --units imperial --days 5
```

### alerts.py

Get active weather alerts and warnings.

**Parameters**:
- `location` (required) - City name and country code
- `--summary` (optional) - Show brief summary only
- `--json` (optional) - Output raw JSON response

**Exit codes**:
- 0: Success (including no alerts present)
- 1: Error (API key missing, location invalid, network failure)

**Examples**:
```bash
python3 alerts.py "Miami, US"
python3 alerts.py "New Orleans, US" --summary
python3 alerts.py "Houston, US" --json
```

## Agent Integration

### Usage Pattern

Agents execute scripts via Bash tool:

```bash
python3 .claude/skills/openweathermap/scripts/<script>.py <location> [options]
```

### Configured Agents

- **transportation** - Weather-based route planning
- **meals** - Outdoor dining conditions
- **accommodation** - Weather at destination
- **attractions** - Outdoor activity planning
- **shopping** - Market/street shopping weather
- **entertainment** - Outdoor event conditions
- **timeline** - Activity scheduling based on weather
- **budget** - Weather-related expense adjustments

## API Limits

| Tier | Calls/Min | Calls/Month | Cost |
|------|-----------|-------------|------|
| Free | 60 | 1,000,000 | $0 |
| Startup | 600 | 3,000,000 | $40/month |

Monitor usage at: https://home.openweathermap.org/statistics

## Error Handling

### Common Errors

**API key missing**:
```
Error: OPENWEATHER_API_KEY environment variable not set
```
**Solution**: Set environment variable or add to .env file

**Invalid location**:
```
Error: Failed after 3 attempts: MCP error: City not found
```
**Solution**: Use correct format "CityName, CountryCode" (e.g., "London, GB")

**Rate limit exceeded**:
```
Error: Rate limit exceeded
```
**Solution**: Wait 1 minute (free tier: 60 calls/min) or upgrade plan

### Retry Logic

Scripts automatically retry on transient errors:
- Network timeouts: 3 attempts with exponential backoff
- Server errors (5xx): 3 attempts with backoff
- Rate limits: Automatic retry after delay

## Security

- Never commit API keys to version control
- Use environment variables for credentials
- Add `.env` to `.gitignore`
- Rotate API keys regularly
- Monitor usage for anomalies

## Testing

**Test current weather**:
```bash
export OPENWEATHER_API_KEY="your-key"
python3 .claude/skills/openweathermap/scripts/current.py "New York, US"
```

**Test forecast**:
```bash
python3 .claude/skills/openweathermap/scripts/forecast.py "London, GB" --days 3
```

**Test alerts**:
```bash
python3 .claude/skills/openweathermap/scripts/alerts.py "Miami, US"
```

**Test JSON parsing**:
```bash
python3 .claude/skills/openweathermap/scripts/current.py "Tokyo, JP" --json | jq .
```

## Documentation

- **SKILL.md** - Complete skill documentation with usage patterns
- **examples/** - Real-world usage examples for each script
- **tools/** - MCP tool documentation (reference only, not loaded in context)

## Support

- OpenWeatherMap API: https://openweathermap.org/api
- API Documentation: https://openweathermap.org/current
- MCP Package: @modelcontextprotocol/server-openweathermap
- Account Dashboard: https://home.openweathermap.org/

---

**Implementation Note**: This skill uses Python scripts that communicate with OpenWeatherMap MCP server via JSON-RPC 2.0 over stdio. No MCP server configuration needed in Claude Code. Scripts are executed on-demand via Bash tool.
