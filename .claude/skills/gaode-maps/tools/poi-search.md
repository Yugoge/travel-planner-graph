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
      "name": "陈麻婆豆腐",
      "address": "青羊区西玉龙街197号",
      "location": "104.052825,30.660381",
      "biz_ext": {"rating": "4.5", "cost": "80"}
      // ... (152 total POIs with full details)
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
      "name": "北京首都机场希尔顿酒店",
      "address": "首都机场T3航站楼C出口",
      "distance": "156",
      "biz_ext": {"rating": "4.7", "cost": "850"}
      // ... (23 total hotels)
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
  "pois": [{
    "name": "陈麻婆豆腐",
    "address": "青羊区西玉龙街197号",
    "tel": "028-86754512",
    "biz_ext": {
      "rating": "4.5",
      "cost": "80",
      "open_time": "10:00-22:00",
      "recommend": "麻婆豆腐,回锅肉,宫保鸡丁"
    },
    "photos": [{"title": "店面", "url": "..."}],
    "business_area": "宽窄巷子"
  }]
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

**Quick Reference** (Most Common):
- `050000` - Food & Dining (all restaurants)
  - `050100` - Chinese Restaurant
  - `050102` - Sichuan Cuisine
  - `050104` - Hot Pot
- `080000` - Accommodation (all hotels)
  - `080100` - Star Hotel
  - `080200` - Budget Hotel
- `110000` - Tourist Attractions (all attractions)
  - `110100` - Scenic Spot
  - `110300` - Museum
- `060000` - Shopping (all shopping venues)
- `140000` - Entertainment (theaters, KTV, bars)

**📚 Complete Category Codes**: For comprehensive listing including:
- All subcategories (150+ codes)
- Category hierarchy and combinations
- Search strategy recommendations
- Chinese/English terminology

**See**: [Gaode POI Categories Reference](../../../docs/reference/gaode-poi-categories.md)

## Quick Tips

Keywords: Use Chinese names, filter by rating ≥3.5, check review count ≥20.
Distance: Meals ≤2km, attractions ≤10km from accommodation.
Performance: Use types parameter, limit offset to 10-20, use extensions=base unless photos needed.

Common errors: NO_RESULT (try broader keywords), OVER_LIMIT (rate limited).

---

**Complete patterns and examples**: See commands/gaode-maps/tools/poi-search.md
