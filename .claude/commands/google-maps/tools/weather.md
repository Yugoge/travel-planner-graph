# Google Maps - Weather Lookup Tools

Weather information tools for travel planning using Google Maps Grounding Lite.

## Available Tools

### 1. lookup_weather

Get current weather information for a location.

**MCP Tool**: `lookup_weather`

**Parameters**:
- `location` (required): Location for weather lookup
  - Address string: "Paris, France"
  - Coordinates: { latitude: 48.8566, longitude: 2.3522 }
  - Place ID: Place identifier from Google Maps

**Returns**:
- Temperature (Celsius and Fahrenheit)
- Weather condition (clear, cloudy, rain, snow, etc.)
- Humidity percentage
- Wind speed and direction
- Visibility
- Atmospheric pressure
- UV index
- Sunrise/sunset times
- Location name

**Example**:
```javascript
// Check weather in Paris
lookup_weather({
  location: "Paris, France"
})
```

**Example with coordinates**:
```javascript
// Check weather at specific coordinates
lookup_weather({
  location: {
    latitude: 35.6762,
    longitude: 139.6503
  }
})
```

**Use Cases**:
- Pre-trip weather planning
- Daily activity planning (indoor vs outdoor)
- Packing recommendations
- Best time to visit attractions
- Safety advisories (extreme weather)

---

## Best Practices

### 1. Input Flexibility

Accept multiple location formats:
```javascript
function normalizeWeatherLocation(location) {
  // String address or city name
  if (typeof location === 'string') {
    return location;
  }

  // Coordinates object
  if (location.latitude && location.longitude) {
    return {
      latitude: parseFloat(location.latitude),
      longitude: parseFloat(location.longitude)
    };
  }

  throw new Error('Invalid location format for weather lookup');
}
```

### 2. Temperature Conversion

Convert between Celsius and Fahrenheit:
```javascript
function convertTemperature(celsius) {
  return {
    celsius: celsius,
    fahrenheit: (celsius * 9/5) + 32,
    kelvin: celsius + 273.15
  };
}

function formatTemperature(celsius, unit = 'both') {
  const fahrenheit = (celsius * 9/5) + 32;

  switch (unit) {
    case 'celsius':
      return `${celsius.toFixed(1)}°C`;
    case 'fahrenheit':
      return `${fahrenheit.toFixed(1)}°F`;
    case 'both':
      return `${celsius.toFixed(1)}°C (${fahrenheit.toFixed(1)}°F)`;
    default:
      return `${celsius.toFixed(1)}°C`;
  }
}
```

### 3. Weather-Based Activity Recommendations

Suggest activities based on conditions:
```javascript
function recommendActivityType(weather) {
  const condition = weather.condition.toLowerCase();
  const temp = weather.temperature;

  // Rain or storms: indoor activities
  if (condition.includes('rain') || condition.includes('storm')) {
    return {
      type: 'indoor',
      recommendation: 'Museums, galleries, shopping malls, indoor attractions',
      warning: 'Bring umbrella, avoid outdoor activities'
    };
  }

  // Snow: winter activities or indoor
  if (condition.includes('snow')) {
    return {
      type: 'indoor/winter',
      recommendation: 'Winter sports, indoor attractions, cozy cafes',
      warning: 'Dress warmly, check road conditions'
    };
  }

  // Clear and comfortable: outdoor activities
  if (condition.includes('clear') && temp >= 15 && temp <= 28) {
    return {
      type: 'outdoor',
      recommendation: 'Parks, outdoor attractions, walking tours, photography',
      warning: 'Bring sunscreen and water'
    };
  }

  // Too hot: shade or indoor
  if (temp > 28) {
    return {
      type: 'indoor/shade',
      recommendation: 'Indoor attractions, shaded areas, water activities',
      warning: 'Stay hydrated, avoid midday sun'
    };
  }

  // Too cold: indoor or brief outdoor
  if (temp < 10) {
    return {
      type: 'indoor',
      recommendation: 'Indoor attractions, brief outdoor sightseeing',
      warning: 'Dress warmly in layers'
    };
  }

  // Default
  return {
    type: 'flexible',
    recommendation: 'Mix of indoor and outdoor activities',
    warning: 'Check conditions before each activity'
  };
}
```

### 4. Packing Recommendations

Generate packing suggestions based on weather:
```javascript
function generatePackingList(weather, tripDuration) {
  const items = {
    always: ['Passport', 'Phone charger', 'Medications'],
    clothing: [],
    accessories: [],
    footwear: []
  };

  const condition = weather.condition.toLowerCase();
  const temp = weather.temperature;

  // Temperature-based clothing
  if (temp > 25) {
    items.clothing.push('Light, breathable shirts', 'Shorts', 'Sun hat');
    items.accessories.push('Sunglasses', 'Sunscreen SPF 30+');
  } else if (temp > 15) {
    items.clothing.push('T-shirts', 'Light jacket', 'Long pants');
  } else if (temp > 5) {
    items.clothing.push('Warm layers', 'Jacket', 'Long pants');
    items.accessories.push('Scarf');
  } else {
    items.clothing.push('Heavy coat', 'Thermal layers', 'Warm pants');
    items.accessories.push('Gloves', 'Scarf', 'Warm hat');
  }

  // Weather condition-based items
  if (condition.includes('rain')) {
    items.accessories.push('Umbrella', 'Waterproof jacket', 'Waterproof bag');
    items.footwear.push('Waterproof shoes');
  }

  if (condition.includes('snow')) {
    items.accessories.push('Snow boots', 'Waterproof gloves');
    items.footwear.push('Insulated boots');
  }

  // UV index considerations
  if (weather.uvIndex > 6) {
    items.accessories.push('SPF 50+ sunscreen', 'UV-blocking sunglasses', 'Wide-brim hat');
  }

  return items;
}
```

### 5. Safety Warnings

Generate weather-related safety advisories:
```javascript
function generateWeatherWarnings(weather) {
  const warnings = [];
  const condition = weather.condition.toLowerCase();

  // Extreme temperature
  if (weather.temperature > 35) {
    warnings.push({
      severity: 'high',
      message: 'Extreme heat: Risk of heat exhaustion. Stay hydrated, avoid midday sun.',
      action: 'Schedule outdoor activities for morning/evening only'
    });
  }

  if (weather.temperature < 0) {
    warnings.push({
      severity: 'high',
      message: 'Freezing conditions: Risk of frostbite and hypothermia.',
      action: 'Limit outdoor exposure, dress in multiple warm layers'
    });
  }

  // Severe weather
  if (condition.includes('storm') || condition.includes('thunder')) {
    warnings.push({
      severity: 'high',
      message: 'Thunderstorms: Stay indoors, avoid open areas.',
      action: 'Reschedule outdoor activities, stay away from tall structures'
    });
  }

  // High UV
  if (weather.uvIndex > 8) {
    warnings.push({
      severity: 'medium',
      message: 'Very high UV index: Risk of sunburn within 15 minutes.',
      action: 'Apply sunscreen every 2 hours, wear protective clothing'
    });
  }

  // Poor visibility
  if (weather.visibility < 1000) {
    warnings.push({
      severity: 'medium',
      message: 'Poor visibility: Fog or heavy precipitation.',
      action: 'Exercise caution if driving, allow extra travel time'
    });
  }

  // High wind
  if (weather.windSpeed > 40) {
    warnings.push({
      severity: 'medium',
      message: 'High winds: May affect outdoor activities.',
      action: 'Secure loose items, avoid water activities'
    });
  }

  return warnings;
}
```

### 6. Error Handling

**Retry logic**:
```javascript
async function lookupWeatherWithRetry(location, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await lookup_weather({ location });
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
      // Permanent error - don't retry
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Fallback to WebSearch**:
```javascript
async function getWeatherWithFallback(location) {
  try {
    const weather = await lookup_weather({ location });
    return { source: 'google_maps', data: weather };
  } catch (error) {
    console.warn('Google Maps weather unavailable, falling back to WebSearch');
    const weather = await webSearchWeather(location);
    return { source: 'web_search', data: weather };
  }
}
```

---

## Integration with Travel Planning Agents

### Attractions Agent

Use weather to optimize daily attraction scheduling:
```javascript
async function optimizeAttractionsByWeather(attractions, location, date) {
  // Get weather for the day
  const weather = await lookup_weather({ location });

  // Categorize attractions
  const indoor = attractions.filter(a => a.type === 'museum' || a.type === 'indoor');
  const outdoor = attractions.filter(a => a.type === 'park' || a.type === 'outdoor');

  // Get activity recommendation
  const recommendation = recommendActivityType(weather);

  // Prioritize based on weather
  if (recommendation.type === 'indoor') {
    return {
      morning: indoor[0],
      afternoon: indoor[1],
      backup_outdoor: outdoor[0],
      weather_note: recommendation.warning
    };
  } else if (recommendation.type === 'outdoor') {
    return {
      morning: outdoor[0],
      afternoon: outdoor[1],
      backup_indoor: indoor[0],
      weather_note: recommendation.warning
    };
  }

  // Mix for flexible weather
  return {
    morning: outdoor[0],
    afternoon: indoor[0],
    backup: outdoor[1] || indoor[1],
    weather_note: 'Flexible weather, mix of activities'
  };
}
```

### Timeline Agent

Add weather context to daily plans:
```javascript
async function enrichDayPlanWithWeather(dayPlan, location) {
  const weather = await lookup_weather({ location });
  const warnings = generateWeatherWarnings(weather);

  return {
    ...dayPlan,
    weather: {
      temperature: formatTemperature(weather.temperature),
      condition: weather.condition,
      recommendation: recommendActivityType(weather).recommendation,
      warnings: warnings.map(w => w.message),
      packing_tips: generatePackingList(weather, 1).accessories
    }
  };
}
```

### General Planning Context

Check weather for all destinations upfront:
```javascript
async function getWeatherOverview(cities, dates) {
  const weatherData = [];

  for (const city of cities) {
    const weather = await lookup_weather({ location: city });

    weatherData.push({
      city: city,
      current: {
        temperature: weather.temperature,
        condition: weather.condition
      },
      activity_type: recommendActivityType(weather).type,
      warnings: generateWeatherWarnings(weather)
    });
  }

  return weatherData;
}

// Usage in plan orchestrator
const cities = ["Paris", "Barcelona", "Rome"];
const weatherOverview = await getWeatherOverview(cities);

// Use overview to inform agent planning
agents.forEach(agent => {
  agent.context.weather = weatherOverview;
});
```

---

## Example: Complete Weather-Based Planning

```javascript
async function planDayWithWeather(location, attractions, date) {
  // 1. Get weather
  const weather = await lookup_weather({ location });

  // 2. Generate recommendations
  const activityRec = recommendActivityType(weather);
  const warnings = generateWeatherWarnings(weather);
  const packing = generatePackingList(weather, 1);

  // 3. Filter attractions by suitability
  const suitable = attractions.filter(attraction => {
    // Indoor attractions OK for bad weather
    if (activityRec.type === 'indoor' && attraction.indoor) {
      return true;
    }

    // Outdoor attractions OK for good weather
    if (activityRec.type === 'outdoor' && !attraction.indoor) {
      return true;
    }

    // Flexible weather: all attractions OK
    if (activityRec.type === 'flexible') {
      return true;
    }

    return false;
  });

  // 4. Return weather-optimized plan
  return {
    location: location,
    date: date,
    weather: {
      temperature: formatTemperature(weather.temperature),
      condition: weather.condition,
      humidity: weather.humidity,
      wind: weather.windSpeed,
      uv_index: weather.uvIndex
    },
    recommendations: {
      activity_type: activityRec.type,
      suggestion: activityRec.recommendation,
      warnings: warnings.map(w => w.message)
    },
    suitable_attractions: suitable,
    packing: {
      clothing: packing.clothing,
      accessories: packing.accessories,
      footwear: packing.footwear
    }
  };
}
```

---

## Response Format

**Standard weather response**:
```javascript
{
  location: "Paris, France",
  temperature: 18.5,  // Celsius
  condition: "Partly cloudy",
  humidity: 65,  // percentage
  windSpeed: 12,  // km/h
  windDirection: "NW",
  visibility: 10000,  // meters
  pressure: 1013,  // hPa
  uvIndex: 5,
  sunrise: "06:45",
  sunset: "20:30",
  feelsLike: 17.2  // Celsius
}
```

## Notes

- Weather lookup provides current conditions, not forecasts
- For multi-day forecasts, use specialized weather services (OpenWeatherMap skill)
- Always include weather context in daily plans
- Update packing recommendations based on weather
- Reschedule outdoor activities if severe weather warnings
- Consider seasonal variations when planning trips
- Document data source in agent output
- Fall back to WebSearch if MCP unavailable
