# Deep Research Report: Converting MCP Servers to Claude Skills

**Research Date:** 2026-01-30
**Research Objective:** Comprehensive investigation of MCP server to Claude Skill conversion patterns, structure, and best practices

---

## Executive Summary

This report provides comprehensive documentation on converting MCP (Model Context Protocol) servers into Claude Skills. The research covers official Claude Code documentation, real-world implementations, conversion tools, and best practices from 2025-2026.

**Key Finding:** Skills use a "progressive disclosure" pattern that achieves 90% context savings compared to traditional MCP servers by loading tool definitions dynamically rather than upfront.

---

## Table of Contents

1. [Directory Structure](#1-directory-structure)
2. [SKILL.md Format and Frontmatter Schema](#2-skillmd-format-and-frontmatter-schema)
3. [Skills vs Commands](#3-skills-vs-commands)
4. [Progressive Disclosure Pattern](#4-progressive-disclosure-pattern)
5. [MCP Tool Invocation from Skills](#5-mcp-tool-invocation-from-skills)
6. [Agent Integration](#6-agent-integration)
7. [MCP-to-Skill Converter Tools](#7-mcp-to-skill-converter-tools)
8. [Real-World Examples](#8-real-world-examples)
9. [Best Practices and Token Optimization](#9-best-practices-and-token-optimization)
10. [Known Issues and Limitations](#10-known-issues-and-limitations)

---

## 1. Directory Structure

### 1.1 Official Structure

Skills live in `.claude/skills/` with each skill as a separate directory:

```
.claude/skills/
└── skill-name/
    ├── SKILL.md          # Required: Main instructions with YAML frontmatter
    ├── scripts/          # Optional: Executable automation
    │   ├── helper.py
    │   └── validate.sh
    ├── templates/        # Optional: Templates Claude fills in
    │   └── template.md
    ├── examples/         # Optional: Example outputs
    │   └── sample.md
    ├── references/       # Optional: Detailed documentation
    │   ├── api-docs.md
    │   └── schemas.md
    └── assets/           # Optional: Static resources
        └── config.json
```

### 1.2 Skill Discovery Locations

| Location   | Path                                      | Scope                          | Priority        |
|:-----------|:------------------------------------------|:-------------------------------|:----------------|
| Enterprise | Via managed settings                      | All users in organization      | Highest         |
| Personal   | `~/.claude/skills/<skill-name>/`          | All projects for this user     | High            |
| Project    | `.claude/skills/<skill-name>/`            | Current project only           | Medium          |
| Plugin     | `<plugin>/skills/<skill-name>/`           | Where plugin is enabled        | Low (namespaced)|
| Nested     | `packages/frontend/.claude/skills/`       | Auto-discovered in subdirs     | Context-based   |

**Priority Resolution:** Enterprise > Personal > Project. Skills with the same name at higher levels override lower levels.

### 1.3 Nested Directory Discovery

Claude Code automatically discovers skills from nested `.claude/skills/` directories. For example:

```
project-root/
├── .claude/skills/          # Discovered when working anywhere in project
│   └── project-skill/
└── packages/
    └── frontend/
        └── .claude/skills/  # Discovered when editing files in packages/frontend/
            └── frontend-skill/
```

This supports monorepo setups where packages have their own specialized skills.

**Source:** [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)

---

## 2. SKILL.md Format and Frontmatter Schema

### 2.1 Complete Frontmatter Schema

```yaml
---
# REQUIRED/RECOMMENDED FIELDS
name: skill-name                    # Slash command identifier (kebab-case, max 64 chars)
description: |                      # Primary triggering mechanism - include "what" AND "when"
  What this skill does and when to use it. Use when the user asks for X, Y, or Z.
  Include all "when to use" information here, NOT in the body.

# INVOCATION CONTROL
disable-model-invocation: true      # Only user can invoke (not Claude)
user-invocable: false               # Only Claude can invoke (not user)
argument-hint: "[issue-number]"     # Autocomplete hint for arguments

# TOOL AND MODEL CONFIGURATION
allowed-tools: Read, Grep, Bash     # Tools Claude can use without approval
model: claude-opus-4-5              # Model override for this skill

# SUBAGENT EXECUTION
context: fork                       # Run in isolated subagent context
agent: Explore                      # Subagent type (Explore, Plan, general-purpose, or custom)

# LIFECYCLE HOOKS
hooks:                              # Hooks scoped to skill lifecycle
  pre-execute:
    - script: scripts/setup.sh

# METADATA
license: Apache-2.0                 # License information
version: 1.0.0                      # Version tracking
---

# Skill Instructions

Your markdown content here...
```

### 2.2 Field Descriptions

| Field | Required | Description | Default |
|:------|:---------|:------------|:--------|
| `name` | No | Display name for skill. If omitted, uses directory name. | Directory name |
| `description` | Recommended | What the skill does AND when to use it. Claude uses this for auto-invocation decisions. | First paragraph of body |
| `argument-hint` | No | Hint shown during autocomplete (e.g., `[filename] [format]`) | None |
| `disable-model-invocation` | No | If `true`, only user can invoke with `/skill-name`. For workflows with side effects (deploy, commit). | `false` |
| `user-invocable` | No | If `false`, hidden from `/` menu. For background knowledge Claude auto-loads. | `true` |
| `allowed-tools` | No | Comma-separated tools Claude can use without permission when skill is active. Supports wildcards. | None |
| `model` | No | Override the model used when this skill executes. | Session default |
| `context` | No | Set to `fork` to run in isolated subagent. | None (inline) |
| `agent` | No | Which subagent to use with `context: fork` (Explore, Plan, general-purpose, custom). | `general-purpose` |
| `hooks` | No | Lifecycle hooks scoped to skill. See [Hooks docs](https://code.claude.com/docs/en/hooks). | None |

### 2.3 Invocation Control Matrix

| Frontmatter | User Can Invoke | Claude Can Invoke | When Loaded |
|:------------|:----------------|:------------------|:------------|
| (default) | Yes | Yes | Description in context; full skill when invoked |
| `disable-model-invocation: true` | Yes | No | Description NOT in context; full skill when user invokes |
| `user-invocable: false` | No | Yes | Description in context; full skill when Claude invokes |

### 2.4 String Substitution Variables

Skills support dynamic value injection:

| Variable | Description | Example |
|:---------|:------------|:--------|
| `$ARGUMENTS` | All arguments passed to skill | `/fix-issue 123` → `$ARGUMENTS` = `123` |
| `$ARGUMENTS[N]` | Specific argument by 0-based index | `$ARGUMENTS[0]` = first arg |
| `$N` | Shorthand for `$ARGUMENTS[N]` | `$0`, `$1`, `$2`, etc. |
| `${CLAUDE_SESSION_ID}` | Current session ID | Useful for logging |
| `{baseDir}` | Skill's installation directory | For portable script paths |

**Example:**
```yaml
---
name: migrate-component
description: Migrate a component from one framework to another
---

Migrate the $0 component from $1 to $2.
Preserve all existing behavior and tests.
```

Usage: `/migrate-component SearchBar React Vue`

### 2.5 Dynamic Context Injection

The `!`command`` syntax runs shell commands before sending content to Claude:

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

**How it works:**
1. Each `!`command`` executes immediately (preprocessing)
2. Output replaces the placeholder
3. Claude receives the fully-rendered prompt with actual data

This is NOT something Claude executes - it happens before Claude sees the content.

**Sources:**
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Skill Creator SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)

---

## 3. Skills vs Commands

### 3.1 The Merge (Version 2.1.3)

As of Claude Code version 2.1.3, **slash commands have been merged into the skills system**. The merge maintains backward compatibility while unifying the systems.

### 3.2 Key Differences

| Aspect | Commands (`.claude/commands/`) | Skills (`.claude/skills/`) |
|:-------|:-------------------------------|:---------------------------|
| **Structure** | Single `.md` file | Directory with `SKILL.md` + resources |
| **Invocation** | Manual `/command-name` | Manual `/skill-name` OR auto-discovered by Claude |
| **Supporting Files** | None | Scripts, templates, references, assets |
| **Frontmatter** | Same as skills | Full feature set |
| **Bundled Resources** | No | Yes (unlimited progressive disclosure) |
| **Capability** | Simple prompt injection | Can extend with executable code |

### 3.3 Migration Status

**Backward Compatibility:**
- Files in `.claude/commands/` still work
- Support same frontmatter as skills
- If skill and command share same name, **skill takes precedence**

**Recommendation:**
- **New implementations:** Use `.claude/skills/` for enhanced features
- **Existing commands:** No need to migrate unless you need:
  - Bundled scripts
  - Template files
  - Reference documentation
  - Complex file organization

### 3.4 When to Use Each

**Use Simple Commands (`.claude/commands/`) When:**
- Single-file prompt is sufficient
- No supporting resources needed
- Manual invocation only
- Quick, lightweight customization

**Use Skills (`.claude/skills/`) When:**
- Need bundled scripts or executables
- Have extensive reference documentation
- Want progressive disclosure (>500 lines total)
- Want Claude to auto-discover and invoke
- Building complex workflows

**Sources:**
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Claude Code Merges Slash Commands Into Skills](https://medium.com/@joe.njenga/claude-code-merges-slash-commands-into-skills-dont-miss-your-update-8296f3989697)

---

## 4. Progressive Disclosure Pattern

### 4.1 Core Concept

Progressive disclosure is the foundational design principle that makes Agent Skills efficient and scalable. Instead of loading all information upfront, the system reveals details in stages based on need.

### 4.2 Three-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Level 1: METADATA (Always Loaded)                           │
│ - Skill name + description (~100 tokens per skill)          │
│ - Embedded in Skill tool's system prompt                    │
│ - Default budget: 15,000 characters for all skill metadata  │
└─────────────────────────────────────────────────────────────┘
                           ↓ (Claude decides skill is relevant)
┌─────────────────────────────────────────────────────────────┐
│ Level 2: FULL INSTRUCTIONS (Loaded on Invocation)           │
│ - Complete SKILL.md body (~500-5000 tokens)                 │
│ - Frontmatter excluded (already processed)                  │
│ - Includes {baseDir} for script paths                       │
└─────────────────────────────────────────────────────────────┘
                           ↓ (Claude needs specific details)
┌─────────────────────────────────────────────────────────────┐
│ Level 3: RESOURCES (Loaded on Demand)                       │
│ - scripts/ executed via Bash tool                           │
│ - references/ loaded via Read tool                          │
│ - templates/ copied and modified                            │
│ - Unlimited size, only loaded when referenced               │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Technical Implementation

**Metadata Message vs Instruction Message:**

Skills use a dual-message architecture:

1. **Metadata Message** (`isMeta: false`):
   - Visible in UI
   - 50-200 characters
   - Status information: `<command-message>The "skill-name" skill is loading</command-message>`
   - Provides user transparency

2. **Instruction Message** (`isMeta: true`):
   - Hidden from UI
   - Sent only to Claude
   - Complete SKILL.md content (500-5000 words)
   - Never appears in conversation transcript

This "meta-prompting for meta-tools" pattern allows different audiences (humans and AI) to receive appropriately tailored information.

### 4.4 Context Budget Management

**Default Settings:**
- Skill metadata character budget: 15,000 characters
- If exceeded, some skills excluded from context
- Check with `/context` command

**Environment Variable Override:**
```bash
export SLASH_COMMAND_TOOL_CHAR_BUDGET=25000  # Increase budget
```

### 4.5 Benefits

| Benefit | Traditional MCP | Progressive Disclosure Skills |
|:--------|:----------------|:------------------------------|
| **Startup Tokens** | 30,000-50,000 (all tools) | ~2,000 (all skill names) |
| **Active Task** | 30,000-50,000 | ~5,000 (one skill) |
| **Available Context** | 150k/200k (75%) | 193k/200k (96.5%) |
| **Token Savings** | Baseline | **90% reduction** |

### 4.6 Resource Organization Strategy

**Keep SKILL.md Concise (<500 lines):**
```markdown
---
name: api-integration
description: Integrate with external APIs using our patterns
---

# API Integration

## Quick Start
Basic authentication and request patterns.

## Common Patterns
Standard approaches for REST, GraphQL, and webhooks.

## Advanced Topics
For detailed schema specifications, see [SCHEMAS.md](references/SCHEMAS.md).
For authentication flows, see [AUTH.md](references/AUTH.md).
For rate limiting strategies, see [RATE_LIMITS.md](references/RATE_LIMITS.md).

## Scripts
Use `python {baseDir}/scripts/generate_client.py` to generate API clients.
```

**References Directory Pattern:**
```
api-integration/
├── SKILL.md                    # 400 lines: overview + navigation
├── references/
│   ├── SCHEMAS.md              # 2000 lines: complete schema docs
│   ├── AUTH.md                 # 800 lines: authentication details
│   └── RATE_LIMITS.md          # 500 lines: rate limiting strategies
└── scripts/
    └── generate_client.py      # Executable tool
```

**Sources:**
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Inside Claude Code Skills](https://mikhail.io/2025/10/claude-code-skills/)

---

## 5. MCP Tool Invocation from Skills

### 5.1 MCP Tool Naming Convention

When MCP servers provide tools to Claude Code, they are automatically prefixed with a standardized format:

```
mcp__plugin_<plugin-name>_<server-name>__<tool-name>
```

**Examples:**
- `mcp__plugin_asana_asana__asana_create_task`
- `mcp__plugin_asana_asana__asana_search_tasks`
- `mcp__plugin_github_github__create_pull_request`
- `mcp__plugin_filesystem_filesystem__readFile`

### 5.2 Invoking MCP Tools from Skill Frontmatter

Use the `allowed-tools` field to pre-approve MCP tools:

```yaml
---
name: github-workflow
description: Manage GitHub workflows using MCP
allowed-tools: |
  mcp__plugin_github_github__create_pull_request,
  mcp__plugin_github_github__list_issues,
  mcp__plugin_github_github__create_issue
---

# GitHub Workflow Skill

You can now use pre-approved GitHub tools...
```

**Wildcard Pattern (use sparingly):**
```yaml
allowed-tools: mcp__plugin_github_github__*
```

**Best Practice:** Pre-allow specific tools, not wildcards, for security.

### 5.3 MCP Tool Invocation Patterns

#### Pattern 1: Direct Invocation from SKILL.md

```yaml
---
name: asana-task-creator
description: Create Asana tasks from requirements
allowed-tools: Bash, mcp__plugin_asana_asana__asana_create_task
---

# Asana Task Creator

When creating tasks:
1. Parse requirements from user input
2. Call mcp__plugin_asana_asana__asana_create_task with structured data
3. Confirm task creation with task URL
```

#### Pattern 2: Dynamic Invocation via Executor Script

See [Section 7](#7-mcp-to-skill-converter-tools) for the executor.py pattern.

#### Pattern 3: Subagent with MCP Access

```yaml
---
name: mcp-executor
description: Execute MCP tool calls in isolated context
context: fork
agent: general-purpose
allowed-tools: |
  Bash(python *), Bash(node *),
  mcp__plugin_*__*
---

# MCP Executor

Execute TypeScript or Python code that:
1. Imports MCP client library
2. Connects to MCP server
3. Calls tools dynamically
4. Returns results
```

### 5.4 MCP Integration Architecture

**How Skills and MCP Work Together:**

```
┌────────────────────┐
│   User Request     │
└─────────┬──────────┘
          │
          ↓
┌────────────────────┐
│   Claude Core      │──────→ Skill tool loads relevant skill
└─────────┬──────────┘
          │
          ↓
┌────────────────────┐
│   Skill Execution  │──────→ SKILL.md instructions
└─────────┬──────────┘        + allowed-tools pre-approved
          │
          ↓
┌────────────────────┐
│   MCP Tool Call    │──────→ mcp__plugin_X_Y__tool_name
└─────────┬──────────┘
          │
          ↓
┌────────────────────┐
│   MCP Server       │──────→ Execute tool
└─────────┬──────────┘
          │
          ↓
┌────────────────────┐
│   Result           │──────→ Returned to Claude
└────────────────────┘
```

**Key Points:**
1. **MCP provides tool access** (the "what")
2. **Skills provide workflow logic** (the "how")
3. **Combining both creates powerful workflows**

**Example Combined Workflow:**
```yaml
---
name: competitive-analysis
description: Perform technical competitive analysis
allowed-tools: |
  mcp__plugin_google_drive_google_drive__search,
  mcp__plugin_github_github__list_repos,
  Bash(gh *),
  WebSearch
---

# Competitive Analysis Skill

Perform comprehensive technical competitive analysis:

1. **Gather Documents**: Search Google Drive for competitive research docs
   - Use mcp__plugin_google_drive_google_drive__search

2. **Analyze Repositories**: Find competitor GitHub repos
   - Use mcp__plugin_github_github__list_repos

3. **Market Research**: Search for recent news and trends
   - Use WebSearch

4. **Synthesize Findings**: Create structured report
```

**Sources:**
- [MCP Integration Skill Example](https://github.com/fcakyon/claude-codex-settings/blob/main/plugins/plugin-dev/skills/mcp-integration/SKILL.md)
- [The Complete Claude Code Guide: Skills, MCP & Tool Integration](https://mrzacsmith.medium.com/the-complete-claude-code-guide-skills-mcp-tool-integration-part-2-20dcf2fb8877)

---

## 6. Agent Integration

### 6.1 Subagent Execution with `context: fork`

Skills can run in isolated subagent contexts using `context: fork` frontmatter:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:

1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

**How It Works:**
1. New isolated context created
2. Subagent receives skill content as its prompt
3. `agent` field determines execution environment (model, tools, permissions)
4. Results summarized and returned to main conversation

### 6.2 Agent Types

| Agent Type | Purpose | Tools | Use Case |
|:-----------|:--------|:------|:---------|
| `Explore` | Read-only codebase exploration | Read, Grep, Glob, Bash (limited) | Research, analysis, understanding |
| `Plan` | Task planning and decomposition | Read, Grep, planning tools | Breaking down complex tasks |
| `general-purpose` | Default agent | Standard tool set | Generic tasks |
| Custom | User-defined in `.claude/agents/` | Configurable | Specialized workflows |

### 6.3 Skills vs Subagents Comparison

| Approach | System Prompt | Task | Also Loads |
|:---------|:--------------|:-----|:-----------|
| **Skill with `context: fork`** | From agent type (Explore, Plan, etc.) | SKILL.md content | CLAUDE.md |
| **Subagent with `skills` field** | Subagent's markdown body | Claude's delegation message | Preloaded skills + CLAUDE.md |

**Skills with context: fork:**
- You write the task in your skill
- Pick an agent type to execute it
- Skill content becomes the prompt

**Subagents with skills array:**
- Define custom subagent
- Preload skills as reference material
- Claude delegates with contextual task

### 6.4 Preloading Skills into Subagents

Create a custom subagent in `.claude/agents/specialized.md`:

```yaml
---
name: specialized-agent
skills:
  - api-conventions
  - testing-patterns
model: claude-opus-4-5
allowed-tools: Read, Write, Edit, Bash
---

# Specialized Agent System Prompt

You are a specialized agent with access to:
- API conventions skill (preloaded)
- Testing patterns skill (preloaded)

Apply these guidelines to all work...
```

**Behavior:**
- Full content of `api-conventions` and `testing-patterns` loaded at subagent startup
- Skills act as reference material, NOT isolated tasks
- Agent can use skill knowledge throughout entire session

### 6.5 When to Use `context: fork`

**Use `context: fork` When:**
- Task requires isolation from main conversation
- Want to limit context/history access
- Need specific agent capabilities (read-only Explore, planning-focused Plan)
- Task is self-contained and complete

**Don't Use `context: fork` When:**
- Skill contains only guidelines (no task)
- Need conversation history
- Want iterative refinement with user
- Skill provides reference material rather than executable workflow

**Warning from Docs:**
> `context: fork` only makes sense for skills with explicit instructions. If your skill contains guidelines like "use these API conventions" without a task, the subagent receives the guidelines but no actionable prompt, and returns without meaningful output.

**Sources:**
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Agent Skills in the SDK](https://platform.claude.com/docs/en/agent-sdk/skills)

---

## 7. MCP-to-Skill Converter Tools

### 7.1 Overview

Several tools exist to convert MCP servers into Claude Skills, achieving significant context savings by implementing progressive disclosure.

**Primary Repository:**
- [GBSOSS/-mcp-to-skill-converter](https://github.com/GBSOSS/-mcp-to-skill-converter)
- Alternative: [saygex9965/-mcp-to-skill-converter](https://github.com/saygex9965/-mcp-to-skill-converter)

### 7.2 The Problem Being Solved

**Traditional MCP Approach:**
- All tool definitions loaded into context at startup
- 20 tools = 30,000-50,000 tokens consumed before Claude does any work
- Available context: 150k/200k (75%)

**Skill Approach with Progressive Disclosure:**
- 20 skill names = ~2,000 tokens at startup
- Active skill adds ~5,000 tokens when invoked
- Available context: 193k/200k (96.5%)
- **Token Savings: 90%**

### 7.3 Generated Skill Structure

The converter generates:

```
skill-name/
├── SKILL.md                    # ~100 tokens: metadata and overview
├── executor.py                 # Dynamic MCP tool invocation
├── mcp-config.json             # MCP server configuration
├── requirements.txt            # Python dependencies
└── README.md                   # Usage instructions
```

### 7.4 Executor.py Pattern

The executor acts as a runtime bridge between Claude and the MCP server:

```python
# Simplified executor.py pattern

import json
import sys
from mcp import Client

def list_tools(server_config):
    """List all available tools from MCP server"""
    client = Client(server_config)
    tools = client.list_tools()
    return tools

def describe_tool(server_config, tool_name):
    """Get detailed schema for specific tool"""
    client = Client(server_config)
    schema = client.get_tool_schema(tool_name)
    return schema

def call_tool(server_config, tool_name, arguments):
    """Execute tool with given arguments"""
    client = Client(server_config)
    result = client.call_tool(tool_name, arguments)
    return result

if __name__ == "__main__":
    config = load_config("mcp-config.json")

    if sys.argv[1] == "--list":
        print(list_tools(config))
    elif sys.argv[1] == "--describe":
        print(describe_tool(config, sys.argv[2]))
    elif sys.argv[1] == "--call":
        tool_call = json.loads(sys.argv[2])
        print(call_tool(config, tool_call["tool"], tool_call["arguments"]))
```

### 7.5 SKILL.md Pattern for MCP Wrapper

```yaml
---
name: github-tools
description: GitHub operations via MCP. Use when working with GitHub repos, issues, PRs, or releases.
allowed-tools: Bash(python *)
---

# GitHub Tools Skill

Access GitHub functionality through MCP tools.

## Available Operations

To see all available tools:
```bash
python {baseDir}/executor.py --list
```

To get tool details:
```bash
python {baseDir}/executor.py --describe tool_name
```

To call a tool:
```bash
python {baseDir}/executor.py --call '{"tool": "create_issue", "arguments": {"repo": "user/repo", "title": "Bug report", "body": "Description"}}'
```

## Common Tools

- `create_issue` - Create GitHub issue
- `create_pull_request` - Create PR
- `list_issues` - List issues
- `search_code` - Search code across repos

Call executor.py with --describe for full schemas.
```

### 7.6 MCP Configuration Format

```json
{
  "name": "github",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

### 7.7 Complete Usage Workflow

**1. Create MCP Config:**
```json
// github-mcp.json
{
  "name": "github",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

**2. Run Converter:**
```bash
python mcp_to_skill.py \
  --mcp-config github-mcp.json \
  --output-dir ./skills/github-mcp
```

**3. Install Dependencies:**
```bash
cd skills/github-mcp
pip install -r requirements.txt
```

**4. Deploy to Claude:**
```bash
cp -r . ~/.claude/skills/github-mcp
```

**5. Test Executor:**
```bash
# List available tools
python ~/.claude/skills/github-mcp/executor.py --list

# Describe a tool
python ~/.claude/skills/github-mcp/executor.py --describe create_issue

# Call a tool
python ~/.claude/skills/github-mcp/executor.py --call '{
  "tool": "create_issue",
  "arguments": {
    "repo": "user/repo",
    "title": "Test issue",
    "body": "Created via executor"
  }
}'
```

**6. Use in Claude:**
```
User: Create a GitHub issue for bug in authentication

Claude: [Invokes github-mcp skill]
        [Calls executor.py with create_issue tool]
        [Returns result]
```

### 7.8 Alternative Pattern: cc-mcp-executor-skill

The [cc-mcp-executor-skill](https://github.com/mcfearsome/cc-mcp-executor-skill) provides a different approach:

**Architecture:**
1. Main Claude Code (without MCP servers) recognizes multi-tool workflows
2. Launches subagent via Task tool
3. Subagent writes TypeScript/Python code
4. Executes via Bash
5. Code imports local MCP client library
6. Calls tools via MCP protocol

**Key Difference:**
- Instead of executor.py as wrapper, generates code that directly imports MCP libraries
- Provides 12 cached script examples (6 TypeScript + 6 Python)
- Progressive disclosure: loads MCP tools only in subagent context

**Sources:**
- [MCP-to-Skill Converter Repository](https://github.com/GBSOSS/-mcp-to-skill-converter)
- [Built a converter that turns any MCP server into a Claude Skill](https://gist.github.com/Felo-Sparticle/69f4b54fb3c67fa9d9d9db78dd615a1d)
- [cc-mcp-executor-skill Repository](https://github.com/mcfearsome/cc-mcp-executor-skill)

---

## 8. Real-World Examples

### 8.1 Official Anthropic Skills Repository

**Repository:** [anthropics/skills](https://github.com/anthropics/skills)
- **Stars:** 58.7k | **Forks:** 5.7k
- **Created:** September 22, 2025
- **License:** Mixed (Apache 2.0 for most; source-available for document skills)

### 8.2 Skill Categories and Examples

#### Document Skills (Production-Grade)

**Location:** `skills/document-skills/`

1. **docx** - Word document creation & editing
   - Create new .docx files
   - Modify existing documents
   - Work with tracked changes
   - Handle styles and formatting

2. **pdf** - PDF manipulation and form extraction
   - Extract text and metadata
   - Fill PDF forms
   - Merge and split PDFs

3. **pptx** - PowerPoint presentation generation
   - Create presentations from scratch
   - Add slides with various layouts
   - Apply themes and styles

4. **xlsx** - Excel spreadsheet operations
   - Create workbooks
   - Manipulate data
   - Apply formulas and formatting

**Note:** Document skills are source-available and power Claude's production document capabilities.

#### Creative & Design Skills

**frontend-design** - Distinctive, production-grade UI design

**Frontmatter:**
```yaml
---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications. Generates creative, polished code and UI design that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---
```

**Structure:**
- **Design Thinking Section**: Pre-coding conceptual framework
  - Purpose analysis
  - Tone selection (brutally minimal, maximalist, retro-futuristic, etc.)
  - Constraints identification
  - Differentiation strategy

- **Frontend Aesthetics Guidelines**:
  1. Typography (avoid generic fonts)
  2. Color & Theme (cohesive aesthetic)
  3. Motion (CSS animations, scroll triggers)
  4. Spatial Composition (asymmetry, grid-breaking)
  5. Backgrounds & Visual Details (gradients, textures, patterns)

**Key Principle:** "Choose a clear conceptual direction and execute it with precision."

**Files:**
- `SKILL.md` - 4.34 KB, ~42 lines
- `LICENSE.txt` - License terms

---

**algorithmic-art** - Computational art using p5.js

**Frontmatter:**
```yaml
---
name: algorithmic-art
description: Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems.
license: Complete terms in LICENSE.txt
---
```

**Two-Phase Workflow:**
1. **Algorithmic Philosophy Creation** (.md file)
   - Name the computational aesthetic movement
   - Articulate philosophy (4-6 paragraphs)
   - Leave creative space for implementation

2. **P5.js Implementation** (.html artifact)
   - Self-contained HTML with inline p5.js
   - Seeded randomness for reproducibility
   - Interactive parameter controls
   - Anthropic-branded UI

**Directory Structure:**
```
algorithmic-art/
├── SKILL.md                    # Main instructions
├── templates/
│   ├── viewer.html             # REQUIRED starting point with branding
│   └── generator_template.js   # p5.js best practices reference
├── examples/
│   └── philosophies.md         # Example aesthetic movements
└── LICENSE.txt
```

**Key Patterns:**
- **Seeded Randomness**: `randomSeed(seed); noiseSeed(seed);`
- **Parameter Object**: Structured controls for algorithm variables
- **Art Blocks Pattern**: Same seed = identical output
- **Progressive Disclosure**: Philosophy → Implementation

**Template Structure (viewer.html):**
```
FIXED (keep unchanged):
├── Header with Anthropic branding
├── Sidebar layout
│   ├── Seed Section (prev/next/random/jump)
│   ├── Parameters Section
│   ├── Colors Section
│   └── Actions Section (regenerate/reset/download)
└── Canvas area (1200x1200)

VARIABLE (customize per artwork):
├── P5.js algorithm (setup/draw/classes)
├── Parameter definitions
├── UI control implementation
└── Color scheme
```

#### Development & Technical Skills

**skill-creator** - Meta-skill for creating new skills

**Purpose:** Guide Claude in creating well-structured skills that follow best practices.

**Key Guidelines:**
1. Challenge each paragraph for necessity
2. Target <500 lines for SKILL.md
3. Move detailed docs to references/
4. Use progressive disclosure
5. Include both "what" and "when" in description

**Allowed Tools:** `Read, Write, Bash, Glob, Grep, Edit`

**References:**
- `init_skill.py` script for template generation
- Uses `{baseDir}` variable for portable paths

### 8.3 Community Skills

**Claude Code Showcase:**
- Repository: [ChrisWiles/claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase)
- Comprehensive example project with hooks, skills, agents, commands, GitHub Actions

**Awesome Claude Skills:**
- Repository: [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)
- Curated list of skills, resources, and tools

### 8.4 File Organization Patterns

**Simple Skill (No Resources):**
```
simple-skill/
└── SKILL.md                    # 200 lines: complete instructions
```

**Medium Skill (Scripts):**
```
automation-skill/
├── SKILL.md                    # 300 lines: workflow instructions
└── scripts/
    ├── setup.sh
    ├── deploy.py
    └── validate.js
```

**Complex Skill (Full Structure):**
```
api-integration-skill/
├── SKILL.md                    # 400 lines: overview + navigation
├── scripts/
│   ├── generate_client.py      # Client generation
│   └── test_endpoints.sh       # Endpoint testing
├── templates/
│   ├── request.json            # Request template
│   └── config.yaml             # Configuration template
├── references/
│   ├── API_REFERENCE.md        # 2000 lines: complete API docs
│   ├── SCHEMAS.md              # 1500 lines: data schemas
│   └── EXAMPLES.md             # 800 lines: usage examples
└── examples/
    ├── basic_auth.md
    └── oauth_flow.md
```

**Domain-Organized Skill:**
```
bigquery-skill/
├── SKILL.md                    # Navigation hub
└── references/
    ├── finance.md              # Revenue, billing queries
    ├── sales.md                # Opportunities, pipeline
    ├── product.md              # API usage analytics
    └── marketing.md            # Campaign performance
```

**Sources:**
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Skill Creator SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [Frontend Design SKILL.md](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)
- [Algorithmic Art SKILL.md](https://github.com/anthropics/skills/blob/main/skills/algorithmic-art/SKILL.md)

---

## 9. Best Practices and Token Optimization

### 9.1 Token Optimization Principles

#### The 500-Line Rule
**Keep SKILL.md under 500 lines.** Move detailed reference material to separate files.

**Example Breakdown:**
```
SKILL.md: 400 lines                     ✅ Loaded when skill invokes
references/API_DOCS.md: 2000 lines      ✅ Loaded only when referenced
references/EXAMPLES.md: 800 lines       ✅ Loaded only when referenced
Total available: 3200 lines
Token cost: ~500 tokens (SKILL.md) + 0 tokens (references until needed)
```

vs.

```
SKILL.md: 3200 lines                    ❌ All loaded when skill invokes
Total available: 3200 lines
Token cost: ~4000 tokens immediately
```

#### Description Field Optimization

The description is Claude's PRIMARY triggering mechanism. Optimize carefully:

**Good Description (Comprehensive):**
```yaml
description: |
  Explains code with visual diagrams and analogies. Use when explaining how
  code works, teaching about a codebase, or when the user asks "how does this
  work?" Creates accessible explanations for complex technical concepts.
```

**Poor Description (Vague):**
```yaml
description: Explains code
```

**Include in Description:**
- What the skill does (capabilities)
- When to use it (triggers)
- Specific keywords users might say
- Specific contexts where it applies

**Exclude from Description:**
- Implementation details (put in body)
- Examples (put in body)
- Lengthy explanations (put in body)

#### Resource Reference Strategy

**Pattern 1: High-Level Guide with Deep References**
```markdown
## API Integration

### Quick Start
Basic authentication:
```python
import requests
response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
```

### Reference Documentation
- **Complete API Reference**: See [API_REFERENCE.md](references/API_REFERENCE.md)
- **Authentication Flows**: See [AUTH_GUIDE.md](references/AUTH_GUIDE.md)
- **Rate Limiting**: See [RATE_LIMITS.md](references/RATE_LIMITS.md)
```

**Pattern 2: Conditional Details**
```markdown
## Document Processing

For simple text extraction, use pdftotext directly.

**For advanced features:**
- Form filling: See [FORMS.md](references/FORMS.md)
- OCR processing: See [OCR.md](references/OCR.md)
- Metadata extraction: See [METADATA.md](references/METADATA.md)
```

### 9.2 Skill Design Best Practices

#### Write for Claude, Not Humans

**Remember:** Another Claude instance will use this skill. Include:
- Procedural knowledge Claude needs
- Domain-specific context
- Tool invocation patterns
- Success criteria

**Exclude:**
- User-facing documentation
- Installation instructions
- Changelog
- README content
- Marketing material

#### Use Imperative Voice

**Good:**
```markdown
1. Read the configuration file
2. Validate required fields
3. Generate the client code
4. Write output to src/generated/
```

**Poor:**
```markdown
You should read the configuration file and then you would validate the required
fields before generating the client code which gets written to the generated folder.
```

#### Challenge Token Cost

For every paragraph, ask:
- Does Claude already know this?
- Does this justify its token cost?
- Can this be condensed?
- Should this be in a reference file instead?

#### Prefer Executable Scripts for Determinism

**When to use scripts/ vs inline instructions:**

**Use Script When:**
- Logic is deterministic
- Complex multi-step processing
- External tool orchestration
- Requires specific execution order

**Use Inline Instructions When:**
- Claude needs to make decisions
- Context-dependent behavior
- Creative or interpretive tasks
- User interaction required

**Example:**
```markdown
## Deployment Process

**Automated Checks** (deterministic):
```bash
python {baseDir}/scripts/pre_deploy_checks.py
```

**Review and Decision** (requires judgment):
Review the check results and decide:
- If all tests pass: proceed with deployment
- If warnings present: assess severity and document decision
- If errors present: abort and create issue tickets
```

### 9.3 Allowed-Tools Security Patterns

#### Principle of Least Privilege

**Good (Restrictive):**
```yaml
allowed-tools: Read, Grep, Glob
```
Claude can explore but not modify.

**Poor (Overly Permissive):**
```yaml
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
```
Unnecessary surface area.

#### Bash Tool Wildcards

**Good (Specific):**
```yaml
allowed-tools: Bash(git *), Bash(npm *), Read, Write
```

**Poor (Too Broad):**
```yaml
allowed-tools: Bash(*)
```

#### MCP Tool Pre-Approval

**Good (Explicit):**
```yaml
allowed-tools: |
  mcp__plugin_github_github__create_issue,
  mcp__plugin_github_github__list_issues,
  mcp__plugin_github_github__get_issue,
  Read, Write
```

**Acceptable (Scoped Wildcard):**
```yaml
allowed-tools: mcp__plugin_github_github__*, Read, Write
```

**Avoid (Blanket Wildcard):**
```yaml
allowed-tools: mcp__plugin_*__*
```

### 9.4 Frontmatter Decision Matrix

| Scenario | Frontmatter Configuration |
|:---------|:--------------------------|
| User-only command with side effects | `disable-model-invocation: true` |
| Background knowledge | `user-invocable: false` |
| Read-only exploration | `allowed-tools: Read, Grep, Glob` |
| Isolated execution | `context: fork` |
| Specific agent needed | `context: fork` + `agent: Explore` |
| Model override needed | `model: claude-opus-4-5` |
| Auto-discovery desired | (default - no special fields) |

### 9.5 Progressive Disclosure Checklist

- [ ] Is SKILL.md under 500 lines?
- [ ] Are detailed docs in references/?
- [ ] Does SKILL.md link to all reference files?
- [ ] Do reference files have table of contents (if >100 lines)?
- [ ] Are scripts in scripts/ directory?
- [ ] Is {baseDir} used for all script paths?
- [ ] Does description include "what" and "when"?
- [ ] Are allowed-tools minimally scoped?
- [ ] Are there no unnecessary files (README, CHANGELOG, etc.)?

**Sources:**
- [Skill Creator SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

---

## 10. Known Issues and Limitations

### 10.1 Reported Bugs and Issues

#### Issue #1: allowed-tools Not Enforced

**Status:** Reported bug
**Issue:** [GitHub #18837](https://github.com/anthropics/claude-code/issues/18837)

**Description:** The `allowed-tools` field in skill/command frontmatter does not appear to be enforced. Claude can freely use tools not listed in `allowed-tools`.

**Impact:** Orchestration-style skills that rely on tool restrictions may not function as intended.

**Workaround:** Use permission rules in `/permissions` to enforce tool restrictions at a higher level.

#### Issue #2: context: fork and agent: Not Honored by Skill Tool

**Status:** Feature request
**Issue:** [GitHub #17283](https://github.com/anthropics/claude-code/issues/17283)

**Description:** When a skill is invoked via the Skill tool, the `context: fork` and `agent:` frontmatter fields are ignored. The skill runs in the main conversation context instead of spawning the specified subagent.

**Impact:** Skills designed for isolated execution or specific agent types don't work as intended when Claude auto-invokes them.

**Workaround:**
- Use manual invocation with `/skill-name`
- Create a separate subagent that references the skill

#### Issue #3: Inconsistent context: fork Behavior

**Status:** Reported bug
**Issue:** [GitHub #18394](https://github.com/anthropics/claude-code/issues/18394)

**Description:** Skill frontmatter `fork` parameter fails inconsistently.

**Impact:** Skills with `context: fork` may sometimes execute in main context.

### 10.2 SDK vs CLI Differences

#### allowed-tools Field

**Limitation:** The `allowed-tools` frontmatter field in SKILL.md is only supported when using Claude Code CLI directly and does not apply when using Skills through the SDK.

**SDK Workaround:** Control tool access through the main `allowedTools` option in your query configuration.

**Example:**
```typescript
// SDK approach (skills don't control allowed-tools)
const result = await client.query({
  prompt: "Use the api-integration skill to call the endpoint",
  allowedTools: ["mcp__plugin_api_api__call_endpoint", "Read"],
  // Skill's allowed-tools field ignored
});
```

### 10.3 Context Budget Limitations

#### Skill Metadata Exclusion

**Default Budget:** 15,000 characters for all skill descriptions

**Problem:** If you have many skills, some may be excluded from context.

**Detection:** Run `/context` to check for warnings about excluded skills.

**Solution:** Increase the budget with environment variable:
```bash
export SLASH_COMMAND_TOOL_CHAR_BUDGET=25000
```

**Alternative:** Refactor skill descriptions to be more concise.

### 10.4 Design Limitations

#### No Nested Resource References

**Limitation:** Skills should reference resources in a single level. Avoid nested chains.

**Example of What NOT to Do:**
```markdown
<!-- In SKILL.md -->
See [OVERVIEW.md](references/OVERVIEW.md) for details

<!-- In OVERVIEW.md -->
See [DETAILED_GUIDE.md](detailed/DETAILED_GUIDE.md) for more
```

**Why:** Claude needs to know upfront what resources exist. Nested chains make discovery harder.

**Best Practice:** Link all references directly from SKILL.md:
```markdown
<!-- In SKILL.md -->
- Overview: [OVERVIEW.md](references/OVERVIEW.md)
- Detailed Guide: [DETAILED_GUIDE.md](references/DETAILED_GUIDE.md)
- Examples: [EXAMPLES.md](references/EXAMPLES.md)
```

#### No Interactive/Stateful Scripts

**Limitation:** Skills cannot bundle interactive scripts that require TTY or maintain state across invocations.

**Examples That Won't Work:**
- Scripts using `input()` or `readline`
- Scripts with `--interactive` flags
- Git commands with `-i` flag (`git rebase -i`, `git add -i`)
- Scripts requiring sudo password

**Reason:** Claude invokes scripts via Bash tool which doesn't support interactive input.

**Workaround:** Design scripts to accept all parameters as arguments:
```python
# Bad - requires interactive input
def main():
    name = input("Enter name: ")
    process(name)

# Good - accepts arguments
def main():
    import sys
    name = sys.argv[1]
    process(name)
```

#### Context Isolation Trade-offs

**Limitation:** Skills with `context: fork` don't have access to conversation history.

**Impact:** Can't reference previous discussion, decisions, or context from main conversation.

**When This Matters:**
- User has been discussing requirements for 10 messages
- Skill needs that context to complete task
- Conversation contains decisions or constraints

**Solution:** Either:
1. Don't use `context: fork` for context-dependent skills
2. Pass relevant context as skill arguments
3. Include context in dynamic injection with `!`command``

### 10.5 MCP Integration Limitations

#### Tool Naming Conflicts

**Issue:** If multiple MCP servers provide tools with the same name, the prefixed naming prevents conflicts but can be verbose:

```
mcp__plugin_github_primary_github__create_issue
mcp__plugin_github_secondary_github__create_issue
```

**Mitigation:** Use descriptive plugin names in MCP configuration.

#### Environment Variable Substitution

**Limitation:** MCP config environment variables (like `${GITHUB_TOKEN}`) are resolved at MCP server startup, not at skill invocation.

**Impact:** If environment changes, must restart MCP server or reload configuration.

**Workaround:** Use dynamic injection for runtime-dependent values:
```yaml
---
name: github-operations
---

Current token: !`echo $GITHUB_TOKEN`
Use this token for authentication...
```

**Sources:**
- [GitHub Issue #18837](https://github.com/anthropics/claude-code/issues/18837)
- [GitHub Issue #17283](https://github.com/anthropics/claude-code/issues/17283)
- [GitHub Issue #18394](https://github.com/anthropics/claude-code/issues/18394)
- [Agent Skills in the SDK](https://platform.claude.com/docs/en/agent-sdk/skills)

---

## Conclusion

Converting MCP servers to Claude Skills requires understanding:

1. **Progressive Disclosure Architecture**: Three-level loading (metadata → instructions → resources)
2. **Directory Structure**: `.claude/skills/skill-name/SKILL.md` with optional subdirectories
3. **Frontmatter Schema**: Comprehensive YAML configuration with 12+ optional fields
4. **MCP Tool Invocation**: Standardized naming (`mcp__plugin_X_Y__tool`) with executor patterns
5. **Token Optimization**: 90% context savings through deferred loading
6. **File Organization**: SKILL.md <500 lines, references/ for details, scripts/ for determinism
7. **Agent Integration**: `context: fork` for isolation, `agent:` for specialization

**Primary Benefit:** Skills achieve 90% token savings vs traditional MCP while maintaining full functionality through progressive disclosure and dynamic tool invocation.

**Recommended Approach:**
1. Start with simple SKILL.md (no resources)
2. Add scripts/ for deterministic operations
3. Move detailed docs to references/
4. Use executor.py pattern for dynamic MCP tool access
5. Test with `context: fork` for isolation when needed

---

## Sources

### Official Documentation
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Agent Skills in the SDK](https://platform.claude.com/docs/en/agent-sdk/skills)
- [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)

### Technical Deep Dives
- [Inside Claude Code Skills: Structure, prompts, invocation](https://mikhail.io/2025/10/claude-code-skills/)
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [The Complete Claude Code Guide: Skills, MCP & Tool Integration](https://mrzacsmith.medium.com/the-complete-claude-code-guide-skills-mcp-tool-integration-part-2-20dcf2fb8877)

### Official Repositories
- [anthropics/skills - Public repository for Agent Skills](https://github.com/anthropics/skills)
- [Skill Creator SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [Frontend Design SKILL.md](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)
- [Algorithmic Art SKILL.md](https://github.com/anthropics/skills/blob/main/skills/algorithmic-art/SKILL.md)

### Conversion Tools
- [GBSOSS/mcp-to-skill-converter](https://github.com/GBSOSS/-mcp-to-skill-converter)
- [Built a converter that turns any MCP server into a Claude Skill](https://gist.github.com/Felo-Sparticle/69f4b54fb3c67fa9d9d9db78dd615a1d)
- [mcfearsome/cc-mcp-executor-skill](https://github.com/mcfearsome/cc-mcp-executor-skill)

### Integration Examples
- [MCP Integration Skill](https://github.com/fcakyon/claude-codex-settings/blob/main/plugins/plugin-dev/skills/mcp-integration/SKILL.md)

### Community Resources
- [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)
- [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
- [ChrisWiles/claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase)

### Comparison Articles
- [Claude Code Merges Slash Commands Into Skills](https://medium.com/@joe.njenga/claude-code-merges-slash-commands-into-skills-dont-miss-your-update-8296f3989697)
- [When to Use Claude Code Skills vs Commands vs Agents](https://danielmiessler.com/blog/when-to-use-skills-vs-commands-vs-agents)
- [Claude Skills vs MCP: The 2026 Guide](https://www.cometapi.com/claude-skills-vs-mcp-the-2026-guide-to-agentic-architecture/)

### Engineering Blog Posts
- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Extending Claude's capabilities with skills and MCP](https://claude.com/blog/extending-claude-capabilities-with-skills-mcp-servers)

---

**Report Generated:** 2026-01-30
**Total Sources Consulted:** 40+
**Search Depth:** 5 parallel search rounds + 9 detailed WebFetch operations
**Research Duration:** ~15 minutes
