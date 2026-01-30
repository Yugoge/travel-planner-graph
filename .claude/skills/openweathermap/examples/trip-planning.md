# OpenWeatherMap - Trip Planning Example

Complete workflow for integrating weather data into travel planning.

## Scenario

**Trip Details**:
- Destination: Barcelona, Spain
- Dates: March 15-20, 2026 (6 days)
- Travelers: 2 adults
- Preferences: Mix of outdoor sightseeing and cultural activities
- Concerns: Weather-dependent activity planning

## Workflow

### Step 1: Initial Weather Assessment

**Load forecast tools**:
```
/openweathermap forecast
```

**Get 5-day forecast**:
```javascript
mcp__plugin_openweathermap_openweathermap__forecast_5day({
  location: "Barcelona, ES",
  units: "metric"
})
```

**Analysis**:
```
Day 1 (Mar 15): Clear, 18°C, pop: 0.1 → Perfect for outdoor
Day 2 (Mar 16): Partly cloudy, 19°C, pop: 0.2 → Good for outdoor
Day 3 (Mar 17): Rain, 15°C, pop: 0.8 → Indoor day
Day 4 (Mar 18): Cloudy, 17°C, pop: 0.4 → Flexible
Day 5 (Mar 19): Clear, 20°C, pop: 0.1 → Excellent outdoor
Day 6 (Mar 20): Partly cloudy, 18°C, pop: 0.3 → Good outdoor
```

### Step 2: Optimize Activity Schedule

**Original Itinerary** (before weather analysis):
- Day 1: Arrival, hotel check-in
- Day 2: Sagrada Familia, Park Güell
- Day 3: Beach day, outdoor markets
- Day 4: Gothic Quarter walking tour
- Day 5: Museums (Picasso, MNAC)
- Day 6: Montjuïc, departure

**Weather-Optimized Itinerary**:
- Day 1: Arrival, hotel check-in (weather irrelevant)
- Day 2: Sagrada Familia, Park Güell (clear weather ✓)
- Day 3: **Museums (Picasso, MNAC)** - moved from Day 5 (rain expected)
- Day 4: **Gothic Quarter walking tour** - keep (pop: 0.4 acceptable)
- Day 5: **Beach day, outdoor markets** - moved from Day 3 (clear weather ✓)
- Day 6: Montjuïc, departure (good weather ✓)

**Rationale**: Moved indoor museum day to rainy Day 3, moved beach/market day to clear Day 5.

### Step 3: Check Air Quality

**Load air quality tools**:
```
/openweathermap air-quality
```

**Get current AQI**:
```javascript
mcp__plugin_openweathermap_openweathermap__air_quality({
  location: "Barcelona, ES",
  forecast: false
})
```

**Result**:
```json
{
  "list": [{
    "main": {"aqi": 2},
    "components": {
      "pm2_5": 15.2,
      "pm10": 28.4,
      "o3": 45.0
    }
  }]
}
```

**Assessment**: AQI Level 2 (Fair) - No special precautions needed. All outdoor activities safe.

### Step 4: Check Weather Alerts

**Load alerts tools**:
```
/openweathermap alerts
```

**Get active alerts**:
```javascript
mcp__plugin_openweathermap_openweathermap__weather_alerts({
  location: "Barcelona, ES"
})
```

**Result**:
```json
{
  "alerts": []
}
```

**Assessment**: No active weather warnings. Safe to proceed with plans.

### Step 5: Current Weather on Arrival

**Load current weather tools**:
```
/openweathermap current
```

**Get current conditions** (day before departure):
```javascript
mcp__plugin_openweathermap_openweathermap__current_weather({
  location: "Barcelona, ES",
  units: "metric"
})
```

**Result**:
```json
{
  "weather": [{"main": "Clear", "description": "clear sky"}],
  "main": {
    "temp": 17.5,
    "feels_like": 16.8,
    "temp_min": 14.0,
    "temp_max": 19.0,
    "humidity": 62
  },
  "wind": {"speed": 3.2, "deg": 180},
  "sys": {
    "sunrise": 1710488400,
    "sunset": 1710531600
  }
}
```

**Assessment**: Pleasant conditions on arrival. No immediate weather concerns.

### Step 6: Packing Recommendations

**Based on forecast analysis**:

**Temperature Range**: 15°C - 20°C (59°F - 68°F)

**Clothing**:
- Light layers (temp range of 5°C)
- Long-sleeve shirts
- Light jacket or cardigan
- Comfortable walking shoes (some rain expected)
- Rain jacket or compact umbrella (Day 3 rain)
- Sunglasses (clear days)
- Light scarf (cool mornings)

**Special Items for Weather**:
- Waterproof bag cover (Day 3 rain)
- Sunscreen (UV protection on clear days)
- Reusable water bottle (warm afternoons)

**Not Needed**:
- Heavy winter coat (temps too warm)
- Shorts/tank tops (temps not hot enough)
- Snow gear (no snow forecast)
- Air pollution mask (AQI good)

### Step 7: Daily Weather Check Protocol

**Add to timeline**:
```json
{
  "daily_routine": {
    "07:00": "Check current weather and today's forecast",
    "07:15": "Check air quality if planning outdoor exercise",
    "07:30": "Check weather alerts",
    "07:45": "Adjust day's plans if needed based on conditions"
  }
}
```

**Decision Tree**:
```
Morning weather check:
├─ Alerts active? → Follow alert protocol, postpone outdoor
├─ High pop (>0.6)? → Activate indoor backup plan
├─ AQI > 3? → Limit outdoor exposure, wear mask
├─ Temp > 25°C? → Schedule indoor during afternoon heat
└─ All clear? → Proceed with planned outdoor activities
```

### Step 8: Transportation Weather Impact

**Check weather for inter-city travel days** (if any):

If traveling from Barcelona to Madrid on Day 4:
```javascript
// Check both cities
current_weather({ location: "Barcelona, ES" })
current_weather({ location: "Madrid, ES" })

// Check alerts for both
weather_alerts({ location: "Barcelona, ES" })
weather_alerts({ location: "Madrid, ES" })
```

**Considerations**:
- Rain in Barcelona: Allow extra time to airport/station
- Fog/visibility: Check flight/train status before departure
- Severe weather: Be prepared for delays, have buffer time

### Step 9: Activity-Specific Weather Requirements

**Beach Day (Day 5)**:
```
Required conditions:
- No rain (pop < 0.3) ✓ (pop: 0.1)
- Temp > 18°C ✓ (20°C forecast)
- Wind < 10 m/s ✓ (3.5 m/s expected)
- Sunny or partly cloudy ✓ (Clear forecast)

Status: EXCELLENT beach day
```

**Walking Tour (Day 4)**:
```
Required conditions:
- No heavy rain (pop < 0.6) ✓ (pop: 0.4)
- Comfortable walking temp ✓ (17°C)
- Visibility > 5km ✓

Status: GOOD for walking, bring light rain jacket as backup
```

**Park Visit (Day 2)**:
```
Required conditions:
- No rain ✓ (pop: 0.2)
- Pleasant temp for walking ✓ (19°C)
- Good visibility for photos ✓ (Clear)

Status: PERFECT for Park Güell visit
```

### Step 10: Budget Adjustments for Weather

**Weather-Related Costs**:
```json
{
  "weather_budget": {
    "rain_jacket": 0,  // Already own
    "umbrella_purchase": 15,  // Compact travel umbrella
    "indoor_backup_activities": 50,  // Museum entry if rain on Day 4
    "taxi_during_rain": 30,  // Avoid walking in heavy rain Day 3
    "total": 95
  }
}
```

**Savings from Weather Optimization**:
```json
{
  "savings": {
    "no_air_quality_masks_needed": 20,
    "no_extreme_heat_AC_costs": 30,
    "no_weather_related_cancellations": 0,
    "total_saved": 50
  }
}
```

**Net Weather Impact**: +€45 to budget

## Final Optimized Itinerary

```json
{
  "trip": "Barcelona March 15-20",
  "weather_optimized": true,

  "day_1": {
    "date": "2026-03-15",
    "weather": "Clear, 18°C",
    "activities": [
      "Arrival at BCN airport 10:00",
      "Hotel check-in",
      "Light walking in Gothic Quarter (weather permitting)",
      "Dinner at outdoor tapas bar (clear evening)"
    ],
    "weather_notes": "Excellent arrival weather, enjoy outdoor dining"
  },

  "day_2": {
    "date": "2026-03-16",
    "weather": "Partly cloudy, 19°C, pop: 0.2",
    "activities": [
      "Sagrada Familia 09:00-11:00",
      "Park Güell 12:00-15:00",
      "Beach walk at sunset (18:30)"
    ],
    "weather_notes": "Perfect for outdoor sightseeing, minimal rain chance"
  },

  "day_3": {
    "date": "2026-03-17",
    "weather": "Rain, 15°C, pop: 0.8",
    "activities": [
      "Picasso Museum 10:00-12:30",
      "Lunch at covered market",
      "MNAC (National Art Museum) 14:00-17:00",
      "Shopping in covered areas"
    ],
    "weather_notes": "Indoor day due to rain forecast, bring umbrella",
    "backup_transport": "Use metro or taxi instead of walking"
  },

  "day_4": {
    "date": "2026-03-18",
    "weather": "Cloudy, 17°C, pop: 0.4",
    "activities": [
      "Gothic Quarter walking tour 10:00-13:00",
      "La Boqueria market 13:00-14:00",
      "Barcelona Cathedral 14:30-16:00"
    ],
    "weather_notes": "Pack light rain jacket as precaution",
    "backup_plan": "If rain increases, shift to covered market shopping"
  },

  "day_5": {
    "date": "2026-03-19",
    "weather": "Clear, 20°C, pop: 0.1",
    "activities": [
      "Beach day at Barceloneta 10:00-14:00",
      "Outdoor lunch at beachfront restaurant",
      "Port Vell marina walk 15:00-17:00",
      "Sunset at Bunkers del Carmel 18:30"
    ],
    "weather_notes": "Excellent beach weather, bring sunscreen and sunglasses"
  },

  "day_6": {
    "date": "2026-03-20",
    "weather": "Partly cloudy, 18°C, pop: 0.3",
    "activities": [
      "Montjuïc morning (cable car, castle)",
      "Lunch in El Poble Sec",
      "Departure to airport 15:00"
    ],
    "weather_notes": "Good for cable car ride, clear views expected"
  }
}
```

## Key Takeaways

1. **Weather Assessment Changed Itinerary**: Moved indoor museum day to rainy Day 3, moved beach day to clear Day 5
2. **No Major Safety Concerns**: No weather alerts, acceptable air quality
3. **Minimal Weather-Related Budget Impact**: €45 for rain gear and backup transport
4. **Daily Flexibility Built In**: Each day has indoor backup options if forecast changes
5. **Packing Optimized**: Light layers for 15-20°C, rain jacket for Day 3
6. **Activity Timing Optimized**: Beach on clearest day, museums on rainy day

## Lessons for Future Trips

- Always check 5-day forecast before finalizing itinerary
- Have indoor backup plans for every outdoor activity
- Air quality rarely an issue in Western Europe, but always check for Asian cities
- Weather alerts critical for coastal/tropical destinations
- Re-check forecast 24 hours before travel for final adjustments
- Budget €50-100 for weather-related contingencies
