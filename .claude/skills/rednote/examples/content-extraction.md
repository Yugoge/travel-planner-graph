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

## Step 2: Sample Response

```json
{
  "note_id": "67c3d4e5f67890ab1",
  "title": "西安3日游超详细攻略｜人均1500元全搞定",
  "author": {
    "nickname": "旅行规划师Lily",
    "user_id": "5a1b2c3d4e5f6",
    "verified": false,
    "follower_count": 128934
  },
  "content": "刚从西安回来，3天2夜玩得超满足！分享我的详细行程~\n\n💰 总花费：¥1450/人\n- 住宿：¥600（2晚，钟楼附近民宿）\n- 门票：¥280\n- 餐饮：¥420\n- 交通：¥150\n\n📅 Day 1：历史文化深度游\n\n🌅 早上 (8:00-12:00)\n📍 兵马俑博物馆\n🎫 门票：¥120/人\n⏰ 游览时间：4小时\n🚌 交通：地铁1号线→纺织城站转307路公交\n💡 Tips：\n  - 一定要请讲解员（¥150团队讲解可拼）\n  - 1号坑最震撼，要多留时间\n  - 避开周末人会少很多\n  - 带水和零食，景区贵\n\n🍜 午餐 (12:30-13:30)\n📍 老孙家羊肉泡馍（火车站店）\n💰 人均：¥45\n⭐ 必点：羊肉泡馍、凉皮\n💡 Tips：自己掰馍更入味，掰成黄豆大小\n\n🌆 下午 (14:30-18:00)\n📍 陕西历史博物馆\n🎫 门票：免费（需提前预约）\n⏰ 游览时间：3小时\n🚌 交通：公交5路/30路\n💡 Tips：\n  - 提前3天官网预约\n  - 请讲解或租导览器\n  - 何家村窖藏文物必看\n  - 周一闭馆！\n\n🍜 晚餐 (18:30-20:00)\n📍 德发长饺子馆\n💰 人均：¥60\n⭐ 必点：饺子宴、biangbiang面\n\n🌙 晚上 (20:30-22:00)\n📍 钟鼓楼夜景\n🎫 门票：¥50（联票）\n⏰ 游览时间：1.5小时\n💡 Tips：\n  - 夜景更美\n  - 鼓楼每天6场表演\n  - 周边回民街晚上很热闹\n\n📅 Day 2：古城墙+美食探索\n\n🌅 早上 (8:00-12:00)\n📍 西安城墙（南门）\n🎫 门票：¥54/人\n⏰ 游览时间：3-4小时\n🚴 骑行租车：¥45/人（双人自行车¥90）\n💡 Tips：\n  - 早上8点开门，人少风景好\n  - 骑行一圈13.7公里，2-3小时\n  - 带防晒！城墙上无遮挡\n  - 南门拍照最好看\n\n🍜 午餐 (12:30-13:30)\n📍 樊记腊汁肉夹馍（竹笆市店）\n💰 人均：¥20\n⭐ 必点：肉夹馍、凉皮、冰峰汽水\n💡 Tips：\n  - 本地人都吃这家\n  - 中午排队但速度快\n  - 肉夹馍要"肥瘦"最香\n\n🌆 下午 (14:00-17:00)\n📍 大雁塔+大唐不夜城\n🎫 门票：¥50（登塔另收费¥30）\n⏰ 游览时间：3小时\n💡 Tips：\n  - 大雁塔广场免费\n  - 音乐喷泉每天12:00和21:00\n  - 不夜城晚上更漂亮，下午先逛大雁塔\n\n🍜 晚餐 (18:00-19:30)\n📍 长安大排档\n💰 人均：¥80\n⭐ 必点：葫芦鸡、毛笔酥、油泼面\n💡 Tips：\n  - 网红餐厅，需要排号\n  - 下午5点半开始取号\n  - 环境好拍照好看\n\n🌙 晚上 (20:00-22:00)\n📍 大唐不夜城夜景\n🎫 门票：免费\n💡 Tips：\n  - 不倒翁小姐姐表演20:30-21:30\n  - 灯光秀每晚20:00\n  - 周末人超多\n\n📅 Day 3：回民街+城市漫步\n\n🌅 早上 (9:00-11:00)\n📍 回民街美食探索\n💰 预算：¥50-80\n⭐ 必吃：\n  - 贾三灌汤包（¥28/笼）\n  - 红柳烤肉（¥10/串）\n  - 镜糕（¥5）\n  - 甑糕（¥8）\n  - 酸梅汤（¥8）\n💡 Tips：\n  - 深入小巷，别在主街买（贵且不正宗）\n  - 洒金桥最地道\n  - 上午10点前人少\n\n🌆 中午 (11:30-13:00)\n📍 永兴坊（非遗美食街区）\n💰 人均：¥40\n⭐ 必吃：摔碗酒、陕西各地小吃\n💡 Tips：比回民街人少，小吃品种更全\n\n🛫 下午 (14:00-)\n返程或自由活动\n\n---\n\n💡 实用Tips汇总：\n\n🏨 住宿建议：\n- 钟楼/鼓楼附近最方便\n- 地铁2号线沿线都可以\n- 提前订省钱（我住的¥300/晚的民宿）\n\n🚇 交通建议：\n- 办长安通卡或用支付宝乘车码\n- 地铁覆盖主要景点\n- 打车不贵，市区内20-30元\n\n📱 必备App：\n- 高德地图（导航）\n- 大众点评（找美食）\n- 携程/美团（订票）\n- 陕西历史博物馆官方预约\n\n🎫 门票预订：\n- 兵马俑：现场买或携程提前订\n- 陕博：必须提前3天官网预约\n- 城墙/钟鼓楼：现场或美团\n\n⚠️ 避雷提示：\n- 回民街主街：价格贵，味道一般\n- 火车站拉客：不要相信一日游，多是坑\n- 假兵马俑：在临潼，不要上当\n- 钟楼周边：商业化严重，购物慎重\n\n🎒 行李建议：\n- 春秋：轻薄外套+长袖\n- 夏季：防晒霜、遮阳帽、墨镜必备\n- 冬季：羽绒服，城墙上风大\n- 充电宝、舒适的鞋（走路多）\n\n💰 省钱小技巧：\n- 学生证半价（很多景点）\n- 美团团购餐厅优惠\n- 地铁+公交比打车省很多\n- 回民街深入小巷价格便宜\n- 住青旅或民宿比酒店便宜\n\n❓ 常见问题：\n\nQ: 3天够吗？\nA: 够玩主要景点，想深度游建议4-5天\n\nQ: 什么季节最好？\nA: 春季(3-5月)和秋季(9-11月)最舒适\n\nQ: 适合带小孩吗？\nA: 适合，但兵马俑和博物馆可能无聊，可以少安排点\n\nQ: 要买联票吗？\nA: 钟鼓楼联票划算，其他单独买即可\n\n---\n\n如果有帮助记得点赞收藏哦💖 有问题评论区见~",

  "images": [
    {
      "url": "https://ci.xiaohongshu.com/兵马俑1号坑.jpg",
      "description": "兵马俑1号坑全景"
    },
    {
      "url": "https://ci.xiaohongshu.com/城墙骑行.jpg",
      "description": "西安城墙骑行"
    },
    {
      "url": "https://ci.xiaohongshu.com/大唐不夜城.jpg",
      "description": "大唐不夜城夜景"
    },
    {
      "url": "https://ci.xiaohongshu.com/回民街美食.jpg",
      "description": "回民街小吃合集"
    },
    {
      "url": "https://ci.xiaohongshu.com/羊肉泡馍.jpg",
      "description": "正宗羊肉泡馍"
    }
  ],

  "location": {
    "name": "西安",
    "latitude": 34.341568,
    "longitude": 108.939645
  },

  "tags": ["西安旅游", "西安攻略", "3日游", "省钱攻略", "美食推荐"],

  "likes": 45623,
  "comments_count": 2341,
  "shares": 8934,
  "published_time": "2026-01-18T09:30:00Z"
}
```

## Step 3: Extract Structured Itinerary

### Day 1: Historical and Cultural

```json
{
  "day": 1,
  "theme": "Historical and Cultural Deep Dive",
  "activities": [
    {
      "time": "08:00-12:00",
      "type": "attraction",
      "name": "Terracotta Warriors Museum",
      "name_chinese": "兵马俑博物馆",
      "duration_minutes": 240,
      "cost_cny": 120,
      "cost_additional": {
        "guide": 150,
        "note": "Team guide can be shared"
      },
      "transport": {
        "method": "Metro Line 1 to Fangzhicheng + Bus 307",
        "cost_cny": 10
      },
      "tips": [
        "Hire guide (¥150 for team, can share)",
        "Hall 1 most impressive, allocate more time",
        "Avoid weekends for fewer crowds",
        "Bring water and snacks (expensive inside)"
      ],
      "priority": "must-visit"
    },
    {
      "time": "12:30-13:30",
      "type": "meal",
      "meal_type": "lunch",
      "name": "Lao Sun Jia Lamb Paomo",
      "name_chinese": "老孙家羊肉泡馍（火车站店）",
      "cost_per_person_cny": 45,
      "specialty_dishes": ["Lamb Paomo", "Liangpi (cold noodles)"],
      "tips": [
        "Break bread yourself for better flavor",
        "Break into soybean-sized pieces"
      ]
    },
    {
      "time": "14:30-18:00",
      "type": "attraction",
      "name": "Shaanxi History Museum",
      "name_chinese": "陕西历史博物馆",
      "duration_minutes": 180,
      "cost_cny": 0,
      "reservation": {
        "required": true,
        "advance_days": 3,
        "method": "Official website"
      },
      "transport": {
        "method": "Bus 5 or 30",
        "cost_cny": 2
      },
      "tips": [
        "Book 3 days in advance on official website",
        "Hire guide or rent audio device",
        "Hejiacun Hoard artifacts are must-see",
        "Closed on Mondays!"
      ],
      "priority": "must-visit",
      "closed": ["Monday"]
    },
    {
      "time": "18:30-20:00",
      "type": "meal",
      "meal_type": "dinner",
      "name": "Defachang Dumpling Restaurant",
      "name_chinese": "德发长饺子馆",
      "cost_per_person_cny": 60,
      "specialty_dishes": ["Dumpling Banquet", "Biangbiang Noodles"]
    },
    {
      "time": "20:30-22:00",
      "type": "attraction",
      "name": "Bell and Drum Tower Night View",
      "name_chinese": "钟鼓楼夜景",
      "duration_minutes": 90,
      "cost_cny": 50,
      "ticket_note": "Combined ticket",
      "tips": [
        "Night view is more beautiful",
        "Drum tower has 6 daily performances",
        "Nearby Muslim Quarter is lively at night"
      ],
      "best_time": "evening"
    }
  ],
  "total_cost_cny": 285,
  "total_duration_hours": 11.5
}
```

### Day 2: City Wall and Food Exploration

```json
{
  "day": 2,
  "theme": "Ancient City Wall and Food Exploration",
  "activities": [
    {
      "time": "08:00-12:00",
      "type": "attraction",
      "name": "Xi'an City Wall (South Gate)",
      "name_chinese": "西安城墙（南门）",
      "duration_minutes": 240,
      "cost_cny": 54,
      "cost_additional": {
        "bike_rental_single": 45,
        "bike_rental_tandem": 90
      },
      "tips": [
        "Opens at 8 AM, fewer people and good scenery",
        "Bike circuit is 13.7km, takes 2-3 hours",
        "Bring sunscreen! No shade on wall",
        "South Gate has best photo opportunities"
      ],
      "activities_available": ["Cycling", "Walking", "Photography"],
      "priority": "must-visit"
    },
    {
      "time": "12:30-13:30",
      "type": "meal",
      "meal_type": "lunch",
      "name": "Fan Ji Roujiamo",
      "name_chinese": "樊记腊汁肉夹馍（竹笆市店）",
      "cost_per_person_cny": 20,
      "specialty_dishes": [
        "Roujiamo (Chinese burger)",
        "Liangpi",
        "Bingfeng Soda"
      ],
      "tips": [
        "Locals' favorite",
        "Queue at lunch but fast service",
        "Order 'fat and lean' for best flavor"
      ],
      "recommendation_level": "local_favorite"
    },
    {
      "time": "14:00-17:00",
      "type": "attraction",
      "name": "Giant Wild Goose Pagoda + Tang Dynasty Street",
      "name_chinese": "大雁塔+大唐不夜城",
      "duration_minutes": 180,
      "cost_cny": 50,
      "cost_additional": {
        "climb_pagoda": 30
      },
      "tips": [
        "Square is free",
        "Music fountain at 12:00 and 21:00 daily",
        "Tang Street more beautiful at night, visit pagoda in afternoon"
      ],
      "priority": "recommended"
    },
    {
      "time": "18:00-19:30",
      "type": "meal",
      "meal_type": "dinner",
      "name": "Chang'an Da Pai Dang",
      "name_chinese": "长安大排档",
      "cost_per_person_cny": 80,
      "specialty_dishes": [
        "Calabash Chicken (葫芦鸡)",
        "Brush Crisp (毛笔酥)",
        "Oil-Splashed Noodles (油泼面)"
      ],
      "tips": [
        "Popular restaurant, need queue number",
        "Start taking numbers at 5:30 PM",
        "Nice ambiance and photo-worthy"
      ],
      "reservation": {
        "required": false,
        "queue_system": true,
        "queue_start_time": "17:30"
      }
    },
    {
      "time": "20:00-22:00",
      "type": "attraction",
      "name": "Tang Dynasty Street Night View",
      "name_chinese": "大唐不夜城夜景",
      "duration_minutes": 120,
      "cost_cny": 0,
      "tips": [
        "Tumbler Miss performance 20:30-21:30",
        "Light show nightly at 20:00",
        "Very crowded on weekends"
      ],
      "best_time": "evening",
      "performances": [
        {
          "name": "Tumbler Miss",
          "time": "20:30-21:30"
        },
        {
          "name": "Light Show",
          "time": "20:00"
        }
      ]
    }
  ],
  "total_cost_cny": 249,
  "total_duration_hours": 12
}
```

### Day 3: Muslim Quarter and Departure

```json
{
  "day": 3,
  "theme": "Food Exploration and City Wandering",
  "activities": [
    {
      "time": "09:00-11:00",
      "type": "food_exploration",
      "name": "Muslim Quarter Food Tour",
      "name_chinese": "回民街美食探索",
      "duration_minutes": 120,
      "cost_cny": 65,
      "must_try_foods": [
        {
          "name": "Jia San Steamed Buns",
          "name_chinese": "贾三灌汤包",
          "cost_cny": 28
        },
        {
          "name": "Red Willow BBQ Skewers",
          "name_chinese": "红柳烤肉",
          "cost_cny": 10
        },
        {
          "name": "Mirror Cake",
          "name_chinese": "镜糕",
          "cost_cny": 5
        },
        {
          "name": "Zeng Cake",
          "name_chinese": "甑糕",
          "cost_cny": 8
        },
        {
          "name": "Sour Plum Drink",
          "name_chinese": "酸梅汤",
          "cost_cny": 8
        }
      ],
      "tips": [
        "Go deep into alleys, avoid main street (expensive and less authentic)",
        "Sajinqiao area most authentic",
        "Visit before 10 AM for fewer crowds"
      ],
      "priority": "must-visit"
    },
    {
      "time": "11:30-13:00",
      "type": "attraction",
      "name": "Yongxing Lane (Intangible Heritage Food District)",
      "name_chinese": "永兴坊（非遗美食街区）",
      "duration_minutes": 90,
      "cost_per_person_cny": 40,
      "specialty": "Bowl-Smashing Wine, Shaanxi Regional Snacks",
      "tips": [
        "Less crowded than Muslim Quarter",
        "More variety of Shaanxi snacks",
        "Good alternative food street"
      ]
    },
    {
      "time": "14:00",
      "type": "departure",
      "name": "Return Trip or Free Time"
    }
  ],
  "total_cost_cny": 105,
  "total_duration_hours": 4
}
```

## Step 4: Extract Budget Breakdown

```json
{
  "total_budget_per_person_cny": 1450,
  "breakdown": {
    "accommodation": {
      "cost_cny": 600,
      "nights": 2,
      "cost_per_night_cny": 300,
      "location": "Near Bell Tower",
      "type": "Guesthouse/Hostel"
    },
    "attractions": {
      "cost_cny": 280,
      "items": [
        "Terracotta Warriors: ¥120",
        "City Wall: ¥54",
        "Bell Tower + Drum Tower: ¥50",
        "Giant Wild Goose Pagoda: ¥50",
        "Guide tip: ¥150 (shared)"
      ]
    },
    "meals": {
      "cost_cny": 420,
      "daily_average_cny": 140,
      "budget_level": "mid-range"
    },
    "transportation": {
      "cost_cny": 150,
      "includes": [
        "Metro/bus passes",
        "Airport transfer",
        "Bike rental",
        "Occasional taxi"
      ]
    }
  }
}
```

## Step 5: Extract Practical Tips

```json
{
  "accommodation_tips": [
    "Stay near Bell Tower/Drum Tower for convenience",
    "Along Metro Line 2 is also good",
    "Book in advance to save money (¥300/night guesthouse)"
  ],
  "transportation_tips": [
    "Get Chang'an Tong card or use Alipay transit code",
    "Metro covers main attractions",
    "Taxis affordable, ¥20-30 within city"
  ],
  "essential_apps": [
    "Gaode Maps (navigation)",
    "Dianping (restaurant discovery)",
    "Ctrip/Meituan (ticket booking)",
    "Shaanxi History Museum (official reservation)"
  ],
  "ticket_booking": {
    "terracotta_warriors": "On-site or Ctrip advance booking",
    "shaanxi_museum": "Must book 3 days in advance on official site",
    "city_wall_bell_drum": "On-site or Meituan"
  },
  "scam_warnings": [
    "Muslim Quarter main street: Expensive, mediocre quality",
    "Train station touts: Don't trust one-day tours, mostly scams",
    "Fake Terracotta Warriors: Located in Lintong, avoid scam",
    "Bell Tower area: Highly commercialized, shop carefully"
  ],
  "packing_suggestions": {
    "spring_autumn": "Light jacket + long sleeves",
    "summer": "Sunscreen, sun hat, sunglasses essential",
    "winter": "Down jacket, city wall is windy",
    "always": "Power bank, comfortable shoes (lots of walking)"
  },
  "money_saving_tips": [
    "Student ID gets half price at many attractions",
    "Meituan group buying for restaurant discounts",
    "Metro + bus much cheaper than taxis",
    "Muslim Quarter: Go to side alleys for better prices",
    "Stay at hostels or guesthouses instead of hotels"
  ]
}
```

## Key Takeaways

1. **Comprehensive content**: High-quality RedNote guides contain complete itineraries with timing, costs, and tips
2. **Practical details**: Real prices, exact locations, operating hours from actual travelers
3. **Honest warnings**: Good posts include scam alerts and quality warnings
4. **Budget transparency**: Detailed cost breakdowns help planning
5. **Visual reference**: Photos validate recommendations and set expectations
6. **Community validation**: High engagement (45k+ likes) indicates trustworthy content

## Extraction Workflow Pattern

```markdown
1. Identify high-engagement comprehensive guides (30k+ likes)
2. Use get_note_content to retrieve full content
3. Parse content sections:
   - Budget breakdown
   - Day-by-day itinerary
   - Attraction details (cost, duration, tips)
   - Restaurant recommendations
   - Practical tips and warnings
4. Structure data into JSON format
5. Validate costs and times for reasonableness
6. Cross-reference locations with Gaode Maps
7. Note reservation requirements and booking methods
8. Extract scam warnings and practical tips
9. Create final structured itinerary
10. Note content source and engagement for credibility tracking
```

## Data Quality Assessment

**This guide scores high on credibility**:
- ✅ 45k+ likes (very high engagement)
- ✅ Detailed cost breakdown (transparent)
- ✅ Specific prices and timing (actionable)
- ✅ Honest warnings about tourist traps
- ✅ Recent publication (Jan 2026)
- ✅ Multiple photos validating experiences
- ✅ Practical tips section (transportation, apps, packing)
- ✅ FAQ addressing common questions

**Integration ready**: Data can be directly structured into travel planner JSON format for attractions, meals, and daily schedules.

---

**Pattern demonstrated**: Comprehensive travel guide content extraction and structuring
**Tools used**: `get_note_content`
**Output**: Fully structured multi-day itinerary with budget, tips, and warnings
