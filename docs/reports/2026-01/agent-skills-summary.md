# Travel Planner Agent Skills Summary

Updated: 2026-01-31

## Overview

This document provides a clear breakdown of which skills are used by each travel planning agent, distinguishing between international and China domestic capabilities.

---

## Agent Skill Breakdown

### 1. **accommodation** (Hotel Research)
**Skills**:
- `google-maps` (International)
- `gaode-maps` (China)
- `airbnb` (Global vacation rentals)

**Coverage**: Global

**Notes**:
- Uses Gaode Maps for China domestic locations
- Uses Google Maps for international locations
- Airbnb provides vacation rental alternatives worldwide

---

### 2. **attractions** (Sightseeing & Activities)
**Skills**:
- `google-maps` (International)
- `gaode-maps` (China)

**Coverage**: Global

**Notes**:
- Uses Gaode Maps for China POI search and place details
- Uses Google Maps for international attractions

---

### 3. **budget** (Budget Calculation)
**Skills**: None (removed weather)

**Coverage**: N/A

**Notes**:
- Calculates budgets based on data from other agents
- Weather-related expenses (umbrellas, clothing) included in shopping category if recommended
- No direct API calls needed

---

### 4. **entertainment** (Shows & Nightlife)
**Skills**:
- `google-maps` (International)
- `gaode-maps` (China)

**Coverage**: Global

**Notes**:
- Uses Gaode Maps for China entertainment venues
- Uses Google Maps for international venues
- Eventbrite skill retired (removed)

---

### 5. **meals** (Restaurant Research)
**Skills**:
- `google-maps` (International)
- `gaode-maps` (China)

**Coverage**: Global

**Notes**:
- Uses Gaode Maps for China restaurant search
- Uses Google Maps for international restaurants

---

### 6. **shopping** (Retail Destinations)
**Skills**:
- `google-maps` (International)
- `gaode-maps` (China)

**Coverage**: Global

**Notes**:
- Uses Gaode Maps for China shopping districts and malls
- Uses Google Maps for international shopping

---

### 7. **timeline** (Schedule Optimization)
**Skills**:
- `weather` (Global weather data)

**Coverage**: Global

**Notes**:
- Uses weather forecasts to optimize activity scheduling
- Accounts for rain, extreme heat/cold in timeline planning

---

### 8. **transportation** (Inter-City Travel)
**Skills**:
- `google-maps` (International routes outside China)
- `gaode-maps` (China domestic road/transit)
- `duffel-flights` (ALL flights - international AND China domestic)
- `weather` (Travel day weather considerations)

**Coverage**: Global

**Notes**:
- **Duffel Flights**: Confirmed working for China domestic flights (PEK→SHA tested ✅)
- Uses Gaode Maps for China road/transit alternatives
- Uses Google Maps for international non-China routes
- Weather considerations noted but no real-time API calls required

---

## Skill Capability Matrix

| Skill | Type | Coverage | Used By Agents |
|-------|------|----------|----------------|
| `google-maps` | Mapping/POI | International (worldwide except China) | accommodation, attractions, entertainment, meals, shopping, transportation |
| `gaode-maps` | Mapping/POI | China domestic | accommodation, attractions, entertainment, meals, shopping, transportation |
| `duffel-flights` | Flight Search | Global (international + China domestic) | transportation |
| `airbnb` | Vacation Rentals | Global | accommodation |
| `weather` | Weather Data | Global | timeline, transportation |

---

## China vs International Routing

### For China Domestic Travel:
- **Flights**: Use `duffel-flights` (confirmed working for PEK, SHA, CAN, etc.)
- **Road/Transit**: Use `gaode-maps` for high-speed rail, bus, driving
- **POI/Places**: Use `gaode-maps` for accurate Chinese addresses
- **Hotels**: Use `gaode-maps` + `airbnb`

### For International Travel (Outside China):
- **Flights**: Use `duffel-flights`
- **Road/Transit**: Use `google-maps`
- **POI/Places**: Use `google-maps`
- **Hotels**: Use `google-maps` + `airbnb`

### For Cross-Border Travel (China ↔ International):
- **Flights**: Use `duffel-flights` (supports both)
- **Origin/Destination POI**: Use `gaode-maps` for China side, `google-maps` for international side

---

## Retired Skills

### eventbrite (Retired 2026-01-31)
- **Reason**: API compatibility issues, 400 errors on all endpoints
- **Status**: Completely removed, all files deleted
- **Replacement**: Entertainment agent uses google-maps/gaode-maps for venue search

---

## Testing Status

All skills have been tested and verified:

✅ **google-maps**: Routing, place search confirmed working
✅ **gaode-maps**: POI search, routing confirmed working
✅ **duffel-flights**: International flights tested (JFK→LAX)
✅ **duffel-flights**: China domestic tested (PEK→SHA)
✅ **duffel-flights**: Multi-city tested (JFK→LAX→SFO)
✅ **airbnb**: Configured with --ignore-robots-txt
✅ **weather**: Timeline integration working

---

## Script-Based Implementation

**Duffel Flights** uses direct REST API Python scripts (not MCP):
- `search_flights.py` - Single/round-trip flights
- `search_multi_city.py` - Multi-city itineraries
- `get_offer_details.py` - Detailed flight information
- `search_airports.py` - Airport lookup
- `list_airlines.py` - Airline information

**Dependencies**: Only `requests` library required

**See**: `.claude/skills/duffel-flights/SKILL.md` for detailed usage

---

## Summary

- **8 agents** total
- **5 active skills**: google-maps, gaode-maps, duffel-flights, airbnb, weather
- **6 agents** use both google-maps and gaode-maps for global coverage
- **1 agent** (budget) uses no skills (pure calculation)
- **1 agent** (transportation) uses 4 skills for comprehensive travel options
- **Duffel Flights** supports BOTH international AND China domestic flights
- **Weather** only used by timeline and transportation agents (removed from budget)
