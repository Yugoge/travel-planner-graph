# Amadeus Flight - Details Tools

Detailed flight and airline information tools.

## MCP Tools

### Tool 1: flight_details

**MCP Tool Name**: `mcp__plugin_amadeus-flight_amadeus-flight__flight_details`

**Description**: Get comprehensive details for a specific flight.

**Parameters**:
- `flight_id` (required, string): Flight ID from search results
- `include_aircraft` (optional, boolean): Include aircraft specifications (default: true)
- `include_amenities` (optional, boolean): Include cabin amenities (default: true)

**Returns**:
```json
{
  "flight_id": "flight_id",
  "carrier": {
    "code": "AF",
    "name": "Air France",
    "alliance": "SkyTeam"
  },
  "aircraft": {
    "code": "77W",
    "name": "Boeing 777-300ER",
    "specifications": {
      "seats_total": 381,
      "seats_economy": 266,
      "seats_premium_economy": 40,
      "seats_business": 58,
      "seats_first": 17,
      "range_km": 13649,
      "speed_kmh": 905
    }
  },
  "route": {
    "origin": {
      "iata": "PEK",
      "city": "Beijing",
      "country": "China",
      "terminal": "3"
    },
    "destination": {
      "iata": "CDG",
      "city": "Paris",
      "country": "France",
      "terminal": "2E"
    }
  },
  "schedule": {
    "departure_time": "09:30",
    "arrival_time": "14:00",
    "duration": "PT10H30M",
    "frequency": "Daily",
    "on_time_performance": 0.87
  },
  "amenities": {
    "wifi": true,
    "power_outlets": true,
    "entertainment": "Seatback IFE with 1000+ options",
    "meals": "Complimentary meals and beverages",
    "seat_pitch_cm": 79
  },
  "baggage": {
    "checked": {
      "pieces": 2,
      "weight_kg": 23,
      "max_dimensions_cm": "158 linear"
    },
    "cabin": {
      "pieces": 1,
      "weight_kg": 12,
      "max_dimensions_cm": "55x35x25"
    }
  }
}
```

**Use Cases**:
- Get aircraft specifications
- Check cabin amenities before booking
- Verify baggage allowance details
- Compare on-time performance
- Research specific flight details

**Example Usage**:
```javascript
// Get full flight details
flight_details({
  flight_id: "AF382_20260215",
  include_aircraft: true,
  include_amenities: true
})
```

---

### Tool 2: seat_availability

**MCP Tool Name**: `mcp__plugin_amadeus-flight_amadeus-flight__seat_availability`

**Description**: Check seat and cabin availability for a flight.

**Parameters**:
- `flight_id` (required, string): Flight ID from search results
- `cabin_class` (optional, string): Specific cabin class to check

**Returns**:
```json
{
  "flight_id": "flight_id",
  "availability": {
    "economy": {
      "available": true,
      "seats_remaining": 47,
      "booking_classes": [
        {
          "class": "Y",
          "available": true,
          "seats": 20
        },
        {
          "class": "B",
          "available": true,
          "seats": 15
        },
        {
          "class": "M",
          "available": true,
          "seats": 12
        }
      ]
    },
    "premium_economy": {
      "available": true,
      "seats_remaining": 12
    },
    "business": {
      "available": true,
      "seats_remaining": 8,
      "booking_classes": [
        {
          "class": "J",
          "available": true,
          "seats": 5
        },
        {
          "class": "C",
          "available": true,
          "seats": 3
        }
      ]
    },
    "first": {
      "available": false,
      "seats_remaining": 0
    }
  },
  "seat_map_available": true,
  "advance_seat_selection": true
}
```

**Use Cases**:
- Check availability before booking
- Verify specific cabin class has seats
- Determine booking class options
- Plan upgrade possibilities
- Check if seat selection available

**Example Usage**:
```javascript
// Check all cabin availability
seat_availability({
  flight_id: "AF382_20260215"
})

// Check specific cabin
seat_availability({
  flight_id: "AF382_20260215",
  cabin_class: "BUSINESS"
})
```

---

## Best Practices

### Flight Details

**When to use**:
- User specifically asks about aircraft type
- Amenities are important decision factors
- Long-haul flights where comfort matters
- Comparing similar-priced options
- Accessibility requirements need verification

**Information to highlight**:
- Aircraft type for comfort level
- Seat pitch for legroom assessment
- WiFi availability for business travelers
- Entertainment options for long flights
- On-time performance for reliability

### Seat Availability

**When to use**:
- Limited seats available in search results
- Planning group travel (need multiple seats)
- Considering cabin upgrade
- Booking close to departure date
- Premium cabin consideration

**Interpretation**:
- <10 seats: Book immediately, high demand
- 10-30 seats: Moderate availability
- >30 seats: Good availability
- 0 seats: Check alternative flights or dates

### Booking Classes

**Understanding Codes**:
- **Economy**: Y (full fare), B, M, H, Q, K (discount tiers)
- **Premium Economy**: W, E
- **Business**: J (full fare), C, D, I, Z (discount tiers)
- **First**: F (full fare), A, P

**Why it matters**:
- Higher booking class = more flexibility
- Affects upgrade eligibility
- Impacts earned frequent flyer miles
- Cancellation/change policies vary

## Integration with Search Tools

**Recommended Workflow**:

1. **Search flights** using `search_flights`
2. **Review results**, identify top 2-3 options
3. **Get details** for selected flights using `flight_details`
4. **Check availability** using `seat_availability`
5. **Compare** based on price, duration, amenities, availability
6. **Select optimal** flight for recommendation

**Example Integration**:
```javascript
// 1. Search flights
const flights = await search_flights({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-02-15",
  adults: 2
});

// 2. Get top 3 results
const topFlights = flights.flights.slice(0, 3);

// 3. Get details for each
const detailedFlights = await Promise.all(
  topFlights.map(f => flight_details({ flight_id: f.id }))
);

// 4. Check availability
const availability = await Promise.all(
  topFlights.map(f => seat_availability({ flight_id: f.id }))
);

// 5. Compare and select
const selected = compareAndSelect(detailedFlights, availability);
```

## Error Handling

### Common Errors

**Flight Not Found**:
```json
{
  "error": "not_found",
  "message": "Flight ID 'invalid_id' not found"
}
```
**Solution**: Verify flight_id from search results, check for typos

**Details Unavailable**:
```json
{
  "error": "data_unavailable",
  "message": "Aircraft details not available for this flight"
}
```
**Solution**: Continue without detailed specs, use basic info from search

**Stale Data**:
```json
{
  "error": "outdated",
  "message": "Flight data is more than 24 hours old"
}
```
**Solution**: Re-run search to get fresh results

### Retry Logic

Same as search tools:
- 3 attempts with exponential backoff
- Log errors for debugging
- Fall back to search results data if details unavailable
- Document partial data in output

## Performance Optimization

**Caching Strategy**:
- Cache flight details for 24 hours (static data)
- Cache seat availability for 1 hour (dynamic data)
- Invalidate cache if booking made

**Selective Loading**:
- Only load details for top 3 search results
- Skip amenities if not requested by user
- Use batch requests if API supports

**Response Time**:
- Flight details: ~500ms
- Seat availability: ~300ms
- Total (with search): ~1-2 seconds

## Data Accuracy

**Reliability by Data Type**:
- Aircraft type: 99% accurate (static)
- Schedule: 95% accurate (seasonal changes)
- Amenities: 90% accurate (aircraft swaps)
- Seat availability: 85% accurate (real-time changes)
- On-time performance: Historical average, reference only

**Always verify**:
- Seat availability at booking time
- Baggage allowance in booking confirmation
- Schedule changes before departure
- Terminal information (subject to change)

## Output Structure for Agent

**When integrating with transportation agent**:

```json
{
  "transportation": "Flight - Air France AF382",
  "aircraft": "Boeing 777-300ER",
  "amenities": {
    "wifi": true,
    "entertainment": true,
    "seat_pitch_cm": 79
  },
  "reliability": {
    "on_time_performance": 0.87,
    "recommendation": "Highly reliable route"
  },
  "seat_availability": {
    "economy": 47,
    "business": 8,
    "recommendation": "Good availability, book soon"
  },
  "notes": "Long-haul flight with full amenities, good on-time record"
}
```

## Cost Considerations

- Details API typically included in search cost
- Seat availability may be separate API call
- Minimize calls by batching requests
- Cache static data (aircraft specs, amenities)
- Only fetch details for shortlisted flights

---

**See also**:
- `search.md` for flight search tools
- `../examples/flight-search.md` for complete workflow
