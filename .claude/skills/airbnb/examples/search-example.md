# Airbnb Search Example

Example of searching for vacation rentals using the Airbnb skill scripts.

## Scenario

Family of 4 (2 adults, 2 children) planning a week-long vacation in Austin, TX.

**Requirements**:
- Dates: June 15-22, 2026 (7 nights)
- Budget: $100-250 per night
- Full kitchen and laundry facilities
- Minimum 2 bedrooms

## Step 1: Search Listings

```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py "Austin, TX" \
  --checkin 2026-06-15 \
  --checkout 2026-06-22 \
  --adults 2 \
  --children 2 \
  --min-price 100 \
  --max-price 250
```

### Sample Output

```
Found 18 listings

1. Cozy Downtown Loft with Full Kitchen
   ID: 12345678
   Location: Downtown Austin, TX
   Type: Entire home
   Price: $180/night
   Bedrooms: 2 | Beds: 3 | Bathrooms: 2
   Max Guests: 6
   Rating: 4.9 (143 reviews)
   ⭐ Superhost
   URL: https://www.airbnb.com/rooms/12345678

2. Modern East Austin House
   ID: 23456789
   Location: East Austin, TX
   Type: Entire home
   Price: $220/night
   Bedrooms: 3 | Beds: 4 | Bathrooms: 2
   Max Guests: 8
   Rating: 4.8 (87 reviews)
   ⭐ Superhost
   URL: https://www.airbnb.com/rooms/23456789

3. Stylish South Congress Apartment
   ID: 34567890
   Location: South Congress, Austin, TX
   Type: Entire home
   Price: $195/night
   Bedrooms: 2 | Beds: 2 | Bathrooms: 1.5
   Max Guests: 5
   Rating: 4.7 (52 reviews)
   URL: https://www.airbnb.com/rooms/34567890

... (15 more listings)

More results available. Use --cursor 'eyJvZmZzZXQiOjIwfQ==' to see next page

View on Airbnb: https://www.airbnb.com/s/Austin--TX/homes?...
```

## Step 2: Filter Results

Based on search results, filter for top candidates:
- Rating >= 4.8
- Superhost status
- Review count >= 50
- Property type: Entire home

**Top candidates**: Listings #1 and #2

## Step 3: Get Detailed Information

Get details for listing #1 (ID: 12345678):

```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/airbnb/scripts/details.py 12345678 \
  --checkin 2026-06-15 \
  --checkout 2026-06-22 \
  --adults 2 \
  --children 2
```

### Sample Output

```
=== Cozy Downtown Loft with Full Kitchen ===

ID: 12345678
Type: Entire home
URL: https://www.airbnb.com/rooms/12345678

Location: Austin, TX
Neighborhood: Downtown
Coordinates: 30.2672, -97.7431

Capacity:
  Bedrooms: 2
  Beds: 3
  Bathrooms: 2
  Max Guests: 6

Host: Sarah M.
  ⭐ Superhost
  Response Rate: 100%
  Response Time: within an hour

Rating: 4.9 (143 reviews)

Pricing:
  Base Price: $180/night
  Cleaning Fee: $100
  Service Fee: $95
  Total: $1,455
  Average per Night: $207.86 (7 nights)

Amenities (28):
  • Full kitchen with dishwasher
  • In-unit washer and dryer
  • WiFi - 150+ Mbps
  • Dedicated workspace
  • Free street parking
  • Air conditioning
  • Heating
  • Smart TV with streaming
  • Coffee maker
  • Microwave
  • Refrigerator
  • Oven and stove
  • Dishes and silverware
  • Cooking basics
  • Hair dryer
  • Iron and ironing board
  • Hangers
  • Bed linens
  • Extra pillows and blankets
  • Blackout curtains
  ... and 8 more

Policies:
  Check-in: Flexible (after 3pm)
  Check-out: 11am
  Cancellation: Moderate (full refund 5 days before)
  House Rules:
    - No smoking
    - No pets
    - No parties or events
    - Quiet hours 10pm-8am

Description:
Welcome to our beautiful downtown Austin loft! This spacious 2-bedroom home is
perfect for families or small groups. Located within walking distance to the best
restaurants, bars, and live music venues on 6th Street. The fully equipped kitchen
has everything you need to cook meals, and the in-unit washer/dryer makes extended
stays convenient...

Recent Reviews (3):
  • Perfect location, super clean, and Sarah was an amazing host! Kitchen had everything
    we needed to cook meals. Great for our family of four.
    Date: 2026-01-15

  • Loved this place! Walking distance to everything downtown. Apartment was exactly
    as described. Would definitely stay again.
    Date: 2025-12-28

  • Great space with lots of natural light. Very quiet despite being downtown. Host
    was responsive and accommodating.
    Date: 2025-12-10
```

## Step 4: Compare Options

Get details for listing #2 to compare:

```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/airbnb/scripts/details.py 23456789 \
  --checkin 2026-06-15 \
  --checkout 2026-06-22 \
  --adults 2 \
  --children 2
```

## Step 5: Make Recommendation

Based on:
- **Listing #1**: $207.86/night avg, 4.9 rating, Superhost, downtown location
- **Listing #2**: $245/night avg, 4.8 rating, Superhost, more space (3BR)

**Recommendation**: Listing #1 (Cozy Downtown Loft)
- Better value ($207.86 vs $245/night)
- Higher rating (4.9 vs 4.8)
- More reviews (143 vs 87)
- Perfect location for tourist activities
- Has all required amenities (kitchen, washer/dryer)

## JSON Output for Accommodation Plan

```json
{
  "name": "Cozy Downtown Loft with Full Kitchen",
  "location": "Downtown Austin, TX (30.2672° N, 97.7431° W)",
  "cost": 208,
  "total_cost": 1455,
  "type": "Vacation Rental (Airbnb)",
  "amenities": [
    "Full kitchen with dishwasher",
    "In-unit washer/dryer",
    "WiFi (150+ Mbps)",
    "Dedicated workspace",
    "Free street parking",
    "Air conditioning",
    "Smart TV with streaming"
  ],
  "notes": "Average per night $208 | Total for 7 nights: $1,455 (base: $1,260 + cleaning: $100 + service: $95) | Superhost | 4.9 stars (143 reviews) | Host response: 100% within 1 hour | Check-in: flexible after 3pm, Check-out: 11am | House rules: No smoking, No pets, No parties | Cancellation: Moderate (full refund 5 days before) | Recent review (Jan 2026): 'Perfect location, super clean, Sarah was amazing host'"
}
```

## Tips

1. **Always specify dates**: Pricing varies significantly by date
2. **Include all guests**: Properties have capacity limits and may charge extra
3. **Filter by Superhost**: Generally better reliability and communication
4. **Check recent reviews**: Look for consistency in ratings and recurring themes
5. **Calculate total cost**: Include cleaning and service fees for accurate comparison
6. **Verify amenities**: Confirm critical features in property details
7. **Read house rules**: Ensure property allows your group composition (pets, children, etc.)
