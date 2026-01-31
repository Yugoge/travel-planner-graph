# Gaode Maps - Utility Tools

> **Consolidated Documentation**: See [skills/gaode-maps/tools/utilities.md](../../../skills/gaode-maps/tools/utilities.md) for complete reference.

## Quick Reference

Supporting tools for distance calculation and weather information.

### Available Tools

1. **distance_measure** - Calculate distance and travel time between points
2. **weather_info** - Get current weather and 4-day forecast

### Usage

```javascript
// Calculate driving distance
distance_measure({
  origins: "116.481488,39.990464",
  destination: "121.473701,31.230416",
  type: 1  // 0=straight-line, 1=driving, 3=walking
})

// Get weather forecast
weather_info({ city: "成都", extensions: "all" })
```

### Distance Types

- **Type 0**: Straight-line (fastest, feasibility checks)
- **Type 1**: Driving distance (car/taxi planning)
- **Type 3**: Walking distance (pedestrian accessibility)

### Weather Integration

- Use forecast for activity planning (indoor vs outdoor)
- Generate packing recommendations
- Add weather warnings to itinerary

---

**For detailed documentation**, including:
- Distance calculation strategies
- Weather-based activity suggestions
- Packing list generation
- Batch distance calculations
- Caching strategies
- Integration with timeline/budget agents

**See**: [skills/gaode-maps/tools/utilities.md](../../../skills/gaode-maps/tools/utilities.md)
