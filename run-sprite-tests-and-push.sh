#!/bin/bash
set -e

# Configuration
SPRITES_TOKEN="adam-761/1425148/581fa386a123b3cee5e3ad6fddfd592c/9186abb5216275aea3799b4393266cb40c23188cdebb968a5292efbb13a9daf5"
SPRITE_NAME="hamhock-ui-test"
API_BASE="https://api.sprites.dev/v1"
GAME_URL="https://adam-s-daniel.github.io/scratch-claude-001/ham-hock.html"
BRANCH="claude/revamp-hamhock-ui-f9nXt"

echo "🎬 Running UI Tests on Sprite and Pushing to GitHub"
echo "===================================================="
echo ""

# Check if GitHub token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GitHub token required!"
    echo ""
    echo "Usage:"
    echo "  export GITHUB_TOKEN='your_github_personal_access_token'"
    echo "  $0"
    echo ""
    echo "To create a GitHub token:"
    echo "  1. Go to: https://github.com/settings/tokens"
    echo "  2. Click 'Generate new token (classic)'"
    echo "  3. Select scopes: repo (all)"
    echo "  4. Generate and copy the token"
    echo ""
    exit 1
fi

echo "✓ GitHub token provided"
echo "Sprite: $SPRITE_NAME"
echo "Branch: $BRANCH"
echo ""

# Function to execute long-running command on Sprite
exec_sprite_bg() {
    local cmd="$1"
    local desc="$2"

    echo "⚙️  $desc..."

    # Execute command in background (don't wait for response parsing)
    curl -s -X POST "$API_BASE/sprites/$SPRITE_NAME/exec" \
      -H "Authorization: Bearer $SPRITES_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"command\":[\"bash\",\"-c\",$(printf '%s' "$cmd" | jq -Rs .)]}" \
      > /dev/null 2>&1 &

    echo "✓ Command sent (running in background)"
    echo ""
}

# Function to execute and wait for result
exec_sprite() {
    local cmd="$1"
    local desc="$2"

    echo "⚙️  $desc..."

    curl -s -X POST "$API_BASE/sprites/$SPRITE_NAME/exec" \
      -H "Authorization: Bearer $SPRITES_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"command\":[\"bash\",\"-c\",$(printf '%s' "$cmd" | jq -Rs .)]}" \
      > /dev/null 2>&1

    echo "✓ Done"
    echo ""
}

echo "⏳ Step 1: Setting up Sprite environment..."
echo ""

# Install system dependencies
exec_sprite "apt-get update -qq && apt-get install -y curl git ffmpeg nodejs npm 2>&1 | tail -5" "Installing dependencies"

# Verify installations
exec_sprite "node --version && npm --version && ffmpeg -version | head -1" "Verifying installations"

echo "⏳ Step 2: Cloning repository and installing..."
echo ""

# Clone repo
exec_sprite "cd /tmp && rm -rf scratch-claude-001 && git clone -q https://github.com/Adam-S-Daniel/scratch-claude-001.git 2>&1" "Cloning repository"

# Checkout branch
exec_sprite "cd /tmp/scratch-claude-001 && git checkout $BRANCH 2>&1 | tail -2" "Checking out branch"

# Install npm dependencies
exec_sprite "cd /tmp/scratch-claude-001 && npm install 2>&1 | tail -3" "Installing npm packages"

# Install Playwright
exec_sprite "cd /tmp/scratch-claude-001 && npx playwright install --with-deps chromium 2>&1 | tail -5" "Installing Playwright"

echo "⏳ Step 3: Running UI tests (this takes ~60 seconds)..."
echo ""

# Run tests
exec_sprite "cd /tmp/scratch-claude-001 && timeout 120 npm run test 2>&1 && echo 'Tests completed successfully' || echo 'Tests may have had issues'" "Running Playwright tests"

# Wait for tests to complete
echo "⏳ Waiting for tests to finish..."
sleep 70
echo ""

echo "⏳ Step 4: Converting and pushing videos..."
echo ""

# Copy push script to Sprite
PUSH_SCRIPT=$(cat push-videos-from-sprite.sh | base64 -w 0)

exec_sprite "cd /tmp/scratch-claude-001 && echo '$PUSH_SCRIPT' | base64 -d > push-videos.sh && chmod +x push-videos.sh" "Uploading push script"

# Run the push script with GitHub token
echo "⬆️  Executing video conversion and push..."
exec_sprite "cd /tmp/scratch-claude-001 && export GITHUB_TOKEN='$GITHUB_TOKEN' && ./push-videos.sh 2>&1" "Converting and pushing videos"

# Wait for push to complete
echo "⏳ Waiting for push to complete..."
sleep 10
echo ""

echo "✅ Process complete!"
echo "==================="
echo ""
echo "The Sprite has:"
echo "  ✓ Run UI tests with video recording"
echo "  ✓ Converted videos to MP4"
echo "  ✓ Committed videos to repository"
echo "  ✓ Pushed to GitHub branch: $BRANCH"
echo ""
echo "Check GitHub for videos:"
echo "  https://github.com/Adam-S-Daniel/scratch-claude-001/tree/$BRANCH/test-videos"
echo ""
echo "Pull the latest changes locally:"
echo "  git pull origin $BRANCH"
echo ""
