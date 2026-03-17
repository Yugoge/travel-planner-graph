---
description: "Decision tree and rules for POI classification across domains"
---

# POI Classification Rules

## Decision Tree

```
POI Type?
├─ Food/Beverage
│  ├─ Restaurant → meals.json
│  ├─ Cafe/Tea House → meals.json
│  └─ Food Market → meals.json
│
├─ Sightseeing
│  ├─ Historical Site → attractions.json
│  ├─ Natural Landmark → attractions.json
│  ├─ Monument/Museum → attractions.json
│  └─ Scenic Area → attractions.json
│
├─ Entertainment
│  ├─ Theme Park → entertainment.json
│  ├─ Cinema → entertainment.json
│  ├─ Theater/Show → entertainment.json
│  ├─ Nightclub/Bar → entertainment.json
│  ├─ Spa/Massage → entertainment.json
│  └─ Game Center → entertainment.json
│
└─ Shopping
   ├─ Shopping Mall → shopping.json
   ├─ Specialty Store → shopping.json
   ├─ Market/Bazaar → shopping.json
   └─ Brand Store → shopping.json
```

## Classification Criteria

**Attractions.json**:
- Sightseeing appeal is PRIMARY value
- Educational or historical significance
- Natural beauty or iconic landmarks
- Typical visit: 1-3 hours, daytime

**Meals.json**:
- Primary purpose is eating/drinking
- Restaurant, cafe, food market, tea house
- Any establishment focusing on food service
- Typical visit: 0.5-2 hours, meal times

**Entertainment.json**:
- Primarily for entertainment/leisure
- Activity-based (games, shows, sports)
- Social venues (clubs, bars)
- Wellness venues (spa, massage)
- Typical visit: 1-4 hours, flexible times

**Shopping.json**:
- Retail focus: buying goods/services
- Shopping malls, markets, stores
- Brand-specific or specialty shops
- Typical visit: 1-3 hours, flexible times

## Bilingual Annotation Requirements

All proper nouns must include annotations:

**Format**: `"Romanized/Translated Name (原文)"`

**Examples**:
- Chinese: `"Qu Nanshan Yeqing Huoguo Gongyuan (去南山夜景火锅公园)"`
- Japanese: `"Fushimi Inari Shrine (伏見稲荷大社)"`
- Korean: `"Gyeongbokgung Palace (경복궁)"`

**Apply to**:
- Restaurant names
- Attraction names
- Venue names (entertainment, shopping)
- Street/area names (if not standardized)

**NOT for**:
- Common nouns ("restaurant", "temple", "market")
- Standardized place names ("Beijing", "Tokyo")
- International brands ("Starbucks", "McDonald's")

## Edge Cases

**Hybrid Venues** (restaurant + entertainment):
→ Primary purpose determines classification
→ If equal, choose based on time allocation in itinerary

**Hotel/Accommodation Attached Facilities**:
→ Classify separately (restaurant → meals, spa → entertainment)
→ Not in accommodation.json

**Tourist Markets with Food**:
→ If primarily shopping: shopping.json
→ If primarily food vendors: meals.json

## Validation

After classification, verify:
1. Proper nouns have bilingual annotations
2. Opening hours are valid
3. Address is complete
4. Rating/review data is authentic
5. No duplicates across domains
