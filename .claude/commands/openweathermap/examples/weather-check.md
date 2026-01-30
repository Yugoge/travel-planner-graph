# Example: Weather Check for Trip Planning

Complete workflow for integrating weather data into travel planning.

## Scenario

User planning a 5-day trip to Chongqing, China from February 10-14, 2026.

## Step 1: Check Weather Alerts

First, check for any severe weather warnings.

```javascript
// Load alerts tools
// File: /root/travel-planner/.claude/commands/openweathermap/tools/alerts.md

const alerts = await weather_alerts({
  location: "Chongqing,CN"
});

console.log("Alert Check:", alerts.alert_count === 0 ? "No alerts" : `${alerts.alert_count} active alerts`);
```

**Result**:
```json
{
  "location": { "name": "Chongqing", "country": "CN" },
  "alerts": [],
  "alert_count": 0,
  "status": "No active alerts"
}
```

**Conclusion**: Safe to proceed with planning.

---

## Step 2: Get 5-Day Forecast

Retrieve weather forecast for trip dates.

```javascript
// Load forecast tools
// File: /root/travel-planner/.claude/commands/openweathermap/tools/forecast.md

const forecast = await forecast_5day({
  location: "Chongqing,CN",
  units: "metric"
});

// Aggregate into daily summaries
const dailySummary = aggregateForecast(forecast);
```

**Result**:
```javascript
[
  {
    date: "2026-02-10",
    temp_min: 8,
    temp_max: 15,
    temp_avg: 11.5,
    condition: "Clouds",
    rain_probability: 0.2,
    wind_avg: 2.8
  },
  {
    date: "2026-02-11",
    temp_min: 10,
    temp_max: 16,
    temp_avg: 13,
    condition: "Rain",
    rain_probability: 0.75,
    wind_avg: 3.2
  },
  {
    date: "2026-02-12",
    temp_min: 9,
    temp_max: 14,
    temp_avg: 11.5,
    condition: "Clouds",
    rain_probability: 0.3,
    wind_avg: 2.5
  },
  {
    date: "2026-02-13",
    temp_min: 11,
    temp_max: 18,
    temp_avg: 14.5,
    condition: "Clear",
    rain_probability: 0.1,
    wind_avg: 2.1
  },
  {
    date: "2026-02-14",
    temp_min: 12,
    temp_max: 19,
    temp_avg: 15.5,
    condition: "Clear",
    rain_probability: 0.05,
    wind_avg: 1.9
  }
]
```

**Analysis**:
- Day 1 (Feb 10): Cloudy, mild, low rain chance - **Good for most activities**
- Day 2 (Feb 11): Rain likely (75%) - **Plan indoor activities**
- Day 3 (Feb 12): Cloudy, slight rain chance - **Flexible day**
- Day 4 (Feb 13): Clear, warmer - **Excellent for outdoor activities**
- Day 5 (Feb 14): Clear, warmest - **Best day for outdoor sightseeing**

---

## Step 3: Check Air Quality

Assess air quality for outdoor activity planning.

```javascript
// Load air quality tools
// File: /root/travel-planner/.claude/commands/openweathermap/tools/air-quality.md

const airQuality = await air_quality({
  location: "Chongqing,CN"
});
```

**Result**:
```json
{
  "location": { "name": "Chongqing" },
  "aqi": {
    "value": 2,
    "category": "Fair",
    "description": "Acceptable quality, minor concern for sensitive individuals"
  },
  "components": {
    "pm2_5": 28.5,
    "pm10": 42.3,
    "o3": 55.2
  }
}
```

**Analysis**: Air quality is acceptable (AQI 2). All outdoor activities safe for general population. Sensitive individuals should monitor conditions.

---

## Step 4: Check Current Conditions (Day of Departure)

On departure day, check real-time conditions.

```javascript
// Load current weather tools
// File: /root/travel-planner/.claude/commands/openweathermap/tools/current.md

const current = await current_weather({
  location: "Chongqing,CN",
  units: "metric"
});
```

**Result**:
```json
{
  "location": { "name": "Chongqing" },
  "temperature": {
    "current": 10,
    "feels_like": 8,
    "min": 8,
    "max": 15
  },
  "weather": {
    "main": "Clouds",
    "description": "scattered clouds"
  },
  "humidity": 70,
  "wind": { "speed": 2.5 },
  "visibility": 10000
}
```

**Analysis**: Matches forecast. Conditions favorable for arrival day activities.

---

## Step 5: Weather-Based Itinerary Adjustments

### Day 1 (Feb 10) - Arrival Day
**Weather**: Cloudy, 8-15°C, low rain chance

**Recommendations**:
- Activities: Mix of indoor/outdoor (Hongya Cave, Jiefangbei Square)
- Clothing: Light jacket or sweater
- Notes: Good visibility for photos

### Day 2 (Feb 11) - Rain Day
**Weather**: Rain likely (75%), 10-16°C

**Recommendations**:
- Activities: Indoor attractions (Chongqing Museum, shopping malls, hotpot restaurants)
- Clothing: Waterproof jacket, umbrella (add to shopping list)
- Transportation: Covered walkways preferred, subway over walking
- Meals: Indoor restaurants, covered venues

### Day 3 (Feb 12) - Flexible Day
**Weather**: Cloudy, 9-14°C, slight rain chance

**Recommendations**:
- Activities: Flexible schedule with indoor backups (Ciqikou Ancient Town with museum fallback)
- Clothing: Layers, light rain jacket
- Notes: Check hourly forecast in morning for precise timing

### Day 4 (Feb 13) - Best Outdoor Day
**Weather**: Clear, 11-18°C, minimal rain

**Recommendations**:
- Activities: Major outdoor attractions (Dazu Rock Carvings day trip, river cruise)
- Clothing: Light layers, comfortable walking shoes
- Notes: Excellent photo opportunities, clear visibility

### Day 5 (Feb 14) - Departure Day
**Weather**: Clear, 12-19°C, warmest day

**Recommendations**:
- Activities: Morning outdoor sightseeing before departure (Eling Park, city viewpoints)
- Clothing: Light clothing, sun protection
- Transportation: Clear weather ideal for scenic routes

---

## Step 6: Shopping List Adjustments

Based on weather forecast, add to packing list:

```javascript
const weatherBasedItems = [
  {
    item: "Umbrella or waterproof jacket",
    reason: "Rain expected on Day 2 (75% probability)",
    priority: "high"
  },
  {
    item: "Light jacket or sweater",
    reason: "Temperatures 8-19°C, layering needed",
    priority: "high"
  },
  {
    item: "Comfortable walking shoes (waterproof)",
    reason: "Possible rain, extensive walking",
    priority: "medium"
  },
  {
    item: "Sunglasses",
    reason: "Clear weather days 4-5, good visibility",
    priority: "low"
  }
];
```

---

## Step 7: Timeline Optimization

### Hourly Forecast for Day 4 (Best Day)

```javascript
const hourlyForecast = await hourly_forecast({
  location: "Chongqing,CN",
  units: "metric"
});

// Find best 6-hour window for outdoor activities
const bestWindow = findBestWeatherWindow(hourlyForecast, 6);
```

**Result**:
```javascript
{
  start_time: "10:00",
  end_time: "16:00",
  avg_temp: 16,
  rain_probability: 0.05,
  score: 95,
  recommendation: "Optimal window for outdoor sightseeing"
}
```

**Timeline for Day 4**:
- 08:00-10:00: Breakfast, travel to Dazu Rock Carvings
- 10:00-16:00: **Outdoor sightseeing (optimal weather window)**
- 16:00-18:00: Return to city
- 18:00+: Indoor evening activities (weather cooling)

---

## Step 8: Budget Adjustments

Weather-related budget items:

```javascript
const weatherBudget = {
  umbrella: 15,  // Purchase on Day 1
  indoor_alternative_day2: 50,  // Museum admission instead of free outdoor park
  rain_gear: 25,  // Waterproof jacket if needed
  total_weather_adjustment: 90
};
```

---

## Complete Weather Integration Summary

### Weather Data Used
- **Alerts**: No active warnings ✓
- **5-Day Forecast**: Rain on Day 2, clear Days 4-5 ✓
- **Air Quality**: Fair (AQI 2), acceptable ✓
- **Current Conditions**: Verified on arrival ✓
- **Hourly Forecast**: Optimized Day 4 timing ✓

### Itinerary Adjustments
1. **Day 2 rescheduled**: Indoor activities due to rain
2. **Day 4 optimized**: Outdoor activities during best weather window (10:00-16:00)
3. **Day 5 leveraged**: Warmest day for morning outdoor sightseeing

### Shopping List Additions
- Umbrella/waterproof jacket (Day 2 rain)
- Light jacket (cool temperatures)
- Waterproof shoes

### Budget Impact
- +$90 for weather-related items and adjusted activities

### Travel Recommendations
- Transportation: Subway preferred on Day 2 (rain)
- Meals: Indoor dining on Day 2, outdoor options Days 4-5
- Photography: Best conditions Days 4-5 (clear, good visibility)

---

## Error Handling Example

What if weather data is unavailable?

```javascript
try {
  const forecast = await forecast_5day({ location: "Chongqing,CN" });
  return processForecast(forecast);
} catch (error) {
  console.warn("OpenWeatherMap unavailable, using fallback");

  // Fallback to WebSearch
  const webWeather = await webSearchWeather("Chongqing weather February 2026");

  return {
    source: "web_search",
    note: "Weather data from web search (less precise)",
    forecast: parseWebWeatherResults(webWeather),
    recommendation: "Monitor weather daily during trip"
  };
}
```

---

## Integration with Agents

### Attractions Agent
```javascript
// Before recommending attractions for Day 2
const dayWeather = forecast.find(d => d.date === "2026-02-11");

if (dayWeather.rain_probability > 0.6) {
  attractions = attractions.filter(a => a.indoor);
  note = "Indoor attractions prioritized due to high rain probability (75%)";
}
```

### Timeline Agent
```javascript
// Schedule outdoor activities on best weather days
const clearDays = forecast.filter(d => d.condition === "Clear");
clearDays.forEach(day => {
  scheduleOutdoorActivities(day.date);
});
```

### Transportation Agent
```javascript
// Prefer covered transportation on rainy days
const rainyDays = forecast.filter(d => d.rain_probability > 0.5);
rainyDays.forEach(day => {
  recommendSubwayOverWalking(day.date);
});
```

---

## Best Practices Demonstrated

1. **Check alerts first**: Safety before planning
2. **Get full forecast early**: Guides overall itinerary structure
3. **Use hourly forecast for optimization**: Fine-tune best days
4. **Check air quality**: Especially important for polluted cities
5. **Verify current conditions**: On departure day
6. **Adjust all aspects**: Activities, shopping, budget, timeline
7. **Implement fallbacks**: Handle API unavailability gracefully
8. **Document sources**: Transparency about data sources
9. **Cache appropriately**: Forecast valid 1-3 hours, current valid 10-15 minutes
10. **Communicate clearly**: Weather impact explained to user
