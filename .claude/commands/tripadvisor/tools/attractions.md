# TripAdvisor - Attraction Tools

Attraction discovery and detail tools for finding top-rated sights, landmarks, and activities.

## Available Tools

### 1. search_attractions

Search for attractions by location, keywords, and filters.

**MCP Tool**: `search_attractions`

**Parameters**:
- `location` (required): Location name (e.g., "Paris, France", "Tokyo", "New York City")
- `keywords` (optional): Search keywords (e.g., "museum", "park", "historical site")
- `category` (optional): Attraction category filter
  - `attractions`: All attractions (default)
  - `museums`: Museums and galleries
  - `outdoor`: Parks, gardens, nature
  - `sights`: Landmarks and monuments
  - `tours`: Guided tours
  - `activities`: Activities and experiences
- `min_rating` (optional): Minimum rating filter (1-5)
- `limit` (optional): Maximum results (default 20, max 50)
- `offset` (optional): Pagination offset (default 0)

**Returns**:
- Attraction name
- Location address
- Rating (1-5 scale)
- Number of reviews
- Price level ($ to $$$$)
- Category/type
- Brief description
- Photo URLs
- TripAdvisor URL
- Coordinates (lat/lng)

**Example**:
```javascript
// Search for museums in Paris
search_attractions({
  location: "Paris, France",
  category: "museums",
  min_rating: 4.0,
  limit: 10
})
```

**Response Structure**:
```json
{
  "results": [
    {
      "name": "Louvre Museum",
      "location": "75001 Paris, France",
      "rating": 4.5,
      "review_count": 85432,
      "price_level": "$$",
      "category": "Museum",
      "description": "World's largest art museum...",
      "hours": "09:00-18:00 (Mon, Wed-Sun)",
      "ticket_price": "€17 ($18)",
      "photos": ["url1", "url2"],
      "url": "https://tripadvisor.com/...",
      "coordinates": {
        "lat": 48.8606,
        "lng": 2.3376
      }
    }
  ],
  "total_count": 142
}
```

**Use Cases**:
- Daily attraction planning
- Interest-based discovery
- Top-rated sight selection
- Budget-appropriate filtering

---

### 2. get_attraction_details

Get comprehensive details for a specific attraction.

**MCP Tool**: `get_attraction_details`

**Parameters**:
- `attraction_id` (required): TripAdvisor attraction ID (from search results)
- `include_reviews` (optional): Include user reviews (default: true)
- `review_limit` (optional): Number of reviews to fetch (default: 10, max: 50)

**Returns**:
- Full attraction details
- Complete description
- All photos (up to 50)
- Opening hours (daily schedule)
- Ticket prices and options
- Facilities (parking, accessibility, WiFi)
- Contact information (phone, website, email)
- User reviews with ratings
- Tips from travelers
- Best times to visit
- Average visit duration
- Languages supported

**Example**:
```javascript
// Get details for specific museum
get_attraction_details({
  attraction_id: "d188455",
  include_reviews: true,
  review_limit: 20
})
```

**Response Structure**:
```json
{
  "id": "d188455",
  "name": "Louvre Museum",
  "full_description": "Detailed description...",
  "rating": 4.5,
  "review_count": 85432,
  "ranking": "#1 of 3,387 things to do in Paris",
  "price": {
    "adults": "€17 ($18)",
    "children": "Free (under 18)",
    "booking_required": true
  },
  "hours": {
    "monday": "Closed",
    "tuesday": "09:00-18:00",
    "wednesday": "09:00-21:45",
    "best_time": "Weekday mornings"
  },
  "duration": "2-3 hours",
  "facilities": ["Wheelchair accessible", "Audio guides", "Café", "Gift shop"],
  "contact": {
    "phone": "+33 1 40 20 50 50",
    "website": "https://louvre.fr",
    "email": "info@louvre.fr"
  },
  "photos": ["url1", "url2", "..."],
  "reviews": [
    {
      "author": "John D.",
      "rating": 5,
      "date": "2026-01-15",
      "text": "Absolutely stunning...",
      "helpful_votes": 42
    }
  ],
  "tips": [
    "Book tickets online to skip the line",
    "Visit on Wednesday evening for less crowds",
    "Allow 3-4 hours minimum"
  ],
  "coordinates": {
    "lat": 48.8606,
    "lng": 2.3376
  }
}
```

**Use Cases**:
- Detailed attraction planning
- Opening hours verification
- Price comparison
- Review analysis
- Visit duration estimation

---

### 3. get_reviews

Get filtered user reviews for an attraction.

**MCP Tool**: `get_reviews`

**Parameters**:
- `attraction_id` (required): TripAdvisor attraction ID
- `min_rating` (optional): Filter by minimum rating (1-5)
- `language` (optional): Review language (e.g., "en", "fr", "es")
- `sort_by` (optional): Sort order
  - `recent`: Most recent first (default)
  - `helpful`: Most helpful first
  - `rating_high`: Highest rating first
  - `rating_low`: Lowest rating first
- `limit` (optional): Number of reviews (default 20, max 100)
- `offset` (optional): Pagination offset

**Returns**:
- Review author
- Rating (1-5)
- Review date
- Review text
- Photos (if included)
- Helpful votes count
- Traveler type (family, couple, solo, business)
- Visit date

**Example**:
```javascript
// Get recent 4+ star reviews
get_reviews({
  attraction_id: "d188455",
  min_rating: 4,
  sort_by: "recent",
  limit: 30
})
```

**Use Cases**:
- Quality assessment
- Recent visitor feedback
- Issue identification
- Seasonal considerations

---

## Best Practices

### 1. Search Strategy

**Start broad, then narrow**:
```javascript
// Step 1: Broad search
const all_attractions = await search_attractions({
  location: "Rome, Italy",
  min_rating: 3.5
});

// Step 2: Filter by user interests
const cultural = all_attractions.results.filter(
  a => a.category.includes('Museum') || a.category.includes('Historical')
);

// Step 3: Get details for top candidates
const detailed = await Promise.all(
  cultural.slice(0, 5).map(a => get_attraction_details({ attraction_id: a.id }))
);
```

**Category-based search**:
```javascript
// Search by specific interests
const interests = {
  history: ['museums', 'sights'],
  nature: ['outdoor'],
  activities: ['activities', 'tours']
};

for (const category of interests[userPreference]) {
  const results = await search_attractions({
    location: location,
    category: category,
    min_rating: 4.0
  });
}
```

### 2. Rating and Review Analysis

**Filter by quality threshold**:
```javascript
function filterQualityAttractions(attractions, minRating = 4.0, minReviews = 100) {
  return attractions.filter(a => {
    return a.rating >= minRating && a.review_count >= minReviews;
  });
}
```

**Analyze review sentiment**:
```javascript
async function analyzeReviews(attractionId) {
  const reviews = await get_reviews({
    attraction_id: attractionId,
    sort_by: 'recent',
    limit: 50
  });

  // Check recent review trends
  const recentReviews = reviews.slice(0, 10);
  const recentAvg = recentReviews.reduce((sum, r) => sum + r.rating, 0) / 10;

  // Identify common themes
  const commonIssues = extractCommonThemes(reviews.map(r => r.text));

  return {
    recent_average: recentAvg,
    common_positives: commonIssues.positive,
    common_negatives: commonIssues.negative
  };
}
```

### 3. Price and Budget Filtering

**Convert price levels to budget**:
```javascript
function filterByBudget(attractions, budget) {
  const priceLevels = {
    '$': { min: 0, max: 20 },
    '$$': { min: 20, max: 50 },
    '$$$': { min: 50, max: 100 },
    '$$$$': { min: 100, max: Infinity }
  };

  return attractions.filter(a => {
    const range = priceLevels[a.price_level] || { min: 0, max: 0 };
    return range.max <= budget;
  });
}
```

### 4. Time and Schedule Optimization

**Check opening hours compatibility**:
```javascript
async function checkAvailability(attractionId, visitDate, visitTime) {
  const details = await get_attraction_details({ attraction_id: attractionId });

  const dayOfWeek = visitDate.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
  const hours = details.hours[dayOfWeek];

  if (hours === 'Closed') {
    return { available: false, reason: 'Closed on this day' };
  }

  // Parse opening hours and check compatibility
  const [open, close] = hours.split('-');
  const isWithinHours = visitTime >= open && visitTime <= close;

  return {
    available: isWithinHours,
    hours: hours,
    best_time: details.hours.best_time
  };
}
```

**Estimate visit duration**:
```javascript
function calculateTimeRequired(attraction) {
  // Parse duration string (e.g., "2-3 hours")
  const durationMatch = attraction.duration.match(/(\d+)-?(\d*)/);
  const minHours = parseInt(durationMatch[1]);
  const maxHours = parseInt(durationMatch[2] || minHours);

  // Add buffer for travel and queues
  const avgHours = (minHours + maxHours) / 2;
  const totalMinutes = avgHours * 60 + 30; // 30 min buffer

  return {
    duration_minutes: totalMinutes,
    recommended_time: `${avgHours} hours`,
    buffer_included: true
  };
}
```

### 5. Geographic Clustering

**Group attractions by proximity**:
```javascript
function clusterAttractionsByLocation(attractions, maxDistance = 2000) {
  // maxDistance in meters
  const clusters = [];

  for (const attraction of attractions) {
    let addedToCluster = false;

    for (const cluster of clusters) {
      const distance = calculateDistance(
        cluster[0].coordinates,
        attraction.coordinates
      );

      if (distance <= maxDistance) {
        cluster.push(attraction);
        addedToCluster = true;
        break;
      }
    }

    if (!addedToCluster) {
      clusters.push([attraction]);
    }
  }

  return clusters;
}

function calculateDistance(coord1, coord2) {
  // Haversine formula for distance in meters
  const R = 6371000; // Earth radius in meters
  const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
  const dLon = (coord2.lng - coord1.lng) * Math.PI / 180;

  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}
```

### 6. Error Handling

**Retry with exponential backoff**:
```javascript
async function searchWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_attractions(params);
    } catch (error) {
      if (error.status === 429 || error.status >= 500) {
        const delay = 1000 * Math.pow(2, i);
        await sleep(delay);
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Fallback to WebSearch**:
```javascript
async function searchAttractionsWithFallback(location, category) {
  try {
    return await search_attractions({ location, category });
  } catch (error) {
    console.warn('TripAdvisor unavailable, falling back to WebSearch');

    const query = `top rated ${category} attractions in ${location} 2026`;
    return await WebSearch({ query });
  }
}
```

---

## Integration with Attractions Agent

The attractions agent should:

1. **Load this file** when researching attractions for a day
2. **Search attractions** by location and user interests
3. **Filter by rating** (minimum 4.0 recommended)
4. **Get detailed information** for top candidates (5-10)
5. **Analyze reviews** for recent feedback
6. **Check hours and prices** for accuracy
7. **Group by proximity** to minimize travel
8. **Select 2-4 attractions** per day (avoid over-scheduling)
9. **Save structured data** to `attractions.json`
10. **Fall back to WebSearch** if MCP unavailable

### Example Workflow

```javascript
// Step 1: Identify location and interests
const day = planSkeleton.days[0];
const location = day.location;
const interests = requirements.interests; // e.g., ["museums", "history", "architecture"]

// Step 2: Search attractions by interests
const allAttractions = [];
for (const interest of interests) {
  const results = await search_attractions({
    location: location,
    keywords: interest,
    min_rating: 4.0,
    limit: 20
  });
  allAttractions.push(...results.results);
}

// Step 3: Filter and deduplicate
const uniqueAttractions = deduplicateById(allAttractions);
const qualityAttractions = filterQualityAttractions(uniqueAttractions, 4.0, 100);

// Step 4: Get details for top 10
const detailed = await Promise.all(
  qualityAttractions.slice(0, 10).map(a =>
    get_attraction_details({ attraction_id: a.id })
  )
);

// Step 5: Cluster by proximity
const clusters = clusterAttractionsByLocation(detailed);

// Step 6: Select best attractions (2-4 per day)
const selected = selectOptimalAttractions(clusters, day.available_hours);

// Step 7: Format for attractions.json
const formattedAttractions = selected.map(a => ({
  name: a.name,
  location: a.location,
  cost: parsePrice(a.price.adults),
  duration_minutes: calculateTimeRequired(a).duration_minutes,
  type: a.category,
  notes: `Rating: ${a.rating}/5 (${a.review_count} reviews). ${a.tips[0] || ''}`
}));

// Step 8: Save to attractions.json
```

---

## Tips for Effective Attraction Planning

1. **Quality over quantity**: 2-4 attractions per day is optimal
2. **Check recent reviews**: Quality can change over time
3. **Verify opening hours**: Especially for Mondays and holidays
4. **Book in advance**: If attraction requires timed entry
5. **Consider travel time**: Group nearby attractions
6. **Read traveler tips**: Often contain valuable insights
7. **Check accessibility**: Important for families and elderly
8. **Budget realistically**: Include skip-the-line options
9. **Allow buffer time**: Queues and travel take longer than expected
10. **Have backups**: Indoor alternatives for bad weather
