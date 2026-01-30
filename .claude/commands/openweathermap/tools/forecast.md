# OpenWeatherMap - Forecast Tools

Weather forecast tools for short-term and medium-term planning.

## Available Tools

### 1. forecast_5day

Get 5-day weather forecast with 3-hour intervals.

**MCP Tool**: `forecast_5day`

**Parameters**:
- `location` (required): City name, coordinates, or location ID
- `units` (optional): Unit system (metric, imperial, standard)

**Returns**:
- 40 data points (5 days × 8 intervals/day)
- Temperature forecast
- Weather conditions
- Precipitation probability
- Wind speed and direction
- Cloud cover
- Humidity
- Atmospheric pressure

**Example**:
```javascript
// Get 5-day forecast for Chengdu
forecast_5day({
  location: "Chengdu,CN",
  units: "metric"
})
```

**Response Format**:
```json
{
  "location": {
    "name": "Chengdu",
    "country": "CN",
    "coordinates": { "lat": 30.6667, "lon": 104.0667 }
  },
  "forecast": [
    {
      "dt": 1738267200,
      "dt_txt": "2026-01-30 12:00:00",
      "temperature": {
        "current": 15.2,
        "feels_like": 14.5,
        "min": 13.8,
        "max": 15.2
      },
      "weather": {
        "main": "Clouds",
        "description": "scattered clouds"
      },
      "clouds": 40,
      "wind": { "speed": 2.5, "deg": 180 },
      "visibility": 10000,
      "pop": 0.15,
      "humidity": 70,
      "pressure": 1015
    }
    // ... 39 more intervals
  ],
  "timezone": 28800
}
```

**Use Cases**:
- Multi-day trip planning
- Activity scheduling across several days
- Packing list recommendations
- Weather-based itinerary adjustments
- Identifying best weather windows

---

### 2. hourly_forecast

Get hourly weather forecast for the next 48 hours.

**MCP Tool**: `hourly_forecast`

**Parameters**:
- `location` (required): City name, coordinates, or location ID
- `units` (optional): Unit system (metric, imperial, standard)

**Returns**:
- 48 hourly data points
- Detailed temperature progression
- Hour-by-hour conditions
- Precipitation probability and volume
- Minute-by-minute precipitation (if available)
- Wind gusts
- UV index
- Dew point

**Example**:
```javascript
// Get hourly forecast for Shanghai
hourly_forecast({
  location: "Shanghai",
  units: "metric"
})
```

**Response Format**:
```json
{
  "location": {
    "name": "Shanghai",
    "coordinates": { "lat": 31.2304, "lon": 121.4737 }
  },
  "hourly": [
    {
      "dt": 1738267200,
      "temperature": 12.5,
      "feels_like": 11.8,
      "weather": {
        "main": "Rain",
        "description": "light rain"
      },
      "pop": 0.65,
      "rain": { "1h": 0.8 },
      "wind": { "speed": 4.2, "deg": 90, "gust": 6.5 },
      "humidity": 85,
      "uvi": 2.5,
      "clouds": 90,
      "visibility": 8000
    }
    // ... 47 more hours
  ]
}
```

**Use Cases**:
- Precise timing for outdoor activities
- Hourly itinerary optimization
- Rain avoidance scheduling
- Temperature-sensitive planning
- Same-day and next-day detailed planning

---

## Best Practices

### 1. Forecast Selection

**Use 5-day forecast when**:
- Planning multi-day trips
- Checking overall weather patterns
- Identifying best travel days
- Making general packing decisions

**Use hourly forecast when**:
- Optimizing daily schedules
- Avoiding specific rain periods
- Planning outdoor activities (hikes, tours)
- Timing photography sessions
- Scheduling transport during clear weather

### 2. Data Aggregation

**Daily summary from 5-day forecast**:
```javascript
function getDailySummary(forecastData) {
  const dailySummaries = {};

  forecastData.forecast.forEach(interval => {
    const date = interval.dt_txt.split(' ')[0];

    if (!dailySummaries[date]) {
      dailySummaries[date] = {
        temps: [],
        conditions: [],
        precip_prob: 0,
        wind_speeds: []
      };
    }

    dailySummaries[date].temps.push(interval.temperature.current);
    dailySummaries[date].conditions.push(interval.weather.main);
    dailySummaries[date].precip_prob = Math.max(
      dailySummaries[date].precip_prob,
      interval.pop
    );
    dailySummaries[date].wind_speeds.push(interval.wind.speed);
  });

  // Calculate daily min/max/avg
  return Object.entries(dailySummaries).map(([date, data]) => ({
    date,
    temp_min: Math.min(...data.temps),
    temp_max: Math.max(...data.temps),
    temp_avg: data.temps.reduce((a, b) => a + b) / data.temps.length,
    dominant_condition: getMostFrequent(data.conditions),
    rain_probability: data.precip_prob,
    wind_avg: data.wind_speeds.reduce((a, b) => a + b) / data.wind_speeds.length
  }));
}
```

**Find best weather windows**:
```javascript
function findBestWeatherWindows(hourlyData, durationHours = 4) {
  const windows = [];

  for (let i = 0; i < hourlyData.hourly.length - durationHours; i++) {
    const window = hourlyData.hourly.slice(i, i + durationHours);

    const avgTemp = window.reduce((sum, h) => sum + h.temperature, 0) / durationHours;
    const maxRainProb = Math.max(...window.map(h => h.pop));
    const hasRain = window.some(h => h.weather.main === 'Rain');

    const score = calculateWeatherScore(avgTemp, maxRainProb, hasRain);

    windows.push({
      start_time: window[0].dt,
      end_time: window[durationHours - 1].dt,
      avg_temp: avgTemp,
      rain_probability: maxRainProb,
      score
    });
  }

  return windows.sort((a, b) => b.score - a.score);
}

function calculateWeatherScore(temp, rainProb, hasRain) {
  let score = 100;

  // Ideal temperature: 18-25°C
  if (temp < 10 || temp > 30) score -= 30;
  else if (temp < 15 || temp > 28) score -= 15;

  // Penalize rain
  score -= rainProb * 50;
  if (hasRain) score -= 20;

  return Math.max(0, score);
}
```

### 3. Precipitation Handling

**Interpret precipitation probability**:
```javascript
function interpretPrecipitation(pop) {
  if (pop < 0.3) return {
    category: "low",
    recommendation: "Rain unlikely, no special preparation needed"
  };
  if (pop < 0.6) return {
    category: "moderate",
    recommendation: "Rain possible, bring umbrella as backup"
  };
  return {
    category: "high",
    recommendation: "Rain likely, plan indoor activities or bring rain gear"
  };
}
```

**Rain volume assessment**:
```javascript
function assessRainVolume(rainMm) {
  if (rainMm < 0.5) return "Light drizzle";
  if (rainMm < 2) return "Light rain";
  if (rainMm < 10) return "Moderate rain";
  if (rainMm < 50) return "Heavy rain";
  return "Very heavy rain - avoid outdoor activities";
}
```

### 4. Temperature Trends

**Identify temperature patterns**:
```javascript
function analyzeTemperatureTrend(dailySummaries) {
  const trends = [];

  for (let i = 1; i < dailySummaries.length; i++) {
    const prevAvg = dailySummaries[i - 1].temp_avg;
    const currAvg = dailySummaries[i].temp_avg;
    const change = currAvg - prevAvg;

    if (Math.abs(change) < 2) {
      trends.push("stable");
    } else if (change > 0) {
      trends.push("warming");
    } else {
      trends.push("cooling");
    }
  }

  return {
    overall_trend: getMostFrequent(trends),
    max_change: Math.max(...dailySummaries.map((d, i) =>
      i > 0 ? Math.abs(d.temp_avg - dailySummaries[i-1].temp_avg) : 0
    ))
  };
}
```

### 5. Multi-Location Comparison

**Compare weather across destinations**:
```javascript
async function compareDestinationWeather(locations, startDate, endDate) {
  const forecasts = await Promise.all(
    locations.map(loc => forecast_5day({ location: loc, units: "metric" }))
  );

  return forecasts.map((forecast, idx) => {
    const dailySummary = getDailySummary(forecast);

    return {
      location: locations[idx],
      avg_temp: dailySummary.reduce((sum, d) => sum + d.temp_avg, 0) / dailySummary.length,
      rain_days: dailySummary.filter(d => d.rain_probability > 0.5).length,
      best_day: dailySummary.reduce((best, d) =>
        d.rain_probability < best.rain_probability ? d : best
      ),
      recommendation: generateRecommendation(dailySummary)
    };
  });
}
```

### 6. Error Handling

**Retry with exponential backoff**:
```javascript
async function getForecastWithRetry(location, type = "5day", maxRetries = 3) {
  const toolMap = {
    "5day": forecast_5day,
    "hourly": hourly_forecast
  };

  const tool = toolMap[type];

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await tool({ location, units: "metric" });
    } catch (error) {
      if (error.status === 429 || error.status >= 500) {
        await sleep(Math.pow(2, i) * 1000);
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Integration with Travel Planning Agents

### Timeline Agent

**Use forecast to optimize daily schedules**:

**Example workflow**:
```
1. User requests 5-day itinerary for Chengdu
2. Invoke /openweathermap forecast (loads this file)
3. Call forecast_5day({ location: "Chengdu", units: "metric" })
4. Analyze daily summaries:
   - Day 1: Clear, 20°C (excellent)
   - Day 2: Rain 70%, 15°C (indoor activities)
   - Day 3: Clouds, 18°C (good)
   - Day 4: Rain 40%, 16°C (flexible)
   - Day 5: Clear, 22°C (excellent)
5. Schedule outdoor attractions on Days 1, 3, 5
6. Schedule museums/shopping on Day 2
7. Keep Day 4 flexible with indoor backup plans
8. Include weather notes in timeline output
```

### Attractions Agent

**Use forecast to select appropriate attractions**:
```javascript
function selectAttractions(attractions, weatherForecast, day) {
  const dayWeather = weatherForecast.find(d => d.day === day);

  if (dayWeather.rain_probability > 0.6) {
    // Prioritize indoor attractions
    return attractions.filter(a => a.type === "museum" || a.indoor);
  }

  if (dayWeather.temp_max > 30) {
    // Avoid outdoor midday, suggest morning/evening
    return attractions.filter(a =>
      a.indoor || a.has_shade || a.type === "park_morning"
    );
  }

  // Good weather - all options available
  return attractions;
}
```

### Shopping Agent

**Use forecast for packing recommendations**:
```javascript
function generatePackingList(weatherForecast) {
  const items = [];

  const temps = weatherForecast.map(d => d.temp_avg);
  const minTemp = Math.min(...temps);
  const maxTemp = Math.max(...temps);
  const rainDays = weatherForecast.filter(d => d.rain_probability > 0.5).length;

  if (minTemp < 15) items.push("Warm jacket or coat");
  if (maxTemp > 25) items.push("Light breathable clothing");
  if (rainDays >= 2) items.push("Umbrella and waterproof jacket");
  if (maxTemp > 28) items.push("Sun hat and sunscreen");

  return items;
}
```

### Transportation Agent

**Use forecast for transport mode selection**:
```javascript
function selectTransportMode(weather, options) {
  // Heavy rain or storms - prefer train over flight
  if (weather.conditions.includes("Thunderstorm") || weather.rain_probability > 0.8) {
    return options.filter(opt => opt.mode === "train" || opt.mode === "bus");
  }

  // Clear weather - all options viable
  return options;
}
```

## Quality Standards

- Always fetch forecast at start of planning process
- Cache forecast data (valid for 1-3 hours)
- Aggregate hourly data into daily summaries for overview
- Use hourly data for precise timing decisions
- Include weather-based notes in all agent outputs
- Clearly communicate precipitation probability (not just yes/no)
- Account for temperature feels-like, not just actual
- Consider wind speed for outdoor activities
- Document forecast source and timestamp
- Handle missing data gracefully (use fallback values)
- Validate forecast dates match trip dates
- Warn users about extreme weather conditions
