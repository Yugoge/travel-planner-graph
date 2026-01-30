---
name: openweathermap
description: Weather information for travel planning
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# OpenWeatherMap Skill

Get weather forecasts, alerts for travel planning.

## How to Use

```bash
cd /root/travel-planner/.claude/skills/openweathermap
python3 scripts/current.py "LOCATION"
python3 scripts/forecast.py "LOCATION" --days N
python3 scripts/alerts.py "LOCATION"
```

## Examples

**Current Weather**:
```bash
python3 scripts/current.py "New York, US"
```

**Forecast**:
```bash
python3 scripts/forecast.py "London, GB" --days 3
```

**Alerts**:
```bash
python3 scripts/alerts.py "Miami, US"
```

Returns JSON with temperature, conditions, alerts.
