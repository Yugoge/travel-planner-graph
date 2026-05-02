# Travel Planner Project Documentation

> Reference documentation for project configuration, structure, and conventions.
> MCP servers, skill definitions, data flow, and best practices are documented here.
> This file was extracted from `.claude/settings.json` to keep settings.json minimal and standard.

---

## MCP Servers

### Gaode Maps (`@amap/amap-maps-mcp-server`)

Gaode Maps (高德地图) API for route planning, POI search, and geocoding in China.

**Required for**: transportation agent (enhanced routing), meals/accommodation/attractions agents (POI search), timeline agent (distance calculation)

**Configuration (recommended — streamable_http)**:

```json
{
  "mcpServers": {
    "amap-maps": {
      "url": "https://mcp.amap.com/mcp?key=YOUR_AMAP_API_KEY"
    }
  }
}
```

Config location: `~/.config/Claude/claude_desktop_config.json`

**Configuration (alternative — nodejs_io)**:

```json
{
  "mcpServers": {
    "amap-maps": {
      "command": "npx",
      "args": ["-y", "@amap/amap-maps-mcp-server"],
      "env": { "AMAP_MAPS_API_KEY": "YOUR_AMAP_API_KEY" }
    }
  }
}
```

**Setup**:
1. Get API key from https://console.amap.com/dev/key/app
2. Add MCP server config to `claude_desktop_config.json`
3. Replace `YOUR_AMAP_API_KEY` with actual key
4. Restart Claude Desktop

**Rate limits**: Free tier: 2,000–3,000 calls/day | Basic: 300,000 calls/day

**Available tools**: `driving_route`, `walking_route`, `cycling_route`, `transit_route`, `poi_search_keyword`, `poi_search_nearby`, `poi_detail`, `geocode`, `reverse_geocode`, `ip_location`, `weather_info`, `distance_measure`

**Coordinate system**: GCJ-02 (China-specific) | **Response language**: Chinese

**Security**: Never commit API keys. Use environment variables. Config file should stay in user's home directory (not in git repo).

---

## Permissions Notes

- **Write tool is BLOCKED** for all 8 travel planning agents via deny rules (commits ef0ed28, f9634dc)
- **Recommended load script**: `scripts/load.py` (3-level hierarchical loading)
- **Mandatory save script**: `scripts/save.py` (batch validation + atomic writes)
- **Root cause reference**: Commits ef0ed28 (2026-02-07) and f9634dc (2026-02-12) — Write tool overwrites entire files causing Day 2-21 data deletion
- **Developer note**: Developers (non-agent context) can still use Write tool normally. Only agents are blocked.

**Blocked agents**: accommodation, attractions, budget, entertainment, meals, shopping, timeline, transportation

---

## Skill Invocations

### `/gaode-maps [category]`
Invoke Gaode Maps skill for route planning and POI search.
Categories: `routing`, `poi-search`, `geocoding`, `utilities`
Allowed agents: transportation, meals, accommodation, attractions, shopping, timeline

### `/plan [destination]`
Multi-agent travel planning orchestrator. Invokes agents: meals, accommodation, attractions, entertainment, shopping, transportation, timeline, budget.

---

## Project Structure

| Path | Purpose |
|------|---------|
| `.claude/commands/` | Slash commands (skills) |
| `.claude/agents/` | Subagent definitions |
| `.claude/hooks/` | Lifecycle hooks |
| `scripts/` | Bash scripts for validation and HTML generation |
| `scripts/todo/` | Python scripts for workflow management |
| `data/` | Trip-specific data (one subdirectory per trip) |

---

## Data Flow

**Pattern**: equity-research (file-based communication)

**Input**: `data/{destination-slug}/requirements-skeleton.json`

**Agent outputs**:
- `data/{destination-slug}/meals.json`
- `data/{destination-slug}/accommodation.json`
- `data/{destination-slug}/attractions.json`
- `data/{destination-slug}/entertainment.json`
- `data/{destination-slug}/shopping.json`
- `data/{destination-slug}/transportation.json`
- `data/{destination-slug}/timeline.json`
- `data/{destination-slug}/budget.json`

**Final output**: `travel-plan-{destination-slug}.html`

---

## Skills

### `gaode-maps`
- **Pattern**: progressive_disclosure
- **Main file**: `.claude/commands/gaode-maps.md` (~200 tokens)
- **Canonical docs**: `.claude/commands/scripts/gaode-maps/tools/` (routing.md, poi-search.md, geocoding.md, utilities.md — ~8000 tokens)
- **Quick reference**: `.claude/commands/gaode-maps/tools/` (~1000 tokens stubs)
- **Load strategy**: Load main file initially, load categories on demand
- **Token savings**: 85–98% vs loading all tools upfront
- **Consolidation** (2026-01-31): Eliminated 1857 lines, ~95% duplication reduction in commands/

### `plan`
- **Type**: orchestrator
- **Main file**: `.claude/commands/plan.md`
- **Phases**: BA requirement collection → Skeleton initialization → Parallel agent execution (6 agents) → Serial (timeline, budget) → Validation → HTML generation → Refinement loop

---

## Dependencies

- **Runtime**: Linux, Claude Code Agent SDK
- **External**: Gaode Maps MCP (`@amap/amap-maps-mcp-server`) — optional, fallback to WebSearch

---

## Best Practices

- Never hardcode API keys in skill files or code
- Load only necessary tool definitions to optimize tokens (progressive disclosure)
- Implement retry logic with exponential backoff for transient errors
- Fall back to WebSearch if MCP unavailable
- Accept both English and Chinese inputs for Chinese destinations
- Agents communicate via JSON files, not direct invocation
- Run validation after each agent phase
- Use git checkpoints for auto-save, commit manually after milestones
