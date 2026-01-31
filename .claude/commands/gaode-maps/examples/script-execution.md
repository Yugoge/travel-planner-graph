# Gaode Maps Script Execution Examples

Real-world examples of executing Gaode Maps Python scripts.

## 1. Geocoding Examples

### Convert Address to Coordinates

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/geocoding.py geocode "北京市朝阳区国贸"
```

**Expected Output**:
```json
{
  "formatted_address": "北京市朝阳区国贸",
  "location": {"lng": "116.459585", "lat": "39.910176"},
  "level": "POI"
}
```

### Reverse Geocoding (Coordinates to Address)

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/geocoding.py regeocode "104.065735,30.659462"
```

**Expected Output**:
```json
{
  "formatted_address": "四川省成都市锦江区红星路三段1号",
  "poi": "国际金融中心"
}
```

### IP Location Lookup

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/geocoding.py ip_location
```

**Expected Output**:
```json
{
  "city": "北京市",
  "adcode": "110000"
}
```

---

## 2. Routing Examples

### Driving Route (Beijing to Shanghai)

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/routing.py driving "北京市" "上海市" 0
```

**Expected Output**:
```json
{
  "route": {
    "distance": "1213420",
    "duration": "43685",
    "tolls": "455",
    "paths": [{...}]
  }
}
```

### Transit Route (Chongqing to Chengdu)

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/routing.py transit "重庆市" "成都市" "重庆" "成都" 0
```

**Expected Output**:
```json
{
  "route": {
    "transits": [{
      "duration": "8100",
      "cost": "154",
      "segments": [{"type": "railway", "name": "G8501", "departure_stop": "重庆北站", "arrival_stop": "成都东站"}]
    }]
  }
}
```

### Walking Route (Short Distance)

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/routing.py walking "重庆市渝中区解放碑" "重庆市渝中区洪崖洞"
```

**Expected Output**:
```json
{
  "route": {
    "distance": "1250",
    "duration": "900"
  }
}
```

---

## 3. POI Search Examples

### Keyword Search

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/poi_search.py keyword "火锅" "重庆" "050100" 10
```

**Returns**: `count`, `pois[]` with name/address/rating (352 results)

### Nearby Search

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/poi_search.py nearby "104.065735,30.659462" "餐厅" "" 500 10
```

**Returns**: `count`, `pois[]` with name/address/distance/rating (47 results)

### POI Detail Lookup

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/poi_search.py detail "B000A7BD6C"
```

**Returns**: name, address, tel, business_hours, rating

---

## 4. Utilities Examples

### Weather Forecast

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/utilities.py weather "成都" "all"
```

**Returns**: city, casts[] (4 days with date/weather/temps)

### Current Weather

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/utilities.py weather "成都" "base"
```

**Returns**: city, weather, temperature, humidity

### Distance Measurement

```bash
# Driving distance
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/utilities.py distance "116.481488,39.990464" "121.473701,31.230416" 1

# Straight-line distance
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/utilities.py distance "116.481488,39.990464" "121.473701,31.230416" 0
```

**Returns**: distance, duration (if driving), formatted values

---

## Error Handling Examples

### Invalid Address

```bash
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/geocoding.py geocode "xyzabc123notreal"
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
source /root/.claude/venv/bin/activate && python3 .claude/commands/gaode-maps/scripts/geocoding.py regeocode "999,999"
```

**Output**:
```
Error: Invalid coordinates: out of China service area
```

**Exit Code**: 1

---

## Integration Notes

**Bash Tool**: Execute scripts and parse JSON stdout

**Script Help**: Run without arguments for usage information

**API Key Override**: Set `AMAP_MAPS_API_KEY` environment variable (defaults to project key)
