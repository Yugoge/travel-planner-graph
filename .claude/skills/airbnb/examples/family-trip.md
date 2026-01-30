# Example: Family Trip to Austin

Searching for vacation rental for a family of 4 staying 7 nights.

## Scenario

- **Destination**: Austin, TX
- **Dates**: June 15-22, 2026 (7 nights)
- **Guests**: 2 adults, 2 children (ages 8 and 10)
- **Budget**: $150-250/night
- **Requirements**: Full kitchen, washer/dryer, parking, WiFi, 2+ bedrooms

## Step 1: Search Listings

```javascript
/airbnb search

// Then use tool:
mcp__plugin_airbnb_airbnb__airbnb_search({
  location: "Austin, TX",
  checkin: "2026-06-15",
  checkout: "2026-06-22",
  adults: 2,
  children: 2,
  minPrice: 150,
  maxPrice: 250
})
```

**Results**: 28 properties found

**Initial filtering**:
```javascript
const filtered = results.filter(listing =>
  listing.rating >= 4.5 &&
  listing.isSuperhost &&
  listing.reviewCount >= 10 &&
  listing.bedrooms >= 2
)
```

**Top 5 candidates** after filtering: 12 properties

## Step 2: Load Details for Top Candidates

Select top 3 based on ratings and reviews:

```javascript
/airbnb details

// Property 1: "Cozy Hyde Park Family Home"
mcp__plugin_airbnb_airbnb__airbnb_listing_details({
  id: "789456123",
  checkin: "2026-06-15",
  checkout: "2026-06-22",
  adults: 2,
  children: 2
})

// Property 2: "Modern South Congress Loft"
mcp__plugin_airbnb_airbnb__airbnb_listing_details({
  id: "654321987",
  checkin: "2026-06-15",
  checkout: "2026-06-22",
  adults: 2,
  children: 2
})

// Property 3: "Spacious East Austin Duplex"
mcp__plugin_airbnb_airbnb__airbnb_listing_details({
  id: "987654321",
  checkin: "2026-06-15",
  checkout: "2026-06-22",
  adults: 2,
  children: 2
})
```

## Step 3: Compare Properties

### Property 1: Cozy Hyde Park Family Home
- **Rating**: 4.8 (143 reviews)
- **Bedrooms**: 3 bedrooms, 6 beds, 2 bathrooms
- **Superhost**: Yes
- **Amenities**: Full kitchen, washer/dryer, WiFi, 2 parking spots, backyard, AC
- **Pricing**:
  - Base: $180/night × 7 = $1,260
  - Cleaning fee: $100
  - Service fee: $136
  - **Total**: $1,496 ($214/night average)
- **House Rules**: No smoking, pets allowed (small dogs only), no parties
- **Cancellation**: Flexible (full refund 24 hours before)
- **Recent Review** (Jan 2026): "Perfect for families! Kids loved the backyard. Kitchen had everything we needed."

### Property 2: Modern South Congress Loft
- **Rating**: 4.9 (87 reviews)
- **Bedrooms**: 2 bedrooms, 4 beds, 2 bathrooms
- **Superhost**: Yes
- **Amenities**: Full kitchen, washer/dryer, WiFi, 1 parking spot, rooftop terrace, AC
- **Pricing**:
  - Base: $210/night × 7 = $1,470
  - Cleaning fee: $125
  - Service fee: $160
  - **Total**: $1,755 ($251/night average)
- **House Rules**: No smoking, no pets, no parties
- **Cancellation**: Moderate (full refund 5 days before)
- **Recent Review** (Dec 2025): "Amazing location! Walking distance to everything. Modern and clean."

### Property 3: Spacious East Austin Duplex
- **Rating**: 4.7 (96 reviews)
- **Bedrooms**: 3 bedrooms, 5 beds, 2.5 bathrooms
- **Superhost**: No
- **Amenities**: Full kitchen, washer/dryer, WiFi, free parking, patio, AC
- **Pricing**:
  - Base: $165/night × 7 = $1,155
  - Cleaning fee: $95
  - Service fee: $125
  - **Total**: $1,375 ($196/night average)
- **House Rules**: No smoking, no pets, quiet hours after 10pm
- **Cancellation**: Strict (50% refund up to 1 week before)
- **Recent Review** (Jan 2026): "Good value, but location is a bit far from downtown. Need a car."

## Step 4: Selection

**Winner: Property 1 - Cozy Hyde Park Family Home**

**Rationale**:
1. **Best for families**: 3 bedrooms, backyard, allows small pets
2. **Great location**: Hyde Park is central, walkable, family-friendly neighborhood
3. **Value**: $214/night average within budget
4. **Flexibility**: Flexible cancellation policy
5. **Recent positive feedback**: Reviews specifically mention families
6. **Superhost**: Reliable host with great reviews

**Alternatives**:
- Property 2: Over budget ($251/night), but excellent location if willing to spend more
- Property 3: Best price ($196/night), but not Superhost and strict cancellation

## Step 5: Output for Accommodation Agent

```json
{
  "name": "Cozy Hyde Park Family Home",
  "location": "Hyde Park, Austin, TX",
  "cost": 214,
  "total_cost": 1496,
  "type": "Vacation Rental (Airbnb)",
  "amenities": [
    "Full kitchen with dishwasher",
    "Washer/Dryer in unit",
    "High-speed WiFi",
    "2 free parking spots",
    "Backyard with patio",
    "Air conditioning",
    "3 bedrooms, 2 bathrooms"
  ],
  "notes": "Average per night $214 | Total for 7 nights: $1,496 (base: $1,260 + cleaning: $100 + service: $136) | Superhost | 4.8 stars (143 reviews) | Small pets allowed | Flexible cancellation (full refund 24 hours before) | Check-in: 3pm, Check-out: 11am | Recent review (Jan 2026): 'Perfect for families! Kids loved the backyard. Kitchen had everything we needed. Host was very responsive.'"
}
```

## Key Takeaways

1. **Search with complete parameters**: Dates and guest counts ensure accurate results
2. **Filter aggressively**: Start with 28 results, narrow to 3 for detailed analysis
3. **Verify amenities**: Kitchen and washer/dryer critical for family stays
4. **Calculate total cost**: Include all fees for accurate comparison
5. **Prioritize recent reviews**: Check what recent guests say about families
6. **Consider flexibility**: Flexible cancellation valuable for family travel
7. **Location matters**: Hyde Park offers walkability and family-friendly environment

## Common Pitfalls Avoided

- ❌ **Not including children in search**: Would miss guest capacity limits
- ❌ **Ignoring cleaning fees**: Property 3 looks cheapest per night but comparable when fees included
- ❌ **Skipping house rules**: Property 2 doesn't allow pets (deal-breaker if traveling with dog)
- ❌ **Overlooking cancellation policy**: Property 3's strict policy risky for family travel
- ❌ **Not reading recent reviews**: Property 1's reviews specifically mention families (important validation)

---

**Workflow time**: ~5-10 minutes from search to final selection with detailed analysis.
