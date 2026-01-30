# Example: Route Computation with Google Maps

Complete workflow for computing travel routes using Google Maps skill.

## Scenario

User is traveling from New York to Boston and needs to compare different transportation modes.

## Step-by-Step Workflow

### Step 1: Set Environment Variable

```bash
export GOOGLE_MAPS_API_KEY="your-api-key-here"
```

### Step 2: Execute Route Computation Script

#### Driving Route

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York, NY" \
  "Boston, MA" \
  DRIVE
```

**Output**:
```
Route: New York, NY → Boston, MA
Travel Mode: DRIVE

Distance: 346.2 km (346200 meters)
Duration: 3h 52m (13920s)
Polyline available: Yes

Route Steps (5 steps):
  1. Head east on E 42nd St toward 5th Ave (200m)
  2. Turn right onto I-95 N (320000m)
  3. Take exit 45 toward Boston (15000m)
  4. Merge onto I-90 E (8000m)
  5. Take exit 24A to Downtown Boston (3000m)
  ... and 0 more steps
```

#### Transit Route

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York, NY" \
  "Boston, MA" \
  TRANSIT
```

**Output**:
```
Route: New York, NY → Boston, MA
Travel Mode: TRANSIT

Distance: 363.5 km (363500 meters)
Duration: 4h 15m (15300s)
Polyline available: Yes

Route Steps (3 steps):
  1. Walk to Penn Station (800m)
  2. Take Amtrak Northeast Regional to Boston South Station (360000m)
  3. Walk to destination (700m)
```

#### Walking Route (for short distances)

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "Times Square" \
  "Central Park" \
  WALK
```

**Output**:
```
Route: Times Square → Central Park
Travel Mode: WALK

Distance: 1.2 km (1200 meters)
Duration: 15m (900s)
Polyline available: Yes

Route Steps (5 steps):
  1. Head north on 7th Ave (400m)
  2. Turn right onto W 59th St (300m)
  3. Enter Central Park (200m)
  4. Follow path to destination (250m)
  5. Arrive at Central Park (50m)
```

### Step 3: Parse JSON Output

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York" "Boston" DRIVE 2>/tmp/route.json

cat /tmp/route.json | jq '{
  origin: .origin,
  destination: .destination,
  mode: .travel_mode,
  distance_km: (.route.distanceMeters / 1000),
  duration_hours: (.route.duration | tonumber | . / 3600)
}'
```

**JSON Output**:
```json
{
  "origin": "New York",
  "destination": "Boston",
  "mode": "DRIVE",
  "distance_km": 346.2,
  "duration_hours": 3.87
}
```

## Advanced Usage

### Route with Waypoints

```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "Paris, France" \
  "Berlin, Germany" \
  DRIVE \
  "Brussels,Belgium,Amsterdam,Netherlands"
```

**Output includes waypoints**:
```
Route: Paris, France → Berlin, Germany
Travel Mode: DRIVE
Waypoints: Brussels, Belgium; Amsterdam, Netherlands

Distance: 1,245.8 km (1245800 meters)
Duration: 12h 45m (45900s)
```

### Multi-Modal Comparison

```bash
# Compare all travel modes for inter-city route
for mode in DRIVE TRANSIT; do
  echo "=== $mode ==="
  python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
    "San Francisco, CA" "Los Angeles, CA" $mode 2>&1 | grep -E "(Distance|Duration)"
  echo
done
```

**Output**:
```
=== DRIVE ===
Distance: 617.3 km (617300 meters)
Duration: 5h 52m (21120s)

=== TRANSIT ===
Distance: 634.2 km (634200 meters)
Duration: 11h 30m (41400s)
```

## Agent Integration

### Transportation Agent

**Workflow for inter-city transportation**:

```markdown
User asks: "How do I get from New York to Boston?"

Agent executes multiple route computations:

Step 1: Check driving option
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York, NY" "Boston, MA" DRIVE
```

Step 2: Check transit option
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York, NY" "Boston, MA" TRANSIT
```

Step 3: Compare results and recommend:

**Driving**:
- Distance: 346 km
- Duration: 3h 52m
- Cost: ~$30 gas + tolls

**Transit (Train)**:
- Distance: 364 km
- Duration: 4h 15m
- Cost: $49-$150 (Amtrak)

**Recommendation**: Transit via Amtrak Northeast Regional is recommended for comfort,
avoiding traffic, and similar travel time. Driving offers flexibility for side trips.
```

### Attractions Agent

**Workflow for walking routes between attractions**:

```markdown
User has visited Eiffel Tower and wants to walk to Arc de Triomphe.

Agent executes:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "Eiffel Tower, Paris" \
  "Arc de Triomphe, Paris" \
  WALK
```

Result: 2.4 km, 30 minutes walking along Champs-Élysées
```

## Error Handling

### Invalid Travel Mode

**Command**:
```bash
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York" "Boston" FLY
```

**Output**:
```
Error: Invalid travel mode: FLY
```

**JSON Output**:
```json
{
  "error": "Invalid travel mode: FLY",
  "valid_modes": ["DRIVE", "WALK", "BICYCLE", "TRANSIT"]
}
```

### Missing API Key

**Command**:
```bash
unset GOOGLE_MAPS_API_KEY
python3 /root/travel-planner/.claude/skills/google-maps/scripts/routing.py \
  "New York" "Boston"
```

**Output**:
```
Error: GOOGLE_MAPS_API_KEY environment variable not set
```

## Best Practices

1. **Choose appropriate travel mode**: DRIVE for long distances, WALK for nearby locations
2. **Use waypoints for complex routes**: Add intermediate stops for better route planning
3. **Cache results**: Save JSON output for repeated queries
4. **Compare modes**: Execute multiple times with different modes for comparison
5. **Parse JSON**: Use stderr JSON output for extracting specific fields (distance, duration)

## Performance Notes

- Script launches MCP server on each execution (~2 seconds overhead)
- Route computation typically completes in 1-3 seconds
- Complex routes with waypoints may take longer
- API rate limits apply (monitor usage at Google Cloud Console)

## Integration Pattern

**Standard pattern for agents**:

```markdown
1. User provides origin and destination
2. Agent determines appropriate travel mode(s) based on:
   - Distance (short: WALK, long: DRIVE/TRANSIT)
   - User preferences (time, cost, comfort)
   - Context (intra-city vs inter-city)
3. Agent executes routing.py with selected mode(s)
4. Agent parses results and formats recommendation
5. Agent includes distance, duration, and key waypoints
```

**Example agent response**:

```markdown
To get from San Francisco to Los Angeles:

**Driving**: 617 km, 5h 52m
- Take I-5 S for most direct route
- Alternative: Pacific Coast Highway (CA-1) for scenic route (longer)

**Transit**: 634 km, 11h 30m
- Amtrak Coast Starlight: $60-$150
- More comfortable, can work/relax during journey

**Recommendation**: Driving offers flexibility and shorter travel time.
Transit recommended if you want to avoid traffic and enjoy scenery.
```
