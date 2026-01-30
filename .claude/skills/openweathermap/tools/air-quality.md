# OpenWeatherMap - Air Quality

Get air quality data for health-conscious travel planning.

## MCP Tools

### Tool 1: air_quality

**MCP Tool Name**: `mcp__plugin_openweathermap_openweathermap__air_quality`

**Parameters**:
- `location` (required): City name or coordinates
  - Format: "City, Country Code" (e.g., "Beijing, CN")
  - Format: "lat,lon" (e.g., "39.9042,116.4074")
- `forecast` (optional): Get forecast instead of current (boolean, default: false)

**Returns**:
- `coord`: Location coordinates
  - `lat`: Latitude
  - `lon`: Longitude
- `list`: Array of air quality entries
  - `dt`: Data timestamp (UTC)
  - `main`: Air Quality Index data
    - `aqi`: Air Quality Index (1-5)
      - 1: Good
      - 2: Fair
      - 3: Moderate
      - 4: Poor
      - 5: Very Poor
  - `components`: Pollutant concentrations (μg/m³)
    - `co`: Carbon monoxide
    - `no`: Nitrogen monoxide
    - `no2`: Nitrogen dioxide
    - `o3`: Ozone
    - `so2`: Sulphur dioxide
    - `pm2_5`: Fine particles (PM2.5)
    - `pm10`: Coarse particles (PM10)
    - `nh3`: Ammonia

**Example**:
```javascript
// Get current air quality for Delhi
mcp__plugin_openweathermap_openweathermap__air_quality({
  location: "Delhi, IN",
  forecast: false
})

// Response example:
{
  "coord": {"lat": 28.6139, "lon": 77.209},
  "list": [
    {
      "dt": 1706624400,
      "main": {"aqi": 4},
      "components": {
        "co": 1140.5,
        "no": 12.3,
        "no2": 68.4,
        "o3": 45.2,
        "so2": 22.1,
        "pm2_5": 125.8,
        "pm10": 185.3,
        "nh3": 8.9
      }
    }
  ]
}
```

**Use Cases**:
- Alert travelers with respiratory conditions
- Recommend indoor vs outdoor activities
- Suggest mask usage in high-pollution areas
- Plan outdoor exercise timing
- Advise vulnerable groups (children, elderly)
- Choose accommodation location based on air quality

## Air Quality Index (AQI) Interpretation

### AQI Level 1: Good (0-50 equivalent)
**Health Impact**: Air quality is satisfactory
**Recommendations**:
- All outdoor activities safe
- No precautions needed
- Excellent for sightseeing, hiking, outdoor dining
- Safe for all population groups

### AQI Level 2: Fair (51-100 equivalent)
**Health Impact**: Acceptable for most people
**Recommendations**:
- Normal outdoor activities OK
- Sensitive individuals may experience minor irritation
- Good for most activities
- Monitor if you have respiratory conditions

### AQI Level 3: Moderate (101-150 equivalent)
**Health Impact**: May affect sensitive groups
**Recommendations**:
- Reduce prolonged outdoor exertion
- Sensitive groups should limit outdoor activities
- Consider indoor alternatives for strenuous activities
- Children and elderly should take breaks indoors
- Still OK for sightseeing but limit exercise

### AQI Level 4: Poor (151-200 equivalent)
**Health Impact**: Everyone may experience effects
**Recommendations**:
- Avoid prolonged outdoor activities
- Sensitive groups should stay indoors
- Wear N95 mask if outdoor activity necessary
- Prefer indoor attractions (museums, shopping)
- Reschedule outdoor hiking/sports
- Close windows in accommodation

### AQI Level 5: Very Poor (201+ equivalent)
**Health Impact**: Serious health effects for all
**Recommendations**:
- Stay indoors as much as possible
- Wear N95/FFP2 mask outdoors
- Avoid all strenuous activities
- Keep windows closed
- Use air purifiers indoors
- Consider rescheduling outdoor activities
- Focus on indoor entertainment, shopping, museums

## Pollutant-Specific Guidance

### PM2.5 (Fine Particles)
**Concern Levels**:
- < 12 μg/m³: Good
- 12-35 μg/m³: Moderate
- 35-55 μg/m³: Unhealthy for sensitive groups
- 55-150 μg/m³: Unhealthy
- > 150 μg/m³: Very unhealthy

**Health Impact**: Respiratory and cardiovascular issues
**Sources**: Vehicle emissions, industrial pollution, dust

### PM10 (Coarse Particles)
**Concern Levels**:
- < 54 μg/m³: Good
- 54-154 μg/m³: Moderate
- 154-254 μg/m³: Unhealthy for sensitive groups
- > 254 μg/m³: Unhealthy

**Health Impact**: Respiratory irritation
**Sources**: Dust, construction, industrial activities

### O3 (Ozone)
**Concern Levels**:
- < 100 μg/m³: Good
- 100-160 μg/m³: Moderate
- > 160 μg/m³: Unhealthy

**Health Impact**: Respiratory irritation, reduced lung function
**Peak Times**: Afternoon (12:00-17:00) on sunny days
**Recommendation**: Avoid outdoor exercise during peak ozone hours

### NO2 (Nitrogen Dioxide)
**Concern Levels**:
- < 40 μg/m³: Good
- 40-100 μg/m³: Moderate
- > 100 μg/m³: Unhealthy

**Health Impact**: Respiratory inflammation
**Sources**: Traffic, especially diesel vehicles
**Recommendation**: Avoid high-traffic areas, especially during rush hours

## Best Practices

### 1. Daily Air Quality Check

```markdown
For each destination city:
1. Get current air quality
2. If AQI > 3:
   - Warn in itinerary notes
   - Recommend mask purchase
   - Suggest indoor activity alternatives
3. If AQI = 5:
   - Strongly recommend indoor activities
   - Provide air purifier recommendations
   - Suggest accommodation with good ventilation
```

### 2. Activity Planning

**High AQI (4-5)**:
```markdown
Prioritize:
- Indoor museums and galleries
- Shopping malls
- Indoor entertainment
- Restaurants with good ventilation
- Short outdoor transits only

Avoid:
- Parks and outdoor hiking
- Outdoor sports
- Long walking tours
- Outdoor markets
- Beach activities
```

**Moderate AQI (2-3)**:
```markdown
OK with precautions:
- Sightseeing with frequent breaks
- Light walking tours
- Outdoor dining in evening
- Parks during low-traffic hours

Reduce:
- Strenuous hiking
- Outdoor exercise
- Prolonged outdoor exposure
```

### 3. Vulnerable Groups

**Extra precautions for**:
- Children under 5
- Adults over 65
- People with asthma or respiratory conditions
- People with heart conditions
- Pregnant women

**Recommendations**:
- Lower AQI thresholds (treat AQI 3 as 4)
- Mandatory masks at AQI 3+
- Indoor activities preferred
- Consult doctor before travel if AQI consistently high

### 4. Seasonal Considerations

**High Pollution Seasons**:
- Delhi: October-January (crop burning, winter inversions)
- Beijing: December-February (heating season)
- Los Angeles: July-September (summer smog)

**Recommendations**:
- Check historical AQI before booking
- Consider alternative destinations during high-pollution seasons
- Book accommodation with air filtration

### 5. Mask Recommendations

**AQI 3 (Moderate)**:
- Optional for sensitive individuals
- N95 or KN95 for prolonged outdoor exposure

**AQI 4 (Poor)**:
- Recommended for everyone during outdoor activities
- N95, KN95, or FFP2 masks
- Ensure proper fit

**AQI 5 (Very Poor)**:
- Mandatory for all outdoor exposure
- N95, KN95, or FFP2 masks required
- Consider goggles for severe pollution

## Integration with Planning

### Transportation

```markdown
If air quality poor at destination:
- Prefer airport/station with indoor climate control
- Book taxi/private transfer over public transit
- Minimize outdoor waiting time
- Choose accommodation near attractions (reduce transit)
```

### Accommodation

```markdown
For high-pollution cities:
- Prioritize hotels with:
  - Air purification systems
  - Well-sealed windows
  - Indoor amenities (gym, pool, restaurant)
- Avoid rooms facing busy streets
- Request non-smoking floors
```

### Activities

```markdown
AQI-based activity scheduling:
- Morning: Check daily AQI forecast
- If AQI 4-5: Replace outdoor activities with indoor
- If AQI improving: Schedule outdoor for better hours
- Always have indoor backup plans
```

### Budgeting

```markdown
Air quality impact on budget:
- AQI 4-5 expected: Budget for masks (¥50-100/person)
- Extended poor air: Budget for indoor entertainment
- May need air purifier rental (¥200-500/week)
- Premium accommodation with filtration (+20% cost)
```

## Error Handling

**Location Not Found**:
```markdown
1. Try major city in same region
2. Use coordinates if available
3. Fall back to WebSearch: "air quality [city]"
```

**Data Unavailable**:
```markdown
- Use WebSearch for local AQI data
- Check local environmental agency websites
- Consult AirVisual or IQAir for crowd-sourced data
```

**API Limits**:
```markdown
- Cache air quality data (valid for 1-3 hours)
- Prioritize checking high-pollution cities
- Use forecast mode for trip planning
```

## Data Sources and Reliability

**OpenWeatherMap AQI**:
- Based on European Environment Agency (EEA) standards
- Updated hourly
- Generally reliable for major cities
- May differ from local government indices

**Alternative Sources** (for verification):
- AirVisual/IQAir: Real-time, crowd-sourced
- Local EPA: Official government data
- Embassy air quality monitors: US embassies in China, India
