#!/bin/bash
# Generate Notion-style React HTML and deploy to GitHub Pages
# Usage: bash scripts/generate-notion-and-deploy.sh <plan-id>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check argument
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Plan ID required${NC}"
    echo -e "Usage: bash scripts/generate-notion-and-deploy.sh <plan-id>"
    echo -e "Example: bash scripts/generate-notion-and-deploy.sh beijing-exchange-bucket-list-20260202-232405"
    exit 1
fi

PLAN_ID="$1"
DATA_DIR="$PROJECT_ROOT/data/$PLAN_ID"
OUTPUT_FILE="$PROJECT_ROOT/travel-plan-notion-${PLAN_ID}.html"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎨 Notion React HTML Generator & Deployer${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Validate data directory
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}❌ Error: Data directory not found: $DATA_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Plan ID: ${YELLOW}$PLAN_ID${NC}"
echo -e "${GREEN}✓${NC} Data directory: $DATA_DIR"
echo ""

# Step 1: Generate Notion React HTML
echo -e "${BLUE}[1/4]${NC} Generating Notion-style React HTML..."
cd "$PROJECT_ROOT"
python3 "$SCRIPT_DIR/generate-notion-react.py" "$PLAN_ID"

if [ ! -f "$OUTPUT_FILE" ]; then
    echo -e "${RED}❌ Error: HTML generation failed${NC}"
    exit 1
fi

FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo -e "${GREEN}✓${NC} Generated: $OUTPUT_FILE (${FILE_SIZE})"
echo ""

# Step 2: Validate HTML
echo -e "${BLUE}[2/4]${NC} Validating HTML structure..."
if ! grep -q "PLAN_DATA" "$OUTPUT_FILE"; then
    echo -e "${RED}❌ Error: PLAN_DATA not found in HTML${NC}"
    exit 1
fi
if ! grep -q "NotionTravelApp" "$OUTPUT_FILE"; then
    echo -e "${RED}❌ Error: NotionTravelApp component not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} HTML structure valid"
echo ""

# Step 3: Deploy to GitHub Pages
echo -e "${BLUE}[3/4]${NC} Deploying to GitHub Pages..."
bash "$SCRIPT_DIR/deploy-travel-plans.sh" "$OUTPUT_FILE"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
