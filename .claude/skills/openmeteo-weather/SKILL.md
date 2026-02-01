---
name: openmeteo-weather
description: Global weather forecasts using Open-Meteo API (free, no API key needed)
category: weather
provider: Open-Meteo
api_type: REST API
requires_auth: false
supports_global: true
supports_china: true
---

# Open-Meteo Weather Skill

Free global weather forecasts with no API key required.

## Features

- **Global Coverage**: Works worldwide (China, US, Europe, everywhere)
- **No API Key**: Completely free, no registration needed
- **7-Day Forecast**: Temperature, precipitation, wind, weather conditions
- **Current Weather**: Real-time conditions
- **High Quality**: Data from national weather services

## Available Scripts

### 1. forecast.py - Get Weather Forecast

Get weather forecast for any location worldwide.

**Usage:**
```bash
python3 forecast.py <latitude> <longitude> [--days N] [--location-name NAME]
```

**Examples:**
```bash
# Beijing 7-day forecast
python3 forecast.py 39.9 116.4 --days 7 --location-name "Beijing"

# Shanghai 3-day forecast
python3 forecast.py 31.23 121.47 --days 3 --location-name "Shanghai"

# New York 7-day forecast
python3 forecast.py 40.71 -74.01 --days 7 --location-name "New York"
```

**Output:**
```json
{
  "location": {
    "name": "Beijing",
    "latitude": 39.875,
    "longitude": 116.375,
    "elevation": 49.0,
    "timezone": "Asia/Shanghai"
  },
  "current": {
    "temperature": 0.9,
    "feels_like": -3.7,
    "humidity": 33.0,
    "precipitation": 0.0,
    "weather_code": 1,
    "wind_speed": 7.6,
    "condition": "Mainly clear"
  },
  "forecast": [
    {
      "date": "2026-02-01",
      "temp_max": 5.1,
      "temp_min": -6.0,
      "precipitation": 0.0,
      "precipitation_probability": 0.0,
      "wind_speed_max": 10.5,
      "weather_code": 0,
      "condition": "Clear sky"
    }
  ],
  "units": {
    "temperature": "°C",
    "precipitation": "mm",
    "wind_speed": "km/h",
    "humidity": "%"
  }
}
```

## Weather Conditions

Weather codes follow WMO standard:
- 0: Clear sky
- 1: Mainly clear
- 2: Partly cloudy
- 3: Overcast
- 45/48: Fog
- 51/53/55: Drizzle (light/moderate/dense)
- 61/63/65: Rain (slight/moderate/heavy)
- 71/73/75: Snow (slight/moderate/heavy)
- 80/81/82: Rain showers
- 95/96/99: Thunderstorm

## Data Source

- Provider: Open-Meteo (https://open-meteo.com)
- Data: National weather services (NOAA, DWD, etc.)
- Resolution: High-resolution models (1-11km)
- Update frequency: Hourly
- License: Free for non-commercial use

## Dependencies

```bash
pip install openmeteo-requests requests-cache retry-requests numpy pandas
```

## Use Cases

**Travel Planning:**
- Check 7-day forecast for destinations
- Plan outdoor vs indoor activities based on weather
- Optimize trip timing for best weather

**China Travel:**
- Works perfectly for all Chinese cities
- No firewall issues (global API)
- Accurate forecasts from international models

**Global Coverage:**
- Same API works everywhere
- Consistent data format
- Reliable for international travel

## Advantages over other weather APIs

1. **No API Key**: Start using immediately
2. **Global Coverage**: Works in China and worldwide
3. **Free**: No costs, no limits for reasonable use
4. **Reliable**: Data from official weather services
5. **Fast**: Optimized FlatBuffers protocol

## Notes

- Forecasts up to 14 days available (7 days recommended for accuracy)
- All times in local timezone of location
- Temperature in Celsius, wind speed in km/h
- Precipitation probability: 0-100%
