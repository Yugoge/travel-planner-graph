# Gaode Maps POI Category Codes Reference

Comprehensive category code listing for Gaode Maps POI search tools. Use these codes with the `types` parameter in `poi_search_keyword` and `poi_search_nearby`.

---

## Quick Reference

Most common categories for travel planning:

| Code | Category | Use For |
|------|----------|---------|
| `050000` | Food & Dining | Restaurant search |
| `060000` | Shopping | Malls, markets, stores |
| `080000` | Accommodation | Hotels, hostels |
| `110000` | Tourist Attractions | Landmarks, museums, parks |
| `140000` | Entertainment | Theaters, KTV, bars |
| `150000` | Medical & Health | Hospitals, clinics |

---

## Detailed Categories

### Food & Dining (050000)

#### Chinese Restaurants (050100)
- `050100` - Chinese Restaurant (general)
- `050101` - Beijing Cuisine (京菜)
- `050102` - Sichuan Cuisine (川菜)
- `050103` - Cantonese Cuisine (粤菜)
- `050104` - Hot Pot (火锅)
- `050105` - Hunan Cuisine (湘菜)
- `050106` - Shandong Cuisine (鲁菜)
- `050107` - Jiangsu Cuisine (苏菜)
- `050108` - Zhejiang Cuisine (浙菜)
- `050109` - Shanghai Cuisine (沪菜)
- `050110` - Anhui Cuisine (徽菜)
- `050111` - Fujian Cuisine (闽菜)
- `050112` - Northeastern Cuisine (东北菜)
- `050113` - Northwest Cuisine (西北菜)
- `050114` - Yunnan Cuisine (云南菜)
- `050115` - Guizhou Cuisine (贵州菜)
- `050116` - Hakka Cuisine (客家菜)

#### Foreign Restaurants (050200)
- `050200` - Foreign Restaurant (general)
- `050201` - Western Food
- `050202` - Japanese Food
- `050203` - Korean Food
- `050204` - Southeast Asian Food
- `050205` - South Asian Food
- `050206` - Middle Eastern Food

#### Quick Service (050300)
- `050300` - Fast Food
- `050400` - Snack Bar
- `050500` - Cafe
- `050600` - Tea House
- `050700` - Bakery
- `050800` - Dessert Shop
- `050900` - Bar & Pub

---

### Shopping (060000)

#### Retail Venues (060100-060400)
- `060100` - Shopping Mall
- `060200` - Convenience Store
- `060300` - Supermarket
- `060400` - Traditional Market
- `060500` - Department Store

#### Specialty Stores (060600+)
- `060600` - Electronics Store
- `060700` - Bookstore
- `060800` - Pharmacy
- `060900` - Clothing Store
- `061000` - Sporting Goods
- `061100` - Home Furnishings
- `061200` - Arts & Crafts

---

### Accommodation (080000)

#### Hotels (080100)
- `080100` - Star Hotel (general)
- `080101` - 5-Star Hotel
- `080102` - 4-Star Hotel
- `080103` - 3-Star Hotel
- `080104` - 2-Star Hotel
- `080105` - 1-Star Hotel

#### Budget Options (080200+)
- `080200` - Budget Hotel / Express Hotel
- `080300` - Hostel / Youth Hostel
- `080400` - Guesthouse / Homestay (民宿)
- `080500` - Apartment Hotel

---

### Tourist Attractions (110000)

#### Natural & Parks (110100-110200)
- `110100` - Scenic Spot (风景名胜)
- `110200` - Park & Plaza (公园广场)
- `110800` - Zoo (动物园)
- `110900` - Botanical Garden (植物园)

#### Cultural Sites (110300-110600)
- `110300` - Museum (博物馆)
- `110400` - Temple (寺庙)
- `110500` - Church (教堂)
- `110600` - Art Gallery (美术馆)
- `110700` - Historical Site (古迹)

#### Entertainment Attractions (111000+)
- `111000` - Amusement Park
- `111100` - Theme Park
- `111200` - Water Park
- `111300` - Exhibition Center

---

### Sports & Recreation (120000)

- `120100` - Stadium (体育场馆)
- `120200` - Fitness Center (健身中心)
- `120300` - Swimming Pool (游泳馆)
- `120400` - Sports Club (体育俱乐部)
- `120500` - Golf Course (高尔夫球场)
- `120600` - Ski Resort (滑雪场)

---

### Entertainment (140000)

#### Performing Arts (140100-140200)
- `140100` - Cinema (电影院)
- `140200` - Theater (剧院)
- `140300` - Concert Hall (音乐厅)

#### Nightlife (140400+)
- `140300` - KTV
- `140400` - Bar
- `140500` - Nightclub
- `140600` - Game Center (游戏厅)
- `140700` - Internet Cafe (网吧)

---

### Medical & Health (150000)

#### Medical Facilities (150100-150300)
- `150100` - Hospital (综合医院)
- `150200` - Specialized Hospital (专科医院)
- `150300` - Clinic (诊所)
- `150400` - Emergency Center (急救中心)
- `150500` - Disease Control Center (疾控中心)

#### Health Services (150600+)
- `150600` - Pharmacy (药店)
- `150700` - Medical Laboratory (医学检验)
- `150800` - Health Checkup Center (体检中心)

---

### Transportation (170000)

#### Transit Stations (170100-170400)
- `170100` - Airport (机场)
- `170200` - Railway Station (火车站)
- `170300` - Bus Station (长途汽车站)
- `170400` - Subway Station (地铁站)
- `170500` - Ferry Terminal (码头)

#### Auto Services (170600+)
- `170600` - Gas Station (加油站)
- `170700` - Parking Lot (停车场)
- `170800` - Car Repair (汽车维修)
- `170900` - Car Wash (洗车)

---

### Services (180000)

#### Financial (180100-180300)
- `180100` - Bank (银行)
- `180200` - ATM (ATM)
- `180300` - Insurance Company (保险公司)

#### Public Services (180400+)
- `180400` - Post Office (邮局)
- `180500` - Telecom Office (电信营业厅)
- `180600` - Government Office (政府机关)
- `180700` - Embassy (大使馆)

---

## Usage Tips

### Combining Multiple Categories

Use the pipe `|` operator to search multiple categories:

```javascript
types: "050100|050200"  // Chinese + Foreign restaurants
types: "080100|080200"  // Star hotels + Budget hotels
types: "110100|110200"  // Scenic spots + Parks
```

### Category Hierarchy

- **Top-level** (e.g., `050000`): Broad category, many results
- **Mid-level** (e.g., `050100`): Category group, focused results
- **Specific** (e.g., `050102`): Precise subcategory, highly targeted

**Example**:
```javascript
// Broad: All food & dining
types: "050000"  // ~500 results

// Focused: Chinese restaurants only
types: "050100"  // ~200 results

// Precise: Sichuan cuisine only
types: "050102"  // ~50 results
```

### Search Strategy

1. **Start broad** with keywords only (no types)
2. **Refine** with top-level category if too many results
3. **Target** with specific subcategory if needed

**Example Flow**:
```javascript
// Step 1: Broad search
poi_search_keyword({ keywords: "餐厅", city: "成都" })
// Too many results (500+)

// Step 2: Add category
poi_search_keyword({ keywords: "餐厅", city: "成都", types: "050100" })
// Better (200 results)

// Step 3: Specific cuisine
poi_search_keyword({ keywords: "餐厅", city: "成都", types: "050102" })
// Focused on Sichuan cuisine (50 results)
```

### Common Combinations

**Restaurant Discovery**:
- Chinese: `050100`
- Foreign: `050200`
- Fast Food: `050300`
- Cafes: `050500`

**Accommodation Options**:
- All hotels: `080000`
- Star hotels: `080100`
- Budget: `080200`
- Homestay: `080400`

**Attraction Exploration**:
- All attractions: `110000`
- Cultural: `110300|110400|110600`
- Nature: `110100|110200`
- Entertainment: `111000|111100`

**Shopping Trip**:
- Malls: `060100`
- Markets: `060400`
- Specialty: `060600|060700|061200`

---

## Language Notes

### Chinese Terms

- **餐饮** (cān yǐn) - Food & Dining
- **购物** (gòu wù) - Shopping
- **住宿** (zhù sù) - Accommodation
- **景点** (jǐng diǎn) - Tourist Attraction
- **娱乐** (yú lè) - Entertainment
- **医疗** (yī liáo) - Medical
- **交通** (jiāo tōng) - Transportation

### English Search

Gaode Maps accepts English keywords for:
- International chains: "Starbucks", "McDonald's", "KFC"
- Generic terms: "hotel", "restaurant", "hospital"
- Place names: "Great Wall", "Forbidden City"

**However**, Chinese keywords often yield better results:
- More comprehensive coverage
- Better local business discovery
- Accurate category matching

---

## API Integration

### Basic Usage

```javascript
// Single category
mcp__plugin_amap-maps_amap-maps__poi_search_keyword({
  keywords: "川菜",
  city: "成都",
  types: "050102"  // Sichuan cuisine
})

// Multiple categories
mcp__plugin_amap-maps_amap-maps__poi_search_keyword({
  keywords: "酒店",
  city: "北京",
  types: "080100|080200"  // Star + Budget hotels
})

// No category filter (broad search)
mcp__plugin_amap-maps_amap-maps__poi_search_keyword({
  keywords: "博物馆",
  city: "上海"
  // types omitted - searches all categories
})
```

### Nearby Search

```javascript
mcp__plugin_amap-maps_amap-maps__poi_search_nearby({
  location: "116.397428,39.90923",  // Tiananmen Square
  types: "050000",  // All food & dining
  radius: 1000  // 1km
})
```

---

## See Also

- [POI Search Tools Documentation](../../.claude/skills/gaode-maps/tools/poi-search.md)
- [Gaode Maps API Official Docs](https://lbs.amap.com/api/webservice/guide/api/search)
- [Geocoding Reference](geocoding.md)

---

**Last Updated**: 2026-01-31
**Maintained By**: Claude Code Agent System
