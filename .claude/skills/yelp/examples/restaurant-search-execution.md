# Yelp Restaurant Search - Script Execution Example

This example demonstrates executing Yelp MCP scripts to search restaurants and get detailed information.

## Scenario

Find top-rated Italian restaurants in San Francisco for dinner, budget-friendly ($$ or less).

## Step 1: Search Restaurants

Execute search script with filters:

```bash
cd /root/travel-planner/.claude/skills/yelp/scripts
export YELP_API_KEY=your_api_key_here

python3 search.py search "italian restaurant" "San Francisco, CA" --price=1,2 --limit=10
```

### Expected Output

```
Found 10 of 147 restaurants:

1. Tony's Pizza Napoletana
   Rating: 4.5★ (2,847 reviews)
   Price: $$
   Categories: Italian, Pizza
   Address: 1570 Stockton St, San Francisco
   ID: tonys-pizza-napoletana-san-francisco

2. Flour + Water
   Rating: 4.4★ (3,124 reviews)
   Price: $$
   Categories: Italian, Pasta Shops
   Address: 2401 Harrison St, San Francisco
   ID: flour-water-san-francisco

3. SPQR
   Rating: 4.3★ (1,892 reviews)
   Price: $$
   Categories: Italian, Wine Bars
   Address: 1911 Fillmore St, San Francisco
   ID: spqr-san-francisco

...
```

## Step 2: Get Business Details

Get complete information for top choice:

```bash
python3 details.py tonys-pizza-napoletana-san-francisco
```

### Expected Output

```
Tony's Pizza Napoletana
=======================

Rating: 4.5★ (2,847 reviews)
Price: $$
Categories: Italian, Pizza, Cocktail Bars

Address:
1570 Stockton St, San Francisco, CA, 94133

Coordinates: 37.8014, -122.4104

Contact:
Phone: +14159453900
Website: https://www.yelp.com/biz/tonys-pizza-napoletana-san-francisco

Transactions: delivery, pickup, restaurant_reservation
Photos: 15 available

Operating Hours:
Status: Currently Open

Mon: 11:30-22:00
Tue: 11:30-22:00
Wed: 11:30-22:00
Thu: 11:30-22:00
Fri: 11:30-23:00
Sat: 11:30-23:00
Sun: 11:30-22:00
```

## Step 3: Search by Category

Find vegetarian options nearby:

```bash
python3 search.py category vegetarian "San Francisco, CA" --price=1,2 --limit=5
```

### Expected Output

```
Found 5 of 89 restaurants:

1. Greens Restaurant
   Rating: 4.2★ (2,156 reviews)
   Price: $$
   Categories: Vegetarian, American
   Address: Fort Mason Center, San Francisco
   ID: greens-restaurant-san-francisco

2. Gracias Madre
   Rating: 4.1★ (1,743 reviews)
   Price: $$
   Categories: Vegan, Mexican
   Address: 2211 Mission St, San Francisco
   ID: gracias-madre-san-francisco

...
```

## Step 4: Geographic Search

Find breakfast cafes within 500m of hotel location:

```bash
python3 search.py search "breakfast cafe" --lat=37.7749 --lon=-122.4194 --radius=500 --categories=breakfast_brunch,cafes --price=1,2 --open-now
```

### Expected Output

```
Found 7 of 32 restaurants:

1. Sightglass Coffee
   Rating: 4.4★ (1,234 reviews)
   Price: $
   Categories: Coffee & Tea, Cafes
   Address: 270 7th St, San Francisco
   ID: sightglass-coffee-san-francisco

2. Bluestone Lane
   Rating: 4.2★ (856 reviews)
   Price: $$
   Categories: Cafes, Australian, Breakfast & Brunch
   Address: 149 Montgomery St, San Francisco
   ID: bluestone-lane-san-francisco

...
```

## Integration with Travel Planning

### Usage in Agent Workflow

```python
# Meals agent workflow
location = "San Francisco, CA"
meal_type = "dinner"
budget_level = "2,3"  # $$ to $$$
cuisine_preference = "italian"

# Step 1: Search restaurants
result = search_by_category(
    category=cuisine_preference,
    location=location,
    price=budget_level,
    radius=2000,
    limit=15
)

# Step 2: Filter by quality
restaurants = [
    b for b in result['businesses']
    if b['rating'] >= 3.5 and b['review_count'] >= 20
]

# Step 3: Get details for top choices
for restaurant in restaurants[:3]:
    details = get_business_details(restaurant['id'])
    # Verify hours, location, and add to itinerary
```

## Error Handling Example

### Invalid API Key

```bash
python3 search.py search "restaurants" "San Francisco"
```

```
Error: Invalid API key. Check YELP_API_KEY environment variable.
```

### Rate Limit Exceeded

```
Error: Rate limit exceeded. Please try again later.
```

Script automatically retries with exponential backoff (1s, 2s, 4s).

## Performance

- Average search time: 2-3 seconds
- Average details lookup: 1-2 seconds
- Retry overhead: +3-7 seconds on transient errors
- Rate limit: 5,000 calls/day (free tier)

## Notes

- Business IDs are permanent identifiers
- Coordinates use WGS84 (latitude, longitude)
- Price levels: $ (<$10), $$ ($11-30), $$$ ($31-60), $$$$ (>$61) per person
- Radius in meters (max 40,000m = 40km)
- Categories use Yelp's standardized aliases
