# Gaode Maps - POI Search Tools

## Quick Reference

Search for Points of Interest (restaurants, hotels, attractions, services) in China.

### Available Tools

1. **poi_search_keyword** - Search POIs by keyword and category
2. **poi_search_nearby** - Find POIs near specific coordinates
3. **poi_detail** - Get detailed information for specific POI

### Common Category Codes

- `050000` - Food & Dining
- `080000` - Accommodation
- `110000` - Tourist Attractions
- `060000` - Shopping
- `150000` - Transportation (subway, airports)

### Usage

```javascript
// Search restaurants in city
poi_search_keyword({ keywords: "火锅", city: "重庆", types: "050100" })

// Find nearby hotels
poi_search_nearby({ location: "104.065735,30.659462", keywords: "酒店", radius: 1000 })

// Get POI details
poi_detail({ id: "B000A7BD6C" })
```

### Integration with Agents

- **Meals**: Search restaurants by cuisine, filter by rating
- **Accommodation**: Search hotels, compare by location and price
- **Attractions**: Discover landmarks, get business hours
- **Shopping**: Find malls and specialty markets

---

**For detailed documentation**, including:
- Complete category code reference
- Search strategies and filtering
- Pagination and batch processing
- Error handling and fallbacks
- Result enrichment patterns
- Multi-language support

**See**: [skills/gaode-maps/tools/poi-search.md](../../../skills/gaode-maps/tools/poi-search.md)
