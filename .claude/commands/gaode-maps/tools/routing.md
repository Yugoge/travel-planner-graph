# Gaode Maps - Routing Tools

> **Consolidated Documentation**: See [skills/gaode-maps/tools/routing.md](../../../skills/gaode-maps/tools/routing.md) for complete reference.

## Quick Reference

Route planning for all transportation modes in China.

### Available Tools

1. **driving_route** - Car/taxi routes with traffic and tolls
2. **walking_route** - Pedestrian routes via sidewalks
3. **cycling_route** - Bicycle routes via bike lanes
4. **transit_route** - Public transportation (bus, subway, train)

### Usage

```javascript
// Driving route
driving_route({ origin: "北京", destination: "上海", strategy: 0 })

// Walking route
walking_route({ origin: "天安门", destination: "故宫" })

// Public transit (inter-city)
transit_route({ origin: "北京", destination: "成都", cityd: "成都" })
```

### Route Strategies

**Driving**: 0=fastest, 1=avoid tolls, 2=shortest, 3=avoid highways
**Transit**: 0=fastest, 1=fewest transfers, 2=minimize walking

### Transportation Agent Integration

Use `transit_route` for inter-city travel to get:
- Train schedules and types (high-speed, regular)
- Bus routes and fares
- Duration and cost estimates

---

**For detailed documentation**, including:
- Complete parameter reference
- Response structure with examples
- Multi-city routing strategies
- Error handling and retries
- Cost estimation formulas
- Integration with transportation workflow

**See**: [skills/gaode-maps/tools/routing.md](../../../skills/gaode-maps/tools/routing.md)
