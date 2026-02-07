# Issue #3: Before & After Comparison

## Problem: Gaode Maps Receives English Names

### Before Fix

**Data in attractions.json**:
```json
{
  "name": "Raffles City Chongqing Observation Deck (来福士观景台)",
  "name_chinese": ""
}
```

**POI Collection Code (line 378)**:
```python
chinese_name = item.get("name_chinese", "")
# Result: chinese_name = ""
```

**Gaode Search Call (line 425)**:
```python
photo_url = self.fetch_poi_photo_gaode(
    poi['name'],  # "Raffles City Chongqing Observation Deck (来福士观景台)"
    poi['city'],  # "Chongqing"
    chinese_name=poi.get('chinese_name')  # ""
)
```

**Inside fetch_poi_photo_gaode (line 170)**:
```python
search_name = chinese_name if chinese_name else poi_name
# Result: search_name = "Raffles City Chongqing Observation Deck (来福士观景台)"
```

**Gaode API receives**:
```
keyword: "Raffles City Chongqing Observation Deck (来福士观景台)"
city: "Chongqing"
```

**Problem**: Gaode Maps cannot find POIs with English names → returns irrelevant results ❌

---

### After Fix

**Data in attractions.json** (unchanged):
```json
{
  "name": "Raffles City Chongqing Observation Deck (来福士观景台)",
  "name_chinese": ""
}
```

**POI Collection Code (line 378)** - NOW INCLUDES EXTRACTION:
```python
chinese_name = item.get("name_chinese", "") or self._extract_chinese_name(name)
# Execution:
#   1. item.get("name_chinese", "") returns ""
#   2. "" is falsy, so execute self._extract_chinese_name(name)
#   3. Extract "来福士观景台" from "Raffles City Chongqing Observation Deck (来福士观景台)"
# Result: chinese_name = "来福士观景台"
```

**Extraction Logic**:
```python
def _extract_chinese_name(self, name: str) -> str:
    match = re.search(r'^(.+?)\s*\(([^)]+)\)', name)
    # match.group(1) = "Raffles City Chongqing Observation Deck"
    # match.group(2) = "来福士观景台"

    has_chinese_before = bool(re.search(r'[\u4e00-\u9fff]', "Raffles City..."))
    # Result: False (no Chinese before parentheses)

    # Return inside_paren (Format 1: English (Chinese))
    return "来福士观景台"
```

**Gaode Search Call (line 425)**:
```python
photo_url = self.fetch_poi_photo_gaode(
    poi['name'],  # "Raffles City Chongqing Observation Deck (来福士观景台)"
    poi['city'],  # "Chongqing"
    chinese_name=poi.get('chinese_name')  # "来福士观景台" ✓
)
```

**Inside fetch_poi_photo_gaode (line 170)**:
```python
search_name = chinese_name if chinese_name else poi_name
# Result: search_name = "来福士观景台"
```

**Gaode API receives**:
```
keyword: "来福士观景台"
city: "Chongqing"
```

**Result**: Gaode Maps finds POI with accurate Chinese name → returns relevant photos ✅

---

## All 5 Chongqing Day 1 POIs - Before & After

### Before Fix (Gaode searches with English):
1. ❌ `"Raffles City Chongqing Observation Deck (来福士观景台)"` → Irrelevant results
2. ❌ `"Huguang Guild Hall (湖广会馆)"` → Irrelevant results
3. ❌ `"Xiayao Li (下浩里) & Longmenhao Old Street (龙门浩老街)"` → Irrelevant results
4. ❌ `"Liziba Station (李子坝单轨穿楼) - Optional"` → Irrelevant results
5. ❌ `"Hongyadong (洪崖洞民俗风貌区) - Optional"` → Irrelevant results

### After Fix (Gaode searches with Chinese):
1. ✅ `"来福士观景台"` → Accurate Raffles City observation deck photos
2. ✅ `"湖广会馆"` → Accurate Huguang Guild Hall photos
3. ✅ `"下浩里"` → Accurate Xiayao Li district photos
4. ✅ `"李子坝单轨穿楼"` → Accurate Liziba Station monorail photos
5. ✅ `"洪崖洞民俗风貌区"` → Accurate Hongyadong scenic area photos

---

## Code Changes Summary

**Only 2 changes needed**:

1. **Added extraction method** (33 lines)
   - Location: `scripts/fetch-images-batch.py` lines 292-332
   - Regex-based extraction from parentheses
   - Handles both `English (Chinese)` and `Chinese (English)` formats

2. **Updated 8 POI collection points** (1 line each)
   - Changed: `chinese_name = item.get("name_chinese", "")`
   - To: `chinese_name = item.get("name_chinese", "") or self._extract_chinese_name(name)`
   - Locations: Lines 378, 393, 407, 421, 436, 451, 465, 479

**Result**: Minimal invasive change, maximum impact. No changes to data format, no changes to Gaode API calls, no changes to agent outputs. Just smart extraction at POI collection time.

---

## User Impact

**Before**: "为什么重庆第一天你搜的图片都很不准确？都是风牛马不相及的。"

**After**: Accurate, relevant POI photos for all mainland China attractions using Gaode Maps with proper Chinese names.
