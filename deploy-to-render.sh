#!/bin/bash
set -e

echo "🚀 WealthFlow Backend Deploy Script"
echo "===================================="
echo ""

# Check if GITHUB_USER is set
if [ -z "$GITHUB_USER" ]; then
    echo "Enter your GitHub username:"
    read GITHUB_USER
fi

REPO_NAME="${1:-wealthflow-backend}"
REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"

echo ""
echo "Step 1: Pushing to GitHub..."
echo "   Repo: $REMOTE_URL"

# Check if remote exists, add if not
git remote get-url origin 2>/dev/null || git remote add origin "$REMOTE_URL"

git push -u origin main || {
    echo ""
    echo "❌ Push failed. Make sure you:"
    echo "   1. Created the repo: https://github.com/new"
    echo "   2. Named it: $REPO_NAME"
    echo "   3. Are logged in: gh auth login"
    exit 1
}

echo ""
echo "✅ Pushed to GitHub!"
echo ""
echo "Step 2: Deploy to Render"
echo "   Click this link to deploy with one click:"
echo ""
echo "   https://dashboard.render.com/select-repo?type=web"
echo ""
echo "   Or use the Render Blueprint:"
echo "   https://render.com/docs/blueprint-spec"
echo ""
echo "   After deploy, your API will be at:"
echo "   https://$REPO_NAME.onrender.com"
echo ""
echo "Step 3: Update frontend"
echo "   Edit frontend/app.js and set:"
echo "   const API_BASE = 'https://$REPO_NAME.onrender.com';"
echo ""
