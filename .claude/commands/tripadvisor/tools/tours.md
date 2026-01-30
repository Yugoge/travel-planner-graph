# TripAdvisor - Tour and Activity Tools

Tour discovery and booking tools for finding guided tours, experiences, and entertainment activities.

## Available Tools

### 1. search_tours

Search for tours, activities, and experiences by location and type.

**MCP Tool**: `search_tours`

**Parameters**:
- `location` (required): Location name (e.g., "Paris, France", "Tokyo")
- `category` (optional): Tour category filter
  - `all`: All tours and activities (default)
  - `cultural`: Cultural tours and experiences
  - `outdoor`: Outdoor adventures and nature tours
  - `food`: Food tours and culinary experiences
  - `nightlife`: Evening entertainment and nightlife tours
  - `shows`: Theater, concerts, and performances
  - `private`: Private and custom tours
- `duration` (optional): Duration filter
  - `short`: Under 3 hours
  - `half_day`: 3-6 hours
  - `full_day`: 6+ hours
  - `multi_day`: Multiple days
- `min_rating` (optional): Minimum rating (1-5)
- `price_range` (optional): Price range filter
  - `budget`: Under $50
  - `moderate`: $50-$150
  - `luxury`: $150+
- `limit` (optional): Maximum results (default 20, max 50)

**Returns**:
- Tour name
- Provider/operator
- Rating (1-5 scale)
- Number of reviews
- Price per person
- Duration
- Category/type
- Description
- Inclusions (tickets, meals, transport)
- Meeting point
- Cancellation policy
- Languages offered
- Photo URLs
- Booking URL

**Example**:
```javascript
// Search for evening shows in Paris
search_tours({
  location: "Paris, France",
  category: "shows",
  duration: "short",
  min_rating: 4.0
})
```

**Response Structure**:
```json
{
  "results": [
    {
      "id": "t123456",
      "name": "Moulin Rouge Cabaret Show with Champagne",
      "provider": "Moulin Rouge Paris",
      "rating": 4.7,
      "review_count": 12453,
      "price": 120,
      "currency": "USD",
      "duration": "2 hours",
      "category": "Show/Performance",
      "description": "Experience the legendary Moulin Rouge cabaret...",
      "inclusions": [
        "Reserved seating",
        "Half bottle of champagne",
        "Souvenir program"
      ],
      "exclusions": ["Dinner", "Hotel pickup"],
      "meeting_point": "82 Boulevard de Clichy, 75018 Paris",
      "times": ["19:00", "21:00"],
      "languages": ["English", "French", "Spanish"],
      "cancellation": "Free cancellation up to 24 hours",
      "photos": ["url1", "url2"],
      "booking_url": "https://tripadvisor.com/..."
    }
  ],
  "total_count": 87
}
```

**Use Cases**:
- Evening entertainment planning
- Activity recommendations
- Group experience booking
- Special occasion planning

---

### 2. get_tour_details

Get comprehensive details for a specific tour or activity.

**MCP Tool**: `get_tour_details`

**Parameters**:
- `tour_id` (required): TripAdvisor tour ID (from search results)
- `include_reviews` (optional): Include user reviews (default: true)
- `check_availability` (optional): Check real-time availability (default: false)
- `date` (optional): Specific date for availability check (YYYY-MM-DD)

**Returns**:
- Complete tour description
- Detailed itinerary
- Full pricing breakdown
- All departure times
- Availability calendar
- Maximum group size
- Age restrictions
- Physical requirements
- What to bring/wear
- Accessibility information
- COVID-19 safety measures
- User reviews with ratings
- Operator contact info
- Booking terms and conditions

**Example**:
```javascript
// Get details with availability check
get_tour_details({
  tour_id: "t123456",
  include_reviews: true,
  check_availability: true,
  date: "2026-03-15"
})
```

**Response Structure**:
```json
{
  "id": "t123456",
  "name": "Moulin Rouge Cabaret Show with Champagne",
  "full_description": "Detailed description...",
  "itinerary": [
    {
      "time": "19:00",
      "activity": "Arrival and seating",
      "duration": "30 minutes"
    },
    {
      "time": "19:30",
      "activity": "Show begins",
      "duration": "90 minutes"
    }
  ],
  "pricing": {
    "base_price": 120,
    "children_price": null,
    "group_discount": "10% for 6+ people",
    "peak_surcharge": 20
  },
  "schedule": {
    "available_dates": ["2026-03-15", "2026-03-16", "..."],
    "times": {
      "2026-03-15": {
        "19:00": { "available": true, "spots": 12 },
        "21:00": { "available": true, "spots": 8 }
      }
    },
    "blackout_dates": ["2025-12-25", "2026-01-01"]
  },
  "requirements": {
    "min_age": 6,
    "max_age": null,
    "physical_level": "Easy",
    "mobility": "Wheelchair accessible",
    "dress_code": "Smart casual"
  },
  "what_to_bring": [
    "Printed or mobile voucher",
    "Valid ID",
    "Camera (no flash during show)"
  ],
  "reviews": [
    {
      "author": "Sarah M.",
      "rating": 5,
      "date": "2026-01-20",
      "text": "Absolutely spectacular show...",
      "helpful_votes": 28,
      "visit_date": "2026-01-15"
    }
  ],
  "operator": {
    "name": "Moulin Rouge Paris",
    "phone": "+33 1 53 09 82 82",
    "email": "reservations@moulinrouge.fr",
    "website": "https://moulinrouge.fr"
  },
  "booking_terms": {
    "cancellation": "Free cancellation up to 24 hours before start time",
    "refund_policy": "Full refund if cancelled 24h+ in advance",
    "modification": "Date changes allowed up to 48h before"
  }
}
```

**Use Cases**:
- Detailed activity planning
- Availability verification
- Price comparison
- Booking requirement check

---

### 3. search_shows

Specialized search for theater, concerts, and live performances.

**MCP Tool**: `search_shows`

**Parameters**:
- `location` (required): Location name
- `show_type` (optional): Type of show
  - `theater`: Plays and theatrical performances
  - `concert`: Music concerts
  - `opera`: Opera and ballet
  - `cabaret`: Cabaret and variety shows
  - `comedy`: Stand-up comedy
- `date_range` (optional): Date range filter
  - `start_date`: YYYY-MM-DD
  - `end_date`: YYYY-MM-DD
- `time_of_day` (optional): Preferred time
  - `evening`: After 6pm
  - `matinee`: Afternoon shows
  - `late_night`: After 10pm
- `min_rating` (optional): Minimum rating (1-5)
- `limit` (optional): Maximum results (default 20)

**Returns**:
- Show name
- Venue
- Rating and reviews
- Price range
- Show times
- Duration
- Language/subtitles
- Seating options
- Dress code
- Booking availability

**Example**:
```javascript
// Search for evening theater shows
search_shows({
  location: "London, UK",
  show_type: "theater",
  date_range: {
    start_date: "2026-03-15",
    end_date: "2026-03-22"
  },
  time_of_day: "evening",
  min_rating: 4.5
})
```

**Use Cases**:
- Evening entertainment planning
- Theater and concert booking
- Cultural activity discovery
- Special event planning

---

## Best Practices

### 1. Tour Search Strategy

**Filter by user preferences**:
```javascript
async function findToursForEntertainment(location, preferences, travelDates) {
  const categories = [];

  if (preferences.theater) categories.push('shows');
  if (preferences.nightlife) categories.push('nightlife');
  if (preferences.cultural) categories.push('cultural');

  const allTours = [];

  for (const category of categories) {
    const results = await search_tours({
      location: location,
      category: category,
      min_rating: 4.0,
      limit: 20
    });
    allTours.push(...results.results);
  }

  return filterByDateAvailability(allTours, travelDates);
}
```

**Price-based filtering**:
```javascript
function filterByBudget(tours, budget) {
  return tours.filter(tour => {
    return tour.price <= budget;
  }).sort((a, b) => b.rating - a.rating);
}
```

### 2. Availability Management

**Check availability for specific dates**:
```javascript
async function checkTourAvailability(tourId, dates) {
  const availabilityResults = [];

  for (const date of dates) {
    const details = await get_tour_details({
      tour_id: tourId,
      check_availability: true,
      date: date
    });

    const daySchedule = details.schedule.times[date];
    if (daySchedule) {
      availabilityResults.push({
        date: date,
        times: Object.entries(daySchedule).map(([time, info]) => ({
          time: time,
          available: info.available,
          spots: info.spots
        }))
      });
    }
  }

  return availabilityResults;
}
```

**Find best time slot**:
```javascript
function findBestTimeSlot(availability, preferredTime = 'evening') {
  const timePreferences = {
    'evening': time => parseInt(time.split(':')[0]) >= 18,
    'afternoon': time => {
      const hour = parseInt(time.split(':')[0]);
      return hour >= 13 && hour < 18;
    },
    'morning': time => parseInt(time.split(':')[0]) < 13
  };

  const filter = timePreferences[preferredTime] || (() => true);

  for (const slot of availability) {
    const matchingTimes = slot.times.filter(t =>
      t.available && filter(t.time)
    );

    if (matchingTimes.length > 0) {
      return {
        date: slot.date,
        time: matchingTimes[0].time,
        spots_available: matchingTimes[0].spots
      };
    }
  }

  return null;
}
```

### 3. Entertainment Selection

**Balance variety and quality**:
```javascript
function selectEntertainment(tours, days) {
  const selected = [];
  const usedCategories = new Set();

  // Prioritize high-rated options
  const sorted = tours.sort((a, b) => {
    if (Math.abs(a.rating - b.rating) > 0.5) {
      return b.rating - a.rating;
    }
    return b.review_count - a.review_count;
  });

  for (const tour of sorted) {
    // Avoid repetitive entertainment types
    if (usedCategories.has(tour.category) && usedCategories.size < days) {
      continue;
    }

    // Allow rest days (not every day needs entertainment)
    if (selected.length >= Math.ceil(days * 0.7)) {
      break;
    }

    selected.push(tour);
    usedCategories.add(tour.category);
  }

  return selected;
}
```

### 4. Review Analysis for Shows

**Identify show quality trends**:
```javascript
async function analyzeShowQuality(tourId) {
  const details = await get_tour_details({
    tour_id: tourId,
    include_reviews: true
  });

  const reviews = details.reviews;

  // Calculate recent trend
  const recentReviews = reviews.filter(r => {
    const reviewDate = new Date(r.date);
    const monthsAgo = (Date.now() - reviewDate) / (1000 * 60 * 60 * 24 * 30);
    return monthsAgo <= 3;
  });

  const recentAvg = recentReviews.reduce((sum, r) => sum + r.rating, 0) / recentReviews.length;

  // Extract common themes
  const positives = [];
  const negatives = [];

  reviews.forEach(r => {
    if (r.rating >= 4) {
      positives.push(extractKeywords(r.text));
    } else {
      negatives.push(extractKeywords(r.text));
    }
  });

  return {
    overall_rating: details.rating,
    recent_rating: recentAvg,
    trend: recentAvg >= details.rating ? 'improving' : 'declining',
    common_positives: getMostCommon(positives.flat()),
    common_negatives: getMostCommon(negatives.flat()),
    recommendation: recentAvg >= 4.0 ? 'recommended' : 'consider_alternatives'
  };
}
```

### 5. Time and Schedule Integration

**Check conflict with other activities**:
```javascript
function checkScheduleConflict(tour, existingActivities) {
  const tourStart = parseTime(tour.times[0]);
  const tourEnd = addHours(tourStart, parseDuration(tour.duration));

  for (const activity of existingActivities) {
    const activityStart = parseTime(activity.time);
    const activityEnd = addHours(activityStart, activity.duration_hours);

    // Check for overlap
    if (tourStart < activityEnd && tourEnd > activityStart) {
      return {
        conflict: true,
        conflicting_activity: activity.name
      };
    }
  }

  // Check if enough time for dinner before show
  const dinnerBuffer = 2; // hours
  const hasDinnerTime = existingActivities.some(a => {
    if (a.type === 'meal') {
      const mealEnd = addHours(parseTime(a.time), a.duration_hours);
      const hoursUntilShow = (tourStart - mealEnd) / (1000 * 60 * 60);
      return hoursUntilShow >= 0 && hoursUntilShow <= dinnerBuffer;
    }
    return false;
  });

  return {
    conflict: false,
    dinner_compatible: hasDinnerTime
  };
}
```

### 6. Error Handling

**Handle sold-out shows**:
```javascript
async function findAlternativeShows(originalTour, location, date) {
  // Search for similar shows
  const alternatives = await search_tours({
    location: location,
    category: originalTour.category,
    min_rating: originalTour.rating - 0.5,
    limit: 10
  });

  // Check availability
  const availableAlternatives = [];

  for (const alt of alternatives.results) {
    if (alt.id === originalTour.id) continue;

    const details = await get_tour_details({
      tour_id: alt.id,
      check_availability: true,
      date: date
    });

    const hasAvailability = details.schedule.times[date] &&
      Object.values(details.schedule.times[date]).some(slot => slot.available);

    if (hasAvailability) {
      availableAlternatives.push({
        ...alt,
        available_times: Object.keys(details.schedule.times[date])
          .filter(time => details.schedule.times[date][time].available)
      });
    }
  }

  return availableAlternatives;
}
```

**Fallback to WebSearch**:
```javascript
async function searchToursWithFallback(location, category) {
  try {
    return await search_tours({ location, category });
  } catch (error) {
    console.warn('TripAdvisor unavailable, falling back to WebSearch');

    const queries = {
      'shows': `theater shows concerts ${location} 2026 tickets`,
      'nightlife': `nightlife entertainment bars clubs ${location}`,
      'cultural': `cultural tours experiences ${location}`
    };

    const query = queries[category] || `tours activities ${location}`;
    return await WebSearch({ query });
  }
}
```

---

## Integration with Entertainment Agent

The entertainment agent should:

1. **Load this file** when researching evening entertainment
2. **Search tours** by entertainment category (shows, nightlife, cultural)
3. **Filter by date availability** for travel dates
4. **Get detailed information** including show times and pricing
5. **Analyze reviews** for quality assurance
6. **Check schedule conflicts** with dinner and other activities
7. **Select 1-2 options** per 2-3 days (not every night needs entertainment)
8. **Save structured data** to `entertainment.json`
9. **Fall back to WebSearch** if MCP unavailable
10. **Provide alternatives** for sold-out shows

### Example Workflow

```javascript
// Step 1: Identify location and entertainment preferences
const day = planSkeleton.days[0];
const location = day.location;
const preferences = requirements.entertainment; // { theater: true, nightlife: false }

// Step 2: Search entertainment options
const shows = preferences.theater ?
  await search_shows({
    location: location,
    show_type: 'theater',
    date_range: {
      start_date: day.date,
      end_date: day.date
    },
    time_of_day: 'evening',
    min_rating: 4.5
  }) : [];

const nightlife = preferences.nightlife ?
  await search_tours({
    location: location,
    category: 'nightlife',
    min_rating: 4.0
  }) : [];

const allOptions = [...shows.results, ...nightlife.results];

// Step 3: Check availability
const availableOptions = [];
for (const option of allOptions) {
  const availability = await checkTourAvailability(option.id, [day.date]);
  if (availability.length > 0 && availability[0].times.some(t => t.available)) {
    availableOptions.push({
      ...option,
      availability: availability[0]
    });
  }
}

// Step 4: Analyze quality
const analyzed = await Promise.all(
  availableOptions.map(async opt => ({
    ...opt,
    quality: await analyzeShowQuality(opt.id)
  }))
);

// Step 5: Select best option
const recommended = analyzed
  .filter(opt => opt.quality.recommendation === 'recommended')
  .sort((a, b) => b.rating - a.rating)[0];

// Step 6: Find best time slot
const bestTime = findBestTimeSlot(recommended.availability, 'evening');

// Step 7: Format for entertainment.json
const formatted = {
  name: recommended.name,
  location: recommended.meeting_point || recommended.provider,
  cost: recommended.price,
  time: bestTime.time,
  type: recommended.category,
  notes: `Rating: ${recommended.rating}/5. ${recommended.cancellation}. Book in advance.`
};

// Step 8: Save to entertainment.json
```

---

## Tips for Entertainment Planning

1. **Book in advance**: Popular shows sell out quickly
2. **Check dress codes**: Some venues have requirements
3. **Verify language options**: Ensure understanding
4. **Consider logistics**: Late shows mean late return to hotel
5. **Allow rest days**: Not every night needs entertainment
6. **Read cancellation policy**: Weather or illness may require changes
7. **Check age restrictions**: Important for family travel
8. **Compare prices**: Box office vs. tour packages
9. **Time for dinner**: Ensure meal before/after show
10. **Have alternatives**: Backup plans for sold-out shows
