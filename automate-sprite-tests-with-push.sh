#!/bin/bash
set -e

API_TOKEN="adam-761/1425148/581fa386a123b3cee5e3ad6fddfd592c/9186abb5216275aea3799b4393266cb40c23188cdebb968a5292efbb13a9daf5"
SPRITE_NAME="hamhock-ui-test"
API_BASE="https://api.sprites.dev/v1"
GAME_URL="https://adam-s-daniel.github.io/scratch-claude-001/ham-hock.html"
BRANCH="claude/revamp-hamhock-ui-f9nXt"
VIDEO_DIR="test-videos"

echo "🎬 Automated Ham Hock UI Testing with GitHub Push"
echo "=================================================="
echo ""
echo "Sprite: $SPRITE_NAME"
echo "Game URL: $GAME_URL"
echo "Branch: $BRANCH"
echo "Video Directory: $VIDEO_DIR"
echo ""

# Function to execute command in sprite and extract output
exec_sprite() {
    local cmd="$1"
    local desc="$2"

    echo "⚙️  $desc..."

    # Create temp file for response
    local response_file=$(mktemp)

    # Execute command
    curl -s -X POST "$API_BASE/sprites/$SPRITE_NAME/exec" \
      -H "Authorization: Bearer $API_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"command\":[\"bash\",\"-c\",$(printf '%s' "$cmd" | jq -Rs .)]}" \
      -o "$response_file"

    # Extract stdout/stderr, handling null bytes
    local output=$(cat "$response_file" | tr -d '\000' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    stdout = data.get('stdout', '')
    stderr = data.get('stderr', '')
    exit_code = data.get('exit_code', 0)
    if stderr:
        print(f'[stderr] {stderr}', file=sys.stderr)
    if stdout:
        print(stdout)
    sys.exit(exit_code)
except Exception as e:
    print(f'Error parsing response: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

    local exit_code=$?

    # Clean up temp file
    rm -f "$response_file"

    # Print output
    if [ -n "$output" ]; then
        echo "$output"
    fi

    if [ $exit_code -ne 0 ]; then
        echo "❌ Command failed with exit code $exit_code"
        return $exit_code
    fi

    echo "✓ Done"
    echo ""

    return 0
}

# Wait for GitHub Pages deployment
echo "⏳ Waiting for GitHub Pages deployment..."
echo "Checking $GAME_URL"
echo ""

for i in {1..30}; do
    if curl -s -I "$GAME_URL" | head -1 | grep -q "200"; then
        echo "✓ GitHub Pages is live!"
        echo ""
        break
    fi
    echo "  Attempt $i/30: Not ready yet, waiting 5s..."
    sleep 5
done

# Check one more time
if ! curl -s -I "$GAME_URL" | head -1 | grep -q "200"; then
    echo "❌ GitHub Pages not accessible after 150s"
    exit 1
fi

# Install system dependencies
exec_sprite "apt-get update -qq && apt-get install -y curl git ffmpeg 2>&1 | tail -5" "Installing system dependencies"

# Install Node.js
exec_sprite "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1 && apt-get install -y nodejs 2>&1 | tail -3" "Installing Node.js 20"

# Verify Node.js
exec_sprite "node --version && npm --version" "Verifying Node.js installation"

# Clone repository
exec_sprite "cd /tmp && rm -rf scratch-claude-001 && git clone -q https://github.com/Adam-S-Daniel/scratch-claude-001.git 2>&1" "Cloning repository"

# Checkout branch
exec_sprite "cd /tmp/scratch-claude-001 && git checkout $BRANCH 2>&1 | tail -2" "Checking out branch $BRANCH"

# Configure git for commits
exec_sprite "cd /tmp/scratch-claude-001 && git config user.email 'sprite-bot@sprites.dev' && git config user.name 'Sprite Test Bot'" "Configuring git"

# Install dependencies
exec_sprite "cd /tmp/scratch-claude-001 && npm install 2>&1 | tail -5" "Installing npm dependencies"

# Install Playwright
exec_sprite "cd /tmp/scratch-claude-001 && npx playwright install --with-deps chromium 2>&1 | tail -10" "Installing Playwright + Chromium"

# Run tests
echo "🎬 Running Playwright UI tests..."
echo "This will take ~60 seconds..."
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && timeout 120 npm run test 2>&1" "Running UI tests"

# Create test-videos directory
exec_sprite "cd /tmp/scratch-claude-001 && mkdir -p $VIDEO_DIR" "Creating $VIDEO_DIR directory"

# Convert and copy videos to test-videos folder
echo ""
echo "🎥 Converting and organizing videos..."
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && find test-results/videos -name '*.webm' -type f 2>/dev/null | while read video; do
    basename_no_ext=\$(basename \"\$video\" .webm)
    timestamp=\$(date +%Y%m%d-%H%M%S)
    output_name=\"\${basename_no_ext}-\${timestamp}.mp4\"
    echo \"Converting: \$video -> $VIDEO_DIR/\$output_name\"
    ffmpeg -i \"\$video\" -c:v libx264 -c:a aac -movflags +faststart \"$VIDEO_DIR/\$output_name\" -y 2>&1 | tail -3
done" "Converting WebM to MP4"

# List generated videos
echo ""
echo "📹 Generated Videos:"
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && ls -lh $VIDEO_DIR/*.mp4 2>/dev/null || echo 'No MP4 videos found'" "Listing video files in $VIDEO_DIR"

# Add videos to git
exec_sprite "cd /tmp/scratch-claude-001 && git add $VIDEO_DIR/*.mp4 2>&1" "Adding videos to git"

# Check git status
exec_sprite "cd /tmp/scratch-claude-001 && git status --short" "Checking git status"

# Commit videos
echo ""
echo "💾 Committing videos to repository..."
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && git commit -m \"Add UI test videos from Sprite execution

Desktop and mobile test videos:
- Desktop: 1920x1080, ~35 seconds
- Mobile: 375x667, ~15 seconds

Generated on Sprite VM: $SPRITE_NAME
Date: \$(date -u +%Y-%m-%d_%H:%M:%S_UTC)

Features demonstrated:
- Photo-realistic 3D ham hock with Three.js
- HUGE bow tie accessory (2x scale)
- Mobile split-screen layout
- Complete game flow

https://claude.ai/code/session_01ULMfLgZmVfnT9jQhp68TdW\" 2>&1 || echo 'Nothing to commit'" "Committing videos"

# Push to GitHub
echo ""
echo "⬆️  Pushing to GitHub..."
echo ""

# Configure git remote with token for authentication
exec_sprite "cd /tmp/scratch-claude-001 && git remote set-url origin https://$API_TOKEN@github.com/Adam-S-Daniel/scratch-claude-001.git" "Configuring git remote with auth"

exec_sprite "cd /tmp/scratch-claude-001 && git push origin $BRANCH 2>&1" "Pushing to GitHub"

# Verify push
exec_sprite "cd /tmp/scratch-claude-001 && git log --oneline -1" "Verifying last commit"

echo ""
echo "✅ Automated testing and push complete!"
echo "======================================="
echo ""
echo "Sprite VM Details:"
echo "  Name: $SPRITE_NAME"
echo "  URL: https://hamhock-ui-test-blpx4.sprites.app"
echo ""
echo "Videos pushed to:"
echo "  Repository: Adam-S-Daniel/scratch-claude-001"
echo "  Branch: $BRANCH"
echo "  Directory: $VIDEO_DIR/"
echo ""
echo "View on GitHub:"
echo "  https://github.com/Adam-S-Daniel/scratch-claude-001/tree/$BRANCH/$VIDEO_DIR"
echo ""
echo "Test Summary:"
echo "  ✓ Tests executed on Sprite VM"
echo "  ✓ Videos converted to MP4"
echo "  ✓ Videos committed to repository"
echo "  ✓ Changes pushed to GitHub"
echo ""
