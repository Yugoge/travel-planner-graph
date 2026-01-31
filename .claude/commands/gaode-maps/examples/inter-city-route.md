# Example: Inter-City Route Planning

Complete workflow for planning inter-city transportation using Gaode Maps skill.

## Scenario

User is traveling from Chongqing to Chengdu on Day 3 of their trip. Transportation agent needs to research options and recommend the best one.

## Step-by-Step Workflow

### Step 1: Load Routing Tools

```markdown
Load routing category: /root/travel-planner/.claude/commands/gaode-maps/tools/routing.md
```

This loads the `transit_route` and `driving_route` tools.

### Step 2: Plan Transit Route

```javascript
// Use transit_route for public transportation options
const transitResult = await transit_route({
  origin: "重庆",
  destination: "成都",
  cityd: "成都",
  strategy: 0  // Fastest route
});

// Response structure:
{
  route: {
    transits: [{
      segments: [{
        transit_type: "railway",
        departure: {name: "重庆西站", time: "08:30"},
        arrival: {name: "成都东站", time: "10:15"},
        duration: 6300,
        cost: 154
      }],
      duration: 6300,
      cost: 154
    }]
  }
}
```

### Step 3: Parse Response

Use the `parse-transit-routes.py` script to extract structured data:

```bash
# Save API response to file
echo "$transitResult" > transit-response.json

# Parse with Python script
/root/travel-planner/scripts/gaode-maps/parse-transit-routes.py transit-response.json -o parsed-route.json
```

**Parsed result:**
```json
{
  "from": "Chongqing",
  "to": "Chengdu",
  "transportation": "High-speed train",
  "departure_time": "08:30",
  "arrival_time": "10:15",
  "duration_minutes": 105,
  "cost": 154,
  "distance_km": 308,
  "notes": "Depart from 重庆西站, arrive at 成都东站"
}
```

**Script details:** `/root/travel-planner/scripts/gaode-maps/README.md`

### Step 4: Compare with Driving Option (Optional)

```javascript
// For comparison, also check driving route
const drivingResult = await driving_route({
  origin: "重庆",
  destination: "成都",
  strategy: 0  // Fastest
});

// Response structure:
{
  route: {
    distance: 308000,
    duration: 12600,
    tolls: 120
  }
}

// Parsed:
{
  from: "Chongqing",
  to: "Chengdu",
  transportation: "Private car",
  duration_minutes: 210,  // 3.5 hours
  cost: 120,  // Tolls only (excluding fuel)
  distance_km: 308,
  notes: "Tolls: ¥120, estimated fuel: ¥180 (total ~¥300)"
}
```

### Step 5: Make Recommendation

Use the `recommend-transportation.py` script to compare options:

```bash
# Create user preferences file
cat > preferences.json <<EOF
{
  "luggage": "light",
  "travelers": 2,
  "fuel_estimate_per_km": 0.6
}
EOF

# Generate recommendation
/root/travel-planner/scripts/gaode-maps/recommend-transportation.py \
  parsed-transit.json \
  parsed-driving.json \
  -p preferences.json \
  -o recommendation.json
```

**Output includes:**
- Recommended transportation option
- Score comparison (transit vs driving)
- Detailed reasoning for each factor (time, cost, convenience)

**Script details:** `/root/travel-planner/scripts/gaode-maps/README.md`

### Step 6: Save to Transportation JSON

```javascript
const recommendation = recommendTransportation(transitOption, drivingOption, {
  luggage: 'light',
  travelers: 2
});

const transportationData = {
  agent: "transportation",
  status: "complete",
  data: {
    days: [
      {
        day: 3,
        location_change: {
          from: "Chongqing",
          to: "Chengdu",
          ...recommendation
        }
      }
    ]
  },
  notes: "High-speed train recommended for time and cost efficiency. Book 1-2 weeks in advance for best prices."
};

// Save to: data/{destination-slug}/transportation.json
writeJSON(`data/${destinationSlug}/transportation.json`, transportationData);
```

---

## Error Handling Example

### Scenario: API Errors with Retry

The `fetch-route-with-retry.py` script handles transient errors automatically:

```bash
# Fetch with retry logic (max 3 attempts, exponential backoff)
/root/travel-planner/scripts/gaode-maps/fetch-route-with-retry.py \
  "重庆" "成都" \
  -t transit \
  -r 3 \
  -d 1.0 \
  -o route.json
```

**Retry behavior:**
- Retries on 429 (rate limit) and 5xx (server errors)
- Exponential backoff: 1s, 2s, 4s delays
- Fails immediately on 4xx client errors
- Logs all retry attempts for debugging

---

## Retry Logic Details

The retry logic is built into `fetch-route-with-retry.py`:

**Retryable errors:**
- HTTP 429 (rate limiting)
- HTTP 5xx (server errors)
- Network timeouts
- Temporary connection failures

**Non-retryable errors:**
- HTTP 4xx (client errors, except 429)
- Invalid parameters
- Authentication failures

**Backoff strategy:**
```
Attempt 1: Immediate
Attempt 2: Wait 1s
Attempt 3: Wait 2s
Attempt 4: Wait 4s
```

See script for implementation details.

---

## Multi-City Trip Example

### Scenario: Beijing → Bazhong → Chengdu → Shanghai

Use the `plan-multi-city.py` script:

```bash
/root/travel-planner/scripts/gaode-maps/plan-multi-city.py \
  Beijing Bazhong Chengdu Shanghai \
  -s 2 \
  -r 0.2 \
  -o multi-city-plan.json
```

**Features:**
- Automatic rate limiting (200ms between requests)
- Graceful error handling with manual research placeholders
- Sequential day numbering
- Complete transportation agent output format

**Output format:**
```json
{
  "agent": "transportation",
  "status": "complete",
  "data": {
    "days": [
      {"day": 2, "location_change": {...}},
      {"day": 3, "location_change": {...}},
      {"day": 4, "location_change": {...}}
    ]
  },
  "notes": "Transportation options researched using Gaode Maps API"
}
```

---

## Complete Transportation Agent Workflow

Use the `transportation-workflow.py` script for the complete agent workflow:

```bash
/root/travel-planner/scripts/gaode-maps/transportation-workflow.py \
  chongqing-chengdu-2026 \
  -v
```

**Workflow steps:**
1. Read requirements-skeleton.json and plan-skeleton.json
2. Identify days with location changes
3. Research routes with retry and recommendation logic
4. Save to transportation.json

**Required input files:**
- `/root/travel-planner/data/{destination-slug}/requirements-skeleton.json`
- `/root/travel-planner/data/{destination-slug}/plan-skeleton.json`

**Output file:**
- `/root/travel-planner/data/{destination-slug}/transportation.json`

**Returns:** `complete` status when finished

**Script details:** `/root/travel-planner/scripts/gaode-maps/README.md`

---

## Tips for Transportation Agent

1. **Always try Gaode Maps first**: More accurate and real-time than web search

2. **Implement retry logic**: Network issues are common, exponential backoff helps

3. **Graceful degradation**: If MCP fails, fall back to WebSearch

4. **Compare options**: Transit vs driving (when applicable)

5. **Consider user preferences**: Luggage, group size, budget, time constraints

6. **Rate limiting**: Add small delays between requests to avoid hitting limits

7. **Structured data**: Always output consistent JSON format for downstream agents

8. **Error reporting**: Include clear error messages and fallback instructions

9. **Real-time data**: Gaode Maps provides current schedules and traffic

10. **Chinese locations**: Works best with Chinese city names (e.g., "重庆" vs "Chongqing")
