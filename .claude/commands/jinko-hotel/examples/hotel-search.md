# Example: Hotel Search for Multi-City Trip

This example demonstrates using Jinko Hotel skill for a multi-city trip: Beijing → Chengdu → Shanghai.

## Scenario

User requirements:
- Destinations: Beijing (3 nights), Chengdu (2 nights), Shanghai (2 nights)
- Budget: $100-150 per night
- Required amenities: WiFi, breakfast
- Preferred: Near city center, high ratings (4+)
- Travel dates: March 1-8, 2026

## Step-by-Step Workflow

### Step 1: Load Jinko Hotel Search Tools

```markdown
Invoke: /jinko-hotel search
```

This loads `/root/travel-planner/.claude/commands/jinko-hotel/tools/search.md` with hotel search and filtering tools.

---

### Step 2: Search Hotels in Beijing

```javascript
// Search for hotels in Beijing (March 1-4)
const beijingSearch = await search_hotels({
  location: "Beijing, China",
  check_in: "2026-03-01",
  check_out: "2026-03-04",
  guests: 2,
  rooms: 1,
  min_price: 100,
  max_price: 150,
  rating_min: 4,
  sort_by: "rating"
});

// Results:
// - 47 hotels found
// - Price range: $102-148
// - Average rating: 4.3 stars
// - search_id: "search_beijing_abc123"
```

---

### Step 3: Filter by Required Amenities

```javascript
// Filter for WiFi and breakfast
const beijingFiltered = await filter_by_facilities({
  search_id: "search_beijing_abc123",
  facilities: ["wifi", "breakfast"]
});

// Results:
// - 23 hotels match criteria
// - Top result: Beijing Central Hotel
//   - Price: $128/night
//   - Rating: 4.6 stars (guest rating: 8.9/10)
//   - Location: 2km from Forbidden City
```

---

### Step 4: Validate Top Hotel (Optional)

Load details tools if additional validation needed:

```markdown
Invoke: /jinko-hotel details
```

```javascript
// Get detailed information
const hotelDetails = await get_hotel_details({
  hotel_id: "beijing_central_hotel_001",
  check_in: "2026-03-01",
  check_out: "2026-03-04"
});

// Verify:
// - Amenities: Free WiFi, Breakfast buffet, Gym, Pool
// - Check-in: 14:00, Check-out: 12:00
// - Cancellation: Free until 24h before check-in
// - Reviews: 856 reviews, average 8.9/10
//   - Common praises: "clean", "friendly staff", "great location"
//   - Common complaints: "small rooms" (minor)
```

---

### Step 5: Select Hotel for Beijing

```json
{
  "day": 1,
  "accommodation": {
    "name": "Beijing Central Hotel",
    "location": "2 Dongcheng District, Beijing, 2km from Forbidden City",
    "cost": 128,
    "type": "Hotel",
    "amenities": ["Free WiFi", "Breakfast buffet", "Gym", "Pool"],
    "notes": "Check-in: 14:00, Check-out: 12:00, Free cancellation"
  }
}
```

---

### Step 6: Repeat for Chengdu

```javascript
// Search Chengdu hotels (March 4-6)
const chengduSearch = await search_hotels({
  location: "Chengdu, China",
  check_in: "2026-03-04",
  check_out: "2026-03-06",
  guests: 2,
  rooms: 1,
  min_price: 100,
  max_price: 150,
  rating_min: 4,
  sort_by: "rating"
});

// Filter by amenities
const chengduFiltered = await filter_by_facilities({
  search_id: chengduSearch.search_id,
  facilities: ["wifi", "breakfast"]
});

// Select top result
// Chengdu Jinjiang Hotel
// - Price: $115/night
// - Rating: 4.5 stars (8.7/10)
// - Location: Jinjiang District, near metro
```

Result:
```json
{
  "day": 4,
  "accommodation": {
    "name": "Chengdu Jinjiang Hotel",
    "location": "88 Hongxing Road, Jinjiang District, Chengdu",
    "cost": 115,
    "type": "Hotel",
    "amenities": ["Free WiFi", "Breakfast included", "Airport shuttle"],
    "notes": "Near metro Line 2, 15min to Tianfu Square"
  }
}
```

---

### Step 7: Repeat for Shanghai

```javascript
// Search Shanghai hotels (March 6-8)
const shanghaiSearch = await search_hotels({
  location: "Shanghai, China",
  check_in: "2026-03-06",
  check_out: "2026-03-08",
  guests: 2,
  rooms: 1,
  min_price: 100,
  max_price: 150,
  rating_min: 4,
  sort_by: "rating"
});

// Filter by amenities
const shanghaiFiltered = await filter_by_facilities({
  search_id: shanghaiSearch.search_id,
  facilities: ["wifi", "breakfast"]
});

// Select top result
// Shanghai Bund View Hotel
// - Price: $145/night
// - Rating: 4.7 stars (9.1/10)
// - Location: Near the Bund, river view
```

Result:
```json
{
  "day": 6,
  "accommodation": {
    "name": "Shanghai Bund View Hotel",
    "location": "123 Zhongshan Road, Huangpu District, Shanghai",
    "cost": 145,
    "type": "Hotel",
    "amenities": ["Free WiFi", "Breakfast buffet", "River view", "Gym"],
    "notes": "5min walk to the Bund, metro nearby"
  }
}
```

---

## Final Output

Save to `data/beijing-chengdu-shanghai/accommodation.json`:

```json
{
  "agent": "accommodation",
  "status": "complete",
  "data": {
    "days": [
      {
        "day": 1,
        "accommodation": {
          "name": "Beijing Central Hotel",
          "location": "2 Dongcheng District, Beijing, 2km from Forbidden City",
          "cost": 128,
          "type": "Hotel",
          "amenities": ["Free WiFi", "Breakfast buffet", "Gym", "Pool"],
          "notes": "Check-in: 14:00, Check-out: 12:00, Free cancellation"
        }
      },
      {
        "day": 4,
        "accommodation": {
          "name": "Chengdu Jinjiang Hotel",
          "location": "88 Hongxing Road, Jinjiang District, Chengdu",
          "cost": 115,
          "type": "Hotel",
          "amenities": ["Free WiFi", "Breakfast included", "Airport shuttle"],
          "notes": "Near metro Line 2, 15min to Tianfu Square"
        }
      },
      {
        "day": 6,
        "accommodation": {
          "name": "Shanghai Bund View Hotel",
          "location": "123 Zhongshan Road, Huangpu District, Shanghai",
          "cost": 145,
          "type": "Hotel",
          "amenities": ["Free WiFi", "Breakfast buffet", "River view", "Gym"],
          "notes": "5min walk to the Bund, metro nearby"
        }
      }
    ]
  },
  "notes": "All hotels within budget ($100-150), high ratings (4.5+), include WiFi and breakfast. Total accommodation cost: $906 for 7 nights."
}
```

---

## Error Handling Example

If Jinko Hotel API unavailable:

```javascript
try {
  const hotels = await search_hotels({
    location: "Beijing, China",
    check_in: "2026-03-01",
    check_out: "2026-03-04",
    min_price: 100,
    max_price: 150
  });
} catch (error) {
  console.warn("Jinko Hotel API unavailable, falling back to WebSearch");

  // Fallback to WebSearch
  const webResults = await WebSearch({
    query: "hotels in Beijing China $100-150 per night WiFi breakfast included site:booking.com OR site:hotels.com",
    allowed_domains: ["booking.com", "hotels.com", "agoda.com"]
  });

  // Parse WebSearch results manually
  // Extract hotel names, prices, ratings from search results
}
```

---

## Performance Optimization

**Parallel searches** (if processing multiple cities):

```javascript
// Search all cities in parallel
const [beijingResults, chengduResults, shanghaiResults] = await Promise.all([
  search_hotels({
    location: "Beijing, China",
    check_in: "2026-03-01",
    check_out: "2026-03-04",
    min_price: 100,
    max_price: 150,
    rating_min: 4
  }),
  search_hotels({
    location: "Chengdu, China",
    check_in: "2026-03-04",
    check_out: "2026-03-06",
    min_price: 100,
    max_price: 150,
    rating_min: 4
  }),
  search_hotels({
    location: "Shanghai, China",
    check_in: "2026-03-06",
    check_out: "2026-03-08",
    min_price: 100,
    max_price: 150,
    rating_min: 4
  })
]);

// Then filter each in parallel
const [beijingFiltered, chengduFiltered, shanghaiFiltered] = await Promise.all([
  filter_by_facilities({
    search_id: beijingResults.search_id,
    facilities: ["wifi", "breakfast"]
  }),
  filter_by_facilities({
    search_id: chengduResults.search_id,
    facilities: ["wifi", "breakfast"]
  }),
  filter_by_facilities({
    search_id: shanghaiResults.search_id,
    facilities: ["wifi", "breakfast"]
  })
]);
```

This reduces total API call time from ~6 seconds (sequential) to ~2 seconds (parallel).

---

## Key Takeaways

1. **Progressive loading**: Load only needed tool categories (`search` vs `details` vs `booking`)
2. **Filter progressively**: Search first, then filter by facilities to narrow results
3. **Validate selectively**: Get full details only for top candidates
4. **Handle errors gracefully**: Fall back to WebSearch if MCP unavailable
5. **Optimize for performance**: Use parallel API calls when processing multiple locations
6. **Structure data consistently**: Follow accommodation.json schema for integration
