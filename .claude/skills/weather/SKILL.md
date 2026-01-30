---
name: weather
description: Comprehensive weather data with global coverage using NOAA and Open-Meteo APIs
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Weather Skill

Comprehensive weather information for travel planning with global coverage.
Uses NOAA for US locations (more detailed) and Open-Meteo for international locations.

**MCP Server**: `@dangahagan/weather-mcp` (v1.6.1)
**API Coverage**: 12/12 tools (100%)
**API Key**: Optional (NCEI token for enhanced climate normals)

## Available Tools

1. **get_forecast** - Get future weather forecast for a location (global coverage)
2. **get_current_conditions** - Get current weather observations (US only)
3. **get_alerts** - Get active weather alerts, watches, warnings (US only)
4. **get_historical_weather** - Get historical weather data for specific past dates
5. **check_service_status** - Check NOAA and Open-Meteo service status
6. **search_location** - Search for location coordinates by name
7. **get_air_quality** - Get air quality index and pollutant data
8. **get_marine_conditions** - Get marine weather conditions for coastal areas
9. **get_weather_imagery** - Get radar and satellite imagery links
10. **get_lightning_activity** - Get real-time lightning activity data
11. **get_river_conditions** - Get river gauge and flood conditions
12. **get_wildfire_info** - Get active wildfire information

## How to Use

Execute scripts from skill directory:
```bash
cd /root/travel-planner/.claude/skills/weather
python3 scripts/<script_name>.py <arguments>
```

## Scripts

### 1. Forecast (forecast.py)

Get future weather forecast with flexible granularity.

```bash
# Basic 7-day forecast
python3 scripts/forecast.py 39.9042 116.4074

# Hourly forecast for next 3 days
python3 scripts/forecast.py 40.7128 -74.0060 --days 3 --granularity hourly

# With climate normals comparison
python3 scripts/forecast.py 51.5074 -0.1278 --include-normals
```

**Parameters**:
- `latitude`, `longitude`: Location coordinates
- `--days`: Number of days (1-16 for global, 1-7 for US)
- `--granularity`: daily (default) or hourly
- `--include-severe`: Severe weather probabilities (US only)
- `--include-normals`: Climate normals comparison
- `--source`: auto (default), noaa (US), openmeteo (global)

### 2. Current Conditions (current.py)

Get most recent weather observation (US only).

```bash
# Current conditions
python3 scripts/current.py 40.7128 -74.0060

# With fire weather indices
python3 scripts/current.py 34.0522 -118.2437 --include-fire-weather
```

**Parameters**:
- `latitude`, `longitude`: Location coordinates
- `--include-fire-weather`: Fire weather indices (Haines, Red Flag)
- `--include-normals`: Climate normals comparison

### 3. Weather Alerts (alerts.py)

Get active weather warnings and watches (US only).

```bash
# Active alerts only
python3 scripts/alerts.py 40.7128 -74.0060

# All alerts (including inactive)
python3 scripts/alerts.py 25.7617 -80.1918 --all
```

**Returns**: Severity, urgency, certainty, effective/expiration times

### 4. Historical Weather (historical.py)

Get weather data for specific past dates (global coverage).

```bash
# Single day
python3 scripts/historical.py 40.7128 -74.0060 2024-01-15

# Date range
python3 scripts/historical.py 51.5074 -0.1278 2024-01-01 2024-01-07
```

**Data Sources**:
- NOAA: Last 7 days (US only)
- Open-Meteo: Worldwide, back to 1940

### 5. Service Status (status.py)

Check if weather services are operational.

```bash
python3 scripts/status.py
```

**Returns**: NOAA and Open-Meteo service health status

### 6. Location Search (location.py)

Search for location coordinates by name.

```bash
python3 scripts/location.py "Beijing, China"
python3 scripts/location.py "New York" --limit 5
```

**Returns**: Coordinates, country, timezone for matching locations

### 7. Air Quality (air_quality.py)

Get air quality index and pollutant concentrations.

```bash
python3 scripts/air_quality.py 39.9042 116.4074
```

**Returns**: AQI, PM2.5, PM10, CO, NO2, O3, SO2 levels

### 8. Marine Conditions (marine.py)

Get marine weather for coastal and ocean areas.

```bash
python3 scripts/marine.py 25.7617 -80.1918
```

**Returns**: Wave height, period, direction, water temperature

### 9. Weather Imagery (imagery.py)

Get radar and satellite imagery links.

```bash
python3 scripts/imagery.py 40.7128 -74.0060 --type radar
```

**Types**: radar, satellite

### 10. Lightning Activity (lightning.py)

Get real-time lightning strike data.

```bash
python3 scripts/lightning.py 40.7128 -74.0060 --radius 50
```

**Parameters**:
- `--radius`: Search radius in kilometers (default: 50)

### 11. River Conditions (river.py)

Get river gauge data and flood warnings.

```bash
python3 scripts/river.py 40.7128 -74.0060
```

**Returns**: Water level, flow rate, flood stage status

### 12. Wildfire Info (wildfire.py)

Get active wildfire information.

```bash
python3 scripts/wildfire.py 34.0522 -118.2437 --radius 100
```

**Returns**: Fire name, location, size, containment, start date

## Output Format

All scripts output:
- **stdout**: JSON formatted data
- **stderr**: Error messages

## Error Handling

Scripts return structured errors with status page links when services are unavailable.
Use `check_service_status` to verify API availability.

## Tool Name Verification

Tool names verified against actual MCP server source code (v1.6.1):
- All 12 tools match source code definitions
- Parameter names match API expectations
- No assumed tool names
