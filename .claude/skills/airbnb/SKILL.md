---
name: airbnb
description: Vacation rental search via Airbnb
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Airbnb Skill

Search vacation rentals with Airbnb data.

## How to Use

```bash
cd /root/travel-planner/.claude/skills/airbnb
python3 scripts/search.py "LOCATION" --checkin DATE --checkout DATE --adults N --min-price N
python3 scripts/details.py LISTING_ID --checkin DATE --checkout DATE
```

## Examples

**Search**:
```bash
python3 scripts/search.py "Austin, TX" --checkin 2026-06-15 --checkout 2026-06-22 --adults 2
```

**Details**:
```bash
python3 scripts/details.py 12345678 --checkin 2026-06-15 --checkout 2026-06-22 --adults 2
```

Returns JSON with amenities, pricing, policies, reviews.
