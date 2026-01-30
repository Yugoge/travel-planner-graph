# Jinko Hotel - Booking Tools

Booking link generation and availability checking tools.

## Available Tools

### 1. generate_booking_link

Generate booking URL for selected hotel and room.

**MCP Tool**: `generate_booking_link`

**Parameters**:
- `hotel_id` (required): Hotel ID from search results
- `room_type_id` (optional): Specific room type ID
- `check_in` (required): Check-in date (ISO 8601)
- `check_out` (required): Check-out date (ISO 8601)
- `guests` (required): Number of guests
- `rooms` (optional): Number of rooms (default: 1)
- `affiliate_id` (optional): Affiliate tracking ID

**Returns**:
- Booking URL (deep link to hotel booking page)
- Price summary
- Booking terms
- Expiration time (link validity)

**Example**:
```javascript
// Generate booking link for selected hotel
generate_booking_link({
  hotel_id: "hotel_beijing_123",
  room_type_id: "deluxe_double",
  check_in: "2026-03-01",
  check_out: "2026-03-06",
  guests: 2,
  rooms: 1
})
```

**Use Cases**:
- Provide direct booking URL to users
- Track affiliate commissions
- Generate shareable links
- Preserve pricing in link

---

### 2. check_availability

Check real-time availability for specific dates.

**MCP Tool**: `check_availability`

**Parameters**:
- `hotel_id` (required): Hotel ID from search results
- `check_in` (required): Check-in date (ISO 8601)
- `check_out` (required): Check-out date (ISO 8601)
- `rooms` (optional): Number of rooms (default: 1)

**Returns**:
- Availability status (available, limited, unavailable)
- Available room count
- Price per night
- Total price
- Restrictions (minimum stay, maximum stay)

**Example**:
```javascript
// Check if hotel available for dates
check_availability({
  hotel_id: "hotel_beijing_123",
  check_in: "2026-03-01",
  check_out: "2026-03-06",
  rooms: 2
})
```

**Use Cases**:
- Verify availability before presenting option
- Check multi-room availability
- Validate date restrictions

---

### 3. compare_prices

Compare prices across different booking platforms.

**MCP Tool**: `compare_prices`

**Parameters**:
- `hotel_id` (required): Hotel ID from search results
- `check_in` (required): Check-in date (ISO 8601)
- `check_out` (required): Check-out date (ISO 8601)
- `room_type_id` (optional): Specific room type

**Returns**:
- Platform name (Booking.com, Expedia, Hotels.com, etc.)
- Price per night
- Total price
- Included amenities
- Cancellation policy
- Booking link

**Example**:
```javascript
// Compare prices across platforms
compare_prices({
  hotel_id: "hotel_beijing_123",
  check_in: "2026-03-01",
  check_out: "2026-03-06",
  room_type_id: "standard_double"
})
```

**Use Cases**:
- Find best price for hotel
- Compare cancellation policies
- Identify platform-specific deals

---

## Best Practices

### 1. Availability Checking

**Validate before presenting**:
```javascript
async function validateHotelAvailability(hotelId, checkIn, checkOut, rooms) {
  const availability = await check_availability({
    hotel_id: hotelId,
    check_in: checkIn,
    check_out: checkOut,
    rooms: rooms
  });

  if (availability.status === "unavailable") {
    console.warn(`Hotel ${hotelId} unavailable for requested dates`);
    return false;
  }

  if (availability.status === "limited" && availability.available_rooms < rooms) {
    console.warn(`Only ${availability.available_rooms} rooms available, requested ${rooms}`);
    return false;
  }

  return true;
}
```

### 2. Price Comparison

**Find best deal**:
```javascript
async function findBestPrice(hotelId, checkIn, checkOut, roomTypeId) {
  const prices = await compare_prices({
    hotel_id: hotelId,
    check_in: checkIn,
    check_out: checkOut,
    room_type_id: roomTypeId
  });

  // Sort by total price
  const sorted = prices.platforms.sort((a, b) => a.total_price - b.total_price);

  // Consider cancellation policy in selection
  const bestWithFreeCancellation = sorted.find(p => p.cancellation_policy === "free");

  return {
    cheapest: sorted[0],
    recommended: bestWithFreeCancellation || sorted[0],
    all: sorted
  };
}
```

### 3. Booking Link Generation

**Generate with context**:
```javascript
async function generateBookingWithContext(hotel, roomType, dates, guests) {
  // Verify availability first
  const available = await check_availability({
    hotel_id: hotel.id,
    check_in: dates.check_in,
    check_out: dates.check_out,
    rooms: 1
  });

  if (available.status !== "available") {
    throw new Error("Hotel not available for selected dates");
  }

  // Generate link with tracking
  const link = await generate_booking_link({
    hotel_id: hotel.id,
    room_type_id: roomType.id,
    check_in: dates.check_in,
    check_out: dates.check_out,
    guests: guests,
    rooms: 1,
    affiliate_id: process.env.AFFILIATE_ID  // Never hardcode
  });

  return {
    url: link.url,
    price: link.price_summary.total,
    valid_until: link.expiration_time,
    terms: link.booking_terms
  };
}
```

### 4. Error Handling

**Handle booking errors**:
```javascript
async function generateBookingLinkWithFallback(params) {
  try {
    const link = await generate_booking_link(params);
    return link;
  } catch (error) {
    if (error.status === 404) {
      // Hotel or room no longer available
      console.error("Hotel or room type unavailable");
      throw new Error("Selected accommodation is no longer available");
    }
    if (error.status === 400) {
      // Invalid parameters (dates, guest count, etc.)
      console.error("Invalid booking parameters:", error.message);
      throw new Error("Invalid booking details - please check dates and guest count");
    }
    if (error.status === 429) {
      // Rate limit - retry after delay
      await sleep(2000);
      return await generate_booking_link(params);
    }
    // Fall back to manual hotel search URL
    console.warn("Booking link generation failed, providing search URL");
    return {
      url: generateManualSearchURL(params),
      price_summary: { total: null },
      booking_terms: "Please search manually for this hotel",
      expiration_time: null
    };
  }
}

function generateManualSearchURL(params) {
  // Fallback: Generate Google search URL for hotel
  const hotelName = encodeURIComponent(params.hotel_name || params.hotel_id);
  const location = encodeURIComponent(params.location || "");
  return `https://www.google.com/search?q=${hotelName}+${location}+hotel+booking`;
}
```

### 5. Price Validation

**Verify price consistency**:
```javascript
function validatePriceConsistency(searchPrice, bookingPrice) {
  const tolerance = 0.1; // 10% tolerance for price differences

  const priceDiff = Math.abs(searchPrice - bookingPrice);
  const priceDiffPercent = priceDiff / searchPrice;

  if (priceDiffPercent > tolerance) {
    console.warn(
      `Price mismatch: search=${searchPrice}, booking=${bookingPrice} ` +
      `(${(priceDiffPercent * 100).toFixed(1)}% difference)`
    );
    return false;
  }

  return true;
}
```

### 6. Link Expiration Handling

**Track link validity**:
```javascript
function checkLinkExpiration(link) {
  if (!link.expiration_time) {
    // No expiration - likely valid for 24h
    return { valid: true, hours_remaining: 24 };
  }

  const now = new Date();
  const expiration = new Date(link.expiration_time);
  const hoursRemaining = (expiration - now) / (1000 * 60 * 60);

  if (hoursRemaining <= 0) {
    return { valid: false, hours_remaining: 0 };
  }

  if (hoursRemaining < 1) {
    console.warn(`Booking link expires soon: ${hoursRemaining.toFixed(1)}h remaining`);
  }

  return { valid: true, hours_remaining: hoursRemaining };
}
```

## Integration with Accommodation Agent

The accommodation agent should:

1. **Use check_availability** to verify hotel is bookable for dates
2. **Use compare_prices** to find best deal (optional, if time permits)
3. **Use generate_booking_link** to provide booking URL to user
4. **Validate price consistency** between search and booking
5. **Handle errors gracefully** with fallback to manual search

Example workflow:
```
1. Hotel selected from search: hotel_id="beijing_hotel_123"
2. Invoke /jinko-hotel booking (loads this file)
3. Call check_availability({ hotel_id: "beijing_hotel_123", check_in: "2026-03-01", check_out: "2026-03-06", rooms: 1 })
4. Verify: status="available", available_rooms >= 1
5. Call generate_booking_link({ hotel_id: "beijing_hotel_123", check_in: "2026-03-01", check_out: "2026-03-06", guests: 2, rooms: 1 })
6. Validate: price matches search results (within 10% tolerance)
7. Save booking URL to accommodation.json notes
8. Return complete
```

**Note**: The accommodation agent may skip booking link generation during automated planning to save API calls. Generate links only when user requests booking URLs.
