# Example: Attraction Search in Paris

This example demonstrates how to search for top-rated museums in Paris using the TripAdvisor script.

## Prerequisites

Set environment variable:
```bash
export TRIPADVISOR_API_KEY="your_api_key_here"
```

## Step 1: Search Museums in Paris

**Command**:
```bash
python3 .claude/skills/tripadvisor/scripts/attractions.py search "Paris, France" \
  --category museums \
  --min-rating 4.0 \
  --max-results 5 \
  --sort-by rating
```

**Expected Output**:
```json
{
  "attractions": [
    {
      "id": "188151",
      "name": "Musée d'Orsay",
      "location": "1 Rue de la Légion d'Honneur, 75007 Paris, France",
      "rating": 4.6,
      "reviews_count": 78234,
      "price_usd": 16.0,
      "category": "museum",
      "hours": "9:30 AM - 6:00 PM",
      "duration_minutes": 180,
      "booking_required": false,
      "booking_url": "https://www.tripadvisor.com/Attraction_Review-g188151",
      "coordinates": {
        "lat": 48.8600,
        "lng": 2.3266
      }
    },
    {
      "id": "188679",
      "name": "Musée Rodin",
      "location": "77 Rue de Varenne, 75007 Paris, France",
      "rating": 4.5,
      "reviews_count": 23456,
      "price_usd": 14.0,
      "category": "museum",
      "hours": "10:00 AM - 6:30 PM",
      "duration_minutes": 120,
      "booking_required": false,
      "booking_url": "https://www.tripadvisor.com/Attraction_Review-g188679",
      "coordinates": {
        "lat": 48.8553,
        "lng": 2.3159
      }
    }
  ],
  "total_results": 156
}
```

## Step 2: Get Detailed Information

Get full details for Musée d'Orsay:

**Command**:
```bash
python3 .claude/skills/tripadvisor/scripts/attractions.py details 188151
```

**Expected Output**:
```json
{
  "id": "188151",
  "name": "Musée d'Orsay",
  "description": "The Musée d'Orsay is housed in a former railway station and features extensive collections of Impressionist and Post-Impressionist masterpieces...",
  "location": {
    "address": "1 Rue de la Légion d'Honneur, 75007 Paris, France",
    "coordinates": {
      "lat": 48.8600,
      "lng": 2.3266
    },
    "neighborhood": "7th arrondissement"
  },
  "rating": 4.6,
  "reviews_count": 78234,
  "price": {
    "amount_usd": 16.0,
    "currency": "EUR",
    "notes": "Free first Sunday of each month"
  },
  "hours": {
    "tuesday": "9:30 AM - 6:00 PM",
    "wednesday": "9:30 AM - 6:00 PM",
    "thursday": "9:30 AM - 9:45 PM",
    "friday": "9:30 AM - 6:00 PM",
    "saturday": "9:30 AM - 6:00 PM",
    "sunday": "9:30 AM - 6:00 PM",
    "monday": "Closed",
    "general": "Closed Mondays"
  },
  "booking": {
    "required": false,
    "advance_recommended": true,
    "url": "https://www.musee-orsay.fr/en/visit/tickets"
  },
  "features": [
    "Wheelchair accessible",
    "Audio guide available",
    "Photography allowed (no flash)",
    "Cafe and restaurant on-site"
  ],
  "duration_minutes": 180,
  "best_time_to_visit": "Thursday evenings less crowded, arrive at opening time",
  "reviews": [
    {
      "author": "ArtLover2026",
      "rating": 5,
      "date": "2026-01-20",
      "text": "Stunning collection of Impressionist art. The building itself is worth the visit. Book tickets online to skip the line!",
      "helpful_votes": 234
    }
  ],
  "traveler_tips": [
    "Book tickets online in advance to avoid 1-2 hour queues",
    "Thursday evening (open until 9:45 PM) is less crowded",
    "The cafe on 5th floor has beautiful views through the clock window",
    "Allow at least 3 hours to see the main collections"
  ]
}
```

## Step 3: Search Nearby Attractions

Find attractions within 2km of Musée d'Orsay:

**Command**:
```bash
python3 .claude/skills/tripadvisor/scripts/attractions.py nearby 48.8600 2.3266 \
  --radius 2 \
  --min-rating 4.0 \
  --max-results 5
```

This returns attractions like Musée Rodin, Les Invalides, and Tuileries Garden that are within walking distance.

## Integration with Travel Planning

**Workflow**:
1. Search attractions by city and category
2. Filter by rating (4.0+ recommended)
3. Get details for top attractions
4. Check traveler tips for best visit times
5. Find nearby attractions for clustered itinerary
6. Verify booking requirements before finalizing plan

**Output for Agents**:
```json
{
  "attraction": {
    "name": "Musée d'Orsay",
    "location": "7th arrondissement, Paris",
    "cost": 16.0,
    "duration_minutes": 180,
    "rating": 4.6,
    "reviews": 78234,
    "booking_required": false,
    "booking_url": "https://www.musee-orsay.fr/en/visit/tickets",
    "best_time": "Thursday evening or opening time",
    "tips": [
      "Book online to skip queues",
      "Thursday open until 9:45 PM",
      "Allow 3 hours minimum"
    ],
    "data_source": "tripadvisor"
  }
}
```
