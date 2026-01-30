# OpenWeatherMap - Weather Alerts Tools

Severe weather warnings and alerts for safety-conscious travel planning.

## Available Tools

### 1. weather_alerts

Get active weather warnings and alerts for a location.

**MCP Tool**: `weather_alerts`

**Parameters**:
- `location` (required): City name, coordinates, or location ID

**Returns**:
- Active alerts list
- Alert severity (Minor, Moderate, Severe, Extreme)
- Alert type (Thunderstorm, Flood, Snow, Wind, Heat, Cold, etc.)
- Start and end times
- Alert description
- Issuing authority
- Affected areas

**Example**:
```javascript
// Get weather alerts for Miami during hurricane season
weather_alerts({
  location: "Miami,US"
})
```

**Response Format**:
```json
{
  "location": {
    "name": "Miami",
    "coordinates": { "lat": 25.7617, "lon": -80.1918 }
  },
  "alerts": [
    {
      "sender_name": "NWS Miami",
      "event": "Hurricane Warning",
      "start": 1738267200,
      "end": 1738353600,
      "description": "Hurricane force winds expected. Prepare for sustained winds of 75+ mph with higher gusts.",
      "severity": "Extreme",
      "tags": ["Wind", "Hurricane"],
      "areas": ["Miami-Dade County", "Broward County"]
    },
    {
      "sender_name": "NWS Miami",
      "event": "Storm Surge Warning",
      "start": 1738267200,
      "end": 1738353600,
      "description": "Life-threatening storm surge expected. Coastal flooding of 6-10 feet above ground level.",
      "severity": "Extreme",
      "tags": ["Coastal flood", "Storm surge"]
    }
  ],
  "alert_count": 2
}
```

**Alert Severity Levels**:
- **Minor**: Minimal impact expected
- **Moderate**: Possible impact to daily activities
- **Severe**: Significant impact, take action
- **Extreme**: Extraordinary threat, immediate action required

**Common Alert Types**:
- Thunderstorm
- Tornado
- Hurricane/Typhoon
- Flood/Flash Flood
- Winter Storm/Blizzard
- Heat/Excessive Heat
- Cold/Extreme Cold
- High Wind
- Dense Fog
- Ice Storm

**Use Cases**:
- Pre-trip safety assessment
- Real-time travel decisions
- Activity rescheduling
- Evacuation planning
- Insurance/cancellation decisions

---

## Best Practices

### 1. Alert Severity Interpretation

**Response by severity level**:
```javascript
function getActionBySeverity(severity) {
  const actions = {
    "Minor": {
      urgency: "low",
      action: "Monitor conditions, proceed with caution",
      impact: "Minimal disruption to plans expected"
    },
    "Moderate": {
      urgency: "medium",
      action: "Adjust outdoor activities, have backup plans",
      impact: "Some activities may need rescheduling"
    },
    "Severe": {
      urgency: "high",
      action: "Significantly modify itinerary, prioritize safety",
      impact: "Substantial changes to plans required"
    },
    "Extreme": {
      urgency: "critical",
      action: "Consider postponing trip or relocating to safer area",
      impact: "Life-threatening conditions, major disruption"
    }
  };

  return actions[severity] || actions["Moderate"];
}
```

### 2. Alert Type Handling

**Activity restrictions by alert type**:
```javascript
function getActivityRestrictions(alertType) {
  const restrictions = {
    "Thunderstorm": {
      avoid: ["Outdoor activities", "Water activities", "High elevation"],
      safe: ["Indoor attractions", "Shopping malls", "Museums"],
      timing: "Delay outdoor activities until 30 min after last thunder"
    },
    "Hurricane": {
      avoid: ["All outdoor activities", "Coastal areas", "Non-essential travel"],
      safe: ["Indoor shelter", "Sturdy buildings"],
      timing: "Remain sheltered until all-clear issued"
    },
    "Flood": {
      avoid: ["Low-lying areas", "River crossings", "Driving through water"],
      safe: ["Higher elevation areas", "Upper floor locations"],
      timing: "Avoid travel until waters recede"
    },
    "Heat": {
      avoid: ["Strenuous outdoor activities midday", "Prolonged sun exposure"],
      safe: ["Air-conditioned venues", "Water activities (pools)", "Early morning/evening activities"],
      timing: "Limit outdoor activities to early morning or evening"
    },
    "Winter Storm": {
      avoid: ["Road travel", "Outdoor activities", "Remote areas"],
      safe: ["Indoor venues with heating", "Well-stocked accommodations"],
      timing: "Travel only after roads cleared and conditions improve"
    },
    "High Wind": {
      avoid: ["High altitude", "Open areas", "Near trees/structures"],
      safe: ["Indoor venues", "Sheltered areas"],
      timing: "Wait for wind advisory to expire"
    }
  };

  return restrictions[alertType] || {
    avoid: ["Outdoor activities during alert"],
    safe: ["Indoor venues"],
    timing: "Monitor local authorities for updates"
  };
}
```

### 3. Multi-Alert Scenario

**Handle multiple simultaneous alerts**:
```javascript
function prioritizeAlerts(alerts) {
  const severityOrder = {
    "Extreme": 4,
    "Severe": 3,
    "Moderate": 2,
    "Minor": 1
  };

  const sorted = alerts.sort((a, b) =>
    (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0)
  );

  const highestSeverity = sorted[0]?.severity;

  return {
    alerts: sorted,
    primary_alert: sorted[0],
    action_required: severityOrder[highestSeverity] >= 3,
    recommendation: severityOrder[highestSeverity] >= 4
      ? "Strongly consider postponing or relocating trip"
      : "Adjust itinerary to account for weather conditions"
  };
}
```

### 4. Temporal Alert Analysis

**Check if alerts affect trip dates**:
```javascript
function analyzeAlertImpact(alerts, tripStartDate, tripEndDate) {
  const tripStart = new Date(tripStartDate).getTime() / 1000;
  const tripEnd = new Date(tripEndDate).getTime() / 1000;

  const impactingAlerts = alerts.filter(alert =>
    (alert.start <= tripEnd && alert.end >= tripStart)
  );

  const daysAffected = impactingAlerts.map(alert => {
    const overlapStart = Math.max(alert.start, tripStart);
    const overlapEnd = Math.min(alert.end, tripEnd);
    const durationDays = (overlapEnd - overlapStart) / 86400;

    return {
      alert: alert.event,
      severity: alert.severity,
      affected_days: Math.ceil(durationDays),
      start_date: new Date(overlapStart * 1000).toISOString(),
      end_date: new Date(overlapEnd * 1000).toISOString()
    };
  });

  return {
    has_impact: impactingAlerts.length > 0,
    alerts_during_trip: impactingAlerts,
    days_affected_breakdown: daysAffected,
    total_days_affected: daysAffected.reduce((sum, d) => sum + d.affected_days, 0),
    recommendation: generateRecommendationFromImpact(impactingAlerts)
  };
}
```

### 5. Alert Notification Thresholds

**Determine when to notify user**:
```javascript
function shouldNotifyUser(alerts, tripDays) {
  // Notify if:
  // 1. Any Extreme alerts
  if (alerts.some(a => a.severity === "Extreme")) {
    return {
      notify: true,
      urgency: "critical",
      message: "CRITICAL: Extreme weather alert active. Review trip safety."
    };
  }

  // 2. Multiple Severe alerts
  const severeCount = alerts.filter(a => a.severity === "Severe").length;
  if (severeCount >= 2) {
    return {
      notify: true,
      urgency: "high",
      message: `WARNING: ${severeCount} severe weather alerts. Significant itinerary changes may be needed.`
    };
  }

  // 3. Severe alert affecting >50% of trip
  const severeAlerts = alerts.filter(a => a.severity === "Severe");
  if (severeAlerts.length > 0) {
    const analysis = analyzeAlertImpact(severeAlerts, tripDays.start, tripDays.end);
    const tripDuration = (new Date(tripDays.end) - new Date(tripDays.start)) / (1000 * 86400);

    if (analysis.total_days_affected / tripDuration > 0.5) {
      return {
        notify: true,
        urgency: "high",
        message: `More than half of trip affected by severe weather. Consider rescheduling.`
      };
    }
  }

  // 4. Any alerts present (lower urgency)
  if (alerts.length > 0) {
    return {
      notify: true,
      urgency: "medium",
      message: `${alerts.length} weather alert(s) active. Review and adjust plans as needed.`
    };
  }

  return { notify: false };
}
```

### 6. Error Handling

**Handle missing alert data**:
```javascript
async function getWeatherAlertsWithFallback(location) {
  try {
    const alerts = await weather_alerts({ location });

    if (!alerts || alerts.alert_count === 0) {
      return {
        location,
        alerts: [],
        alert_count: 0,
        status: "No active alerts",
        checked_at: new Date().toISOString()
      };
    }

    return alerts;
  } catch (error) {
    if (error.status === 404) {
      // No alert data available for this location
      console.warn(`Alert data not available for ${location}`);
      return {
        location,
        alerts: [],
        alert_count: 0,
        status: "Alert data unavailable",
        note: "Monitor local weather authorities"
      };
    }

    // Other errors - fall back to web search
    console.warn('Weather alerts API unavailable, falling back to WebSearch');
    return await webSearchWeatherAlerts(location);
  }
}
```

## Integration with Travel Planning Agents

### Plan Orchestrator

**Check alerts before initiating planning**:

**Example workflow**:
```
1. User requests trip to Florida in August
2. Invoke /openweathermap alerts (loads this file)
3. Call weather_alerts({ location: "Florida,US" })
4. Check for active alerts: Hurricane Warning (Extreme)
5. Alert user IMMEDIATELY:
   "CRITICAL WEATHER ALERT: Hurricane warning active for Florida.
    Trip planning suspended pending weather update.
    Recommendation: Consider postponing or selecting alternative destination."
6. If user chooses to proceed, include weather warnings in all outputs
7. Prioritize flexible cancellation policies in all bookings
8. Include evacuation route information
```

### Transportation Agent

**Adjust transport based on alerts**:
```javascript
function selectTransportWithAlerts(options, weatherAlerts) {
  const severeAlerts = weatherAlerts.filter(a =>
    a.severity === "Severe" || a.severity === "Extreme"
  );

  if (severeAlerts.length === 0) return options;

  // Filter out affected transport modes
  const filtered = options.filter(opt => {
    if (severeAlerts.some(a => a.tags.includes("Wind") && opt.mode === "flight")) {
      return false; // Avoid flights during high wind
    }
    if (severeAlerts.some(a => a.tags.includes("Flood") && opt.mode === "driving")) {
      return false; // Avoid driving during floods
    }
    if (severeAlerts.some(a => a.tags.includes("Winter") && opt.mode === "driving")) {
      return false; // Avoid driving in winter storms
    }
    return true;
  });

  return filtered.map(opt => ({
    ...opt,
    note: "Selected based on active weather alerts",
    alert_consideration: true
  }));
}
```

### Accommodation Agent

**Recommend suitable accommodations**:
```javascript
function selectSafeAccommodation(hotels, weatherAlerts) {
  const extremeAlerts = weatherAlerts.filter(a => a.severity === "Extreme");

  if (extremeAlerts.length === 0) return hotels;

  // Prioritize hotels with safety features
  return hotels.sort((a, b) => {
    let scoreA = 0, scoreB = 0;

    // Hurricane/storm alerts
    if (extremeAlerts.some(a => a.tags.includes("Hurricane"))) {
      if (a.features?.includes("hurricane_rated")) scoreA += 10;
      if (b.features?.includes("hurricane_rated")) scoreB += 10;
      if (a.floor_level > 3) scoreA += 5; // Above storm surge
      if (b.floor_level > 3) scoreB += 5;
    }

    // Flood alerts
    if (extremeAlerts.some(a => a.tags.includes("Flood"))) {
      if (a.elevation === "high") scoreA += 10;
      if (b.elevation === "high") scoreB += 10;
    }

    return scoreB - scoreA;
  });
}
```

### Timeline Agent

**Reschedule activities around alerts**:
```javascript
function adjustTimelineForAlerts(timeline, alerts) {
  const alertsByDay = groupAlertsByDay(alerts);

  return timeline.map(day => {
    const dayAlerts = alertsByDay[day.date] || [];

    if (dayAlerts.some(a => a.severity === "Extreme")) {
      return {
        ...day,
        activities: [{
          type: "safety_day",
          description: "Remain in safe location due to extreme weather alert",
          details: dayAlerts.map(a => a.description).join("; ")
        }],
        alert_level: "extreme",
        original_activities: day.activities
      };
    }

    if (dayAlerts.some(a => a.severity === "Severe")) {
      return {
        ...day,
        activities: day.activities.filter(a => a.indoor),
        alert_level: "severe",
        note: "Outdoor activities moved to indoor alternatives due to severe weather"
      };
    }

    return day;
  });
}
```

## Quality Standards

- Check weather alerts during initial trip planning phase
- Re-check alerts 48 hours before trip departure
- Monitor alerts daily during trip
- Immediately notify users of Extreme alerts
- Provide clear action items for each alert severity
- Include alert issuing authority in outputs
- Document alert start/end times in local timezone
- Cache alert data (valid for 15-30 minutes)
- Handle regions without alert systems gracefully
- Provide alternative safety information sources
- Include emergency contact information for extreme alerts
- Document alert source and check timestamp
