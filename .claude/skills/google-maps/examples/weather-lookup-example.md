# Example: Weather Lookup with Google Maps

Complete workflow for looking up weather information using Google Maps skill.

## Scenario

User is planning activities in San Francisco and needs to check current weather conditions.

## Step-by-Step Workflow

### Step 1: Set Environment Variable

```bash
export GOOGLE_MAPS_API_KEY="your-api-key-here"
```

### Step 2: Execute Weather Lookup Script

```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py \
  "San Francisco, CA"
```

**Output**:
```
Weather for: San Francisco, CA

Temperature: 16°C
Feels like: 15°C
Conditions: Partly cloudy
Humidity: 72%
Wind: 4.5 m/s NW
Pressure: 1013 hPa
Visibility: 10000 m
```

### Step 3: Parse JSON Output

```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py \
  "San Francisco, CA" 2>/tmp/weather.json

cat /tmp/weather.json | jq '.weather'
```

**JSON Output**:
```json
{
  "location": "San Francisco, CA",
  "weather": {
    "temperature": {
      "current": 16,
      "feels_like": 15,
      "unit": "°C"
    },
    "conditions": "Partly cloudy",
    "humidity": 72,
    "wind": {
      "speed": 4.5,
      "direction": "NW"
    },
    "pressure": 1013,
    "visibility": 10000
  },
  "source": "google_maps"
}
```

## Advanced Usage

### Multiple Locations

```bash
# Check weather for multiple destinations
for city in "Paris, France" "Tokyo, Japan" "New York, NY"; do
  echo "=== $city ==="
  python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "$city" 2>&1 | grep -E "(Temperature|Conditions)"
  echo
done
```

**Output**:
```
=== Paris, France ===
Temperature: 12°C
Conditions: Light rain

=== Tokyo, Japan ===
Temperature: 22°C
Conditions: Clear sky

=== New York, NY ===
Temperature: 8°C
Conditions: Overcast
```

### Extract Specific Fields

```bash
# Get just temperature
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py \
  "London, UK" 2>&1 >/dev/null | jq -r '.weather.temperature.current'

# Output: 10
```

### Weather Comparison for Travel Planning

```bash
#!/bin/bash
# Compare weather across multiple destinations

destinations=("Rome, Italy" "Barcelona, Spain" "Athens, Greece")

for dest in "${destinations[@]}"; do
  temp=$(python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py \
    "$dest" 2>&1 >/dev/null | jq -r '.weather.temperature.current')
  conditions=$(python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py \
    "$dest" 2>&1 >/dev/null | jq -r '.weather.conditions')
  echo "$dest: $temp°C, $conditions"
done
```

**Output**:
```
Rome, Italy: 18°C, Clear sky
Barcelona, Spain: 20°C, Partly cloudy
Athens, Greece: 22°C, Sunny
```

## Agent Integration

### Transportation Agent

**Workflow for weather-aware route planning**:

```markdown
User asks: "What's the best way to get from New York to Boston today?"

Agent checks weather at both locations:

Step 1: Check departure weather
```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "New York, NY"
```

Result: 8°C, Light snow

Step 2: Check destination weather
```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "Boston, MA"
```

Result: 5°C, Heavy snow

Step 3: Compute route
```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York, NY" "Boston, MA" TRANSIT
```

Agent recommendation:
**Weather Advisory**: Heavy snow expected in Boston. Driving not recommended due to
road conditions. Transit via Amtrak is safer option. Expected delays: 30-60 minutes.
```

### Attractions Agent

**Workflow for activity recommendations**:

```markdown
User asks: "What should I do in San Francisco today?"

Agent checks weather:
```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "San Francisco, CA"
```

Result: 16°C, Partly cloudy

Agent recommendation based on weather:
**Perfect weather for outdoor activities!**
- Walk across Golden Gate Bridge (16°C, light wind)
- Visit Fisherman's Wharf (comfortable for walking)
- Outdoor dining at Ferry Building Marketplace

**Indoor alternatives** (if weather changes):
- Exploratorium
- de Young Museum
- California Academy of Sciences
```

### Meals Agent

**Workflow for dining recommendations**:

```markdown
User asks: "Where should I eat dinner in Paris?"

Agent checks weather:
```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "Paris, France"
```

Result: 12°C, Light rain

Agent recommendation:
**Weather consideration**: Light rain expected. Recommend restaurants with:
- Covered outdoor seating (heated terraces)
- Good indoor ambiance
- Easy access from metro stations

Recommended restaurants:
1. Le Comptoir du Relais (indoor bistro, near metro)
2. L'Avant Comptoir (covered terrace, Saint-Germain)
3. Chez Janou (Provençal with indoor seating)
```

## Error Handling

### Missing API Key

**Command**:
```bash
unset GOOGLE_MAPS_API_KEY
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "Paris"
```

**Output**:
```
Error: GOOGLE_MAPS_API_KEY environment variable not set
```

### Invalid Location

**Command**:
```bash
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py "InvalidCity123"
```

**Output**:
```
Error: MCP error: Unable to find location
```

## Best Practices

1. **Use specific locations**: Include city and country for accuracy
2. **Cache results**: Weather data changes slowly, cache for 30-60 minutes
3. **Combine with routing**: Check weather at origin and destination
4. **Parse JSON**: Use stderr JSON output for programmatic integration
5. **Multiple destinations**: Batch weather checks for itinerary planning

## Integration Pattern

**Standard pattern for agents**:

```markdown
1. User asks about activities, transportation, or dining
2. Agent determines relevant location(s)
3. Agent executes weather.py for current conditions
4. Agent adjusts recommendations based on:
   - Temperature (indoor vs outdoor activities)
   - Precipitation (covered vs open venues)
   - Wind (waterfront activities, outdoor dining)
   - Visibility (scenic viewpoints, photography)
5. Agent includes weather context in response
```

## Performance Notes

- Script launches MCP server on each execution (~2 seconds overhead)
- Weather lookup typically completes in 1-2 seconds
- Results are current conditions (not forecast)
- API rate limits apply (monitor usage at Google Cloud Console)

## Weather-Based Decision Tree

**For agents to use**:

```
Temperature:
  < 5°C: Recommend indoor activities, warn about cold
  5-15°C: Moderate weather, both indoor/outdoor OK
  15-25°C: Ideal for outdoor activities
  > 25°C: Recommend shaded areas, indoor options for midday

Conditions:
  Clear/Sunny: Outdoor activities, scenic viewpoints
  Partly Cloudy: All activities suitable
  Rain/Snow: Indoor activities, covered venues
  Heavy Rain/Storm: Indoor only, transit delays possible

Wind:
  < 5 m/s: All activities OK
  5-10 m/s: Avoid waterfront, outdoor dining may be uncomfortable
  > 10 m/s: Indoor activities recommended
```

## Combining Weather with Other Skills

### Weather + Places Search

```bash
# Find indoor attractions in rainy weather
weather=$(python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py \
  "London, UK" 2>&1 >/dev/null | jq -r '.weather.conditions')

if [[ "$weather" == *"rain"* ]]; then
  python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
    "museums in London" 10
fi
```

### Weather + Routing

```bash
# Choose transit over driving in bad weather
weather=$(python3 /root/travel-planner/.claude/skills/google-maps/scripts/weather.py \
  "Boston, MA" 2>&1 >/dev/null | jq -r '.weather.conditions')

if [[ "$weather" == *"snow"* || "$weather" == *"rain"* ]]; then
  mode="TRANSIT"
else
  mode="DRIVE"
fi

source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York, NY" "Boston, MA" $mode
```

## Example Agent Response

**User**: "Plan my day in San Francisco"

**Agent workflow**:
1. Check weather: `weather.py "San Francisco, CA"`
2. Search places: `places.py "attractions in San Francisco" 10`
3. Plan routes: `routing.py "Hotel" "Golden Gate Bridge" DRIVE`

**Agent response**:

```
Good morning! Here's your San Francisco itinerary based on current weather:

**Current Weather**: 16°C, Partly cloudy - Perfect for outdoor activities!

**Morning (9:00 AM - 12:00 PM)**:
- Golden Gate Bridge walk (2.7 km, 35 min)
  Weather: Ideal conditions, light wind

**Lunch (12:00 PM - 1:30 PM)**:
- Ferry Building Marketplace
  Option: Outdoor seating available (comfortable at 16°C)

**Afternoon (2:00 PM - 5:00 PM)**:
- Fisherman's Wharf & Pier 39
  Weather: Slightly warmer, 18°C expected

**Evening (6:00 PM+)**:
- Sunset at Twin Peaks (bring light jacket, cooler at elevation)

**Weather Advisory**: Conditions may change. Indoor backup options:
- Exploratorium, de Young Museum
```
