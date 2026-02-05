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

# Check if gh-pages branch exists
if ! git show-ref --verify --quiet refs/heads/gh-pages; then
    echo -e "${YELLOW}⚠${NC}  gh-pages branch doesn't exist, creating..."
    git checkout --orphan gh-pages
    git rm -rf .
    git commit --allow-empty -m "Initialize gh-pages"
    git checkout master
fi

# Create deployment directory
DEPLOY_DATE=$(date +%Y-%m-%d)
DEPLOY_DIR="$PROJECT_ROOT/_deploy"
DEPLOY_SUBDIR="$DEPLOY_DIR/$PLAN_ID/$DEPLOY_DATE"

mkdir -p "$DEPLOY_SUBDIR"
cp "$OUTPUT_FILE" "$DEPLOY_SUBDIR/index.html"

echo -e "${GREEN}✓${NC} Copied to deployment directory"

# Commit and push
cd "$DEPLOY_DIR"
git init 2>/dev/null || true
git checkout -B gh-pages 2>/dev/null || true
git add .
git commit -m "Deploy Notion React HTML: $PLAN_ID ($DEPLOY_DATE)" || true

# Push to GitHub
REMOTE_URL=$(cd "$PROJECT_ROOT" && git remote get-url origin 2>/dev/null || echo "")
if [ -n "$REMOTE_URL" ]; then
    # Extract username and repo from git URL
    if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
        USERNAME="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"

        git remote add origin "$REMOTE_URL" 2>/dev/null || true
        git push -f origin gh-pages

        GITHUB_PAGES_URL="https://${USERNAME}.github.io/${REPO}/${PLAN_ID}/${DEPLOY_DATE}/"
        echo -e "${GREEN}✓${NC} Deployed to GitHub Pages"
        echo ""
        echo -e "${BLUE}[4/4]${NC} Deployment complete!"
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✅ Success!${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "📄 Local file:  file://$OUTPUT_FILE"
        echo -e "🌐 GitHub Pages: ${GITHUB_PAGES_URL}"
        echo ""
        echo -e "${YELLOW}💡 Tip:${NC} It may take 1-2 minutes for GitHub Pages to update"
        echo ""
    else
        echo -e "${YELLOW}⚠${NC}  Could not parse GitHub URL, skipping push"
        echo -e "   Manual push: cd $DEPLOY_DIR && git push -f origin gh-pages"
    fi
else
    echo -e "${YELLOW}⚠${NC}  No git remote configured, skipping push"
    echo -e "${GREEN}✓${NC} HTML ready for manual deployment"
    echo ""
    echo -e "📄 Local file: file://$OUTPUT_FILE"
fi

cd "$PROJECT_ROOT"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
