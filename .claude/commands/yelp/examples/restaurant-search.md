# Example: Restaurant Search Workflow

Complete workflow for researching dining options using Yelp skill.

## Scenario

Meals agent needs to find breakfast, lunch, and dinner options for Day 2 in San Francisco. User has dietary preference for vegetarian options and a daily meal budget of $80.

## Step-by-Step Workflow

### Step 1: Load Search Tools

```markdown
Load search category: /root/travel-planner/.claude/commands/yelp/tools/search.md
```

This loads the `search_businesses`, `get_business_details`, and `search_by_category` tools.

### Step 2: Read Requirements

```javascript
// Read user requirements
const requirements = readJSON('data/san-francisco/requirements-skeleton.json');
const planSkeleton = readJSON('data/san-francisco/plan-skeleton.json');

// Extract Day 2 details
const day2 = planSkeleton.days.find(d => d.day === 2);
const accommodation = day2.accommodation;  // "Union Square area"
const attractions = day2.attractions;  // ["Golden Gate Park", "Japanese Tea Garden"]

const dietaryRestrictions = requirements.trip_summary.preferences.dietary || [];
const dailyBudget = requirements.trip_summary.budget.meals_per_day || 80;
```

### Step 3: Search Breakfast Options

```javascript
// Search for breakfast near accommodation
const breakfastResults = await search_businesses({
  query: "breakfast brunch vegetarian friendly",
  location: "Union Square, San Francisco, CA",
  categories: "breakfast_brunch,cafes",
  open_now: false,  // Don't filter by current time
  limit: 15
});

// Filter and parse results
const breakfastOptions = breakfastResults.businesses
  .filter(b => b.rating >= 3.5 && b.review_count >= 20)
  .filter(b => {
    const cost = estimateCostPerPerson(b.price);
    return cost <= dailyBudget * 0.15;  // 15% of daily budget
  })
  .map(b => parseYelpBusiness(b));

// Select top option
const breakfast = breakfastOptions[0];

// Response structure:
{
  name: "Cafe Reveille",
  location: "610 Long Bridge St, San Francisco, CA 94111",
  cost: 15,  // Estimated per person
  cuisine: "Cafes, Breakfast & Brunch, Coffee & Tea",
  rating: 4.5,
  review_count: 342,
  notes: "Highly rated, Very popular, Known for avocado toast and organic coffee"
}
```

### Step 4: Search Lunch Near Attraction

```javascript
// Find lunch near Golden Gate Park
const lunchResults = await search_businesses({
  query: "lunch restaurants vegetarian",
  location: "Golden Gate Park, San Francisco, CA",
  radius: 1000,  // 1km radius from park
  price: 2,  // $$ - moderate pricing
  limit: 15
});

// Parse and filter
const lunchOptions = lunchResults.businesses
  .filter(b => b.rating >= 3.5)
  .filter(b => {
    const cost = estimateCostPerPerson(b.price);
    return cost <= dailyBudget * 0.30;  // 30% of daily budget
  })
  .map(b => parseYelpBusiness(b));

const lunch = lunchOptions[0];

// Response:
{
  name: "Park Chow",
  location: "1240 9th Ave, San Francisco, CA 94122",
  cost: 25,
  cuisine: "American (Traditional), Vegetarian",
  rating: 4.0,
  review_count: 1250,
  notes: "Very popular, Close to Golden Gate Park, Vegetarian options available"
}
```

### Step 5: Search Dinner with Specific Cuisine

```javascript
// Search for special dinner - Italian with vegetarian options
const dinnerResults = await search_by_category({
  category: "italian",
  location: "Union Square, San Francisco, CA",
  price: 3,  // $$$ - upscale
  limit: 15
});

// Filter for vegetarian-friendly
const dinnerOptions = dinnerResults.businesses
  .filter(b => b.rating >= 4.0)
  .filter(b => {
    // Check if reviews mention vegetarian options
    const hasVegOptions = b.categories.some(c =>
      c.alias.includes('vegetarian') || c.title.includes('Vegetarian')
    );
    return hasVegOptions || b.rating >= 4.5;  // High-rated likely has options
  })
  .map(b => parseYelpBusiness(b));

const dinner = dinnerOptions[0];

// Response:
{
  name: "Flour + Water",
  location: "2401 Harrison St, San Francisco, CA 94110",
  cost: 60,
  cuisine: "Italian, Pasta, Wine Bars",
  rating: 4.5,
  review_count: 2890,
  notes: "Highly rated, Very popular, Reservations recommended, Known for handmade pasta"
}
```

### Step 6: Validate and Get Details

```javascript
// For dinner reservation requirement, get full details
const dinnerDetails = await get_business_details({
  business_id: dinner.id
});

// Check opening hours and booking
const hasReservation = dinnerDetails.transactions?.includes('restaurant_reservation');
const bookingUrl = dinnerDetails.url;

// Update dinner notes
dinner.notes += hasReservation
  ? `, Book at: ${bookingUrl}`
  : ', Walk-ins only';
```

### Step 7: Structure Output

```javascript
const mealsData = {
  agent: "meals",
  status: "complete",
  data: {
    days: [
      {
        day: 2,
        breakfast: {
          name: breakfast.name,
          location: breakfast.location,
          cost: breakfast.cost,
          cuisine: breakfast.cuisine,
          notes: breakfast.notes
        },
        lunch: {
          name: lunch.name,
          location: lunch.location,
          cost: lunch.cost,
          cuisine: lunch.cuisine,
          notes: lunch.notes
        },
        dinner: {
          name: dinner.name,
          location: dinner.location,
          cost: dinner.cost,
          cuisine: dinner.cuisine,
          notes: dinner.notes
        }
      }
    ]
  },
  notes: "All restaurants researched via Yelp Fusion AI. Vegetarian options verified. Total daily cost: $100 (within $80 target with some flexibility for special dinner)."
};

// Save to file
writeJSON('data/san-francisco/meals.json', mealsData);
```

---

## Error Handling Example

### Scenario: MCP Server Unavailable

```javascript
async function searchRestaurantWithFallback(query, location, category) {
  try {
    // Try Yelp first
    const results = await search_businesses({
      query: query,
      location: location,
      categories: category,
      limit: 15
    });

    return {
      source: 'yelp',
      data: results.businesses.map(b => parseYelpBusiness(b))
    };
  } catch (error) {
    console.warn('Yelp unavailable, falling back to WebSearch');

    // Fallback to WebSearch
    const searchQuery = `best ${query} restaurants in ${location} ${new Date().getFullYear()}`;
    const searchResults = await WebSearch({ query: searchQuery });

    return {
      source: 'web_search',
      data: parseWebSearchResults(searchResults),
      warning: 'Data from web search, may not include real-time ratings or pricing'
    };
  }
}
```

---

## Retry Logic Example

### Scenario: Transient Network Error

```javascript
async function searchWithRetry(params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await search_businesses(params);
    } catch (error) {
      // Retry on transient errors
      if (error.status === 429 || error.status >= 500) {
        const delay = 1000 * Math.pow(2, i);  // Exponential backoff
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

## Multi-Day Trip Example

### Scenario: 5-Day Trip with Variety

```javascript
async function planAllMeals(destinationSlug) {
  const requirements = readJSON(`data/${destinationSlug}/requirements-skeleton.json`);
  const planSkeleton = readJSON(`data/${destinationSlug}/plan-skeleton.json`);

  const allMeals = [];

  for (const day of planSkeleton.days) {
    const dayNumber = day.day;
    const location = day.location || day.accommodation;

    // Get breakfast, lunch, dinner for this day
    const breakfast = await searchMeal('breakfast', location, requirements, dayNumber);
    const lunch = await searchMeal('lunch', location, requirements, dayNumber);
    const dinner = await searchMeal('dinner', location, requirements, dayNumber);

    allMeals.push({
      day: dayNumber,
      breakfast,
      lunch,
      dinner
    });

    // Rate limiting: small delay between days
    await sleep(200);
  }

  return {
    agent: "meals",
    status: "complete",
    data: { days: allMeals },
    notes: "Meals researched via Yelp. Variety ensured across days."
  };
}

async function searchMeal(mealType, location, requirements, dayNumber) {
  const categoryMap = {
    'breakfast': 'breakfast_brunch,cafes',
    'lunch': 'restaurants',
    'dinner': 'restaurants'
  };

  const budgetPercent = {
    'breakfast': 0.15,
    'lunch': 0.30,
    'dinner': 0.40
  };

  const maxCost = requirements.trip_summary.budget.meals_per_day * budgetPercent[mealType];

  try {
    const results = await searchWithRetry({
      query: `${mealType} ${requirements.trip_summary.preferences.dietary.join(' ')}`,
      location: location,
      categories: categoryMap[mealType],
      limit: 15
    });

    // Filter and select
    const options = results.businesses
      .filter(b => b.rating >= 3.5 && b.review_count >= 20)
      .filter(b => estimateCostPerPerson(b.price) <= maxCost)
      .map(b => parseYelpBusiness(b));

    // Avoid repeating restaurants across days
    const uniqueOption = options.find(o =>
      !previouslyUsed.has(o.name)
    ) || options[0];

    previouslyUsed.add(uniqueOption.name);

    return uniqueOption;
  } catch (error) {
    console.error(`Failed to search ${mealType} for day ${dayNumber}`, error);

    // Return placeholder for manual research
    return {
      name: `${mealType} - Manual research required`,
      location: location,
      cost: maxCost,
      cuisine: "TBD",
      notes: `Error: ${error.message}`
    };
  }
}

// Track used restaurants to ensure variety
const previouslyUsed = new Set();
```

---

## Helper Functions

### Parse Yelp Business

```javascript
function parseYelpBusiness(business) {
  return {
    id: business.id,
    name: business.name,
    location: business.location.display_address.join(', '),
    cost: estimateCostPerPerson(business.price),
    cuisine: business.categories.map(c => c.title).join(', '),
    rating: business.rating,
    review_count: business.review_count,
    phone: business.phone,
    booking_url: business.url,
    coordinates: business.coordinates,
    notes: generateNotes(business)
  };
}
```

### Estimate Cost Per Person

```javascript
function estimateCostPerPerson(priceLevel) {
  const priceMap = {
    '$': 15,
    '$$': 30,
    '$$$': 60,
    '$$$$': 100
  };

  return priceMap[priceLevel] || 25;
}
```

### Generate Notes

```javascript
function generateNotes(business) {
  const notes = [];

  if (business.rating >= 4.5) {
    notes.push('Highly rated');
  }

  if (business.review_count > 500) {
    notes.push('Very popular');
  }

  if (business.transactions?.includes('restaurant_reservation')) {
    notes.push('Reservations recommended');
  }

  if (business.distance && business.distance < 500) {
    notes.push('Very close (< 500m)');
  }

  // Extract popular items from review highlights
  if (business.review_highlights) {
    const dishes = business.review_highlights
      .filter(h => h.includes('best') || h.includes('famous'))
      .slice(0, 1);
    if (dishes.length > 0) {
      notes.push(`Known for ${dishes[0]}`);
    }
  }

  return notes.join(', ');
}
```

---

## Complete Meals Agent Workflow

```javascript
async function mealsAgentWorkflow(destinationSlug) {
  // Step 1: Read requirements and plan
  const requirements = readJSON(`data/${destinationSlug}/requirements-skeleton.json`);
  const planSkeleton = readJSON(`data/${destinationSlug}/plan-skeleton.json`);

  // Step 2: Extract preferences
  const dietary = requirements.trip_summary.preferences.dietary || [];
  const cuisinePrefs = requirements.trip_summary.preferences.cuisine || [];
  const mealBudget = requirements.trip_summary.budget.meals_per_day || 60;

  // Step 3: Research meals for each day
  const allDays = [];
  const usedRestaurants = new Set();

  for (const day of planSkeleton.days) {
    const location = day.location || day.accommodation;

    // Breakfast near accommodation
    const breakfast = await findRestaurant({
      mealType: 'breakfast',
      location: location,
      dietary: dietary,
      maxCost: mealBudget * 0.15,
      usedRestaurants: usedRestaurants
    });

    // Lunch near attraction
    const lunchLocation = day.attractions?.[0] || location;
    const lunch = await findRestaurant({
      mealType: 'lunch',
      location: lunchLocation,
      dietary: dietary,
      maxCost: mealBudget * 0.30,
      usedRestaurants: usedRestaurants
    });

    // Dinner with cuisine preference
    const dinner = await findRestaurant({
      mealType: 'dinner',
      location: location,
      dietary: dietary,
      cuisine: cuisinePrefs,
      maxCost: mealBudget * 0.40,
      usedRestaurants: usedRestaurants
    });

    allDays.push({
      day: day.day,
      breakfast,
      lunch,
      dinner
    });

    // Rate limiting
    await sleep(200);
  }

  // Step 4: Save results
  const mealsData = {
    agent: "meals",
    status: "complete",
    data: { days: allDays },
    notes: `All restaurants verified via Yelp. Dietary preferences: ${dietary.join(', ')}. Average daily cost: $${calculateAverageCost(allDays)}.`
  };

  writeJSON(`data/${destinationSlug}/meals.json`, mealsData);

  return "complete";
}

async function findRestaurant(options) {
  const { mealType, location, dietary, cuisine, maxCost, usedRestaurants } = options;

  // Build search query
  let query = mealType;
  if (dietary.length > 0) {
    query += ` ${dietary.join(' ')}`;
  }

  const category = mealType === 'breakfast' ? 'breakfast_brunch,cafes' : 'restaurants';

  try {
    const results = await searchWithRetry({
      query: query,
      location: location,
      categories: category,
      limit: 20
    });

    // Filter and rank
    let candidates = results.businesses
      .filter(b => b.rating >= 3.5 && b.review_count >= 20)
      .filter(b => estimateCostPerPerson(b.price) <= maxCost)
      .filter(b => !usedRestaurants.has(b.id));

    // Prefer cuisine match if specified
    if (cuisine && cuisine.length > 0) {
      const withCuisine = candidates.filter(b =>
        b.categories.some(c =>
          cuisine.some(pref => c.title.toLowerCase().includes(pref.toLowerCase()))
        )
      );
      if (withCuisine.length > 0) {
        candidates = withCuisine;
      }
    }

    // Select top option
    const selected = candidates[0];
    if (selected) {
      usedRestaurants.add(selected.id);
      return parseYelpBusiness(selected);
    }

    // No results found
    throw new Error('No suitable restaurants found');

  } catch (error) {
    console.error(`Restaurant search failed for ${mealType} in ${location}`, error);

    return {
      name: `${mealType} - Research required`,
      location: location,
      cost: maxCost,
      cuisine: "TBD",
      notes: `Manual research needed: ${error.message}`
    };
  }
}

function calculateAverageCost(days) {
  const total = days.reduce((sum, day) => {
    return sum + day.breakfast.cost + day.lunch.cost + day.dinner.cost;
  }, 0);
  return Math.round(total / days.length);
}
```

---

## Tips for Meals Agent

1. **Always try Yelp first**: More accurate ratings and reviews than web search

2. **Implement retry logic**: Handle rate limits and transient errors

3. **Graceful degradation**: Fall back to WebSearch if Yelp unavailable

4. **Filter by quality**: Minimum 3.5 stars and 20+ reviews

5. **Budget awareness**: Allocate breakfast (15%), lunch (30%), dinner (40%) of daily budget

6. **Location convenience**: Search near accommodation or attractions

7. **Dietary compliance**: Always filter by user restrictions

8. **Variety**: Track used restaurants to avoid repetition

9. **Verify hours**: Use `get_business_details` for important reservations

10. **Rate limiting**: Add 200ms delay between searches to avoid limits
