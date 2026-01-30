# TripAdvisor - Attractions

Search and discover tourist attractions, landmarks, and points of interest worldwide.

## MCP Tools

### Tool 1: search_attractions

**MCP Tool Name**: `mcp__plugin_tripadvisor_tripadvisor__search_attractions`

**Purpose**: Search for attractions by location, category, and filters.

**Parameters**:
- `location` (required): City name, address, or coordinates (e.g., "Paris, France", "40.7128,-74.0060")
- `category` (optional): Attraction type (museums, landmarks, parks, tours, outdoor, entertainment)
- `min_rating` (optional): Minimum rating (1-5 scale, default: 3.0)
- `max_results` (optional): Maximum results to return (default: 20, max: 50)
- `price_level` (optional): Price range filter (free, budget, moderate, expensive)
- `sort_by` (optional): Sort order (rating, popularity, distance, price)

**Returns**:
```json
{
  "attractions": [
    {
      "id": "12345",
      "name": "Eiffel Tower",
      "location": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris, France",
      "rating": 4.5,
      "reviews_count": 145820,
      "price_usd": 28.0,
      "category": "landmark",
      "hours": "9:00 AM - 11:45 PM",
      "duration_minutes": 120,
      "booking_required": true,
      "booking_url": "https://www.tripadvisor.com/...",
      "coordinates": {"lat": 48.8584, "lng": 2.2945}
    }
  ],
  "total_results": 156
}
```

**Use Cases**:
- Find top attractions in a destination
- Filter by user ratings and price
- Discover attractions by category (museums, parks, etc.)
- Sort by popularity or distance from location

**Example**:
```javascript
mcp__plugin_tripadvisor_tripadvisor__search_attractions({
  location: "Tokyo, Japan",
  category: "museums",
  min_rating: 4.0,
  max_results: 10,
  sort_by: "rating"
})
```

---

### Tool 2: get_attraction_details

**MCP Tool Name**: `mcp__plugin_tripadvisor_tripadvisor__get_attraction_details`

**Purpose**: Get comprehensive details for a specific attraction.

**Parameters**:
- `attraction_id` (required): TripAdvisor attraction ID from search results
- `include_reviews` (optional): Include user reviews (default: true, max: 10)
- `include_photos` (optional): Include photo URLs (default: true, max: 5)

**Returns**:
```json
{
  "id": "12345",
  "name": "Eiffel Tower",
  "description": "The iconic iron lattice tower on the Champ de Mars...",
  "location": {
    "address": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris, France",
    "coordinates": {"lat": 48.8584, "lng": 2.2945},
    "neighborhood": "7th arrondissement"
  },
  "rating": 4.5,
  "reviews_count": 145820,
  "price": {
    "amount_usd": 28.0,
    "currency": "USD",
    "notes": "Adult ticket, lift to summit"
  },
  "hours": {
    "monday": "9:00 AM - 11:45 PM",
    "tuesday": "9:00 AM - 11:45 PM",
    "general": "Open daily 9:00 AM - 11:45 PM"
  },
  "booking": {
    "required": true,
    "advance_recommended": true,
    "url": "https://www.tripadvisor.com/..."
  },
  "features": ["Skip-the-line available", "Audio guide", "Accessibility"],
  "duration_minutes": 120,
  "best_time_to_visit": "Early morning or evening to avoid crowds",
  "reviews": [
    {
      "author": "JohnDoe123",
      "rating": 5,
      "date": "2026-01-15",
      "text": "Absolutely stunning views! Book skip-the-line tickets.",
      "helpful_votes": 45
    }
  ],
  "photos": [
    {"url": "https://...", "caption": "View from summit"}
  ],
  "traveler_tips": [
    "Book tickets online in advance to avoid long queues",
    "Visit at sunset for spectacular views",
    "Bring a light jacket as it's windy at the top"
  ]
}
```

**Use Cases**:
- Get comprehensive information before recommending
- Access user reviews and traveler tips
- Check booking requirements and hours
- Verify pricing and duration

**Example**:
```javascript
mcp__plugin_tripadvisor_tripadvisor__get_attraction_details({
  attraction_id: "12345",
  include_reviews: true,
  include_photos: false
})
```

---

### Tool 3: search_by_coordinates

**MCP Tool Name**: `mcp__plugin_tripadvisor_tripadvisor__search_by_coordinates`

**Purpose**: Find attractions near specific GPS coordinates.

**Parameters**:
- `latitude` (required): Latitude coordinate
- `longitude` (required): Longitude coordinate
- `radius_km` (optional): Search radius in kilometers (default: 5, max: 50)
- `category` (optional): Filter by category
- `min_rating` (optional): Minimum rating filter
- `max_results` (optional): Maximum results (default: 20)

**Returns**: Same format as `search_attractions`

**Use Cases**:
- Find attractions near hotel or current location
- Discover nearby activities during travel
- Plan walking tours around specific area
- Find attractions along a route

**Example**:
```javascript
mcp__plugin_tripadvisor_tripadvisor__search_by_coordinates({
  latitude: 48.8584,
  longitude: 2.2945,
  radius_km: 2,
  min_rating: 4.0,
  max_results: 15
})
```

---

## Best Practices

### Search Strategy
1. **Start broad, then filter**:
   - Initial search with just location
   - Apply rating filter (4.0+ recommended)
   - Narrow by category if needed
   - Sort by rating or popularity

2. **Geographic clustering**:
   - Use `search_by_coordinates` after finding accommodation
   - Group attractions within 2-3km radius
   - Minimize travel time between activities

3. **Rating validation**:
   - Minimum 4.0 rating for reliable quality
   - Check review count (100+ reviews more reliable)
   - Read recent reviews for current status

### Data Processing
1. **Extract key information**:
   - Name, location, rating, reviews_count
   - Price (verify per-person vs per-group)
   - Hours (check for seasonal variations)
   - Duration (add buffer for queues)

2. **Validate booking requirements**:
   - Note if advance booking required
   - Check if skip-the-line available
   - Verify ticket URL is active

3. **Use traveler tips**:
   - Include in recommendations
   - Highlight important warnings
   - Note best times to visit

### Error Handling
```javascript
// Retry pattern
for (let attempt = 1; attempt <= 3; attempt++) {
  try {
    const results = await search_attractions(params);
    return results;
  } catch (error) {
    if (attempt === 3) {
      // Fall back to WebSearch
      return await webSearchAttractions(location);
    }
    await sleep(Math.pow(2, attempt) * 1000); // Exponential backoff
  }
}
```

### Common Filters
**By experience type**:
- Cultural: museums, historical sites, religious sites
- Nature: parks, beaches, viewpoints, gardens
- Entertainment: theme parks, zoos, aquariums
- Architecture: landmarks, monuments, buildings

**By activity level**:
- Low: museums, galleries, scenic drives
- Moderate: walking tours, parks, markets
- High: outdoor adventures, sports, physical activities

**By weather dependency**:
- Indoor: museums, galleries, shopping, theaters
- Outdoor: parks, monuments, viewpoints, markets
- Mixed: covered markets, some historical sites

## Output Structure

Structure attraction data for agents:
```json
{
  "name": "Attraction Name",
  "location": "Full address or area",
  "cost": 28.0,
  "duration_minutes": 120,
  "type": "Museum",
  "rating": 4.5,
  "reviews": 145820,
  "booking_required": true,
  "booking_url": "https://...",
  "notes": "Book skip-the-line tickets online. Visit early morning to avoid crowds.",
  "traveler_tips": ["Tip 1", "Tip 2"],
  "data_source": "tripadvisor"
}
```

## Integration with Weather

Combine with weather data for optimal recommendations:
- **Clear weather**: Outdoor attractions, parks, viewpoints
- **Rain**: Indoor museums, galleries, covered areas
- **Hot**: Morning outdoor visits, afternoon indoor attractions
- **Cold**: Indoor attractions, shorter outdoor visits

Load weather tools: `/openweathermap forecast`

## Common Issues

**Location not found**:
- Try broader search (city name instead of neighborhood)
- Use coordinates instead of address
- Check spelling and use English names

**No results**:
- Broaden search radius
- Remove rating filter
- Try different category
- Use WebSearch as fallback

**Outdated information**:
- Check review dates (prefer recent reviews)
- Verify hours on official website
- Note any warnings in recent reviews
- Confirm seasonal closures

**Pricing confusion**:
- Verify if price is per person or per group
- Check if price includes all features (e.g., lift to top)
- Note any additional fees (booking fees, audio guides)
- Confirm currency conversion

## Rate Limits

TripAdvisor API has rate limits:
- 100 requests per minute
- 10,000 requests per day

**If rate limited**:
- Implement exponential backoff
- Cache results for reuse
- Fall back to WebSearch
- Wait 60 seconds before retry
