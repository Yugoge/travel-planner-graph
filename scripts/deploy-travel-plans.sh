#!/bin/bash
# Deploy travel plan HTML to GitHub Pages
# Usage: bash scripts/deploy-travel-plans.sh travel-plan-paris-2026-03-15.html
# Prerequisites: Git + (GITHUB_TOKEN or SSH keys)

set -e

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_NAME="travel-planner-graph"
BRANCH="${GITHUB_PAGES_BRANCH:-gh-pages}"
TEMP_BASE="${TEMP_DIR:-/tmp}"
DEPLOY_DIR="${TEMP_BASE}/${REPO_NAME}-deploy"

# Parse command line argument
if [ -z "$1" ]; then
    echo "Error: Please provide travel plan HTML file path"
    echo "Usage: bash scripts/deploy-travel-plans.sh travel-plan-paris-2026-03-15.html"
    exit 1
fi

INPUT_FILE="$1"
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File not found: $INPUT_FILE"
    exit 1
fi

# Extract filename without path
FILENAME=$(basename "$INPUT_FILE")

# Parse destination and date from filename
# Format 1: travel-plan-{destination-slug}-{YYYY-MM-DD}.html (itinerary)
# Format 2: travel-plan-{destination-slug}-{YYYYMMDD-HHMMSS}.html (timestamped)
# Format 3: travel-plan-{destination-slug}.html (bucket list, no specific date)
# Format 4: Any format with version suffix: travel-plan-{...}-v2.html

# Remove version suffix if present
BASE_FILENAME="${FILENAME%%-v[0-9]*.html}.html"
BASE_FILENAME="${BASE_FILENAME##travel-plan-}"
BASE_FILENAME="${BASE_FILENAME%.html}"

# Try to extract date in various formats
if [[ "$BASE_FILENAME" =~ -([0-9]{4}-[0-9]{2}-[0-9]{2})$ ]]; then
    # Format 1: Standard date format (YYYY-MM-DD)
    PLAN_DATE="${BASH_REMATCH[1]}"
    DESTINATION_SLUG="${BASE_FILENAME%-*}"
elif [[ "$BASE_FILENAME" =~ -([0-9]{8}-[0-9]{6})$ ]]; then
    # Format 2: Timestamp format (YYYYMMDD-HHMMSS)
    TIMESTAMP="${BASH_REMATCH[1]}"
    # Convert timestamp to date (YYYY-MM-DD)
    YEAR="${TIMESTAMP:0:4}"
    MONTH="${TIMESTAMP:4:2}"
    DAY="${TIMESTAMP:6:2}"
    PLAN_DATE="${YEAR}-${MONTH}-${DAY}"
    DESTINATION_SLUG="${BASE_FILENAME%-*}"
else
    # Format 3: No date (bucket list)
    PLAN_DATE=$(date +%Y-%m-%d)
    DESTINATION_SLUG="${BASE_FILENAME}"
fi

echo "=================================================="
echo "🚀 Deploying Travel Plan to GitHub Pages"
echo "Destination: ${DESTINATION_SLUG}"
echo "Date: ${PLAN_DATE}"
echo "Repository: ${REPO_NAME}"
echo "=================================================="

# Step 1: Detect GitHub username
echo ""
echo "📋 Step 1: Detecting GitHub username..."

GIT_USER=$(git config --get user.name 2>/dev/null || echo "")
GIT_EMAIL=$(git config --get user.email 2>/dev/null || echo "")

if [ -z "$GIT_USER" ]; then
    echo "❌ Error: Git user.name not configured"
    echo ""
    echo "Configure with:"
    echo "  git config --global user.name 'YourUsername'"
    echo "  git config --global user.email 'your@email.com'"
    exit 1
fi

# Extract GitHub username from git remotes or use git config name
GITHUB_USER=""
if git remote -v 2>/dev/null | grep -q "github.com"; then
    GITHUB_USER=$(git remote -v | grep "github.com" | head -1 | sed -E 's/.*github\.com[:/]([^/]+)\/.*/\1/')
fi

if [ -z "$GITHUB_USER" ]; then
    if [[ "$GIT_EMAIL" == *"@users.noreply.github.com" ]]; then
        GITHUB_USER=$(echo "$GIT_EMAIL" | sed -E 's/.*\+([^@]+)@users\.noreply\.github\.com/\1/')
    else
        GITHUB_USER="$GIT_USER"
    fi
fi

echo "✓ GitHub Username: $GITHUB_USER"
echo "  Git Name: $GIT_USER"
echo "  Git Email: $GIT_EMAIL"

# Step 2: Check authentication method
echo ""
echo "📋 Step 2: Checking authentication..."

USE_SSH=false
USE_TOKEN=false

if [ -n "$GITHUB_TOKEN" ]; then
    echo "✓ Using GITHUB_TOKEN for authentication"
    USE_TOKEN=true
    REPO_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
elif [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ]; then
    echo "✓ Using SSH keys for authentication"

    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        echo "✓ SSH connection to GitHub verified"
    else
        echo "⚠️  Warning: SSH key might not be added to GitHub"
        echo "  If deployment fails, add your public key to:"
        echo "  https://github.com/settings/keys"
    fi

    USE_SSH=true
    REPO_URL="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
else
    echo "⚠️  Warning: No authentication method found"
    echo ""
    echo "Please set up authentication:"
    echo ""
    echo "Option 1: Personal Access Token (recommended)"
    echo "  1. Visit: https://github.com/settings/tokens/new"
    echo "  2. Select scopes: repo (all), workflow"
    echo "  3. Generate token and run:"
    echo "     export GITHUB_TOKEN='your_token_here'"
    echo ""
    echo "Option 2: SSH Keys"
    echo "  1. Generate key: ssh-keygen -t ed25519 -C 'your@email.com'"
    echo "  2. Add to GitHub: https://github.com/settings/keys"
    echo ""
    exit 1
fi

# Step 3: Check if repository exists
echo ""
echo "📋 Step 3: Checking if repository exists..."

REPO_EXISTS=false
if [ "$USE_TOKEN" = true ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: token ${GITHUB_TOKEN}" \
        "https://api.github.com/repos/${GITHUB_USER}/${REPO_NAME}")

    if [ "$HTTP_CODE" = "200" ]; then
        REPO_EXISTS=true
    fi
else
    if git ls-remote "$REPO_URL" &>/dev/null; then
        REPO_EXISTS=true
    fi
fi

if [ "$REPO_EXISTS" = true ]; then
    echo "✓ Repository exists: ${GITHUB_USER}/${REPO_NAME}"
else
    echo "⚠️  Repository does not exist: ${GITHUB_USER}/${REPO_NAME}"

    if [ "$USE_TOKEN" = true ]; then
        echo "  Creating repository via GitHub API..."

        CREATE_RESPONSE=$(curl -s -X POST \
            -H "Authorization: token ${GITHUB_TOKEN}" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/user/repos" \
            -d "{\"name\":\"${REPO_NAME}\",\"description\":\"Travel Plans - Auto-generated by travel-planner\",\"public\":true,\"auto_init\":false}")

        if echo "$CREATE_RESPONSE" | grep -q '"full_name"'; then
            echo "✓ Repository created successfully"
            REPO_EXISTS=true
            sleep 2
        else
            echo "❌ Failed to create repository"
            echo "$CREATE_RESPONSE"
            exit 1
        fi
    else
        if command -v gh &> /dev/null; then
            echo "  Checking GitHub CLI authentication..."
            if gh auth status &>/dev/null; then
                echo "  Creating repository via GitHub CLI..."

                if gh repo create "${REPO_NAME}" --public --description "Travel Plans - Auto-generated by travel-planner" 2>/dev/null; then
                    echo "✓ Repository created successfully via GitHub CLI"
                    REPO_EXISTS=true
                    sleep 2
                else
                    if gh repo view "${GITHUB_USER}/${REPO_NAME}" &>/dev/null; then
                        echo "✓ Repository already exists"
                        REPO_EXISTS=true
                    else
                        echo "❌ Failed to create repository"
                        echo ""
                        echo "Please create the repository manually:"
                        echo "  1. Visit: https://github.com/new"
                        echo "  2. Repository name: ${REPO_NAME}"
                        echo "  3. Make it public"
                        echo "  4. Do NOT initialize with README"
                        echo "  5. Run this script again"
                        exit 1
                    fi
                fi
            else
                echo "⚠️  GitHub CLI not authenticated"
                echo ""
                echo "Please create the repository manually:"
                echo "  1. Visit: https://github.com/new"
                echo "  2. Repository name: ${REPO_NAME}"
                echo "  3. Make it public"
                echo "  4. Run this script again"
                exit 1
            fi
        else
            echo "⚠️  GitHub CLI not installed"
            echo ""
            echo "Please create the repository manually:"
            echo "  1. Visit: https://github.com/new"
            echo "  2. Repository name: ${REPO_NAME}"
            echo "  3. Make it public"
            echo "  4. Run this script again"
            exit 1
        fi
    fi
fi

# Step 4: Clone/prepare deployment directory
echo ""
echo "📋 Step 4: Preparing deployment..."

# Check if we can clone existing repo
if [ "$REPO_EXISTS" = true ]; then
    rm -rf "$DEPLOY_DIR"

    # Try to clone gh-pages branch if it exists
    if git ls-remote --heads "$REPO_URL" "$BRANCH" 2>/dev/null | grep -q "$BRANCH"; then
        echo "  Cloning existing gh-pages branch..."
        git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$DEPLOY_DIR" 2>/dev/null || {
            echo "  Creating new gh-pages branch..."
            mkdir -p "$DEPLOY_DIR"
            cd "$DEPLOY_DIR"
            git init
            git checkout -b "$BRANCH"
        }
    else
        echo "  Creating new gh-pages branch..."
        mkdir -p "$DEPLOY_DIR"
        cd "$DEPLOY_DIR"
        git init
        git checkout -b "$BRANCH"
    fi
else
    rm -rf "$DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
    git init
    git checkout -b "$BRANCH"
fi

cd "$DEPLOY_DIR"

# Step 5: Create directory structure and copy file
echo ""
echo "📋 Step 5: Creating directory structure..."

TARGET_DIR="${DEPLOY_DIR}/${DESTINATION_SLUG}/${PLAN_DATE}"
mkdir -p "$TARGET_DIR"

# Copy the HTML file to target directory
cp "$INPUT_FILE" "${TARGET_DIR}/index.html"

echo "✓ Copied to: /${DESTINATION_SLUG}/${PLAN_DATE}/index.html"

# Create .nojekyll to disable Jekyll processing
touch "${DEPLOY_DIR}/.nojekyll"

# Step 6: Generate/update index.html
echo ""
echo "📋 Step 6: Generating index page..."

# Scan all directories to build plan list
PLAN_DIRS=$(find . -mindepth 2 -maxdepth 2 -type d | grep -E '^\./[^/]+/[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort -r || echo "")

# Generate index.html
cat > "${DEPLOY_DIR}/index.html" << 'EOF_TEMPLATE'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Travel Plans</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 1rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 3rem;
        }

        header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .plans-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }

        .plan-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            display: flex;
            flex-direction: column;
        }

        .plan-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
        }

        .plan-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            margin-bottom: 1rem;
        }

        .plan-card h2 {
            font-size: 1.5rem;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            text-transform: capitalize;
        }

        .plan-meta {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }

        .plan-date {
            font-weight: 600;
            color: #667eea;
        }

        .view-button {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            text-align: center;
            transition: opacity 0.3s ease;
            margin-top: auto;
        }

        .view-button:hover {
            opacity: 0.9;
        }

        .empty-state {
            text-align: center;
            color: white;
            padding: 3rem;
        }

        .empty-state h2 {
            font-size: 1.8rem;
            margin-bottom: 1rem;
        }

        footer {
            text-align: center;
            color: white;
            padding: 2rem 0;
            opacity: 0.8;
        }

        @media (max-width: 768px) {
            header h1 {
                font-size: 2rem;
            }

            .plans-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>My Travel Plans</h1>
            <p>All your adventures in one place</p>
        </header>

        <main>
            <div class="plans-grid" id="plans-grid">
                <!-- Plans will be inserted here -->
            </div>
        </main>

        <footer>
            <p>Generated by Claude Travel Planner</p>
            <p>Last updated: TIMESTAMP_PLACEHOLDER</p>
        </footer>
    </div>

    <script>
        // Plans data will be inserted here
        const plans = PLANS_DATA_PLACEHOLDER;

        const plansGrid = document.getElementById('plans-grid');

        if (plans.length === 0) {
            plansGrid.innerHTML = '<div class="empty-state"><h2>No travel plans yet</h2><p>Create your first plan to see it here!</p></div>';
        } else {
            plans.forEach(plan => {
                const card = document.createElement('div');
                card.className = 'plan-card';
                card.innerHTML = `
                    <div class="plan-icon">🗺️</div>
                    <h2>${plan.destination}</h2>
                    <div class="plan-meta">
                        <span class="plan-date">${plan.date}</span>
                    </div>
                    <a href="${plan.url}" class="view-button">View Plan</a>
                `;
                plansGrid.appendChild(card);
            });
        }
    </script>
</body>
</html>
EOF_TEMPLATE

# Build plans JSON data
PLANS_JSON="["
FIRST=true

if [ -n "$PLAN_DIRS" ]; then
    for dir in $PLAN_DIRS; do
        # Extract destination and date from path
        # Format: ./destination/YYYY-MM-DD
        DEST=$(echo "$dir" | sed 's|^\./||' | cut -d'/' -f1)
        DATE=$(echo "$dir" | sed 's|^\./||' | cut -d'/' -f2)

        # Format destination name (capitalize and replace hyphens with spaces)
        DEST_NAME=$(echo "$DEST" | tr '-' ' ' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')

        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            PLANS_JSON+=","
        fi

        PLANS_JSON+="{\"destination\":\"$DEST_NAME\",\"date\":\"$DATE\",\"url\":\"./$DEST/$DATE/\"}"
    done
fi

PLANS_JSON+="]"

# Replace placeholders in index.html
CURRENT_TIME=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
sed -i "s|PLANS_DATA_PLACEHOLDER|$PLANS_JSON|g" "${DEPLOY_DIR}/index.html"
sed -i "s|TIMESTAMP_PLACEHOLDER|$CURRENT_TIME|g" "${DEPLOY_DIR}/index.html"

echo "✓ Index page generated with all plans"

# Create README
cat > "${DEPLOY_DIR}/README.md" << EOF
# Travel Plans

This repository contains auto-generated travel plans from the travel-planner.

**Live Site:** [https://${GITHUB_USER}.github.io/${REPO_NAME}/](https://${GITHUB_USER}.github.io/${REPO_NAME}/)

## Travel Plans

EOF

if [ -n "$PLAN_DIRS" ]; then
    for dir in $PLAN_DIRS; do
        DEST=$(echo "$dir" | sed 's|^\./||' | cut -d'/' -f1)
        DATE=$(echo "$dir" | sed 's|^\./||' | cut -d'/' -f2)
        DEST_NAME=$(echo "$DEST" | tr '-' ' ' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')

        echo "- [$DEST_NAME - $DATE](https://${GITHUB_USER}.github.io/${REPO_NAME}/${DEST}/${DATE}/)" >> "${DEPLOY_DIR}/README.md"
    done
fi

cat >> "${DEPLOY_DIR}/README.md" << EOF

Last updated: $CURRENT_TIME
EOF

# Step 7: Commit and push
echo ""
echo "📋 Step 7: Deploying to GitHub Pages..."

git config user.name "$GIT_USER"
git config user.email "$GIT_EMAIL"

git add -A

# Create commit message
git commit -m "Add travel plan: ${DESTINATION_SLUG} (${PLAN_DATE})

Generated: $CURRENT_TIME

🤖 Auto-deployed by travel-planner
"

# Set remote
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

# Push to gh-pages branch (without force to preserve history)
echo "  Pushing to ${BRANCH} branch..."
git push origin "$BRANCH"

echo "✓ Pushed to GitHub"

# Step 8: Enable GitHub Pages (if using token)
if [ "$USE_TOKEN" = true ]; then
    echo ""
    echo "📋 Step 8: Configuring GitHub Pages..."

    PAGES_RESPONSE=$(curl -s -X POST \
        -H "Authorization: token ${GITHUB_TOKEN}" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/${GITHUB_USER}/${REPO_NAME}/pages" \
        -d "{\"source\":{\"branch\":\"${BRANCH}\",\"path\":\"/\"}}")

    if echo "$PAGES_RESPONSE" | grep -q '"html_url"' || echo "$PAGES_RESPONSE" | grep -q 'already exists'; then
        echo "✓ GitHub Pages enabled"
    else
        echo "⚠️  Could not auto-enable GitHub Pages (may already be enabled)"
        echo "  Manual check: https://github.com/${GITHUB_USER}/${REPO_NAME}/settings/pages"
    fi
else
    echo ""
    echo "📋 Step 8: GitHub Pages configuration..."

    if command -v gh &> /dev/null && gh auth status &>/dev/null; then
        echo "  Attempting to enable GitHub Pages via GitHub CLI..."

        PAGES_RESPONSE=$(gh api -X POST "/repos/${GITHUB_USER}/${REPO_NAME}/pages" \
            -f branch="${BRANCH}" \
            -f path="/" 2>&1 || true)

        if echo "$PAGES_RESPONSE" | grep -q '"html_url"' || echo "$PAGES_RESPONSE" | grep -q 'already enabled'; then
            echo "✓ GitHub Pages enabled via GitHub CLI"
        else
            echo "⚠️  Could not auto-enable GitHub Pages (may already be enabled)"
        fi
    else
        echo "⚠️  Using SSH - GitHub Pages may need manual enablement:"
        echo "  Visit: https://github.com/${GITHUB_USER}/${REPO_NAME}/settings/pages"
        echo "  Source: Deploy from branch"
        echo "  Branch: ${BRANCH}"
    fi
fi

# Step 9: Cleanup
echo ""
echo "📋 Step 9: Cleaning up..."
cd /
rm -rf "$DEPLOY_DIR"
echo "✓ Temporary files removed"

# Final message
echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""
echo "🌐 Your travel plan will be live at:"
echo "  ${DESTINATION_SLUG}: https://${GITHUB_USER}.github.io/${REPO_NAME}/${DESTINATION_SLUG}/${PLAN_DATE}/"
echo "  Index: https://${GITHUB_USER}.github.io/${REPO_NAME}/"
echo ""
echo "⏱️  Note: GitHub Pages may take 1-2 minutes to build"
echo "📁 Repository: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "=================================================="
