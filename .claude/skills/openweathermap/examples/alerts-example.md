# Weather Alerts Example

Get severe weather alerts and warnings for safety planning.

## Use Case

Check for weather alerts before travel to avoid dangerous conditions and plan safe routes.

## Script Execution

### Example 1: Check Alerts

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/alerts.py "Miami, US"
```

**Expected Output (with alerts)**:
```
Location Timezone: America/New_York

2 Active Weather Alert(s):
============================================================

Alert #1
----------------------------------------
Issued by: NWS Miami (National Weather Service)
Event: Hurricane Warning
Start: 2026-01-30 08:00:00
End: 2026-01-31 20:00:00

Description:
...HURRICANE WARNING IN EFFECT...

A Hurricane Warning means that hurricane conditions are expected
somewhere within the warning area. A warning is typically issued
36 hours before the anticipated first occurrence of tropical-storm-
force winds, conditions that make outside preparations difficult or
dangerous. Preparations to protect life and property should be rushed
to completion.

* LOCATIONS AFFECTED
  - Miami-Dade County
  - Broward County

* HAZARDS
  - Hurricane force winds expected
  - Storm surge 5 to 8 feet possible
  - Heavy rainfall 4 to 8 inches

Tags: Hurricane, Tropical

Alert #2
----------------------------------------
Issued by: NWS Miami (National Weather Service)
Event: Coastal Flood Warning
Start: 2026-01-30 12:00:00
End: 2026-01-31 18:00:00

Description:
...COASTAL FLOOD WARNING IN EFFECT...

A Coastal Flood Warning means that moderate to major coastal flooding
is occurring or imminent. Coastal residents in the warned area should
be alert for rising water, and take appropriate action to protect life
and property.

Tags: Flood, Coastal
```

**Expected Output (no alerts)**:
```
Location Timezone: America/New_York

No active weather alerts for this location.
```

### Example 2: Summary Only

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/alerts.py "New Orleans, US" --summary
```

**Expected Output**:
```
2 Tropical Storm Warning, 1 Flood Watch
```

### Example 3: JSON Output

**Command**:
```bash
python3 .claude/skills/openweathermap/scripts/alerts.py "Houston, US" --json
```

**Expected Output** (abbreviated):
```json
{
  "lat": 29.7604,
  "lon": -95.3698,
  "timezone": "America/Chicago",
  "timezone_offset": -21600,
  "alerts": [
    {
      "sender_name": "NWS Houston/Galveston",
      "event": "Flood Watch",
      "start": 1706659200,
      "end": 1706745600,
      "description": "...FLOOD WATCH IN EFFECT FROM THURSDAY EVENING THROUGH FRIDAY AFTERNOON...\n\nThe National Weather Service in Houston/Galveston has issued a Flood Watch...",
      "tags": ["Flood"]
    }
  ]
}
```

## Agent Integration

**For transportation agent**:
```markdown
Before planning route:

1. Execute: python3 .claude/skills/openweathermap/scripts/alerts.py "<origin-city>"
2. Execute: python3 .claude/skills/openweathermap/scripts/alerts.py "<destination-city>"
3. Parse alerts for severe weather
4. If hurricane/tornado/flood warning: Recommend travel delay or alternative route
5. Provide safety warnings to user
```

**For timeline agent**:
```markdown
When creating daily schedule:

1. Execute: python3 .claude/skills/openweathermap/scripts/alerts.py "<city>" --summary
2. If alerts present: Execute full details (without --summary)
3. Parse alert types and time ranges
4. Reschedule outdoor activities outside alert periods
5. Recommend indoor alternatives during severe weather
6. Provide emergency preparation recommendations
```

**For all agents**:
```markdown
Critical safety check:

1. Always check alerts before providing recommendations
2. Hurricane/Tornado Warning: STRONGLY recommend postponing travel
3. Flood Warning: Suggest alternative routes, avoid low-lying areas
4. Heat Advisory: Recommend early morning/evening activities
5. Winter Storm Warning: Add extra travel time, suggest postponement
6. Include alert details in final recommendations
```

## Alert Types and Actions

| Alert Type | Recommended Action |
|------------|-------------------|
| Hurricane Warning | Postpone travel, seek shelter |
| Tornado Warning | Immediate shelter, cancel outdoor plans |
| Flood Warning | Avoid affected areas, alternative routes |
| Severe Thunderstorm | Delay outdoor activities 1-2 hours |
| Heat Advisory | Schedule indoor activities, stay hydrated |
| Winter Storm Warning | Postpone travel, allow extra time |
| High Wind Warning | Secure outdoor items, avoid exposed areas |
| Fog Advisory | Reduce speed, allow extra travel time |

## Parsing JSON Alerts

**Extract key information**:
```bash
# Get all alert types
python3 .claude/skills/openweathermap/scripts/alerts.py "Miami, US" --json | \
  jq '.alerts[] | .event'

# Get alerts active now
python3 .claude/skills/openweathermap/scripts/alerts.py "Houston, US" --json | \
  jq --arg now "$(date +%s)" '.alerts[] | select(.start <= ($now|tonumber) and .end >= ($now|tonumber))'

# Count alerts by type
python3 .claude/skills/openweathermap/scripts/alerts.py "New Orleans, US" --json | \
  jq '.alerts | group_by(.event) | map({event: .[0].event, count: length})'
```

## Integration with Other Weather Scripts

**Complete weather check workflow**:
```bash
# Step 1: Check alerts (safety first)
python3 .claude/skills/openweathermap/scripts/alerts.py "Miami, US" --summary

# Step 2: If safe, check current weather
if [ $? -eq 0 ]; then
  python3 .claude/skills/openweathermap/scripts/current.py "Miami, US"
fi

# Step 3: Get forecast for planning
python3 .claude/skills/openweathermap/scripts/forecast.py "Miami, US" --days 3
```

## Error Handling

**If location not found**:
```bash
$ python3 .claude/skills/openweathermap/scripts/alerts.py "InvalidCity, XX"
Error: Failed after 3 attempts: MCP error: Location not found
```

**Solution**: Verify city name and country code format

## Notes

- Alerts are location-specific (city/county level)
- Alert timing in local timezone
- Some locations may have no alerts (normal)
- Free tier includes alert data
- Alerts updated in real-time by government agencies (NWS, NOAA, etc.)
- International alerts available where supported by local agencies

## Safety Recommendations

**When alerts present**:
1. Always prioritize user safety over itinerary
2. Provide clear, actionable recommendations
3. Include official alert text in response
4. Suggest alternative dates or locations
5. Recommend emergency preparation if needed
6. Link to local emergency services information
