# Gaode Maps - POI Search Tools

Point of Interest search for restaurants, hotels, attractions, and more in China.

## MCP Tools

### Tool 1: poi_search_keyword

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__poi_search_keyword`

**Purpose**: Search for POIs by keyword, category, or name within a specified area.

**Parameters**:
- `keywords` (required): Search keywords (Chinese or English)
  - Business names: "星巴克", "Starbucks"
  - Categories: "餐厅", "酒店", "景点"
  - Combinations: "川菜 餐厅"
- `city` (optional): City name or adcode (e.g., "北京", "110000")
  - Required for city-wide search
  - Omit for nationwide search (slower)
- `types` (optional): POI category codes (see category table below)
  - Format: "050000" (food), "100000" (attractions)
  - Multiple: "050000|100000"
- `offset` (optional): Results per page (max 50, default 20)
- `page` (optional): Page number (starting from 1)
- `extensions` (optional): Detail level
  - `base` - Basic info (default)
  - `all` - Full details including photos, reviews

**Returns**:
- `pois` array, each containing:
  - `id` - Unique POI identifier
  - `name` - POI name (Chinese)
  - `type` - Category type code
  - `typecode` - Subcategory code
  - `address` - Full address
  - `location` - Coordinates "lng,lat" (GCJ-02)
  - `tel` - Phone number
  - `distance` - Distance from search center (if applicable)
  - `biz_ext` - Business info:
    - `rating` - User rating (0-5)
    - `cost` - Average price (CNY)
  - `photos` - Array of photo URLs (if extensions=all)

**Category Codes**:
| Code | Category | Examples |
|------|----------|----------|
| 050000 | Food & Dining | Restaurants, cafes, bars |
| 060000 | Shopping | Malls, markets, stores |
| 080000 | Accommodation | Hotels, hostels, guesthouses |
| 110000 | Tourist Attractions | Landmarks, museums, parks |
| 120000 | Sports & Recreation | Gyms, stadiums, pools |
| 140000 | Entertainment | Theaters, KTV, cinemas |
| 150000 | Medical & Health | Hospitals, clinics, pharmacies |

**Example (Restaurant Search)**:
```javascript
mcp__plugin_amap-maps_amap-maps__poi_search_keyword({
  keywords: "川菜",
  city: "成都",
  types: "050000",
  offset: 10,
  extensions: "all"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "count": "152",
  "pois": [
    {
      "id": "B001B0FKW6",
      "name": "陈麻婆豆腐",
      "type": "餐饮服务;中餐厅;川菜馆",
      "typecode": "050102",
      "address": "青羊区西玉龙街197号",
      "location": "104.052825,30.660381",
      "tel": "028-86754512",
      "biz_ext": {
        "rating": "4.5",
        "cost": "80"
      },
      "photos": [
        {"url": "https://store.is.autonavi.com/..."}
      ]
    }
  ]
}
```

**Use Cases**:
- Find restaurants by cuisine type
- Search hotels in specific area
- Locate attractions by name
- Discover shopping districts
- Filter by rating and price

---

### Tool 2: poi_search_nearby

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__poi_search_nearby`

**Purpose**: Find POIs near a specific coordinate location.

**Parameters**:
- `location` (required): Center point as "longitude,latitude"
- `keywords` (optional): Filter by keywords
- `types` (optional): Filter by category codes (see poi_search_keyword)
- `radius` (optional): Search radius in meters (default 1000, max 50000)
- `offset` (optional): Results per page (max 50, default 20)
- `page` (optional): Page number
- `sortrule` (optional): Sort order
  - `distance` - Nearest first (default)
  - `weight` - By importance/popularity
- `extensions` (optional): Detail level (base or all)

**Returns**:
- Same structure as `poi_search_keyword`
- Results ordered by distance from center point
- Each POI includes `distance` field in meters

**Example (Hotels near airport)**:
```javascript
mcp__plugin_amap-maps_amap-maps__poi_search_nearby({
  location: "116.597466,40.072919",  // Beijing Capital Airport
  keywords: "酒店",
  types: "080000",
  radius: 3000,
  sortrule: "distance",
  extensions: "all"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "count": "23",
  "pois": [
    {
      "id": "B0FFGJXJ6P",
      "name": "北京首都机场希尔顿酒店",
      "type": "住宿服务;宾馆酒店;星级酒店",
      "address": "首都机场T3航站楼C出口",
      "location": "116.596234,40.071582",
      "distance": "156",
      "biz_ext": {
        "rating": "4.7",
        "cost": "850"
      }
    }
  ]
}
```

**Use Cases**:
- Find nearby restaurants for meals
- Locate hotels near attraction
- Discover POIs within walking distance
- Search amenities near accommodation
- Emergency services (hospitals, police)

---

### Tool 3: poi_detail

**MCP Tool Name**: `mcp__plugin_amap-maps_amap-maps__poi_detail`

**Purpose**: Get comprehensive details for a specific POI by ID.

**Parameters**:
- `id` (required): POI unique identifier (from search results)
- `extensions` (optional): Detail level
  - `base` - Basic info
  - `all` - Full details (default)

**Returns**:
- Single POI object with extended information:
  - All fields from search results
  - `photos` - Array of photo objects with URLs
  - `biz_ext` - Extended business data:
    - `rating` - Aggregate rating (0-5)
    - `cost` - Average cost per person
    - `open_time` - Opening hours
    - `recommend` - Featured dishes/services
  - `indoor_map` - Indoor floor plan (if available)
  - `business_area` - Business district name
  - `parking_type` - Parking availability

**Example**:
```javascript
mcp__plugin_amap-maps_amap-maps__poi_detail({
  id: "B001B0FKW6",
  extensions: "all"
})
```

**Response Structure**:
```json
{
  "status": "1",
  "pois": [
    {
      "id": "B001B0FKW6",
      "name": "陈麻婆豆腐",
      "type": "餐饮服务;中餐厅;川菜馆",
      "address": "青羊区西玉龙街197号",
      "location": "104.052825,30.660381",
      "tel": "028-86754512",
      "biz_ext": {
        "rating": "4.5",
        "cost": "80",
        "open_time": "10:00-22:00",
        "recommend": "麻婆豆腐,回锅肉,宫保鸡丁"
      },
      "photos": [
        {
          "title": "店面",
          "url": "https://store.is.autonavi.com/..."
        },
        {
          "title": "麻婆豆腐",
          "url": "https://store.is.autonavi.com/..."
        }
      ],
      "parking_type": "路边停车",
      "business_area": "宽窄巷子"
    }
  ]
}
```

**Use Cases**:
- Get detailed restaurant information
- Check hotel amenities and photos
- Verify attraction opening hours
- Read specialty recommendations
- View location photos

---

## POI Category Reference

### Detailed Category Codes

**Food & Dining (050000)**:
- `050100` - Chinese Restaurant
  - `050101` - Beijing Cuisine
  - `050102` - Sichuan Cuisine
  - `050103` - Cantonese Cuisine
  - `050104` - Hot Pot
- `050200` - Foreign Restaurant
  - `050201` - Western Food
  - `050202` - Japanese Food
  - `050203` - Korean Food
- `050300` - Fast Food
- `050500` - Cafe
- `050600` - Tea House
- `050700` - Bakery
- `050800` - Dessert Shop

**Shopping (060000)**:
- `060100` - Shopping Mall
- `060200` - Convenience Store
- `060300` - Supermarket
- `060400` - Market
- `060500` - Specialty Store

**Accommodation (080000)**:
- `080100` - Star Hotel
  - `080101` - 5-star
  - `080102` - 4-star
  - `080103` - 3-star
- `080200` - Budget Hotel
- `080300` - Hostel
- `080400` - Guesthouse

**Tourist Attractions (110000)**:
- `110100` - Scenic Spot
- `110200` - Park & Plaza
- `110300` - Museum
- `110400` - Temple
- `110500` - Church
- `110600` - Art Gallery
- `110700` - Zoo
- `110800` - Botanical Garden

**Entertainment (140000)**:
- `140100` - Cinema
- `140200` - Theater
- `140300` - KTV
- `140400` - Bar
- `140500` - Club
- `140600` - Game Center

## Best Practices

### 1. Search Strategy

**Broad to Specific**:
```markdown
1. Start with city-wide keyword search
2. Filter by category type
3. Sort by rating or distance
4. Get details for top results
```

**Location-based**:
```markdown
1. Geocode address to coordinates
2. Use poi_search_nearby with radius
3. Adjust radius if too few/many results
4. Get details for promising POIs
```

### 2. Keyword Optimization

**Effective Keywords**:
- Chinese names: "陈麻婆豆腐" (specific) > "川菜" (category)
- English acceptable: "Starbucks" works for chains
- Combined: "三星堆 博物馆" (name + type)

**Avoid**:
- Generic terms alone: "好吃" (delicious)
- Overly specific: "便宜的川菜小炒"
- Mixed languages: "delicious 川菜"

### 3. Result Filtering

**Quality Thresholds**:
- Rating ≥ 3.5 stars (good quality)
- Review count ≥ 20 (reliable rating)
- Cost appropriate to budget tier

**Distance Considerations**:
- Meals: ≤ 2km from accommodation (walkable)
- Attractions: ≤ 10km from accommodation (manageable)
- Hotels: ≤ 5km from main activities

### 4. Response Parsing

**Extract Key Data**:
```python
poi = {
    "name": result["name"],
    "address": result["address"],
    "coordinates": result["location"],
    "phone": result.get("tel", "N/A"),
    "rating": result["biz_ext"]["rating"],
    "cost": result["biz_ext"]["cost"],
    "distance": result.get("distance", 0)
}
```

**Handle Missing Data**:
- Rating missing: Default to 3.0 or skip
- Cost missing: Use "Price unavailable"
- Phone missing: Check online for booking info

## Integration Patterns

### Pattern 1: Multi-step POI Discovery
```markdown
1. Load `/gaode-maps poi-search`
2. Search by keyword in city
3. Filter results by rating ≥ 4.0
4. Get details for top 3 results
5. Structure output with photos and hours
```

### Pattern 2: Radius-based Search
```markdown
1. Geocode accommodation address
2. Search nearby restaurants (radius 1000m)
3. Sort by distance
4. Get details for closest 3
5. Recommend based on cuisine variety
```

### Pattern 3: Category Comparison
```markdown
1. Search "酒店" in area
2. Filter: types="080100" (star hotels)
3. Compare ratings and costs
4. Search "民宿" in same area
5. Filter: types="080400" (guesthouses)
6. Present both options with pros/cons
```

## Error Handling

**Common Errors**:
- "INVALID_USER_KEY" - Check API key configuration
- "DAILY_QUERY_OVER_LIMIT" - Rate limit hit, wait or upgrade
- "NO_RESULT" - Try broader keywords or larger radius
- "INVALID_PARAMS" - Check coordinate format (lng,lat)

**Retry Strategy**:
```python
if status != "1":
    if "NO_RESULT" in info:
        # Try alternative keywords
        keywords = fallback_keywords
    elif "OVER_LIMIT" in info:
        # Use WebSearch fallback
        use_websearch()
    else:
        # Log error and skip
        log_error(info)
```

## Performance Tips

- **Use types parameter**: Faster than keyword-only search
- **Limit offset**: 10-20 results usually sufficient
- **Cache popular POIs**: Reuse details across queries
- **Batch requests**: Group related searches when possible
- **extensions=base**: Use unless photos needed (faster)

## Data Quality Notes

- **Ratings**: Generally reliable for ≥20 reviews
- **Cost**: Average price, actual may vary ±20%
- **Hours**: May not reflect holidays or special events
- **Photos**: User-submitted, may be outdated
- **Address**: Highly accurate in cities, verify in rural areas

---

**Token Count**: ~2200 tokens (loaded on demand only)
