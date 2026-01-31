# Example: Finding Hidden Attractions in Chengdu

This example demonstrates using RedNote to discover authentic local attractions beyond typical tourist sites.

## Scenario

**User Request**:
"Planning 2 days in Chengdu, want to see pandas but also explore local spots that aren't too touristy"

**Requirements**:
- Mix of famous and hidden attractions
- Local perspective on what's worth visiting
- Budget-friendly options
- Practical visiting tips from recent travelers

## Step-by-Step Workflow

### Step 1: Search for Popular Attractions

**Search for must-visit spots**:

```javascript
mcp__rednote__search_notes({
  keyword: "成都必去景点",
  page: 1,
  sort_type: "popularity_descending"
})
```

**Sample Response Analysis**:
```json
{
  "notes": [
    {
      "note_id": "65a1b2c3d4e5f6789",
      "title": "成都必去的10个景点！本地人良心推荐",
      "url": "https://www.xiaohongshu.com/explore/65a1b2c3d4e5f6789",
      "likes": 15234,
      "comments": 892,
      "description": "在成都生活5年，这些地方真的值得去...",
      "author": {
        "nickname": "成都小王子",
        "verified": false
      },
      "cover_image": "https://...",
      "note_type": "image"
    },
    {
      "note_id": "65b2c3d4e5f67890a",
      "title": "成都3日游保姆级攻略｜人均1000元",
      "url": "https://www.xiaohongshu.com/explore/65b2c3d4e5f67890a",
      "likes": 8943,
      "comments": 456,
      "description": "刚从成都回来，超详细攻略分享..."
    }
  ]
}
```

**Insights**:
- First post has 15k+ likes (high credibility signal)
- Author claims local perspective (5 years in Chengdu)
- Second post is budget-focused (aligns with user preferences)

### Step 2: Search for Hidden Gems

**Search for off-the-beaten-path locations**:

```javascript
mcp__rednote__search_notes({
  keyword: "成都小众景点",
  sort_type: "popularity_descending"
})
```

**Sample Response**:
```json
{
  "notes": [
    {
      "note_id": "65c3d4e5f67890ab1",
      "title": "成都小众景点合集｜人少景美拍照绝",
      "url": "https://www.xiaohongshu.com/explore/65c3d4e5f67890ab1",
      "likes": 4521,
      "comments": 234,
      "description": "这些地方本地人都不一定知道！拍照超出片..."
    }
  ]
}
```

### Step 3: Get Detailed Content from Top Posts

**Retrieve full content from most promising post**:

```javascript
mcp__rednote__get_note_by_url({
  note_url: "https://www.xiaohongshu.com/explore/65a1b2c3d4e5f6789"
})
```

**Sample Detailed Response**:
```json
{
  "note_id": "65a1b2c3d4e5f6789",
  "title": "成都必去的10个景点！本地人良心推荐",
  "content": "📍1. 成都大熊猫繁育研究基地\n时间：早上8点到达最佳（看熊猫吃早餐）\n门票：55元\n建议游玩：3小时\n\n📍2. 人民公园\n免费！本地人最爱的公园\n喝茶、掏耳朵体验地道成都慢生活\n建议游玩：2小时\n\n📍3. 东郊记忆（小众）\n工业风艺术园区，拍照圣地\n免费参观\n建议游玩：1.5小时\n\n📍4. 玉林路（本地推荐）\n小酒馆原址，夜生活好去处\n晚上去最有氛围\n消费：人均100-200元\n\n📍5. 宽窄巷子\n必打卡，但商业化严重\n适合拍照，不建议买东西（贵）\n建议游玩：1小时\n\n...",
  "images": [
    {
      "url": "https://ci.xiaohongshu.com/熊猫基地照片.jpg",
      "description": "熊猫宝宝太可爱了"
    },
    {
      "url": "https://ci.xiaohongshu.com/人民公园茶馆.jpg",
      "description": "人民公园鹤鸣茶社"
    }
  ],
  "location": {
    "name": "成都",
    "latitude": 30.572269,
    "longitude": 104.066541
  },
  "tags": ["成都旅游", "成都攻略", "必去景点", "本地推荐"],
  "likes": 15234,
  "comments_count": 892,
  "shares": 3421,
  "published_time": "2026-01-15T14:23:00Z"
}
```

### Step 4: Extract Structured Data

**Parse content into structured attraction data**:

```json
{
  "attractions_from_rednote": [
    {
      "name": "Chengdu Research Base of Giant Panda Breeding",
      "name_chinese": "成都大熊猫繁育研究基地",
      "type": "Wildlife/Nature",
      "cost_cny": 55,
      "duration_minutes": 180,
      "best_time": "8:00 AM (feeding time)",
      "notes": "Arrive early to see pandas at breakfast - most active time. Very popular.",
      "recommendation_source": "Must-visit (15k+ likes)",
      "verified_via": "rednote_high_engagement"
    },
    {
      "name": "People's Park",
      "name_chinese": "人民公园",
      "type": "Park/Cultural",
      "cost_cny": 0,
      "duration_minutes": 120,
      "notes": "Free entry. Experience local life: tea culture, ear cleaning service. Authentic Chengdu slow living.",
      "recommendation_source": "Local favorite",
      "verified_via": "rednote_local_recommendation"
    },
    {
      "name": "Eastern Suburb Memory",
      "name_chinese": "东郊记忆",
      "type": "Art District",
      "cost_cny": 0,
      "duration_minutes": 90,
      "notes": "Industrial art park, excellent photography spot. Hidden gem with free entry.",
      "recommendation_source": "Hidden gem (local insight)",
      "verified_via": "rednote_hidden_gem_tag"
    },
    {
      "name": "Yulin Road",
      "name_chinese": "玉林路",
      "type": "Nightlife District",
      "cost_cny": 150,
      "duration_minutes": 180,
      "notes": "Famous from song 'Chengdu'. Best visited at night for bars and atmosphere. Budget ¥100-200 per person.",
      "recommendation_source": "Local nightlife hotspot",
      "verified_via": "rednote_local_recommendation"
    },
    {
      "name": "Kuanzhai Alley",
      "name_chinese": "宽窄巷子",
      "type": "Historical/Commercial",
      "cost_cny": 0,
      "duration_minutes": 60,
      "notes": "Tourist area - good for photos but overpriced shopping. Limit time to 1 hour.",
      "recommendation_source": "Tourist spot (with warning)",
      "verified_via": "rednote_honest_review"
    }
  ]
}
```

### Step 5: Cross-Reference with Additional Searches

**Search for recent panda base tips**:

```javascript
mcp__rednote__search_notes({
  keyword: "成都熊猫基地攻略",
  sort_type: "time_descending"
})
```

**Search for photo spots**:

```javascript
mcp__rednote__search_notes({
  keyword: "成都拍照圣地",
  sort_type: "popularity_descending"
})
```

**Benefits of multiple searches**:
- Validate information across sources
- Get time-sensitive updates (recent posts may note closures, renovations)
- Discover additional hidden spots
- Find seasonal considerations

### Step 6: Verify Locations with Gaode Maps

**After collecting RedNote recommendations, verify with Gaode Maps**:

```javascript
// Load Gaode Maps POI search
mcp__plugin_amap-maps_amap-maps__poi_search_keyword({
  keywords: "成都大熊猫繁育研究基地",
  city: "成都"
})
```

**Cross-check**:
- Exact address and coordinates
- Current operating hours
- Official ticket prices
- Public transport access
- Distance from accommodation

### Step 7: Final Recommendations

**Day 1: Famous + Hidden Mix**
1. **Morning (8:00-11:00)**: Panda Base
   - Source: RedNote + Gaode Maps verified
   - Cost: ¥55, Duration: 3 hours
   - Tip: Arrive at 8 AM for feeding time

2. **Afternoon (14:00-16:00)**: People's Park + Tea Experience
   - Source: RedNote local recommendation
   - Cost: ¥30-50 (tea), Duration: 2 hours
   - Tip: Try ear cleaning for authentic experience

3. **Evening (19:00-22:00)**: Yulin Road Nightlife
   - Source: RedNote nightlife guide
   - Cost: ¥100-200, Duration: 3 hours
   - Tip: Visit Small Tavern (小酒馆) original location

**Day 2: Hidden Gems Focus**
1. **Morning (10:00-11:30)**: Eastern Suburb Memory
   - Source: RedNote hidden gem list
   - Cost: Free, Duration: 1.5 hours
   - Tip: Industrial photography spot

2. **Afternoon (13:00-14:00)**: Kuanzhai Alley
   - Source: RedNote (with warning)
   - Cost: Free entry, Duration: 1 hour
   - Tip: Photos only, skip shopping (overpriced)

3. **Evening**: Additional exploration based on interests

## Key Takeaways

1. **High engagement = credibility**: Posts with 10k+ likes are usually reliable
2. **Local perspective matters**: "本地人推荐" (local recommendation) tags add value
3. **Honest warnings**: Good posts note tourist traps and overpriced areas
4. **Verify independently**: Always cross-check with maps and official sources
5. **Recent content**: Sort by time for latest conditions and updates
6. **Visual inspiration**: Use images to set expectations and plan photos

## Workflow Pattern (Reusable)

```markdown
1. Search broad topic: "城市名 + 必去景点"
2. Search hidden gems: "城市名 + 小众景点"
3. Identify high-engagement posts (5k+ likes)
4. Extract URLs from top 3-5 results
5. Use get_note_by_url for detailed content
6. Parse structured data from note content
7. Cross-reference with Gaode Maps for verification
8. Cross-search for specific attractions/activities
9. Compile final recommendations with sources noted
10. Include warnings and practical tips from posts
```

## Data Quality Checks

**Before trusting RedNote content**:
- ✅ Check likes (>5k = high confidence)
- ✅ Check comments (100+ indicates discussion/validation)
- ✅ Check post date (prefer <6 months old)
- ✅ Look for specific details (prices, hours, addresses)
- ✅ Compare 3+ sources for consensus
- ✅ Verify with official maps or websites
- ❌ Avoid single-source recommendations
- ❌ Skip posts with no engagement
- ❌ Ignore outdated content (>1 year old for travel)

---

**Pattern demonstrated**: Multi-source UGC travel content aggregation and verification
**Tools used**: `search_notes`, `get_note_by_url`, Gaode Maps verification
**Output**: Structured attraction recommendations with authenticity and practicality balance
