# TripAdvisor - Attraction Search Example

Complete workflow for searching and recommending attractions using TripAdvisor.

## Scenario

User planning 3-day trip to Paris, France (Feb 20-22, 2026).
Interests: Museums, historical sites, architecture.
Budget: Moderate ($20-40 per attraction).

## Workflow

### Step 1: Load TripAdvisor Attraction Tools

```
User request: Research attractions for Paris trip
Agent: attractions

# Load skill
Read .claude/skills/tripadvisor/tools/attractions.md
```

### Step 2: Initial Broad Search

**Search Parameters**:
```javascript
{
  location: "Paris, France",
  min_rating: 4.0,
  max_results: 30,
  sort_by: "rating"
}
```

**API Call**:
```
mcp__plugin_tripadvisor_tripadvisor__search_attractions
```

**Sample Response**:
```json
{
  "attractions": [
    {
      "id": "188151",
      "name": "Louvre Museum",
      "location": "Rue de Rivoli, 75001 Paris",
      "rating": 4.6,
      "reviews_count": 112456,
      "price_usd": 22.0,
      "category": "museum",
      "hours": "9:00 AM - 6:00 PM",
      "duration_minutes": 180,
      "booking_required": true,
      "booking_url": "https://www.tripadvisor.com/..."
    },
    {
      "id": "188152",
      "name": "Eiffel Tower",
      "location": "Champ de Mars, 75007 Paris",
      "rating": 4.5,
      "reviews_count": 145820,
      "price_usd": 28.0,
      "category": "landmark",
      "hours": "9:00 AM - 11:45 PM",
      "duration_minutes": 120,
      "booking_required": true
    },
    {
      "id": "188153",
      "name": "Sainte-Chapelle",
      "location": "8 Boulevard du Palais, 75001 Paris",
      "rating": 4.8,
      "reviews_count": 23450,
      "price_usd": 13.0,
      "category": "historical",
      "hours": "9:00 AM - 5:00 PM",
      "duration_minutes": 60,
      "booking_required": false
    }
  ],
  "total_results": 156
}
```

### Step 3: Filter by User Interests

**Apply filters**:
- Category: museums, historical sites, landmarks
- Price: $20-40 USD range
- Rating: 4.5+ for reliability

**Selected attractions** (top 3 per day):
- Day 1: Louvre, Sainte-Chapelle (both in 1st arrondissement)
- Day 2: Eiffel Tower, Musée d'Orsay
- Day 3: Arc de Triomphe, Notre-Dame exterior

### Step 4: Get Detailed Information

For each selected attraction, get full details:

**Example - Louvre Museum**:
```javascript
mcp__plugin_tripadvisor_tripadvisor__get_attraction_details({
  attraction_id: "188151",
  include_reviews: true,
  include_photos: false
})
```

**Detailed Response**:
```json
{
  "id": "188151",
  "name": "Louvre Museum",
  "description": "The world's largest art museum and historic monument...",
  "location": {
    "address": "Rue de Rivoli, 75001 Paris, France",
    "coordinates": {"lat": 48.8606, "lng": 2.3376},
    "neighborhood": "1st arrondissement"
  },
  "rating": 4.6,
  "reviews_count": 112456,
  "price": {
    "amount_usd": 22.0,
    "currency": "USD",
    "notes": "Free first Sunday of month, under 18 free"
  },
  "hours": {
    "general": "9:00 AM - 6:00 PM, closed Tuesdays",
    "wednesday_friday": "9:00 AM - 9:45 PM"
  },
  "booking": {
    "required": true,
    "advance_recommended": true,
    "url": "https://www.louvre.fr/en/visit"
  },
  "features": [
    "Audio guide available (€5)",
    "Wheelchair accessible",
    "Free wifi",
    "Coat check",
    "Café and restaurant"
  ],
  "duration_minutes": 180,
  "best_time_to_visit": "Wednesday or Friday evening for fewer crowds",
  "reviews": [
    {
      "author": "ArtLover2024",
      "rating": 5,
      "date": "2025-12-15",
      "text": "Incredible museum! Book timed entry online to skip lines. Allow at least 3-4 hours.",
      "helpful_votes": 67
    },
    {
      "author": "TravelPro",
      "rating": 4,
      "date": "2026-01-08",
      "text": "Amazing art collection. Very crowded. Arrive early or visit evening hours.",
      "helpful_votes": 42
    }
  ],
  "traveler_tips": [
    "Book timed entry tickets online at least 3 days in advance",
    "Visit on Wednesday or Friday evening for extended hours and smaller crowds",
    "Download the Louvre app for self-guided tours",
    "Mona Lisa is very crowded - see it first thing or last hour",
    "Wear comfortable shoes - the museum is enormous",
    "Bring a light jacket - some galleries are cool"
  ]
}
```

### Step 5: Geographic Clustering

Use coordinates to cluster attractions:

**Day 1 - 1st Arrondissement** (both walkable):
- Louvre Museum (48.8606, 2.3376)
- Sainte-Chapelle (48.8553, 2.3450)
- Distance: ~0.9 km walking (12 minutes)

**Day 2 - Left Bank**:
- Eiffel Tower (48.8584, 2.2945)
- Musée d'Orsay (48.8600, 2.3266)
- Distance: ~2.8 km (25 min walk or metro)

**Day 3 - Champs-Élysées Area**:
- Arc de Triomphe (48.8738, 2.2950)
- Distance from hotel: Check with accommodation location

### Step 6: Weather Integration

Check weather forecast to optimize indoor/outdoor balance:

```
# Load weather skill
Read .claude/skills/openweathermap/tools/forecast.md

# Get 5-day forecast
mcp__plugin_openweathermap_openweathermap__get_forecast({
  location: "Paris, France",
  days: 5
})
```

**Sample forecast**:
- Feb 20: Rain 70%, 12°C → Indoor attractions (Louvre, Sainte-Chapelle)
- Feb 21: Clear, 15°C → Outdoor attractions (Eiffel Tower, walking)
- Feb 22: Partly cloudy, 13°C → Mix (Arc de Triomphe, indoor backup)

**Adjustment**: Move Louvre to rainy day (Feb 20), Eiffel Tower to clear day (Feb 21).

### Step 7: Validate Timing

**Day 1 - Feb 20 (Rainy)**:
- 9:00 AM: Louvre Museum (timed entry)
  - Duration: 3 hours
  - Exit: 12:00 PM
- 12:30 PM: Lunch break (1.5 hours)
- 2:00 PM: Sainte-Chapelle
  - Duration: 1 hour
  - Exit: 3:00 PM
- Total attraction time: 4 hours
- Buffer: 2 hours for meals, travel

**Day 2 - Feb 21 (Clear)**:
- 10:00 AM: Eiffel Tower (timed entry)
  - Duration: 2 hours
  - Exit: 12:00 PM
- 12:30 PM: Lunch (1.5 hours)
- 2:30 PM: Musée d'Orsay
  - Duration: 2.5 hours
  - Exit: 5:00 PM
- Total: Balanced indoor/outdoor

### Step 8: Structure Output

Format data for attractions.json:

```json
{
  "agent": "attractions",
  "status": "complete",
  "data": {
    "days": [
      {
        "day": 1,
        "date": "2026-02-20",
        "weather": "Rain 70%, 12°C - indoor attractions recommended",
        "attractions": [
          {
            "name": "Louvre Museum",
            "location": "Rue de Rivoli, 75001 Paris",
            "cost": 22.0,
            "duration_minutes": 180,
            "type": "Museum",
            "rating": 4.6,
            "reviews": 112456,
            "booking_required": true,
            "booking_url": "https://www.louvre.fr/en/visit",
            "time_slot": "9:00 AM",
            "notes": "Book timed entry 3+ days ahead. Visit Mona Lisa early. Wear comfortable shoes.",
            "traveler_tips": [
              "Download Louvre app for self-guided tour",
              "Some galleries are cool - bring light jacket",
              "Allow 3-4 hours minimum"
            ],
            "data_source": "tripadvisor"
          },
          {
            "name": "Sainte-Chapelle",
            "location": "8 Boulevard du Palais, 75001 Paris",
            "cost": 13.0,
            "duration_minutes": 60,
            "type": "Historical Site",
            "rating": 4.8,
            "reviews": 23450,
            "booking_required": false,
            "time_slot": "2:00 PM",
            "notes": "Short visit for stunning stained glass. Combined ticket available with Conciergerie.",
            "data_source": "tripadvisor"
          }
        ]
      },
      {
        "day": 2,
        "date": "2026-02-21",
        "weather": "Clear, 15°C - excellent for outdoor sightseeing",
        "attractions": [
          {
            "name": "Eiffel Tower",
            "location": "Champ de Mars, 75007 Paris",
            "cost": 28.0,
            "duration_minutes": 120,
            "type": "Landmark",
            "rating": 4.5,
            "reviews": 145820,
            "booking_required": true,
            "time_slot": "10:00 AM",
            "notes": "Book skip-the-line tickets. Clear day perfect for summit visit. Windy at top - bring jacket.",
            "traveler_tips": [
              "Arrive 10 min before time slot",
              "Visit summit for best views on clear day",
              "Photo opportunities on every level"
            ],
            "data_source": "tripadvisor"
          }
        ]
      }
    ]
  },
  "notes": "All attractions require advance booking. Timed entries recommended 3-7 days ahead. Schedule adjusted for weather forecast.",
  "booking_deadlines": {
    "louvre": "Book by Feb 17",
    "eiffel_tower": "Book by Feb 18"
  },
  "total_cost_usd": 63.0
}
```

## Error Handling Example

```javascript
async function searchAttractions(location) {
  // Attempt 1
  try {
    const results = await mcp__plugin_tripadvisor_tripadvisor__search_attractions({
      location: location,
      min_rating: 4.0,
      max_results: 30
    });
    return { data: results, source: "tripadvisor" };
  } catch (error) {
    console.log("Attempt 1 failed, retrying in 1s...");
    await sleep(1000);
  }

  // Attempt 2
  try {
    const results = await mcp__plugin_tripadvisor_tripadvisor__search_attractions({
      location: location,
      min_rating: 4.0,
      max_results: 30
    });
    return { data: results, source: "tripadvisor" };
  } catch (error) {
    console.log("Attempt 2 failed, retrying in 2s...");
    await sleep(2000);
  }

  // Attempt 3
  try {
    const results = await mcp__plugin_tripadvisor_tripadvisor__search_attractions({
      location: location,
      min_rating: 4.0,
      max_results: 30
    });
    return { data: results, source: "tripadvisor" };
  } catch (error) {
    console.log("All attempts failed, falling back to WebSearch");
    // Fallback to WebSearch
    const webResults = await webSearchAttractions(location);
    return { data: webResults, source: "web_search" };
  }
}
```

## Best Practices Demonstrated

1. **Progressive disclosure**: Load only attraction tools needed
2. **Filtering**: Apply user preferences (budget, interests, ratings)
3. **Geographic clustering**: Group attractions by proximity
4. **Weather integration**: Adjust indoor/outdoor based on forecast
5. **Timing validation**: Ensure realistic daily schedules
6. **Booking awareness**: Note advance booking requirements
7. **Traveler tips**: Include practical advice from reviews
8. **Error handling**: Retry with backoff, fallback to WebSearch
9. **Data source citation**: Always note data origin
10. **Structured output**: Format for easy consumption by orchestrator

## Common Pitfalls to Avoid

1. **Over-scheduling**: Don't pack 6+ attractions per day
2. **Ignoring travel time**: Allow 30-60 min between locations
3. **Missing booking deadlines**: Note advance booking requirements
4. **Ignoring weather**: Indoor backup for outdoor attractions
5. **Not reading reviews**: Traveler tips contain crucial info
6. **Price confusion**: Verify per-person vs family pricing
7. **Outdated hours**: Check seasonal variations in operating hours
8. **No error handling**: Always implement retry and fallback

## Output Quality Checklist

- [ ] All attractions real and currently open
- [ ] Ratings 4.0+ for reliability
- [ ] Booking requirements clearly noted
- [ ] Prices in USD per person
- [ ] Duration estimates realistic (include queues)
- [ ] Weather considerations included
- [ ] Geographic clustering optimized
- [ ] Traveler tips from reviews included
- [ ] Data source cited (tripadvisor or web_search)
- [ ] Booking deadlines calculated
- [ ] Total daily time under 6 hours of activities
- [ ] Buffer time for meals and travel included
