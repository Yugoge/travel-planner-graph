# Amadeus Flight - Details Tools

Flight information and airline details for comprehensive flight research.

## Available Tools

### 1. flight_details

Get detailed information about a specific flight.

**MCP Tool**: `flight_details`

**Parameters**:
- `carrier_code` (required): IATA airline code (e.g., "AF", "BA", "UA")
- `flight_number` (required): Flight number (e.g., "382", "1234")
- `scheduled_date` (required): Flight date in ISO 8601 format (YYYY-MM-DD)

**Returns**:
- Aircraft type and configuration
- Scheduled departure/arrival times
- Terminal information
- Gate assignments (if available)
- Flight status (scheduled, delayed, cancelled)
- Historical on-time performance
- Meal service availability
- In-flight entertainment options
- WiFi availability

**Example**:
```javascript
// Get details for Air France flight AF382
flight_details({
  carrier_code: "AF",
  flight_number: "382",
  scheduled_date: "2026-06-15"
})
```

**Response Structure**:
```json
{
  "data": {
    "carrier": {
      "code": "AF",
      "name": "Air France"
    },
    "flight_number": "382",
    "scheduled_date": "2026-06-15",
    "departure": {
      "airport": {"iataCode": "PEK", "name": "Beijing Capital International"},
      "terminal": "3",
      "scheduled_time": "2026-06-15T13:30:00+08:00",
      "estimated_time": "2026-06-15T13:30:00+08:00"
    },
    "arrival": {
      "airport": {"iataCode": "CDG", "name": "Paris Charles de Gaulle"},
      "terminal": "2E",
      "scheduled_time": "2026-06-15T18:00:00+02:00",
      "estimated_time": "2026-06-15T18:00:00+02:00"
    },
    "aircraft": {
      "code": "77W",
      "name": "Boeing 777-300ER"
    },
    "service": {
      "meals": true,
      "wifi": true,
      "entertainment": true,
      "power_outlets": true
    },
    "on_time_performance": {
      "percentage": 87,
      "average_delay_minutes": 12
    }
  }
}
```

**Use Cases**:
- Verify flight schedule accuracy
- Check aircraft amenities
- Assess on-time reliability
- Plan airport connections
- Determine meal service availability

---

### 2. airline_info

Get detailed information about an airline.

**MCP Tool**: `airline_info`

**Parameters**:
- `carrier_code` (required): IATA airline code

**Returns**:
- Airline name and country
- Alliance membership (Star Alliance, oneworld, SkyTeam)
- Baggage policies
- Frequent flyer program
- Fleet information
- Service class offerings
- Customer service contact

**Example**:
```javascript
// Get info about Air France
airline_info({
  carrier_code: "AF"
})
```

**Response Structure**:
```json
{
  "data": {
    "code": "AF",
    "name": "Air France",
    "country": "France",
    "alliance": "SkyTeam",
    "baggage_policy": {
      "economy": {
        "checked": {"pieces": 1, "weight_kg": 23},
        "carry_on": {"pieces": 1, "weight_kg": 12}
      },
      "business": {
        "checked": {"pieces": 2, "weight_kg": 32},
        "carry_on": {"pieces": 2, "weight_kg": 18}
      }
    },
    "frequent_flyer": {
      "program": "Flying Blue",
      "partners": ["Delta", "KLM", "Virgin Atlantic"]
    },
    "service_classes": ["Economy", "Premium Economy", "Business", "La Première"],
    "fleet_size": 224,
    "contact": {
      "phone": "+33 1 41 56 78 00",
      "website": "https://www.airfrance.com"
    }
  }
}
```

**Use Cases**:
- Compare airline baggage policies
- Check alliance benefits
- Verify frequent flyer partnerships
- Assess service quality
- Plan multi-airline bookings

---

### 3. aircraft_specs

Get specifications for an aircraft type.

**MCP Tool**: `aircraft_specs`

**Parameters**:
- `aircraft_code` (required): IATA aircraft code (e.g., "77W", "388", "32A")

**Returns**:
- Aircraft manufacturer and model
- Seat configuration by class
- Total passenger capacity
- Range and speed
- Age and technology features
- Cabin amenities
- Environmental efficiency

**Example**:
```javascript
// Get specs for Boeing 777-300ER
aircraft_specs({
  aircraft_code: "77W"
})
```

**Response Structure**:
```json
{
  "data": {
    "code": "77W",
    "manufacturer": "Boeing",
    "model": "777-300ER",
    "configuration": {
      "first": 4,
      "business": 80,
      "premium_economy": 24,
      "economy": 184,
      "total": 292
    },
    "specifications": {
      "range_km": 13649,
      "cruise_speed_kmh": 905,
      "length_m": 73.9,
      "wingspan_m": 64.8
    },
    "amenities": {
      "wifi": true,
      "power_outlets": true,
      "entertainment_screens": true,
      "overhead_bins": "large",
      "lavatory_count": 10
    },
    "environmental": {
      "fuel_efficiency": "high",
      "noise_level": "moderate",
      "emissions_category": "Chapter 4"
    }
  }
}
```

**Use Cases**:
- Compare aircraft comfort levels
- Assess seat configuration
- Evaluate long-haul suitability
- Check amenity availability
- Plan seating preferences

---

### 4. airport_info

Get detailed airport information.

**MCP Tool**: `airport_info`

**Parameters**:
- `airport_code` (required): IATA airport code

**Returns**:
- Airport name and location
- Terminal layout
- Transportation options
- Facilities and services
- Operating hours
- Visa/transit requirements
- Lounge availability

**Example**:
```javascript
// Get info about Paris Charles de Gaulle
airport_info({
  airport_code: "CDG"
})
```

**Response Structure**:
```json
{
  "data": {
    "code": "CDG",
    "name": "Paris Charles de Gaulle Airport",
    "city": "Paris",
    "country": "France",
    "timezone": "Europe/Paris",
    "terminals": [
      {
        "number": "1",
        "airlines": ["Air France", "Lufthansa", "British Airways"],
        "facilities": ["Lounges", "Duty-free", "Restaurants"]
      },
      {
        "number": "2E",
        "airlines": ["Air France", "SkyTeam partners"],
        "facilities": ["Lounges", "Spa", "Hotels", "Shopping"]
      }
    ],
    "transportation": {
      "train": {
        "name": "RER B",
        "to_city_center": {"duration_minutes": 35, "cost_eur": 10}
      },
      "bus": {
        "name": "Roissybus",
        "to_city_center": {"duration_minutes": 60, "cost_eur": 13}
      },
      "taxi": {
        "to_city_center": {"duration_minutes": 45, "cost_eur": 55}
      }
    },
    "visa_requirements": {
      "transit": "Schengen visa or visa-free for certain nationalities",
      "entry": "Check specific country requirements"
    },
    "lounges": {
      "count": 12,
      "priority_pass": true,
      "airline_lounges": ["Air France", "Emirates", "Star Alliance"]
    }
  }
}
```

**Use Cases**:
- Plan airport connections
- Estimate transfer times
- Check visa requirements
- Find ground transportation
- Locate airport facilities

---

## Best Practices

### 1. Flight Verification

**Cross-reference schedule**:
```javascript
async function verifyFlightSchedule(carrierCode, flightNumber, date) {
  const details = await flight_details({
    carrier_code: carrierCode,
    flight_number: flightNumber,
    scheduled_date: date
  });

  return {
    is_scheduled: details.data.departure.scheduled_time !== null,
    on_time_likely: details.data.on_time_performance.percentage > 80,
    has_amenities: details.data.service.wifi && details.data.service.meals
  };
}
```

### 2. Airline Comparison

**Compare baggage policies**:
```javascript
async function compareBaggagePolicies(carrierCodes) {
  const airlines = await Promise.all(
    carrierCodes.map(code => airline_info({carrier_code: code}))
  );

  return airlines.map(airline => ({
    name: airline.data.name,
    economy_checked: airline.data.baggage_policy.economy.checked,
    business_checked: airline.data.baggage_policy.business.checked
  }));
}
```

### 3. Aircraft Comfort Assessment

**Evaluate long-haul comfort**:
```javascript
async function assessLongHaulComfort(aircraftCode) {
  const specs = await aircraft_specs({aircraft_code: aircraftCode});

  const comfortScore = {
    wifi: specs.data.amenities.wifi ? 1 : 0,
    power: specs.data.amenities.power_outlets ? 1 : 0,
    entertainment: specs.data.amenities.entertainment_screens ? 1 : 0,
    range: specs.data.specifications.range_km > 10000 ? 1 : 0
  };

  const totalScore = Object.values(comfortScore).reduce((a, b) => a + b, 0);

  return {
    score: totalScore,
    rating: totalScore >= 3 ? 'excellent' : totalScore >= 2 ? 'good' : 'basic',
    suitable_for_long_haul: totalScore >= 2
  };
}
```

### 4. Airport Connection Planning

**Calculate minimum connection time**:
```javascript
async function calculateConnectionTime(arrivalAirport, departureAirport) {
  if (arrivalAirport === departureAirport) {
    const airportInfo = await airport_info({airport_code: arrivalAirport});
    const terminalCount = airportInfo.data.terminals.length;

    return {
      same_terminal: 60,  // minutes
      different_terminal: terminalCount > 2 ? 120 : 90,
      international_to_domestic: 150
    };
  }

  // Different airports
  return {
    minimum: 240,  // 4 hours for different airports
    recommended: 360  // 6 hours to be safe
  };
}
```

### 5. Error Handling

**Handle missing data**:
```javascript
async function getFlightDetailsWithFallback(carrier, flightNumber, date) {
  try {
    const details = await flight_details({
      carrier_code: carrier,
      flight_number: flightNumber,
      scheduled_date: date
    });
    return {source: 'amadeus', data: details.data};
  } catch (error) {
    console.warn('Flight details unavailable, using basic info');
    return {
      source: 'fallback',
      data: {
        carrier: {code: carrier, name: 'Unknown'},
        flight_number: flightNumber,
        scheduled_date: date,
        note: 'Detailed information unavailable'
      }
    };
  }
}
```

## Integration with Transportation Agent

The transportation agent should:

1. **Load this file** for detailed flight information
2. **Use flight_details** to verify flight schedules
3. **Use airline_info** to check baggage policies
4. **Use aircraft_specs** to assess comfort for long flights
5. **Use airport_info** to plan airport transfers
6. **Include in recommendations** relevant details (amenities, baggage, transfers)

Example workflow:
```
1. User searches for flights Beijing → Paris
2. Agent gets search results with flight AF382
3. Agent loads flight details: /amadeus-flight details
4. Agent calls flight_details({carrier: "AF", flight_number: "382", date: "2026-06-15"})
5. Agent parses: aircraft=77W, wifi=yes, meals=yes, on-time=87%
6. Agent includes in recommendation: "Air France AF382, Boeing 777-300ER with WiFi and meals, 87% on-time record"
7. Agent saves to transportation.json
```
