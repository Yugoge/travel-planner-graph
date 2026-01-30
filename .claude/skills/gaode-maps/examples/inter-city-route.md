# Example: Inter-city Route Planning (Beijing to Xi'an)

This example demonstrates using Gaode Maps routing tools to plan transportation between two major Chinese cities.

## Scenario

**User Request**:
"Plan transportation from Beijing to Xi'an for a 3-day trip, budget-conscious but time matters"

**Requirements**:
- Departure: Beijing (hotel near Tiananmen)
- Destination: Xi'an (hotel near Bell Tower)
- Budget: Mid-range
- Time sensitivity: Moderate (prefer not to waste full day traveling)
- Luggage: 2 large suitcases

## Step-by-Step Workflow

### Step 1: Load Routing Tools

```markdown
/gaode-maps routing
```

This loads the routing category with all transportation mode tools.

### Step 2: Research Transit Options

**Public Transportation (Train/Bus)**:

```javascript
mcp__plugin_amap-maps_amap-maps__transit_route({
  origin: "北京",
  destination: "西安",
  cityd: "西安",
  date: "2026-02-15",
  time: "08:00"
})
```

**Response Analysis**:
```json
{
  "status": "1",
  "route": {
    "distance": "1216000",
    "transits": [
      {
        "cost": "515",
        "duration": "16200",
        "segments": [
          {
            "railway": {
              "name": "G87",
              "departure_stop": "北京西站",
              "arrival_stop": "西安北站",
              "departure_time": "08:00",
              "arrival_time": "12:30",
              "type": "高铁",
              "seat_type": "二等座"
            }
          },
          {
            "walking": {
              "origin": "西安北站",
              "destination": "钟楼",
              "distance": "850"
            }
          }
        ]
      },
      {
        "cost": "180",
        "duration": "39600",
        "segments": [
          {
            "railway": {
              "name": "K218",
              "departure_stop": "北京西站",
              "arrival_stop": "西安站",
              "departure_time": "20:15",
              "arrival_time": "07:15+1",
              "type": "普快"
            }
          }
        ]
      }
    ]
  }
}
```

**Option 1: High-speed Rail (G87)**
- Departure: 08:00 from Beijing West Station
- Arrival: 12:30 at Xi'an North Station
- Duration: 4.5 hours
- Cost: ¥515 (second class)
- Pros: Fast, comfortable, daytime travel
- Cons: More expensive than regular train

**Option 2: Regular Train (K218)**
- Departure: 20:15 from Beijing West Station
- Arrival: 07:15+1 (next day) at Xi'an Station
- Duration: 11 hours (overnight)
- Cost: ¥180 (hard sleeper)
- Pros: Budget-friendly, saves hotel night
- Cons: Overnight travel, less comfortable

### Step 3: Research Driving Option

```javascript
mcp__plugin_amap-maps_amap-maps__driving_route({
  origin: "北京天安门",
  destination: "西安钟楼",
  strategy: 0
})
```

**Response Analysis**:
```json
{
  "status": "1",
  "route": {
    "distance": "1085000",
    "duration": "39600",
    "tolls": "485",
    "taxi_cost": "3250",
    "paths": [
      {
        "distance": "1085000",
        "duration": "39600",
        "tolls": "485",
        "steps": [
          {
            "instruction": "从北京出发，沿京港澳高速南行",
            "distance": "650000",
            "duration": "23400"
          },
          {
            "instruction": "转西安绕城高速",
            "distance": "45000",
            "duration": "1800"
          }
        ]
      }
    ]
  }
}
```

**Option 3: Private Car/Taxi**
- Distance: 1,085 km
- Duration: ~11 hours (with breaks)
- Toll fees: ¥485
- Taxi cost estimate: ¥3,250
- Fuel cost: ~¥650 (assuming 8L/100km, ¥7.5/L)
- **Total cost**: ¥4,385 (taxi) or ¥1,135 (own car)
- Pros: Door-to-door, flexible schedule, can stop at attractions en route
- Cons: Expensive (taxi), tiring (driving), long duration

### Step 4: Compare Options

| Mode | Duration | Cost | Comfort | Flexibility | Luggage |
|------|----------|------|---------|-------------|---------|
| High-speed rail | 4.5h | ¥515 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Easy |
| Regular train | 11h (overnight) | ¥180 | ⭐⭐⭐ | ⭐⭐ | ✅ Easy |
| Taxi | 11h | ¥4,385 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Easy |
| Own car | 11h | ¥1,135 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Easy |

### Step 5: Make Recommendation

**Recommended: High-speed Rail (G87)**

**Reasoning**:
1. **Time efficiency**: Arrives at 12:30, allows afternoon activities in Xi'an
2. **Cost-effective**: ¥515 is reasonable for mid-range budget
3. **Comfort**: Spacious seats, can walk around, onboard amenities
4. **Luggage-friendly**: Large storage areas for 2 suitcases
5. **Reliability**: High-speed rail is punctual (>98% on-time rate)

**Alternative: Regular Train (K218)** (if budget is very tight)
- Saves ~¥335 vs high-speed rail
- Saves one night of accommodation (~¥200-300)
- Total savings: ~¥535-635
- Trade-off: Less comfortable, loses half a day in Xi'an

**Not Recommended: Private Car**
- Taxi cost (¥4,385) is 8.5× high-speed rail cost
- Own car requires driver, tiring 11-hour journey
- Only worth it if group of 4+ people splitting cost

### Step 6: Structure Output Data

```json
{
  "from": "Beijing",
  "to": "Xi'an",
  "transportation": "High-speed rail (高铁)",
  "train_number": "G87",
  "departure_station": "Beijing West Station (北京西站)",
  "departure_time": "08:00",
  "arrival_station": "Xi'an North Station (西安北站)",
  "arrival_time": "12:30",
  "duration_minutes": 270,
  "cost": 515,
  "seat_class": "Second class (二等座)",
  "distance_km": 1216,
  "notes": "Book 15-30 days in advance for best prices. Xi'an North Station is far from city center; take subway Line 2 to Bell Tower (钟楼) station, ~45 min, ¥4. Luggage allowance: 20kg per adult ticket.",
  "booking_url": "https://www.12306.cn/",
  "alternatives": [
    {
      "type": "Regular train (overnight)",
      "train_number": "K218",
      "cost": 180,
      "duration_minutes": 660,
      "notes": "Budget option, overnight sleeper, saves hotel night"
    }
  ]
}
```

## Key Takeaways

1. **Progressive Loading**: Only loaded routing tools when needed
2. **Multiple Modes**: Compared train, driving for comprehensive view
3. **Real Data**: Used actual API responses for accurate planning
4. **User Context**: Considered budget, luggage, time preferences
5. **Structured Output**: Formatted data for downstream consumption

## Workflow Pattern (Reusable)

```markdown
1. Load `/gaode-maps routing`
2. Call `transit_route` for public transport options
3. Call `driving_route` for private car comparison
4. Parse responses and extract key data:
   - Duration (convert seconds to hours)
   - Cost (CNY)
   - Comfort factors
   - Luggage considerations
5. Create comparison table
6. Recommend based on user preferences
7. Structure output in standard JSON format
8. Add practical booking notes
```

## Error Handling in Practice

**If transit_route returns no results**:
```markdown
1. Try alternative date (maybe no trains on that day)
2. Try broader time range
3. Try destination city name instead of specific address
4. Fall back to WebSearch for train schedules
```

**If driving_route fails**:
```markdown
1. Check coordinate format (lng,lat not lat,lng)
2. Try city names instead of specific addresses
3. Fall back to distance_measure for rough estimate
4. Use WebSearch for highway information
```

---

**Pattern demonstrated**: Multi-modal transportation comparison for inter-city travel planning
**Tools used**: `transit_route`, `driving_route`
**Output**: Structured transportation recommendation with alternatives
