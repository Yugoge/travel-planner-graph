# Example: Extracting Detailed Travel Itinerary from RedNote

This example demonstrates extracting comprehensive travel information from a detailed RedNote guide post.

## Scenario

**User Request**:
"Found a popular 3-day Xi'an guide on RedNote, need to extract structured itinerary data"

**Requirements**:
- Extract day-by-day schedule
- Parse attraction details (cost, duration, tips)
- Extract restaurant recommendations
- Get practical travel tips
- Structure for integration with travel planner

## RedNote Post Details

**Post URL**: `https://www.xiaohongshu.com/explore/67c3d4e5f67890ab1`
**Title**: "西安3日游超详细攻略｜人均1500元全搞定"
**Engagement**: 45,623 likes, 2,341 comments
**Published**: 2026-01-18

## Step 1: Retrieve Full Content

```javascript
mcp__rednote__get_note_content({
  url: "https://www.xiaohongshu.com/explore/67c3d4e5f67890ab1"
})
```

## Step 2: Sample Response (Key Fields)

```json
{
  "note_id": "67c3d4e5f67890ab1",
  "title": "西安3日游超详细攻略｜人均1500元全搞定",
  "author": {"nickname": "旅行规划师Lily", "follower_count": 128934},
  "content": "...(full 3-day itinerary with timing, costs, tips)",
  "tags": ["西安旅游", "西安攻略", "3日游"],
  "likes": 45623,
  "published_time": "2026-01-18T09:30:00Z"
}
```

## Step 3: Extract Structured Data

Example parsed output structure:

```json
{
  "day": 1,
  "theme": "Historical and Cultural",
  "activities": [
    {
      "time": "08:00-12:00",
      "type": "attraction",
      "name_chinese": "兵马俑博物馆",
      "cost_cny": 120,
      "duration_minutes": 240,
      "tips": ["Hire guide for better experience", "Avoid weekends"]
    },
    {
      "time": "12:30-13:30",
      "type": "meal",
      "name_chinese": "老孙家羊肉泡馍",
      "cost_per_person_cny": 45
    }
  ],
  "total_cost_cny": 285
}
```

Example budget structure:

```json
{
  "total_budget_per_person_cny": 1450,
  "breakdown": {
    "accommodation": {"cost_cny": 600, "nights": 2},
    "attractions": {"cost_cny": 280},
    "meals": {"cost_cny": 420, "daily_average_cny": 140},
    "transportation": {"cost_cny": 150}
  }
}
```

## Extraction Workflow

1. Identify high-engagement guides (30k+ likes)
2. Use get_note_content to retrieve full content
3. Parse sections: budget, itinerary, attractions, restaurants, tips
4. Structure into JSON format
5. Validate costs and timing
6. Cross-reference with Gaode Maps
7. Extract warnings and practical tips

## Quality Indicators

High credibility signals: 45k+ likes, detailed costs, specific timing, honest warnings, recent publication, photos, practical tips.

---

**Pattern demonstrated**: Comprehensive travel guide content extraction and structuring
**Tools used**: `get_note_content`
**Output**: Fully structured multi-day itinerary with budget, tips, and warnings
