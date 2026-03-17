---
description: "Standard folder structure and organization patterns"
---

# Folder Structure Standard

## Directory Organization

All folders in this project follow a consistent structure with:

1. **README.md** - Folder overview and purpose
2. **Subfolders** - Organized by function or domain
3. **Configuration files** - When applicable (*.json, *.yaml)
4. **Index files** - Auto-generated navigation (when needed)

## Standard Patterns

### Agents Directory (`.claude/agents/`)

Each agent folder contains:
- **README.md** - Agent overview and responsibilities
- **agent-name.md** - Detailed agent documentation
- **schema.json** - Input/output data structure (optional)

### Commands Directory (`.claude/commands/`)

Each command folder contains:
- **README.md** - Command overview
- **command-name.md** - Command workflow and implementation
- **examples/** - Usage examples (optional)
- **tools/** - Supporting tool definitions (optional)

### Skills Directory (`.claude/skills/`)

Each skill folder contains:
- **README.md** - Skill overview and capabilities
- **skill-name.md** - Skill documentation
- **scripts/** - Implementation scripts
- **tests/** - Verification tests (optional)

## Naming Conventions

- **Folders**: lowercase with hyphens (e.g., `gaode-maps`, `plan-cache`)
- **Files**: lowercase with hyphens for docs (e.g., `README.md`, `schema.json`)
- **Markdown files**: descriptive names matching content (e.g., `poi-classification-rules.md`)

## Documentation Standards

All README.md files should include:

1. **Description** - What is this folder for?
2. **Contents** - What files/folders are inside?
3. **Usage** - How to use contents?
4. **References** - Links to related documentation

## Maintenance

- Keep README.md updated when structure changes
- Remove empty folders periodically
- Archive old content to `docs/archive/YYYY-MM/`
- Index large directories with auto-generated INDEX.md

See `/docs/dev/` for additional standards and guidelines.
