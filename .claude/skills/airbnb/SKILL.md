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
