---
name: test-mcp
description: Test if agent can directly call MCP tools
---

# Test MCP Skill

## How to use

When user asks for route from Beijing to Shanghai:

**Use tool**: `mcp__plugin_amap-maps_amap-maps__maps_direction_driving`

**Parameters**:
- origin: "116.407387,39.904179" (Beijing coordinates)
- destination: "121.473701,31.230416" (Shanghai coordinates)

**Example call**:
```
Call mcp__plugin_amap-maps_amap-maps__maps_direction_driving with:
{
  "origin": "116.407387,39.904179",
  "destination": "121.473701,31.230416"
}
```

Return the distance and duration from the response.
