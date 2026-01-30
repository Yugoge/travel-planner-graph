# Example: Place Search with Google Maps

Complete workflow for searching places using Google Maps skill.

## Scenario

User is planning a trip to San Francisco and needs to find top-rated restaurants in the downtown area.

## Step-by-Step Workflow

### Step 1: Set Environment Variable

```bash
export GOOGLE_MAPS_API_KEY="your-api-key-here"
```

### Step 2: Execute Place Search Script

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
  "restaurants in San Francisco downtown" \
  10
```

### Step 3: Parse Response

**Stdout (human-readable)**:
```
Search: restaurants in San Francisco downtown

1. Gary Danko
   Address: 800 North Point St, San Francisco, CA 94109
   Rating: 4.7
   Types: restaurant, food, point_of_interest

2. Kokkari Estiatorio
   Address: 200 Jackson St, San Francisco, CA 94111
   Rating: 4.6
   Types: restaurant, food, point_of_interest

3. Foreign Cinema
   Address: 2534 Mission St, San Francisco, CA 94110
   Rating: 4.5
   Types: restaurant, bar, food

4. Rich Table
   Address: 199 Gough St, San Francisco, CA 94102
   Rating: 4.6
   Types: restaurant, food, point_of_interest

5. Boulevard Restaurant
   Address: 1 Mission St, San Francisco, CA 94105
   Rating: 4.5
   Types: restaurant, food, point_of_interest

...
```

**Stderr (JSON output)**:
```json
{
  "query": "restaurants in San Francisco downtown",
  "results": [
    {
      "name": "Gary Danko",
      "address": "800 North Point St, San Francisco, CA 94109",
      "rating": 4.7,
      "types": ["restaurant", "food", "point_of_interest"],
      "location": {
        "lat": 37.8056,
        "lng": -122.4188
      },
      "place_id": "ChIJ...",
      "price_level": 4
    },
    ...
  ],
  "source": "google_maps"
}
```

### Step 4: Agent Integration

**How agents use this script**:

```markdown
User asks: "Find good restaurants in San Francisco"

Agent executes via Bash tool:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
  "restaurants in San Francisco" 5
```

Agent receives parsed results and formats response:
- Gary Danko (4.7 stars) - Fine dining at 800 North Point St
- Kokkari Estiatorio (4.6 stars) - Greek cuisine at 200 Jackson St
- Foreign Cinema (4.5 stars) - California cuisine at 2534 Mission St
- Rich Table (4.6 stars) - Contemporary American at 199 Gough St
- Boulevard Restaurant (4.5 stars) - American cuisine at 1 Mission St
```

## Advanced Usage

### Search with Location Bias

```bash
# Bias results toward specific coordinates (San Francisco city center)
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
  "coffee shops" \
  10 \
  "37.7749,-122.4194"
```

### Search by Category

```bash
# Hotels
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "hotels in Paris" 20

# Museums
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "museums in London" 15

# Shopping
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "shopping malls in Tokyo" 10
```

### Capture JSON for Programmatic Use

```bash
# Save JSON output to file
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
  "restaurants in Paris" 2>/tmp/places.json

# Parse JSON with jq
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
  "restaurants in Paris" 2>&1 >/dev/null | jq '.results[] | {name, rating, address}'
```

## Error Handling

### Missing API Key

**Command**:
```bash
unset GOOGLE_MAPS_API_KEY
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "restaurants"
```

**Output**:
```
Error: GOOGLE_MAPS_API_KEY environment variable not set
```

**Solution**: Set GOOGLE_MAPS_API_KEY environment variable.

### Invalid Query

**Command**:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py ""
```

**Output**:
```
Error: MCP error: Invalid query parameter
```

**Solution**: Provide a non-empty search query.

## Best Practices

1. **Use specific queries**: "Italian restaurants in Manhattan" vs "food"
2. **Limit results**: Use max_results parameter to avoid excessive API usage
3. **Cache results**: Save JSON output and reuse when possible
4. **Location bias**: Provide coordinates for better local results
5. **Parse JSON**: Use stderr JSON output for programmatic integration

## Integration with Agents

### Meals Agent

```markdown
When user asks for restaurant recommendations:
1. Execute places.py with user's criteria
2. Parse top 5 results
3. Format with ratings, cuisine type, and address
4. Include price level if available
```

### Accommodation Agent

```markdown
When user asks for hotel search:
1. Execute places.py with "hotels in [destination]"
2. Parse results for name, rating, address
3. Supplement with jinko-hotel skill for pricing/booking
```

### Attractions Agent

```markdown
When user asks for tourist attractions:
1. Execute places.py with "tourist attractions in [destination]"
2. Parse results for popular places
3. Cross-reference with tripadvisor skill for reviews
```

## Performance Notes

- Script launches MCP server on each execution (~2 seconds overhead)
- For multiple queries, consider batching or caching
- API rate limits apply (monitor usage at Google Cloud Console)
- Results are real-time (no caching by MCP server)
