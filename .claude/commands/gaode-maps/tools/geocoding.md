# Gaode Maps - Geocoding Tools

> **Consolidated Documentation**: See [skills/gaode-maps/tools/geocoding.md](../../../skills/gaode-maps/tools/geocoding.md) for complete reference.

## Quick Reference

Convert between addresses and coordinates for Chinese locations.

### Available Tools

1. **geocode** - Convert address to coordinates (forward geocoding)
2. **reverse_geocode** - Convert coordinates to address (reverse geocoding)
3. **ip_location** - Get location from IP address

### Coordinate System

All tools use **GCJ-02** (Mars Coordinates) - China's official coordinate system with ~50-500m offset from WGS-84.

### Usage

```javascript
// Geocode an address
geocode({ address: "洪崖洞", city: "重庆" })

// Reverse geocode coordinates
reverse_geocode({ location: "104.065735,30.659462" })

// Get city from IP
ip_location()
```

### Integration Patterns

- **Transportation**: Geocode origin/destination for routing
- **Accommodation**: Find coordinates for nearby POI search
- **Attractions**: Convert attraction names to coordinates

---

**For detailed documentation**, including:
- Complete parameter reference
- Response structure examples
- Best practices and error handling
- Integration patterns with other agents
- Batch geocoding strategies
- Validation techniques

**See**: [skills/gaode-maps/tools/geocoding.md](../../../skills/gaode-maps/tools/geocoding.md)
