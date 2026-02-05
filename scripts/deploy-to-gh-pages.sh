#!/bin/bash
# Deploy Notion React HTML to GitHub Pages (preserving history)
# Usage: bash scripts/deploy-to-gh-pages.sh <plan-id> <html-file>

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

# Check arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}❌ Error: Plan ID and HTML file required${NC}"
    echo -e "Usage: bash scripts/deploy-to-gh-pages.sh <plan-id> <html-file>"
    echo -e "Example: bash scripts/deploy-to-gh-pages.sh beijing-exchange-bucket-list-20260202-232405 travel-plan-notion-*.html"
    exit 1
fi

PLAN_ID="$1"
HTML_FILE="$2"
DEPLOY_DATE=$(date +%Y-%m-%d)

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 GitHub Pages Deployment (History-Preserving)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Validate HTML file
if [ ! -f "$HTML_FILE" ]; then
    echo -e "${RED}❌ Error: HTML file not found: $HTML_FILE${NC}"
    exit 1
fi

FILE_SIZE=$(du -h "$HTML_FILE" | cut -f1)
echo -e "${GREEN}✓${NC} Plan ID: ${YELLOW}$PLAN_ID${NC}"
echo -e "${GREEN}✓${NC} HTML file: $HTML_FILE (${FILE_SIZE})"
echo -e "${GREEN}✓${NC} Deploy date: $DEPLOY_DATE"
echo ""

# Step 1: Clone gh-pages branch
echo -e "${BLUE}[1/4]${NC} Cloning gh-pages branch..."
TEMP_DIR="/tmp/gh-pages-deploy-$$"
REPO_URL=$(cd "$PROJECT_ROOT" && git remote get-url origin 2>/dev/null || echo "")

if [ -z "$REPO_URL" ]; then
    echo -e "${RED}❌ Error: No git remote configured${NC}"
    exit 1
fi

# Extract username and repo from git URL
if [[ "$REPO_URL" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    USERNAME="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
else
    echo -e "${RED}❌ Error: Could not parse GitHub URL: $REPO_URL${NC}"
    exit 1
fi

# Clone gh-pages branch (or create if doesn't exist)
if git ls-remote --exit-code --heads "$REPO_URL" gh-pages >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Cloning existing gh-pages branch..."
    git clone --branch gh-pages --single-branch "$REPO_URL" "$TEMP_DIR"
else
    echo -e "${YELLOW}⚠${NC}  gh-pages branch doesn't exist, creating..."
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    git init
    git remote add origin "$REPO_URL"
    git checkout -b gh-pages
    echo "# GitHub Pages" > README.md
    git add README.md
    git commit -m "Initialize gh-pages branch"
    git push -u origin gh-pages
fi

cd "$TEMP_DIR"
echo -e "${GREEN}✓${NC} Working directory: $TEMP_DIR"
echo ""

# Step 2: Copy HTML to deployment directory
echo -e "${BLUE}[2/4]${NC} Copying HTML to deployment structure..."
DEPLOY_SUBDIR="$PLAN_ID/$DEPLOY_DATE"
mkdir -p "$DEPLOY_SUBDIR"
cp "$HTML_FILE" "$DEPLOY_SUBDIR/index.html"
echo -e "${GREEN}✓${NC} Copied to $DEPLOY_SUBDIR/index.html"
echo ""

# Step 3: Generate automatic index.html
echo -e "${BLUE}[3/4]${NC} Generating automatic index.html..."
python3 "$SCRIPT_DIR/generate-gh-pages-index.py" "$TEMP_DIR"
echo -e "${GREEN}✓${NC} Auto-generated index.html"
echo ""

# Step 4: Commit and push (NO FORCE PUSH)
echo -e "${BLUE}[4/4]${NC} Committing and pushing..."
git add .
if git diff --staged --quiet; then
    echo -e "${YELLOW}⚠${NC}  No changes to commit"
else
    git commit -m "Deploy: $PLAN_ID ($DEPLOY_DATE)

- Added version: $DEPLOY_DATE
- Auto-generated index.html
- File size: $FILE_SIZE"

    # IMPORTANT: NO -f flag! This preserves history
    git push origin gh-pages
    echo -e "${GREEN}✓${NC} Pushed to GitHub Pages"
fi

# Cleanup
cd "$PROJECT_ROOT"
rm -rf "$TEMP_DIR"

# Success message
GITHUB_PAGES_URL="https://${USERNAME}.github.io/${REPO}/${PLAN_ID}/${DEPLOY_DATE}/"
ROOT_URL="https://${USERNAME}.github.io/${REPO}/"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📄 Local file:       file://$HTML_FILE"
echo -e "🌐 This version:     ${GITHUB_PAGES_URL}"
echo -e "🏠 All plans:        ${ROOT_URL}"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "  • It may take 1-2 minutes for GitHub Pages to update"
echo -e "  • Previous versions are preserved (history maintained)"
echo -e "  • index.html automatically lists all deployed plans"
echo ""
