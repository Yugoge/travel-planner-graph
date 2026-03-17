# Issue #3 Implementation Summary

**Issue**: Gaode Maps image search returns irrelevant results for Chongqing Day 1 POIs

**Root Cause**: Agent outputs use bilingual format `"English (中文)"` in single `name` field, but `name_chinese` field is empty. Script passed empty `chinese_name` to Gaode Maps, causing fallback to English search.

**Fix**: Extract Chinese names from parentheses using regex pattern that handles both formats.

---

## Changes Made

### 1. Added `_extract_chinese_name()` Method

**Location**: `scripts/fetch-images-batch.py` line 292-332

**Implementation**:
```python
def _extract_chinese_name(self, name: str) -> str:
    """Extract Chinese name from bilingual format"""
    import re

    # Find FIRST parenthesized content (handles multiple parentheses and trailing text)
    match = re.search(r'^(.+?)\s*\(([^)]+)\)', name)
    if not match:
        return ""

    before_paren = match.group(1).strip()
    inside_paren = match.group(2).strip()

    # Detect if text before parentheses contains Chinese characters
    has_chinese_before = bool(re.search(r'[\u4e00-\u9fff]', before_paren))

    if has_chinese_before:
        # Format 2: Chinese (English) - entertainment style
        return before_paren
    else:
        # Format 1: English (Chinese) - attractions style
        return inside_paren
```

**Handles Two Formats**:
- Format 1: `"English Name (中文名)"` → Returns `"中文名"`
- Format 2: `"中文名 (English Name)"` → Returns `"中文名"`

**Edge Cases**:
- Multiple parentheses: `"Name1 (中文1) & Name2 (中文2)"` → Returns `"中文1"` (first match)
- Trailing text: `"Name (中文) - Optional"` → Returns `"中文"` (ignores trailing)
- No parentheses: `"Just a Name"` → Returns `""` (empty string)

### 2. Updated POI Collection Logic

**Location**: `scripts/fetch-images-batch.py` lines 378, 393, 407, 421 (days format), 436, 451, 465, 479 (cities format)

**Before**:
```python
chinese_name = item.get("name_chinese", "")
```

**After**:
```python
chinese_name = item.get("name_chinese", "") or self._extract_chinese_name(name)
```

**Affected Sections**:
- Attractions (days format)
- Meals (days format)
- Accommodation (days format)
- Entertainment (days format)
- Attractions (cities format)
- Meals (cities format)
- Accommodation (cities format)
- Entertainment (cities format)

**Result**: All 8 POI collection points now extract Chinese names when `name_chinese` field is empty.

---

## Test Results

### Unit Tests

**Test Script**: `scripts/test-chinese-extraction.py`

All 8 test cases passed:
1. ✓ `'Raffles City Chongqing Observation Deck (来福士观景台)'` → `'来福士观景台'`
2. ✓ `'Huguang Guild Hall (湖广会馆)'` → `'湖广会馆'`
3. ✓ `'Xiayao Li (下浩里) & Longmenhao Old Street (龙门浩老街)'` → `'下浩里'`
4. ✓ `'Liziba Station (李子坝单轨穿楼) - Optional'` → `'李子坝单轨穿楼'`
5. ✓ `'Hongyadong (洪崖洞民俗风貌区) - Optional'` → `'洪崖洞民俗风貌区'`
6. ✓ `'Chengdu Taikoo Li (成都太古里)'` → `'成都太古里'`
7. ✓ `'Some Place Without Chinese'` → `''`
8. ✓ `''` → `''`

### Format Detection Tests

**Test Script**: `scripts/test-enhanced-extraction.py`

All 7 test cases passed:
- Format 1 (English → Chinese): 3 passed
- Format 2 (Chinese → Chinese): 2 passed
- Edge cases: 2 passed

### Integration Tests

**Test Script**: `scripts/verify-extraction-on-data.py`

Verified on actual Chongqing Day 1 data from `attractions.json`:
- 5/5 attractions correctly extracted Chinese names
- All extractions verified against expected values

**Test Script**: `scripts/test-complete-flow.py`

Simulated full POI collection flow:
- Loaded data from JSON
- Applied extraction logic
- Verified chinese_name passed to Gaode Maps
- All 5 POIs correctly extracted

---

## Git Rationale

**Root Cause Commit**: `3755270` - Added `chinese_name` routing but agents don't populate the field

**Why Issue Occurred**:
Commit 3755270 added `chinese_name` parameter to `fetch_poi_photo_gaode()` expecting agents to provide separate `name_chinese` field. However, agents output bilingual names in single `name` field as `'English (中文)'`, leaving `name_chinese` empty. Script tried to use `poi.get('chinese_name')` which returned empty string, causing fallback to full English name for Gaode search.

**How Fix Addresses Root**:
Extract Chinese text from parentheses in `name` field using regex. This works with current agent output format without requiring agent modifications. Gaode Maps now receives accurate Chinese names for mainland China POI searches.

---

## QA Validation Steps

1. Clear image cache for Chongqing POIs (remove `gaode_*` entries from `images.json`)
2. Run `fetch-images-batch.py` for `china-feb-15-mar-7-2026-20260202-195429` with limit 5
3. Verify Gaode Maps searches use Chinese names (来福士观景台, 湖广会馆, etc.)
4. Check fetched images are relevant to actual POIs
5. Verify Hong Kong/Macau still use Google Maps with English names

---

## Files Modified

1. `scripts/fetch-images-batch.py` - Added extraction method and updated POI collection
2. `scripts/test-chinese-extraction.py` - Unit tests for extraction
3. `scripts/test-enhanced-extraction.py` - Format detection tests
4. `scripts/verify-extraction-on-data.py` - Integration test with real data
5. `scripts/test-complete-flow.py` - End-to-end flow simulation

---

## Status

✅ **Implementation Complete**
✅ **All Tests Passing**
✅ **Ready for QA**

No blocking issues. No new permissions required.
