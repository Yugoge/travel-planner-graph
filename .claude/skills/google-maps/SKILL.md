---
name: google-maps
description: Search places, compute routes, and lookup weather using Google Maps Grounding Lite MCP
allowed-tools: [Bash, Read]
model: inherit
user-invocable: true
---

# Google Maps Skill

International mapping and location services using Google Maps Grounding Lite MCP.

## How to Use

Execute scripts from skill directory:
```bash
cd /root/travel-planner/.claude/skills/google-maps
python3 scripts/<category>.py <arguments>
```

Available scripts:
- `scripts/places.py` - Place search
- `scripts/routing.py` - Route computation  
- `scripts/weather.py` - Weather lookup

## Quick Examples

**Place Search**:
```bash
python3 scripts/places.py "restaurants in Paris" 10
```

**Route Computation**:
```bash
python3 scripts/routing.py "New York, NY" "Boston, MA" TRANSIT
```

**Weather Lookup**:
```bash
python3 scripts/weather.py "Tokyo, Japan"
```

All scripts return JSON output.
