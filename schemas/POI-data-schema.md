# POI Data Schema Specification

This document defines the unified data structure for all Point-of-Interest (POI) types in the travel planner system.

## Core Principle

All POI types share a common base structure with type-specific extensions. Field names follow the `_base` / `_local` convention for bilingual support.

## Universal Fields (All POI Types)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name_base` | string | Yes | English name |
| `name_local` | string | Yes | Local language name (e.g., Chinese) |
| `location_base` | string | No | English address |
| `location_local` | string | No | Local language address |
| `coordinates` | object | No | `{lat: float, lng: float}` in GCJ-02 |
| `cost` | number | No | Cost in local currency |
| `currency_local` | string | No | ISO 4217 code (e.g., "CNY", "EUR") |
| `notes_base` | string | No | English notes |
| `notes_local` | string | No | Local language notes |
| `search_results` | array | No | List of search result objects |
| `time` | object | No | `{start: "HH:MM", end: "HH:MM"}` |
| `**optional**` | boolean | **Yes** | **Whether this POI is optional to visit** |
| `links` | object | No | External links (maps, booking, etc.) |

## Type-Specific Fields

### Attractions (`attractions.json`)

```json
{
  "duration_minutes": number,
  "type_base": string,
  "type_local": string,
  "opening_hours": string
}
```

### Meals (`meals.json` - breakfast/lunch/dinner)

```json
{
  "cuisine_base": string,
  "cuisine_local": string,
  "signature_dishes_base": array,
  "signature_dishes_local": array
}
```

### Accommodation (`accommodation.json`)

```json
{
  "type_base": string,
  "type_local": string,
  "stars": number,
  "check_in": string,  // "HH:MM"
  "check_out": string, // "HH:MM"
  "amenities_base": array,
  "amenities_local": array
}
```

### Entertainment (`entertainment.json`)

```json
{
  "duration_minutes": number,
  "type_base": string,
  "type_local": string
}
```

### Shopping (`shopping.json`)

```json
{
  "duration_minutes": number,
  "type_base": string,
  "type_local": string
}
```

### Transportation (`transportation.json` - structure differs)

```json
{
  "location_change": {
    "from_base": string,
    "from_local": string,
    "to_base": string,
    "to_local": string,
    "type_base": string,
    "type_local": string,
    "departure_point_base": string,
    "departure_point_local": string,
    "arrival_point_base": string,
    "arrival_point_local": string,
    "route_number": string,
    "company_base": string,
    "company_local": string,
    "status_base": string,
    "status_local": string,
    "cost": number,
    "currency_local": string,
    "booking_required": boolean,
    "booking_urgency": string,
    "notes_base": string,
    "notes_local": string
  }
}
```

## Search Results Format

```json
[
  {
    "skill": "gaode-maps" | "google-maps" | "web-search",
    "type": "poi_search" | "place_detail" | "geocode",
    "url": string,
    "display_text": string
  }
]
```

## Optional Field Implementation

The `optional` field should be:
- `true` - POI is nice-to-have, skip if time-constrained
- `false` - POI is a core activity, should not be skipped
- Defaults to `false` if not specified

### Migration Strategy

For existing data without the `optional` field, infer from:
1. Explicit `optional` field (if present)
2. `- Optional` suffix in name (legacy pattern)
3. "optional" in notes_base/notes_local (as fallback)

## Example

```json
{
  "name_base": "Hongyadong Folk Culture District",
  "name_local": "洪崖洞民俗风貌区",
  "location_base": "Jialing River Binjiang Road 88",
  "location_local": "嘉陵江滨江路88号",
  "coordinates": {"lat": 29.562204, "lng": 106.579027},
  "cost": 0,
  "duration_minutes": 45,
  "type_local": "风景区",
  "notes_local": "火锅晚餐前可选择游览。",
  "time": {"start": "16:30", "end": "17:15"},
  "opening_hours": "All day",
  "currency_local": "CNY",
  "notes_base": "Optional evening visit before hotpot dinner.",
  "type_base": "Scenic Area",
  "optional": true
}
```
