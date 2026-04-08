#!/bin/bash
# ============================================
#  Push Dashboard Cloning Tool to GitHub
# ============================================

echo ""
echo "======================================"
echo " GitHub Setup — Dashboard Cloning Tool"
echo "======================================"
echo ""

# Ask for GitHub repo URL
read -p "Enter your GitHub repo URL (e.g. https://github.com/yourname/dashboard-cloning-tool.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
  echo "ERROR: Repo URL is required"
  exit 1
fi

# Init git if not already
if [ ! -d ".git" ]; then
  echo "Initializing git repo..."
  git init
  git branch -M main
fi

# Add remote
git remote remove origin 2>/dev/null
git remote add origin "$REPO_URL"
echo "Remote set to: $REPO_URL"

# Stage all files
echo ""
echo "Staging files..."
git add .
git status --short

# Commit
echo ""
git commit -m "Initial commit — Dashboard Cloning Tool"

# Push
echo ""
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "======================================"
echo " ✓ Code pushed to GitHub!"
echo "======================================"
echo ""
echo "NEXT STEP — Add these secrets to your GitHub repo:"
echo "  Go to: Settings → Secrets and variables → Actions → New repository secret"
echo ""
echo "  REDSHIFT_HOST"
echo "  REDSHIFT_PORT"
echo "  REDSHIFT_DB"
echo "  REDSHIFT_USER"
echo "  REDSHIFT_PASSWORD"
echo "  REDSHIFT_SCHEMA"
echo "  TABLEAU_URL"
echo "  TABLEAU_PAT_NAME"
echo "  TABLEAU_PAT_SECRET"
echo "  TABLEAU_SITE"
echo "  JWT_SECRET            (any long random string)"
echo "  SUPER_ADMIN_EMAIL"
echo "  SUPER_ADMIN_PASSWORD"
echo "  SMTP_HOST"
echo "  SMTP_PORT"
echo "  SMTP_USER"
echo "  SMTP_PASSWORD"
echo ""
echo "Once secrets are added, go to:"
echo "  Actions tab → Deploy Dashboard Cloning Tool → Run workflow"
echo "  Download the generated .env artifact and place it in the project root"
echo ""
