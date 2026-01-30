# OpenWeatherMap - Weather Alerts

Get severe weather warnings for travel safety.

## MCP Tools

### Tool 1: weather_alerts

**MCP Tool Name**: `mcp__plugin_openweathermap_openweathermap__weather_alerts`

**Parameters**:
- `location` (required): City name or coordinates
  - Format: "City, Country Code" (e.g., "Miami, US")
  - Format: "lat,lon" (e.g., "25.7617,-80.1918")

**Returns**:
- `alerts`: Array of active weather alerts (may be empty if no alerts)
  - `sender_name`: Issuing agency/organization
  - `event`: Alert type/event name
  - `start`: Alert start time (UTC timestamp)
  - `end`: Alert end time (UTC timestamp)
  - `description`: Detailed alert description
  - `tags`: Alert category tags (array)

**Example**:
```javascript
// Get weather alerts for Miami
mcp__plugin_openweathermap_openweathermap__weather_alerts({
  location: "Miami, US"
})

// Response example (active hurricane warning):
{
  "alerts": [
    {
      "sender_name": "National Weather Service",
      "event": "Hurricane Warning",
      "start": 1706620800,
      "end": 1706707200,
      "description": "Hurricane warning in effect. Sustained winds of 120 mph expected. Storm surge of 10-15 feet possible. Evacuate coastal areas immediately. Shelter in place if unable to evacuate. Expect widespread power outages and flooding.",
      "tags": ["Extreme", "Wind", "Flood"]
    }
  ]
}

// Response example (no alerts):
{
  "alerts": []
}
```

**Use Cases**:
- Check for severe weather before trip
- Monitor alerts during travel
- Adjust itinerary for safety
- Decide whether to postpone travel
- Plan evacuation routes if necessary
- Alert travelers to take precautions

## Alert Types and Severity

### Extreme Severity

**Hurricane Warning**:
- **Action**: Evacuate or shelter immediately
- **Travel Impact**: Cancel/postpone travel
- **Duration**: 24-72 hours
- **Recommendations**: Do not travel, seek shelter

**Tornado Warning**:
- **Action**: Seek shelter immediately
- **Travel Impact**: Stop all outdoor activities
- **Duration**: Minutes to hours
- **Recommendations**: Indoor shelter, avoid windows

**Severe Thunderstorm Warning**:
- **Action**: Seek shelter, avoid outdoor exposure
- **Travel Impact**: Delay outdoor activities
- **Duration**: 1-3 hours
- **Recommendations**: Stay indoors, postpone outdoor plans

**Flash Flood Warning**:
- **Action**: Move to higher ground immediately
- **Travel Impact**: Avoid low-lying areas and roads
- **Duration**: Hours to days
- **Recommendations**: Do not drive through water, change routes

**Blizzard Warning**:
- **Action**: Stay indoors, avoid travel
- **Travel Impact**: All travel dangerous
- **Duration**: 12-48 hours
- **Recommendations**: Cancel outdoor plans, stock supplies

### High Severity

**Winter Storm Warning**:
- **Action**: Prepare for hazardous conditions
- **Travel Impact**: Travel difficult or dangerous
- **Duration**: 12-48 hours
- **Recommendations**: Delay travel, prepare warm clothing

**Heat Warning**:
- **Action**: Stay hydrated, limit outdoor exposure
- **Travel Impact**: Avoid strenuous outdoor activities
- **Duration**: Days to weeks
- **Recommendations**: Indoor activities during peak heat, hydration

**Flood Warning**:
- **Action**: Monitor conditions, prepare to evacuate
- **Travel Impact**: Roads may be impassable
- **Duration**: Days to weeks
- **Recommendations**: Alternative routes, avoid flood-prone areas

**High Wind Warning**:
- **Action**: Secure loose objects, avoid exposed areas
- **Travel Impact**: Driving hazardous, flights may delay
- **Duration**: Hours to day
- **Recommendations**: Indoor activities, monitor flight status

### Moderate Severity

**Winter Weather Advisory**:
- **Action**: Exercise caution when traveling
- **Travel Impact**: Roads may be slippery
- **Duration**: Hours to days
- **Recommendations**: Allow extra travel time, warm clothing

**Heat Advisory**:
- **Action**: Take heat precautions
- **Travel Impact**: Outdoor comfort reduced
- **Duration**: Days
- **Recommendations**: Plan indoor activities midday, stay hydrated

**Wind Advisory**:
- **Action**: Secure loose outdoor items
- **Travel Impact**: Minor travel impacts
- **Duration**: Hours
- **Recommendations**: Avoid exposed areas, monitor conditions

**Dense Fog Advisory**:
- **Action**: Reduce speed, use headlights
- **Travel Impact**: Visibility reduced
- **Duration**: Hours
- **Recommendations**: Allow extra travel time, delayed outdoor activities

## Best Practices

### 1. Pre-Trip Alert Check

**1-2 Weeks Before Travel**:
```markdown
1. Check weather alerts for destination
2. If extreme alert expected:
   - Consider rescheduling trip
   - Contact accommodation about cancellation
   - Monitor alert updates
3. If moderate alert:
   - Adjust itinerary
   - Pack appropriate gear
   - Have indoor backup plans
```

**24-48 Hours Before Travel**:
```markdown
1. Re-check weather alerts
2. If new extreme alert:
   - Postpone travel if possible
   - Contact airline/hotel
   - Have evacuation plan
3. If high severity alert:
   - Adjust first day plans
   - Stock emergency supplies
   - Know shelter locations
```

### 2. Daily Alert Monitoring

```markdown
Check alerts each morning:
1. If no alerts: Proceed with planned activities
2. If advisory issued: Adjust outdoor timing
3. If warning issued: Replace outdoor with indoor
4. If extreme warning: Shelter in place, cancel activities
```

### 3. Alert-Based Itinerary Adjustments

**Extreme Alert**:
```markdown
- Cancel all outdoor activities
- Stay in accommodation or indoor shelter
- Stock food, water, batteries
- Charge all devices
- Know emergency contacts
- Monitor alert updates every 2 hours
```

**High Severity Alert**:
```markdown
- Replace outdoor activities with indoor
- Visit museums, shopping malls, indoor entertainment
- Avoid driving unless necessary
- Stay in weather-resistant accommodation
- Monitor alert every 4 hours
```

**Moderate Severity Alert**:
```markdown
- Adjust outdoor activity timing
- Have indoor alternatives ready
- Pack appropriate weather gear
- Allow extra travel time
- Check alert status before leaving
```

### 4. Safety Protocols by Alert Type

**Hurricane/Typhoon**:
```markdown
- Evacuate if ordered by authorities
- If sheltering: stay away from windows, interior room
- Stock 3-7 days supplies
- Full device charges
- Know hospital/shelter locations
- Do NOT go outside during eye of storm
```

**Tornado**:
```markdown
- Go to lowest floor, interior room, no windows
- Bathroom or closet ideal
- Cover head and neck
- Stay until all-clear
- Do not try to outrun in vehicle
```

**Flash Flood**:
```markdown
- Move to higher ground immediately
- Never walk/drive through flood water
- 6 inches flowing water can knock you down
- 12 inches flowing water can move vehicle
- Abandon vehicle if trapped by rising water
```

**Extreme Heat**:
```markdown
- Stay indoors with AC 10:00-16:00
- Drink water every 30 minutes
- Avoid alcohol and caffeine
- Watch for heat exhaustion symptoms
- Cool showers, light clothing
```

**Blizzard**:
```markdown
- Stay indoors completely
- Do NOT attempt to travel
- Stock food and water
- Have flashlight and batteries
- Keep warm (layer clothing)
- Protect pipes from freezing
```

### 5. Communication During Alerts

**Before Alert Hits**:
```markdown
- Inform family/friends of situation
- Share accommodation address
- Exchange emergency contact numbers
- Set check-in schedule
- Download offline maps
```

**During Alert**:
```markdown
- Regular status updates to emergency contacts
- Monitor local news and official channels
- Follow instructions from local authorities
- Keep phone charged (conserve battery)
- Use text over calls (lower battery usage)
```

### 6. Travel Insurance and Alerts

```markdown
Weather alert issued:
- Document alert with screenshots
- Save official weather service warnings
- Keep all receipts for changed plans
- Contact insurance within 24 hours
- File claim with alert documentation

Covered scenarios:
- Trip cancellation due to extreme weather
- Accommodation extension due to travel delays
- Emergency evacuation
- Lost/damaged belongings in severe weather
```

## Integration with Planning

### Pre-Trip Planning

```markdown
Check historical alert frequency:
1. WebSearch: "[destination] weather alerts history [month]"
2. Identify high-risk periods (e.g., hurricane season June-Nov)
3. Consider alternative dates if frequent severe alerts
4. Factor alert risk into destination choice
```

### Timeline Agent Integration

```markdown
Daily timeline should include:
- Morning alert check (7:00-8:00 AM)
- Note: "Check weather alerts before starting activities"
- Flexible activities that can move indoors
- Emergency shelter location identified
- Alternative indoor itinerary ready
```

### Budget Agent Integration

```markdown
Alert-related budget items:
- Travel insurance with weather coverage: $50-150
- Emergency supplies (flashlight, water, snacks): $30-50
- Potential extra accommodation nights: $100-200/night
- Alternative transportation if routes closed: $50-300
- Emergency communication (prepaid SIM): $20-40
```

### Accommodation Agent Integration

```markdown
Choose accommodation with:
- Structural integrity for severe weather
- Backup generator for power outages
- Emergency shelter area (basement/interior rooms)
- 24/7 front desk for assistance
- Flexible cancellation policy
- Not in flood-prone or coastal evacuation zones
```

## Error Handling

**No Alert Data**:
```markdown
Not all locations provide alert data in API:
1. Fall back to WebSearch: "[location] weather warnings"
2. Check national weather service website
3. Subscribe to local emergency alerts
4. Download local weather apps
```

**Alert Format Variations**:
```markdown
Different countries use different alert systems:
- US: National Weather Service
- EU: MeteoAlarm
- Asia: Local meteorological agencies

Parse alerts flexibly, look for keywords:
- Warning, Watch, Advisory
- Severe, Extreme, Dangerous
- Hurricane, Tornado, Flood, etc.
```

**Language Barriers**:
```markdown
If alert in local language:
1. Use translation API
2. Look for severity indicators (colors, numbers)
3. Consult hotel staff for interpretation
4. Check English-language news sources
```

## Real-Time Alert Workflow

```markdown
Step 1: Check alerts for destination
  ↓
Step 2: No alerts → Proceed with plans
  ↓
Step 3: Alert exists → Analyze severity
  ↓
Step 4: Extreme → Postpone/evacuate
        High → Major adjustments
        Moderate → Minor adjustments
  ↓
Step 5: Update itinerary accordingly
  ↓
Step 6: Set alert re-check schedule
  ↓
Step 7: Monitor until alert expires
  ↓
Step 8: Resume normal activities after all-clear
```

## Example Integration

```markdown
User planning Miami trip Feb 15-20:

1. Check alerts: `/openweathermap alerts`
2. Load alerts tool, invoke for Miami
3. Result: No current alerts
4. Check historical: WebSearch "Miami weather alerts February history"
5. Result: Low risk, but check daily during trip
6. Add to itinerary notes:
   - "Check weather alerts daily at 7 AM"
   - "Have indoor backup plans for beach days"
   - "Know hurricane shelter location (rare but possible)"
7. Include in packing: Weather radio or alert app
```
