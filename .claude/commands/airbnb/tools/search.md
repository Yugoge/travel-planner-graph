# Airbnb - Search Tools

Vacation rental and apartment search tools for finding accommodation alternatives.

## Available Tools

### 1. search_listings

Search for vacation rentals and apartments by location, dates, and guest count.

**MCP Tool**: `search_listings`

**Parameters**:
- `location` (required): City, neighborhood, or address (e.g., "Paris, France" or "Manhattan, New York")
- `check_in` (required): Check-in date (ISO format: "2026-03-15")
- `check_out` (required): Check-out date (ISO format: "2026-03-20")
- `guests` (required): Number of guests (integer)
- `price_min` (optional): Minimum price per night in USD
- `price_max` (optional): Maximum price per night in USD
- `room_type` (optional): Type of accommodation
  - `entire_place`: Entire home/apartment
  - `private_room`: Private room in shared space
  - `shared_room`: Shared room
- `bedrooms` (optional): Minimum number of bedrooms
- `beds` (optional): Minimum number of beds
- `bathrooms` (optional): Minimum number of bathrooms

**Returns**:
- List of matching listings
- Property name and type
- Price per night (USD)
- Total price for stay
- Guest capacity
- Bedroom/bathroom count
- Superhost status
- Overall rating
- Number of reviews
- Location details
- Thumbnail images

**Example**:
```javascript
// Search for family apartment in Paris
search_listings({
  location: "Paris, France",
  check_in: "2026-06-01",
  check_out: "2026-06-07",
  guests: 4,
  price_max: 200,
  room_type: "entire_place",
  bedrooms: 2
})
```

**Use Cases**:
- Family vacation rentals
- Extended stay accommodations
- Group travel lodging
- Budget-friendly alternatives to hotels

---

### 2. get_listing_details

Get comprehensive details about a specific listing.

**MCP Tool**: `get_listing_details`

**Parameters**:
- `listing_id` (required): Airbnb listing ID (from search results)

**Returns**:
- Full property description
- Complete amenities list
- House rules and policies
- Check-in/check-out instructions
- Cancellation policy
- Cleaning fee
- Service fees
- Security deposit
- Minimum/maximum stay requirements
- Neighborhood description
- Host information
- Exact location (after booking)
- Calendar availability
- Pricing calendar

**Example**:
```javascript
// Get details for specific listing
get_listing_details({
  listing_id: "12345678"
})
```

**Use Cases**:
- Verify amenities before booking
- Understand house rules
- Check cancellation terms
- Review host policies

---

### 3. filter_by_amenities

Filter search results by specific amenities and facilities.

**MCP Tool**: `filter_by_amenities`

**Parameters**:
- `listing_ids` (required): Array of listing IDs to filter
- `amenities` (required): Array of required amenities
  - `wifi`: WiFi internet
  - `kitchen`: Full kitchen
  - `washer`: Washing machine
  - `dryer`: Clothes dryer
  - `air_conditioning`: Air conditioning
  - `heating`: Heating
  - `parking`: Free parking
  - `elevator`: Elevator access
  - `pool`: Swimming pool
  - `gym`: Gym/fitness center
  - `workspace`: Dedicated workspace
  - `tv`: Television
  - `crib`: Baby crib
  - `high_chair`: High chair
  - `pets_allowed`: Pets allowed
  - `smoking_allowed`: Smoking allowed
  - `wheelchair_accessible`: Wheelchair accessible
  - `self_checkin`: Self check-in

**Returns**:
- Filtered list of listings matching all specified amenities
- Amenity availability for each listing

**Example**:
```javascript
// Filter for work-friendly rentals with parking
filter_by_amenities({
  listing_ids: ["12345678", "87654321", "11223344"],
  amenities: ["wifi", "workspace", "parking", "kitchen"]
})
```

**Use Cases**:
- Remote work accommodations
- Family-friendly properties
- Accessible accommodations
- Pet-friendly rentals

---

### 4. get_host_reviews

Get host ratings and property reviews.

**MCP Tool**: `get_host_reviews`

**Parameters**:
- `listing_id` (required): Airbnb listing ID
- `limit` (optional): Maximum number of reviews to retrieve (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Returns**:
- Overall rating (1-5 stars)
- Rating breakdown:
  - Cleanliness
  - Accuracy
  - Communication
  - Location
  - Check-in
  - Value
- Total review count
- Recent reviews (text, date, reviewer)
- Host response rate
- Host response time
- Superhost status
- Years hosting
- Number of listings

**Example**:
```javascript
// Get recent reviews for listing
get_host_reviews({
  listing_id: "12345678",
  limit: 10
})
```

**Use Cases**:
- Verify property quality
- Check host reliability
- Identify potential issues
- Assess value for money

---

## Best Practices

### 1. Location Search

**Specific locations work better**:
- Good: "Montmartre, Paris, France"
- Good: "Lower East Side, Manhattan, New York"
- Weak: "France"
- Weak: "New York"

**Include context for ambiguous locations**:
- "Cambridge, Massachusetts, USA" (not UK)
- "Portland, Oregon, USA" (not Maine)

### 2. Date Selection

**Price optimization**:
- Weekdays are typically cheaper
- Avoid major holidays and events
- Shoulder season (spring/fall) often has best rates
- Weekly/monthly discounts for longer stays

**Availability windows**:
- Book 2-3 months ahead for popular destinations
- Last-minute bookings may have limited options
- Check minimum stay requirements (often 2-7 nights)

### 3. Guest Count Accuracy

**Important for filtering**:
- Some listings have strict guest limits
- Extra guests may incur additional fees
- Children count towards guest limits
- Infants (under 2) often don't count

### 4. Room Type Selection

**Choose based on needs**:
- **Entire place**: Best for families, groups, privacy
- **Private room**: Budget option with shared common areas
- **Shared room**: Most economical, less privacy

### 5. Amenity Filtering Strategy

**Prioritize essential amenities**:
```javascript
// Step 1: Search with broad criteria
const results = await search_listings({
  location: "Tokyo, Japan",
  check_in: "2026-04-01",
  check_out: "2026-04-07",
  guests: 2,
  price_max: 150
});

// Step 2: Filter by required amenities
const filtered = await filter_by_amenities({
  listing_ids: results.map(r => r.listing_id),
  amenities: ["wifi", "washer", "kitchen"]  // Must-haves only
});

// Step 3: Get details for top matches
const details = await Promise.all(
  filtered.slice(0, 3).map(listing =>
    get_listing_details({ listing_id: listing.listing_id })
  )
);
```

### 6. Review Analysis

**Focus on recent reviews**:
```javascript
// Get reviews and analyze patterns
const reviews = await get_host_reviews({
  listing_id: "12345678",
  limit: 20
});

// Check for red flags:
// - Rating drop in recent reviews
// - Complaints about cleanliness
// - Inaccurate listing descriptions
// - Neighborhood safety concerns
// - Unresponsive host

// Green flags:
// - Consistent 5-star ratings
// - Positive cleanliness feedback
// - Accurate listing description
// - Responsive host
// - Superhost status
```

### 7. Price Calculation

**Total cost includes**:
```javascript
function calculateTotalCost(listing, nights) {
  const basePrice = listing.price_per_night * nights;
  const cleaningFee = listing.cleaning_fee || 0;
  const serviceFee = basePrice * 0.14;  // Airbnb service fee ~14%
  const taxes = basePrice * 0.10;  // Estimated taxes ~10%

  return {
    base: basePrice,
    cleaning: cleaningFee,
    service: serviceFee,
    taxes: taxes,
    total: basePrice + cleaningFee + serviceFee + taxes
  };
}
```

### 8. Error Handling

**Retry logic**:
```javascript
async function searchWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_listings(params);
    } catch (error) {
      if (error.status === 429) {
        // Rate limit - exponential backoff
        await sleep(2000 * Math.pow(2, i));
        continue;
      }
      if (error.status >= 500) {
        // Server error - retry
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
  const listings = await search_listings(params);
  return formatListingData(listings);
} catch (error) {
  console.warn('Airbnb MCP unavailable, falling back to WebSearch');
  return await webSearchRentals(params.location, params.check_in, params.check_out);
}
```

### 9. Comparison with Hotels

**When comparing accommodation types**:
```javascript
async function compareAccommodationOptions(location, checkIn, checkOut, guests) {
  // Get Airbnb options
  const airbnbListings = await search_listings({
    location: location,
    check_in: checkIn,
    check_out: checkOut,
    guests: guests,
    room_type: "entire_place"
  });

  // Get hotel options (using jinko-hotel skill)
  const hotelListings = await searchHotels({
    city: location,
    checkin: checkIn,
    checkout: checkOut,
    guests: guests
  });

  // Compare based on criteria
  const nights = calculateNights(checkIn, checkOut);

  const airbnbBest = airbnbListings[0];
  const airbnbTotal = calculateTotalCost(airbnbBest, nights).total;
  const airbnbPerPerson = airbnbTotal / guests;

  const hotelBest = hotelListings[0];
  const hotelTotal = hotelBest.price_per_night * nights;
  const hotelPerPerson = hotelTotal / guests;

  return {
    recommendation: airbnbPerPerson < hotelPerPerson ? 'airbnb' : 'hotel',
    airbnb: {
      name: airbnbBest.name,
      total_cost: airbnbTotal,
      per_person: airbnbPerPerson,
      benefits: ["Full kitchen", "Living space", "Washer/dryer"]
    },
    hotel: {
      name: hotelBest.name,
      total_cost: hotelTotal,
      per_person: hotelPerPerson,
      benefits: ["Daily housekeeping", "Front desk", "Hotel amenities"]
    }
  };
}
```

---

## Integration with Accommodation Agent

The accommodation agent should:

1. **Load this file** when researching vacation rentals
2. **Use search_listings** for initial rental search
3. **Use filter_by_amenities** to match user requirements
4. **Use get_listing_details** for top 2-3 options
5. **Use get_host_reviews** to verify quality
6. **Compare with hotel options** from jinko-hotel skill
7. **Save structured data** to `accommodation.json`
8. **Fall back to WebSearch** if MCP unavailable

Example workflow:
```
1. Read requirements: Family of 4, need kitchen, 5 nights in Paris
2. Invoke /airbnb search (loads this file)
3. Call search_listings({ location: "Paris", guests: 4, bedrooms: 2 })
4. Call filter_by_amenities({ amenities: ["kitchen", "wifi", "washer"] })
5. Call get_listing_details() for top 3 matches
6. Call get_host_reviews() to verify quality
7. Compare with hotel options
8. Save recommendation to accommodation.json
9. Return complete
```

---

## Response Parsing

### Parse Search Results

```javascript
function parseSearchResults(results) {
  return results.listings.map(listing => ({
    id: listing.listing_id,
    name: listing.name,
    type: listing.room_type,
    price_per_night: listing.price_per_night,
    total_price: listing.total_price,
    bedrooms: listing.bedrooms,
    beds: listing.beds,
    bathrooms: listing.bathrooms,
    guests: listing.max_guests,
    rating: listing.rating,
    reviews: listing.review_count,
    superhost: listing.is_superhost,
    location: listing.location,
    amenities: listing.amenities
  }));
}
```

### Parse Listing Details

```javascript
function parseListingDetails(details) {
  return {
    description: details.description,
    amenities: details.amenities,
    house_rules: details.house_rules,
    cancellation_policy: details.cancellation_policy,
    check_in_time: details.check_in_time,
    check_out_time: details.check_out_time,
    min_nights: details.minimum_nights,
    max_nights: details.maximum_nights,
    cleaning_fee: details.cleaning_fee,
    security_deposit: details.security_deposit,
    extra_guest_fee: details.extra_people_fee
  };
}
```

### Parse Reviews

```javascript
function parseReviews(reviews) {
  return {
    overall_rating: reviews.overall_rating,
    rating_breakdown: {
      cleanliness: reviews.cleanliness_rating,
      accuracy: reviews.accuracy_rating,
      communication: reviews.communication_rating,
      location: reviews.location_rating,
      check_in: reviews.checkin_rating,
      value: reviews.value_rating
    },
    total_reviews: reviews.review_count,
    recent_reviews: reviews.reviews.slice(0, 5).map(r => ({
      date: r.created_at,
      rating: r.rating,
      comment: r.comments.substring(0, 200),  // Truncate long reviews
      reviewer: r.reviewer_name
    })),
    host_info: {
      response_rate: reviews.host_response_rate,
      response_time: reviews.host_response_time,
      superhost: reviews.is_superhost
    }
  };
}
```
