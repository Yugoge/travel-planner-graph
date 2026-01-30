# Example: Multi-City Hotel Search Workflow

Complete end-to-end example demonstrating Jinko Hotel skill usage for a 7-day trip across three cities.

## Scenario

**Trip**: Beijing → Chengdu → Shanghai (March 1-7, 2026)
**Travelers**: 2 adults
**Budget**: $100-150/night
**Requirements**: Free WiFi, breakfast included, 4+ star rating

## Step 1: Load Search Tools

```
/jinko-hotel search
```

This loads: `search_hotels`, `filter_by_facilities`, `search_nearby`

## Step 2: Search Hotels in All Cities (Parallel)

```javascript
// Search all three cities in parallel for performance
const [beijing, chengdu, shanghai] = await Promise.all([
  mcp__context7_jinko_hotel__search_hotels({
    location: "Beijing, China",
    check_in: "2026-03-01",
    check_out: "2026-03-03",
    guests: 2,
    rooms: 1,
    min_price: 100,
    max_price: 150,
    rating_min: 4,
    sort_by: "rating"
  }),
  mcp__context7_jinko_hotel__search_hotels({
    location: "Chengdu, China",
    check_in: "2026-03-03",
    check_out: "2026-03-05",
    guests: 2,
    rooms: 1,
    min_price: 100,
    max_price: 150,
    rating_min: 4,
    sort_by: "rating"
  }),
  mcp__context7_jinko_hotel__search_hotels({
    location: "Shanghai, China",
    check_in: "2026-03-05",
    check_out: "2026-03-07",
    guests: 2,
    rooms: 1,
    min_price: 100,
    max_price: 150,
    rating_min: 4,
    sort_by: "rating"
  })
]);

console.log(`Beijing: ${beijing.total_results} hotels found`);
console.log(`Chengdu: ${chengdu.total_results} hotels found`);
console.log(`Shanghai: ${shanghai.total_results} hotels found`);
```

**Output**:
```
Beijing: 47 hotels found
Chengdu: 32 hotels found
Shanghai: 59 hotels found
```

## Step 3: Filter by Required Amenities

```javascript
// Filter each city for WiFi and breakfast
const [beijingFiltered, chengduFiltered, shanghaiFiltered] = await Promise.all([
  mcp__context7_jinko_hotel__filter_by_facilities({
    search_id: beijing.search_id,
    facilities: ["wifi", "breakfast"]
  }),
  mcp__context7_jinko_hotel__filter_by_facilities({
    search_id: chengdu.search_id,
    facilities: ["wifi", "breakfast"]
  }),
  mcp__context7_jinko_hotel__filter_by_facilities({
    search_id: shanghai.search_id,
    facilities: ["wifi", "breakfast"]
  })
]);

console.log(`Beijing: ${beijingFiltered.filtered_count} hotels with WiFi and breakfast`);
console.log(`Chengdu: ${chengduFiltered.filtered_count} hotels with WiFi and breakfast`);
console.log(`Shanghai: ${shanghaiFiltered.filtered_count} hotels with WiFi and breakfast`);
```

**Output**:
```
Beijing: 23 hotels with WiFi and breakfast
Chengdu: 18 hotels with WiFi and breakfast
Shanghai: 31 hotels with WiFi and breakfast
```

## Step 4: Select Top Hotel Per City

```javascript
// Select best hotel by rating for each city
const beijingTop = beijingFiltered.hotels
  .sort((a, b) => b.rating - a.rating)[0];

const chengduTop = chengduFiltered.hotels
  .sort((a, b) => b.rating - a.rating)[0];

const shanghaiTop = shanghaiFiltered.hotels
  .sort((a, b) => b.rating - a.rating)[0];

console.log("Selected hotels:");
console.log(`Beijing: ${beijingTop.name} - $${beijingTop.price}/night - ${beijingTop.rating} stars`);
console.log(`Chengdu: ${chengduTop.name} - $${chengduTop.price}/night - ${chengduTop.rating} stars`);
console.log(`Shanghai: ${shanghaiTop.name} - $${shanghaiTop.price}/night - ${shanghaiTop.rating} stars`);
```

**Output**:
```
Selected hotels:
Beijing: Grand Hyatt Beijing - $145/night - 4.8 stars
Chengdu: The Ritz-Carlton Chengdu - $135/night - 4.7 stars
Shanghai: The Langham Shanghai - $148/night - 4.9 stars
```

## Step 5: Load Details Tools and Validate

```
/jinko-hotel details
```

This loads: `get_hotel_details`, `get_room_types`, `get_reviews`

```javascript
// Get comprehensive details for all three hotels (parallel)
const [beijingDetails, chengduDetails, shanghaiDetails] = await Promise.all([
  Promise.all([
    mcp__context7_jinko_hotel__get_hotel_details({
      hotel_id: beijingTop.id,
      check_in: "2026-03-01",
      check_out: "2026-03-03"
    }),
    mcp__context7_jinko_hotel__get_reviews({
      hotel_id: beijingTop.id,
      limit: 15,
      sort_by: "recent"
    })
  ]),
  Promise.all([
    mcp__context7_jinko_hotel__get_hotel_details({
      hotel_id: chengduTop.id,
      check_in: "2026-03-03",
      check_out: "2026-03-05"
    }),
    mcp__context7_jinko_hotel__get_reviews({
      hotel_id: chengduTop.id,
      limit: 15,
      sort_by: "recent"
    })
  ]),
  Promise.all([
    mcp__context7_jinko_hotel__get_hotel_details({
      hotel_id: shanghaiTop.id,
      check_in: "2026-03-05",
      check_out: "2026-03-07"
    }),
    mcp__context7_jinko_hotel__get_reviews({
      hotel_id: shanghaiTop.id,
      limit: 15,
      sort_by: "recent"
    })
  ])
]);

// Extract details and reviews
const [beijingHotel, beijingReviews] = beijingDetails;
const [chengduHotel, chengduReviews] = chengduDetails;
const [shanghaiHotel, shanghaiReviews] = shanghaiDetails;

// Validate policies
console.log("Beijing check-in:", beijingHotel.hotel.policies.check_in_time);
console.log("Chengdu check-in:", chengduHotel.hotel.policies.check_in_time);
console.log("Shanghai check-in:", shanghaiHotel.hotel.policies.check_in_time);

// Validate reviews
console.log("Beijing reviews:", beijingReviews.summary.average_rating, `(${beijingReviews.summary.total_reviews} reviews)`);
console.log("Chengdu reviews:", chengduReviews.summary.average_rating, `(${chengduReviews.summary.total_reviews} reviews)`);
console.log("Shanghai reviews:", shanghaiReviews.summary.average_rating, `(${shanghaiReviews.summary.total_reviews} reviews)`);
```

**Output**:
```
Beijing check-in: 14:00
Chengdu check-in: 15:00
Shanghai check-in: 14:00

Beijing reviews: 4.7 (1,234 reviews)
Chengdu reviews: 4.6 (987 reviews)
Shanghai reviews: 4.8 (2,156 reviews)
```

## Step 6: Load Booking Tools and Check Availability

```
/jinko-hotel booking
```

This loads: `generate_booking_link`, `check_availability`, `compare_prices`

```javascript
// Check availability for all hotels
const [beijingAvail, chengduAvail, shanghaiAvail] = await Promise.all([
  mcp__context7_jinko_hotel__check_availability({
    hotel_id: beijingTop.id,
    check_in: "2026-03-01",
    check_out: "2026-03-03"
  }),
  mcp__context7_jinko_hotel__check_availability({
    hotel_id: chengduTop.id,
    check_in: "2026-03-03",
    check_out: "2026-03-05"
  }),
  mcp__context7_jinko_hotel__check_availability({
    hotel_id: shanghaiTop.id,
    check_in: "2026-03-05",
    check_out: "2026-03-07"
  })
]);

// Verify all are available
if (!beijingAvail.available || !chengduAvail.available || !shanghaiAvail.available) {
  console.error("One or more hotels unavailable - need to select alternatives");
} else {
  console.log("✓ All hotels available");
}
```

**Output**:
```
✓ All hotels available
```

## Step 7: Generate Booking Links

```javascript
// Get room options and generate booking links
const [beijingRooms, chengduRooms, shanghaiRooms] = await Promise.all([
  mcp__context7_jinko_hotel__get_room_types({
    hotel_id: beijingTop.id,
    check_in: "2026-03-01",
    check_out: "2026-03-03",
    guests: 2
  }),
  mcp__context7_jinko_hotel__get_room_types({
    hotel_id: chengduTop.id,
    check_in: "2026-03-03",
    check_out: "2026-03-05",
    guests: 2
  }),
  mcp__context7_jinko_hotel__get_room_types({
    hotel_id: shanghaiTop.id,
    check_in: "2026-03-05",
    check_out: "2026-03-07",
    guests: 2
  })
]);

// Select best room (lowest price)
const beijingRoom = beijingRooms.rooms.sort((a, b) => a.price_per_night - b.price_per_night)[0];
const chengduRoom = chengduRooms.rooms.sort((a, b) => a.price_per_night - b.price_per_night)[0];
const shanghaiRoom = shanghaiRooms.rooms.sort((a, b) => a.price_per_night - b.price_per_night)[0];

// Generate booking links
const [beijingLink, chengduLink, shanghaiLink] = await Promise.all([
  mcp__context7_jinko_hotel__generate_booking_link({
    hotel_id: beijingTop.id,
    room_id: beijingRoom.room_id,
    check_in: "2026-03-01",
    check_out: "2026-03-03",
    guests: 2
  }),
  mcp__context7_jinko_hotel__generate_booking_link({
    hotel_id: chengduTop.id,
    room_id: chengduRoom.room_id,
    check_in: "2026-03-03",
    check_out: "2026-03-05",
    guests: 2
  }),
  mcp__context7_jinko_hotel__generate_booking_link({
    hotel_id: shanghaiTop.id,
    room_id: shanghaiRoom.room_id,
    check_in: "2026-03-05",
    check_out: "2026-03-07",
    guests: 2
  })
]);

console.log("Booking links generated:");
console.log(`Beijing: ${beijingLink.booking_url}`);
console.log(`Chengdu: ${chengduLink.booking_url}`);
console.log(`Shanghai: ${shanghaiLink.booking_url}`);
```

## Step 8: Format for accommodation.json

```javascript
const accommodationData = {
  agent: "accommodation",
  status: "complete",
  data: {
    days: [
      // Day 1: Beijing (March 1)
      {
        day: 1,
        accommodation: {
          name: beijingTop.name,
          location: beijingHotel.hotel.address,
          cost: beijingTop.price,
          type: "Hotel",
          amenities: ["Free WiFi", "Breakfast buffet", "Gym", "Pool", "Business center"],
          notes: `Check-in: ${beijingHotel.hotel.policies.check_in_time}, ${beijingHotel.hotel.policies.cancellation_policy}, ${beijingRoom.bed_type}, ${beijingReviews.summary.average_rating} stars (${beijingReviews.summary.total_reviews} reviews), Book: ${beijingLink.booking_url}`
        }
      },
      // Day 2: Beijing (March 2)
      {
        day: 2,
        accommodation: {
          name: beijingTop.name,
          location: beijingHotel.hotel.address,
          cost: beijingTop.price,
          type: "Hotel",
          amenities: ["Free WiFi", "Breakfast buffet", "Gym", "Pool", "Business center"],
          notes: "Same as Day 1"
        }
      },
      // Day 3: Chengdu (March 3)
      {
        day: 3,
        accommodation: {
          name: chengduTop.name,
          location: chengduHotel.hotel.address,
          cost: chengduTop.price,
          type: "Hotel",
          amenities: ["Free WiFi", "Breakfast included", "Spa", "Restaurant", "Bar"],
          notes: `Check-in: ${chengduHotel.hotel.policies.check_in_time}, ${chengduHotel.hotel.policies.cancellation_policy}, ${chengduRoom.bed_type}, ${chengduReviews.summary.average_rating} stars (${chengduReviews.summary.total_reviews} reviews), Book: ${chengduLink.booking_url}`
        }
      },
      // Day 4: Chengdu (March 4)
      {
        day: 4,
        accommodation: {
          name: chengduTop.name,
          location: chengduHotel.hotel.address,
          cost: chengduTop.price,
          type: "Hotel",
          amenities: ["Free WiFi", "Breakfast included", "Spa", "Restaurant", "Bar"],
          notes: "Same as Day 3"
        }
      },
      // Day 5: Shanghai (March 5)
      {
        day: 5,
        accommodation: {
          name: shanghaiTop.name,
          location: shanghaiHotel.hotel.address,
          cost: shanghaiTop.price,
          type: "Hotel",
          amenities: ["Free WiFi", "Breakfast buffet", "Infinity pool", "Rooftop bar", "Concierge"],
          notes: `Check-in: ${shanghaiHotel.hotel.policies.check_in_time}, ${shanghaiHotel.hotel.policies.cancellation_policy}, ${shanghaiRoom.bed_type}, ${shanghaiReviews.summary.average_rating} stars (${shanghaiReviews.summary.total_reviews} reviews), Book: ${shanghaiLink.booking_url}`
        }
      },
      // Day 6: Shanghai (March 6)
      {
        day: 6,
        accommodation: {
          name: shanghaiTop.name,
          location: shanghaiHotel.hotel.address,
          cost: shanghaiTop.price,
          type: "Hotel",
          amenities: ["Free WiFi", "Breakfast buffet", "Infinity pool", "Rooftop bar", "Concierge"],
          notes: "Same as Day 5"
        }
      }
    ]
  },
  notes: `Total accommodation cost: $${(beijingTop.price * 2 + chengduTop.price * 2 + shanghaiTop.price * 2).toFixed(2)}. All hotels have free WiFi and breakfast included. Booking links valid for 24 hours.`
};

// Save to file
await writeFile(
  '/root/travel-planner/data/beijing-chengdu-shanghai-2026/accommodation.json',
  JSON.stringify(accommodationData, null, 2)
);

console.log("✓ Accommodation data saved to accommodation.json");
```

## Step 9: Error Handling and Fallback

```javascript
// Error handling example
async function searchHotelsWithFallback(location, checkIn, checkOut, params) {
  try {
    // Try Jinko Hotel MCP
    const results = await mcp__context7_jinko_hotel__search_hotels({
      location,
      check_in: checkIn,
      check_out: checkOut,
      ...params
    });
    return results;
  } catch (error) {
    console.warn(`Jinko Hotel MCP error: ${error.message}`);
    console.log("Falling back to WebSearch...");

    // Fallback to WebSearch
    const webResults = await WebSearch({
      query: `hotels in ${location} ${checkIn} to ${checkOut} ${params.min_price}-${params.max_price} USD`,
      allowed_domains: ["booking.com", "hotels.com", "expedia.com"]
    });

    // Parse web results (simplified)
    return {
      hotels: parseWebSearchResults(webResults),
      source: "websearch"
    };
  }
}
```

## Performance Metrics

**Execution Time**:
- Sequential execution: ~12 seconds
- Parallel execution: ~4 seconds
- **3x speedup** with parallel API calls

**API Calls Made**:
- Search: 3 calls (Beijing, Chengdu, Shanghai)
- Filter: 3 calls
- Details: 3 calls
- Reviews: 3 calls
- Availability: 3 calls
- Room types: 3 calls
- Booking links: 3 calls
- **Total**: 21 API calls

**Token Usage**:
- SKILL.md loaded: ~800 tokens
- tools/search.md: ~2,500 tokens
- tools/details.md: ~2,000 tokens
- tools/booking.md: ~1,800 tokens
- **Total**: ~7,100 tokens (progressive disclosure)

## Summary

**Completed Workflow**:
1. ✓ Loaded search tools
2. ✓ Searched 3 cities in parallel
3. ✓ Filtered by WiFi and breakfast
4. ✓ Selected top hotel per city by rating
5. ✓ Validated details and reviews
6. ✓ Checked availability
7. ✓ Generated booking links
8. ✓ Formatted accommodation.json
9. ✓ Saved to data directory

**Results**:
- Beijing: Grand Hyatt Beijing - $145/night (2 nights)
- Chengdu: The Ritz-Carlton Chengdu - $135/night (2 nights)
- Shanghai: The Langham Shanghai - $148/night (2 nights)
- **Total**: $856 for 6 nights
- **Average**: $142.67/night

**Quality**:
- All hotels 4+ star rating
- All have WiFi and breakfast
- All within budget ($100-150/night)
- All available for requested dates
- All have booking links ready

---

**This example demonstrates**:
- Progressive disclosure pattern (load tools as needed)
- Parallel API calls for performance
- Complete search → filter → select → validate → book workflow
- Error handling and fallback strategies
- Proper data formatting for accommodation.json
- Integration with accommodation agent workflow
