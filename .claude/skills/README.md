# .claude/skills

MCP skill integrations for travel planning via script-based MCP server communication.

---

## Purpose

This folder contains MCP (Model Context Protocol) skill integrations that provide access to external travel APIs without polluting Claude's tool context. Each skill uses Python scripts to communicate with MCP servers via JSON-RPC 2.0.

**Key principle**: Scripts invoked via Bash tool, not loaded as MCP tools in Claude's context (progressive disclosure pattern).

## Allowed File Types

- `.md` files: Skill documentation (SKILL.md), examples, tool reference
- `.py` files: Python scripts for MCP communication
- `.sh` files: Shell scripts for verification/testing
- `.json` files: Test reports and configuration
- NO `.pyc` files in git (bytecode should be .gitignored)

## Naming Convention

- **Directories**: kebab-case (e.g., `google-maps`, `duffel-flights`)
- **Python files**: snake_case (e.g., `mcp_client.py`, `search_flights.py`)
- **Markdown files**: UPPERCASE for main docs (`SKILL.md`, `README.md`), kebab-case for examples

## Organization Rules

### Standard Skill Structure

Each skill follows this pattern:

```
skill-name/
├── SKILL.md              # Main skill documentation (REQUIRED)
├── README.md             # Optional: Setup guide (comprehensive docs)
├── scripts/              # Python MCP client scripts (API-based skills)
│   ├── mcp_client.py    # Base MCP JSON-RPC client
│   └── *.py             # Feature-specific scripts
├── examples/             # Usage examples (markdown)
│   └── *.md             # Workflow examples with agent integration
└── tools/                # MCP tool documentation (reference only)
    └── *.md             # Tool parameter specs
```

### File Responsibilities

**SKILL.md** (required):
- Entry point for skill usage
- Quick reference for agents
- Script invocation examples
- API key requirements
- Return value formats

**README.md** (optional):
- Comprehensive setup guide
- Architecture explanation
- Troubleshooting
- Best practices
- Only needed for complex skills (e.g., google-maps)

**scripts/** (for API-based skills):
- Python scripts that communicate with MCP servers
- Each script is self-contained and executable
- Common pattern: `mcp_client.py` (base) + feature scripts
- Output: Stdout (human-readable), Stderr (JSON)

**examples/** (optional):
- Markdown files with usage examples
- Show agent integration patterns
- Include sample inputs/outputs

**tools/** (optional):
- MCP tool documentation (reference)
- Parameter specifications
- Not directly used by agents (scripts abstract this)

## File Creation Patterns

Based on Git history analysis:

**Created by**: Manual user additions via checkpoint commits
**Timeframe**: Jan 29-31, 2026 (recent project setup)
**Pattern**: Batch skill additions during initial project configuration

**Commit pattern**:
- "checkpoint: Auto-save at YYYY-MM-DD HH:MM:SS" (90% of commits)
- "feat: Add [skill name] MCP skill with complete configuration" (feature commits)

**Automation level**: ~10% (most skills manually created, few automated scripts)

## Standards

### Python Scripts (.py)

1. **Executable**: All scripts must have proper shebang if standalone
2. **API keys**: Use environment variables, NEVER hardcode
3. **Output**: Dual output (stdout human-readable, stderr JSON)
4. **Error handling**: Distinguish transient (retry) vs permanent errors
5. **MCP client**: Reuse `mcp_client.py` base class when possible

### Documentation (.md)

1. **SKILL.md required**: Every skill must have SKILL.md entry point
2. **Examples**: Include at least one usage example
3. **API keys**: Document required environment variables
4. **Return format**: Specify output structure (JSON schema)

### Git Hygiene

1. **Ignore bytecode**: .pyc files should not be committed (.gitignore)
2. **No secrets**: API keys in environment only
3. **Descriptive commits**: Use "feat:", "fix:", "docs:" prefixes

## Skill Categories

### Maps & Navigation (3 skills)
- **google-maps**: Google Maps API (global)
- **gaode-maps**: 高德地图 (China-specific)
- Both provide: geocoding, POI search, routing

### Accommodation (1 skill)
- **airbnb**: Property search and details

### Transportation (1 skill)
- **duffel-flights**: Flight search via Duffel API

### Weather (1 skill)
- **weather**: Weather.gov API (free, US-focused)

### Social Media (1 skill)
- **rednote**: 小红书 content extraction (China travel insights)

### Testing (1 skill)
- **test-mcp**: MCP server validation

## API Key Management

**Skills requiring API keys** (5):
1. airbnb → `AIRBNB_API_KEY`
2. duffel-flights → `DUFFEL_API_KEY`
3. gaode-maps → `GAODE_API_KEY`
4. google-maps → `GOOGLE_MAPS_API_KEY`
5. weather → No key required (free API)

**Skills without API keys** (2):
1. rednote → Scraping-based (no key)
2. test-mcp → Testing only (no key)

**Setup**: Set environment variables in shell profile or project .env file

## Agent Integration

Agents use skills via Bash tool:

```bash
# Example: Google Maps place search
source /root/.claude/venv/bin/activate && python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py \
  "restaurants in Paris" 5
```

**No MCP tools loaded**: Scripts communicate with MCP servers directly, avoiding Claude context pollution.

## Recent Changes

<!-- AUTO-GENERATED by rule-inspector -->
Last 30 days:

- 2026-01-31 18:56:23: feat: Add RedNote (小红书) MCP skill with complete configuration
- 2026-01-31 13:42:29: checkpoint: Auto-save at 2026-01-31 13:42:29
- 2026-01-31 13:17:26: checkpoint: Auto-save at 2026-01-31 13:17:26
- 2026-01-31 12:52:33: checkpoint: Auto-save at 2026-01-31 12:52:33
- 2026-01-30 22:04:07: checkpoint: Auto-save at 2026-01-30 22:04:07
<!-- END AUTO-GENERATED -->

---

## Git Analysis

<!-- AUTO-GENERATED by rule-inspector - DO NOT EDIT -->
Project initialized: 2026-01-29
Skills added: Jan 30-31, 2026
Total commits (skills folder): 25+ checkpoint commits
Last significant update: 2026-01-31 (rednote skill)
<!-- END AUTO-GENERATED -->

---

*This README documents the discovered organization patterns for .claude/skills. Generated by rule-inspector from git history analysis.*
