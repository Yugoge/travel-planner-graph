# Gaode Maps Script Execution Examples

Real-world examples of executing Gaode Maps Python scripts.

## 1. Geocoding Examples

### Convert Address to Coordinates

```bash
python3 .claude/commands/gaode-maps/scripts/geocoding.py geocode "北京市朝阳区国贸"
```

**Expected Output**:
```json
{
  "formatted_address": "北京市朝阳区国贸",
  "province": "北京市",
  "city": [],
  "district": "朝阳区",
  "location": {
    "lng": "116.459585",
    "lat": "39.910176"
  },
  "level": "POI"
}
```

### Reverse Geocoding (Coordinates to Address)

```bash
python3 .claude/commands/gaode-maps/scripts/geocoding.py regeocode "104.065735,30.659462"
```

**Expected Output**:
```json
{
  "formatted_address": "四川省成都市锦江区红星路三段1号",
  "province": "四川省",
  "city": "成都市",
  "district": "锦江区",
  "street": "红星路三段",
  "poi": "国际金融中心"
}
```

### IP Location Lookup

```bash
python3 .claude/commands/gaode-maps/scripts/geocoding.py ip_location
```

**Expected Output**:
```json
{
  "province": "北京市",
  "city": "北京市",
  "adcode": "110000",
  "rectangle": "116.0119343,39.66127144;116.7829835,40.2164962"
}
```

---

## 2. Routing Examples

### Driving Route (Beijing to Shanghai)

```bash
python3 .claude/commands/gaode-maps/scripts/routing.py driving "北京市" "上海市" 0
```

**Expected Output**:
```json
{
  "route": {
    "distance": "1213420",
    "duration": "43685",
    "tolls": "455",
    "traffic_lights": "87",
    "paths": [
      {
        "distance": "1213.4 km",
        "duration": "12h 8m",
        "tolls": "455 CNY",
        "steps": [...]
      }
    ]
  }
}
```

### Transit Route (Chongqing to Chengdu)

```bash
python3 .claude/commands/gaode-maps/scripts/routing.py transit "重庆市" "成都市" "重庆" "成都" 0
```

**Expected Output**:
```json
{
  "route": {
    "transits": [
      {
        "duration": "8100",
        "cost": "154",
        "segments": [
          {
            "type": "railway",
            "name": "G8501",
            "departure_stop": "重庆北站",
            "arrival_stop": "成都东站",
            "duration": "7200",
            "cost": "154"
          }
        ]
      }
    ]
  }
}
```

### Walking Route (Short Distance)

```bash
python3 .claude/commands/gaode-maps/scripts/routing.py walking "重庆市渝中区解放碑" "重庆市渝中区洪崖洞"
```

**Expected Output**:
```json
{
  "route": {
    "distance": "1250",
    "duration": "900",
    "paths": [
      {
        "distance": "1.25 km",
        "duration": "15m",
        "steps": [...]
      }
    ]
  }
}
```

---

## 3. POI Search Examples

### Keyword Search (Hotpot Restaurants in Chongqing)

```bash
python3 .claude/commands/gaode-maps/scripts/poi_search.py keyword "火锅" "重庆" "050100" 10
```

**Expected Output**:
```json
{
  "count": "352",
  "pois": [
    {
      "id": "B000A7BD6C",
      "name": "德庄火锅",
      "type": "餐饮服务;中餐厅;火锅店",
      "address": "解放碑步行街",
      "location": {
        "lng": "106.577143",
        "lat": "29.555958"
      },
      "tel": "023-63845678",
      "rating": "4.6"
    },
    ...
  ]
}
```

### Nearby Search (Restaurants within 500m)

```bash
python3 .claude/commands/gaode-maps/scripts/poi_search.py nearby "104.065735,30.659462" "餐厅" "" 500 10
```

**Expected Output**:
```json
{
  "count": "47",
  "pois": [
    {
      "id": "B001B0JH8K",
      "name": "蜀大侠火锅",
      "type": "餐饮服务;中餐厅;火锅店",
      "address": "红星路三段1号IFS",
      "location": {
        "lng": "104.066289",
        "lat": "30.660134"
      },
      "distance": "85",
      "rating": "4.5"
    },
    ...
  ]
}
```

### POI Detail Lookup

```bash
python3 .claude/commands/gaode-maps/scripts/poi_search.py detail "B000A7BD6C"
```

**Expected Output**:
```json
{
  "id": "B000A7BD6C",
  "name": "德庄火锅(解放碑店)",
  "type": "餐饮服务;中餐厅;火锅店",
  "address": "重庆市渝中区解放碑步行街88号",
  "location": {
    "lng": "106.577143",
    "lat": "29.555958"
  },
  "tel": "023-63845678",
  "website": "http://www.dezhuang.com",
  "business_hours": "10:00-22:00",
  "rating": "4.6",
  "photos": [...]
}
```

---

## 4. Utilities Examples

### Weather Forecast (Chengdu 4-day Forecast)

```bash
python3 .claude/commands/gaode-maps/scripts/utilities.py weather "成都" "all"
```

**Expected Output**:
```json
{
  "city": "成都市",
  "province": "四川",
  "casts": [
    {
      "date": "2026-01-30",
      "dayweather": "多云",
      "nightweather": "阴",
      "daytemp": "12",
      "nighttemp": "6",
      "daywind": "西北",
      "nightwind": "西北",
      "daypower": "≤3",
      "nightpower": "≤3"
    },
    {
      "date": "2026-01-31",
      "dayweather": "小雨",
      "nightweather": "小雨",
      "daytemp": "10",
      "nighttemp": "7"
    },
    ...
  ]
}
```

### Current Weather

```bash
python3 .claude/commands/gaode-maps/scripts/utilities.py weather "成都" "base"
```

**Expected Output**:
```json
{
  "city": "成都市",
  "weather": "多云",
  "temperature": "11",
  "winddirection": "西北",
  "windpower": "≤3",
  "humidity": "68",
  "reporttime": "2026-01-30 13:45:00"
}
```

### Distance Measurement (Beijing to Shanghai Driving)

```bash
python3 .claude/commands/gaode-maps/scripts/utilities.py distance "116.481488,39.990464" "121.473701,31.230416" 1
```

**Expected Output**:
```json
{
  "origin": "116.481488,39.990464",
  "destination": "121.473701,31.230416",
  "distance": "1213420",
  "duration": "43685",
  "formatted": {
    "distance": "1213.4 km",
    "duration": "12h 8m"
  }
}
```

### Straight-Line Distance

```bash
python3 .claude/commands/gaode-maps/scripts/utilities.py distance "116.481488,39.990464" "121.473701,31.230416" 0
```

**Expected Output**:
```json
{
  "origin": "116.481488,39.990464",
  "destination": "121.473701,31.230416",
  "distance": "1067890",
  "formatted": {
    "distance": "1067.9 km"
  }
}
```

---

## Error Handling Examples

### Invalid Address

```bash
python3 .claude/commands/gaode-maps/scripts/geocoding.py geocode "xyzabc123notreal"
```

**Output**:
```
Error: MCP error: No results found for address
```

**Exit Code**: 1

### Rate Limit (Automatic Retry)

If you hit rate limits, scripts automatically retry with exponential backoff:

```
Attempt 1 failed: Rate limit exceeded (429)
Retrying in 2 seconds...
Attempt 2 failed: Rate limit exceeded (429)
Retrying in 4 seconds...
Attempt 3 succeeded
```

### Invalid Coordinates

```bash
python3 .claude/commands/gaode-maps/scripts/geocoding.py regeocode "999,999"
```

**Output**:
```
Error: Invalid coordinates: out of China service area
```

**Exit Code**: 1

---

## Integration with Bash Tool

Agents should execute scripts via Bash tool:

```javascript
// In agent code
const result = await bash({
  command: 'python3 .claude/commands/gaode-maps/scripts/routing.py transit "重庆市" "成都市" "重庆" "成都"',
  description: 'Get transit route from Chongqing to Chengdu'
});

const data = JSON.parse(result.stdout);
console.log(`Duration: ${data.route.transits[0].duration}s`);
console.log(`Cost: ${data.route.transits[0].cost} CNY`);
```

---

## Script Help

All scripts provide usage information when called without arguments:

```bash
python3 .claude/commands/gaode-maps/scripts/geocoding.py
```

**Output**:
```
Usage:
  geocoding.py geocode <address> [city]
  geocoding.py regeocode <longitude,latitude> [radius]
  geocoding.py ip_location [ip_address]
```

---

## Environment Variable Override

Use your own API key:

```bash
export AMAP_MAPS_API_KEY="your_key_here"
python3 .claude/commands/gaode-maps/scripts/geocoding.py geocode "北京市"
```

If `AMAP_MAPS_API_KEY` is not set, scripts default to project key: `99e97af6fd426ce3cfc45d22d26e78e3`
