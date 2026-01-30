# Jinko Hotel - Details Tools

Hotel information and details retrieval tools.

## Available Tools

### 1. get_hotel_details

Get comprehensive hotel information including rooms, amenities, policies, and reviews.

**MCP Tool**: `get_hotel_details`

**Parameters**:
- `hotel_id` (required): Hotel ID from search results
- `check_in` (optional): Check-in date for pricing (ISO 8601)
- `check_out` (optional): Check-out date for pricing (ISO 8601)

**Returns**:
- Hotel name and location
- Full address and coordinates
- Star rating and guest rating
- Complete amenities list
- Room types and pricing
- Photos (URLs)
- Hotel description
- Policies (check-in/out times, cancellation, pets, etc.)
- Guest reviews summary
- Contact information

**Example**:
```javascript
// Get details for specific hotel
get_hotel_details({
  hotel_id: "hotel_beijing_123",
  check_in: "2026-03-01",
  check_out: "2026-03-06"
})
```

**Use Cases**:
- Verify hotel quality before booking
- Check detailed amenities and services
- Review cancellation policies
- Get contact information

---

### 2. get_room_types

Get available room types, pricing, and occupancy details.

**MCP Tool**: `get_room_types`

**Parameters**:
- `hotel_id` (required): Hotel ID from search results
- `check_in` (required): Check-in date (ISO 8601)
- `check_out` (required): Check-out date (ISO 8601)
- `guests` (optional): Number of guests (default: 2)

**Returns**:
- Room type name (Standard, Deluxe, Suite, etc.)
- Price per night
- Total price for stay
- Maximum occupancy
- Bed configuration
- Room size (sqm)
- Room amenities
- Availability status
- Cancellation policy

**Example**:
```javascript
// Get room options for family of 4
get_room_types({
  hotel_id: "hotel_beijing_123",
  check_in: "2026-03-01",
  check_out: "2026-03-06",
  guests: 4
})
```

**Use Cases**:
- Compare room options within hotel
- Find rooms matching guest count
- Check pricing differences
- Verify room amenities

---

### 3. get_reviews

Get guest reviews and ratings.

**MCP Tool**: `get_reviews`

**Parameters**:
- `hotel_id` (required): Hotel ID from search results
- `sort_by` (optional): Sort order
  - `recent`: Most recent first (default)
  - `rating_high`: Highest rating first
  - `rating_low`: Lowest rating first
  - `helpful`: Most helpful first
- `limit` (optional): Maximum reviews to return (default: 10)
- `language` (optional): Filter by language (e.g., "en", "zh")

**Returns**:
- Review text
- Rating (1-10)
- Review date
- Reviewer name/country
- Stay date
- Room type
- Helpfulness score
- Review categories (cleanliness, location, service, etc.)

**Example**:
```javascript
// Get recent English reviews
get_reviews({
  hotel_id: "hotel_beijing_123",
  sort_by: "recent",
  limit: 20,
  language: "en"
})
```

**Use Cases**:
- Check guest feedback quality
- Identify common issues
- Verify service quality
- Read recent experiences

---

## Best Practices

### 1. Details Retrieval Strategy

**Selective loading**:
```javascript
// Step 1: Search and filter
const hotels = await search_hotels({ location: "Beijing", ... });
const filtered = await filter_by_facilities({ facilities: ["wifi", "breakfast"] });

// Step 2: Get details only for top candidates (don't fetch all)
const topHotels = filtered.hotels.slice(0, 3);

for (const hotel of topHotels) {
  const details = await get_hotel_details({
    hotel_id: hotel.id,
    check_in: params.check_in,
    check_out: params.check_out
  });

  // Analyze details to make final selection
  if (meetsAllCriteria(details)) {
    return details;
  }
}
```

### 2. Room Selection

**Match guest count**:
```javascript
function selectBestRoom(rooms, guestCount, budget) {
  // Filter by occupancy
  const suitable = rooms.filter(r => r.max_occupancy >= guestCount);

  // Filter by budget
  const affordable = suitable.filter(r => r.price_per_night <= budget);

  // Sort by value (space per dollar)
  return affordable.sort((a, b) => {
    const valueA = a.size_sqm / a.price_per_night;
    const valueB = b.size_sqm / b.price_per_night;
    return valueB - valueA;
  })[0];
}
```

### 3. Review Analysis

**Extract insights**:
```javascript
function analyzeReviews(reviews) {
  const insights = {
    averageRating: 0,
    commonPraises: [],
    commonComplaints: [],
    recentTrend: null
  };

  // Calculate average
  insights.averageRating = reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length;

  // Analyze recent trend (last 10 vs previous 10)
  const recent = reviews.slice(0, 10);
  const previous = reviews.slice(10, 20);

  const recentAvg = recent.reduce((sum, r) => sum + r.rating, 0) / recent.length;
  const previousAvg = previous.reduce((sum, r) => sum + r.rating, 0) / previous.length;

  if (recentAvg > previousAvg + 0.5) {
    insights.recentTrend = "improving";
  } else if (recentAvg < previousAvg - 0.5) {
    insights.recentTrend = "declining";
  } else {
    insights.recentTrend = "stable";
  }

  // Extract common themes (simplified - use NLP in production)
  const positiveKeywords = ["clean", "friendly", "excellent", "great", "comfortable"];
  const negativeKeywords = ["dirty", "rude", "poor", "noisy", "small"];

  reviews.forEach(review => {
    const text = review.text.toLowerCase();
    positiveKeywords.forEach(kw => {
      if (text.includes(kw) && !insights.commonPraises.includes(kw)) {
        insights.commonPraises.push(kw);
      }
    });
    negativeKeywords.forEach(kw => {
      if (text.includes(kw) && !insights.commonComplaints.includes(kw)) {
        insights.commonComplaints.push(kw);
      }
    });
  });

  return insights;
}
```

### 4. Policy Extraction

**Build notes from policies**:
```javascript
function buildPolicyNotes(details) {
  const notes = [];

  // Check-in/out times
  if (details.check_in_time) {
    notes.push(`Check-in: ${details.check_in_time}`);
  }
  if (details.check_out_time) {
    notes.push(`Check-out: ${details.check_out_time}`);
  }

  // Cancellation policy
  if (details.cancellation_policy) {
    const policy = details.cancellation_policy;
    if (policy.free_cancellation_until) {
      notes.push(`Free cancellation until ${policy.free_cancellation_until}`);
    } else if (policy.type === "non_refundable") {
      notes.push("Non-refundable");
    }
  }

  // Special requirements
  if (details.policies.age_restriction) {
    notes.push(`Minimum age: ${details.policies.age_restriction}`);
  }

  if (details.policies.deposit_required) {
    notes.push(`Deposit required: ${details.policies.deposit_amount}`);
  }

  // Parking details
  if (details.parking) {
    if (details.parking.free) {
      notes.push("Free parking available");
    } else if (details.parking.available) {
      notes.push(`Parking: ${details.parking.price_per_day}/day`);
    }
  }

  return notes.join("; ");
}
```

### 5. Error Handling

**Handle missing details gracefully**:
```javascript
async function getDetailsWithFallback(hotelId, checkIn, checkOut) {
  try {
    const details = await get_hotel_details({
      hotel_id: hotelId,
      check_in: checkIn,
      check_out: checkOut
    });
    return details;
  } catch (error) {
    if (error.status === 404) {
      // Hotel no longer available
      console.warn(`Hotel ${hotelId} not found - may be unavailable`);
      return null;
    }
    if (error.status === 429) {
      // Rate limit - wait and retry
      await sleep(2000);
      return await get_hotel_details({ hotel_id: hotelId, check_in: checkIn, check_out: checkOut });
    }
    // Fall back to WebSearch
    console.warn('Jinko API unavailable, using WebSearch for hotel details');
    return await webSearchHotelDetails(hotelId);
  }
}
```

### 6. Data Validation

**Verify completeness**:
```javascript
function validateHotelDetails(details) {
  const required = [
    'name',
    'location',
    'price_per_night',
    'guest_rating',
    'amenities'
  ];

  const missing = required.filter(field => !details[field]);

  if (missing.length > 0) {
    console.warn(`Hotel details missing fields: ${missing.join(', ')}`);
    return false;
  }

  // Validate price range
  if (details.price_per_night < 10 || details.price_per_night > 10000) {
    console.warn(`Suspicious price: ${details.price_per_night} USD`);
    return false;
  }

  // Validate rating
  if (details.guest_rating < 1 || details.guest_rating > 10) {
    console.warn(`Invalid rating: ${details.guest_rating}`);
    return false;
  }

  return true;
}
```

## Integration with Accommodation Agent

The accommodation agent should:

1. **Use get_hotel_details** after selecting hotel from search results
2. **Use get_room_types** to verify room availability and pricing
3. **Use get_reviews** to validate hotel quality (optional, for high-priority bookings)
4. **Extract policy information** for user notes
5. **Validate completeness** before saving to accommodation.json

Example workflow:
```
1. Hotel selected from search: hotel_id="beijing_hotel_123"
2. Invoke /jinko-hotel details (loads this file)
3. Call get_hotel_details({ hotel_id: "beijing_hotel_123", check_in: "2026-03-01", check_out: "2026-03-06" })
4. Call get_room_types({ hotel_id: "beijing_hotel_123", check_in: "2026-03-01", check_out: "2026-03-06", guests: 2 })
5. Verify: amenities match requirements, price within budget, rating acceptable
6. Extract notes: check-in time, cancellation policy, parking availability
7. Save to accommodation.json with complete information
8. Return complete
```
