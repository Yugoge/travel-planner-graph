# OpenWeatherMap - Air Quality Tools

Air quality index and pollutant concentration data for health-conscious travel planning.

## Available Tools

### 1. air_quality

Get current air quality index (AQI) and pollutant concentrations.

**MCP Tool**: `air_quality`

**Parameters**:
- `location` (required): City name, coordinates, or location ID
  - City name: "Beijing", "Delhi", "Los Angeles"
  - Coordinates: "39.9042,116.4074" (lat,lon)

**Returns**:
- Air Quality Index (AQI) value (1-5 scale)
- AQI category (Good, Fair, Moderate, Poor, Very Poor)
- Pollutant concentrations (μg/m³):
  - CO (Carbon monoxide)
  - NO (Nitric oxide)
  - NO2 (Nitrogen dioxide)
  - O3 (Ozone)
  - SO2 (Sulfur dioxide)
  - PM2.5 (Fine particulate matter)
  - PM10 (Coarse particulate matter)
  - NH3 (Ammonia)
- Timestamp

**Example**:
```javascript
// Get air quality for Beijing
air_quality({
  location: "Beijing,CN"
})
```

**Response Format**:
```json
{
  "location": {
    "name": "Beijing",
    "coordinates": { "lat": 39.9042, "lon": 116.4074 }
  },
  "aqi": {
    "value": 3,
    "category": "Moderate",
    "description": "Acceptable for most, sensitive groups may experience minor issues"
  },
  "components": {
    "co": 230.5,
    "no": 0.2,
    "no2": 15.8,
    "o3": 68.3,
    "so2": 5.1,
    "pm2_5": 35.2,
    "pm10": 50.1,
    "nh3": 2.3
  },
  "timestamp": "2026-01-30T11:00:00Z"
}
```

**AQI Scale**:
- **1 - Good**: Air quality is satisfactory
- **2 - Fair**: Acceptable quality, minor concern for sensitive individuals
- **3 - Moderate**: Sensitive groups may experience health effects
- **4 - Poor**: Everyone may begin to experience health effects
- **5 - Very Poor**: Health warnings of emergency conditions

**Use Cases**:
- Determine outdoor activity safety
- Plan activities for sensitive travelers (children, elderly, asthmatics)
- Recommend protective equipment (masks)
- Adjust itinerary based on air quality
- Select destinations with better air quality

---

## Best Practices

### 1. AQI Interpretation

**Health recommendations by AQI**:
```javascript
function getHealthRecommendation(aqi) {
  const recommendations = {
    1: {
      category: "Good",
      color: "green",
      outdoor_activities: "All outdoor activities safe",
      sensitive_groups: "No restrictions",
      protective_equipment: "None needed"
    },
    2: {
      category: "Fair",
      color: "yellow",
      outdoor_activities: "All outdoor activities acceptable",
      sensitive_groups: "Unusually sensitive individuals should limit prolonged outdoor exertion",
      protective_equipment: "Optional for sensitive individuals"
    },
    3: {
      category: "Moderate",
      color: "orange",
      outdoor_activities: "Reduce prolonged or heavy outdoor exertion",
      sensitive_groups: "Limit prolonged outdoor activities",
      protective_equipment: "Recommended for sensitive groups (N95 masks)"
    },
    4: {
      category: "Poor",
      color: "red",
      outdoor_activities: "Avoid prolonged outdoor exertion",
      sensitive_groups: "Avoid outdoor activities",
      protective_equipment: "Highly recommended for everyone (N95 masks)"
    },
    5: {
      category: "Very Poor",
      color: "purple",
      outdoor_activities: "Avoid all outdoor activities",
      sensitive_groups: "Remain indoors with air filtration",
      protective_equipment: "Essential for any outdoor exposure (N95/N99 masks)"
    }
  };

  return recommendations[aqi] || recommendations[3];
}
```

### 2. Pollutant-Specific Analysis

**PM2.5 concentration assessment** (most critical for health):
```javascript
function assessPM25(pm25) {
  // Concentration in μg/m³
  if (pm25 <= 12) return {
    level: "Good",
    aqi_equivalent: 1,
    recommendation: "Air quality excellent for outdoor activities"
  };
  if (pm25 <= 35.4) return {
    level: "Moderate",
    aqi_equivalent: 2,
    recommendation: "Acceptable air quality, sensitive groups use caution"
  };
  if (pm25 <= 55.4) return {
    level: "Unhealthy for Sensitive Groups",
    aqi_equivalent: 3,
    recommendation: "Limit prolonged outdoor exertion for sensitive groups"
  };
  if (pm25 <= 150.4) return {
    level: "Unhealthy",
    aqi_equivalent: 4,
    recommendation: "Everyone should reduce outdoor exertion"
  };
  return {
    level: "Very Unhealthy",
    aqi_equivalent: 5,
    recommendation: "Avoid all outdoor activities, stay indoors"
  };
}
```

**Ozone (O3) assessment**:
```javascript
function assessOzone(o3) {
  // Concentration in μg/m³
  if (o3 <= 54) return "Good - Safe for all activities";
  if (o3 <= 70) return "Moderate - Sensitive groups limit outdoor time";
  if (o3 <= 85) return "Unhealthy for sensitive groups";
  if (o3 <= 105) return "Unhealthy - Reduce outdoor exertion";
  return "Very Unhealthy - Avoid outdoor activities";
}
```

### 3. Activity Recommendations

**Adjust activities based on AQI**:
```javascript
function adjustActivitiesForAQI(activities, aqi) {
  const adjustedActivities = [];

  activities.forEach(activity => {
    if (activity.outdoor) {
      if (aqi <= 2) {
        // Good/Fair - all outdoor activities OK
        adjustedActivities.push(activity);
      } else if (aqi === 3) {
        // Moderate - reduce strenuous outdoor activities
        if (activity.intensity === "light") {
          adjustedActivities.push({
            ...activity,
            note: "Limit duration, sensitive groups use caution"
          });
        } else {
          // Suggest indoor alternative
          adjustedActivities.push({
            ...activity,
            alternative: getIndoorAlternative(activity),
            note: "Consider indoor alternative due to moderate air quality"
          });
        }
      } else {
        // Poor/Very Poor - strongly prefer indoor
        adjustedActivities.push({
          ...activity,
          alternative: getIndoorAlternative(activity),
          note: "Indoor alternative recommended due to poor air quality"
        });
      }
    } else {
      // Indoor activities - always OK
      adjustedActivities.push(activity);
    }
  });

  return adjustedActivities;
}
```

### 4. Protective Equipment Recommendations

**Mask recommendations**:
```javascript
function getMaskRecommendation(aqi, pm25) {
  if (aqi <= 2 && pm25 <= 35) {
    return {
      required: false,
      type: "None needed",
      note: "Air quality is acceptable"
    };
  }

  if (aqi === 3 || (pm25 > 35 && pm25 <= 55)) {
    return {
      required: false,
      type: "N95 mask (optional for sensitive groups)",
      note: "Recommended for children, elderly, or individuals with respiratory conditions"
    };
  }

  if (aqi >= 4 || pm25 > 55) {
    return {
      required: true,
      type: "N95 or N99 mask",
      note: "Essential for outdoor activities. Ensure proper fit."
    };
  }
}
```

### 5. Multi-Day Air Quality Tracking

**Track air quality trends** (if historical data available):
```javascript
async function trackAirQualityTrend(location, days = 5) {
  const readings = [];

  for (let i = 0; i < days; i++) {
    try {
      const aq = await air_quality({ location });
      readings.push({
        day: i + 1,
        aqi: aq.aqi.value,
        pm25: aq.components.pm2_5,
        timestamp: aq.timestamp
      });
      await sleep(1000); // Rate limiting
    } catch (error) {
      console.warn(`Failed to get air quality for day ${i + 1}`);
    }
  }

  const avgAQI = readings.reduce((sum, r) => sum + r.aqi, 0) / readings.length;
  const trend = readings.length > 1
    ? (readings[readings.length - 1].aqi > readings[0].aqi ? "worsening" : "improving")
    : "stable";

  return {
    readings,
    average_aqi: avgAQI,
    trend,
    recommendation: avgAQI > 3
      ? "Consider destinations with better air quality"
      : "Air quality acceptable for visit"
  };
}
```

### 6. Error Handling

**Retry logic for air quality API**:
```javascript
async function getAirQualityWithRetry(location, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await air_quality({ location });
    } catch (error) {
      if (error.status === 429 || error.status >= 500) {
        await sleep(Math.pow(2, i) * 1000);
        continue;
      }
      if (error.status === 404) {
        throw new Error(`Air quality data not available for location: ${location}`);
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Fallback to WebSearch**:
```javascript
try {
  const aq = await air_quality({ location });
  return formatAirQualityData(aq);
} catch (error) {
  console.warn('OpenWeatherMap air quality unavailable, falling back to WebSearch');
  return await webSearchAirQuality(location);
}
```

## Integration with Travel Planning Agents

### Attractions Agent

**Adjust attraction recommendations based on air quality**:

**Example workflow**:
```
1. User requests attractions for Beijing
2. Invoke /openweathermap air-quality (loads this file)
3. Call air_quality({ location: "Beijing,CN" })
4. Check AQI: 4 (Poor)
5. Check PM2.5: 85 μg/m³ (Unhealthy)
6. Prioritize indoor attractions:
   - Museums (Forbidden City indoor sections)
   - Shopping malls
   - Indoor markets
   - Cultural performances (theaters)
7. Include outdoor alternatives only with health warning
8. Add mask recommendation to shopping list
9. Save AQI data and recommendations to output
```

### Timeline Agent

**Schedule activities based on air quality patterns**:
```javascript
function scheduleActivitiesWithAirQuality(activities, airQuality) {
  // Early morning often has better air quality
  const outdoorActivities = activities.filter(a => a.outdoor);
  const indoorActivities = activities.filter(a => !a.outdoor);

  if (airQuality.aqi.value >= 3) {
    return [
      ...indoorActivities,
      ...outdoorActivities.map(a => ({
        ...a,
        scheduled_time: "early_morning",
        note: "Scheduled early when air quality typically better",
        duration: "reduced"
      }))
    ];
  }

  return activities;
}
```

### Shopping Agent

**Add protective equipment to shopping list**:
```javascript
function addAirQualityItems(shoppingList, airQuality) {
  if (airQuality.aqi.value >= 3) {
    shoppingList.push({
      item: "N95 or KN95 masks",
      quantity: "Pack of 10-20",
      reason: `Air quality moderate to poor (AQI ${airQuality.aqi.value})`,
      priority: "high"
    });
  }

  if (airQuality.aqi.value >= 4) {
    shoppingList.push({
      item: "Portable air purifier (optional)",
      reason: "Poor air quality for extended stay",
      priority: "medium"
    });
  }

  return shoppingList;
}
```

### Meals Agent

**Prefer enclosed/indoor dining**:
```javascript
function selectDiningVenues(restaurants, airQuality) {
  if (airQuality.aqi.value >= 3) {
    return restaurants.filter(r => r.indoor || r.enclosed_terrace).map(r => ({
      ...r,
      note: "Indoor dining recommended due to air quality"
    }));
  }

  return restaurants;
}
```

## Quality Standards

- Always check air quality for destinations with known pollution issues
- Include AQI value and category in all relevant outputs
- Provide clear health recommendations for different AQI levels
- Document protective equipment needs in shopping lists
- Prioritize indoor activities when AQI > 3
- Cache air quality data (valid for 1 hour)
- Handle missing air quality data gracefully
- Include timestamp of air quality reading
- Warn users about extreme air quality conditions (AQI 4-5)
- Consider sensitive groups (children, elderly, asthmatics) in recommendations
- Document air quality source and measurement time
