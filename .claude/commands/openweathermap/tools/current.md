# OpenWeatherMap - Current Weather Tools

Real-time weather conditions for any location worldwide.

## Available Tools

### 1. current_weather

Get current weather conditions including temperature, humidity, wind, and more.

**MCP Tool**: `current_weather`

**Parameters**:
- `location` (required): City name, coordinates, or location ID
  - City name: "London", "Tokyo", "New York"
  - Coordinates: "51.5074,-0.1278" (lat,lon)
  - Location ID: "2643743" (London)
- `units` (optional): Unit system
  - `metric`: Celsius, m/s (default)
  - `imperial`: Fahrenheit, mph
  - `standard`: Kelvin, m/s

**Returns**:
- Temperature (current, feels like, min, max)
- Weather condition (clear, clouds, rain, snow, etc.)
- Weather description (light rain, broken clouds, etc.)
- Humidity percentage
- Atmospheric pressure (hPa)
- Wind speed and direction
- Visibility (meters)
- Cloud cover percentage
- Sunrise and sunset times (UTC)
- Timezone offset (seconds)
- Location coordinates

**Example**:
```javascript
// Get current weather for Chongqing in metric units
current_weather({
  location: "Chongqing",
  units: "metric"
})
```

**Response Format**:
```json
{
  "location": {
    "name": "Chongqing",
    "country": "CN",
    "coordinates": {
      "lat": 29.5637,
      "lon": 106.5504
    }
  },
  "weather": {
    "main": "Clouds",
    "description": "broken clouds",
    "icon": "04d"
  },
  "temperature": {
    "current": 18.5,
    "feels_like": 17.8,
    "min": 16.2,
    "max": 20.1
  },
  "humidity": 65,
  "pressure": 1013,
  "wind": {
    "speed": 3.5,
    "deg": 120,
    "gust": 5.2
  },
  "visibility": 10000,
  "clouds": 75,
  "sunrise": "2026-01-30T23:45:00Z",
  "sunset": "2026-01-30T10:15:00Z",
  "timezone": 28800
}
```

**Use Cases**:
- Check current conditions before outdoor activities
- Determine appropriate clothing recommendations
- Assess visibility for scenic viewpoints
- Plan immediate travel decisions
- Validate forecast accuracy

---

## Best Practices

### 1. Location Input

**Preferred formats**:
```javascript
// City name (simplest)
current_weather({ location: "Paris" })

// City with country code (more accurate)
current_weather({ location: "Paris,FR" })

// Coordinates (most precise)
current_weather({ location: "48.8566,2.3522" })
```

**For ambiguous city names**, use country codes:
- "Portland,US" vs "Portland,AU"
- "London,UK" vs "London,CA"

### 2. Unit Selection

**Match destination conventions**:
```javascript
// USA destinations
current_weather({ location: "New York", units: "imperial" })

// International destinations
current_weather({ location: "Tokyo", units: "metric" })
```

**For travel planning**, use metric (more universal).

### 3. Error Handling

**Retry logic**:
```javascript
async function getCurrentWeatherWithRetry(location, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await current_weather({ location, units: "metric" });
    } catch (error) {
      if (error.status === 429) {
        // Rate limit - wait and retry
        await sleep(2000 * (i + 1));
        continue;
      }
      if (error.status >= 500) {
        // Server error - retry
        await sleep(1000 * (i + 1));
        continue;
      }
      if (error.status === 404) {
        // Location not found - don't retry
        throw new Error(`Location not found: ${location}`);
      }
      // Other permanent errors
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Fallback to WebSearch**:
```javascript
try {
  const weather = await current_weather({ location });
  return formatWeatherData(weather);
} catch (error) {
  console.warn('OpenWeatherMap unavailable, falling back to WebSearch');
  return await webSearchWeather(location);
}
```

### 4. Response Parsing

**Temperature interpretation**:
```javascript
function interpretTemperature(temp) {
  if (temp < 0) return { category: "freezing", recommendation: "Heavy winter clothing" };
  if (temp < 10) return { category: "cold", recommendation: "Warm jacket and layers" };
  if (temp < 20) return { category: "mild", recommendation: "Light jacket or sweater" };
  if (temp < 30) return { category: "warm", recommendation: "Light clothing" };
  return { category: "hot", recommendation: "Minimal clothing, sun protection" };
}
```

**Weather condition mapping**:
```javascript
function getActivityRecommendation(weatherMain) {
  const recommendations = {
    "Clear": "Excellent for outdoor activities",
    "Clouds": "Good for most activities",
    "Rain": "Indoor activities or covered venues recommended",
    "Drizzle": "Light rain gear sufficient",
    "Thunderstorm": "Indoor activities only",
    "Snow": "Winter activities or indoor alternatives",
    "Mist": "Reduced visibility, indoor activities safer",
    "Fog": "Reduced visibility, avoid scenic viewpoints"
  };
  return recommendations[weatherMain] || "Check detailed forecast";
}
```

**Wind assessment**:
```javascript
function assessWind(windSpeed) {
  // Speed in m/s (metric)
  if (windSpeed < 2) return "Calm";
  if (windSpeed < 6) return "Light breeze";
  if (windSpeed < 12) return "Moderate wind";
  if (windSpeed < 18) return "Strong wind - outdoor activities affected";
  return "Very strong wind - avoid outdoor activities";
}
```

### 5. Time Conversion

**Convert UTC to local time**:
```javascript
function convertToLocalTime(utcTimestamp, timezoneOffset) {
  // utcTimestamp in seconds, timezoneOffset in seconds
  const localTime = new Date((utcTimestamp + timezoneOffset) * 1000);
  return localTime.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
}

// Usage
const sunriseLocal = convertToLocalTime(
  weatherData.sunrise,
  weatherData.timezone
);
```

### 6. Visibility Assessment

**For scenic attractions**:
```javascript
function assessVisibility(visibilityMeters) {
  if (visibilityMeters >= 10000) return "Excellent - ideal for scenic views";
  if (visibilityMeters >= 5000) return "Good - most views clear";
  if (visibilityMeters >= 2000) return "Moderate - some haze";
  if (visibilityMeters >= 1000) return "Poor - limited scenic value";
  return "Very poor - avoid scenic attractions";
}
```

## Integration with Travel Planning Agents

### Attractions Agent

**Use current weather to**:
1. Decide between indoor and outdoor attractions
2. Assess visibility for scenic viewpoints
3. Recommend timing for outdoor activities
4. Suggest weather-appropriate alternatives

**Example workflow**:
```
1. User requests attractions for today in Chongqing
2. Invoke /openweathermap current (loads this file)
3. Call current_weather({ location: "Chongqing", units: "metric" })
4. Check temperature: 18°C (mild)
5. Check weather: Clouds (good for most activities)
6. Check visibility: 10000m (excellent)
7. Recommend: Mix of indoor and outdoor attractions
8. Include note: "Weather is favorable for outdoor sightseeing"
```

### Timeline Agent

**Use current weather to**:
1. Optimize activity scheduling
2. Suggest indoor activities during bad weather
3. Prioritize outdoor activities during good weather
4. Account for sunrise/sunset times

### Shopping Agent

**Use current weather to**:
1. Recommend weather-appropriate clothing
2. Suggest umbrella/raincoat if needed
3. Include sun protection for hot weather
4. Add cold-weather gear for low temperatures

### Entertainment Agent

**Use current weather to**:
1. Suggest indoor venues during rain
2. Recommend outdoor events in good weather
3. Account for weather in evening plans

## Quality Standards

- Always specify units for consistency (prefer metric)
- Convert times to local timezone for user-friendly output
- Include weather-based recommendations in agent output
- Document data source: indicate if from OpenWeatherMap or WebSearch
- Handle location not found errors gracefully
- Cache results to minimize API calls (5-10 minute cache acceptable)
- Validate temperature ranges (sanity check: -50°C to 60°C)
- Check for extreme conditions and issue warnings
