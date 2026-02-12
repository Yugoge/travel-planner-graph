# Image Fetch Fallback Status

**Last Updated**: 2026-02-12
**Script**: `scripts/fetch-images-batch.py`

---

## Fallback Chain

The image fetching system has a multi-tier fallback strategy:

### Tier 1: Primary Services (✅ Fully Working)

#### Gaode Maps (高德地图)
- **Usage**: Mainland China POIs (ISO2=CN detected by geopip)
- **Method**: Gaode Maps POI Search API
- **Success Rate**: ~97-99% for Chinese POIs
- **Image Quality**: Good, official POI photos

#### Google Maps
- **Usage**: International POIs (non-CN) or fallback when geopip fails
- **Method**: Google Places API
- **Success Rate**: ~90%+ globally
- **Image Quality**: Excellent, Google's extensive database

---

### Tier 2: Xiaohongshu Fallback (⚠️ Limited)

**Status**: Code implemented but **NOT functional** for image extraction

#### Implementation
- ✅ Search integration via `rednote-mcp`
- ✅ xvfb support for headless environment
- ✅ Note metadata extraction (title, author, link)
- ❌ **Image URL extraction** - NOT IMPLEMENTED

#### Limitations

**1. Data Format Issue**
- `rednote-mcp` returns text-only metadata
- Does NOT include image URLs in search results
- Would need additional `get_note_content` API calls

**2. Technical Complexity**
```
search_notes API → text metadata (title, author, link)
                ↓
get_note_content API → full content (timeout issues)
                ↓
parse HTML/JSON → extract images (unreliable)
```

**3. Environment Requirements**
- Requires xvfb (virtual display) - ✓ Available
- Requires valid cookie authentication - ✓ Available
- Requires Playwright browser - ✓ Installed

**4. Reliability Issues**
- `get_note_content` frequently times out (30s limit)
- Xiaohongshu may block automated requests
- Cookie expiration requires re-authentication

#### Current Behavior
```python
_xiaohongshu_search(search_name, city):
    → Searches Xiaohongshu notes
    → Extracts note URLs
    → Returns None (no image extraction)
```

---

### Tier 3: Bing Images Fallback (❌ Not Implemented)

**Status**: Placeholder only

#### Why Not Implemented

**Option 1**: Bing Image Search API
- ❌ Requires Azure subscription + API key
- ❌ Not free tier available
- ✅ Would provide reliable results

**Option 2**: Web Scraping
- ❌ Bing Images loads via JavaScript
- ❌ Requires browser automation (Selenium/Playwright)
- ❌ Unreliable and易被封禁

#### Current Behavior
```python
_bing_images_search(search_name, city):
    → Returns None immediately
    → Placeholder for future implementation
```

---

## Success Rates (china-feb-15-mar-7-2026 Plan)

```
Total POIs: 136

Primary Services:
  Gaode (CN):  135 (99.3%) ✅
  Google:      1   (0.7%)  ✅

Fallbacks:
  Xiaohongshu: 0   (0%)    ⚠️  (not functional)
  Bing Images: 0   (0%)    ❌ (not implemented)
```

**The 1 Google POI**: "Airport Quick Service" at Shanghai Pudong Airport
- Reason: geopip data boundary issue (coordinates not recognized)
- Not a bug: Google successfully found the image

---

## Recommendations

### Short Term (Keep Current System)
- ✅ 99.3% success rate is excellent
- ✅ Gaode + Google covers all practical use cases
- ✅ No additional APIs or costs needed

### Medium Term (If Higher Coverage Needed)

**Option 1**: Fix Xiaohongshu Fallback
1. Modify `rednote-mcp` or create custom scraper
2. Implement `get_note_content` with retry logic
3. Parse note HTML to extract image CDN URLs
4. **Estimated effort**: 4-8 hours
5. **Reliability**: Medium (depends on Xiaohongshu's anti-bot measures)

**Option 2**: Add Free Image API
- **Unsplash API** (free, 50 requests/hour)
  - Great for travel/landscape photos
  - Requires API key (free signup)
  - High quality images
- **Pixabay API** (free, 100 requests/minute)
  - Creative Commons images
  - Good for generic POI photos
  - Requires API key (free signup)

**Option 3**: Bing Image Search API
- **Cost**: ~$5-7 per 1000 queries
- **Quality**: Excellent
- **Requires**: Azure subscription

### Long Term

**Hybrid Approach**:
```
1. Gaode/Google (current) → 99%+ coverage
2. Unsplash/Pixabay API → Generic fallback for missing POIs
3. Manual curator for critical POIs → Perfect coverage
```

---

## Code Architecture

### Service Detection
```python
_map_service_for(city, poi_coordinates=None):
    if poi_coordinates:
        → Use POI's own coordinates (fixes multi-city bug)
    else:
        → Use city-level coordinates
    → geopip.search(lng, lat) → ISO2
    → CN → "gaode", else → "google"
```

### Fetch Flow
```python
fetch_poi_photo(poi_name, city, ...):
    1. Detect service (Gaode/Google)
    2. Try primary service
    3. If failed → Try Xiaohongshu (returns None currently)
    4. If failed → Try Bing (returns None - placeholder)
    5. Return photo_url or None
```

---

## Testing

### Test Xiaohongshu (Text Metadata Only)
```bash
cd .claude/skills/rednote/scripts
DISPLAY=:99 xvfb-run -a python search.py "重庆洪崖洞" --limit 1
```

**Expected Output**:
```json
{
  "status": "success",
  "data": "标题: ... 链接: https://www.xiaohongshu.com/explore/..."
}
```

**Note**: No image URLs in output!

### Test End-to-End
```bash
python scripts/fetch-images-batch.py <plan-name> 0 5 --force
```

---

## Conclusions

1. **Current system is excellent**: 99.3% success rate
2. **Xiaohongshu fallback**: Code exists but doesn't extract images
3. **Bing fallback**: Placeholder only
4. **No urgent need for improvement**: Primary services handle everything

If you need to improve coverage beyond 99.3%, consider Unsplash/Pixabay APIs (free, easy to integrate).
