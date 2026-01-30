# Example: International Flight Search

Complete workflow for searching and booking international flights using Amadeus Flight skill.

## Scenario

User is traveling from Beijing to Paris on Day 1 of their trip. Transportation agent needs to research flight options and recommend the best one.

## Step-by-Step Workflow

### Step 1: Load Flight Search Tools

```markdown
Load search category: /root/travel-planner/.claude/commands/amadeus-flight/tools/search.md
```

This loads the `search_flights`, `multi_city_search`, `price_analysis`, and `seat_availability` tools.

### Step 2: Search for Flights

```javascript
// Search for one-way flights from Beijing to Paris
const searchResult = await search_flights({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-06-15",
  adults: 2,
  travel_class: "ECONOMY",
  non_stop: false,
  currency: "USD",
  max_results: 10
});

// Response structure:
{
  data: [
    {
      id: "1",
      price: {
        total: "1250.00",
        currency: "USD",
        base: "950.00",
        fees: [
          {amount: "150.00", type: "SUPPLIER"},
          {amount: "150.00", type: "TICKETING"}
        ]
      },
      itineraries: [
        {
          duration: "PT11H30M",
          segments: [
            {
              departure: {
                iataCode: "PEK",
                terminal: "3",
                at: "2026-06-15T13:30:00+08:00"
              },
              arrival: {
                iataCode: "CDG",
                terminal: "2E",
                at: "2026-06-15T18:00:00+02:00"
              },
              carrierCode: "AF",
              number: "382",
              aircraft: {code: "77W"},
              duration: "PT11H30M",
              numberOfStops: 0
            }
          ]
        }
      ],
      travelerPricings: [
        {
          travelerId: "1",
          fareOption: "STANDARD",
          travelerType: "ADULT",
          price: {total: "625.00", currency: "USD"},
          fareDetailsBySegment: [
            {
              segmentId: "1",
              cabin: "ECONOMY",
              class: "Y",
              includedCheckedBags: {quantity: 2}
            }
          ]
        }
      ]
    }
  ]
}
```

### Step 3: Parse Flight Data

```javascript
function parseFlightOffer(offer) {
  const segment = offer.itineraries[0].segments[0];
  const pricing = offer.travelerPricings[0];

  // Parse ISO 8601 duration
  const durationMatch = segment.duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
  const hours = parseInt(durationMatch[1] || 0);
  const minutes = parseInt(durationMatch[2] || 0);

  return {
    price: {
      total: parseFloat(offer.price.total),
      per_person: parseFloat(pricing.price.total),
      currency: offer.price.currency
    },
    flight: {
      airline: segment.carrierCode,
      flight_number: `${segment.carrierCode}${segment.number}`,
      aircraft: segment.aircraft.code,
      departure: {
        airport: segment.departure.iataCode,
        terminal: segment.departure.terminal,
        time: segment.departure.at,
        local_time: new Date(segment.departure.at).toLocaleString('en-US', {
          timeZone: 'Asia/Shanghai'
        })
      },
      arrival: {
        airport: segment.arrival.iataCode,
        terminal: segment.arrival.terminal,
        time: segment.arrival.at,
        local_time: new Date(segment.arrival.at).toLocaleString('en-US', {
          timeZone: 'Europe/Paris'
        })
      },
      duration: {
        hours: hours,
        minutes: minutes,
        total_minutes: hours * 60 + minutes,
        formatted: `${hours}h ${minutes}m`
      },
      stops: segment.numberOfStops
    },
    baggage: {
      checked_bags: pricing.fareDetailsBySegment[0].includedCheckedBags.quantity,
      cabin_class: pricing.fareDetailsBySegment[0].cabin
    }
  };
}

// Parsed result:
{
  price: {total: 1250.00, per_person: 625.00, currency: "USD"},
  flight: {
    airline: "AF",
    flight_number: "AF382",
    aircraft: "77W",
    departure: {
      airport: "PEK",
      terminal: "3",
      time: "2026-06-15T13:30:00+08:00",
      local_time: "6/15/2026, 1:30:00 PM"
    },
    arrival: {
      airport: "CDG",
      terminal: "2E",
      time: "2026-06-15T18:00:00+02:00",
      local_time: "6/15/2026, 6:00:00 PM"
    },
    duration: {hours: 11, minutes: 30, total_minutes: 690, formatted: "11h 30m"},
    stops: 0
  },
  baggage: {checked_bags: 2, cabin_class: "ECONOMY"}
}
```

### Step 4: Compare Multiple Options

```javascript
function rankFlightOffers(offers, preferences = {}) {
  const scored = offers.map(offer => {
    const parsed = parseFlightOffer(offer);
    let score = 0;

    // Price score (lower is better)
    const priceScore = 1000 / parsed.price.total;
    score += priceScore * (preferences.price_weight || 0.4);

    // Duration score (shorter is better)
    const durationScore = 1000 / parsed.flight.duration.total_minutes;
    score += durationScore * (preferences.duration_weight || 0.3);

    // Non-stop bonus
    if (parsed.flight.stops === 0) {
      score += 10 * (preferences.non_stop_weight || 0.3);
    }

    return {offer: parsed, score: score};
  });

  return scored.sort((a, b) => b.score - a.score);
}

// Rank all search results
const rankedFlights = rankFlightOffers(searchResult.data, {
  price_weight: 0.5,
  duration_weight: 0.3,
  non_stop_weight: 0.2
});

// Top recommendation
const recommended = rankedFlights[0].offer;
```

### Step 5: Get Price Analysis

```javascript
// Get price trends for better booking decision
const priceAnalysis = await price_analysis({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-06-15",
  lookback_days: 180,
  lookahead_days: 30,
  currency: "USD"
});

// Response:
{
  data: {
    current_price: {amount: 1250.00, currency: "USD"},
    historical: {
      min: 850.00,
      max: 1850.00,
      average: 1200.00,
      median: 1150.00
    },
    percentile: 55,
    prediction: {
      next_7_days: {min: 1200.00, max: 1350.00, trend: "increasing"},
      next_30_days: {min: 1150.00, max: 1500.00, trend: "stable"}
    },
    optimal_booking: {
      window_start: "2026-04-15",
      window_end: "2026-05-15",
      reason: "3-8 weeks advance booking yields best prices"
    }
  }
}

// Determine if current price is good
function analyzePriceValue(currentPrice, analysis) {
  const percentile = analysis.data.percentile;

  if (percentile <= 25) {
    return {
      value: "excellent",
      recommendation: "Book now - price is in bottom 25% of historical range"
    };
  } else if (percentile <= 50) {
    return {
      value: "good",
      recommendation: "Good price - consider booking soon"
    };
  } else if (percentile <= 75) {
    return {
      value: "fair",
      recommendation: "Average price - monitor for better deals"
    };
  } else {
    return {
      value: "poor",
      recommendation: "High price - wait if possible or search flexible dates"
    };
  }
}

const priceValue = analyzePriceValue(1250.00, priceAnalysis);
// {value: "good", recommendation: "Good price - consider booking soon"}
```

### Step 6: Save to Transportation JSON

```javascript
const recommendation = {
  from: "Beijing",
  to: "Paris",
  transportation: "Flight",
  airline: recommended.flight.airline,
  flight_number: recommended.flight.flight_number,
  aircraft: recommended.flight.aircraft,
  departure_time: recommended.flight.departure.local_time,
  arrival_time: recommended.flight.arrival.local_time,
  departure_airport: recommended.flight.departure.airport,
  arrival_airport: recommended.flight.arrival.airport,
  duration_minutes: recommended.flight.duration.total_minutes,
  cost: recommended.price.total,
  currency: recommended.price.currency,
  stops: recommended.flight.stops,
  baggage_allowance: `${recommended.baggage.checked_bags} checked bags`,
  cabin_class: recommended.baggage.cabin_class,
  price_analysis: {
    percentile: priceAnalysis.data.percentile,
    value_rating: priceValue.value,
    booking_recommendation: priceValue.recommendation
  },
  notes: `Non-stop flight, ${recommended.flight.duration.formatted} duration. ${priceValue.recommendation}`
};

const transportationData = {
  agent: "transportation",
  status: "complete",
  data: {
    days: [
      {
        day: 1,
        location_change: recommendation
      }
    ]
  },
  notes: "Flight booked via Amadeus API. Book 3-8 weeks in advance for best prices."
};

// Save to: data/{destination-slug}/transportation.json
writeJSON(`data/${destinationSlug}/transportation.json`, transportationData);
```

---

## Multi-City Trip Example

### Scenario: Beijing → Paris → London → Beijing

```javascript
async function searchMultiCityTrip() {
  // Define segments
  const segments = [
    {origin: "PEK", destination: "CDG", departure_date: "2026-06-15"},
    {origin: "CDG", destination: "LHR", departure_date: "2026-06-20"},
    {origin: "LHR", destination: "PEK", departure_date: "2026-06-25"}
  ];

  // Search multi-city itinerary
  const result = await multi_city_search({
    segments: segments,
    adults: 2,
    travel_class: "ECONOMY",
    currency: "USD"
  });

  // Parse multi-city result
  function parseMultiCityOffer(offer) {
    const itinerary = offer.itineraries[0];

    return {
      total_price: parseFloat(offer.price.total),
      currency: offer.price.currency,
      segments: itinerary.segments.map((seg, idx) => ({
        leg: idx + 1,
        from: seg.departure.iataCode,
        to: seg.arrival.iataCode,
        departure: new Date(seg.departure.at).toLocaleString(),
        arrival: new Date(seg.arrival.at).toLocaleString(),
        airline: seg.carrierCode,
        flight_number: `${seg.carrierCode}${seg.number}`,
        duration: seg.duration
      }))
    };
  }

  const parsed = parseMultiCityOffer(result.data[0]);

  return {
    agent: "transportation",
    status: "complete",
    data: {
      days: [
        {
          day: 1,
          location_change: {
            from: "Beijing",
            to: "Paris",
            ...parsed.segments[0],
            cost_per_person: parsed.total_price / 2
          }
        },
        {
          day: 6,
          location_change: {
            from: "Paris",
            to: "London",
            ...parsed.segments[1],
            cost_per_person: parsed.total_price / 2
          }
        },
        {
          day: 11,
          location_change: {
            from: "London",
            to: "Beijing",
            ...parsed.segments[2],
            cost_per_person: parsed.total_price / 2
          }
        }
      ]
    },
    notes: `Multi-city booking via Amadeus API. Total cost: $${parsed.total_price} for all flights.`
  };
}
```

---

## Error Handling Example

### Scenario: MCP Server Unavailable

```javascript
async function searchFlightWithFallback(origin, destination, date) {
  try {
    // Try Amadeus API first
    const result = await search_flights({
      origin: origin,
      destination: destination,
      departure_date: date,
      adults: 2,
      currency: "USD"
    });

    return {
      source: 'amadeus',
      data: parseFlightOffer(result.data[0]),
      reliability: 'real-time'
    };
  } catch (error) {
    console.warn('Amadeus API unavailable, falling back to WebSearch');

    // Fallback to WebSearch
    const searchQuery = `flights from ${origin} to ${destination} ${date}`;
    const searchResults = await WebSearch({query: searchQuery});

    // Parse web search results (simplified)
    const webData = {
      price: {total: 1300.00, currency: "USD"},
      flight: {
        airline: "Unknown",
        departure: {airport: origin, time: "Unknown"},
        arrival: {airport: destination, time: "Unknown"}
      }
    };

    return {
      source: 'web_search',
      data: webData,
      reliability: 'estimated',
      warning: 'Data from web search - not real-time, verify before booking'
    };
  }
}
```

---

## Retry Logic Example

### Scenario: Transient Network Error

```javascript
async function searchFlightWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_flights(params);
    } catch (error) {
      // Retry on transient errors
      if (error.status === 429 || error.status >= 500) {
        const delay = 1000 * Math.pow(2, i);  // Exponential backoff: 1s, 2s, 4s
        console.warn(`Retry ${i + 1}/${maxRetries} after ${delay}ms`);
        await sleep(delay);
        continue;
      }

      // Don't retry on permanent errors (400, 401, 403, 404)
      throw error;
    }
  }

  throw new Error('Max retries exceeded');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Usage
const result = await searchFlightWithRetry({
  origin: "PEK",
  destination: "CDG",
  departure_date: "2026-06-15"
});
```

---

## Complete Transportation Agent Workflow

```javascript
async function transportationAgentWorkflow(destinationSlug) {
  // Step 1: Read requirements and plan skeleton
  const requirements = readJSON(`data/${destinationSlug}/requirements-skeleton.json`);
  const planSkeleton = readJSON(`data/${destinationSlug}/plan-skeleton.json`);

  // Step 2: Identify days with location changes
  const locationChangeDays = planSkeleton.days.filter(day => day.location_change);

  if (locationChangeDays.length === 0) {
    return {
      agent: "transportation",
      status: "complete",
      data: {days: []},
      notes: "No inter-city transportation needed"
    };
  }

  // Step 3: Determine transportation mode (flight vs train)
  const routes = [];

  for (const day of locationChangeDays) {
    const {from, to} = day.location_change;
    const distance = calculateDistance(from, to);

    // Use flights for international or long-distance (>1000km)
    if (isInternational(from, to) || distance > 1000) {
      try {
        // Search flights
        const flightResult = await searchFlightWithRetry({
          origin: getAirportCode(from),
          destination: getAirportCode(to),
          departure_date: day.date,
          adults: requirements.trip_summary.travelers,
          currency: "USD"
        });

        // Get price analysis
        const priceAnalysis = await price_analysis({
          origin: getAirportCode(from),
          destination: getAirportCode(to),
          departure_date: day.date
        });

        const parsed = parseFlightOffer(flightResult.data[0]);
        const priceValue = analyzePriceValue(parsed.price.total, priceAnalysis);

        routes.push({
          day: day.day,
          location_change: {
            from: from,
            to: to,
            transportation: "Flight",
            ...parsed.flight,
            cost: parsed.price.total,
            price_analysis: priceValue,
            notes: priceValue.recommendation
          }
        });
      } catch (error) {
        console.error(`Flight search failed for day ${day.day}`, error);
        routes.push({
          day: day.day,
          location_change: {
            from: from,
            to: to,
            status: 'research_failed',
            error: error.message
          }
        });
      }
    } else {
      // Use Gaode Maps for domestic China routes
      // (see gaode-maps example)
    }

    // Rate limiting
    await sleep(200);
  }

  // Step 4: Save results
  const transportationData = {
    agent: "transportation",
    status: "complete",
    data: {days: routes},
    notes: "International flights via Amadeus API, domestic routes via Gaode Maps"
  };

  writeJSON(`data/${destinationSlug}/transportation.json`, transportationData);

  return "complete";
}
```

---

## Tips for Transportation Agent

1. **Use Amadeus for international flights**: More accurate pricing and schedule than web search

2. **Implement retry logic**: API calls can fail, exponential backoff helps

3. **Compare prices across dates**: Search +/- 3 days for flexibility

4. **Use price analysis**: Recommend optimal booking window

5. **Parse all segments**: Multi-city trips have complex itineraries

6. **Check baggage policies**: Include in cost estimate and notes

7. **Consider connection times**: Minimum 2-4 hours for international transfers

8. **Fall back gracefully**: If Amadeus fails, use WebSearch

9. **Include all costs**: Taxes, fees, baggage, airport transfers

10. **Document source**: Indicate if data from Amadeus or web search
