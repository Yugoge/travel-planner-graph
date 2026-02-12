#!/bin/bash
# Update all agent documentation to use unified load.py/save.py scripts
# Remove contradictory Write tool instructions

set -e

AGENTS_DIR=".claude/agents"
AGENTS=("meals" "attractions" "entertainment" "accommodation" "shopping" "transportation" "timeline" "budget")

echo "🔧 Updating agent documentation..."
echo ""

for agent in "${AGENTS[@]}"; do
    agent_file="$AGENTS_DIR/$agent.md"

    if [[ ! -f "$agent_file" ]]; then
        echo "⚠️  Skipping $agent (file not found)"
        continue
    fi

    echo "📝 Processing $agent.md..."

    # Create backup
    cp "$agent_file" "$agent_file.bak"

    # Replace Write tool instructions with unified save.py script
    sed -i 's/Write tool/scripts\/save.py script/g' "$agent_file"
    sed -i 's/Use Write(/Use scripts\/save.py(/g' "$agent_file"
    sed -i 's/Write(/save.py(/g' "$agent_file"

    # Add unified scripts section if not exists
    if ! grep -q "## Unified Data Access Scripts" "$agent_file"; then
        cat >> "$agent_file" << 'EOF'

---

## Unified Data Access Scripts

**CRITICAL: All data access must use unified scripts**

### Loading Data (load.py)

Use `scripts/load.py` for reading agent data with 3-level access:

**Level 1** - Day metadata only:
```bash
python3 scripts/load.py --trip TRIP_SLUG --agent AGENT_NAME --level 1
```

**Level 2** - POI titles/keys:
```bash
python3 scripts/load.py --trip TRIP_SLUG --agent AGENT_NAME --level 2 --day 3
```

**Level 3** - Full POI data:
```bash
python3 scripts/load.py --trip TRIP_SLUG --agent AGENT_NAME --level 3 --day 3 --poi POIKEY
```

### Saving Data (save.py)

Use `scripts/save.py` for writing agent data with mandatory validation:

**Save from file**:
```bash
python3 scripts/save.py --trip TRIP_SLUG --agent AGENT_NAME --input modified_data.json
```

**Save from stdin**:
```bash
cat modified_data.json | python3 scripts/save.py --trip TRIP_SLUG --agent AGENT_NAME
```

**Features**:
- ✅ Automatic validation (plan-validate.py)
- ✅ Atomic writes (.tmp → rename)
- ✅ Automatic backups (.bak)
- ✅ HIGH severity issues block saves
- ✅ Redundant field detection (100% structure validation)

### Write Tool Disabled

**The Write tool is disabled for all agents** to ensure:
- Data corruption prevention
- Mandatory validation
- Atomic operations
- Backup management
- 100% structure validation (including redundant field detection)

All agents must use `scripts/save.py` instead of Write tool.

EOF
    fi

    echo "   ✅ Updated $agent.md"
done

echo ""
echo "✅ All agent documentation updated"
echo "📦 Backups created with .bak extension"
