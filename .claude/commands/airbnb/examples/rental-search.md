# Example: Vacation Rental Search

Complete workflow for finding vacation rentals using Airbnb skill.

## Scenario

Family of 4 traveling to Paris for 6 nights. Need apartment with kitchen and washer for extended stay. Budget max $200/night.

## Step-by-Step Workflow

### Step 1: Load Search Tools

```markdown
Load search category: /root/travel-planner/.claude/commands/airbnb/tools/search.md
```

This loads the `search_listings`, `filter_by_amenities`, `get_listing_details`, and `get_host_reviews` tools.

### Step 2: Initial Search

```javascript
// Search for family apartments in Paris
const searchResults = await search_listings({
  location: "Paris, France",
  check_in: "2026-06-15",
  check_out: "2026-06-21",
  guests: 4,
  price_max: 200,
  room_type: "entire_place",
  bedrooms: 2
});

// Response structure:
{
  listings: [
    {
      listing_id: "12345678",
      name: "Charming 2BR Apartment in Le Marais",
      room_type: "entire_place",
      price_per_night: 180,
      total_price: 1280,  // Includes cleaning fee, service fee, taxes
      bedrooms: 2,
      beds: 3,
      bathrooms: 1,
      max_guests: 5,
      rating: 4.8,
      review_count: 127,
      is_superhost: true,
      location: {
        city: "Paris",
        neighborhood: "Le Marais",
        lat: 48.8584,
        lng: 2.3522
      },
      amenities: ["wifi", "kitchen", "washer", "heating", "tv"],
      thumbnail: "https://..."
    },
    // ... more listings
  ],
  total_results: 45
}
```

### Step 3: Filter by Required Amenities

```javascript
// Extract listing IDs from search results
const listingIds = searchResults.listings.map(l => l.listing_id);

// Filter for must-have amenities
const filtered = await filter_by_amenities({
  listing_ids: listingIds,
  amenities: ["kitchen", "washer", "wifi", "workspace"]
});

// Response:
{
  filtered_listings: [
    {
      listing_id: "12345678",
      matched_amenities: ["kitchen", "washer", "wifi", "workspace", "heating", "tv"],
      missing_amenities: []
    },
    {
      listing_id: "87654321",
      matched_amenities: ["kitchen", "washer", "wifi", "workspace"],
      missing_amenities: []
    }
    // Listings without all amenities are excluded
  ]
}
```

### Step 4: Get Detailed Information

```javascript
// Get details for top 3 matches
const topListings = filtered.filtered_listings.slice(0, 3);

const details = await Promise.all(
  topListings.map(listing =>
    get_listing_details({ listing_id: listing.listing_id })
  )
);

// Response for one listing:
{
  listing_id: "12345678",
  description: "Beautiful 2-bedroom apartment in the heart of Le Marais...",
  amenities: [
    "WiFi",
    "Full kitchen with dishwasher",
    "Washing machine",
    "Dedicated workspace",
    "Smart TV",
    "Air conditioning",
    "Heating",
    "Elevator"
  ],
  house_rules: {
    check_in_time: "15:00",
    check_out_time: "11:00",
    quiet_hours: "22:00 - 08:00",
    no_smoking: true,
    no_pets: true,
    no_parties: true,
    additional_rules: "Please remove shoes indoors"
  },
  cancellation_policy: "Flexible: Full refund up to 24 hours before check-in",
  minimum_nights: 3,
  maximum_nights: 28,
  cleaning_fee: 80,
  security_deposit: 0,
  extra_people_fee: 0,
  neighborhood_description: "Le Marais is a historic district known for...",
  host_about: "I'm Marie, a Paris native who loves sharing my city..."
}
```

### Step 5: Check Reviews

```javascript
// Get reviews for top choice
const reviews = await get_host_reviews({
  listing_id: "12345678",
  limit: 15
});

// Response:
{
  overall_rating: 4.8,
  rating_breakdown: {
    cleanliness: 4.9,
    accuracy: 4.8,
    communication: 5.0,
    location: 4.7,
    checkin: 4.9,
    value: 4.6
  },
  review_count: 127,
  reviews: [
    {
      id: "rev123",
      created_at: "2026-05-15",
      rating: 5,
      reviewer_name: "Jennifer",
      comments: "Perfect apartment for our family! The kitchen was fully equipped and the location was excellent for exploring Paris. Marie was very responsive and helpful.",
      reviewer_id: "user456"
    },
    {
      id: "rev124",
      created_at: "2026-05-10",
      rating: 5,
      reviewer_name: "David",
      comments: "Clean, comfortable, and exactly as described. Great for a longer stay.",
      reviewer_id: "user789"
    }
    // ... more reviews
  ],
  host_response_rate: 100,
  host_response_time: "within an hour",
  is_superhost: true,
  years_hosting: 5,
  total_listings: 2
}
```

### Step 6: Calculate Total Cost

```javascript
function calculateTotalCost(listing, nights) {
  const basePrice = listing.price_per_night * nights;
  const cleaningFee = 80;  // From listing details
  const serviceFee = Math.round(basePrice * 0.14);  // Airbnb service fee
  const taxes = Math.round(basePrice * 0.10);  // Estimated local taxes

  return {
    base_price: basePrice,
    cleaning_fee: cleaningFee,
    service_fee: serviceFee,
    taxes: taxes,
    total: basePrice + cleaningFee + serviceFee + taxes,
    per_night_avg: Math.round((basePrice + cleaningFee + serviceFee + taxes) / nights)
  };
}

const cost = calculateTotalCost({ price_per_night: 180 }, 6);

// Result:
{
  base_price: 1080,
  cleaning_fee: 80,
  service_fee: 151,
  taxes: 108,
  total: 1419,
  per_night_avg: 237  // Above budget when fees included
}
```

### Step 7: Compare with Hotels

```javascript
// Also search hotels for comparison
const hotelOptions = await searchHotels({
  city: "Paris, France",
  checkin: "2026-06-15",
  checkout: "2026-06-21",
  guests: 4,
  rooms: 2
});

const hotelBest = hotelOptions[0];
const hotelTotal = hotelBest.price_per_night * 6 * 2;  // 2 rooms needed

// Comparison:
const comparison = {
  airbnb: {
    name: "Charming 2BR Apartment in Le Marais",
    total_cost: 1419,
    per_person: 355,
    pros: [
      "Full kitchen saves on meals",
      "Washer for laundry",
      "More space for family",
      "Local neighborhood experience"
    ],
    cons: [
      "No daily housekeeping",
      "Self check-in only",
      "Higher upfront cost with fees"
    ]
  },
  hotel: {
    name: hotelBest.name,
    total_cost: hotelTotal,
    per_person: hotelTotal / 4,
    pros: [
      "Daily housekeeping",
      "24/7 front desk",
      "Hotel amenities (gym, breakfast)",
      "Easier cancellation"
    ],
    cons: [
      "Need 2 rooms for family",
      "No kitchen",
      "Less space",
      "Tourist area pricing"
    ]
  }
};

// Recommendation logic
function recommendAccommodation(airbnb, hotel, nights, guests) {
  // For families with 4+ guests and 5+ nights, Airbnb often better value
  if (nights >= 5 && guests >= 4) {
    const airbnbValue = airbnb.total_cost / (nights * guests);
    const hotelValue = hotel.total_cost / (nights * guests);

    if (airbnbValue < hotelValue * 1.2) {  // Allow 20% premium for space/kitchen
      return {
        choice: "airbnb",
        reason: "Better value for extended family stay with kitchen and space"
      };
    }
  }

  return {
    choice: "hotel",
    reason: "Better for shorter stays with hotel services"
  };
}
```

### Step 8: Save to Accommodation JSON

```javascript
const selectedListing = {
  listing_id: "12345678",
  name: "Charming 2BR Apartment in Le Marais",
  price_per_night: 180,
  total_cost: 1419,
  bedrooms: 2,
  rating: 4.8,
  reviews: 127
};

const accommodationData = {
  agent: "accommodation",
  status: "complete",
  data: {
    days: [
      {
        day: 1,
        accommodation: {
          name: selectedListing.name,
          location: "Le Marais, Paris, France",
          cost: 237,  // Average per night including all fees
          type: "Vacation Rental (Airbnb)",
          amenities: [
            "Full kitchen",
            "Washer",
            "WiFi",
            "Workspace",
            "TV",
            "Elevator"
          ],
          notes: [
            "Check-in: 3pm, Check-out: 11am",
            "Cleaning fee: $80 (one-time)",
            "Total for 6 nights: $1,419",
            "Superhost with 127 reviews (4.8 stars)",
            "Self check-in with keypad",
            "Quiet hours: 10pm - 8am"
          ].join(" | ")
        }
      },
      // Days 2-6 same accommodation
      { day: 2, accommodation: { same_as_day: 1 } },
      { day: 3, accommodation: { same_as_day: 1 } },
      { day: 4, accommodation: { same_as_day: 1 } },
      { day: 5, accommodation: { same_as_day: 1 } },
      { day: 6, accommodation: { same_as_day: 1 } }
    ]
  },
  notes: "Airbnb rental selected for family stay. Kitchen saves on dining costs. Book soon as availability changes frequently. Verify final price on Airbnb as rates may fluctuate."
};

// Save to: data/{destination-slug}/accommodation.json
writeJSON(`data/paris-family-trip/accommodation.json`, accommodationData);
```

---

## Error Handling Example

### Scenario: MCP Server Unavailable

```javascript
async function searchRentalsWithFallback(location, checkIn, checkOut, guests) {
  try {
    // Try Airbnb MCP first
    const listings = await search_listings({
      location: location,
      check_in: checkIn,
      check_out: checkOut,
      guests: guests,
      room_type: "entire_place"
    });

    return {
      source: 'airbnb_mcp',
      data: listings
    };
  } catch (error) {
    console.warn('Airbnb MCP unavailable, falling back to WebSearch');

    // Fallback to WebSearch
    const searchQuery = `Airbnb ${location} ${checkIn} to ${checkOut} ${guests} guests vacation rental`;
    const searchResults = await WebSearch({ query: searchQuery });

    return {
      source: 'web_search',
      data: parseWebSearchRentals(searchResults),
      warning: 'Data from web search, prices may not be current. Verify on Airbnb.'
    };
  }
}
```

---

## Retry Logic Example

### Scenario: Rate Limiting

```javascript
async function searchWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_listings(params);
    } catch (error) {
      // Retry on transient errors
      if (error.status === 429 || error.status >= 500) {
        const delay = 1000 * Math.pow(2, i);  // Exponential backoff: 1s, 2s, 4s
        console.warn(`Rate limited, retry ${i + 1}/${maxRetries} after ${delay}ms`);
        await sleep(delay);
        continue;
      }

      // Don't retry on permanent errors
      throw error;
    }
  }

  throw new Error('Max retries exceeded');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

---

## Best Practices Summary

### 1. Always Filter by Amenities

Don't rely on search results alone:
```javascript
// Bad: Accept first result
const listing = searchResults.listings[0];

// Good: Filter for requirements first
const filtered = await filter_by_amenities({
  listing_ids: searchResults.listings.map(l => l.listing_id),
  amenities: ["kitchen", "washer", "wifi"]
});
```

### 2. Check Reviews Before Recommending

```javascript
// Verify quality with reviews
const reviews = await get_host_reviews({ listing_id: listing.listing_id });

if (reviews.overall_rating < 4.5 || reviews.review_count < 10) {
  console.warn('Low rating or few reviews, consider alternative');
}

// Check recent reviews (within 6 months)
const recentReviews = reviews.reviews.filter(r =>
  new Date(r.created_at) > new Date(Date.now() - 6 * 30 * 24 * 60 * 60 * 1000)
);

if (recentReviews.length < 3) {
  console.warn('Few recent reviews, property may have changed');
}
```

### 3. Calculate Total Cost Including Fees

```javascript
// Always show total cost, not just nightly rate
const nights = 6;
const totalCost = {
  base: listing.price_per_night * nights,
  cleaning: 80,
  service: Math.round(listing.price_per_night * nights * 0.14),
  taxes: Math.round(listing.price_per_night * nights * 0.10)
};
totalCost.total = Object.values(totalCost).reduce((a, b) => a + b, 0);
```

### 4. Compare with Hotel Options

```javascript
// Always provide comparison for informed decision
const airbnbOption = await searchAirbnb(...);
const hotelOption = await searchHotels(...);

return {
  recommended: airbnbOption.total_cost < hotelOption.total_cost ? 'airbnb' : 'hotel',
  comparison: { airbnb: airbnbOption, hotel: hotelOption }
};
```

### 5. Note Important Details

```javascript
// Include crucial information in notes
const notes = [
  `Check-in: ${details.house_rules.check_in_time}`,
  `Minimum stay: ${details.minimum_nights} nights`,
  `Cancellation: ${details.cancellation_policy}`,
  `Cleaning fee: $${details.cleaning_fee}`,
  details.house_rules.no_pets ? 'No pets allowed' : 'Pets allowed',
  `Superhost: ${reviews.is_superhost ? 'Yes' : 'No'}`
].join(' | ');
```

---

## Tips for Accommodation Agent

1. **Load Airbnb skill for family/group travel**: When guests >= 4 or nights >= 5

2. **Compare options**: Always check both Airbnb and hotels, recommend best value

3. **Filter aggressively**: Use amenity filtering to match exact requirements

4. **Verify with reviews**: Don't recommend listings with <4.5 rating or <10 reviews

5. **Calculate total cost**: Include cleaning fee, service fee, and taxes in recommendations

6. **Check recent reviews**: Reviews older than 6 months may not reflect current state

7. **Note limitations**: Highlight house rules, check-in requirements, cancellation policies

8. **Graceful fallback**: If MCP unavailable, use WebSearch and note data limitations

9. **Location matters**: Prefer listings near attractions or with good transit access

10. **Superhost priority**: Prioritize Superhosts for reliability and responsiveness
