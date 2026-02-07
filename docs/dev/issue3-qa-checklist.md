# Issue #3 QA Validation Checklist

**Issue**: Gaode Maps receives English names, returns irrelevant Chongqing Day 1 POI images
**Fix**: Extract Chinese names from parentheses in bilingual format
**Status**: Implementation complete, ready for QA validation

---

## Pre-Validation Setup

### 1. Understand the Fix

**Before**:
```python
chinese_name = item.get("name_chinese", "")  # Always empty → Gaode uses English
```

**After**:
```python
chinese_name = item.get("name_chinese", "") or self._extract_chinese_name(name)
# Extracts "中文" from "English (中文)" → Gaode uses Chinese ✓
```

**Extraction Logic**:
- Pattern: `r'^(.+?)\s*\(([^)]+)\)'`
- Format 1: `"Raffles City Observation Deck (来福士观景台)"` → `"来福士观景台"`
- Format 2: `"静·serene SPA (Serene Thai SPA)"` → `"静·serene SPA"`
- Edge cases: Multiple parentheses, trailing text handled

### 2. Run Unit Tests

```bash
python3 scripts/test-chinese-extraction.py
python3 scripts/test-enhanced-extraction.py
python3 scripts/verify-extraction-on-data.py
python3 scripts/test-complete-flow.py
```

**Expected**: All tests pass with ✅

---

## Validation Steps

### Step 1: Backup Current Images Cache

```bash
cp data/china-feb-15-mar-7-2026-20260202-195429/images.json \
   data/china-feb-15-mar-7-2026-20260202-195429/images.json.backup
```

**Purpose**: Can restore if needed

---

### Step 2: Clear Chongqing POI Cache

**Manual edit** `data/china-feb-15-mar-7-2026-20260202-195429/images.json`:

Remove these entries from `"pois"` section:
```json
"gaode_Raffles City Chongqing Observation Deck (来福士观景台)": "...",
"gaode_Huguang Guild Hall (湖广会馆)": "...",
"gaode_Xiayao Li (下浩里) & Longmenhao Old Street (龙门浩老街)": "...",
"gaode_Liziba Station (李子坝单轨穿楼) - Optional": "...",
"gaode_Hongyadong (洪崖洞民俗风貌区) - Optional": "..."
```

**OR** use this command:
```bash
python3 -c "
import json
from pathlib import Path

file = Path('data/china-feb-15-mar-7-2026-20260202-195429/images.json')
data = json.loads(file.read_text())

# Remove Chongqing Day 1 POI cache entries
keys_to_remove = [k for k in data['pois'].keys() if k.startswith('gaode_') and any(
    poi in k for poi in ['Raffles City', 'Huguang', 'Xiayao', 'Liziba', 'Hongyadong']
)]

for key in keys_to_remove:
    print(f'Removing: {key}')
    del data['pois'][key]

file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
print(f'Cleared {len(keys_to_remove)} POI cache entries')
"
```

**Expected Output**: "Cleared 5 POI cache entries"

---

### Step 3: Re-fetch Chongqing Day 1 POI Images

```bash
cd /root/travel-planner
source venv/bin/activate
python3 scripts/fetch-images-batch.py china-feb-15-mar-7-2026-20260202-195429 1 5
```

**Monitor Output for These Lines**:
```
📍 Fetching POI photos (max 5)...
  Found XX POIs across all agent files
  Fetching 来福士观景台 (attraction, Gaode)... ✓
  Fetching 湖广会馆 (attraction, Gaode)... ✓
  Fetching 下浩里 (attraction, Gaode)... ✓
  Fetching 李子坝单轨穿楼 (attraction, Gaode)... ✓
  Fetching 洪崖洞民俗风貌区 (attraction, Gaode)... ✓
  Total fetched: 5/5
```

**CRITICAL CHECKS**:
- ✅ POI names should be IN CHINESE (来福士观景台, not "Raffles City...")
- ✅ Service should be "Gaode" (not Google)
- ✅ All 5 should show "✓" (success, not "✗")

**If you see English names**: Implementation failed, check code
**If you see "✗"**: Gaode API issue, not implementation issue

---

### Step 4: Verify Extracted Names in Cache

```bash
cat data/china-feb-15-mar-7-2026-20260202-195429/images.json | grep "gaode_" | grep -E "(来福士|湖广|下浩|李子坝|洪崖洞)"
```

**Expected Output** (5 entries with Chinese names):
```
"gaode_Raffles City Chongqing Observation Deck (来福士观景台)": "http://...",
"gaode_Huguang Guild Hall (湖广会馆)": "http://...",
"gaode_Xiayao Li (下浩里) & Longmenhao Old Street (龙门浩老街)": "http://...",
"gaode_Liziba Station (李子坝单轨穿楼) - Optional": "http://...",
"gaode_Hongyadong (洪崖洞民俗风貌区) - Optional": "http://..."
```

**CRITICAL**: Cache keys still use full name (for deduplication), but search used Chinese names

---

### Step 5: Validate Image Relevance

**Manual verification** - Open images.json and check URLs:

1. `gaode_Raffles City Chongqing Observation Deck (来福士观景台)`
   - **Should show**: Raffles City Chongqing observation deck/tower
   - **Should NOT show**: Random buildings, unrelated places

2. `gaode_Huguang Guild Hall (湖广会馆)`
   - **Should show**: Traditional Chinese guild hall, ornate architecture
   - **Should NOT show**: Modern buildings, unrelated sites

3. `gaode_Xiayao Li (下浩里) & Longmenhao Old Street (龙门浩老街)`
   - **Should show**: Historic street district, old buildings
   - **Should NOT show**: Modern areas, unrelated locations

4. `gaode_Liziba Station (李子坝单轨穿楼)`
   - **Should show**: Monorail passing through building
   - **Should NOT show**: Regular train stations, other buildings

5. `gaode_Hongyadong (洪崖洞民俗风貌区)`
   - **Should show**: Illuminated stilted buildings, riverside scenic area
   - **Should NOT show**: Caves, unrelated scenic spots

**Validation Method**: Open each URL in browser, verify image matches POI

---

### Step 6: Verify Hong Kong/Macau Unchanged

Check that Hong Kong/Macau POIs still use Google Maps with English names:

```bash
cat data/china-feb-15-mar-7-2026-20260202-195429/images.json | grep "google_" | head -5
```

**Expected**: Should see entries like `"google_Victoria Peak"`, `"google_Temple Street Night Market"`, etc.

**CRITICAL**: Hong Kong/Macau should use Google Maps, not Gaode

---

### Step 7: Compare Before/After Results

**Before Fix** (from user complaint):
- Images were "风牛马不相及的" (completely irrelevant)
- Gaode searched with English names
- No relevant POI photos returned

**After Fix** (from QA validation):
- All 5 POIs should have relevant images
- Gaode searched with Chinese names (来福士观景台, etc.)
- Images match actual POIs

**Success Criteria**:
- ✅ All 5 Chongqing Day 1 POIs have relevant images
- ✅ Gaode Maps searches used Chinese names (visible in logs)
- ✅ Hong Kong/Macau still use Google Maps
- ✅ No errors during image fetching

---

## Edge Case Testing (Optional but Recommended)

### Test 1: POI Without Parentheses

**Scenario**: If any POI has no parentheses (e.g., "Some Place")
**Expected**: Extraction returns empty string, Gaode uses full name
**Validation**: Check logs, should see full name used

### Test 2: Multiple Parentheses

**Scenario**: POI like "Name1 (中文1) & Name2 (中文2)"
**Expected**: Extracts first Chinese name "中文1"
**Validation**: Already covered in Day 1 - "Xiayao Li (下浩里) & Longmenhao Old Street (龙门浩老街)" → Should extract "下浩里"

### Test 3: Trailing Text After Parentheses

**Scenario**: POI like "Name (中文) - Optional"
**Expected**: Extracts "中文", ignores " - Optional"
**Validation**: Already covered in Day 1 - "Liziba Station (李子坝单轨穿楼) - Optional" → Should extract "李子坝单轨穿楼"

---

## Troubleshooting

### Issue: Still seeing English names in logs

**Cause**: Code not applied or cache not cleared
**Fix**:
1. Verify fetch-images-batch.py has _extract_chinese_name() method
2. Verify line 378 (and other POI collection points) use extraction
3. Clear cache completely and re-run

### Issue: Getting "✗" (failed fetches)

**Cause**: Gaode API issue, not implementation issue
**Check**:
1. Verify AMAP_API_KEY is set in .env
2. Check Gaode Maps skill script is working
3. Test with simple Chinese name manually

### Issue: Images still irrelevant

**Cause**: Extraction not working or wrong names extracted
**Check**:
1. Run test-complete-flow.py to see extracted names
2. Verify extraction logic matches Format 1 or Format 2
3. Check if POI name format is different than expected

---

## QA Sign-off Criteria

✅ **All unit tests pass**
✅ **All 5 Chongqing Day 1 POIs fetched successfully**
✅ **Gaode Maps searches used Chinese names (verified in logs)**
✅ **All 5 fetched images are relevant to actual POIs**
✅ **Hong Kong/Macau POIs still use Google Maps**
✅ **No errors or warnings during image fetching**
✅ **Cache entries created with correct format**

**If all criteria met**: Issue #3 RESOLVED ✅
**If any criteria failed**: Document failure, return to dev for fixes

---

## Expected Final State

**images.json should have**:
```json
{
  "pois": {
    "gaode_Raffles City Chongqing Observation Deck (来福士观景台)": "https://...",
    "gaode_Huguang Guild Hall (湖广会馆)": "https://...",
    "gaode_Xiayao Li (下浩里) & Longmenhao Old Street (龙门浩老街)": "https://...",
    "gaode_Liziba Station (李子坝单轨穿楼) - Optional": "https://...",
    "gaode_Hongyadong (洪崖洞民俗风貌区) - Optional": "https://..."
  }
}
```

**User complaint should be resolved**:
- Before: "为什么重庆第一天你搜的图片都很不准确？都是风牛马不相及的。"
- After: Accurate, relevant images for all Chongqing Day 1 POIs ✅

---

## QA Report Template

```
Issue #3 QA Validation Report

Date: [DATE]
QA Engineer: [NAME]

Test Results:
- Unit Tests: [PASS/FAIL]
- Image Re-fetch: [PASS/FAIL]
- Chinese Name Extraction: [PASS/FAIL]
- Image Relevance: [PASS/FAIL]
- HK/Macau Unchanged: [PASS/FAIL]

Issues Found:
[List any issues or NONE]

Recommendations:
[Any recommendations or NONE]

Sign-off: [APPROVED/REJECTED]
```

---

**QA Ready**: ✅ YES
**Dev Report**: docs/dev/dev-report-issue3-20260207-120927.json
