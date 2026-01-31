# Travel Planner

Travel planning application with MCP skill integrations for accommodations, flights, maps, and travel information.

**Last structural update**: 2026-01-31

---

## Overview

This project provides a comprehensive travel planning system with:
- MCP skill integrations for external travel APIs (Airbnb, Duffel Flights, Google Maps, Gaode Maps, RedNote)
- Structured JSON data storage for trip plans
- Validation and generation scripts for quality assurance
- Interactive HTML generation for trip visualization

**Architecture**: Script-based MCP communication (no context pollution) with progressive disclosure pattern.

---

## Structure

### Core Directories

- **.claude/** - Claude Code configuration
  - `skills/` (7 MCP integrations) - Airbnb, Duffel Flights, Google Maps, Gaode Maps, RedNote, Weather, Test MCP
  - `agents/` - Specialized subagent prompts
  - `commands/` - Slash command definitions
  - `settings.json` - Claude Code configuration

- **data/** (2 active trips, 15 JSON files) - Travel plan data storage
  - `china-multi-city-feb15-mar7-2026/` - 21-day China trip (10 JSON files)
  - `test-trip/` - Test data and templates (5 JSON files)

- **scripts/** (6 scripts, ~1200 lines) - Validation, generation, deployment
  - Validation: `check-day-completion.sh`, `check-location-continuity.sh`, `validate-timeline-consistency.sh`
  - Generation: `generate-travel-html.sh`
  - Deployment: `deploy-travel-plans.sh`
  - Workflow: `todo/plan.py`

- **docs/** - Documentation and workflow JSONs
  - `clean/` - Clean workflow JSONs
  - `dev/` - Development workflow JSONs

### Root Files

**Project documentation**:
- `README.md` - This file
- `INDEX.md` - Project inventory

**Test results** (13 files):
- MCP skills testing reports
- Airbnb configuration guide
- RedNote skill test results and setup

---

## Features

### MCP Skills (7 integrations)

**Maps & Navigation**:
- Google Maps - Global maps, routing, places, weather
- Gaode Maps (高德地图) - China-specific maps and routing

**Accommodation**:
- Airbnb - Property search and details

**Transportation**:
- Duffel Flights - Flight search with real-time pricing

**Social Media**:
- RedNote (小红书) - Chinese UGC travel content

**Weather**:
- Weather.gov - Free weather data

**Testing**:
- Test MCP - Server validation

### Data Management

**Trip structure**:
```
trip-name/
├── requirements-skeleton.json    # Input requirements
├── plan-skeleton.json            # Generated plan
├── timeline.json                 # Day-by-day schedule
├── transportation.json           # Travel bookings
├── accommodation.json            # Lodging
├── attractions.json              # Sightseeing
├── meals.json                    # Dining
├── entertainment.json            # Events
├── shopping.json                 # Shopping
└── budget.json                   # Cost tracking
```

### Validation Scripts

Quality assurance for trip data:
- Day completion checks
- Location continuity validation
- Timeline consistency verification

---

## Installation

### Prerequisites

1. **Node.js** - For MCP server execution (npx)
2. **Python 3** - For MCP client scripts
3. **Claude Code** - For skill execution

### API Keys (Optional)

MCP skills require API keys:

```bash
# Required for API-based skills
export GOOGLE_MAPS_API_KEY="your-key"
export GAODE_API_KEY="your-key"
export AIRBNB_API_KEY="your-key"
export DUFFEL_API_KEY="your-key"

# No keys required
# - RedNote (scraping-based)
# - Weather (free government API)
# - Test MCP (testing only)
```

### Setup

```bash
# Clone repository
git clone <repo-url>
cd travel-planner

# Make scripts executable
chmod +x scripts/*.sh

# Test MCP skills (optional)
python3 .claude/skills/google-maps/scripts/places.py "restaurants in Paris" 5
```

---

## Usage

### Planning a Trip

1. **Create requirements**: `data/trip-name/requirements-skeleton.json`
2. **Generate plan**: Use planning agents or scripts
3. **Validate**: Run validation scripts
4. **Generate HTML**: `./scripts/generate-travel-html.sh data/trip-name/`
5. **Deploy**: `./scripts/deploy-travel-plans.sh data/trip-name/`

### Using MCP Skills

Skills are invoked via Bash tool:

```bash
# Google Maps place search
python3 .claude/skills/google-maps/scripts/places.py "restaurants in Tokyo" 10

# Gaode Maps routing (China)
python3 .claude/skills/gaode-maps/scripts/routing.py "北京" "上海" DRIVING

# RedNote search (Chinese travel content)
# Via SKILL.md examples
```

### Validation

```bash
# Validate timeline structure
./scripts/validate-timeline-consistency.sh data/trip-name/timeline.json

# Check day completion
./scripts/check-day-completion.sh data/trip-name/

# Check location continuity
./scripts/check-location-continuity.sh data/trip-name/timeline.json
```

---

## Documentation

- **Project overview**: README.md (this file)
- **Project inventory**: INDEX.md
- **Skills documentation**: `.claude/skills/README.md`
- **Data organization**: `data/README.md`
- **Scripts reference**: `scripts/README.md`
- **Individual skills**: `.claude/skills/{skill-name}/SKILL.md`

---

## Recent Structural Changes

Last 30 days:

- 2026-01-31 18:56:23: feat: Add RedNote (小红书) MCP skill with complete configuration
- 2026-01-31 13:42:29: checkpoint: Auto-save at 2026-01-31 13:42:29
- 2026-01-30 22:04:07: checkpoint: Auto-save at 2026-01-30 22:04:07
- 2026-01-30 20:02:37: checkpoint: Auto-save at 2026-01-30 20:02:37
- 2026-01-29 01:00:42: Initial commit: project setup

---

## Git Analysis

<!-- AUTO-GENERATED by rule-inspector - DO NOT EDIT -->
Project initialized: 2026-01-29
MCP skills added: Jan 30-31, 2026
Total commits: 50+
Last structural update: 2026-01-31 (RedNote skill)
Total directories: 33
Total MCP skills: 7
Total trip plans: 2 (1 active, 1 test)
<!-- END AUTO-GENERATED -->

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

---

*Root README updated by rule-inspector on 2026-01-31 to reflect current project structure*
