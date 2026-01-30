# Example: Inter-city Route Planning

This example demonstrates using Google Maps route computation for transportation planning.

## Scenario

Planning transportation from Beijing to Shanghai for a multi-city trip.

## Workflow

### Step 1: Load Routing Tools

```
/google-maps routing
```

This loads the complete route computation tool documentation.

### Step 2: Invoke MCP Tool

```javascript
mcp__plugin_google-maps_google-maps__compute_routes({
  origin: {
    address: "Beijing, China"
  },
  destination: {
    address: "Shanghai, China"
  },
  travel_mode: "DRIVE",
  departure_time: "2026-02-15T08:00:00Z"
})
```

### Step 3: Parse Response

```json
{
  "routes": [
    {
      "summary": "G2 Beijing-Shanghai Expressway",
      "legs": [
        {
          "distance": {
            "value": 1213000,
            "text": "1,213 km"
          },
          "duration": {
            "value": 43200,
            "text": "12 hours 0 mins"
          },
          "duration_in_traffic": {
            "value": 46800,
            "text": "13 hours 0 mins"
          },
          "start_address": "Beijing, China",
          "end_address": "Shanghai, China",
          "start_location": {
            "lat": 39.9042,
            "lng": 116.4074
          },
          "end_location": {
            "lat": 31.2304,
            "lng": 121.4737
          }
        }
      ],
      "warnings": ["May include toll roads"]
    }
  ]
}
```

### Step 4: Calculate Transportation Options

```javascript
const route = routes[0].legs[0];
const distance_km = route.distance.value / 1000;
const driving_duration_hours = route.duration_in_traffic.value / 3600;

// Option 1: High-speed train
const train_duration = 5.5; // hours (typical for Beijing-Shanghai)
const train_cost = 80; // USD (second class)

// Option 2: Flight
const flight_duration = 2.5; // hours (including airport time)
const flight_cost = 120; // USD (economy)

// Option 3: Driving (not practical for this distance)
const driving_cost = distance_km * 0.5; // $0.50/km estimate
// driving_duration_hours from API
```

### Step 5: Select Optimal Option

```javascript
const options = [
  {
    type: "High-speed train",
    duration_hours: 5.5,
    cost: 80,
    comfort: "high",
    recommended: true,
    notes: "Most convenient, city center to city center"
  },
  {
    type: "Flight",
    duration_hours: 2.5,
    cost: 120,
    comfort: "medium",
    recommended: false,
    notes: "Fastest but includes airport transfers (add 3 hours total)"
  },
  {
    type: "Driving",
    duration_hours: 13,
    cost: 607,
    comfort: "low",
    recommended: false,
    notes: "Not recommended for this distance"
  }
];

// Select based on budget and time constraints
const selected = options.find(opt => opt.recommended);
```

### Step 6: Structure for Output

```json
{
  "day": 3,
  "location_change": {
    "from": "Beijing",
    "to": "Shanghai",
    "transportation": "High-speed train",
    "departure_time": "08:30",
    "arrival_time": "14:00",
    "duration_minutes": 330,
    "cost": 80,
    "notes": "Book 2 weeks in advance for discount | Distance: 1,213 km | Alternative: Flight (2.5h, $120)",
    "data_source": "google_maps"
  }
}
```

## Example 2: Local Transit Route

### Scenario

Getting from hotel to tourist attraction using public transit.

### Workflow

```javascript
mcp__plugin_google-maps_google-maps__compute_routes({
  origin: {
    latitude: 40.7580,
    longitude: -73.9855
  },
  destination: {
    latitude: 40.7614,
    longitude: -73.9776
  },
  travel_mode: "TRANSIT",
  departure_time: "2026-02-15T09:00:00Z"
})
```

### Response

```json
{
  "routes": [
    {
      "legs": [
        {
          "distance": { "value": 1200, "text": "1.2 km" },
          "duration": { "value": 780, "text": "13 mins" },
          "steps": [
            {
              "travel_mode": "WALKING",
              "distance": { "value": 150, "text": "150 m" },
              "duration": { "value": 120, "text": "2 mins" },
              "instruction": "Walk to Times Sq - 42 St"
            },
            {
              "travel_mode": "TRANSIT",
              "distance": { "value": 950, "text": "950 m" },
              "duration": { "value": 480, "text": "8 mins" },
              "instruction": "Subway towards Uptown",
              "transit_details": {
                "line": { "name": "N/Q/R/W", "color": "#FCCC0A" },
                "departure_stop": "Times Sq - 42 St",
                "arrival_stop": "57 St - 7 Av",
                "num_stops": 2
              }
            },
            {
              "travel_mode": "WALKING",
              "distance": { "value": 100, "text": "100 m" },
              "duration": { "value": 180, "text": "3 mins" },
              "instruction": "Walk to destination"
            }
          ]
        }
      ]
    }
  ]
}
```

### Parse Transit Instructions

```javascript
const steps = routes[0].legs[0].steps;
const transit_steps = steps.filter(s => s.travel_mode === "TRANSIT");

const instructions = transit_steps.map(step => ({
  line: step.transit_details.line.name,
  from: step.transit_details.departure_stop,
  to: step.transit_details.arrival_stop,
  stops: step.transit_details.num_stops,
  duration: step.duration.text
}));

// Output: "Take N/Q/R/W from Times Sq to 57 St (2 stops, 8 mins)"
```

## Error Handling

```javascript
let route_result;
const modes = ["TRANSIT", "DRIVE", "WALK"];

for (const mode of modes) {
  try {
    route_result = await compute_routes({
      origin: origin,
      destination: destination,
      travel_mode: mode
    });

    if (route_result.routes.length > 0) {
      route_result.travel_mode = mode;
      break;
    }
  } catch (error) {
    console.log(`${mode} mode failed, trying next...`);
    continue;
  }
}

if (!route_result) {
  // Fallback to WebSearch
  route_result = await webSearch(`how to get from ${origin} to ${destination}`);
  route_result.data_source = "web_search";
}
```

## Integration with Transportation Agent

```markdown
## Tasks

For each location change day:

1. Invoke `/google-maps routing` to load tool documentation
2. Call compute_routes with origin and destination
3. Parse response for distance and duration
4. For inter-city routes:
   - If distance > 1000km: Consider flight
   - If distance 300-1000km: Consider high-speed train
   - If distance < 300km: Consider bus or regular train
5. Use route data to estimate travel time and cost
6. Structure data for transportation.json
7. Fall back to WebSearch if MCP fails
```

## Best Practices

1. Always provide `departure_time` for traffic-aware routing
2. Try multiple travel modes to compare options
3. For TRANSIT, parse steps to extract vehicle types
4. Add 10-20% buffer time to API duration estimates
5. Check `warnings` for toll roads or restrictions
6. Document data source for traceability
7. Use WebSearch fallback for route verification
