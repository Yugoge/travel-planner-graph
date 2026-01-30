# Amadeus Flight - Search Tools

Flight search and pricing tools for international travel.

## Available Tools

### 1. search_flights

Search for flights between two locations with real-time pricing.

**MCP Tool**: `search_flights`

**Parameters**:
- `origin` (required): IATA airport code (e.g., "LAX", "JFK", "PEK")
- `destination` (required): IATA airport code
- `departure_date` (required): Departure date in ISO 8601 format (YYYY-MM-DD)
- `return_date` (optional): Return date for round-trip flights
- `adults` (optional): Number of adult passengers (default: 1, max: 9)
- `children` (optional): Number of children (ages 2-11, default: 0)
- `infants` (optional): Number of infants (under 2, default: 0)
- `travel_class` (optional): Cabin class
  - `ECONOMY` (default)
  - `PREMIUM_ECONOMY`
  - `BUSINESS`
  - `FIRST`
- `non_stop` (optional): Only non-stop flights (default: false)
- `currency` (optional): Price currency code (default: USD)
- `max_results` (optional): Maximum results to return (default: 10, max: 50)

**Returns**:
- Flight offers with pricing
- Itineraries with segments
- Airline and flight numbers
- Departure/arrival times with timezones
- Duration (total and per segment)
- Number of stops
- Baggage allowance
- Seat availability
- Booking class codes

**Example**:
```javascript
// One-way flight from Beijing to Paris
search_flights({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-06-15",
  adults: 2,
  travel_class: "ECONOMY",
  non_stop: false,
  currency: "USD",
  max_results: 10
})
```

**Response Structure**:
```json
{
  "data": [
    {
      "id": "1",
      "price": {
        "total": "1250.00",
        "currency": "USD",
        "base": "950.00",
        "fees": [
          {"amount": "150.00", "type": "SUPPLIER"},
          {"amount": "150.00", "type": "TICKETING"}
        ]
      },
      "itineraries": [
        {
          "duration": "PT11H30M",
          "segments": [
            {
              "departure": {
                "iataCode": "PEK",
                "terminal": "3",
                "at": "2026-06-15T13:30:00+08:00"
              },
              "arrival": {
                "iataCode": "CDG",
                "terminal": "2E",
                "at": "2026-06-15T18:00:00+02:00"
              },
              "carrierCode": "AF",
              "number": "382",
              "aircraft": {"code": "77W"},
              "duration": "PT11H30M",
              "numberOfStops": 0
            }
          ]
        }
      ],
      "travelerPricings": [
        {
          "travelerId": "1",
          "fareOption": "STANDARD",
          "travelerType": "ADULT",
          "price": {"total": "625.00", "currency": "USD"},
          "fareDetailsBySegment": [
            {
              "segmentId": "1",
              "cabin": "ECONOMY",
              "class": "Y",
              "includedCheckedBags": {"quantity": 2}
            }
          ]
        }
      ]
    }
  ]
}
```

**Use Cases**:
- Point-to-point international flights
- Round-trip booking price comparison
- Family travel with multiple passengers
- Business class upgrade analysis
- Non-stop preference filtering

---

### 2. multi_city_search

Search for multi-city itineraries with multiple destinations.

**MCP Tool**: `multi_city_search`

**Parameters**:
- `segments` (required): Array of flight segments
  - Each segment includes: `origin`, `destination`, `departure_date`
- `adults` (optional): Number of adult passengers (default: 1)
- `children` (optional): Number of children (default: 0)
- `infants` (optional): Number of infants (default: 0)
- `travel_class` (optional): Cabin class (default: ECONOMY)
- `currency` (optional): Price currency code (default: USD)
- `max_results` (optional): Maximum results (default: 10)

**Returns**:
- Multi-segment flight offers
- Combined pricing for entire journey
- Connection times between flights
- Total journey duration
- Baggage rules for multi-segment trips

**Example**:
```javascript
// Beijing → Paris → London → Beijing
multi_city_search({
  segments: [
    {origin: "PEK", destination: "CDG", departure_date: "2026-06-15"},
    {origin: "CDG", destination: "LHR", departure_date: "2026-06-20"},
    {origin: "LHR", destination: "PEK", departure_date: "2026-06-25"}
  ],
  adults: 2,
  travel_class: "ECONOMY",
  currency: "USD"
})
```

**Response Structure**:
```json
{
  "data": [
    {
      "id": "1",
      "price": {"total": "2850.00", "currency": "USD"},
      "itineraries": [
        {
          "segments": [
            {
              "departure": {"iataCode": "PEK", "at": "2026-06-15T13:30:00+08:00"},
              "arrival": {"iataCode": "CDG", "at": "2026-06-15T18:00:00+02:00"}
            },
            {
              "departure": {"iataCode": "CDG", "at": "2026-06-20T10:15:00+02:00"},
              "arrival": {"iataCode": "LHR", "at": "2026-06-20T10:40:00+01:00"}
            },
            {
              "departure": {"iataCode": "LHR", "at": "2026-06-25T12:00:00+01:00"},
              "arrival": {"iataCode": "PEK", "at": "2026-06-26T06:30:00+08:00"}
            }
          ]
        }
      ]
    }
  ]
}
```

**Use Cases**:
- Complex multi-destination trips
- Around-the-world itineraries
- Business trips with multiple stops
- Gap year travel planning
- Regional tour packages

---

### 3. price_analysis

Get price trends and predictions for a specific route.

**MCP Tool**: `price_analysis`

**Parameters**:
- `origin` (required): IATA airport code
- `destination` (required): IATA airport code
- `departure_date` (required): Target departure date
- `lookback_days` (optional): Historical data period (default: 180)
- `lookahead_days` (optional): Prediction period (default: 30)
- `currency` (optional): Price currency (default: USD)

**Returns**:
- Historical price trends (min, max, average)
- Price predictions for next 30 days
- Optimal booking window
- Price percentile (current price vs historical)
- Seasonality patterns
- Day-of-week price variations

**Example**:
```javascript
// Price analysis for Beijing to Paris
price_analysis({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-06-15",
  lookback_days: 180,
  lookahead_days: 30,
  currency: "USD"
})
```

**Response Structure**:
```json
{
  "data": {
    "origin": "PEK",
    "destination": "CDG",
    "departure_date": "2026-06-15",
    "current_price": {"amount": 1250.00, "currency": "USD"},
    "historical": {
      "min": 850.00,
      "max": 1850.00,
      "average": 1200.00,
      "median": 1150.00
    },
    "percentile": 55,
    "prediction": {
      "next_7_days": {"min": 1200.00, "max": 1350.00, "trend": "increasing"},
      "next_30_days": {"min": 1150.00, "max": 1500.00, "trend": "stable"}
    },
    "optimal_booking": {
      "window_start": "2026-04-15",
      "window_end": "2026-05-15",
      "reason": "3-8 weeks advance booking yields best prices"
    },
    "seasonality": {
      "peak_season": {"start": "2026-06-01", "end": "2026-08-31"},
      "off_peak": {"start": "2026-11-01", "end": "2026-02-28"}
    }
  }
}
```

**Use Cases**:
- Budget planning for future trips
- Booking timing optimization
- Price drop alerts
- Seasonal trend analysis
- Historical price comparison

---

### 4. seat_availability

Check seat availability and cabin class options for specific flights.

**MCP Tool**: `seat_availability`

**Parameters**:
- `flight_offer_id` (required): Flight offer ID from search results
- `cabin_class` (optional): Specific cabin to check (ECONOMY, BUSINESS, FIRST)

**Returns**:
- Available seats by cabin class
- Seat map (if available)
- Extra legroom seats
- Premium economy options
- Upgrade availability
- Real-time availability status

**Example**:
```javascript
// Check availability for flight offer
seat_availability({
  flight_offer_id: "1",
  cabin_class: "ECONOMY"
})
```

**Response Structure**:
```json
{
  "data": {
    "flight_offer_id": "1",
    "availability": {
      "ECONOMY": {
        "available_seats": 42,
        "booking_class": ["Y", "B", "M"],
        "status": "available"
      },
      "PREMIUM_ECONOMY": {
        "available_seats": 8,
        "booking_class": ["W"],
        "status": "limited"
      },
      "BUSINESS": {
        "available_seats": 0,
        "booking_class": [],
        "status": "sold_out"
      }
    },
    "seat_features": {
      "extra_legroom": {"available": true, "additional_cost": 50.00},
      "preferred_seats": {"available": true, "additional_cost": 25.00}
    }
  }
}
```

**Use Cases**:
- Group booking coordination
- Cabin upgrade decisions
- Seat selection planning
- Last-minute availability check
- Overbooking risk assessment

---

## Best Practices

### 1. Search Optimization

**Date Flexibility**:
```javascript
// Search multiple dates to find best price
const dates = ["2026-06-15", "2026-06-16", "2026-06-17"];
const results = await Promise.all(
  dates.map(date => search_flights({
    origin: "PEK",
    destination: "CDG",
    departure_date: date
  }))
);

// Find cheapest option
const cheapest = results
  .flatMap(r => r.data)
  .sort((a, b) => parseFloat(a.price.total) - parseFloat(b.price.total))[0];
```

**Cabin Class Comparison**:
```javascript
// Compare economy vs business
const classes = ["ECONOMY", "BUSINESS"];
const classResults = await Promise.all(
  classes.map(cls => search_flights({
    origin: "PEK",
    destination: "CDG",
    departure_date: "2026-06-15",
    travel_class: cls
  }))
);
```

### 2. Multi-City Planning

**Logical Connections**:
```javascript
// Ensure minimum connection time (2-4 hours)
const segments = [
  {origin: "PEK", destination: "CDG", departure_date: "2026-06-15"},
  {origin: "CDG", destination: "LHR", departure_date: "2026-06-20"},  // 5 days later
  {origin: "LHR", destination: "PEK", departure_date: "2026-06-25"}   // 5 days later
];

// Avoid tight connections on same day
const tightConnection = [
  {origin: "PEK", destination: "CDG", departure_date: "2026-06-15"},
  {origin: "CDG", destination: "LHR", departure_date: "2026-06-15"}  // Same day - risky!
];
```

### 3. Error Handling

**Retry Logic**:
```javascript
async function searchFlightsWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_flights(params);
    } catch (error) {
      // Retry on transient errors
      if (error.status === 429 || error.status >= 500) {
        const delay = 1000 * Math.pow(2, i);  // Exponential backoff
        await sleep(delay);
        continue;
      }
      // Don't retry on permanent errors
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Fallback to WebSearch**:
```javascript
async function getFlightDataWithFallback(origin, destination, date) {
  try {
    const result = await search_flights({origin, destination, departure_date: date});
    return {source: 'amadeus', data: result.data};
  } catch (error) {
    console.warn('Amadeus unavailable, falling back to WebSearch');
    const query = `flights from ${origin} to ${destination} ${date}`;
    const searchResults = await WebSearch({query});
    return {source: 'web_search', data: parseWebResults(searchResults)};
  }
}
```

### 4. Response Parsing

**Extract Price**:
```javascript
function extractPrice(flightOffer) {
  return {
    total: parseFloat(flightOffer.price.total),
    currency: flightOffer.price.currency,
    base: parseFloat(flightOffer.price.base),
    fees: flightOffer.price.fees.reduce(
      (sum, fee) => sum + parseFloat(fee.amount), 0
    )
  };
}
```

**Calculate Duration**:
```javascript
function parseDuration(isoDuration) {
  // Parse ISO 8601 duration: PT11H30M
  const match = isoDuration.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
  const hours = parseInt(match[1] || 0);
  const minutes = parseInt(match[2] || 0);
  return {hours, minutes, totalMinutes: hours * 60 + minutes};
}
```

**Format Times**:
```javascript
function formatFlightTime(segment) {
  return {
    departure: {
      airport: segment.departure.iataCode,
      time: new Date(segment.departure.at).toLocaleString(),
      timezone: segment.departure.at.slice(-6)
    },
    arrival: {
      airport: segment.arrival.iataCode,
      time: new Date(segment.arrival.at).toLocaleString(),
      timezone: segment.arrival.at.slice(-6)
    }
  };
}
```

### 5. Rate Limiting

**Batch Requests**:
```javascript
// Add delay between requests
async function batchSearch(searches) {
  const results = [];
  for (const search of searches) {
    const result = await search_flights(search);
    results.push(result);
    await sleep(200);  // 200ms delay
  }
  return results;
}
```

**Monitor Usage**:
```javascript
let requestCount = 0;
const maxRequestsPerMinute = 50;

async function rateLimitedSearch(params) {
  if (requestCount >= maxRequestsPerMinute) {
    await sleep(60000);  // Wait 1 minute
    requestCount = 0;
  }
  requestCount++;
  return await search_flights(params);
}
```

## Integration with Transportation Agent

The transportation agent should:

1. **Load this file** when processing international flights
2. **Use search_flights** for one-way or round-trip flights
3. **Use multi_city_search** for complex multi-destination trips
4. **Use price_analysis** to recommend optimal booking time
5. **Parse response** for price, duration, stops, airline
6. **Save structured data** to `transportation.json`
7. **Fall back to WebSearch** if MCP unavailable

Example workflow:
```
1. Detect international location change: Beijing → Paris
2. Invoke /amadeus-flight search (loads this file)
3. Call search_flights({origin: "PEK", destination: "CDG", departure_date: "2026-06-15"})
4. Parse response: price=$1250, duration=11h30m, airline=Air France, non-stop
5. Save to transportation.json
6. Return complete
```
