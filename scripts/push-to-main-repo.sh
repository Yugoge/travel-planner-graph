#!/bin/bash
# Push source code to main travel-planner repository (private)
# This is separate from travel-planner-graph which is for GitHub Pages only
# Based on knowledge-system's deployment pattern

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

# Repository name for source code (private)
MAIN_REPO_NAME="travel-planner"
MAIN_REPO_URL="git@github.com:Yugoge/${MAIN_REPO_NAME}.git"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 Pushing Source Code to Main Repository${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}✓${NC} Current repository: $(git remote get-url origin $(git rev-parse --abbrev-ref HEAD@{u} 2>/dev/null || echo 'origin'))"
echo -e "${GREEN}✓${NC} Current branch: ${YELLOW}${CURRENT_BRANCH}${NC}"
echo ""

# Step 1: Check authentication
echo -e "${BLUE}📋 Step 1: Checking authentication...${NC}"

if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ]; then
    echo -e "${GREEN}✓${NC} Using SSH keys for authentication"

    # Verify SSH key is accessible to GitHub
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        echo -e "${GREEN}✓${NC} SSH connection to GitHub verified"
    else
        echo -e "${YELLOW}⚠${NC} Warning: SSH key might not be added to GitHub"
        echo "  If push fails, add your public key to:"
        echo "  https://github.com/settings/keys"
        echo ""
        if [ -f ~/.ssh/id_ed25519.pub ]; then
            echo "  Your public key (~/.ssh/id_ed25519.pub):"
            cat ~/.ssh/id_ed25519.pub
            echo ""
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC} Warning: No SSH keys found"
    echo ""
    echo "Please set up SSH keys:"
    echo "  1. Generate key: ssh-keygen -t ed25519 -C 'your@email.com'"
    echo "  2. Add to GitHub: https://github.com/settings/keys"
    echo ""
    exit 1
fi

# Step 2: Add remote if it doesn't exist
echo ""
echo -e "${BLUE}📋 Step 2: Setting up remote...${NC}"

if git remote | grep -q "^${MAIN_REPO_NAME}$"; then
    echo -e "${GREEN}✓${NC} Remote '${MAIN_REPO_NAME}' already exists"
    git remote set-url "${MAIN_REPO_NAME}" "${MAIN_REPO_URL}"
else
    echo -e "${GREEN}✓${NC} Adding remote '${MAIN_REPO_NAME}'..."
    git remote add "${MAIN_REPO_NAME}" "${MAIN_REPO_URL}"
fi

echo -e "  Remote URL: ${MAIN_REPO_URL}"

# Step 3: Check if main repo exists
echo ""
echo -e "${BLUE}📋 Step 3: Checking if repository exists...${NC}"

if git ls-remote "${MAIN_REPO_URL}" &>/dev/null; then
    echo -e "${GREEN}✓${NC} Repository exists: Yugoge/${MAIN_REPO_NAME}"
else
    echo -e "${RED}❌${NC} Error: Repository does not exist: Yugoge/${MAIN_REPO_NAME}"
    echo ""
    echo "Please create the repository first:"
    echo "  gh repo create ${MAIN_REPO_NAME} --private"
    echo ""
    exit 1
fi

# Step 4: Show changes
echo ""
echo -e "${BLUE}📋 Step 4: Showing changes...${NC}"

if git diff --stat "${MAIN_REPO_NAME}/${CURRENT_BRANCH}" 2>/dev/null; then
    echo ""
    echo -e "${YELLOW}Changes to be pushed:${NC}"
    git diff --stat "${MAIN_REPO_NAME}/${CURRENT_BRANCH}" 2>/dev/null || true
else
    echo -e "${YELLOW}⚠${NC} No changes compared to remote (or remote doesn't have this branch yet)"
fi

# Step 5: Push
echo ""
echo -e "${BLUE}📋 Step 5: Pushing to ${MAIN_REPO_NAME}/${CURRENT_BRANCH}...${NC}"
echo ""

git push "${MAIN_REPO_NAME}" "${CURRENT_BRANCH}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Push Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📦 Repository: https://github.com/Yugoge/${MAIN_REPO_NAME}"
echo -e "🔒 Private: Yes"
echo ""
echo -e "${BLUE}Note:${NC} This pushes to the MAIN repository (${MAIN_REPO_NAME})"
echo -e "      For GitHub Pages, use: ${YELLOW}bash scripts/generate-and-deploy.sh <plan-id>${NC}"
