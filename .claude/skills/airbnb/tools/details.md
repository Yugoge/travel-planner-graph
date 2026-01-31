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
- `listing`: id, name, url, description, propertyType
  - `host`: name, isSuperhost, responseRate, responseTime
  - `location`: city, neighborhood, lat/lng, address (partial)
  - `capacity`: bedrooms, beds, bathrooms, maxGuests
  - `amenities`: Array (WiFi, kitchen, washer, etc.)
  - `pricing`: basePrice, cleaningFee, serviceFee, total (if dates)
  - `policies`: checkIn, checkOut, houseRules[], cancellationPolicy
  - `rating`, `reviewCount`, `reviews[]`

**Example**:
```javascript
mcp__plugin_airbnb_airbnb__airbnb_listing_details({
  id: "12345678", checkin: "2026-06-15", checkout: "2026-06-22", adults: 2, children: 2
})
```

**Use Cases**: Verify amenities, check house rules, get total cost, review policy, read reviews, verify Superhost

---

## Best Practices

**Load details after filtering**: Search → filter top candidates → load details for top 3-5 only

**Include dates**: Required for accurate total cost (basePrice + cleaningFee + serviceFee)

**Match guest counts**: Use same parameters as search for consistent pricing

**Verify critical amenities**: Kitchen type, parking, WiFi speed, washer location, workspace, climate control

**Check house rules**: Smoking, pets, parties, quiet hours, extra guest fees

**Review analysis**: Focus on recent reviews (6 months), check cleanliness/accuracy mentions, verify amenities match

## Workflow Integration

1. **Filter top candidates**: rating ≥ 4.5, Superhost, reviewCount ≥ 10 → top 5
2. **Load details**: Include checkin/checkout/guest counts
3. **Verify requirements**: Check amenities and house rules
4. **Calculate costs**: nightlyAverage = total / nights
5. **Select best**: Highest rating, best value, recent reviews, Superhost

## Cost Calculation

```javascript
// avgPerNight = (basePrice × nights + cleaningFee + serviceFee) / nights
const avgPerNight = details.pricing.total / nights
```

**Output**: `cost` (avg/night), `total_cost`, notes with breakdown

**Hotel comparison**: Consider value adds (kitchen, washer, space, free parking)

## Error Handling

**Invalid ID**: Verify from search results, listing may be removed, try alternatives

**Dates unavailable**: Try ±1-2 days, check calendar URL, consider alternatives

**Missing details**: Check URL directly, review mentions, note uncertainty, prefer complete listings

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
