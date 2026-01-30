---
name: jinko-hotel
description: Hotel search with 2M+ properties worldwide
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Jinko Hotel Skill

Search hotels worldwide with real-time pricing and availability.

## How to Use

```bash
cd /root/travel-planner/.claude/skills/jinko-hotel
python3 scripts/search.py search LOCATION CHECKIN CHECKOUT ADULTS ROOMS MIN_PRICE MAX_PRICE MIN_RATING
python3 scripts/details.py details HOTEL_ID
python3 scripts/booking.py availability HOTEL_ID CHECKIN CHECKOUT ADULTS ROOMS
```

## Examples

**Search**:
```bash
python3 scripts/search.py search 'Beijing' '2026-02-15' '2026-02-17' 2 1 200 500 4.0
```

**Details**:
```bash
python3 scripts/details.py details 'hotel_12345'
```

Returns JSON with pricing, availability, facilities, ratings.
