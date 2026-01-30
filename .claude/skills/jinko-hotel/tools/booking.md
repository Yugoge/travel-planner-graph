# Jinko Hotel - Booking and Availability Tools

Booking link generation, real-time availability checking, and cross-platform price comparison.

## MCP Tools

### Tool 1: generate_booking_link

**MCP Tool Name**: `mcp__context7_jinko-hotel__generate_booking_link`

Generate booking URL with pricing and availability preserved.

**Parameters**:
- `hotel_id` (required, string): Hotel identifier
- `room_id` (required, string): Room type identifier from get_room_types
- `check_in` (required, string): Check-in date (YYYY-MM-DD)
- `check_out` (required, string): Check-out date (YYYY-MM-DD)
- `guests` (required, number): Number of guests
- `affiliate_id` (optional, string): Affiliate tracking ID

**Returns**:
- `booking_url` (string): Direct booking link
- `price` (number): Guaranteed price in USD
- `currency` (string): Currency code
- `expires_at` (string): Link expiration time (ISO 8601)
- `platform` (string): Booking platform (e.g., "Booking.com", "Expedia", "Direct")
- `confirmation_required` (boolean): Whether email confirmation needed

**Example**:
```javascript
// Generate booking link for selected hotel and room
const bookingLink = await mcp__context7_jinko_hotel__generate_booking_link({
  hotel_id: "hotel_12345",
  room_id: "room_standard_double",
  check_in: "2026-03-15",
  check_out: "2026-03-18",
  guests: 2
});

console.log(`Book here: ${bookingLink.booking_url}`);
console.log(`Price guaranteed: $${bookingLink.price}`);
console.log(`Link expires: ${bookingLink.expires_at}`);
```

**Use Cases**:
- Generate final booking link for user
- Preserve pricing during search-to-booking flow
- Track affiliate conversions
- Provide direct booking option

**Best Practices**:

1. **Link Expiration Handling**:
```javascript
const link = await generate_booking_link({...});

// Check expiration
const expiresIn = new Date(link.expires_at) - new Date();
const hoursUntilExpiry = expiresIn / (1000 * 60 * 60);

if (hoursUntilExpiry < 1) {
  console.warn("Booking link expires soon - regenerate if needed");
}

// Include expiration in user message
console.log(`Link valid for ${hoursUntilExpiry.toFixed(1)} hours`);
```

2. **Price Consistency Check**:
```javascript
// Verify price matches previous quote
const roomInfo = await get_room_types({
  hotel_id: hotelId,
  check_in: checkIn,
  check_out: checkOut
});

const expectedPrice = roomInfo.rooms.find(r => r.room_id === roomId).total_price;

const bookingLink = await generate_booking_link({
  hotel_id: hotelId,
  room_id: roomId,
  check_in: checkIn,
  check_out: checkOut,
  guests: 2
});

if (Math.abs(bookingLink.price - expectedPrice) > 1) {
  console.warn(`Price changed: Was $${expectedPrice}, now $${bookingLink.price}`);
}
```

3. **Fallback for Link Generation Failure**:
```javascript
async function getBookingLink(hotelId, roomId, checkIn, checkOut, guests) {
  try {
    const link = await generate_booking_link({
      hotel_id: hotelId,
      room_id: roomId,
      check_in: checkIn,
      check_out: checkOut,
      guests
    });
    return link.booking_url;
  } catch (error) {
    // Fallback: Manual search URL
    const hotelDetails = await get_hotel_details({ hotel_id: hotelId });
    const manualUrl = `https://www.booking.com/search?ss=${encodeURIComponent(hotelDetails.hotel.name)}&checkin=${checkIn}&checkout=${checkOut}`;
    console.warn("Booking link generation failed, using manual search URL");
    return manualUrl;
  }
}
```

---

### Tool 2: check_availability

**MCP Tool Name**: `mcp__context7_jinko-hotel__check_availability`

Check real-time availability and booking restrictions.

**Parameters**:
- `hotel_id` (required, string): Hotel identifier
- `check_in` (required, string): Check-in date (YYYY-MM-DD)
- `check_out` (required, string): Check-out date (YYYY-MM-DD)
- `room_type` (optional, string): Specific room type to check

**Returns**:
- `available` (boolean): Whether hotel is available
- `rooms_available` (array): List of available room types
  - `room_id` (string): Room identifier
  - `name` (string): Room name
  - `count` (number): Number of rooms available
  - `price` (number): Current price per night
- `restrictions` (object): Booking restrictions
  - `min_stay` (number): Minimum nights required
  - `max_stay` (number): Maximum nights allowed
  - `advance_booking` (number): Minimum days in advance required
  - `sold_out_dates` (array): Dates with no availability
- `last_checked` (string): Timestamp of availability check

**Example**:
```javascript
// Check availability before presenting option
const availability = await mcp__context7_jinko_hotel__check_availability({
  hotel_id: "hotel_12345",
  check_in: "2026-04-20",
  check_out: "2026-04-23"
});

if (!availability.available) {
  console.log("Hotel not available for these dates");
  console.log(`Sold out on: ${availability.restrictions.sold_out_dates.join(", ")}`);
} else {
  console.log(`${availability.rooms_available.length} room types available`);
  availability.rooms_available.forEach(room => {
    console.log(`${room.name}: ${room.count} rooms at $${room.price}/night`);
  });
}
```

**Use Cases**:
- Validate availability before generating booking link
- Check minimum stay requirements
- Identify sold-out dates
- Verify booking timeline (advance booking requirements)
- Get real-time room counts

**Best Practices**:

1. **Pre-Recommendation Validation**:
```javascript
async function recommendHotel(hotelId, checkIn, checkOut) {
  // Always check availability before recommending
  const availability = await check_availability({
    hotel_id: hotelId,
    check_in: checkIn,
    check_out: checkOut
  });

  if (!availability.available) {
    console.warn(`Hotel ${hotelId} not available - skipping`);
    return null;
  }

  // Check minimum stay restriction
  const nights = calculateNights(checkIn, checkOut);
  if (nights < availability.restrictions.min_stay) {
    console.warn(`Hotel requires minimum ${availability.restrictions.min_stay} nights, requested ${nights}`);
    return null;
  }

  // Proceed with recommendation
  const details = await get_hotel_details({ hotel_id: hotelId });
  return details;
}
```

2. **Advance Booking Check**:
```javascript
const availability = await check_availability({
  hotel_id: hotelId,
  check_in: checkIn,
  check_out: checkOut
});

// Calculate days until check-in
const daysUntilCheckIn = (new Date(checkIn) - new Date()) / (1000 * 60 * 60 * 24);

if (daysUntilCheckIn < availability.restrictions.advance_booking) {
  console.warn(`Hotel requires booking ${availability.restrictions.advance_booking} days in advance, only ${daysUntilCheckIn.toFixed(0)} days remaining`);
}
```

3. **Room Count Urgency**:
```javascript
const availability = await check_availability({
  hotel_id: hotelId,
  check_in: checkIn,
  check_out: checkOut
});

// Check low availability
availability.rooms_available.forEach(room => {
  if (room.count <= 2) {
    console.log(`⚠️ Only ${room.count} ${room.name} remaining - book soon!`);
  }
});
```

---

### Tool 3: compare_prices

**MCP Tool Name**: `mcp__context7_jinko-hotel__compare_prices`

Compare prices across booking platforms (Booking.com, Expedia, Hotels.com, etc.).

**Parameters**:
- `hotel_id` (required, string): Hotel identifier
- `check_in` (required, string): Check-in date (YYYY-MM-DD)
- `check_out` (required, string): Check-out date (YYYY-MM-DD)
- `room_type` (optional, string): Specific room type to compare

**Returns**:
- `prices` (array): Prices from different platforms
  - `platform` (string): Platform name (e.g., "Booking.com", "Expedia")
  - `price` (number): Total price for stay
  - `price_per_night` (number): Average per night
  - `currency` (string): Currency code
  - `fees_included` (boolean): Whether all fees are included
  - `cancellation_free` (boolean): Free cancellation available
  - `url` (string): Booking URL on this platform
- `best_deal` (object): Platform with lowest price
- `price_difference` (number): Difference between highest and lowest

**Example**:
```javascript
// Compare prices across platforms
const comparison = await mcp__context7_jinko_hotel__compare_prices({
  hotel_id: "hotel_12345",
  check_in: "2026-05-10",
  check_out: "2026-05-13"
});

console.log("Price comparison:");
comparison.prices.forEach(p => {
  console.log(`${p.platform}: $${p.price} (${p.cancellation_free ? 'Free cancellation' : 'Non-refundable'})`);
});

console.log(`\nBest deal: ${comparison.best_deal.platform} at $${comparison.best_deal.price}`);
console.log(`Save $${comparison.price_difference} vs highest price`);
```

**Use Cases**:
- Find best price for hotel across platforms
- Identify platforms with free cancellation
- Compare total cost including fees
- Provide user with multiple booking options
- Validate pricing consistency

**Best Practices**:

1. **Smart Platform Selection**:
```javascript
async function getBestBookingOption(hotelId, checkIn, checkOut, preferences) {
  const comparison = await compare_prices({
    hotel_id: hotelId,
    check_in: checkIn,
    check_out: checkOut
  });

  // Filter by user preferences
  let options = comparison.prices;

  // Prioritize free cancellation if requested
  if (preferences.freeCancellation) {
    const freeCancellation = options.filter(p => p.cancellation_free);
    if (freeCancellation.length > 0) {
      options = freeCancellation;
    }
  }

  // Prioritize all-inclusive pricing
  if (preferences.allFeesIncluded) {
    const allInclusive = options.filter(p => p.fees_included);
    if (allInclusive.length > 0) {
      options = allInclusive;
    }
  }

  // Return best option after filtering
  return options.sort((a, b) => a.price - b.price)[0];
}
```

2. **Price Validation**:
```javascript
const comparison = await compare_prices({
  hotel_id: hotelId,
  check_in: checkIn,
  check_out: checkOut
});

// Check for suspicious price differences
if (comparison.price_difference > comparison.best_deal.price * 0.2) {
  console.warn(`Large price variance detected: $${comparison.price_difference} difference`);
  console.warn("Verify fees included and cancellation policies");
}

// Validate fees disclosure
const hiddenFees = comparison.prices.filter(p => !p.fees_included);
if (hiddenFees.length > 0) {
  console.log("⚠️ Some platforms have additional fees not shown in price:");
  hiddenFees.forEach(p => console.log(`- ${p.platform}`));
}
```

3. **User-Friendly Presentation**:
```javascript
async function presentPriceComparison(hotelId, checkIn, checkOut) {
  const comparison = await compare_prices({
    hotel_id: hotelId,
    check_in: checkIn,
    check_out: checkOut
  });

  // Sort by price
  const sorted = comparison.prices.sort((a, b) => a.price - b.price);

  // Format output
  console.log("Booking Options (best to worst):");
  sorted.forEach((option, index) => {
    const badge = index === 0 ? "🏆 BEST DEAL" : "";
    const cancellation = option.cancellation_free ? "✓ Free cancellation" : "✗ Non-refundable";
    const fees = option.fees_included ? "All fees included" : "Additional fees may apply";

    console.log(`
${badge}
${option.platform}: $${option.price} total ($${option.price_per_night}/night)
${cancellation} | ${fees}
Book: ${option.url}
    `.trim());
  });

  return sorted[0];  // Return best option
}
```

---

## Best Practices

### Complete Booking Workflow

**End-to-end process from search to booking link**:

```javascript
async function completeBookingWorkflow(location, checkIn, checkOut, guests, budget) {
  // Phase 1: Search
  const searchResults = await search_hotels({
    location,
    check_in: checkIn,
    check_out: checkOut,
    guests,
    max_price: budget,
    rating_min: 4
  });

  // Phase 2: Filter
  const filtered = await filter_by_facilities({
    search_id: searchResults.search_id,
    facilities: ["wifi", "breakfast"]
  });

  // Phase 3: Check availability for top 3
  const topHotels = filtered.hotels.slice(0, 3);
  const availableHotels = [];

  for (const hotel of topHotels) {
    const availability = await check_availability({
      hotel_id: hotel.id,
      check_in: checkIn,
      check_out: checkOut
    });

    if (availability.available) {
      availableHotels.push({
        hotel,
        availability
      });
    }
  }

  if (availableHotels.length === 0) {
    console.log("No available hotels - expand search criteria");
    return null;
  }

  // Phase 4: Compare prices for best available hotel
  const bestHotel = availableHotels[0];
  const priceComparison = await compare_prices({
    hotel_id: bestHotel.hotel.id,
    check_in: checkIn,
    check_out: checkOut
  });

  // Phase 5: Get room options
  const rooms = await get_room_types({
    hotel_id: bestHotel.hotel.id,
    check_in: checkIn,
    check_out: checkOut,
    guests
  });

  const selectedRoom = rooms.rooms.sort((a, b) => a.price_per_night - b.price_per_night)[0];

  // Phase 6: Generate booking link
  const bookingLink = await generate_booking_link({
    hotel_id: bestHotel.hotel.id,
    room_id: selectedRoom.room_id,
    check_in: checkIn,
    check_out: checkOut,
    guests
  });

  // Return complete booking information
  return {
    hotel: bestHotel.hotel,
    room: selectedRoom,
    booking: bookingLink,
    priceComparison: priceComparison.prices,
    bestPrice: priceComparison.best_deal
  };
}
```

### Error Handling for Booking Tools

**Retry and fallback strategies**:

```javascript
async function generateBookingLinkWithRetry(params, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await generate_booking_link(params);
    } catch (error) {
      if (attempt === maxRetries) {
        // Final fallback: manual search URL
        console.warn("Booking link generation failed after retries");
        const hotelDetails = await get_hotel_details({ hotel_id: params.hotel_id });
        return {
          booking_url: `https://www.booking.com/search?ss=${encodeURIComponent(hotelDetails.hotel.name)}`,
          price: null,
          platform: "Manual Search",
          manual: true
        };
      }

      // Exponential backoff
      await sleep(Math.pow(2, attempt) * 1000);
    }
  }
}
```

### Performance Optimization

**Parallel operations for booking workflow**:

```javascript
async function optimizedBookingWorkflow(hotelId, checkIn, checkOut, guests) {
  // Run availability check and price comparison in parallel
  const [availability, priceComparison] = await Promise.all([
    check_availability({ hotel_id: hotelId, check_in: checkIn, check_out: checkOut }),
    compare_prices({ hotel_id: hotelId, check_in: checkIn, check_out: checkOut })
  ]);

  if (!availability.available) {
    console.log("Hotel not available");
    return null;
  }

  // Get room types
  const rooms = await get_room_types({
    hotel_id: hotelId,
    check_in: checkIn,
    check_out: checkOut,
    guests
  });

  // Select best platform from price comparison
  const bestPlatform = priceComparison.best_deal;

  // Generate booking link for best room on best platform
  const bookingLink = await generate_booking_link({
    hotel_id: hotelId,
    room_id: rooms.rooms[0].room_id,
    check_in: checkIn,
    check_out: checkOut,
    guests
  });

  return {
    available: true,
    room: rooms.rooms[0],
    booking: bookingLink,
    alternativePlatforms: priceComparison.prices
  };
}
```

---

## Integration with Search and Details

**Complete hotel selection pipeline**:

```javascript
// 1. Search → 2. Filter → 3. Details → 4. Availability → 5. Price Compare → 6. Book

async function fullHotelPipeline(params) {
  // Step 1: Search
  const search = await search_hotels({
    location: params.location,
    check_in: params.checkIn,
    check_out: params.checkOut,
    guests: params.guests,
    max_price: params.budget
  });

  // Step 2: Filter
  const filtered = await filter_by_facilities({
    search_id: search.search_id,
    facilities: params.requiredAmenities
  });

  // Step 3: Get details for top 3
  const top3 = filtered.hotels.slice(0, 3);
  const withDetails = await Promise.all(
    top3.map(async hotel => {
      const [details, reviews, availability] = await Promise.all([
        get_hotel_details({ hotel_id: hotel.id }),
        get_reviews({ hotel_id: hotel.id, limit: 10 }),
        check_availability({ hotel_id: hotel.id, check_in: params.checkIn, check_out: params.checkOut })
      ]);

      return {
        hotel,
        details,
        reviews: reviews.summary,
        availability
      };
    })
  );

  // Step 4: Filter by availability
  const available = withDetails.filter(h => h.availability.available);

  if (available.length === 0) {
    return { error: "No available hotels" };
  }

  // Step 5: Select best
  const selected = available[0];

  // Step 6: Get pricing and booking
  const [rooms, priceComparison] = await Promise.all([
    get_room_types({
      hotel_id: selected.hotel.id,
      check_in: params.checkIn,
      check_out: params.checkOut,
      guests: params.guests
    }),
    compare_prices({
      hotel_id: selected.hotel.id,
      check_in: params.checkIn,
      check_out: params.checkOut
    })
  ]);

  // Step 7: Generate final booking link
  const bookingLink = await generate_booking_link({
    hotel_id: selected.hotel.id,
    room_id: rooms.rooms[0].room_id,
    check_in: params.checkIn,
    check_out: params.checkOut,
    guests: params.guests
  });

  return {
    hotel: selected.hotel,
    details: selected.details,
    room: rooms.rooms[0],
    reviews: selected.reviews,
    priceOptions: priceComparison.prices,
    booking: bookingLink
  };
}
```

---

**Next**: See `/root/travel-planner/.claude/skills/jinko-hotel/examples/hotel-search.md` for complete workflow example.
