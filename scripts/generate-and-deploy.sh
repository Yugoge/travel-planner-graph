#!/bin/bash
# Generate interactive React HTML and deploy to GitHub Pages
# Usage: bash scripts/generate-and-deploy.sh <plan-id>

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
    echo -e "Usage: bash scripts/generate-and-deploy.sh <plan-id>"
    echo -e "Example: bash scripts/generate-and-deploy.sh beijing-exchange-bucket-list-20260202-232405"
    exit 1
fi

PLAN_ID="$1"
DATA_DIR="$PROJECT_ROOT/data/$PLAN_ID"
OUTPUT_FILE="$PROJECT_ROOT/travel-plan-${PLAN_ID}.html"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎨 Interactive HTML Generator & Deployer${NC}"
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

# Step 1: Fetch real images from Google Maps and Gaode Maps
echo -e "${BLUE}[1/5]${NC} Fetching real photos from Google Maps and Gaode Maps..."
cd "$PROJECT_ROOT"

# Check if images.json exists and has photos
IMAGES_FILE="$DATA_DIR/images.json"
if [ -f "$IMAGES_FILE" ]; then
    POI_COUNT=$(python3 -c "import json; data = json.load(open('$IMAGES_FILE')); print(len(data.get('pois', {})))" 2>/dev/null || echo "0")
    if [ "$POI_COUNT" -gt "0" ]; then
        echo -e "${GREEN}✓${NC} Found $POI_COUNT cached POI photos"
    else
        echo -e "${YELLOW}⚠${NC}  No POI photos cached, fetching 20 POIs..."
        python3 "$SCRIPT_DIR/fetch-images-batch.py" "$PLAN_ID" 5 20 2>/dev/null || echo -e "${YELLOW}⚠${NC}  Image fetch failed, using fallback images"
    fi
else
    echo -e "${YELLOW}⚠${NC}  No image cache found, fetching 20 POIs..."
    python3 "$SCRIPT_DIR/fetch-images-batch.py" "$PLAN_ID" 5 20 2>/dev/null || echo -e "${YELLOW}⚠${NC}  Image fetch failed, using fallback images"
fi
echo ""

# Step 2: Generate interactive React HTML
echo -e "${BLUE}[2/5]${NC} Generating interactive React HTML..."
cd "$PROJECT_ROOT"
python3 "$SCRIPT_DIR/generate-html-interactive.py" "$PLAN_ID"

if [ ! -f "$OUTPUT_FILE" ]; then
    echo -e "${RED}❌ Error: HTML generation failed${NC}"
    exit 1
fi

FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo -e "${GREEN}✓${NC} Generated: $OUTPUT_FILE (${FILE_SIZE})"
echo ""

# Step 3: Validate HTML
echo -e "${BLUE}[3/5]${NC} Validating HTML structure..."
if ! grep -q "PLAN_DATA" "$OUTPUT_FILE"; then
    echo -e "${RED}❌ Error: PLAN_DATA not found in HTML${NC}"
    exit 1
fi
if ! grep -q "React" "$OUTPUT_FILE"; then
    echo -e "${RED}❌ Error: React library not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} HTML structure valid"
echo ""

# Step 4: Deploy to GitHub Pages
echo -e "${BLUE}[4/5]${NC} Deploying to GitHub Pages..."
bash "$SCRIPT_DIR/deploy-travel-plans.sh" "$OUTPUT_FILE"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
