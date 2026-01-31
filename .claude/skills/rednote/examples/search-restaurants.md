# Example: Discovering Authentic Restaurants in Shanghai

This example demonstrates using RedNote to find local restaurants beyond tourist guides.

## Scenario

**User Request**:
"Looking for authentic Shanghai cuisine for 3-day trip, want local favorites not tourist traps"

**Requirements**:
- Authentic Shanghai/Chinese cuisine
- Local recommendations (not just TripAdvisor top lists)
- Mix of budget and mid-range options
- Practical info: operating hours, specialties, prices

## Step-by-Step Workflow

### Step 1: Search for Local Food Recommendations

**Search with local-focused keywords**:

```javascript
mcp__rednote__search_notes({
  keywords: "上海本地人推荐美食",
  sort_type: "popularity_descending"
})
```

**Sample Response**:
```json
{
  "notes": [
    {
      "note_id": "66a1b2c3d4e5f6789",
      "title": "上海本地人才知道的20家小店｜人均50以下",
      "url": "https://www.xiaohongshu.com/explore/66a1b2c3d4e5f6789",
      "likes": 28934,
      "comments": 1823,
      "description": "在上海15年，这些店是真的好吃不贵...",
      "author": {
        "nickname": "上海阿姨的美食日记",
        "verified": false
      }
    },
    {
      "note_id": "66b2c3d4e5f67890a",
      "title": "上海老字号餐厅测评｜踩雷vs推荐",
      "url": "https://www.xiaohongshu.com/explore/66b2c3d4e5f67890a",
      "likes": 12456,
      "comments": 678
    }
  ]
}
```

**Insights**:
- First post: 28k+ likes, author claims 15 years local experience
- Budget-friendly focus (¥50 per person)
- Second post: Honest reviews including "failures" (more credible)

### Step 2: Search for Specific Shanghai Cuisine

**Search for Shanghai specialties**:

```javascript
mcp__rednote__search_notes({
  keywords: "上海生煎包推荐",
  sort_type: "popularity_descending"
})
```

```javascript
mcp__rednote__search_notes({
  keywords: "上海本帮菜哪家好",
  sort_type: "popularity_descending"
})
```

```javascript
mcp__rednote__search_notes({
  keywords: "上海小笼包必吃",
  sort_type: "popularity_descending"
})
```

**Searches target**:
- 生煎包 (sheng jian bao): pan-fried pork buns (Shanghai specialty)
- 本帮菜 (ben bang cai): authentic Shanghai cuisine
- 小笼包 (xiao long bao): soup dumplings

### Step 3: Get Detailed Content from Top Restaurant Guide

**Retrieve comprehensive guide**:

```javascript
mcp__rednote__get_note_content({
  url: "https://www.xiaohongshu.com/explore/66a1b2c3d4e5f6789"
})
```

**Sample Detailed Response**:
```json
{
  "note_id": "66a1b2c3d4e5f6789",
  "title": "上海本地人才知道的20家小店｜人均50以下",
  "content": "🍜 早餐必吃：\n\n1️⃣ 大壶春（四川北路店）\n📍 地址：四川北路650号\n💰 人均：¥30\n⭐ 必点：生煎包（¥12/4个）、虾仁馄饨（¥15）\n⏰ 营业时间：6:30-13:00\n💡 Tips：早上7-8点高峰期要排队，建议6:30开门就去\n\n2️⃣ 小杨生煎（吴江路店）\n📍 地址：吴江路269号\n💰 人均：¥25\n⭐ 必点：鲜肉生煎（¥10/4个）\n⏰ 营业时间：7:00-21:00\n💡 Tips：下午3-5点人少，不用排队\n\n🥘 午餐/晚餐：\n\n3️⃣ 老吉士酒家\n📍 地址：云南南路46号\n💰 人均：¥80\n⭐ 必点：红烧肉、响油鳝丝、糟钵头\n⏰ 营业时间：11:00-14:00, 17:00-21:00\n💡 Tips：本帮菜老字号，晚餐需要预订\n\n4️⃣ 阿娘面（黄河路店）\n📍 地址：黄河路90号\n💰 人均：¥35\n⭐ 必点：辣肉面、大排面、葱油拌面\n⏰ 营业时间：10:30-20:30\n💡 Tips：面量很大，女生建议点小碗\n\n5️⃣ 沧浪亭（静安寺店）\n📍 地址：南京西路1728号\n💰 人均：¥120\n⭐ 必点：松鼠桂鱼、蟹粉豆腐、碧螺虾仁\n⏰ 营业时间：11:00-22:00\n💡 Tips：苏州菜馆，环境好适合商务宴请\n\n...",
  "images": [
    {
      "url": "https://ci.xiaohongshu.com/大壶春生煎.jpg",
      "description": "大壶春的生煎包，底部焦脆"
    },
    {
      "url": "https://ci.xiaohongshu.com/老吉士红烧肉.jpg",
      "description": "老吉士红烧肉，入口即化"
    }
  ],
  "tags": ["上海美食", "本地推荐", "小店", "性价比"],
  "likes": 28934,
  "published_time": "2026-01-20T10:15:00Z"
}
```

### Step 4: Parse Restaurant Data

**Extract structured information**:

```json
{
  "breakfast_options": [
    {
      "name": "Da Hu Chun (Sichuan North Road)",
      "name_chinese": "大壶春（四川北路店）",
      "address": "650 Sichuan North Road",
      "address_chinese": "四川北路650号",
      "cost_per_person_cny": 30,
      "specialty_dishes": [
        "Sheng Jian Bao (¥12/4 pieces)",
        "Shrimp Wonton Soup (¥15)"
      ],
      "hours": "6:30 AM - 1:00 PM",
      "tips": "Peak hours 7-8 AM, arrive at 6:30 opening to avoid queue",
      "cuisine_type": "Shanghai Breakfast",
      "source": "RedNote local guide (28k likes)",
      "recommendation_level": "Must-try"
    },
    {
      "name": "Xiao Yang Sheng Jian (Wujiang Road)",
      "name_chinese": "小杨生煎（吴江路店）",
      "address": "269 Wujiang Road",
      "address_chinese": "吴江路269号",
      "cost_per_person_cny": 25,
      "specialty_dishes": [
        "Pork Sheng Jian Bao (¥10/4 pieces)"
      ],
      "hours": "7:00 AM - 9:00 PM",
      "tips": "Fewer crowds 3-5 PM",
      "cuisine_type": "Shanghai Breakfast/Snacks",
      "source": "RedNote local guide",
      "recommendation_level": "Recommended"
    }
  ],
  "lunch_dinner_options": [
    {
      "name": "Lao Ji Shi Restaurant",
      "name_chinese": "老吉士酒家",
      "address": "46 Yunnan South Road",
      "address_chinese": "云南南路46号",
      "cost_per_person_cny": 80,
      "specialty_dishes": [
        "Braised Pork Belly (红烧肉)",
        "Fried Eel with Sizzling Oil (响油鳝丝)",
        "Zao Bo Tou (糟钵头)"
      ],
      "hours": "11:00 AM - 2:00 PM, 5:00 PM - 9:00 PM",
      "tips": "Traditional Shanghai cuisine, dinner requires reservation",
      "cuisine_type": "Ben Bang Cai (Shanghai Cuisine)",
      "source": "RedNote local guide",
      "recommendation_level": "Must-try (old establishment)",
      "reservation_required": true
    },
    {
      "name": "A Niang Noodles (Huanghe Road)",
      "name_chinese": "阿娘面（黄河路店）",
      "address": "90 Huanghe Road",
      "address_chinese": "黄河路90号",
      "cost_per_person_cny": 35,
      "specialty_dishes": [
        "Spicy Pork Noodles (辣肉面)",
        "Pork Chop Noodles (大排面)",
        "Scallion Oil Noodles (葱油拌面)"
      ],
      "hours": "10:30 AM - 8:30 PM",
      "tips": "Large portions, women should order small bowl",
      "cuisine_type": "Shanghai Noodles",
      "source": "RedNote local guide",
      "recommendation_level": "Recommended (budget-friendly)"
    }
  ]
}
```

### Step 5: Verify with Gaode Maps

**Cross-check restaurant locations and details**:

```javascript
mcp__plugin_amap-maps_amap-maps__poi_search_keyword({
  keywords: "大壶春 四川北路",
  city: "上海",
  types: "050000"
})
```

**Verification checklist**:
- ✅ Exact address and coordinates
- ✅ Current business status (open/closed)
- ✅ Phone number for reservations
- ✅ User ratings and review count
- ✅ Distance from accommodation
- ✅ Transit access

### Step 6: Search for Recent Reviews

**Get latest updates on specific restaurant**:

```javascript
mcp__rednote__search_notes({
  keywords: "大壶春生煎 2026",
  sort_type: "time_descending"
})
```

**Check for**:
- Recent closures or relocations
- Price changes
- Quality changes (management/chef changes)
- Wait time updates
- New menu items

### Step 7: Create Meal Plan

**Day 1**
- **Breakfast (7:00 AM)**: Da Hu Chun - Sheng Jian Bao
  - Cost: ¥30, Duration: 45 min
  - Arrive early to avoid queue

- **Lunch (12:00 PM)**: A Niang Noodles - Shanghai Noodles
  - Cost: ¥35, Duration: 1 hour
  - Near shopping area, convenient

- **Dinner (6:30 PM)**: Lao Ji Shi - Traditional Shanghai Cuisine
  - Cost: ¥80, Duration: 2 hours
  - Reservation made, authentic local flavors

**Day 2**
- **Breakfast (8:00 AM)**: Xiao Yang Sheng Jian - Pan-fried Buns
  - Cost: ¥25, Duration: 30 min
  - Different style from Day 1

- **Lunch (1:00 PM)**: (Search for seafood/hotpot via RedNote)

- **Dinner (7:00 PM)**: (Search for special occasion restaurant)

**Day 3**
- **Breakfast**: Hotel or near attractions
- **Lunch**: Street food/market exploration
- **Dinner**: Airport area (if departing)

## Key Takeaways

1. **Local keywords matter**: "本地人推荐" (local recommendation) filters out tourist traps
2. **Specific dishes**: Search by dish name (生煎包, 小笼包) for specialist restaurants
3. **Practical details**: RedNote posts often include exact prices, hours, wait times
4. **Visual verification**: Photos show actual food quality and portion sizes
5. **Recent content crucial**: Restaurant quality can change, prefer posts <3 months old
6. **Cross-verification**: Always confirm with Gaode Maps for current status

## Search Pattern Templates

**Budget food search**:
```
"城市名 + 美食 + 人均XX以下"
"城市名 + 本地人推荐 + 小店"
"城市名 + 性价比美食"
```

**Specific cuisine search**:
```
"城市名 + 菜系名 + 推荐"
"城市名 + 特色菜 + 哪家好"
"城市名 + 老字号餐厅"
```

**Dish-specific search**:
```
"城市名 + 菜品名 + 最好吃"
"城市名 + 菜品名 + 必吃"
"菜品名 + 城市名 + 排名"
```

## Quality Signals in RedNote Food Posts

**High credibility indicators**:
- ✅ Author mentions years living in city
- ✅ Specific prices and addresses included
- ✅ Photos of actual food (not stock images)
- ✅ Honest reviews (mentions both pros and cons)
- ✅ Practical tips (timing, ordering, reservations)
- ✅ Multiple dishes photographed and described
- ✅ High engagement (10k+ likes for major cities)

**Red flags**:
- ❌ Generic descriptions without specifics
- ❌ Only exterior/interior photos (no food)
- ❌ Overly promotional language
- ❌ No price information
- ❌ Stock/professional photography only
- ❌ All positive (no caveats or warnings)

## Workflow Pattern (Reusable)

```markdown
1. Search broad: "城市名 + 本地人推荐美食"
2. Search specific: "城市名 + 菜品名 + 推荐"
3. Identify high-engagement guides (20k+ likes)
4. Extract top 5-10 restaurant recommendations
5. Get detailed content via get_note_content
6. Parse structured data (name, address, cost, specialties)
7. Verify with Gaode Maps (location, hours, status)
8. Search recent updates for each restaurant
9. Create daily meal plan with variety
10. Note reservations needed and timing tips
```

---

**Pattern demonstrated**: Authentic local restaurant discovery through UGC aggregation
**Tools used**: `search_notes`, `get_note_content`, Gaode Maps verification
**Output**: Structured meal plan with authentic local restaurants and practical details
