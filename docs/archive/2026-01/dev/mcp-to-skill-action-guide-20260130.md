# MCP to Skill Conversion - Action Guide for Dev Subagents

**Date**: 2026-01-30
**Purpose**: Convert 8 MCP servers to proper Claude Skills in `.claude/skills/` directory
**Research Base**: `/root/travel-planner/docs/dev/mcp-to-skill-research-report.md`

---

## Critical Requirements

### 1. Correct Directory Structure

**MUST USE:**
```
.claude/skills/
└── skill-name/
    ├── SKILL.md          # Main file (NOT skill-name.md!)
    ├── tools/            # Tool category documentation
    │   ├── category1.md
    │   └── category2.md
    └── examples/         # Usage examples
        └── example1.md
```

**DO NOT USE:**
```
.claude/commands/skill-name.md  # WRONG! This was the mistake!
```

### 2. SKILL.md Frontmatter Schema

```yaml
---
name: skill-name
description: |
  Complete description including WHEN to use this skill.
  Must trigger Claude to invoke automatically when relevant.
allowed-tools: [Task, Read, Bash]  # Tools this skill can use
model: inherit                      # Inherit from main agent
user-invocable: true                # Allow /skill-name invocation
---
```

### 3. Progressive Disclosure Pattern

**Token Optimization:**
- SKILL.md: ~500-1000 tokens (overview + loading instructions)
- Tool categories: Load on demand via Read tool
- Examples: Reference only, not auto-loaded

**Loading Pattern in SKILL.md:**
```markdown
## Tool Categories

Load on demand:
- `/skill-name category1` → Read `.claude/skills/skill-name/tools/category1.md`
- `/skill-name category2` → Read `.claude/skills/skill-name/tools/category2.md`
```

### 4. MCP Tool Invocation

**Pattern:**
```markdown
MCP tools follow naming: `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`

Example:
- MCP server: google-maps
- Tool: search_places
- Full name: `mcp__plugin_google-maps_google-maps__search_places`
```

**In Skill:**
```markdown
## Using MCP Tools

After loading tool category, invoke MCP tools directly:

1. Load category: Read `.claude/skills/google-maps/tools/places.md`
2. Use tool definition to call: `mcp__plugin_google-maps_google-maps__search_places`
3. Parse response and structure data
```

### 5. Agent Integration

**In Agent Frontmatter:**
```yaml
---
name: agent-name
skills:
  - skill-name
---
```

**Agent Body:**
Use skill when needed: `/skill-name category`

---

## 8 MCPs to Convert

### 1. google-maps
- **MCP Name**: Google Maps Grounding Lite
- **Skill Name**: google-maps
- **Tool Categories**: places, routing, weather
- **Agents**: transportation, meals, accommodation, attractions, shopping, entertainment

### 2. yelp
- **MCP Name**: Yelp Fusion AI
- **Skill Name**: yelp
- **Tool Categories**: search
- **Agents**: meals

### 3. tripadvisor
- **MCP Name**: TripAdvisor
- **Skill Name**: tripadvisor
- **Tool Categories**: attractions, tours
- **Agents**: attractions, entertainment

### 4. jinko-hotel
- **MCP Name**: Jinko Hotel Booking
- **Skill Name**: jinko-hotel
- **Tool Categories**: search, details, booking
- **Agents**: accommodation

### 5. airbnb
- **MCP Name**: Airbnb
- **Skill Name**: airbnb
- **Tool Categories**: search
- **Agents**: accommodation

### 6. amadeus-flight
- **MCP Name**: Amadeus Flight Search
- **Skill Name**: amadeus-flight
- **Tool Categories**: search, details
- **Agents**: transportation

### 7. openweathermap
- **MCP Name**: OpenWeatherMap
- **Skill Name**: openweathermap
- **Tool Categories**: current, forecast, air-quality, alerts
- **Agents**: ALL 8 agents

### 8. gaode-maps
- **MCP Name**: Gaode Maps (existing, needs conversion)
- **Skill Name**: gaode-maps
- **Tool Categories**: routing, poi-search, geocoding, utilities
- **Agents**: transportation, meals, accommodation, attractions, shopping, entertainment

---

## Dev Subagent Tasks

### Task 1: Delete Old Command Structure

```bash
# Remove all incorrectly placed command files
rm -rf .claude/commands/google-maps.md .claude/commands/google-maps/
rm -rf .claude/commands/yelp.md .claude/commands/yelp/
rm -rf .claude/commands/tripadvisor.md .claude/commands/tripadvisor/
rm -rf .claude/commands/jinko-hotel.md .claude/commands/jinko-hotel/
rm -rf .claude/commands/airbnb.md .claude/commands/airbnb/
rm -rf .claude/commands/amadeus-flight.md .claude/commands/amadeus-flight/
rm -rf .claude/commands/openweathermap.md .claude/commands/openweathermap/
rm -rf .claude/commands/gaode-maps.md .claude/commands/gaode-maps/
```

### Task 2: Create Correct Skill Structure

For each skill, create:

**Directory:**
```bash
mkdir -p .claude/skills/skill-name/tools
mkdir -p .claude/skills/skill-name/examples
```

**Files:**
1. `.claude/skills/skill-name/SKILL.md` (main file, ~500-1000 tokens)
2. `.claude/skills/skill-name/tools/*.md` (tool categories)
3. `.claude/skills/skill-name/examples/*.md` (usage examples)

### Task 3: SKILL.md Content Template

```markdown
---
name: skill-name
description: |
  [What this skill does and WHEN to use it]
  Use when user needs [specific functionality].
allowed-tools: [Task, Read, Bash]
model: inherit
user-invocable: true
---

# Skill Name

[Brief overview]

## Prerequisites

MCP server must be configured. See Setup section.

## Tool Categories

This skill uses progressive disclosure. Load only what you need:

1. **category1** - [Description]
   - Tool 1
   - Tool 2

2. **category2** - [Description]
   - Tool 3
   - Tool 4

## Loading Tools

Load categories on demand:

```
/skill-name category1  # Loads tools/category1.md
/skill-name category2  # Loads tools/category2.md
```

## MCP Server Setup

[Configuration instructions]

## Security

- Never hardcode API keys
- Use environment variables
- Configure in MCP server config

## Integration

Configured for agents: [list]

Usage: `/skill-name [category]`
```

### Task 4: Tool Category File Template

```markdown
# Skill Name - Category Name

[Category description]

## MCP Tools

### Tool 1: tool_name

**MCP Tool Name**: `mcp__plugin_server_server__tool_name`

**Parameters**:
- `param1` (required): Description
- `param2` (optional): Description

**Returns**:
- Field 1: Description
- Field 2: Description

**Example**:
```javascript
// Example usage
tool_name({
  param1: "value",
  param2: "value"
})
```

**Use Cases**:
- Use case 1
- Use case 2

---

[Repeat for each tool]

## Best Practices

[Category-specific best practices]

## Error Handling

[Error handling patterns]
```

### Task 5: Agent Integration

Update agent frontmatter:
```yaml
---
name: agent-name
skills:
  - existing-skill
  - new-skill-name  # ADD THIS
---
```

Add integration section in agent body:
```markdown
## Skill Integration: skill-name

**When to use**: [conditions]

**Workflow**:
1. Invoke `/skill-name category`
2. Use loaded MCP tools
3. Parse responses
4. Structure data for output

**Fallback**: Use WebSearch if MCP unavailable
```

---

## Quality Standards

### MUST:
1. ✅ Use `.claude/skills/skill-name/SKILL.md` structure
2. ✅ Include complete YAML frontmatter
3. ✅ Implement progressive disclosure
4. ✅ Document MCP tool names correctly (`mcp__plugin_...`)
5. ✅ No hardcoded API keys
6. ✅ Environment variables for credentials
7. ✅ Error handling with retry logic
8. ✅ WebSearch fallback
9. ✅ Update agent frontmatter
10. ✅ Add integration documentation

### MUST NOT:
1. ❌ Create files in `.claude/commands/`
2. ❌ Name main file as `skill-name.md` (must be `SKILL.md`)
3. ❌ Load all tools upfront (defeats progressive disclosure)
4. ❌ Hardcode credentials
5. ❌ Skip frontmatter fields
6. ❌ Forget to update agents

---

## Verification Checklist

After implementation, verify:

- [ ] Skill directory exists: `.claude/skills/skill-name/`
- [ ] Main file named `SKILL.md` (not skill-name.md)
- [ ] Frontmatter has all required fields
- [ ] Tool categories in `tools/` subdirectory
- [ ] Examples in `examples/` subdirectory
- [ ] MCP tool names use correct format
- [ ] No API keys in any files
- [ ] Agent frontmatter updated
- [ ] Agent body has integration section
- [ ] Old command files deleted
- [ ] Progressive disclosure implemented
- [ ] Error handling documented
- [ ] Fallback strategy defined

---

## Success Criteria

1. **File Structure**: All 8 skills in `.claude/skills/` with SKILL.md
2. **Progressive Disclosure**: Main files <1000 tokens, load tools on demand
3. **No Commands**: Zero files in `.claude/commands/` for these skills
4. **Agent Integration**: All agents updated with correct skills
5. **Security**: No hardcoded credentials
6. **Documentation**: Complete MCP setup instructions
7. **Quality**: Passes all QA checks

---

## Common Mistakes to Avoid

Based on previous failure:

1. **Wrong Directory**: Putting skill in `.claude/commands/` instead of `.claude/skills/`
2. **Wrong Filename**: Using `skill-name.md` instead of `SKILL.md`
3. **Missing Frontmatter**: Forgetting YAML frontmatter
4. **Loading Everything**: Not implementing progressive disclosure
5. **Tool Names**: Incorrect MCP tool naming format
6. **Hardcoding**: API keys in files
7. **Agent Config**: Forgetting to update agent frontmatter

---

## Reference Files

- **Research Report**: `/root/travel-planner/docs/dev/mcp-to-skill-research-report.md`
- **Official Docs**: https://code.claude.com/docs/en/skills
- **Converter Tool**: https://github.com/GBSOSS/-mcp-to-skill-converter
- **Examples**: https://github.com/anthropics/skills

---

**This guide is authoritative**. Follow it exactly. Do not deviate from the structure or patterns defined here.
