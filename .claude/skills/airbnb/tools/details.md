# Airbnb - Details

Retrieve comprehensive information about specific Airbnb listings.

## MCP Tools

### Tool: airbnb_listing_details

**MCP Tool Name**: `mcp__plugin_airbnb_airbnb__airbnb_listing_details`

**Purpose**: Get detailed property information including amenities, house rules, policies, and host details.

**Parameters**:
- `id` (required): Airbnb listing ID (from search results)
- `checkin` (optional): Check-in date in YYYY-MM-DD format
- `checkout` (optional): Check-out date in YYYY-MM-DD format
- `adults` (optional): Number of adults (default: 1)
- `children` (optional): Number of children (default: 0)
- `infants` (optional): Number of infants (default: 0)
- `pets` (optional): Number of pets (default: 0)
- `ignoreRobotsText` (optional): Boolean to override robots.txt (use sparingly)

**Returns**:
- `listing`: Complete property details:
  - `id`: Listing ID
  - `name`: Property name
  - `url`: Direct link to listing
  - `description`: Full property description
  - `propertyType`: Type (entire place, private room, etc.)
  - `host`: Host information:
    - `name`: Host name
    - `isSuperhost`: Superhost status
    - `responseRate`: Response rate percentage
    - `responseTime`: Average response time
  - `location`: Location details:
    - `city`: City name
    - `neighborhood`: Neighborhood/area
    - `latitude`: GPS latitude
    - `longitude`: GPS longitude
    - `address`: Partial address (full address after booking)
  - `capacity`:
    - `bedrooms`: Number of bedrooms
    - `beds`: Number of beds
    - `bathrooms`: Number of bathrooms
    - `maxGuests`: Maximum guest capacity
  - `amenities`: Array of amenities (WiFi, kitchen, washer, etc.)
  - `pricing`:
    - `basePrice`: Price per night
    - `cleaningFee`: One-time cleaning fee
    - `serviceFee`: Airbnb service fee
    - `total`: Total cost for stay (if dates provided)
  - `policies`:
    - `checkIn`: Check-in time/instructions
    - `checkOut`: Check-out time
    - `houseRules`: Array of house rules
    - `cancellationPolicy`: Cancellation policy type
  - `rating`: Average rating
  - `reviewCount`: Total number of reviews
  - `reviews`: Recent reviews sample

**Example**:
```javascript
// Get details for a specific listing
mcp__plugin_airbnb_airbnb__airbnb_listing_details({
  id: "12345678",
  checkin: "2026-06-15",
  checkout: "2026-06-22",
  adults: 2,
  children: 2
})

// Response includes:
// - Complete amenities list
// - House rules and policies
// - Host information and ratings
// - Total cost with all fees
// - Location coordinates
// - Recent reviews
```

**Use Cases**:
- Verify amenities before recommending property
- Check house rules for restrictions (pets, smoking, events)
- Get total cost including all fees
- Review cancellation policy
- Read recent guest reviews
- Verify Superhost status and response rates
- Get exact location coordinates

---

## Best Practices

### When to Load Details

**After search filtering**, load details only for top candidates:
1. Search returns 20-30 results
2. Filter by rating, Superhost, review count
3. Load details for top 3-5 properties
4. Make final selection based on complete information

**Don't load details for every search result** (inefficient).

### Date-Specific Pricing

**Always include dates** to get accurate total cost:
```javascript
// GOOD: Get total cost for specific dates
airbnb_listing_details({
  id: "12345678",
  checkin: "2026-07-10",
  checkout: "2026-07-17"
})
// Returns: basePrice, cleaningFee, serviceFee, total

// LESS USEFUL: No dates means no total cost
airbnb_listing_details({
  id: "12345678"
})
// Returns: basePrice only (no fees, no total)
```

### Guest Configuration

**Match search parameters** for consistent pricing:
```javascript
// If you searched with 4 guests, use same for details
airbnb_listing_details({
  id: "12345678",
  adults: 2,
  children: 2,
  checkin: "2026-08-01",
  checkout: "2026-08-08"
})
// Ensures pricing reflects extra guest fees (if any)
```

### Amenity Verification

**Check critical amenities**:
- **Kitchen**: Full kitchen vs. kitchenette
- **Parking**: Free, paid, street only
- **WiFi**: Speed and reliability mentioned in reviews
- **Washer/Dryer**: In-unit vs. shared
- **Workspace**: Dedicated desk and chair
- **AC/Heating**: Climate control for weather

```javascript
const details = airbnb_listing_details({ id: "..." })

// Verify amenities
const hasFullKitchen = details.amenities.some(a =>
  a.toLowerCase().includes('kitchen') && !a.includes('kitchenette')
)
const hasParking = details.amenities.some(a =>
  a.toLowerCase().includes('parking')
)
```

### House Rules Check

**Critical for family/group travel**:
- **No smoking**: Check if enforced
- **No pets**: May have exceptions or fees
- **No parties**: Important for group bookings
- **Quiet hours**: Relevant for families with children
- **Additional guests**: Extra fees or restrictions

```javascript
const details = airbnb_listing_details({ id: "..." })

// Check house rules
const allowsPets = !details.policies.houseRules.some(rule =>
  rule.toLowerCase().includes('no pets')
)
const allowsEvents = !details.policies.houseRules.some(rule =>
  rule.toLowerCase().includes('no parties') ||
  rule.toLowerCase().includes('no events')
)
```

### Review Analysis

**Focus on recent reviews** (within 6 months):
- Check for consistency in ratings
- Look for mentions of cleanliness, accuracy, communication
- Note any recurring issues
- Verify amenities mentioned in reviews match listing

```javascript
const details = airbnb_listing_details({ id: "..." })

// Prioritize recent reviews
const recentReviews = details.reviews.filter(review =>
  new Date(review.date) > new Date('2025-07-01')
)

// Check for red flags
const hasCleanlinessIssues = recentReviews.some(review =>
  review.text.toLowerCase().includes('dirty') ||
  review.text.toLowerCase().includes('not clean')
)
```

## Workflow Integration

### Accommodation Agent Workflow

After getting search results:

1. **Filter top candidates**:
   ```javascript
   const topCandidates = searchResults.filter(listing =>
     listing.rating >= 4.5 &&
     listing.isSuperhost &&
     listing.reviewCount >= 10
   ).slice(0, 5)
   ```

2. **Load details for each**:
   ```javascript
   const detailedListings = topCandidates.map(candidate =>
     airbnb_listing_details({
       id: candidate.id,
       checkin: tripDates.start,
       checkout: tripDates.end,
       adults: guestCounts.adults,
       children: guestCounts.children
     })
   )
   ```

3. **Verify requirements**:
   ```javascript
   const meetsCriteria = detailedListings.filter(listing => {
     const hasRequiredAmenities = requiredAmenities.every(amenity =>
       listing.amenities.some(a => a.toLowerCase().includes(amenity))
     )
     const allowsPets = guestCounts.pets > 0 ?
       !listing.policies.houseRules.includes('No pets') : true

     return hasRequiredAmenities && allowsPets
   })
   ```

4. **Calculate total costs**:
   ```javascript
   const withCosts = meetsCriteria.map(listing => ({
     ...listing,
     nightlyAverage: listing.pricing.total / numberOfNights,
     totalCost: listing.pricing.total
   }))
   ```

5. **Select best option**:
   - Highest rating among options meeting criteria
   - Best value (cost vs. amenities)
   - Most recent positive reviews
   - Superhost preferred

## Cost Calculation

### Complete Cost Breakdown

```javascript
const details = airbnb_listing_details({
  id: "12345678",
  checkin: "2026-06-15",
  checkout: "2026-06-22" // 7 nights
})

// Calculate per-night average
const baseTotal = details.pricing.basePrice * 7  // e.g., $150 × 7 = $1,050
const cleaningFee = details.pricing.cleaningFee   // e.g., $100
const serviceFee = details.pricing.serviceFee     // e.g., $110
const grandTotal = baseTotal + cleaningFee + serviceFee  // $1,260
const avgPerNight = grandTotal / 7  // $180/night

// Output for accommodation agent
{
  "cost": 180,  // Average per night
  "total_cost": 1260,  // Complete total
  "notes": "Average per night $180 | Total for 7 nights: $1,260 (includes $100 cleaning fee, $110 service fee)"
}
```

### Compare with Hotels

When comparing rental vs. hotel:
```javascript
const rentalAvgNight = rentalTotal / nights
const hotelAvgNight = hotelRatePerNight

// Factor in value adds for rentals
const rentalValueAdds = {
  kitchen: true,   // Save on dining out
  washer: true,    // Save on laundry services
  space: true,     // More room than hotel
  parking: true    // Often free vs. hotel fees
}

// Rental may be higher per night but better value
```

## Error Handling

### Invalid Listing ID
```javascript
// If listing not found:
// 1. Verify ID from search results
// 2. Listing may have been removed
// 3. Try alternative listings
```

### Dates Unavailable
```javascript
// If dates not available:
// 1. Try nearby dates (±1-2 days)
// 2. Check calendar in listing URL
// 3. Consider alternative properties
```

### Missing Details
```javascript
// If critical details missing:
// 1. Check listing URL directly
// 2. Look for recent reviews mentioning amenity
// 3. Note uncertainty in output
// 4. Prefer listings with complete information
```

## Output Structure

For accommodation agent JSON:

```json
{
  "name": "Modern Downtown Apartment",
  "location": "Downtown Seattle, WA (47.6062° N, 122.3321° W)",
  "cost": 195,
  "total_cost": 1365,
  "type": "Vacation Rental (Airbnb)",
  "amenities": [
    "Full kitchen with dishwasher",
    "In-unit washer/dryer",
    "High-speed WiFi (100+ Mbps)",
    "Dedicated workspace",
    "Free parking (1 spot)",
    "Air conditioning",
    "Smart TV with Netflix"
  ],
  "notes": "Average per night $195 | Total for 7 nights: $1,365 (base: $1,155 + cleaning: $125 + service: $85) | Superhost | 4.9 stars (87 reviews) | Host response rate: 100% within 1 hour | Check-in: 3pm (flexible), Check-out: 11am | House rules: No smoking, No pets, No parties | Cancellation: Moderate (full refund 5 days before) | Recent review (Jan 2026): 'Spotless apartment, perfect location, very responsive host'"
}
```

**Include in notes**:
- Total cost breakdown
- Superhost status
- Rating and review count
- Host responsiveness
- Check-in/check-out times
- House rules summary
- Cancellation policy
- Recent review highlight

---

**Integration**: Use this tool after `/airbnb search` to verify property details before final recommendation.
