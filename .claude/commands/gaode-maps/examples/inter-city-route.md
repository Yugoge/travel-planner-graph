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

```javascript
function parseTransitRoute(result) {
  const mainSegment = result.route.transits[0].segments.find(
    s => s.transit_type === 'railway' || s.transit_type === 'bus'
  );

  return {
    from: "Chongqing",
    to: "Chengdu",
    transportation: mainSegment.transit_type === 'railway'
      ? 'High-speed train'
      : 'Bus',
    departure_time: mainSegment.departure.time,
    arrival_time: mainSegment.arrival.time,
    duration_minutes: Math.round(mainSegment.duration / 60),
    cost: mainSegment.cost,
    distance_km: Math.round(mainSegment.distance / 1000),
    notes: `Depart from ${mainSegment.departure.name}, arrive at ${mainSegment.arrival.name}`
  };
}

// Parsed result:
{
  from: "Chongqing",
  to: "Chengdu",
  transportation: "High-speed train",
  departure_time: "08:30",
  arrival_time: "10:15",
  duration_minutes: 105,
  cost: 154,
  distance_km: 308,
  notes: "Depart from 重庆西站, arrive at 成都东站"
}
```

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

```javascript
function recommendTransportation(transitOption, drivingOption, userPreferences) {
  const considerations = [];

  // Time comparison
  if (transitOption.duration_minutes < drivingOption.duration_minutes) {
    considerations.push({
      factor: 'time',
      winner: 'transit',
      detail: `Train is ${drivingOption.duration_minutes - transitOption.duration_minutes} minutes faster`
    });
  }

  // Cost comparison (including estimated fuel for driving)
  const drivingTotalCost = drivingOption.cost + 180;  // Tolls + fuel estimate
  if (transitOption.cost < drivingTotalCost) {
    considerations.push({
      factor: 'cost',
      winner: 'transit',
      detail: `Train is ¥${drivingTotalCost - transitOption.cost} cheaper`
    });
  }

  // Convenience
  if (userPreferences.luggage === 'heavy' || userPreferences.travelers > 3) {
    considerations.push({
      factor: 'convenience',
      winner: 'driving',
      detail: 'Private car better for heavy luggage or large groups'
    });
  }

  // Recommendation logic
  const transitScore = considerations.filter(c => c.winner === 'transit').length;
  const drivingScore = considerations.filter(c => c.winner === 'driving').length;

  return transitScore >= drivingScore ? transitOption : drivingOption;
}
```

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

### Scenario: MCP Server Unavailable

```javascript
async function getRouteWithFallback(origin, destination) {
  try {
    // Try Gaode Maps first
    const route = await transit_route({
      origin: origin,
      destination: destination,
      cityd: destination
    });

    return {
      source: 'gaode_maps',
      data: parseTransitRoute(route)
    };
  } catch (error) {
    console.warn('Gaode Maps unavailable, falling back to WebSearch');

    // Fallback to WebSearch
    const searchQuery = `${origin} to ${destination} train schedule 2026`;
    const searchResults = await WebSearch({ query: searchQuery });

    return {
      source: 'web_search',
      data: parseWebSearchResults(searchResults),
      warning: 'Data from web search, may not be real-time'
    };
  }
}
```

---

## Retry Logic Example

### Scenario: Transient Network Error

```javascript
async function getRouteWithRetry(origin, destination, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await transit_route({
        origin: origin,
        destination: destination,
        cityd: destination
      });
    } catch (error) {
      // Retry on transient errors
      if (error.status === 429 || error.status >= 500) {
        const delay = 1000 * Math.pow(2, i);  // Exponential backoff
        console.warn(`Retry ${i + 1}/${maxRetries} after ${delay}ms`);
        await sleep(delay);
        continue;
      }

      // Don't retry on permanent errors
      throw error;
    }
  }

  throw new Error('Max retries exceeded');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

---

## Multi-City Trip Example

### Scenario: Beijing → Bazhong → Chengdu → Shanghai

```javascript
async function planMultiCityTransportation(cities) {
  const routes = [];

  for (let i = 0; i < cities.length - 1; i++) {
    const origin = cities[i];
    const destination = cities[i + 1];

    try {
      // Get transit route
      const route = await getRouteWithRetry(origin, destination);
      const parsed = parseTransitRoute(route);

      routes.push({
        day: i + 2,  // Assuming day 1 is arrival
        location_change: parsed
      });

      // Rate limiting: small delay between requests
      await sleep(200);
    } catch (error) {
      console.error(`Failed to get route: ${origin} → ${destination}`, error);

      // Add placeholder for manual research
      routes.push({
        day: i + 2,
        location_change: {
          from: origin,
          to: destination,
          status: 'manual_research_required',
          error: error.message
        }
      });
    }
  }

  return {
    agent: "transportation",
    status: "complete",
    data: { days: routes },
    notes: "Transportation options researched using Gaode Maps API"
  };
}
```

---

## Complete Transportation Agent Workflow

```javascript
async function transportationAgentWorkflow(destinationSlug) {
  // Step 1: Read requirements and plan skeleton
  const requirements = readJSON(`data/${destinationSlug}/requirements-skeleton.json`);
  const planSkeleton = readJSON(`data/${destinationSlug}/plan-skeleton.json`);

  // Step 2: Identify days with location changes
  const locationChangeDays = planSkeleton.days.filter(day => day.location_change);

  if (locationChangeDays.length === 0) {
    return {
      agent: "transportation",
      status: "complete",
      data: { days: [] },
      notes: "No inter-city transportation needed (single-city trip)"
    };
  }

  // Step 3: Research routes for each location change
  const routes = [];

  for (const day of locationChangeDays) {
    const { from, to } = day.location_change;

    try {
      // Use Gaode Maps with retry and fallback
      const transitRoute = await getRouteWithRetry(from, to);
      const drivingRoute = await getRouteWithRetry(from, to, 2);  // Fewer retries for comparison

      const transitParsed = parseTransitRoute(transitRoute);
      const drivingParsed = parseDrivingRoute(drivingRoute);

      // Make recommendation
      const recommendation = recommendTransportation(
        transitParsed,
        drivingParsed,
        requirements.trip_summary.preferences
      );

      routes.push({
        day: day.day,
        location_change: recommendation
      });
    } catch (error) {
      console.error(`Route research failed for day ${day.day}`, error);

      routes.push({
        day: day.day,
        location_change: {
          from: from,
          to: to,
          status: 'research_failed',
          error: error.message,
          fallback: 'Manual research required'
        }
      });
    }

    // Rate limiting
    await sleep(200);
  }

  // Step 4: Save results
  const transportationData = {
    agent: "transportation",
    status: "complete",
    data: { days: routes },
    notes: "Routes researched using Gaode Maps. Book transportation 1-2 weeks in advance."
  };

  writeJSON(`data/${destinationSlug}/transportation.json`, transportationData);

  return "complete";
}
```

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
