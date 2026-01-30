---
name: tripadvisor
description: Attractions, tours, activities using TripAdvisor data
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# TripAdvisor Skill

Access attraction data, tours, activities, reviews from TripAdvisor.

## How to Use

```bash
cd /root/travel-planner/.claude/skills/tripadvisor
python3 scripts/attractions.py search "LOCATION" --category TYPE --min-rating N
python3 scripts/tours.py search "LOCATION" --category TYPE --time TIME
```

## Examples

**Attractions**:
```bash
python3 scripts/attractions.py search "Paris, France" --category museums --min-rating 4.0
```

**Tours**:
```bash
python3 scripts/tours.py search "Paris, France" --category food-tours --time evening
```

Returns JSON with ratings, pricing, hours, booking info.
