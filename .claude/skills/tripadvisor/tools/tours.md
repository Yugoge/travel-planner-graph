# TripAdvisor - Tours and Activities

Search and discover tours, activities, experiences, and shows worldwide.

## MCP Tools

### Tool 1: search_tours

**MCP Tool Name**: `mcp__plugin_tripadvisor_tripadvisor__search_tours`

**Purpose**: Search for tours, activities, and experiences by location and category.

**Parameters**:
- `location` (required): City name or address
- `category` (optional): Tour type (day-trips, walking-tours, food-tours, cultural, adventure, nightlife, shows, water-activities)
- `time_of_day` (optional): Preferred time (morning, afternoon, evening, full-day)
- `min_rating` (optional): Minimum rating (1-5 scale, default: 4.0)
- `max_results` (optional): Maximum results (default: 20, max: 50)
- `price_range` (optional): Price filter (budget, moderate, luxury)
- `duration_hours` (optional): Preferred duration in hours
- `date` (optional): Specific date for availability check (YYYY-MM-DD)

**Returns**:
```json
{
  "tours": [
    {
      "id": "67890",
      "name": "Paris Evening Food Tour",
      "provider": "Local Food Tours Paris",
      "location": "Latin Quarter, Paris",
      "rating": 4.8,
      "reviews_count": 2340,
      "price_usd": 95.0,
      "duration_hours": 3.5,
      "category": "food-tour",
      "time_of_day": "evening",
      "group_size": "Small group (max 12)",
      "languages": ["English", "French"],
      "pickup_included": false,
      "cancellation_policy": "Free cancellation up to 24 hours",
      "booking_url": "https://www.tripadvisor.com/...",
      "available_dates": ["2026-02-20", "2026-02-21"]
    }
  ],
  "total_results": 87
}
```

**Use Cases**:
- Find evening entertainment and shows
- Search day trips and guided tours
- Discover food tours and culinary experiences
- Book cultural experiences and activities
- Find adventure and outdoor activities

**Example**:
```javascript
mcp__plugin_tripadvisor_tripadvisor__search_tours({
  location: "Paris, France",
  category: "food-tours",
  time_of_day: "evening",
  min_rating: 4.5,
  date: "2026-02-20",
  max_results: 10
})
```

---

### Tool 2: get_tour_details

**MCP Tool Name**: `mcp__plugin_tripadvisor_tripadvisor__get_tour_details`

**Purpose**: Get comprehensive details for a specific tour or activity.

**Parameters**:
- `tour_id` (required): TripAdvisor tour ID from search results
- `check_availability` (optional): Check real-time availability (default: true)
- `date` (optional): Specific date to check (YYYY-MM-DD)
- `include_reviews` (optional): Include user reviews (default: true, max: 10)

**Returns**:
```json
{
  "id": "67890",
  "name": "Paris Evening Food Tour",
  "description": "Discover authentic Parisian cuisine with a local guide...",
  "provider": {
    "name": "Local Food Tours Paris",
    "rating": 4.9,
    "years_operating": 8
  },
  "location": {
    "meeting_point": "Latin Quarter Metro Station",
    "address": "Place Saint-Michel, 75005 Paris",
    "coordinates": {"lat": 48.8534, "lng": 2.3434}
  },
  "rating": 4.8,
  "reviews_count": 2340,
  "price": {
    "amount_usd": 95.0,
    "per": "person",
    "includes": ["Food tastings", "Local guide", "Wine pairings"],
    "excludes": ["Gratuities", "Additional drinks"]
  },
  "schedule": {
    "duration_hours": 3.5,
    "times": ["18:00", "18:30"],
    "days_available": ["Monday", "Tuesday", "Thursday", "Friday", "Saturday"]
  },
  "availability": {
    "available": true,
    "next_available_date": "2026-02-20",
    "spots_remaining": 8
  },
  "details": {
    "group_size": "Small group (max 12)",
    "languages": ["English", "French"],
    "pickup_included": false,
    "accessibility": "Not wheelchair accessible",
    "minimum_age": 18,
    "cancellation_policy": "Free cancellation up to 24 hours before start"
  },
  "itinerary": [
    {
      "stop": 1,
      "location": "Fromagerie",
      "duration_minutes": 30,
      "description": "Cheese tasting with expert"
    },
    {
      "stop": 2,
      "location": "Boulangerie",
      "duration_minutes": 20,
      "description": "French pastries and breads"
    }
  ],
  "what_to_bring": ["Comfortable shoes", "Weather-appropriate clothing"],
  "booking_url": "https://www.tripadvisor.com/...",
  "reviews": [
    {
      "author": "FoodLover99",
      "rating": 5,
      "date": "2026-01-10",
      "text": "Amazing food, great guide, highly recommend!",
      "helpful_votes": 23
    }
  ],
  "traveler_tips": [
    "Book at least 3 days in advance",
    "Arrive 10 minutes early at meeting point",
    "Skip dinner beforehand - you'll eat plenty!"
  ]
}
```

**Use Cases**:
- Get full details before booking
- Check availability for specific dates
- Review itinerary and inclusions
- Verify cancellation policy
- Read traveler experiences

**Example**:
```javascript
mcp__plugin_tripadvisor_tripadvisor__get_tour_details({
  tour_id: "67890",
  check_availability: true,
  date: "2026-02-20",
  include_reviews: true
})
```

---

### Tool 3: search_shows

**MCP Tool Name**: `mcp__plugin_tripadvisor_tripadvisor__search_shows`

**Purpose**: Search for theater shows, concerts, performances, and entertainment.

**Parameters**:
- `location` (required): City name
- `show_type` (optional): Type (theater, concert, opera, ballet, comedy, circus, cultural-show)
- `date` (optional): Specific date or date range
- `min_rating` (optional): Minimum rating (default: 4.0)
- `max_results` (optional): Maximum results (default: 20)
- `price_range` (optional): Price filter

**Returns**:
```json
{
  "shows": [
    {
      "id": "11223",
      "name": "Moulin Rouge Cabaret Show",
      "venue": "Moulin Rouge",
      "location": "82 Boulevard de Clichy, 75018 Paris",
      "rating": 4.6,
      "reviews_count": 15780,
      "price_usd": 120.0,
      "show_type": "cultural-show",
      "duration_hours": 2.0,
      "showtimes": ["19:00", "21:00"],
      "dates_available": ["2026-02-20", "2026-02-21", "2026-02-22"],
      "dress_code": "Smart casual",
      "age_restriction": "18+",
      "languages": ["French", "English subtitles"],
      "booking_url": "https://www.tripadvisor.com/..."
    }
  ],
  "total_results": 34
}
```

**Use Cases**:
- Find evening entertainment
- Book theater shows and performances
- Discover cultural experiences
- Plan nightlife activities
- Find concerts and live music

**Example**:
```javascript
mcp__plugin_tripadvisor_tripadvisor__search_shows({
  location: "Paris, France",
  show_type: "cultural-show",
  date: "2026-02-20",
  min_rating: 4.5,
  max_results: 10
})
```

---

### Tool 4: search_by_category

**MCP Tool Name**: `mcp__plugin_tripadvisor_tripadvisor__search_by_category`

**Purpose**: Advanced search with multiple filters and categories.

**Parameters**:
- `location` (required): City or area name
- `categories` (required): Array of categories to search
- `filters` (optional): Object with additional filters
  - `min_rating`: Number (1-5)
  - `max_price_usd`: Number
  - `duration_range`: {"min": hours, "max": hours}
  - `time_of_day`: Array ["morning", "afternoon", "evening"]
  - `dates`: Array of dates to check
- `sort_by` (optional): Sort order (rating, price, popularity, duration)
- `max_results` (optional): Maximum results per category

**Returns**: Combined results from multiple categories

**Use Cases**:
- Comprehensive activity search
- Compare options across categories
- Filter by multiple criteria
- Find activities for specific time slots

**Example**:
```javascript
mcp__plugin_tripadvisor_tripadvisor__search_by_category({
  location: "Paris, France",
  categories: ["food-tours", "cultural-shows", "walking-tours"],
  filters: {
    min_rating: 4.5,
    max_price_usd: 100,
    time_of_day: ["evening"],
    dates: ["2026-02-20", "2026-02-21"]
  },
  sort_by: "rating",
  max_results: 5
})
```

---

## Tour Categories

### Entertainment Tours
- **nightlife**: Bar tours, pub crawls, nightclub experiences
- **shows**: Theater, cabaret, cultural performances
- **music**: Concerts, live music venues, jazz clubs

### Food & Drink
- **food-tours**: Walking food tours, culinary experiences
- **wine-tasting**: Vineyard tours, wine bars, tastings
- **cooking-classes**: Hands-on cooking experiences

### Cultural
- **cultural**: Traditional experiences, cultural immersion
- **historical**: Historical walking tours, heritage sites
- **religious**: Spiritual sites, pilgrimage tours

### Adventure
- **adventure**: Hiking, climbing, extreme sports
- **water-activities**: Kayaking, sailing, snorkeling
- **outdoor**: Nature tours, wildlife experiences

### Sightseeing
- **walking-tours**: Guided city walks, neighborhood tours
- **day-trips**: Full-day excursions outside city
- **hop-on-hop-off**: Bus tours, city sightseeing

## Best Practices

### Search Strategy for Entertainment

1. **Evening entertainment workflow**:
   ```
   Step 1: Search shows for destination
   Step 2: Filter by date and time (evening)
   Step 3: Check ratings (4.5+ recommended)
   Step 4: Get details for top 3 options
   Step 5: Verify availability and booking requirements
   ```

2. **Time-based filtering**:
   - Morning tours: 08:00-12:00
   - Afternoon activities: 13:00-17:00
   - Evening shows: 18:00-23:00
   - Full-day tours: 08:00-18:00

3. **Price filtering**:
   - Budget: <$50 USD per person
   - Moderate: $50-150 USD
   - Luxury: >$150 USD

### Availability Checking

**Always check availability**:
- Tours can sell out 3-7 days in advance
- Shows may have limited performances
- Seasonal activities may not be available
- Weather-dependent activities may cancel

**Booking timeline**:
- Popular tours: Book 7-14 days ahead
- Shows and performances: Book 3-7 days ahead
- Last-minute activities: Same-day or next-day

### Review Analysis

**What to look for**:
- Overall rating (4.5+ excellent, 4.0-4.5 good)
- Number of reviews (500+ very reliable)
- Recent reviews (last 3 months)
- Common themes in reviews
- Guide quality mentions
- Value for money comments

**Red flags**:
- Declining ratings over time
- Many cancellation complaints
- Safety concerns mentioned
- Misleading description warnings
- Poor guide or organization

### Data Processing

Structure tour data for agents:
```json
{
  "name": "Tour/Show Name",
  "location": "Venue or meeting point",
  "cost": 95.0,
  "time": "19:00",
  "duration_hours": 3.5,
  "type": "food-tour",
  "rating": 4.8,
  "reviews": 2340,
  "booking_required": true,
  "booking_url": "https://...",
  "availability": "Available 2026-02-20",
  "notes": "Book 3 days ahead. Free cancellation 24h.",
  "traveler_tips": ["Tip 1", "Tip 2"],
  "data_source": "tripadvisor"
}
```

## Error Handling

```javascript
// Robust tour search with fallback
async function searchEntertainment(location, date, preferences) {
  // Try TripAdvisor
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      // Search tours
      const tours = await search_tours({
        location,
        category: preferences.category,
        time_of_day: "evening",
        date,
        min_rating: 4.5
      });

      // Search shows
      const shows = await search_shows({
        location,
        show_type: preferences.show_type,
        date,
        min_rating: 4.5
      });

      return {
        tours: tours.tours || [],
        shows: shows.shows || [],
        source: "tripadvisor"
      };
    } catch (error) {
      if (attempt === 3) {
        // Fall back to WebSearch
        return await webSearchEntertainment(location, date);
      }
      await sleep(Math.pow(2, attempt) * 1000);
    }
  }
}
```

## Integration with Other Data

### Weather Integration
Check weather before recommending outdoor tours:
- Rain >50%: Indoor shows, covered tours
- Clear: Outdoor walking tours, night markets
- Hot >30°C: Evening tours only
- Cold <10°C: Shorter outdoor tours

### Schedule Integration
Verify tour timing with daily schedule:
- Morning tours: Don't conflict with breakfast/checkout
- Afternoon tours: Allow lunch time
- Evening shows: Coordinate with dinner plans
- Full-day tours: Entire day blocked

### Transportation Integration
Consider tour location vs accommodation:
- Tours near hotel: Easy logistics
- Tours far from hotel: Need transportation plan
- Pickup included: Verify pickup location/time
- No pickup: Plan transportation in advance

## Common Issues

**No availability**:
- Check alternative dates
- Look for similar tours/shows
- Consider other categories
- Book earlier next time

**Price confusion**:
- Verify per-person vs per-group
- Check what's included/excluded
- Note any additional fees
- Confirm currency

**Booking problems**:
- Use booking URL from API
- Check cancellation policy
- Verify confirmation process
- Note any deposit requirements

**Schedule conflicts**:
- Build buffer time before/after
- Consider travel time to venue
- Account for delays/traffic
- Don't overbook days

## Output Quality

**Include in recommendations**:
- Clear activity description
- Accurate timing and duration
- Verified pricing
- Booking requirements and deadlines
- Cancellation policy summary
- Key traveler tips
- Data source citation

**Warnings to note**:
- Sold out or limited availability
- Advance booking required
- Dress code or age restrictions
- Weather dependency
- Physical requirements
- Accessibility limitations

## Rate Limits

Same as attractions API:
- 100 requests per minute
- 10,000 requests per day

**Optimization**:
- Combine searches when possible
- Cache results within session
- Use category search to reduce API calls
- Implement backoff on rate limit errors
