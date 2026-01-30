---
name: yelp
description: Restaurant search using Yelp Fusion AI MCP
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Yelp Skill

Search restaurants with ratings, reviews, pricing using Yelp Fusion AI.

## How to Use

```bash
cd /root/travel-planner/.claude/skills/yelp
python3 scripts/search.py search "QUERY" "LOCATION" --price=LEVEL --limit=N
python3 scripts/details.py BUSINESS_ID
```

## Examples

**Search**:
```bash
python3 scripts/search.py search "italian restaurants" "San Francisco, CA" --price=2,3 --limit=10
```

**Details**:
```bash
python3 scripts/details.py gary-danko-san-francisco
```

Returns JSON with ratings, reviews, pricing, hours, location.
