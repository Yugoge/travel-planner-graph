# Jinko Hotel - Search Tools

Hotel search and filtering tools for finding accommodations worldwide.

## Available Tools

### 1. search_hotels

Search hotels by location, dates, and preferences.

**MCP Tool**: `search_hotels`

**Parameters**:
- `location` (required): City, address, or landmark (e.g., "Beijing", "Times Square, New York", "Eiffel Tower")
- `check_in` (required): Check-in date (ISO 8601 format: "2026-02-15")
- `check_out` (required): Check-out date (ISO 8601 format: "2026-02-20")
- `guests` (optional): Number of guests (default: 2)
- `rooms` (optional): Number of rooms (default: 1)
- `min_price` (optional): Minimum price per night (USD)
- `max_price` (optional): Maximum price per night (USD)
- `rating_min` (optional): Minimum rating (1-5 stars)
- `sort_by` (optional): Sort order
  - `price_low`: Lowest price first (default)
  - `price_high`: Highest price first
  - `rating`: Highest rating first
  - `distance`: Closest to location first

**Returns**:
- Hotel list with:
  - Hotel name
  - Location/address
  - Price per night (USD)
  - Star rating
  - Guest rating (1-10)
  - Distance from search location
  - Thumbnail image
  - Availability status

**Example**:
```javascript
// Search hotels in Beijing for 5 nights
search_hotels({
  location: "Beijing, China",
  check_in: "2026-03-01",
  check_out: "2026-03-06",
  guests: 2,
  rooms: 1,
  max_price: 150,
  rating_min: 4,
  sort_by: "rating"
})
```

**Use Cases**:
- Find accommodations for travel dates
- Compare hotel options by price and rating
- Search near specific landmarks or addresses
- Filter by budget constraints

---

### 2. filter_by_facilities

Filter hotel search results by facilities and amenities.

**MCP Tool**: `filter_by_facilities`

**Parameters**:
- `search_id` (required): ID from previous search_hotels call
- `facilities` (required): Array of facility filters
  - `wifi`: Free WiFi
  - `parking`: Free parking
  - `pool`: Swimming pool
  - `gym`: Fitness center
  - `spa`: Spa/wellness center
  - `restaurant`: On-site restaurant
  - `breakfast`: Breakfast included
  - `airport_shuttle`: Airport shuttle service
  - `pet_friendly`: Pets allowed
  - `accessible`: Wheelchair accessible
  - `family_rooms`: Family rooms available
  - `non_smoking`: Non-smoking rooms
  - `ac`: Air conditioning
  - `kitchen`: Kitchenette/kitchen

**Returns**:
- Filtered hotel list matching all specified facilities
- Each hotel includes facility availability status
- Updated result count

**Example**:
```javascript
// Filter for hotels with WiFi, parking, and breakfast
filter_by_facilities({
  search_id: "search_abc123",
  facilities: ["wifi", "parking", "breakfast"]
})
```

**Use Cases**:
- Narrow results by required amenities
- Find hotels meeting specific needs (business travel, family vacation)
- Ensure essential facilities are available

---

### 3. search_nearby

Search hotels near a specific point of interest or address.

**MCP Tool**: `search_nearby`

**Parameters**:
- `poi` (required): Point of interest or landmark (e.g., "Forbidden City", "Central Park")
- `radius` (optional): Search radius in kilometers (default: 5)
- `check_in` (required): Check-in date (ISO 8601)
- `check_out` (required): Check-out date (ISO 8601)
- `max_results` (optional): Maximum number of results (default: 20)

**Returns**:
- Hotels sorted by distance from POI
- Walking distance and time
- Transportation options to POI
- Hotel details (price, rating, facilities)

**Example**:
```javascript
// Find hotels near Forbidden City in Beijing
search_nearby({
  poi: "Forbidden City, Beijing",
  radius: 3,
  check_in: "2026-03-01",
  check_out: "2026-03-06",
  max_results: 10
})
```

**Use Cases**:
- Stay near major attractions
- Find hotels close to conference venues
- Minimize travel time to key locations

---

## Best Practices

### 1. Date Formatting

Always use ISO 8601 format for dates:
```javascript
// Correct
check_in: "2026-03-15"
check_out: "2026-03-20"

// Incorrect
check_in: "03/15/2026"
check_out: "March 20, 2026"
```

### 2. Price Range Strategy

**Budget travelers**:
```javascript
max_price: 80  // Set ceiling only
rating_min: 3  // Accept lower ratings for budget
```

**Mid-range travelers**:
```javascript
min_price: 80
max_price: 200
rating_min: 4
```

**Luxury travelers**:
```javascript
min_price: 200  // Set floor only
rating_min: 4.5
sort_by: "rating"
```

### 3. Facility Filtering

**Progressive filtering**:
```javascript
// Step 1: Initial search
const results = await search_hotels({
  location: "Tokyo",
  check_in: "2026-04-01",
  check_out: "2026-04-05"
});

// Step 2: Filter by essential facilities
const filtered = await filter_by_facilities({
  search_id: results.search_id,
  facilities: ["wifi", "breakfast"]
});

// Step 3: Further filter if too many results
if (filtered.count > 10) {
  const finalResults = await filter_by_facilities({
    search_id: results.search_id,
    facilities: ["wifi", "breakfast", "gym", "pool"]
  });
}
```

### 4. Error Handling

**Retry logic for transient errors**:
```javascript
async function searchWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_hotels(params);
    } catch (error) {
      if (error.status === 429) {
        // Rate limit - exponential backoff
        await sleep(2000 * Math.pow(2, i));
        continue;
      }
      if (error.status >= 500) {
        // Server error - retry with backoff
        await sleep(1000 * (i + 1));
        continue;
      }
      // Permanent error - don't retry
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Fallback to WebSearch**:
```javascript
try {
  const hotels = await search_hotels(params);
  return formatHotelData(hotels);
} catch (error) {
  console.warn('Jinko Hotel API unavailable, falling back to WebSearch');
  return await webSearchHotels(params.location, params.check_in, params.check_out);
}
```

### 5. Response Parsing

**Extract hotel data**:
```javascript
function parseHotelResults(response) {
  return response.hotels.map(hotel => ({
    name: hotel.name,
    location: hotel.address || hotel.location,
    cost: hotel.price_per_night,
    type: hotel.property_type || "Hotel",
    amenities: extractAmenities(hotel.facilities),
    rating: hotel.guest_rating,
    star_rating: hotel.star_rating,
    notes: buildNotes(hotel)
  }));
}

function extractAmenities(facilities) {
  const amenityMap = {
    wifi: "Free WiFi",
    parking: "Free parking",
    breakfast: "Breakfast included",
    pool: "Swimming pool",
    gym: "Fitness center"
  };

  return facilities
    .filter(f => f.available)
    .map(f => amenityMap[f.name] || f.name);
}

function buildNotes(hotel) {
  const notes = [];

  if (hotel.check_in_time) {
    notes.push(`Check-in: ${hotel.check_in_time}`);
  }

  if (hotel.check_out_time) {
    notes.push(`Check-out: ${hotel.check_out_time}`);
  }

  if (hotel.distance_from_center) {
    notes.push(`${hotel.distance_from_center}km from city center`);
  }

  if (hotel.cancellation_policy === "free") {
    notes.push("Free cancellation");
  } else if (hotel.cancellation_policy === "non_refundable") {
    notes.push("Non-refundable");
  }

  return notes.join(", ");
}
```

### 6. Multi-Location Searches

For trips with multiple locations, search each separately:
```javascript
const locations = [
  { city: "Beijing", nights: 3 },
  { city: "Chengdu", nights: 2 },
  { city: "Shanghai", nights: 2 }
];

const accommodations = [];

for (const loc of locations) {
  const checkIn = calculateDate(loc.startDate);
  const checkOut = calculateDate(loc.startDate, loc.nights);

  const hotels = await search_hotels({
    location: loc.city,
    check_in: checkIn,
    check_out: checkOut,
    max_price: 150,
    rating_min: 4
  });

  // Pick best hotel based on rating and price
  const bestHotel = hotels.hotels
    .filter(h => h.guest_rating >= 8)
    .sort((a, b) => b.guest_rating - a.guest_rating)[0];

  accommodations.push({
    location: loc.city,
    hotel: bestHotel,
    nights: loc.nights
  });
}
```

## Integration with Accommodation Agent

The accommodation agent should:

1. **Load this file** when processing accommodation requirements
2. **Use search_hotels** with location, dates, and budget constraints
3. **Use filter_by_facilities** to match user requirements (WiFi, breakfast, etc.)
4. **Use search_nearby** if user wants to stay near specific attractions
5. **Parse response** for name, location, cost, amenities, rating
6. **Validate** that selected hotel meets all requirements
7. **Save structured data** to `accommodation.json`
8. **Fall back to WebSearch** if MCP unavailable

Example workflow:
```
1. Read requirements: Beijing, 3 nights, budget $100-150, need WiFi + breakfast
2. Invoke /jinko-hotel search (loads this file)
3. Call search_hotels({ location: "Beijing", check_in: "2026-03-01", check_out: "2026-03-04", min_price: 100, max_price: 150, rating_min: 4 })
4. Call filter_by_facilities({ search_id: result.search_id, facilities: ["wifi", "breakfast"] })
5. Select best hotel by rating
6. Parse: name="Beijing Hotel", cost=120, amenities=["Free WiFi", "Breakfast included", "Gym"]
7. Save to accommodation.json
8. Return complete
```
