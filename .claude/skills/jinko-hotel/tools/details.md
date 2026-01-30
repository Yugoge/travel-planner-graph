# Jinko Hotel - Details and Reviews Tools

Comprehensive hotel information, room types, and guest reviews for detailed comparison.

## MCP Tools

### Tool 1: get_hotel_details

**MCP Tool Name**: `mcp__context7_jinko-hotel__get_hotel_details`

Get comprehensive hotel information including amenities, policies, photos, and contact details.

**Parameters**:
- `hotel_id` (required, string): Hotel unique identifier from search results
- `check_in` (optional, string): Check-in date for pricing context (YYYY-MM-DD)
- `check_out` (optional, string): Check-out date for pricing context (YYYY-MM-DD)

**Returns**:
- `hotel` (object): Complete hotel information
  - `id` (string): Hotel identifier
  - `name` (string): Hotel name
  - `address` (string): Full address
  - `location` (object): Coordinates {lat, lng}
  - `rating` (number): Star rating (1-5)
  - `description` (string): Hotel description
  - `amenities` (array): Full list of amenities and facilities
  - `policies` (object):
    - `check_in_time` (string): Check-in time
    - `check_out_time` (string): Check-out time
    - `cancellation_policy` (string): Cancellation terms
    - `deposit_required` (boolean): Whether deposit needed
    - `pets_allowed` (boolean): Pet policy
  - `contact` (object):
    - `phone` (string): Phone number
    - `email` (string): Email address
    - `website` (string): Hotel website
  - `photos` (array): Photo URLs
  - `nearby_attractions` (array): POIs within 2km

**Example**:
```javascript
// Get full details for shortlisted hotel
const details = await mcp__context7_jinko_hotel__get_hotel_details({
  hotel_id: "hotel_12345",
  check_in: "2026-03-01",
  check_out: "2026-03-04"
});

// Extract key information
console.log(`${details.hotel.name}`);
console.log(`Check-in: ${details.hotel.policies.check_in_time}`);
console.log(`Cancellation: ${details.hotel.policies.cancellation_policy}`);
console.log(`Amenities: ${details.hotel.amenities.join(", ")}`);
```

**Use Cases**:
- Get complete information for shortlisted hotels (top 2-3)
- Verify policies before recommending (check-in time, cancellation)
- Extract nearby attractions for itinerary planning
- Validate amenities match user requirements
- Get contact information for special requests

**Best Practices**:

1. **Selective Loading** (only for top candidates):
```javascript
// Don't load details for all search results (wasteful)
// BAD:
for (const hotel of searchResults.hotels) {
  const details = await get_hotel_details({ hotel_id: hotel.id });
}

// GOOD: Only get details for top 3
const topHotels = searchResults.hotels.slice(0, 3);
for (const hotel of topHotels) {
  const details = await get_hotel_details({ hotel_id: hotel.id });
}
```

2. **Policy Validation**:
```javascript
const details = await get_hotel_details({ hotel_id: hotelId });

// Check critical policies
if (details.hotel.policies.check_in_time > "16:00") {
  console.warn("Late check-in time - verify with user schedule");
}

if (!details.hotel.policies.cancellation_policy.includes("free")) {
  console.warn("Non-refundable - confirm booking commitment");
}
```

---

### Tool 2: get_room_types

**MCP Tool Name**: `mcp__context7_jinko-hotel__get_room_types`

Get available room types with pricing, occupancy, and bed configuration.

**Parameters**:
- `hotel_id` (required, string): Hotel identifier
- `check_in` (required, string): Check-in date (YYYY-MM-DD)
- `check_out` (required, string): Check-out date (YYYY-MM-DD)
- `guests` (optional, number): Number of guests (default: 2)

**Returns**:
- `rooms` (array): Available room types
  - `room_id` (string): Room type identifier
  - `name` (string): Room name/type
  - `description` (string): Room description
  - `size_sqm` (number): Room size in square meters
  - `max_occupancy` (number): Maximum guests
  - `bed_type` (string): Bed configuration (e.g., "1 King", "2 Queens")
  - `price_per_night` (number): Price in USD
  - `total_price` (number): Total for stay
  - `amenities` (array): Room-specific amenities
  - `photos` (array): Room photo URLs
  - `available_count` (number): Rooms available

**Example**:
```javascript
// Get room options for 2 guests
const rooms = await mcp__context7_jinko_hotel__get_room_types({
  hotel_id: "hotel_12345",
  check_in: "2026-04-10",
  check_out: "2026-04-12",
  guests: 2
});

// Find best room option
const bestRoom = rooms.rooms
  .filter(r => r.max_occupancy >= 2)
  .sort((a, b) => a.price_per_night - b.price_per_night)[0];

console.log(`Best option: ${bestRoom.name} - $${bestRoom.price_per_night}/night`);
console.log(`Total for stay: $${bestRoom.total_price}`);
console.log(`Bed: ${bestRoom.bed_type}`);
```

**Use Cases**:
- Find room matching guest count and budget
- Compare room types within same hotel
- Identify best value room option
- Verify bed configuration for families
- Check room-specific amenities (balcony, ocean view, etc.)

**Best Practices**:

1. **Match Guest Count**:
```javascript
async function selectBestRoom(hotelId, checkIn, checkOut, guestCount, maxBudget) {
  const rooms = await get_room_types({
    hotel_id: hotelId,
    check_in: checkIn,
    check_out: checkOut,
    guests: guestCount
  });

  // Filter by occupancy and budget
  const suitable = rooms.rooms.filter(r =>
    r.max_occupancy >= guestCount &&
    r.price_per_night <= maxBudget
  );

  // Sort by value (best rating per dollar)
  return suitable.sort((a, b) => a.price_per_night - b.price_per_night)[0];
}
```

2. **Family Room Selection**:
```javascript
// For families, prioritize bed configuration
const rooms = await get_room_types({
  hotel_id: hotelId,
  check_in: checkIn,
  check_out: checkOut,
  guests: 4
});

// Prefer rooms with multiple beds
const familyFriendly = rooms.rooms.filter(r =>
  r.bed_type.includes("2 ") ||  // 2 beds
  r.bed_type.includes("Bunk") ||
  r.max_occupancy >= 4
);
```

---

### Tool 3: get_reviews

**MCP Tool Name**: `mcp__context7_jinko-hotel__get_reviews`

Get guest reviews with ratings, categories, and helpfulness scores.

**Parameters**:
- `hotel_id` (required, string): Hotel identifier
- `limit` (optional, number): Number of reviews to retrieve (default: 10)
- `sort_by` (optional, string): Sort order - "recent", "helpful", "rating_high", "rating_low"
- `filter_rating` (optional, number): Filter by minimum rating (1-5)

**Returns**:
- `reviews` (array): Guest reviews
  - `review_id` (string): Review identifier
  - `rating` (number): Overall rating (1-5)
  - `title` (string): Review title
  - `content` (string): Review text
  - `author` (string): Reviewer name
  - `date` (string): Review date (ISO 8601)
  - `verified_stay` (boolean): Whether stay was verified
  - `categories` (object): Category ratings
    - `cleanliness` (number): 1-5
    - `staff` (number): 1-5
    - `location` (number): 1-5
    - `value` (number): 1-5
    - `facilities` (number): 1-5
  - `helpful_count` (number): Upvotes/helpful marks
  - `room_type` (string): Room stayed in
- `summary` (object): Aggregate statistics
  - `total_reviews` (number): Total review count
  - `average_rating` (number): Overall average
  - `category_averages` (object): Average by category

**Example**:
```javascript
// Get recent reviews
const reviews = await mcp__context7_jinko_hotel__get_reviews({
  hotel_id: "hotel_12345",
  limit: 20,
  sort_by: "recent"
});

// Analyze review sentiment
console.log(`Average rating: ${reviews.summary.average_rating}/5`);
console.log(`Total reviews: ${reviews.summary.total_reviews}`);
console.log(`Cleanliness: ${reviews.summary.category_averages.cleanliness}/5`);

// Extract common themes
reviews.reviews.forEach(r => {
  if (r.rating >= 4) {
    console.log(`Positive: ${r.title}`);
  } else {
    console.log(`Concern: ${r.title}`);
  }
});
```

**Use Cases**:
- Validate hotel quality through guest feedback
- Identify common issues or concerns
- Verify specific amenities work well (WiFi, breakfast, etc.)
- Check recent reviews for current condition
- Assess value for money through review analysis

**Best Practices**:

1. **Focus on Recent Reviews**:
```javascript
// Get recent reviews (last 6 months)
const recent = await get_reviews({
  hotel_id: hotelId,
  limit: 30,
  sort_by: "recent"
});

// Filter to last 6 months
const sixMonthsAgo = new Date();
sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

const currentReviews = recent.reviews.filter(r =>
  new Date(r.date) >= sixMonthsAgo
);

// Check if recent reviews show declining quality
const recentAvg = currentReviews.reduce((sum, r) => sum + r.rating, 0) / currentReviews.length;
if (recentAvg < recent.summary.average_rating - 0.5) {
  console.warn("Recent reviews show quality decline");
}
```

2. **Extract Insights**:
```javascript
async function analyzeReviews(hotelId) {
  const reviews = await get_reviews({
    hotel_id: hotelId,
    limit: 50,
    sort_by: "helpful"
  });

  // Analyze category strengths and weaknesses
  const categories = reviews.summary.category_averages;

  const strengths = Object.entries(categories)
    .filter(([_, rating]) => rating >= 4.5)
    .map(([category, _]) => category);

  const concerns = Object.entries(categories)
    .filter(([_, rating]) => rating < 3.5)
    .map(([category, _]) => category);

  return {
    strengths,
    concerns,
    overall: reviews.summary.average_rating,
    total_reviews: reviews.summary.total_reviews
  };
}
```

3. **Verify Amenity Quality**:
```javascript
// Check if specific amenity is mentioned positively
const reviews = await get_reviews({ hotel_id: hotelId, limit: 30 });

const wifiMentions = reviews.reviews.filter(r =>
  r.content.toLowerCase().includes("wifi") ||
  r.content.toLowerCase().includes("internet")
);

const positiveWifi = wifiMentions.filter(r => r.rating >= 4).length;
const negativeWifi = wifiMentions.filter(r => r.rating < 3).length;

if (negativeWifi > positiveWifi) {
  console.warn("WiFi quality concerns in reviews");
}
```

---

## Best Practices

### 1. Selective Details Loading

**Only load details for top candidates** (typically top 2-3 from search results):

```javascript
// Step 1: Search and filter
const searchResults = await search_hotels({...});
const filtered = await filter_by_facilities({...});

// Step 2: Select top 3 by rating
const topHotels = filtered.hotels
  .sort((a, b) => b.rating - a.rating)
  .slice(0, 3);

// Step 3: Get details only for top 3
const detailedHotels = await Promise.all(
  topHotels.map(hotel => get_hotel_details({
    hotel_id: hotel.id,
    check_in: checkIn,
    check_out: checkOut
  }))
);
```

### 2. Comprehensive Comparison

**Combine details, rooms, and reviews for complete picture**:

```javascript
async function getComprehensiveHotelInfo(hotelId, checkIn, checkOut, guests) {
  // Load all info in parallel
  const [details, rooms, reviews] = await Promise.all([
    get_hotel_details({ hotel_id: hotelId, check_in: checkIn, check_out: checkOut }),
    get_room_types({ hotel_id: hotelId, check_in: checkIn, check_out: checkOut, guests }),
    get_reviews({ hotel_id: hotelId, limit: 20, sort_by: "recent" })
  ]);

  // Find best room option
  const bestRoom = rooms.rooms
    .filter(r => r.max_occupancy >= guests)
    .sort((a, b) => a.price_per_night - b.price_per_night)[0];

  return {
    name: details.hotel.name,
    address: details.hotel.address,
    rating: details.hotel.rating,
    amenities: details.hotel.amenities,
    policies: details.hotel.policies,
    bestRoom: {
      name: bestRoom.name,
      price: bestRoom.price_per_night,
      total: bestRoom.total_price,
      beds: bestRoom.bed_type
    },
    reviews: {
      average: reviews.summary.average_rating,
      total: reviews.summary.total_reviews,
      categories: reviews.summary.category_averages
    }
  };
}
```

### 3. Data Validation

**Validate critical information before presenting**:

```javascript
async function validateHotel(hotelId, checkIn, checkOut, requirements) {
  const details = await get_hotel_details({ hotel_id: hotelId, check_in: checkIn, check_out: checkOut });
  const reviews = await get_reviews({ hotel_id: hotelId, limit: 10, sort_by: "recent" });

  const validations = {
    checkInTime: details.hotel.policies.check_in_time <= requirements.latestCheckIn,
    cancellation: details.hotel.policies.cancellation_policy.includes("free"),
    recentRating: reviews.summary.average_rating >= requirements.minRating,
    amenitiesPresent: requirements.amenities.every(a =>
      details.hotel.amenities.includes(a)
    )
  };

  const isValid = Object.values(validations).every(v => v);

  if (!isValid) {
    console.warn("Hotel validation failed:", validations);
  }

  return isValid;
}
```

---

## Integration with Search Tools

**Typical workflow combining search and details**:

```javascript
// Phase 1: Search and Filter (broad)
const searchResults = await search_hotels({
  location: "Paris, France",
  check_in: "2026-06-15",
  check_out: "2026-06-18",
  min_price: 100,
  max_price: 200,
  rating_min: 4
});

const filtered = await filter_by_facilities({
  search_id: searchResults.search_id,
  facilities: ["wifi", "breakfast"]
});

// Phase 2: Select Top Candidates (narrow to 3)
const topCandidates = filtered.hotels
  .sort((a, b) => b.rating - a.rating)
  .slice(0, 3);

// Phase 3: Get Details for Final Decision
const detailedInfo = await Promise.all(
  topCandidates.map(async hotel => {
    const [details, rooms, reviews] = await Promise.all([
      get_hotel_details({ hotel_id: hotel.id }),
      get_room_types({ hotel_id: hotel.id, check_in: "2026-06-15", check_out: "2026-06-18", guests: 2 }),
      get_reviews({ hotel_id: hotel.id, limit: 15, sort_by: "recent" })
    ]);

    return {
      hotelId: hotel.id,
      name: hotel.name,
      price: hotel.price,
      rating: hotel.rating,
      details,
      bestRoom: rooms.rooms[0],
      reviewSummary: reviews.summary
    };
  })
);

// Phase 4: Select Winner
const winner = detailedInfo
  .sort((a, b) => {
    // Custom scoring: 40% price, 30% rating, 30% reviews
    const scoreA = (200 - a.price) * 0.4 + a.rating * 20 * 0.3 + a.reviewSummary.average_rating * 20 * 0.3;
    const scoreB = (200 - b.price) * 0.4 + b.rating * 20 * 0.3 + b.reviewSummary.average_rating * 20 * 0.3;
    return scoreB - scoreA;
  })[0];

console.log(`Selected: ${winner.name} - $${winner.price}/night - ${winner.rating} stars`);
```

---

**Next**: Use `/jinko-hotel booking` to load booking link and availability tools.
