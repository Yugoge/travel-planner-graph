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

### Example:

```javascript
const transitResult = await transit_route({
  origin: "重庆", destination: "成都", cityd: "成都", strategy: 0
});
// Returns: route.transits[].{segments[], duration, cost}
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

### Example:

```javascript
const drivingResult = await driving_route({
  origin: "重庆", destination: "成都", strategy: 0
});
// Returns: route.{distance, duration, tolls}
// Parse to: {transportation: "Private car", duration_minutes, cost, distance_km, notes}
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
const transportationData = {
  agent: "transportation", status: "complete",
  data: { days: [{ day: 3, location_change: {...recommendation} }] },
  notes: "Recommendation rationale"
};
// Save to: data/{destination-slug}/transportation.json
```

---

## Error Handling Example

### Scenario: API Errors with Retry

The routing script handles transient errors automatically with built-in retry logic:

```bash
# Use routing.py with retry (max 3 attempts, exponential backoff)
source venv/bin/activate || source .venv/bin/activate
python3 .claude/skills/gaode-maps/scripts/routing.py transit "重庆" "成都" --retry
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

## Multi-City Trip Example

```bash
/root/travel-planner/scripts/gaode-maps/plan-multi-city.py Beijing Bazhong Chengdu Shanghai -s 2 -r 0.2 -o multi-city-plan.json
```

**Features**: Automatic rate limiting, error handling, sequential day numbering
**Output**: Complete transportation agent JSON format

---

## Complete Transportation Agent Workflow

```bash
/root/travel-planner/scripts/gaode-maps/transportation-workflow.py chongqing-chengdu-2026 -v
```

**Input**: requirements-skeleton.json, plan-skeleton.json
**Output**: transportation.json
**Details**: See `/root/travel-planner/scripts/gaode-maps/README.md`

---

## Tips

1. Try Gaode Maps first (accurate, real-time)
2. Implement retry logic with exponential backoff
3. Fall back to WebSearch if MCP fails
4. Compare transit vs driving options
5. Consider user preferences (luggage, group size, budget)
6. Add delays to avoid rate limits
7. Output consistent JSON for downstream agents
8. Use Chinese city names for best results
