---
name: airbnb
description: Vacation rental search via Airbnb
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Airbnb Skill

Search vacation rentals with Airbnb data.

**MCP Server**: `@openbnb/mcp-server-airbnb` (v0.1.3)
**API Coverage**: 2/2 tools (100%)

## Available Tools

1. **airbnb_search** - Search for Airbnb listings with filters and pagination
2. **airbnb_listing_details** - Get detailed information about a specific listing

## Configuration Required

⚠️ **Airbnb blocks requests via robots.txt**. You must configure the MCP server to bypass this restriction.

Add to your `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
      "env": {}
    }
  }
}
```

**Legal Notice**: Web scraping may violate Airbnb's Terms of Service. Use for personal research/testing only.

**See Also**: `/root/travel-planner/AIRBNB-CONFIGURATION-GUIDE.md` for detailed setup instructions, troubleshooting, and legal considerations.

## How to Use in Agents

**IMPORTANT**: In Claude Code CLI, use Bash tool to call Python scripts directly:

```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/.claude/skills/airbnb/scripts/search.py "Beijing" --checkin "2026-02-10" --checkout "2026-02-12" --ignore-robots
```

**Required**: Add `--ignore-robots` flag to bypass robots.txt restrictions.

## How to Use Manually

```bash
cd /root/travel-planner/.claude/skills/airbnb
python3 scripts/search.py "LOCATION" --checkin DATE --checkout DATE --adults N --ignore-robots
python3 scripts/details.py LISTING_ID --checkin DATE --checkout DATE
```

## Examples

**Search**:
```bash
source /root/.claude/venv/bin/activate && python3 scripts/search.py "Austin, TX" --checkin 2026-06-15 --checkout 2026-06-22 --adults 2
```

**Details**:
```bash
source /root/.claude/venv/bin/activate && python3 scripts/details.py 12345678 --checkin 2026-06-15 --checkout 2026-06-22 --adults 2
```

Returns JSON with amenities, pricing, policies, reviews.
