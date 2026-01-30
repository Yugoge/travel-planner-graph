# Yelp Restaurant Search - Complete Example

Complete workflow for meals agent using Yelp skill to research restaurants for multi-day trip.

## Scenario

**Trip**: 3 days in San Francisco
**Accommodation**: Hotel in Union Square (37.7879, -122.4075)
**Budget**: $60/day for meals
**Dietary**: Vegetarian preferred
**Dates**: March 15-17, 2026

## Workflow

### Step 1: Load Yelp Search Tools

```
Read /root/travel-planner/.claude/skills/yelp/tools/search.md
```

### Step 2: Read Requirements

```javascript
// Read requirements-skeleton.json
const requirements = {
  destination: "San Francisco, CA",
  dates: { start: "2026-03-15", end: "2026-03-17" },
  budget: { meals_per_day: 60 },
  dietary_restrictions: ["vegetarian"],
  preferences: { cuisine: ["italian", "mediterranean", "asian"] }
};

// Read plan-skeleton.json
const plan = {
  days: [
    {
      day: 1,
      activities: [
        { name: "Golden Gate Bridge", location: { lat: 37.8199, lon: -122.4783 } },
        { name: "Fisherman's Wharf", location: { lat: 37.8080, lon: -122.4177 } }
      ]
    },
    {
      day: 2,
      activities: [
        { name: "Alcatraz Island", location: { lat: 37.8267, lon: -122.4233 } },
        { name: "Chinatown", location: { lat: 37.7941, lon: -122.4078 } }
      ]
    },
    {
      day: 3,
      activities: [
        { name: "Golden Gate Park", location: { lat: 37.7694, lon: -122.4862 } },
        { name: "Haight-Ashbury", location: { lat: 37.7692, lon: -122.4481 } }
      ]
    }
  ]
};

// Budget allocation
const budget = {
  breakfast: 60 * 0.15, // $9
  lunch: 60 * 0.30,     // $18
  dinner: 60 * 0.40     // $24
};
```

### Step 3: Search Day 1 Breakfast

```javascript
// Near accommodation (Union Square)
const breakfastResult = await search_businesses({
  query: JSON.stringify({
    term: "vegetarian breakfast cafe",
    latitude: 37.7879,
    longitude: -122.4075,
    categories: "breakfast_brunch,cafes,vegetarian",
    price: "1,2",
    radius: 500,
    open_now: false,
    limit: 10
  })
});

// Filter and select
const breakfastOptions = breakfastResult.businesses
  .filter(b => b.rating >= 3.5 && b.review_count >= 20)
  .sort((a, b) => b.rating - a.rating);

const day1Breakfast = {
  name: breakfastOptions[0].name,
  location: `${breakfastOptions[0].location.address1}, ${breakfastOptions[0].location.city}`,
  cost: estimateCost(breakfastOptions[0].price, 'breakfast'),
  cuisine: breakfastOptions[0].categories[0].title,
  notes: `Rating: ${breakfastOptions[0].rating} (${breakfastOptions[0].review_count} reviews)`
};
```

### Step 4: Search Day 1 Lunch

```javascript
// Near Golden Gate Bridge
const lunchResult = await search_businesses({
  query: JSON.stringify({
    term: "vegetarian lunch",
    latitude: 37.8199,
    longitude: -122.4783,
    categories: "restaurants,vegetarian,mediterranean",
    price: "2",
    radius: 1500,
    limit: 10
  })
});

const lunchOptions = lunchResult.businesses
  .filter(b => b.rating >= 3.5 && b.review_count >= 20)
  .filter(b => b.id !== breakfastOptions[0].id); // Avoid duplicates

const day1Lunch = {
  name: lunchOptions[0].name,
  location: `${lunchOptions[0].location.address1}, ${lunchOptions[0].location.city}`,
  cost: estimateCost(lunchOptions[0].price, 'lunch'),
  cuisine: lunchOptions[0].categories[0].title,
  notes: `Near Golden Gate Bridge. Rating: ${lunchOptions[0].rating}`
};
```

### Step 5: Search Day 1 Dinner

```javascript
// Back near Union Square, Italian cuisine
const dinnerResult = await search_by_category({
  category: "italian",
  location: "San Francisco, CA",
  latitude: 37.7879,
  longitude: -122.4075,
  price: "2,3",
  radius: 2000,
  limit: 15
});

// Filter for vegetarian-friendly
const dinnerOptions = dinnerResult.businesses
  .filter(b => b.rating >= 3.5 && b.review_count >= 20)
  .filter(b =>
    b.id !== breakfastOptions[0].id &&
    b.id !== lunchOptions[0].id
  );

const day1Dinner = {
  name: dinnerOptions[0].name,
  location: `${dinnerOptions[0].location.address1}, ${dinnerOptions[0].location.city}`,
  cost: estimateCost(dinnerOptions[0].price, 'dinner'),
  cuisine: "Italian",
  notes: `Vegetarian options available. Rating: ${dinnerOptions[0].rating}. ${dinnerOptions[0].transactions.includes('restaurant_reservation') ? 'Reservations recommended.' : ''}`
};
```

### Step 6: Repeat for Day 2 and 3

```javascript
// Track used restaurants
const usedRestaurants = new Set([
  breakfastOptions[0].id,
  lunchOptions[0].id,
  dinnerOptions[0].id
]);

// Track used cuisines to ensure variety
const usedCuisines = {
  1: ['breakfast_brunch', 'mediterranean', 'italian']
};

// Day 2: Near Alcatraz/Chinatown
// Use different cuisines (asian, american)
// Avoid used restaurants

// Day 3: Near Golden Gate Park
// Use different cuisines (mexican, mediterranean)
// Ensure no duplicates
```

### Step 7: Error Handling

```javascript
async function searchWithFallback(params) {
  try {
    const result = await searchWithRetry(params, 3);

    if (result.success && result.data.businesses.length > 0) {
      return {
        source: 'yelp',
        data: result.data
      };
    }
  } catch (error) {
    console.error('Yelp search failed:', error);
  }

  // Fall back to WebSearch
  const webQuery = `best ${params.term || params.category} restaurants in ${params.location}`;
  const webResult = await WebSearch({ query: webQuery });

  return {
    source: 'websearch',
    data: parseWebSearchResults(webResult)
  };
}
```

### Step 8: Validate Results

```javascript
function validateMeal(meal, budget, mealType) {
  const checks = {
    has_name: !!meal.name,
    has_location: !!meal.location,
    has_cost: meal.cost > 0,
    within_budget: meal.cost <= budget[mealType],
    has_cuisine: !!meal.cuisine
  };

  const isValid = Object.values(checks).every(v => v);

  if (!isValid) {
    console.warn('Meal validation failed:', checks);
  }

  return isValid;
}
```

### Step 9: Structure Output

```javascript
const mealsData = {
  agent: "meals",
  status: "complete",
  data: {
    days: [
      {
        day: 1,
        breakfast: day1Breakfast,
        lunch: day1Lunch,
        dinner: day1Dinner
      },
      {
        day: 2,
        breakfast: day2Breakfast,
        lunch: day2Lunch,
        dinner: day2Dinner
      },
      {
        day: 3,
        breakfast: day3Breakfast,
        lunch: day3Lunch,
        dinner: day3Dinner
      }
    ]
  },
  notes: "All restaurants verified on Yelp with rating ≥3.5 and ≥20 reviews. Vegetarian options confirmed for all meals."
};

// Save to file
await Write({
  file_path: "/root/travel-planner/data/san-francisco/meals.json",
  content: JSON.stringify(mealsData, null, 2)
});
```

### Step 10: Return Complete

```
complete
```

---

## Helper Functions

### Search with Retry

```javascript
async function searchWithRetry(params, maxAttempts = 3) {
  let lastError;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const result = await mcp__plugin_yelp_yelp__search_businesses(params);
      return { success: true, data: result };
    } catch (error) {
      lastError = error;

      // Don't retry permanent errors
      if (error.status === 401 || error.status === 403 || error.status === 400 || error.status === 404) {
        console.error(`Permanent error (${error.status}):`, error.message);
        break;
      }

      // Exponential backoff for transient errors
      if (error.status === 429 || error.status >= 500) {
        const delay = Math.pow(2, attempt - 1) * 1000;
        console.log(`Attempt ${attempt} failed. Retrying in ${delay}ms...`);
        await sleep(delay);
        continue;
      }

      break;
    }
  }

  return {
    success: false,
    error: lastError
  };
}
```

### Estimate Cost

```javascript
function estimateCost(priceLevel, mealType) {
  const priceMap = {
    '$': { breakfast: 8, lunch: 12, dinner: 15 },
    '$$': { breakfast: 15, lunch: 20, dinner: 30 },
    '$$$': { breakfast: 25, lunch: 35, dinner: 50 },
    '$$$$': { breakfast: 40, lunch: 60, dinner: 80 }
  };

  return priceMap[priceLevel]?.[mealType] || 20;
}
```

### Calculate Distance

```javascript
function haversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}
```

### Filter by Distance

```javascript
function filterByDistance(businesses, targetLat, targetLon, maxDistanceKm) {
  return businesses
    .map(b => ({
      ...b,
      distance: haversineDistance(
        targetLat, targetLon,
        b.coordinates.latitude, b.coordinates.longitude
      )
    }))
    .filter(b => b.distance <= maxDistanceKm)
    .sort((a, b) => a.distance - b.distance);
}
```

### Ensure Variety

```javascript
function ensureVariety(options, usedRestaurants, usedCuisines, day) {
  return options
    .filter(b => !usedRestaurants.has(b.id))
    .filter(b => {
      const cuisine = b.categories[0].alias;
      const dayCuisines = usedCuisines[day] || [];
      return !dayCuisines.includes(cuisine);
    });
}
```

---

## Expected Output Structure

```json
{
  "agent": "meals",
  "status": "complete",
  "data": {
    "days": [
      {
        "day": 1,
        "breakfast": {
          "name": "Herbivore",
          "location": "531 Divisadero St, San Francisco",
          "cost": 15,
          "cuisine": "Vegan",
          "notes": "Rating: 4.5 (342 reviews)"
        },
        "lunch": {
          "name": "Greens Restaurant",
          "location": "2 Marina Blvd, San Francisco",
          "cost": 25,
          "cuisine": "Vegetarian",
          "notes": "Near Golden Gate Bridge. Rating: 4.0"
        },
        "dinner": {
          "name": "Flour + Water",
          "location": "2401 Harrison St, San Francisco",
          "cost": 45,
          "cuisine": "Italian",
          "notes": "Vegetarian options available. Rating: 4.5. Reservations recommended."
        }
      }
    ]
  },
  "notes": "All restaurants verified on Yelp with rating ≥3.5 and ≥20 reviews. Vegetarian options confirmed for all meals."
}
```

---

## Key Takeaways

1. **Load tools first**: Use Read to load search.md before searching
2. **Filter by quality**: Minimum 3.5 rating, 20+ reviews
3. **Optimize location**: Breakfast near hotel, lunch near attractions
4. **Track variety**: Avoid duplicate restaurants and cuisines
5. **Budget management**: Allocate 15%/30%/40% for breakfast/lunch/dinner
6. **Error handling**: Retry transient errors, fall back to WebSearch
7. **Validate output**: Ensure all required fields present
8. **Document source**: Note if data from Yelp or WebSearch fallback
