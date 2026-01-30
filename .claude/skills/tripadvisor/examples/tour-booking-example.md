# Example: Tour Booking in Paris

This example demonstrates how to search for food tours in Paris and check availability for booking.

## Prerequisites

Set environment variable:
```bash
export TRIPADVISOR_API_KEY="your_api_key_here"
```

## Step 1: Search Evening Food Tours

**Command**:
```bash
python3 .claude/skills/tripadvisor/scripts/tours.py search "Paris, France" \
  --category food-tours \
  --time evening \
  --min-rating 4.5 \
  --date 2026-02-20 \
  --max-results 5
```

**Expected Output**:
```json
{
  "tours": [
    {
      "id": "67890",
      "name": "Paris Evening Food Tour",
      "provider": "Local Food Tours Paris",
      "location": "Latin Quarter, Paris",
      "rating": 4.8,
      "reviews_count": 2340,
      "price_usd": 95.0,
      "duration_hours": 3.5,
      "category": "food-tour",
      "time_of_day": "evening",
      "group_size": "Small group (max 12)",
      "languages": ["English", "French"],
      "pickup_included": false,
      "cancellation_policy": "Free cancellation up to 24 hours",
      "booking_url": "https://www.tripadvisor.com/AttractionProductReview-67890",
      "available_dates": ["2026-02-20", "2026-02-21", "2026-02-22"]
    },
    {
      "id": "67891",
      "name": "Montmartre Food and Wine Tasting",
      "provider": "Montmartre Gourmet Tours",
      "location": "Montmartre, Paris",
      "rating": 4.7,
      "reviews_count": 1856,
      "price_usd": 85.0,
      "duration_hours": 3.0,
      "category": "food-tour",
      "time_of_day": "evening",
      "group_size": "Small group (max 10)",
      "languages": ["English"],
      "pickup_included": false,
      "cancellation_policy": "Free cancellation up to 48 hours",
      "booking_url": "https://www.tripadvisor.com/AttractionProductReview-67891",
      "available_dates": ["2026-02-20", "2026-02-21"]
    }
  ],
  "total_results": 23
}
```

## Step 2: Get Full Tour Details

**Command**:
```bash
python3 .claude/skills/tripadvisor/scripts/tours.py details 67890 --date 2026-02-20
```

**Expected Output**:
```json
{
  "id": "67890",
  "name": "Paris Evening Food Tour",
  "description": "Discover authentic Parisian cuisine with a local guide in the historic Latin Quarter. Visit 6 food stops including traditional bistros, cheese shops, and patisseries.",
  "provider": {
    "name": "Local Food Tours Paris",
    "rating": 4.9,
    "years_operating": 8
  },
  "location": {
    "meeting_point": "Latin Quarter Metro Station",
    "address": "Place Saint-Michel, 75005 Paris",
    "coordinates": {
      "lat": 48.8534,
      "lng": 2.3434
    }
  },
  "rating": 4.8,
  "reviews_count": 2340,
  "price": {
    "amount_usd": 95.0,
    "currency": "USD",
    "includes": [
      "All food tastings (6 stops)",
      "Local expert guide",
      "Wine pairing at final stop",
      "Recipe booklet"
    ]
  },
  "schedule": {
    "duration_hours": 3.5,
    "start_time": "18:30",
    "end_time": "22:00",
    "days_available": ["Monday", "Wednesday", "Thursday", "Friday", "Saturday"]
  },
  "group_details": {
    "size": "Small group (max 12)",
    "languages": ["English", "French"],
    "age_requirement": "18+ (wine tasting included)"
  },
  "logistics": {
    "pickup_included": false,
    "meeting_instructions": "Meet at fountain in Place Saint-Michel, look for guide with red umbrella",
    "end_location": "Same as meeting point",
    "accessibility": "Walking tour, not wheelchair accessible"
  },
  "cancellation": {
    "policy": "Free cancellation up to 24 hours before start",
    "refund_percentage": 100
  },
  "availability": {
    "date": "2026-02-20",
    "available": true,
    "spots_remaining": 4,
    "next_available_dates": ["2026-02-20", "2026-02-21", "2026-02-22"]
  },
  "booking_url": "https://www.tripadvisor.com/AttractionProductReview-67890",
  "highlights": [
    "Visit 6 authentic food spots in Latin Quarter",
    "Taste French cheese, charcuterie, pastries, wine",
    "Small group (max 12) for personalized experience",
    "Expert local guide sharing culinary history"
  ],
  "reviews": [
    {
      "author": "FoodieTravel2026",
      "rating": 5,
      "date": "2026-01-15",
      "text": "Best food tour ever! Guide was knowledgeable and the food stops were amazing. Highly recommend!",
      "helpful_votes": 45
    }
  ],
  "traveler_tips": [
    "Come hungry - plenty of food at each stop",
    "Wear comfortable walking shoes",
    "Evening can be cool, bring a light jacket",
    "Ask guide for restaurant recommendations"
  ]
}
```

## Step 3: Check Booking Availability

**Command**:
```bash
python3 .claude/skills/tripadvisor/scripts/tours.py booking 67890 2026-02-20 --party-size 4
```

**Expected Output**:
```json
{
  "tour_id": "67890",
  "date": "2026-02-20",
  "available": true,
  "party_size_requested": 4,
  "spots_remaining": 4,
  "pricing": {
    "price_per_person_usd": 95.0,
    "total_usd": 380.0,
    "currency": "USD"
  },
  "booking_deadline": "2026-02-19 18:30:00",
  "cancellation_deadline": "2026-02-19 18:30:00",
  "booking_url": "https://www.tripadvisor.com/Commerce/book?tour=67890&date=2026-02-20&party=4",
  "reservation_instructions": [
    "Click booking URL to reserve",
    "Full payment required at booking",
    "Confirmation email sent immediately",
    "Free cancellation until 24 hours before"
  ]
}
```

## Step 4: Get Recent Reviews

**Command**:
```bash
python3 .claude/skills/tripadvisor/scripts/tours.py reviews 67890 --max-reviews 5 --sort-by recent
```

**Expected Output**:
```json
{
  "tour_id": "67890",
  "tour_name": "Paris Evening Food Tour",
  "average_rating": 4.8,
  "total_reviews": 2340,
  "reviews": [
    {
      "author": "FoodieTravel2026",
      "rating": 5,
      "date": "2026-01-15",
      "text": "Best food tour ever! Guide was knowledgeable and the food stops were amazing. Wine pairing at the end was perfect. Highly recommend!",
      "helpful_votes": 45,
      "verified_purchase": true
    },
    {
      "author": "ParisLover99",
      "rating": 5,
      "date": "2026-01-10",
      "text": "Fantastic experience! Our guide Marie was so friendly and shared great stories about each place. The cheese shop was my favorite.",
      "helpful_votes": 38,
      "verified_purchase": true
    },
    {
      "author": "TravelCouple2026",
      "rating": 4,
      "date": "2026-01-05",
      "text": "Really enjoyed this tour. Food was delicious and portion sizes generous. Only complaint is it ran a bit long (4 hours instead of 3.5).",
      "helpful_votes": 22,
      "verified_purchase": true
    }
  ]
}
```

## Integration with Travel Planning

**Workflow**:
1. Search tours by location, category, and date
2. Filter by rating (4.5+ for tours recommended)
3. Get full details including pricing and availability
4. Check reviews for recent feedback
5. Verify cancellation policy before booking
6. Add to itinerary with meeting point and time

**Output for Agents**:
```json
{
  "tour": {
    "name": "Paris Evening Food Tour",
    "provider": "Local Food Tours Paris",
    "cost_per_person": 95.0,
    "duration_hours": 3.5,
    "start_time": "18:30",
    "rating": 4.8,
    "reviews": 2340,
    "available": true,
    "spots_remaining": 4,
    "meeting_point": "Place Saint-Michel, Latin Quarter",
    "booking_url": "https://www.tripadvisor.com/Commerce/book?tour=67890",
    "highlights": [
      "6 food stops with tastings",
      "Small group (max 12)",
      "Local expert guide",
      "Free cancellation 24h"
    ],
    "traveler_tips": [
      "Come hungry",
      "Wear walking shoes",
      "Bring light jacket"
    ],
    "data_source": "tripadvisor"
  }
}
```
