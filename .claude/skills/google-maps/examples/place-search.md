# Example: Restaurant Search for Meal Planning

This example demonstrates using Google Maps place search to find restaurants for the meals agent.

## Scenario

Finding Italian restaurants near accommodation in Manhattan for dinner.

## Workflow

### Step 1: Load Places Tools

```
/google-maps places
```

This loads the complete place search tool documentation.

### Step 2: Invoke MCP Tool

```javascript
mcp__plugin_google-maps_google-maps__search_places({
  query: "italian restaurants",
  location: {
    latitude: 40.7580,
    longitude: -73.9855
  },
  radius: 2000,
  type: "restaurant"
})
```

### Step 3: Parse Response

```json
{
  "places": [
    {
      "name": "Carbone",
      "formatted_address": "181 Thompson St, New York, NY 10012",
      "location": {
        "lat": 40.7260,
        "lng": -74.0030
      },
      "place_id": "ChIJxxx...",
      "rating": 4.6,
      "user_ratings_total": 3421,
      "types": ["restaurant", "food", "point_of_interest"],
      "price_level": 4,
      "opening_hours": {
        "open_now": true,
        "weekday_text": [
          "Monday: 5:30 PM – 11:00 PM",
          "Tuesday: 5:30 PM – 11:00 PM",
          ...
        ]
      },
      "business_status": "OPERATIONAL"
    },
    {
      "name": "L'Artusi",
      "formatted_address": "228 W 10th St, New York, NY 10014",
      "rating": 4.5,
      "user_ratings_total": 2156,
      "price_level": 3,
      "business_status": "OPERATIONAL"
    }
  ]
}
```

### Step 4: Filter Results

```javascript
const filtered = response.places.filter(place =>
  place.rating >= 4.0 &&
  place.user_ratings_total >= 100 &&
  place.price_level <= 3 &&
  place.business_status === "OPERATIONAL"
);
```

### Step 5: Structure for Output

```json
{
  "day": 1,
  "dinner": {
    "name": "L'Artusi",
    "location": "228 W 10th St, New York, NY 10014",
    "cost": 45,
    "cuisine": "Italian",
    "notes": "4.5 stars (2,156 reviews) | Reservations recommended | Open 5:30-11pm",
    "data_source": "google_maps"
  }
}
```

## Error Handling

```javascript
let result;
let attempts = 0;
const max_attempts = 3;

while (attempts < max_attempts) {
  try {
    result = await mcp__plugin_google-maps_google-maps__search_places({
      query: "italian restaurants",
      location: { latitude: 40.7580, longitude: -73.9855 },
      radius: 2000,
      type: "restaurant"
    });
    break; // Success
  } catch (error) {
    attempts++;
    if (attempts >= max_attempts) {
      // Fallback to WebSearch
      result = await webSearch("italian restaurants near Times Square NYC");
      result.data_source = "web_search";
    } else {
      // Exponential backoff
      await sleep(Math.pow(2, attempts) * 1000);
    }
  }
}
```

## Integration with Meals Agent

```markdown
## Tasks

For each day, for each meal:

1. Invoke `/google-maps places` to load tool documentation
2. Determine search parameters:
   - query: cuisine type + meal type
   - location: coordinates of accommodation or attraction area
   - radius: 1500m for breakfast, 3000m for lunch/dinner
   - type: "restaurant" or "cafe"
3. Call search_places MCP tool
4. Filter results: rating >= 4.0, reviews >= 100, price within budget
5. Structure data for meals.json
6. Fall back to WebSearch if MCP fails
```

## Best Practices

1. Always filter by rating and review count for quality
2. Check `business_status` to avoid closed venues
3. Verify `opening_hours` match meal time
4. Consider `price_level` against budget
5. Document data source for traceability
6. Implement retry logic with fallback
