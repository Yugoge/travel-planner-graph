# Example: Attraction Search and Selection

Complete workflow for searching and selecting attractions using TripAdvisor skill.

## Scenario

User is planning Day 2 in Paris with interests in museums, history, and architecture. Budget is $30 per person per attraction.

## Step-by-Step Workflow

### Step 1: Load Attraction Tools

```markdown
Load attractions category: /root/travel-planner/.claude/commands/tripadvisor/tools/attractions.md
```

This loads the `search_attractions`, `get_attraction_details`, and `get_reviews` tools.

### Step 2: Search Attractions by Interests

```javascript
// Search for museums
const museums = await search_attractions({
  location: "Paris, France",
  category: "museums",
  min_rating: 4.0,
  limit: 20
});

// Search for historical sites
const historical = await search_attractions({
  location: "Paris, France",
  category: "sights",
  keywords: "historical",
  min_rating: 4.0,
  limit: 20
});

// Combine results
const allAttractions = [...museums.results, ...historical.results];

// Response structure for museums:
{
  "results": [
    {
      "id": "d188455",
      "name": "Louvre Museum",
      "location": "75001 Paris, France",
      "rating": 4.5,
      "review_count": 85432,
      "price_level": "$$",
      "category": "Museum",
      "description": "World's largest art museum featuring Mona Lisa...",
      "hours": "09:00-18:00 (Mon, Wed-Sun)",
      "ticket_price": "€17 ($18)",
      "coordinates": {
        "lat": 48.8606,
        "lng": 2.3376
      }
    },
    {
      "id": "d188459",
      "name": "Musée d'Orsay",
      "location": "75007 Paris, France",
      "rating": 4.6,
      "review_count": 52341,
      "price_level": "$",
      "category": "Museum",
      "description": "Impressionist and post-impressionist masterpieces...",
      "hours": "09:30-18:00 (Tue-Sun)",
      "ticket_price": "€16 ($17)",
      "coordinates": {
        "lat": 48.8600,
        "lng": 2.3266
      }
    }
  ],
  "total_count": 142
}
```

### Step 3: Filter by Budget and Quality

```javascript
function filterAttractions(attractions, maxPrice = 30, minRating = 4.0, minReviews = 100) {
  return attractions.filter(a => {
    // Parse price (e.g., "$18" -> 18)
    const price = parseFloat(a.ticket_price.match(/\$(\d+)/)?.[1] || 999);

    return (
      price <= maxPrice &&
      a.rating >= minRating &&
      a.review_count >= minReviews
    );
  });
}

const filtered = filterAttractions(allAttractions, 30, 4.0, 100);

// Result: 8 attractions that meet criteria
```

### Step 4: Get Detailed Information

```javascript
// Get details for top candidates
const detailed = await Promise.all(
  filtered.slice(0, 6).map(async (attraction) => {
    const details = await get_attraction_details({
      attraction_id: attraction.id,
      include_reviews: true,
      review_limit: 20
    });
    return details;
  })
);

// Example detailed response for Louvre:
{
  "id": "d188455",
  "name": "Louvre Museum",
  "full_description": "The Louvre is the world's largest art museum...",
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
    "thursday": "09:00-21:45",
    "friday": "09:00-18:00",
    "saturday": "09:00-18:00",
    "sunday": "09:00-18:00",
    "best_time": "Weekday mornings, especially Tuesday"
  },
  "duration": "2-3 hours minimum, 4-6 hours recommended",
  "facilities": [
    "Wheelchair accessible",
    "Audio guides (€5)",
    "Multiple cafés",
    "Gift shops",
    "Coat check",
    "Free WiFi"
  ],
  "contact": {
    "phone": "+33 1 40 20 50 50",
    "website": "https://www.louvre.fr/en",
    "email": "info@louvre.fr"
  },
  "reviews": [
    {
      "author": "John D.",
      "rating": 5,
      "date": "2026-01-15",
      "text": "Absolutely stunning collection. Book skip-the-line tickets!",
      "helpful_votes": 42,
      "visit_date": "2026-01-10"
    },
    {
      "author": "Maria S.",
      "rating": 5,
      "date": "2026-01-12",
      "text": "Incredible experience. Allow at least 4 hours.",
      "helpful_votes": 38,
      "visit_date": "2026-01-08"
    }
  ],
  "tips": [
    "Book tickets online to skip 1-2 hour queues",
    "Visit on Wednesday evening for less crowds",
    "Download the official app for navigation",
    "Focus on specific galleries to avoid overwhelm"
  ],
  "coordinates": {
    "lat": 48.8606,
    "lng": 2.3376
  }
}
```

### Step 5: Cluster by Geographic Proximity

```javascript
function clusterByProximity(attractions, maxDistance = 2000) {
  // Group attractions within 2km of each other
  const clusters = [];

  for (const attraction of attractions) {
    let added = false;

    for (const cluster of clusters) {
      const distance = calculateDistance(
        cluster[0].coordinates,
        attraction.coordinates
      );

      if (distance <= maxDistance) {
        cluster.push(attraction);
        added = true;
        break;
      }
    }

    if (!added) {
      clusters.push([attraction]);
    }
  }

  return clusters;
}

function calculateDistance(coord1, coord2) {
  // Haversine formula
  const R = 6371000; // meters
  const lat1 = coord1.lat * Math.PI / 180;
  const lat2 = coord2.lat * Math.PI / 180;
  const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
  const dLon = (coord2.lng - coord1.lng) * Math.PI / 180;

  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1) * Math.cos(lat2) *
            Math.sin(dLon/2) * Math.sin(dLon/2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

const clusters = clusterByProximity(detailed);

// Result:
// Cluster 1 (Left Bank): [Louvre, Musée d'Orsay, Sainte-Chapelle]
// Cluster 2 (Montmartre): [Sacré-Cœur]
// Cluster 3 (Marais): [Notre-Dame, Centre Pompidou]
```

### Step 6: Analyze Recent Reviews

```javascript
async function analyzeRecentReviews(attractionId) {
  const reviews = await get_reviews({
    attraction_id: attractionId,
    sort_by: "recent",
    limit: 30
  });

  // Calculate recent rating trend
  const recentAvg = reviews.slice(0, 10).reduce((sum, r) => sum + r.rating, 0) / 10;

  // Extract common themes
  const commonWords = {};
  reviews.forEach(r => {
    const words = r.text.toLowerCase().match(/\b\w{5,}\b/g) || [];
    words.forEach(w => {
      commonWords[w] = (commonWords[w] || 0) + 1;
    });
  });

  const topThemes = Object.entries(commonWords)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .map(([word]) => word);

  return {
    recent_rating: recentAvg,
    common_themes: topThemes
  };
}

// Analyze Louvre reviews
const louvreAnalysis = await analyzeRecentReviews("d188455");
// Result: { recent_rating: 4.6, common_themes: ["crowded", "amazing", "ticket", "early", "queue"] }
```

### Step 7: Select Optimal Attractions

```javascript
function selectAttractions(clusters, maxAttractions = 3, availableHours = 8) {
  const selected = [];
  let totalTime = 0;

  // Sort clusters by average rating
  const sortedClusters = clusters.sort((a, b) => {
    const avgRatingA = a.reduce((sum, attr) => sum + attr.rating, 0) / a.length;
    const avgRatingB = b.reduce((sum, attr) => sum + attr.rating, 0) / b.length;
    return avgRatingB - avgRatingA;
  });

  for (const cluster of sortedClusters) {
    // Sort attractions in cluster by rating
    const sorted = cluster.sort((a, b) => b.rating - a.rating);

    for (const attraction of sorted) {
      if (selected.length >= maxAttractions) break;

      // Parse duration (e.g., "2-3 hours" -> 180 minutes with buffer)
      const durationMatch = attraction.duration.match(/(\d+)-?(\d*)/);
      const minHours = parseInt(durationMatch[1]);
      const maxHours = parseInt(durationMatch[2] || minHours);
      const avgMinutes = ((minHours + maxHours) / 2) * 60 + 30; // 30 min buffer

      if (totalTime + avgMinutes <= availableHours * 60) {
        selected.push({
          ...attraction,
          estimated_duration: avgMinutes
        });
        totalTime += avgMinutes;
      }
    }
  }

  return selected;
}

const selectedAttractions = selectAttractions(clusters, 3, 8);

// Result: 3 attractions selected
// 1. Louvre Museum (240 min)
// 2. Musée d'Orsay (180 min)
// 3. Sainte-Chapelle (90 min)
// Total: 510 minutes (8.5 hours with buffer)
```

### Step 8: Format for attractions.json

```javascript
function formatForOutput(attractions) {
  return attractions.map(a => ({
    name: a.name,
    location: a.location,
    cost: parseFloat(a.price.adults.match(/\$(\d+)/)?.[1] || 0),
    duration_minutes: a.estimated_duration,
    type: a.category,
    notes: [
      `Rating: ${a.rating}/5 (${a.review_count.toLocaleString()} reviews)`,
      `Ranking: ${a.ranking}`,
      a.price.booking_required ? 'Book tickets online in advance' : '',
      a.tips[0] || ''
    ].filter(Boolean).join('. ')
  }));
}

const formatted = formatForOutput(selectedAttractions);

// Result:
[
  {
    "name": "Louvre Museum",
    "location": "75001 Paris, France",
    "cost": 18,
    "duration_minutes": 240,
    "type": "Museum",
    "notes": "Rating: 4.5/5 (85,432 reviews). Ranking: #1 of 3,387 things to do in Paris. Book tickets online in advance. Book tickets online to skip 1-2 hour queues"
  },
  {
    "name": "Musée d'Orsay",
    "location": "75007 Paris, France",
    "cost": 17,
    "duration_minutes": 180,
    "type": "Museum",
    "notes": "Rating: 4.6/5 (52,341 reviews). Ranking: #3 of 3,387 things to do in Paris. Book tickets online in advance. Arrive at opening time for smaller crowds"
  },
  {
    "name": "Sainte-Chapelle",
    "location": "75001 Paris, France",
    "cost": 12,
    "duration_minutes": 90,
    "type": "Historical Site",
    "notes": "Rating: 4.7/5 (23,156 reviews). Ranking: #5 of 3,387 things to do in Paris. Book tickets online in advance. Visit on sunny day for best stained glass views"
  }
]
```

### Step 9: Save to attractions.json

```javascript
const attractionsData = {
  agent: "attractions",
  status: "complete",
  data: {
    days: [
      {
        day: 2,
        date: "2026-03-16",
        location: "Paris, France",
        attractions: formatted
      }
    ]
  },
  notes: "All attractions require advance booking. Total cost: $47/person. Total time: ~8.5 hours including travel and queues.",
  data_source: "tripadvisor"
};

// Save to: data/{destination-slug}/attractions.json
```

---

## Error Handling Example

### Scenario: MCP Server Unavailable

```javascript
async function searchAttractionsWithFallback(location, interests) {
  try {
    // Try TripAdvisor first
    const results = [];

    for (const interest of interests) {
      const attractions = await search_attractions({
        location: location,
        keywords: interest,
        min_rating: 4.0,
        limit: 20
      });
      results.push(...attractions.results);
    }

    return {
      source: 'tripadvisor',
      data: results
    };
  } catch (error) {
    console.warn('TripAdvisor unavailable, falling back to WebSearch');

    // Fallback to WebSearch
    const searchQuery = `top rated ${interests.join(' ')} attractions in ${location} 2026`;
    const searchResults = await WebSearch({ query: searchQuery });

    return {
      source: 'web_search',
      data: parseWebSearchResults(searchResults),
      warning: 'Data from web search, review counts and ratings may be less accurate'
    };
  }
}
```

---

## Retry Logic Example

### Scenario: Transient Network Error

```javascript
async function getAttractionDetailsWithRetry(attractionId, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await get_attraction_details({
        attraction_id: attractionId,
        include_reviews: true
      });
    } catch (error) {
      // Retry on transient errors
      if (error.status === 429 || error.status >= 500) {
        const delay = 1000 * Math.pow(2, i);
        console.warn(`Retry ${i + 1}/${maxRetries} after ${delay}ms`);
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

## Complete Attractions Agent Workflow

```javascript
async function attractionsAgentWorkflow(destinationSlug, dayNumber) {
  // Step 1: Read requirements and plan
  const requirements = readJSON(`data/${destinationSlug}/requirements-skeleton.json`);
  const planSkeleton = readJSON(`data/${destinationSlug}/plan-skeleton.json`);

  const day = planSkeleton.days.find(d => d.day === dayNumber);
  const location = day.location;
  const interests = requirements.interests || ["museums", "sights", "history"];
  const budget = requirements.budget?.attractions || 30;

  // Step 2: Search attractions by interests
  const allAttractions = [];

  for (const interest of interests) {
    try {
      const results = await searchAttractionsWithFallback(location, [interest]);
      allAttractions.push(...results.data);
    } catch (error) {
      console.error(`Failed to search for ${interest}:`, error);
    }
  }

  // Step 3: Deduplicate and filter
  const unique = deduplicateById(allAttractions);
  const filtered = filterAttractions(unique, budget, 4.0, 100);

  if (filtered.length === 0) {
    return {
      agent: "attractions",
      status: "complete",
      data: { days: [{ day: dayNumber, attractions: [] }] },
      notes: "No attractions found matching criteria. Manual research required."
    };
  }

  // Step 4: Get details for top candidates
  const detailed = await Promise.all(
    filtered.slice(0, 8).map(a => getAttractionDetailsWithRetry(a.id))
  );

  // Step 5: Cluster by proximity
  const clusters = clusterByProximity(detailed);

  // Step 6: Select optimal attractions
  const availableHours = day.available_hours || 8;
  const selected = selectAttractions(clusters, 3, availableHours);

  // Step 7: Format and save
  const formatted = formatForOutput(selected);

  const attractionsData = {
    agent: "attractions",
    status: "complete",
    data: {
      days: [{
        day: dayNumber,
        date: day.date,
        location: location,
        attractions: formatted
      }]
    },
    notes: buildNotes(selected),
    data_source: "tripadvisor"
  };

  writeJSON(`data/${destinationSlug}/attractions.json`, attractionsData);

  return "complete";
}

function buildNotes(attractions) {
  const totalCost = attractions.reduce((sum, a) => sum + a.cost, 0);
  const totalTime = attractions.reduce((sum, a) => sum + a.duration_minutes, 0);

  const notes = [
    attractions.some(a => a.price.booking_required) ?
      'Advance booking required for some attractions' : '',
    `Total cost: $${totalCost}/person`,
    `Estimated time: ${Math.round(totalTime / 60)} hours (including travel)`
  ].filter(Boolean);

  return notes.join('. ');
}
```

---

## Tips for Attractions Agent

1. **Use TripAdvisor first**: More reliable ratings and reviews than web search
2. **Implement retry logic**: Handle transient errors gracefully
3. **Cluster geographically**: Minimize travel time between attractions
4. **Check recent reviews**: Quality can change over time
5. **Respect budget constraints**: Filter by price before detailed lookup
6. **Allow buffer time**: Queues and travel take longer than expected
7. **Verify opening hours**: Especially Mondays and holidays
8. **Limit attractions**: 2-4 per day is optimal (avoid over-scheduling)
9. **Include traveler tips**: Valuable practical advice
10. **Have fallback**: WebSearch if TripAdvisor unavailable
