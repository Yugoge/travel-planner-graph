# Example: Complete Flight Search Workflow

This example demonstrates a complete flight search workflow for the transportation agent.

## Scenario

User traveling from Beijing to Paris on February 15, 2026. Need to find optimal flight considering price, duration, and comfort.

## Step-by-Step Workflow

### Step 1: Load Search Tools

```
/amadeus-flight search
```

This loads `.claude/skills/amadeus-flight/tools/search.md` with search tool documentation.

### Step 2: Analyze Price Trends

Before searching, check if current timing is good for booking:

```javascript
// Invoke MCP tool
mcp__plugin_amadeus-flight_amadeus-flight__price_analysis({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-02-15"
})
```

**Response**:
```json
{
  "current_price": 450.00,
  "currency": "USD",
  "price_trend": "stable",
  "recommendations": {
    "booking_window": "2-3 weeks before departure",
    "optimal_days": ["Tuesday", "Wednesday"],
    "price_forecast": "likely_to_increase",
    "confidence": 0.85
  },
  "alerts": {
    "current_deal": false,
    "price_drop_alert": false,
    "peak_season": false
  }
}
```

**Analysis**: Price is stable, recommend booking within 2-3 weeks. Current price around $450 is reasonable.

### Step 3: Search Flights

Search for available flights on the requested date:

```javascript
// Invoke MCP tool
mcp__plugin_amadeus-flight_amadeus-flight__search_flights({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-02-15",
  adults: 2,
  cabin_class: "ECONOMY",
  nonstop: false,
  max_results: 5
})
```

**Response**:
```json
{
  "flights": [
    {
      "id": "AF382_20260215",
      "price": {
        "total": 900.00,
        "currency": "USD",
        "per_adult": 450.00
      },
      "itineraries": [
        {
          "duration": "PT10H30M",
          "segments": [
            {
              "departure": {
                "iata_code": "PEK",
                "terminal": "3",
                "at": "2026-02-15T09:30:00"
              },
              "arrival": {
                "iata_code": "CDG",
                "terminal": "2E",
                "at": "2026-02-15T14:00:00"
              },
              "carrier_code": "AF",
              "flight_number": "382",
              "aircraft": "Boeing 777-300ER",
              "duration": "PT10H30M"
            }
          ]
        }
      ],
      "baggage_allowance": {
        "checked": "2 pieces, 23kg each",
        "cabin": "1 piece, 12kg"
      },
      "cabin_class": "ECONOMY",
      "booking_class": "Y"
    },
    {
      "id": "CA877_20260215",
      "price": {
        "total": 820.00,
        "currency": "USD",
        "per_adult": 410.00
      },
      "itineraries": [
        {
          "duration": "PT11H15M",
          "segments": [
            {
              "departure": {
                "iata_code": "PEK",
                "terminal": "3",
                "at": "2026-02-15T13:20:00"
              },
              "arrival": {
                "iata_code": "CDG",
                "terminal": "1",
                "at": "2026-02-15T18:35:00"
              },
              "carrier_code": "CA",
              "flight_number": "877",
              "aircraft": "Airbus A350-900",
              "duration": "PT11H15M"
            }
          ]
        }
      ],
      "baggage_allowance": {
        "checked": "2 pieces, 23kg each",
        "cabin": "1 piece, 10kg"
      },
      "cabin_class": "ECONOMY",
      "booking_class": "Y"
    },
    {
      "id": "LH723_20260215_CONN",
      "price": {
        "total": 780.00,
        "currency": "USD",
        "per_adult": 390.00
      },
      "itineraries": [
        {
          "duration": "PT14H20M",
          "segments": [
            {
              "departure": {
                "iata_code": "PEK",
                "terminal": "3",
                "at": "2026-02-15T11:10:00"
              },
              "arrival": {
                "iata_code": "FRA",
                "terminal": "1",
                "at": "2026-02-15T15:25:00"
              },
              "carrier_code": "LH",
              "flight_number": "723",
              "aircraft": "Airbus A380-800",
              "duration": "PT10H15M"
            },
            {
              "departure": {
                "iata_code": "FRA",
                "terminal": "1",
                "at": "2026-02-15T19:45:00"
              },
              "arrival": {
                "iata_code": "CDG",
                "terminal": "1",
                "at": "2026-02-15T21:05:00"
              },
              "carrier_code": "LH",
              "flight_number": "1050",
              "aircraft": "Airbus A321",
              "duration": "PT1H20M"
            }
          ]
        }
      ],
      "baggage_allowance": {
        "checked": "2 pieces, 23kg each",
        "cabin": "1 piece, 8kg"
      },
      "cabin_class": "ECONOMY",
      "booking_class": "Y"
    }
  ],
  "meta": {
    "count": 3,
    "currency": "USD"
  }
}
```

### Step 4: Compare Options

**Option 1: Air France AF382**
- Price: $450/person ($900 total)
- Duration: 10h 30m (non-stop)
- Departure: 09:30, Arrival: 14:00 local
- Aircraft: Boeing 777-300ER (modern, comfortable)
- Baggage: 2×23kg checked + 12kg cabin

**Option 2: Air China CA877**
- Price: $410/person ($820 total) - **Cheapest**
- Duration: 11h 15m (non-stop)
- Departure: 13:20, Arrival: 18:35 local
- Aircraft: Airbus A350-900 (newest)
- Baggage: 2×23kg checked + 10kg cabin

**Option 3: Lufthansa LH723 (via Frankfurt)**
- Price: $390/person ($780 total) - **Lowest price**
- Duration: 14h 20m (1 stop, 4h 20m layover)
- Departure: 11:10, Arrival: 21:05 local
- Aircraft: A380 + A321
- Baggage: 2×23kg checked + 8kg cabin
- **Note**: Late arrival, long layover

### Step 5: Load Details Tools (Optional)

For more information on top options:

```
/amadeus-flight details
```

Get details for Air France flight:

```javascript
mcp__plugin_amadeus-flight_amadeus-flight__flight_details({
  flight_id: "AF382_20260215",
  include_aircraft: true,
  include_amenities: true
})
```

**Additional Details**:
```json
{
  "amenities": {
    "wifi": true,
    "power_outlets": true,
    "entertainment": "Seatback IFE with 1000+ options",
    "meals": "Complimentary meals and beverages",
    "seat_pitch_cm": 79
  },
  "schedule": {
    "on_time_performance": 0.87
  }
}
```

### Step 6: Check Availability

```javascript
mcp__plugin_amadeus-flight_amadeus-flight__seat_availability({
  flight_id: "AF382_20260215"
})
```

**Response**:
```json
{
  "availability": {
    "economy": {
      "available": true,
      "seats_remaining": 47
    },
    "business": {
      "available": true,
      "seats_remaining": 8
    }
  }
}
```

Good availability, no urgency to book immediately.

### Step 7: Make Recommendation

**Selected Flight: Air China CA877**

**Rationale**:
1. **Best value**: $410 vs $450 (saves $80 total)
2. **Direct flight**: No connections, less hassle
3. **Modern aircraft**: A350-900, fuel efficient, quiet
4. **Reasonable arrival time**: 18:35, still time for hotel check-in
5. **Good baggage**: Same checked allowance as Air France

**Trade-offs**:
- 45 minutes longer than Air France
- Afternoon departure (vs morning)
- Slightly less cabin baggage (10kg vs 12kg)

**Alternative**: Air France AF382 if morning departure preferred (+$40/person)

### Step 8: Structure Data for Transportation Agent

```json
{
  "day": 3,
  "location_change": {
    "from": "Beijing",
    "to": "Paris",
    "transportation": "Flight - Air China CA877",
    "departure_time": "13:20",
    "arrival_time": "18:35",
    "duration_minutes": 675,
    "cost": 410.00,
    "currency": "USD",
    "total_cost": 820.00,
    "passengers": 2,
    "baggage": "2 checked bags (23kg each), 1 cabin (10kg)",
    "cabin_class": "Economy",
    "booking_class": "Y",
    "aircraft": "Airbus A350-900",
    "booking_recommendation": "Book 2-3 weeks in advance, price stable",
    "notes": "Direct flight, modern aircraft, arrives CDG Terminal 1",
    "data_source": "amadeus",
    "airport_transfer_time": 180,
    "total_journey_minutes": 855
  }
}
```

**Key additions**:
- `airport_transfer_time`: 3 hours (2.5h before departure + 30m after arrival)
- `total_journey_minutes`: Flight + airport time = 675 + 180 = 855 minutes (14h 15m)
- `data_source`: "amadeus" (vs "web_search" for fallback)

### Step 9: Save Output

Write to `data/paris-trip/transportation.json`:

```json
{
  "agent": "transportation",
  "status": "complete",
  "data": {
    "days": [
      {
        "day": 3,
        "location_change": { /* as above */ }
      }
    ]
  },
  "notes": "Flight search completed via Amadeus API. Recommended Air China CA877 for best value ($80 savings vs Air France). Direct flight with modern aircraft. Book 2-3 weeks in advance.",
  "data_sources": {
    "amadeus": true,
    "web_search": false
  },
  "search_timestamp": "2026-01-30T12:00:00Z"
}
```

## Error Handling Example

### Scenario: Rate Limit Error

```javascript
// First attempt
try {
  const flights = await search_flights({ /* params */ });
} catch (error) {
  if (error.code === 'rate_limit') {
    // Wait and retry
    await sleep(2000);
    try {
      const flights = await search_flights({ /* params */ });
    } catch (retryError) {
      // Fall back to WebSearch
      const fallbackResults = await webSearch(
        "flights from Beijing to Paris February 15 2026"
      );
      // Parse and structure fallback data
      // Mark as data_source: "web_search"
    }
  }
}
```

### Scenario: Invalid Airport Code

```javascript
// User provides city name instead of IATA code
const origin = "Beijing";  // Should be "PEK"

// Validate and convert
const originIATA = await validateAirportCode(origin);
// Returns "PEK" or throws error

// Then search
const flights = await search_flights({
  origin: originIATA,  // Now correct
  destination: "CDG",
  // ...
});
```

## Performance Metrics

**Typical Response Times**:
- Price analysis: 300-500ms
- Flight search: 800-1200ms
- Flight details: 300-500ms
- Seat availability: 200-400ms
- **Total workflow**: 1.5-2.5 seconds

**Optimization**:
- Run price analysis and search in parallel if both needed
- Cache search results for 1 hour
- Only fetch details for top 3 results
- Batch availability checks if API supports

## Best Practices Demonstrated

1. **Price analysis first**: Check timing before searching
2. **Reasonable limits**: max_results=5 to avoid overwhelming data
3. **Compare multiple options**: At least 3 flights
4. **Consider total journey**: Include airport transfer time
5. **Document data source**: Track whether from API or fallback
6. **Structured output**: Consistent format for agent pipeline
7. **Error handling**: Retry logic with fallback
8. **Clear rationale**: Explain recommendation reasoning

## Integration Points

**Input from**:
- `requirements-skeleton.json`: Budget, preferences
- `plan-skeleton.json`: Travel dates, locations

**Output to**:
- `transportation.json`: Structured transportation data

**Used by**:
- Timeline agent: Adjusts schedule based on arrival time
- Budget agent: Tracks transportation costs

---

**See also**:
- `../tools/search.md` for detailed search tool documentation
- `../tools/details.md` for details tool documentation
- `../SKILL.md` for skill overview
