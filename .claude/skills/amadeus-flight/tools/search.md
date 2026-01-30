# Amadeus Flight - Search Tools

Flight search and pricing tools using Amadeus GDS data.

## MCP Tools

### Tool 1: search_flights

**MCP Tool Name**: `mcp__plugin_amadeus-flight_amadeus-flight__search_flights`

**Description**: Search flights between two airports with real-time pricing.

**Parameters**:
- `origin` (required, string): IATA airport code (e.g., "PEK", "CDG", "LHR")
- `destination` (required, string): IATA airport code
- `departure_date` (required, string): ISO 8601 date format (YYYY-MM-DD)
- `return_date` (optional, string): For round-trip searches
- `adults` (optional, number): Number of adult passengers (default: 1)
- `children` (optional, number): Number of children
- `infants` (optional, number): Number of infants
- `cabin_class` (optional, string): "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"
- `nonstop` (optional, boolean): Only non-stop flights (default: false)
- `max_results` (optional, number): Maximum results to return (default: 10)

**Returns**:
```json
{
  "flights": [
    {
      "id": "flight_id",
      "price": {
        "total": 450.00,
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
    }
  ],
  "meta": {
    "count": 5,
    "currency": "USD"
  }
}
```

**Use Cases**:
- Point-to-point international flight search
- Round-trip flight pricing
- Comparing airlines for same route
- Finding non-stop options
- Getting real-time availability

**Example Usage**:
```javascript
// One-way international flight
search_flights({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-02-15",
  adults: 2,
  cabin_class: "ECONOMY",
  nonstop: false
})

// Round-trip search
search_flights({
  origin: "LAX",
  destination: "NRT",
  departure_date: "2026-03-20",
  return_date: "2026-03-30",
  adults: 1,
  cabin_class: "BUSINESS"
})
```

---

### Tool 2: multi_city_search

**MCP Tool Name**: `mcp__plugin_amadeus-flight_amadeus-flight__multi_city_search`

**Description**: Search multi-city itineraries with multiple flight segments.

**Parameters**:
- `segments` (required, array): Array of flight segments
  - Each segment:
    - `origin` (required, string): IATA code
    - `destination` (required, string): IATA code
    - `departure_date` (required, string): ISO 8601 date
- `adults` (optional, number): Number of adult passengers (default: 1)
- `cabin_class` (optional, string): Cabin class for all segments
- `max_results` (optional, number): Maximum results (default: 10)

**Returns**:
Similar to search_flights but with multiple itineraries representing different segment combinations.

**Use Cases**:
- Multi-destination trips (e.g., Beijing → Paris → Rome → Beijing)
- Open-jaw itineraries
- Complex routing requirements
- Grand tour planning

**Example Usage**:
```javascript
// Multi-city grand tour
multi_city_search({
  segments: [
    {
      origin: "PEK",
      destination: "CDG",
      departure_date: "2026-04-01"
    },
    {
      origin: "CDG",
      destination: "FCO",
      departure_date: "2026-04-08"
    },
    {
      origin: "FCO",
      destination: "PEK",
      departure_date: "2026-04-15"
    }
  ],
  adults: 2,
  cabin_class: "ECONOMY"
})
```

---

### Tool 3: price_analysis

**MCP Tool Name**: `mcp__plugin_amadeus-flight_amadeus-flight__price_analysis`

**Description**: Analyze price trends and get booking recommendations.

**Parameters**:
- `origin` (required, string): IATA airport code
- `destination` (required, string): IATA airport code
- `departure_date` (required, string): ISO 8601 date
- `return_date` (optional, string): For round-trip analysis

**Returns**:
```json
{
  "current_price": 450.00,
  "currency": "USD",
  "price_trend": "stable",
  "historical_data": {
    "min_price": 420.00,
    "max_price": 580.00,
    "average_price": 480.00,
    "data_points": 30
  },
  "recommendations": {
    "booking_window": "2-3 weeks before departure",
    "optimal_days": ["Tuesday", "Wednesday"],
    "price_forecast": "likely_to_increase",
    "confidence": 0.85
  },
  "alerts": {
    "current_deal": false,
    "price_drop_alert": false,
    "peak_season": true
  }
}
```

**Use Cases**:
- Determine if current price is good
- Recommend booking timing
- Set price alerts
- Identify seasonal patterns
- Optimize booking window

**Example Usage**:
```javascript
// Analyze price trends
price_analysis({
  origin: "SFO",
  destination: "LHR",
  departure_date: "2026-07-15",
  return_date: "2026-07-25"
})
```

---

## Best Practices

### Airport Codes
- Always validate IATA codes before search
- Use 3-letter codes only (PEK, not Beijing Capital)
- Common codes:
  - Beijing: PEK (Capital), PKX (Daxing)
  - Paris: CDG (Charles de Gaulle), ORY (Orly)
  - London: LHR (Heathrow), LGW (Gatwick), STN (Stansted)
  - New York: JFK, EWR, LGA
  - Tokyo: NRT (Narita), HND (Haneda)

### Date Handling
- Use ISO 8601 format: YYYY-MM-DD
- Validate dates are in future
- Check departure before return date
- Consider time zones for arrival times

### Price Optimization
1. Run price_analysis first
2. Check booking recommendation
3. Search flights if price acceptable
4. Compare multiple dates if flexible
5. Consider nearby airports for better deals

### Multi-City Strategy
- Minimize backtracking for better prices
- Consider open-jaw vs. round-trip
- Allow sufficient time between segments (min 2 hours for connections)
- Check visa requirements for each country

### Performance
- Limit max_results to avoid long response times
- Cache results for same search within 1 hour
- Use nonstop filter to reduce result set
- Batch similar searches if possible

## Error Handling

### Common Errors

**Invalid Airport Code**:
```json
{
  "error": "invalid_parameter",
  "message": "Invalid IATA code: 'BEIJING'",
  "parameter": "origin"
}
```
**Solution**: Validate codes against IATA database, use 3-letter codes

**No Results Found**:
```json
{
  "error": "no_results",
  "message": "No flights found for route PEK-CDG on 2026-02-15"
}
```
**Solution**: Try broader date range, check nearby airports, verify route exists

**Rate Limit Exceeded**:
```json
{
  "error": "rate_limit",
  "message": "API rate limit exceeded",
  "retry_after": 60
}
```
**Solution**: Implement exponential backoff, respect retry_after header

**Authentication Error**:
```json
{
  "error": "authentication_failed",
  "message": "Invalid API credentials"
}
```
**Solution**: Check AMADEUS_API_KEY and AMADEUS_API_SECRET configuration

### Retry Logic

```javascript
async function searchWithRetry(params, maxAttempts = 3) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await search_flights(params);
    } catch (error) {
      if (attempt === maxAttempts) {
        // Final attempt failed, fall back to WebSearch
        return fallbackToWebSearch(params);
      }
      // Exponential backoff: 1s, 2s, 4s
      await sleep(Math.pow(2, attempt - 1) * 1000);
    }
  }
}
```

## Integration with Transportation Agent

**Workflow**:
1. Transportation agent identifies international route
2. Invokes `/amadeus-flight search`
3. Reads this tool documentation
4. Validates IATA codes for origin/destination
5. Calls price_analysis to check booking timing
6. Calls search_flights with appropriate parameters
7. Parses response and structures data
8. Calculates total journey time (flight + airport transfers)
9. Saves to transportation.json with data source documented

**Data Structure for Agent Output**:
```json
{
  "day": 3,
  "location_change": {
    "from": "Beijing",
    "to": "Paris",
    "transportation": "Flight - Air France AF382",
    "departure_time": "09:30",
    "arrival_time": "14:00",
    "duration_minutes": 630,
    "cost": 450.00,
    "currency": "USD",
    "baggage": "2 checked bags (23kg each), 1 cabin (12kg)",
    "cabin_class": "Economy",
    "booking_recommendation": "Book 2-3 weeks in advance",
    "notes": "Non-stop flight, arrives CDG Terminal 2E",
    "data_source": "amadeus"
  }
}
```

## Cost Considerations

- API calls are metered, use wisely
- Cache identical searches for 1 hour
- Limit max_results to needed amount
- Use price_analysis before search to avoid unnecessary calls
- Consider batch processing for multiple routes

## Fallback Strategy

If Amadeus MCP unavailable:
1. Log error with details
2. Switch to WebSearch with query:
   - "flights from {origin} to {destination} on {date}"
   - "flight price {origin} to {destination} {month} {year}"
3. Parse web results (less structured)
4. Document data source as "web_search" in output
5. Note reduced data accuracy

---

**See also**: `../examples/flight-search.md` for complete workflow example
