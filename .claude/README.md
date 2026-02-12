# .claude/

Claude Code configuration directory.

---

## Purpose

Configuration directory for Claude Code containing MCP skills, subagents, slash commands, and global settings.

**Architecture**: Multi-agent orchestration with script-based MCP integration.

## Allowed File Types

- `.json` files: Configuration (settings.json)
- `.md` files: Agent prompts, command definitions, skill documentation
- `.py` files: MCP client scripts (in skills/)
- `.sh` files: Helper scripts (in skills/)

## Naming Convention

- **Subdirectories**: kebab-case (skills/, agents/, commands/)
- **Agent files**: kebab-case (accommodation.md, timeline.md)
- **Command files**: kebab-case (plan.md, gaode-maps.md)
- **Skill directories**: kebab-case (google-maps/, duffel-flights/)

## Organization Rules

### Directory Structure

```
.claude/
├── settings.json          # Global Claude Code configuration
├── skills/                # MCP skill integrations (7 skills)
│   ├── airbnb/
│   ├── duffel-flights/
│   ├── gaode-maps/
│   ├── google-maps/
│   ├── rednote/
│   ├── weather/
│   └── test-mcp/
├── agents/                # Specialized subagents (8 agents)
│   ├── accommodation.md
│   ├── attractions.md
│   ├── budget.md
│   ├── entertainment.md
│   ├── meals.md
│   ├── shopping.md
│   ├── timeline.md
│   └── transportation.md
└── commands/              # Slash commands (3 commands)
    ├── plan.md
    ├── gaode-maps.md
    ├── test-gaode.md
    └── gaode-maps/        # Command-specific resources
```

### File Responsibilities

**settings.json**:
- Claude Code global configuration
- Skill activation/deactivation
- Environment variables (API keys)
- Hook configurations
- DO NOT commit API keys to git

**skills/**:
- MCP skill integrations for external APIs
- Each skill is self-contained
- See `.claude/skills/README.md` for details
- Progressive disclosure pattern (no context pollution)

**agents/**:
- Specialized subagent prompts
- Single-responsibility agents
- Travel planning workflow tasks
- Invoked by /plan command

**commands/**:
- User-facing slash command definitions
- Orchestrator prompts (coordinate agents)
- Entry points for workflows
- Example: /plan orchestrates 8 travel agents

## Agent System

### Travel Planning Agents (8)

**Planning agents**:
1. **timeline.md** - Day-by-day itinerary generation
2. **transportation.md** - Inter-city travel planning
3. **accommodation.md** - Hotel/lodging selection
4. **attractions.md** - Tourist site recommendations
5. **meals.md** - Dining plans and reservations
6. **entertainment.md** - Shows, events, nightlife
7. **shopping.md** - Shopping locations and items
8. **budget.md** - Cost estimation and tracking

**Workflow**: /plan command orchestrates all 8 agents in parallel or sequence.

### Agent Principles

1. **Single responsibility**: Each agent handles one planning aspect
2. **JSON communication**: Agents receive/return structured JSON
3. **No orchestration**: Agents do NOT coordinate other agents
4. **Skill integration**: Agents use skills/ for external data
5. **Data output**: Agents write to data/ directory

## Command System

### Available Commands (3)

**plan.md** (16.8KB):
- Main travel planning orchestrator
- Coordinates 8 travel planning agents
- Multi-agent workflow with parallel execution
- Generates interactive HTML output

**gaode-maps.md** (5.6KB):
- Gaode Maps integration command
- China-specific routing and POI search
- Wrapper for gaode-maps skill

**test-gaode.md**:
- Test command for Gaode Maps
- Validation and debugging

### Command Principles

1. **Orchestration only**: Commands coordinate, agents execute
2. **Context building**: Commands build comprehensive JSON context
3. **User interaction**: Commands handle user input/clarification
4. **Results presentation**: Commands format agent outputs for users
5. **No implementation**: Commands delegate to agents

## Skill System

**See `.claude/skills/README.md` for comprehensive documentation.**

**Quick summary**:
- 7 MCP skills (Airbnb, Duffel, Google Maps, Gaode, RedNote, Weather, Test)
- Script-based execution (no context pollution)
- Progressive disclosure pattern
- API key management via environment variables

## Configuration

### settings.json

**Key sections**:
- `skills`: Skill activation/deactivation
- `mcpServers`: MCP server configurations
- `hooks`: Automation hooks (session start, tool use)
- `environmentVariables`: API keys (NOT committed to git)

**Security**:
- NEVER commit API keys
- Use environment variables
- Reference from shell profile or .env

## Integration Flow

```
User types: /plan "3-week trip to China"
    ↓
plan.md command: Parse requirements, build context
    ↓
8 agents execute in parallel:
    timeline.md → google-maps skill → Google Maps API
    accommodation.md → airbnb skill → Airbnb API
    transportation.md → duffel-flights skill → Duffel API
    attractions.md → rednote skill → RedNote scraping
    meals.md → google-maps skill → Places API
    entertainment.md → google-maps skill → Places API
    shopping.md → rednote skill → Shopping content
    budget.md → aggregate costs
    ↓
plan.md command: Aggregate results, generate HTML
    ↓
User: Review interactive trip plan
```

## File Creation Patterns

**agents/** - Created: Jan 30-31, 2026 (manual)
**commands/** - Created: Jan 29-30, 2026 (manual)
**skills/** - Created: Jan 30-31, 2026 (manual)
**settings.json** - Created: Jan 30, 2026 (manual)

**Pattern**: Initial project setup with batch creation.

## Standards

### Agent Files (.md)

1. **Clear purpose**: Single-responsibility description
2. **Input/output**: Specify JSON schema
3. **Skill usage**: Document which skills agent uses
4. **Data output**: Specify data/ files created

### Command Files (.md)

1. **User-facing**: Clear usage instructions
2. **Orchestration**: Define agent coordination
3. **Context building**: Specify JSON context structure
4. **Error handling**: Define failure modes

### Skills

See `.claude/skills/README.md`

## Git Analysis

<!-- AUTO-GENERATED by rule-inspector - DO NOT EDIT -->
First created: 2026-01-29
Configuration setup: Jan 30, 2026
Total agents: 8 (travel planning)
Total commands: 3 (plan, gaode-maps, test-gaode)
Total skills: 7 (API integrations)
Last significant update: 2026-01-31 (RedNote skill)
<!-- END AUTO-GENERATED -->

---

*This README documents the organization rules for .claude/. Generated by rule-inspector from git history analysis.*
