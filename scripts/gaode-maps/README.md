# Gaode Maps Utility Scripts

Python utilities for processing Gaode Maps API responses and transportation planning.

## Scripts Overview

### parse-transit-routes.py

Parse transit route responses from Gaode Maps API into structured format.

**Usage:**
```bash
# From stdin
cat route-response.json | ./parse-transit-routes.py

# From file
./parse-transit-routes.py route-response.json

# Save to file
./parse-transit-routes.py route-response.json -o parsed-route.json
```

**Exit codes:**
- 0: Success
- 1: File not found or invalid JSON
- 2: Unexpected error

---

### recommend-transportation.py

Compare transit and driving options to recommend best transportation.

**Usage:**
```bash
./recommend-transportation.py transit.json driving.json

# With user preferences
./recommend-transportation.py transit.json driving.json -p preferences.json

# Save recommendation
./recommend-transportation.py transit.json driving.json -o recommendation.json
```

**Preferences format:**
```json
{
  "luggage": "light",
  "travelers": 2,
  "fuel_estimate_per_km": 0.6
}
```

**Exit codes:**
- 0: Success
- 1: File not found or invalid JSON
- 2: Unexpected error

---

### fetch-route-with-retry.py

Fetch route with exponential backoff retry logic for transient errors.

**Usage:**
```bash
# Transit route
./fetch-route-with-retry.py "重庆" "成都" -t transit

# Driving route
./fetch-route-with-retry.py "重庆" "成都" -t driving

# With custom retry settings
./fetch-route-with-retry.py "重庆" "成都" -r 5 -d 2.0

# Save to file
./fetch-route-with-retry.py "重庆" "成都" -o route.json
```

**Arguments:**
- `-t, --type`: Route type (transit or driving, default: transit)
- `-c, --cityd`: City for transit routing
- `-r, --max-retries`: Maximum retry attempts (default: 3)
- `-d, --initial-delay`: Initial delay in seconds (default: 1.0)

**Exit codes:**
- 0: Success
- 1: Route fetch failed
- 2: Unexpected error

---

### plan-multi-city.py

Plan transportation for multi-city trips with rate limiting.

**Usage:**
```bash
# Plan route between cities
./plan-multi-city.py Beijing Bazhong Chengdu Shanghai

# Custom starting day
./plan-multi-city.py Beijing Chengdu -s 3

# Save to file
./plan-multi-city.py Beijing Chengdu Shanghai -o multi-city-plan.json
```

**Arguments:**
- `-s, --start-day`: Starting day number (default: 2)
- `-r, --rate-limit-delay`: Delay between requests in seconds (default: 0.2)

**Exit codes:**
- 0: Success
- 1: Invalid input (less than 2 cities)
- 2: Partial success (some routes failed)

---

### transportation-workflow.py

Complete transportation agent workflow for travel planning system.

**Usage:**
```bash
./transportation-workflow.py chongqing-chengdu-2026

# Custom data directory
./transportation-workflow.py destination-slug -d /path/to/data

# Verbose logging
./transportation-workflow.py destination-slug -v
```

**Required input files:**
- `{data-dir}/{destination-slug}/requirements-skeleton.json`
- `{data-dir}/{destination-slug}/plan-skeleton.json`

**Output file:**
- `{data-dir}/{destination-slug}/transportation.json`

**Exit codes:**
- 0: Success
- 1: Workflow failed
- 2: Unexpected error

---

## Common Patterns

### Pipeline Example

```bash
# Fetch, parse, and recommend in pipeline
./fetch-route-with-retry.py "重庆" "成都" -t transit -o transit.json && \
./fetch-route-with-retry.py "重庆" "成都" -t driving -o driving.json && \
./recommend-transportation.py transit.json driving.json -o recommendation.json
```

### Batch Processing

```bash
# Process multiple routes
for origin in Beijing Shanghai Chengdu; do
  for dest in Guangzhou Shenzhen Hangzhou; do
    if [ "$origin" != "$dest" ]; then
      ./fetch-route-with-retry.py "$origin" "$dest" -o "route-${origin}-${dest}.json"
      sleep 0.2  # Rate limiting
    fi
  done
done
```

---

## Error Handling

All scripts follow consistent error handling:

1. **Retryable errors** (429, 5xx): Automatic retry with exponential backoff
2. **Client errors** (4xx except 429): Immediate failure
3. **Network errors**: Retry with backoff
4. **Invalid data**: Immediate failure with clear error message

---

## Logging

Enable verbose logging with `-v` flag:

```bash
./parse-transit-routes.py input.json -v
```

Log levels:
- INFO: Progress and status messages
- DEBUG: Detailed execution flow
- WARNING: Non-fatal issues
- ERROR: Failures requiring attention

---

## Integration with Travel Planner

These scripts are designed to work with the `/plan` command workflow:

1. **Phase 2**: `detect-location-changes.py` identifies location changes
2. **Phase 3**: `transportation-workflow.py` orchestrates route research
3. **Internal**: Other scripts used by workflow as needed

See `/root/travel-planner/.claude/commands/plan.md` for complete workflow.

---

## Testing

Test scripts with sample data:

```bash
# Create test data
echo '{"route": {"transits": [{"segments": [{"transit_type": "railway", "departure": {"name": "Station A", "time": "08:30"}, "arrival": {"name": "Station B", "time": "10:15"}, "duration": 6300, "cost": 154, "distance": 308000}]}]}}' > test-transit.json

# Run parser
./parse-transit-routes.py test-transit.json
```

---

## Notes

- All scripts use UTF-8 encoding for Chinese character support
- JSON output uses `ensure_ascii=False` for readable Chinese text
- Scripts follow PEP 8 style guidelines
- Type hints used for better code clarity
- Proper exception handling with meaningful error messages
