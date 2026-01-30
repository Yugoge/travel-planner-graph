# Gaode Maps - Utility Tools

Additional utility tools for weather information and distance measurement.

## Available Tools

### 1. weather_info

Get weather forecast for a city.

**MCP Tool**: `weather_info`

**Parameters**:
- `city` (required): City name or city code (e.g., "成都" or "028")
- `extensions` (optional): Forecast type
  - `base`: Live weather (current conditions, default)
  - `all`: Forecast (3-4 days)

**Returns (Live Weather)**:
- Province, city, ad code
- Weather description (e.g., "晴", "多云", "雨")
- Temperature (°C)
- Wind direction and power
- Humidity (%)
- Report time

**Returns (Forecast)**:
- Same as live, plus:
- Daytime weather
- Nighttime weather
- Daytime/nighttime temperature
- Forecast for next 3-4 days

**Example**:
```javascript
// Get current weather
weather_info({
  city: "成都",
  extensions: "base"
})

// Get 4-day forecast
weather_info({
  city: "成都",
  extensions: "all"
})
```

**Use Cases**:
- Display weather in travel plan
- Suggest activities based on weather
- Pack recommendation (umbrella, sunscreen, etc.)
- Clothing suggestions
- Outdoor activity planning

---

### 2. distance_measure

Calculate distance and travel time between multiple points.

**MCP Tool**: `distance_measure`

**Parameters**:
- `origins` (required): Starting point(s) coordinates (e.g., "116.481488,39.990464")
- `destination` (required): Destination coordinates
- `type` (optional): Travel mode
  - `0`: Straight-line distance
  - `1`: Driving distance (default)
  - `3`: Walking distance

**Returns**:
- Origin and destination coordinates
- Distance (meters)
- Duration (seconds) - only for driving/walking modes
- Formatted distance (km or m)
- Formatted duration (hours and minutes)

**Example**:
```javascript
// Calculate driving distance
distance_measure({
  origins: "116.481488,39.990464",  // Beijing
  destination: "121.473701,31.230416",  // Shanghai
  type: 1
})

// Calculate straight-line distance
distance_measure({
  origins: "116.481488,39.990464",
  destination: "121.473701,31.230416",
  type: 0
})
```

**Use Cases**:
- Quick distance estimation
- Feasibility check (walking distance?)
- Compare multiple routes
- Budget time allocation
- Day trip radius calculation

---

## Best Practices

### 1. Weather Integration

**Daily weather in travel plan**:
```javascript
async function getDailyWeather(city, days) {
  const forecast = await weather_info({
    city: city,
    extensions: "all"
  });

  // Extract forecast for specific days
  return forecast.casts.slice(0, days).map(cast => ({
    date: cast.date,
    weather: cast.dayweather,
    temp_high: cast.daytemp,
    temp_low: cast.nighttemp,
    advice: generateWeatherAdvice(cast)
  }));
}
```

**Weather-based recommendations**:
```javascript
function generateWeatherAdvice(weatherData) {
  const weather = weatherData.dayweather;
  const temp = parseInt(weatherData.daytemp);

  const advice = [];

  if (weather.includes('雨')) {
    advice.push('Bring umbrella');
    advice.push('Consider indoor attractions');
  }

  if (weather.includes('晴') && temp > 25) {
    advice.push('Bring sunscreen and hat');
    advice.push('Stay hydrated');
  }

  if (temp < 10) {
    advice.push('Wear warm clothing');
    advice.push('Hot beverages recommended');
  }

  if (weather.includes('雪')) {
    advice.push('Wear warm boots');
    advice.push('Allow extra travel time');
  }

  return advice;
}
```

**Activity suggestions by weather**:
```javascript
function suggestActivitiesByWeather(weather, attractions) {
  const weatherLower = weather.toLowerCase();

  if (weatherLower.includes('雨')) {
    // Rainy day: prioritize indoor attractions
    return attractions.filter(a =>
      a.type.includes('博物馆') ||
      a.type.includes('商场') ||
      a.type.includes('室内')
    );
  }

  if (weatherLower.includes('晴')) {
    // Sunny day: outdoor activities
    return attractions.filter(a =>
      a.type.includes('公园') ||
      a.type.includes('古镇') ||
      a.type.includes('山')
    );
  }

  return attractions;  // All weather
}
```

### 2. Distance Calculation Use Cases

**Validate walking feasibility**:
```javascript
async function isWalkable(origin, destination) {
  const distance = await distance_measure({
    origins: origin,
    destination: destination,
    type: 3  // Walking
  });

  const MAX_WALKING_DISTANCE = 2000;  // 2km
  const MAX_WALKING_TIME = 30 * 60;   // 30 minutes

  return {
    walkable: distance.distance <= MAX_WALKING_DISTANCE &&
              distance.duration <= MAX_WALKING_TIME,
    distance: distance.distance,
    duration: distance.duration,
    formatted: `${(distance.distance / 1000).toFixed(1)}km, ${Math.round(distance.duration / 60)}min`
  };
}
```

**Compare multiple destinations**:
```javascript
async function findNearestDestination(origin, destinations) {
  const distances = await Promise.all(
    destinations.map(async (dest) => {
      const distance = await distance_measure({
        origins: origin,
        destination: dest.coordinates,
        type: 1  // Driving
      });

      return {
        ...dest,
        distance: distance.distance,
        duration: distance.duration
      };
    })
  );

  // Sort by distance
  distances.sort((a, b) => a.distance - b.distance);

  return distances;
}
```

**Day trip radius**:
```javascript
async function filterByDayTripRadius(baseLocation, attractions, maxHours = 2) {
  const withinRadius = [];

  for (const attraction of attractions) {
    const distance = await distance_measure({
      origins: baseLocation,
      destination: attraction.coordinates,
      type: 1  // Driving
    });

    if (distance.duration <= maxHours * 3600) {
      withinRadius.push({
        ...attraction,
        distance: distance.distance,
        duration: distance.duration,
        formatted_duration: formatDuration(distance.duration)
      });
    }
  }

  return withinRadius;
}
```

**Multi-point distance matrix**:
```javascript
async function calculateDistanceMatrix(points) {
  const matrix = [];

  for (let i = 0; i < points.length; i++) {
    const row = [];
    for (let j = 0; j < points.length; j++) {
      if (i === j) {
        row.push({ distance: 0, duration: 0 });
      } else {
        const distance = await distance_measure({
          origins: points[i].coordinates,
          destination: points[j].coordinates,
          type: 1
        });
        row.push({
          distance: distance.distance,
          duration: distance.duration
        });

        // Rate limiting
        await sleep(100);
      }
    }
    matrix.push(row);
  }

  return matrix;
}
```

### 3. Packing Recommendations

**Weather-based packing list**:
```javascript
function generatePackingList(weatherForecasts) {
  const essentials = ['Passport', 'Phone charger', 'Medications'];
  const weatherItems = [];

  const hasRain = weatherForecasts.some(w => w.weather.includes('雨'));
  const hasSun = weatherForecasts.some(w => w.weather.includes('晴'));
  const maxTemp = Math.max(...weatherForecasts.map(w => parseInt(w.temp_high)));
  const minTemp = Math.min(...weatherForecasts.map(w => parseInt(w.temp_low)));

  if (hasRain) {
    weatherItems.push('Umbrella', 'Rain jacket');
  }

  if (hasSun && maxTemp > 25) {
    weatherItems.push('Sunscreen', 'Sunglasses', 'Hat');
  }

  if (minTemp < 10) {
    weatherItems.push('Warm jacket', 'Gloves', 'Scarf');
  }

  if (maxTemp > 30) {
    weatherItems.push('Light clothing', 'Water bottle');
  }

  return {
    essentials,
    weather_specific: weatherItems,
    clothing: suggestClothing(minTemp, maxTemp)
  };
}
```

### 4. Error Handling

**Handle city name variations**:
```javascript
async function safeWeatherInfo(cityInput) {
  try {
    return await weather_info({ city: cityInput });
  } catch (error) {
    if (error.message.includes('invalid city')) {
      // Try normalizing city name
      const normalized = normalizeCityName(cityInput);
      return await weather_info({ city: normalized });
    }
    throw error;
  }
}

function normalizeCityName(city) {
  // Remove "市", "省" suffixes
  return city.replace(/[市省]/g, '');
}
```

**Handle invalid coordinates**:
```javascript
async function safeDistanceMeasure(origins, destination, type) {
  // Validate coordinates format
  const coordsRegex = /^-?\d+\.?\d*,-?\d+\.?\d*$/;

  if (!coordsRegex.test(origins) || !coordsRegex.test(destination)) {
    throw new Error('Invalid coordinates format. Use "lng,lat"');
  }

  try {
    return await distance_measure({ origins, destination, type });
  } catch (error) {
    if (error.message.includes('out of service')) {
      // Coordinates outside China, use straight-line distance
      return await distance_measure({
        origins,
        destination,
        type: 0  // Straight-line
      });
    }
    throw error;
  }
}
```

### 5. Caching

**Cache weather forecasts**:
```javascript
const weatherCache = new Map();

async function getCachedWeather(city) {
  const cacheKey = `weather:${city}:${new Date().toDateString()}`;

  if (weatherCache.has(cacheKey)) {
    return weatherCache.get(cacheKey);
  }

  const weather = await weather_info({ city, extensions: "all" });
  weatherCache.set(cacheKey, weather);

  // Clear cache after 6 hours
  setTimeout(() => weatherCache.delete(cacheKey), 6 * 60 * 60 * 1000);

  return weather;
}
```

**Cache distances**:
```javascript
const distanceCache = new Map();

async function getCachedDistance(origins, destination, type) {
  const cacheKey = `distance:${origins}:${destination}:${type}`;

  if (distanceCache.has(cacheKey)) {
    return distanceCache.get(cacheKey);
  }

  const distance = await distance_measure({ origins, destination, type });
  distanceCache.set(cacheKey, distance);

  return distance;
}
```

---

## Integration with Travel Planning

### Plan Agent Integration

**Add weather section to plan**:
```javascript
async function addWeatherToPlans(destinationSlug, days) {
  const requirements = readJSON(`data/${destinationSlug}/requirements-skeleton.json`);
  const city = requirements.days[0].location;

  const weatherData = await getCachedWeather(city);

  const weatherSection = {
    city: city,
    forecast: weatherData.casts.slice(0, days.length),
    packing_recommendations: generatePackingList(weatherData.casts)
  };

  writeJSON(`data/${destinationSlug}/weather.json`, weatherSection);
}
```

### Timeline Agent Integration

**Adjust timeline based on weather**:
```javascript
async function adjustTimelineForWeather(day, activities, city) {
  const weather = await weather_info({ city, extensions: "all" });
  const dayWeather = weather.casts.find(c => c.date === day.date);

  if (dayWeather.dayweather.includes('雨')) {
    // Move outdoor activities to indoor
    const adjusted = activities.map(activity => {
      if (activity.type === 'outdoor') {
        return {
          ...activity,
          warning: 'Rainy weather - consider rescheduling or bringing umbrella'
        };
      }
      return activity;
    });

    return adjusted;
  }

  return activities;
}
```

### Budget Agent Integration

**Include weather-related expenses**:
```javascript
function calculateWeatherRelatedCosts(weatherForecasts) {
  let additionalCosts = 0;

  const hasRain = weatherForecasts.some(w => w.weather.includes('雨'));
  const hasExtremeHeat = weatherForecasts.some(w => parseInt(w.daytemp) > 35);

  if (hasRain) {
    additionalCosts += 10;  // Umbrella or rain gear
  }

  if (hasExtremeHeat) {
    additionalCosts += 15;  // Sunscreen, extra water
  }

  return {
    amount: additionalCosts,
    items: hasRain ? ['Rain gear'] : [],
    notes: 'Weather-related expenses'
  };
}
```

---

## Example: Complete Weather and Distance Analysis

```javascript
async function analyzeTrip(destinations, accommodations, attractions) {
  const analysis = {
    weather: {},
    distances: {},
    recommendations: []
  };

  // 1. Get weather for all destinations
  for (const dest of destinations) {
    const weather = await getCachedWeather(dest.city);
    analysis.weather[dest.city] = {
      forecast: weather.casts,
      packing: generatePackingList(weather.casts)
    };

    // Add weather-based recommendations
    weather.casts.forEach((cast, index) => {
      if (cast.dayweather.includes('雨')) {
        analysis.recommendations.push({
          day: index + 1,
          city: dest.city,
          type: 'weather',
          message: `Day ${index + 1}: Rainy weather in ${dest.city}. Consider indoor attractions.`
        });
      }
    });
  }

  // 2. Calculate distances between accommodations and attractions
  for (const day of Object.keys(accommodations)) {
    const hotel = accommodations[day];
    const dayAttractions = attractions[day];

    for (const attraction of dayAttractions) {
      const distance = await getCachedDistance(
        hotel.coordinates,
        attraction.coordinates,
        1  // Driving
      );

      const walkDistance = await getCachedDistance(
        hotel.coordinates,
        attraction.coordinates,
        3  // Walking
      );

      const isWalkable = walkDistance.duration <= 30 * 60;  // 30 min

      analysis.distances[`${day}_${attraction.name}`] = {
        driving: formatDistance(distance.distance),
        walking: formatDistance(walkDistance.distance),
        walkable: isWalkable,
        driving_time: formatDuration(distance.duration),
        walking_time: formatDuration(walkDistance.duration)
      };

      if (isWalkable) {
        analysis.recommendations.push({
          day: day,
          type: 'distance',
          message: `${attraction.name} is walkable from hotel (${formatDuration(walkDistance.duration)})`
        });
      }
    }
  }

  return analysis;
}

// Helper functions
function formatDistance(meters) {
  return meters >= 1000
    ? `${(meters / 1000).toFixed(1)} km`
    : `${meters} m`;
}

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
}
```
