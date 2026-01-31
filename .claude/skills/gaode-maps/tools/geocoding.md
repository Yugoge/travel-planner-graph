# Gaode Maps - Geocoding Tools

Address and coordinate conversion for Chinese locations.

## MCP Tools

### Tool 1: geocode

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__geocode`

**Purpose**: Convert Chinese addresses or place names to geographic coordinates (GCJ-02).

**Parameters**:
- `address` (required): Address or place name to geocode
  - Structured: "北京市朝阳区望京街10号"
  - Unstructured: "天安门广场"
  - Landmark: "北京首都国际机场"
- `city` (optional): City name to improve accuracy
  - Required if address is ambiguous
  - Examples: "北京", "上海", "成都"
- `batch` (optional): Batch geocoding ("|" separated addresses)

**Returns**:
- `geocodes` array, each containing:
  - `formatted_address` - Standardized address
  - `province` - Province name
  - `city` - City name
  - `district` - District/county name
  - `township` - Township/street name
  - `street` - Street name
  - `number` - Street number
  - `location` - Coordinates as "lng,lat" (GCJ-02)
  - `level` - Geocoding precision:
    - `国家` - Country level
    - `省` - Province level
    - `市` - City level
    - `区县` - District level
    - `开发区` - Development zone
    - `乡镇` - Township level
    - `村庄` - Village level
    - `热点商圈` - Business district
    - `房号` - Building number (most precise)
    - `门牌号` - Street address (very precise)
    - `POI` - Point of interest
    - `道路` - Road
    - `道路交叉口` - Intersection

**Example (Landmark)**:
```javascript
mcp__plugin_amap-maps_amap-maps__geocode({
  address: "天安门",
  city: "北京"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "geocodes": [{
    "formatted_address": "北京市东城区天安门广场",
    "location": "116.397428,39.90923",
    "level": "POI"
  }]
}
```

**Example (Full Address)**:
```javascript
mcp__plugin_amap-maps_amap-maps__geocode({
  address: "朝阳区望京街10号望京SOHO",
  city: "北京"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "geocodes": [{
    "formatted_address": "北京市朝阳区望京街10号",
    "location": "116.480881,39.996567",
    "level": "门牌号"
  }]
}
```

**Example (Batch)**:
```javascript
mcp__plugin_amap-maps_amap-maps__geocode({
  address: "天安门|故宫|长城",
  city: "北京"
})
```

**Use Cases**:
- Convert hotel address to coordinates for routing
- Geocode attraction names for mapping
- Validate and standardize user-provided addresses
- Batch geocode itinerary locations
- Find coordinates for POI names

---

### Tool 2: reverse_geocode

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__reverse_geocode`

**Purpose**: Convert geographic coordinates to human-readable addresses.

**Parameters**:
- `location` (required): Coordinates as "longitude,latitude" (GCJ-02)
- `radius` (optional): Search radius in meters (default 1000, max 3000)
  - Larger radius finds more POIs
  - Smaller radius more precise
- `extensions` (optional): Detail level
  - `base` - Address only (default)
  - `all` - Include nearby POIs and roads
- `roadlevel` (optional): Road hierarchy level (0 or 1)
- `batch` (optional): Batch reverse geocoding ("|" separated coords)

**Returns**:
- `regeocodes` array, each containing:
  - `formatted_address` - Full human-readable address
  - `addressComponent` - Structured address parts:
    - `province` - Province
    - `city` - City
    - `district` - District
    - `township` - Township
    - `street` - Street name
    - `streetNumber` - Street number
    - `neighborhood` - Neighborhood name
    - `building` - Building name
    - `adcode` - Administrative division code
  - `pois` - Nearby POIs (if extensions=all):
    - `name` - POI name
    - `type` - Category
    - `distance` - Distance in meters
    - `direction` - Compass direction
    - `address` - POI address
    - `location` - POI coordinates
  - `roads` - Nearby roads (if extensions=all)
  - `roadinters` - Nearby intersections (if extensions=all)

**Example (Basic)**:
```javascript
mcp__plugin_amap-maps_amap-maps__reverse_geocode({
  location: "116.397428,39.90923",
  extensions: "base"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "regeocode": {
    "formatted_address": "北京市东城区东华门街道天安门广场",
    "addressComponent": {"district": "东城区", "street": "天安门广场"}
  }
}
```

**Example (With POIs)**:
```javascript
mcp__plugin_amap-maps_amap-maps__reverse_geocode({
  location: "116.480881,39.996567",
  radius: 500,
  extensions: "all"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "regeocode": {
    "formatted_address": "北京市朝阳区望京街道望京街10号",
    "addressComponent": {"building": "望京SOHO"},
    "pois": [
      {"name": "望京SOHO", "distance": "18.5"},
      {"name": "望京地铁站", "distance": "245.7"}
      // ... (nearby POIs)
    ],
    "roads": [{"name": "望京街", "distance": "12.3"}]
  }
}
```

**Use Cases**:
- Convert GPS coordinates to address
- Find nearby landmarks for location description
- Identify neighborhood from coordinates
- Determine administrative district
- Discover nearby POIs for context

---

### Tool 3: ip_location

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__ip_location`

**Purpose**: Get approximate geographic location from IP address.

**Parameters**:
- `ip` (optional): IP address to locate
  - IPv4 format: "114.247.50.2"
  - If omitted: Uses requester's IP address
- `output` (optional): Response format (JSON or XML)

**Returns**:
- `province` - Province name
- `city` - City name
- `adcode` - Administrative division code
- `rectangle` - Approximate bounding box "lng1,lat1;lng2,lat2"

**Example**:
```javascript
mcp__plugin_amap-maps_amap-maps__ip_location({
  ip: "114.247.50.2"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "city": "北京市",
  "adcode": "110000"
}
```

**Example (Auto-detect)**:
```javascript
mcp__plugin_amap-maps_amap-maps__ip_location({})
```

**Use Cases**:
- Determine user's likely location
- Auto-suggest nearby cities
- Default city for search
- Regional content customization
- Fraud detection (unusual location)

**Limitations**:
- Accuracy: City-level only (±50km)
- VPN/Proxy: May show VPN server location
- Mobile: May not reflect current location
- Corporate: May show headquarters, not branch

---

## Coordinate System: GCJ-02

### Understanding China's Coordinate System

**GCJ-02 (Mars Coordinates)**:
- Official coordinate system for China
- Mandated by Chinese government
- Offsets WGS-84 (GPS) by ~50-500 meters
- Used by Gaode, Google Maps China, Apple Maps China

**Why It Exists**:
- National security regulation
- Prevents precise military targeting
- Applied to all digital maps in China

**Coordinate Systems Comparison**:
| System | Used By | Offset from GPS |
|--------|---------|-----------------|
| WGS-84 | GPS satellites, Google Maps global | None (reference) |
| GCJ-02 | Gaode, Google Maps CN, Apple Maps CN | ~50-500m SE |
| BD-09 | Baidu Maps only | ~50-700m SE |

### Working with GCJ-02

**Best Practices**:
1. **Use Gaode's geocoding**: Always geocode Chinese addresses with Gaode, not Google
2. **Don't mix systems**: Never combine WGS-84 and GCJ-02 coordinates
3. **Convert if needed**: Use conversion tools for GPS device data
4. **Keep native**: Store coordinates in GCJ-02 for China locations

**When to Convert**:
- GPS device → GCJ-02: Use `geocode` with address
- User input → GCJ-02: Geocode the address
- GCJ-02 → Display: No conversion needed (already correct)

**Conversion Tools** (if needed):
```python
# WGS-84 to GCJ-02 (GPS to Gaode)
# Use external library like coordTransform or eviltransform
# Or geocode address in Gaode directly (recommended)
```

---

## Best Practices

### 1. Geocoding Strategy

**For Accuracy**:
```markdown
1. Use most detailed address available
2. Include city parameter
3. Prefer structured addresses
4. Validate level precision in response
5. Accept level ≥ "POI" for most uses
```

**Quality Thresholds**:
- `门牌号` (street number) - Excellent, use directly
- `POI` - Good for landmarks and businesses
- `道路` (road) - Fair, may need manual adjustment
- `区县` (district) - Poor, address too vague

### 2. Reverse Geocoding Strategy

**For Context**:
```markdown
1. Use extensions=all for rich context
2. Check pois array for landmarks
3. Use formatted_address for display
4. Check building name in addressComponent
5. Use adcode for administrative lookup
```

**Radius Selection**:
- 100m - Precise location, immediate vicinity
- 500m - Walking distance, neighborhood
- 1000m - Local area, multiple POIs
- 3000m - District, broader context

### 3. Batch Processing

**Efficient Batching**:
```markdown
1. Group up to 10 addresses/coordinates per request
2. Separate with "|" character
3. Process responses in same order
4. Handle partial failures gracefully
5. Retry failed items individually
```

**Example**:
```javascript
// Batch geocode 3 hotels
geocode({
  address: "北京希尔顿酒店|上海和平饭店|广州白天鹅宾馆"
})
```

### 4. Error Handling

**Common Issues**:
- Ambiguous addresses: Add city parameter
- No results: Try broader address (remove street number)
- Low precision: Address incomplete or incorrect
- Invalid coordinates: Check format "lng,lat" not "lat,lng"

**Validation**:
```python
def validate_geocode_result(result):
    if result["status"] != "1":
        return False
    if not result["geocodes"]:
        return False
    level = result["geocodes"][0]["level"]
    if level in ["门牌号", "POI", "道路", "道路交叉口"]:
        return True  # Acceptable precision
    return False  # Too vague
```

## Integration Patterns

### Pattern 1: Address Standardization
```markdown
1. Load `/gaode-maps geocoding`
2. Call `geocode` with user-provided address
3. Extract formatted_address from response
4. Use standardized address in database
5. Store coordinates for future routing
```

### Pattern 2: Location Enrichment
```markdown
1. Have coordinates from route planning
2. Call `reverse_geocode` with extensions=all
3. Extract nearby POIs for context
4. Use formatted_address for display
5. Enhance trip itinerary with landmarks
```

### Pattern 3: Multi-location Validation
```markdown
1. Collect all addresses from itinerary
2. Batch geocode using "|" separator
3. Validate all levels ≥ "POI"
4. Flag low-precision results for review
5. Store coordinates for routing phase
```

## Performance Tips

- **Cache geocoded addresses**: Reuse popular locations
- **Batch when possible**: 1 request for 10 addresses
- **Use city parameter**: Faster and more accurate
- **Store coordinates**: Geocode once, route many times
- **Reverse sparingly**: Only when address needed for display

## Data Quality Notes

- **Urban areas**: Very accurate (±10m)
- **Rural areas**: Moderate accuracy (±50m)
- **New developments**: May lag by 3-6 months
- **Street numbers**: Not always available in small cities
- **POI names**: Excellent coverage for major businesses

---

**Token Count**: ~2000 tokens (loaded on demand only)
