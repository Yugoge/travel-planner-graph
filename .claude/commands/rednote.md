---
description: "RedNote (小红书/Xiaohongshu) integration for searching Chinese UGC travel content"
allowed-tools: Task, Read, Bash
argument-hint: "[keyword|help]"
model: inherit
disable-model-invocation: true
---

# RedNote Skill

Search RedNote (小红书/Xiaohongshu) for authentic Chinese user-generated travel content including reviews, recommendations, photo guides, and local insights.

## Quick Start

**Usage**:
```bash
# Search for notes by keyword
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/rednote/scripts/search.py "北京必去景点" --limit 20

# Search for restaurant recommendations
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/rednote/scripts/search.py "成都本地人推荐美食" --limit 15

# Search for shopping tips
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/rednote/scripts/search.py "上海购物必去" --limit 10
```

## Available Scripts

All scripts are in `/root/travel-planner/.claude/skills/rednote/scripts/` and output JSON to stdout.

1. **search.py** - Search RedNote notes by keyword
   - `search.py <keyword> [--limit LIMIT]`
   - Returns: note ID, URL, title, description, author, likes, comments, cover image, note type

## MCP Tools (via Python scripts)

1. **mcp__rednote__search_notes** - Search notes by keyword
2. **mcp__rednote__get_note_content** - Get note content via URL (use full URL with xsec_token from search results)
3. **mcp__rednote__get_note_comments** - Get comments from note URL (~50% success rate, prefer get_note_content)
4. **mcp__rednote__login** - Manual authentication (prefer CLI `rednote-mcp init`)

## Search Keyword Patterns

- Attractions: "城市名必去景点", "小众景点", "拍照圣地"
- Restaurants: "美食推荐", "本地人推荐", "特色小吃"
- Shopping: "购物", "特产", "市场"
- Entertainment: "酒吧", "夜生活", "演出"

Use Chinese keywords for best results. Add modifiers like "推荐" (recommended) or "攻略" (guide).

## Workflow Pattern

1. **Search** for relevant content with targeted Chinese keywords
2. **Parse** search results JSON — review titles, descriptions, engagement metrics
3. **Get detailed content** using full URLs from search results (must include xsec_token)
4. **Extract** actionable info: names, locations, budgets, tips
5. **Verify** by cross-referencing multiple posts and checking with Gaode Maps

## Integration with Agents

Configured for: attractions, meals, shopping, entertainment agents.

```bash
# Attractions agent — hidden gems
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/rednote/scripts/search.py "北京小众景点" --limit 20

# Meals agent — authentic local food
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/rednote/scripts/search.py "成都本地人推荐美食" --limit 15

# Shopping agent — local markets
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/rednote/scripts/search.py "上海购物必去" --limit 10
```

## Authentication

- Cookie-based via `rednote-mcp init` (manual browser login)
- Cookies stored at `~/.mcp/rednote/cookies.json` (outside git)
- Re-run `rednote-mcp init` if cookies expire

## Quality Notes

- Strengths: Authentic UGC, visual content, current info, local insights
- Limitations: Chinese content only, subjective, needs verification
- Best practice: Compare 3-5 posts, check dates, verify with maps, prefer high engagement posts
- Rate limiting: Limit to 10-20 searches per session, avoid rapid-fire requests
