# Gaode Maps - Geocoding Tools

> **Consolidated Documentation**: See commands/gaode-maps/tools/geocoding.md (already consolidated to stub reference).

## Quick Reference

Convert addresses to coordinates (geocoding) and coordinates to addresses (reverse geocoding) for Chinese locations.

### Available Tools

1. **geocode** - Address to coordinates
2. **reverse_geocode** - Coordinates to address
3. **ip_location** - IP to location

### Coordinate System

All tools use **GCJ-02** (Mars Coordinates) - China's official system with offset from WGS-84.

### Usage

```javascript
// Geocode address
mcp__plugin_amap-maps_amap-maps__geocode({
  address: "洪崖洞",
  city: "重庆"
})

// Reverse geocode coordinates
mcp__plugin_amap-maps_amap-maps__reverse_geocode({
  location: "104.065735,30.659462"
})
```

### Integration

- **Transportation**: Geocode origin/destination for routing
- **Accommodation**: Find coordinates for nearby POI search
- **Attractions**: Convert names to coordinates

---

**For complete documentation**: Integration patterns, batch processing, error handling examples - see the commands version which references the full skills documentation.
